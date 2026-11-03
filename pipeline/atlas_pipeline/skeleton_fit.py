"""Place the BoneHub (CT) bones in the HRA female frame.

The trunk gets one similarity transform. Thigh, kneecap and shank are matched bone by bone to HRA's own leg bones.
Arms, hands and feet have no HRA bones, and the HRA skin stands in a different pose than the lying CT body, so
those segments are turned at their joints to follow the skin (see the plan, Task 6).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

import numpy as np
import trimesh
from scipy.optimize import minimize
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree
from scipy.spatial.transform import Rotation

from .bonehub import bone_name_en, bone_segment, bone_side
from .hra_glb import HraMesh
from .parts import Part
from .registration import Similarity, mean_distance_mm, rigid_with_scale, umeyama
from .skin_field import SkinField

TRUNK_PAIRS: dict[str, tuple[str, ...]] = {
    **{f"VERTEBRA_C{i}": (f"VH_F_cervical_vertebra_{i}",) for i in range(1, 8)},
    **{f"VERTEBRA_T{i}": (f"VH_F_thoracic_vertebra_{i}",) for i in range(1, 13)},
    **{f"VERTEBRA_L{i}": (f"VH_F_lumbar_vertebra_{i}",) for i in range(1, 7)},
    "SACRUM": ("VH_F_sacrum", "VH_F_coccyx"),
    "STERNUM": ("VH_F_sternum", "VH_F_manubrium"),
    "HIP_LEFT": ("VH_F_ilium_compact_bone_L",),
    "HIP_RIGHT": ("VH_F_ilium_compact_bone_R",),
}
LEG_PAIRS: dict[str, dict[str, tuple[str, ...]]] = {
    "thigh": {"FEMUR_LEFT": ("VH_F_femur_L",), "FEMUR_RIGHT": ("VH_F_femur_R",)},
    "patella": {"PATELLA_LEFT": ("VH_F_patella_L",), "PATELLA_RIGHT": ("VH_F_patella_R",)},
    "shank": {"TIBIA_LEFT": ("VH_F_tibia_L",), "FIBULA_LEFT": ("VH_F_fibula_L",),
              "TIBIA_RIGHT": ("VH_F_tibia_R",), "FIBULA_RIGHT": ("VH_F_fibula_R",)},
}
# Stems whose reposed segment could not be placed inside the skin; they are replaced by fitted BodyParts3D bones.
SEGMENT_FALLBACKS: frozenset[str] = frozenset()

ARM_SEGMENTS = ("girdle", "upperarm", "forearm", "hand")
MARGINS = {"girdle": 0.003, "upperarm": 0.008, "forearm": 0.005, "hand": 0.002, "foot": 0.002}
OUTSIDE_MM = 2.0
_ARM_X = 0.15
_SLICE_STEP = 0.01
_SLICE_HALF = 0.003
_LINK = 0.015


@dataclass
class SkeletonFit:
    trunk: Similarity
    placement: dict[str, Similarity]
    segment_of: dict[str, str]
    report: dict = field(default_factory=dict)
    fallback: frozenset[str] = frozenset()


# --- helpers --------------------------------------------------------------------------------------------------

def _sample(points: np.ndarray, count: int, seed: int) -> np.ndarray:
    points = np.asarray(points, dtype=np.float64)
    if len(points) <= count:
        return points
    return points[np.random.default_rng(seed).choice(len(points), count, replace=False)]


def rotation_between(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Smallest rotation taking direction a to direction b."""
    a = np.asarray(a, float) / np.linalg.norm(a)
    b = np.asarray(b, float) / np.linalg.norm(b)
    axis = np.cross(a, b)
    sin, cos = np.linalg.norm(axis), float(np.dot(a, b))
    if sin < 1e-12:
        if cos > 0:
            return np.eye(3)
        helper = np.array([1.0, 0, 0]) if abs(a[0]) < 0.9 else np.array([0, 1.0, 0])
        axis = np.cross(a, helper)
        return Rotation.from_rotvec(np.pi * axis / np.linalg.norm(axis)).as_matrix()
    return Rotation.from_rotvec(axis / sin * np.arctan2(sin, cos)).as_matrix()


def about(pivot: np.ndarray, rotation: np.ndarray, shift: np.ndarray | None = None) -> Similarity:
    """Rotation about a pivot point, then an optional shift."""
    pivot = np.asarray(pivot, float)
    translation = pivot - rotation @ pivot + (np.zeros(3) if shift is None else shift)
    return Similarity(1.0, rotation, translation)


def _main_axis(points: np.ndarray) -> np.ndarray:
    centred = points - points.mean(axis=0)
    return np.linalg.svd(centred, full_matrices=False)[2][0]


def _smallest_axis(points: np.ndarray) -> np.ndarray:
    centred = points - points.mean(axis=0)
    return np.linalg.svd(centred, full_matrices=False)[2][2]


def _ends(points: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """(projection on the main axis, vertex at the low end, vertex at the high end)."""
    axis = _main_axis(points)
    projection = points @ axis
    return projection, points[projection.argmin()], points[projection.argmax()]


def _end_near(points: np.ndarray, near: np.ndarray, length: float) -> np.ndarray:
    """Centroid of the vertices within `length` of the bone end closest to `near`."""
    projection, low, high = _ends(points)
    if np.linalg.norm(low - near) <= np.linalg.norm(high - near):
        return points[projection <= projection.min() + length].mean(axis=0)
    return points[projection >= projection.max() - length].mean(axis=0)


def _end_far(points: np.ndarray, near: np.ndarray, length: float) -> np.ndarray:
    projection, low, high = _ends(points)
    if np.linalg.norm(low - near) > np.linalg.norm(high - near):
        return points[projection <= projection.min() + length].mean(axis=0)
    return points[projection >= projection.max() - length].mean(axis=0)


def _extreme_near(points: np.ndarray, near: np.ndarray) -> np.ndarray:
    _, low, high = _ends(points)
    return low if np.linalg.norm(low - near) <= np.linalg.norm(high - near) else high


def point_along(polyline: np.ndarray, origin: np.ndarray, distance: float) -> np.ndarray:
    """First point on the polyline (walked from its start) at `distance` from `origin`; the last point if none."""
    d = np.linalg.norm(polyline - origin, axis=1)
    for i in range(1, len(polyline)):
        if d[i - 1] <= distance <= d[i]:
            a, b = polyline[i - 1], polyline[i]
            # Solve |a + u (b - a) - origin| = distance for u in [0, 1].
            ab, ao = b - a, a - origin
            qa, qb, qc = ab @ ab, 2 * ab @ ao, ao @ ao - distance ** 2
            disc = max(qb * qb - 4 * qa * qc, 0.0)
            u = (-qb + np.sqrt(disc)) / (2 * qa) if qa > 0 else 0.0
            return a + np.clip(u, 0.0, 1.0) * ab
    return polyline[-1]


def _outside_cost(points: np.ndarray, skin: SkinField, margin: float) -> float:
    excess = np.maximum(skin.signed(points) + margin, 0.0)
    return float(np.mean(excess ** 2))


def _refine(points: np.ndarray, pivot: np.ndarray, skin: SkinField, margin: float,
            max_degrees: float, max_shift: float) -> Similarity:
    """Small rotation about `pivot` plus shift that pushes `points` inside the skin by `margin`."""
    if _outside_cost(points, skin, margin) == 0.0:
        return Similarity.identity()
    limit = np.radians(max_degrees)

    def transform(x: np.ndarray) -> Similarity:
        return about(pivot, Rotation.from_rotvec(x[:3]).as_matrix(), x[3:] if len(x) > 3 else None)

    def cost(x: np.ndarray) -> float:
        return _outside_cost(transform(x).apply(points), skin, margin)

    size = 6 if max_shift > 0 else 3
    bounds = [(-limit, limit)] * 3 + [(-max_shift, max_shift)] * (size - 3)
    result = minimize(cost, np.zeros(size), method="Powell", bounds=bounds,
                      options={"xtol": 1e-4, "ftol": 1e-12, "maxfev": 4000})
    best = transform(result.x)
    return best if cost(result.x) < _outside_cost(points, skin, margin) else Similarity.identity()


# --- pairs ----------------------------------------------------------------------------------------------------

def fit_pairs(bones: dict[str, trimesh.Trimesh], targets: dict[str, np.ndarray], stems: Sequence[str],
              init: Similarity, with_scale: bool, recenter: bool = True, iterations: int = 60) -> Similarity:
    """ICP over several bones at once; each target point is matched only to points of its own bone.
    `recenter` first moves the transformed bones' centroid onto the targets' centroid (for complete targets)."""
    stems = [s for s in stems if s in bones and s in targets]
    src = {s: _sample(bones[s].vertices, 20_000, seed=5) for s in stems}
    dst = {s: _sample(targets[s], 6_000, seed=6) for s in stems}
    trees = {s: cKDTree(src[s]) for s in stems}
    transform = init
    if recenter:
        moved = np.concatenate([transform.apply(src[s]) for s in stems])
        wanted = np.concatenate([dst[s] for s in stems])
        transform = Similarity(transform.scale, transform.rotation,
                               transform.translation + wanted.mean(axis=0) - moved.mean(axis=0))
    for fraction in (1.0, 0.9):
        previous = np.inf
        for _ in range(iterations):
            inverse = transform.inverse()
            pairs_src, pairs_dst = [], []
            for s in stems:
                _, idx = trees[s].query(inverse.apply(dst[s]))
                pairs_src.append(src[s][idx])
                pairs_dst.append(dst[s])
            a, b = np.concatenate(pairs_src), np.concatenate(pairs_dst)
            distance = np.linalg.norm(transform.apply(a) - b, axis=1)
            keep = distance <= np.quantile(distance, fraction)
            transform = umeyama(a[keep], b[keep]) if with_scale else rigid_with_scale(a[keep], b[keep], init.scale)
            error = float(distance[keep].mean())
            if abs(previous - error) < 1e-9:
                break
            previous = error
    return transform


# --- limbs ----------------------------------------------------------------------------------------------------

def _components(points: np.ndarray) -> list[np.ndarray]:
    if len(points) == 0:
        return []
    pairs = cKDTree(points).query_pairs(_LINK, output_type="ndarray")
    graph = coo_matrix((np.ones(len(pairs)), (pairs[:, 0], pairs[:, 1])), shape=(len(points), len(points)))
    count, labels = connected_components(graph, directed=False)
    return [points[labels == k] for k in range(count) if (labels == k).sum() >= 20]


def limb_centerline(skin: SkinField, side: str, below_y: float) -> np.ndarray:
    """Centres of the arm's skin cross-sections every 1 cm below `below_y`, top to bottom. Slices where the arm
    is not yet separate from the trunk are skipped; the line ends at the first slice without the arm."""
    sign = 1.0 if side == "left" else -1.0
    points = skin.points
    line: list[np.ndarray] = []
    y = below_y
    lowest = points[:, 1].min()
    while y > lowest:
        slab = points[np.abs(points[:, 1] - y) < _SLICE_HALF]
        # The bounding-box centre of a cross-section is its centre even where the skin samples are uneven.
        candidates = [(c.min(axis=0) + c.max(axis=0)) / 2 for c in _components(slab)
                      if sign * c.mean(axis=0)[0] > _ARM_X]
        if candidates:
            if line:
                previous = line[-1]
                centre = min(candidates, key=lambda c: np.linalg.norm(c[[0, 2]] - previous[[0, 2]]))
                if np.linalg.norm(centre[[0, 2]] - previous[[0, 2]]) > 0.06:
                    break
            else:
                centre = max(candidates, key=lambda c: sign * c[0])
            line.append(np.array([centre[0], y, centre[2]]))
        elif line:
            break
        y -= _SLICE_STEP
    line_array = np.array(line)
    if len(line_array) >= 3:  # light smoothing of sampling noise; keep the two ends
        smooth = line_array.copy()
        smooth[1:-1, [0, 2]] = (line_array[:-2, [0, 2]] + line_array[1:-1, [0, 2]] + line_array[2:, [0, 2]]) / 3
        line_array = smooth
    return line_array


def repose_arm(bones: dict[str, np.ndarray], parent: Similarity, centerline: np.ndarray, skin: SkinField,
               side: str) -> dict[str, Similarity]:
    s = side.upper()
    get = lambda name: np.asarray(bones[f"{name}_{s}"], dtype=np.float64)  # noqa: E731
    clavicle, scapula, humerus = get("CLAVICLE"), get("SCAPULA"), get("HUMERUS")
    forearm_ct = np.concatenate([get("RADIUS"), get("ULNA")])
    hand_stems = [k for k in bones if k.endswith(f"_{s}") and bone_segment(k) == "hand"]
    hand_ct = np.concatenate([np.asarray(bones[k], float) for k in hand_stems])

    # Joint centres in the CT frame.
    sc_joint = clavicle[np.abs(clavicle[:, 0]).argmin()]
    projection, low, high = _ends(humerus)
    top_is_high = high[1] >= low[1]
    shoulder = humerus[projection >= projection.max() - 0.025].mean(axis=0) if top_is_high \
        else humerus[projection <= projection.min() + 0.025].mean(axis=0)
    humerus_distal = low if top_is_high else high
    elbow = (humerus_distal + 0.5 * (_extreme_near(get("RADIUS"), humerus_distal)
                                     + _extreme_near(get("ULNA"), humerus_distal))) / 2
    wrist = _end_far(get("RADIUS"), elbow, 0.015)
    tip_bone = bones.get(f"PHALANGE_HAND_3_{s}")
    hand_tip = _end_far(np.asarray(tip_bone, float), wrist, 0.010) if tip_bone is not None \
        else hand_ct[np.linalg.norm(hand_ct - wrist, axis=1).argmax()]

    # 1. Shoulder girdle: turn at the sternoclavicular joint until it sits inside the skin.
    girdle_points = parent.apply(_sample(np.concatenate([clavicle, scapula]), 1500, seed=8))
    girdle = _refine(girdle_points, parent.apply(sc_joint), skin, MARGINS["girdle"], 25.0, 0.0).compose(parent)

    # 2-4. Upper arm, forearm and hand follow the arm's centreline.
    scale = parent.scale
    shoulder_f = girdle.apply(shoulder)
    elbow_target = point_along(centerline, shoulder_f, scale * np.linalg.norm(elbow - shoulder))
    upper = about(shoulder_f, rotation_between(girdle.rotation @ (elbow - shoulder), elbow_target - shoulder_f)) \
        .compose(girdle)
    elbow_f = upper.apply(elbow)
    wrist_target = point_along(centerline, elbow_f, scale * np.linalg.norm(wrist - elbow))
    fore = about(elbow_f, rotation_between(upper.rotation @ (wrist - elbow), wrist_target - elbow_f)).compose(upper)
    wrist_f = fore.apply(wrist)
    tip_target = centerline[-1]
    hand = about(wrist_f, rotation_between(fore.rotation @ (hand_tip - wrist), tip_target - wrist_f)).compose(fore)

    # Roll hand and forearm about their axes so the palm faces the way the skin's hand does.
    palm_stems = [f"METACARPAL_{i}_{s}" for i in (2, 3, 4, 5) if f"METACARPAL_{i}_{s}" in bones]
    below = centerline[centerline[:, 1] < wrist_f[1]]
    if palm_stems and len(below):
        near_hand = cKDTree(below).query(skin.points, distance_upper_bound=0.05)[0] < np.inf
        hand_skin = skin.points[near_hand & (skin.points[:, 1] < wrist_f[1])]
        if len(hand_skin) > 50:
            axis = (tip_target - wrist_f) / np.linalg.norm(tip_target - wrist_f)
            current = hand.rotation @ _smallest_axis(np.concatenate([np.asarray(bones[k], float) for k in palm_stems]))
            wanted = _smallest_axis(hand_skin)
            flat = lambda v: v - (v @ axis) * axis  # noqa: E731
            c, w = flat(current), flat(wanted)
            if np.linalg.norm(c) > 1e-6 and np.linalg.norm(w) > 1e-6:
                angles = []
                for candidate in (w, -w):
                    angle = np.arctan2(np.cross(c, candidate) @ axis, c @ candidate)
                    angles.append(angle)
                angle = min(angles, key=abs)
                hand = about(wrist_f, Rotation.from_rotvec(axis * angle).as_matrix()).compose(hand)
                fore_axis = (wrist_f - elbow_f) / np.linalg.norm(wrist_f - elbow_f)
                fore = about(elbow_f, Rotation.from_rotvec(fore_axis * angle).as_matrix()).compose(fore)

    # 5. Refine each segment a little; children follow their parent's correction.
    placed = {"girdle": girdle, "upperarm": upper, "forearm": fore, "hand": hand}
    pieces = {"upperarm": humerus, "forearm": forearm_ct, "hand": hand_ct}
    pivots = {"upperarm": shoulder, "forearm": elbow, "hand": wrist}
    for index, segment in enumerate(ARM_SEGMENTS[1:], start=1):
        points = placed[segment].apply(_sample(pieces[segment], 1500, seed=9 + index))
        delta = _refine(points, placed[segment].apply(pivots[segment]), skin, MARGINS[segment], 10.0, 0.010)
        for child in ARM_SEGMENTS[index:]:
            placed[child] = delta.compose(placed[child])
    return placed


def _far_tip(points: np.ndarray, reference: np.ndarray, length: float = 0.01) -> np.ndarray:
    """Centroid of the points within `length` of the farthest point from `reference`."""
    distance = np.linalg.norm(points - reference, axis=1)
    return points[distance >= distance.max() - length].mean(axis=0)


def repose_foot(bones: dict[str, np.ndarray], parent: Similarity, skin: SkinField, side: str) -> Similarity:
    s = side.upper()
    stems = [k for k in bones if k.endswith(f"_{s}") and bone_segment(k) == "foot"]
    foot_ct = np.concatenate([np.asarray(bones[k], float) for k in stems])
    ankle = parent.apply(np.asarray(bones[f"TALUS_{s}"], float).mean(axis=0))
    calcaneus = parent.apply(np.asarray(bones[f"CALCANEUS_{s}"], float))
    heel_ct = calcaneus[calcaneus[:, 2] < calcaneus[:, 2].min() + 0.01].mean(axis=0)
    toe_ct = _far_tip(parent.apply(np.asarray(bones[f"METATARSAL_2_{s}"], float)), ankle)

    points = skin.points
    foot_skin = points[(points[:, 1] < ankle[1] - 0.03) & (np.abs(points[:, 0] - ankle[0]) < 0.08)]
    z = foot_skin[:, 2]
    heel = foot_skin[z < z.min() + 0.01].mean(axis=0)
    toe = foot_skin[z > z.max() - 0.01].mean(axis=0)
    wanted = toe - heel
    turn = rotation_between(toe_ct - heel_ct, wanted)
    foot = about(ankle, turn).compose(parent)

    # Roll about the foot axis so the sole faces down: "up" is perpendicular to the foot axis and to the line
    # across the heads of the first and fifth metatarsals.
    if f"METATARSAL_1_{s}" in bones and f"METATARSAL_5_{s}" in bones:
        axis = wanted / np.linalg.norm(wanted)
        first = foot.apply(_far_tip(np.asarray(bones[f"METATARSAL_1_{s}"], float), parent.inverse().apply(ankle)))
        fifth = foot.apply(_far_tip(np.asarray(bones[f"METATARSAL_5_{s}"], float), parent.inverse().apply(ankle)))
        up = np.cross(axis, fifth - first)
        if up[1] < 0:
            up = -up
        flat_up = up - (up @ axis) * axis
        target = np.array([0.0, 1.0, 0.0]) - axis[1] * axis
        if np.linalg.norm(flat_up) > 1e-6 and np.linalg.norm(target) > 1e-6:
            angle = np.arctan2(np.cross(flat_up, target) @ axis, flat_up @ target)
            foot = about(ankle, Rotation.from_rotvec(axis * angle).as_matrix()).compose(foot)

    points_f = foot.apply(_sample(foot_ct, 1500, seed=12))
    return _refine(points_f, ankle, skin, MARGINS["foot"], 10.0, 0.010).compose(foot)


# --- whole skeleton -------------------------------------------------------------------------------------------

def _outside_fraction(points: np.ndarray, skin: SkinField) -> float:
    return float(np.mean(skin.signed(_sample(points, 3000, seed=13)) > OUTSIDE_MM / 1000))


def fit_skeleton(bones: dict[str, trimesh.Trimesh], hra: dict[str, HraMesh], skin: SkinField) -> SkeletonFit:
    def targets_for(pairs: dict[str, tuple[str, ...]]) -> dict[str, np.ndarray]:
        return {stem: np.concatenate([hra[n].vertices for n in nodes]) for stem, nodes in pairs.items()
                if stem in bones and all(n in hra for n in nodes)}

    report: dict = {"bones": {}, "segments": {}}
    trunk_targets = targets_for(TRUNK_PAIRS)
    stems = sorted(trunk_targets)
    init = umeyama(np.array([bones[s].vertices.mean(axis=0) for s in stems]),
                   np.array([trunk_targets[s].mean(axis=0) for s in stems]))
    trunk = fit_pairs(bones, trunk_targets, stems, init, with_scale=True, recenter=False)
    placement: dict[str, Similarity] = {}
    segment_of: dict[str, str] = {}
    for stem in bones:
        if bone_segment(stem) == "trunk":
            placement[stem], segment_of[stem] = trunk, "trunk"
    for stem in stems:
        report["bones"][stem] = dict(zip(("meanMm", "p95Mm"), mean_distance_mm(bones[stem].vertices,
                                                                              trunk_targets[stem], trunk)))
    report["trunk"] = {"scale": trunk.scale}

    for side in ("left", "right"):
        s = side.upper()
        shank = trunk
        for segment, pairs in LEG_PAIRS.items():
            side_pairs = {k: v for k, v in pairs.items() if k.endswith(f"_{s}")}
            targets = targets_for(side_pairs)
            if not targets:
                continue
            found = fit_pairs(bones, targets, sorted(targets), trunk, with_scale=False)
            for stem in targets:
                placement[stem], segment_of[stem] = found, f"{segment}-{side}"
                report["bones"][stem] = dict(zip(("meanMm", "p95Mm"), mean_distance_mm(bones[stem].vertices,
                                                                                      targets[stem], found)))
            if segment == "shank":
                shank = found

        verts = {k: bones[k].vertices for k in bones if k.endswith(f"_{s}")}
        if all(f"{n}_{s}" in bones for n in ("CLAVICLE", "SCAPULA", "HUMERUS", "RADIUS", "ULNA")):
            shoulder_y = trunk.apply(bones[f"HUMERUS_{s}"].vertices)[:, 1].max()
            line = limb_centerline(skin, side, below_y=shoulder_y)
            report["segments"][f"centerline-{side}"] = len(line)
            arm = repose_arm(verts, trunk, line, skin, side)
            for stem in verts:
                segment = bone_segment(stem)
                if segment in arm:
                    placement[stem], segment_of[stem] = arm[segment], f"{segment}-{side}"
        if f"TALUS_{s}" in bones and f"CALCANEUS_{s}" in bones and f"METATARSAL_2_{s}" in bones:
            foot = repose_foot(verts, shank, skin, side)
            for stem in verts:
                if bone_segment(stem) == "foot":
                    placement[stem], segment_of[stem] = foot, f"foot-{side}"

    for segment in sorted(set(segment_of.values())):
        members = [k for k, v in segment_of.items() if v == segment]
        points = np.concatenate([placement[k].apply(bones[k].vertices) for k in members])
        fraction = _outside_fraction(points, skin)
        status = "lulus" if fraction <= 0.02 else ("dipakai" if fraction <= 0.10 else "gagal")
        report["segments"][segment] = {"outsideFraction": fraction, "status": status, "bones": len(members)}
    fallback = frozenset(s for s in SEGMENT_FALLBACKS if s in bones)
    return SkeletonFit(trunk, placement, segment_of, report, fallback)


def bones_to_parts(bones: dict[str, trimesh.Trimesh], fit: SkeletonFit, fma_by_stem: dict[str, str]) -> list[Part]:
    parts = []
    for stem in sorted(bones):
        if stem in fit.fallback or stem not in fit.placement:
            continue
        notes: list[str] = []
        if fit.segment_of[stem] != "trunk":
            notes.append("pose-disesuaikan")
        if stem.startswith(("HUMERUS_", "RADIUS_", "ULNA_")):
            notes.append("siku-tidak-lengkap")
        parts.append(Part(f"BH:{stem}", "skeletal", bone_side(stem), "perempuan-asli", "bonehub", stem,
                          {"en": bone_name_en(stem)}, fit.placement[stem].apply(bones[stem].vertices),
                          np.asarray(bones[stem].faces), fma=fma_by_stem.get(stem), notes=tuple(notes)))
    return parts
