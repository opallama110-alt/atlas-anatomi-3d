import numpy as np
import pytest
import trimesh
from scipy.spatial.transform import Rotation

from atlas_pipeline.registration import Similarity
from atlas_pipeline.skeleton_fit import fit_pairs, limb_centerline, repose_arm, repose_foot
from atlas_pipeline.skin_field import SkinField


def tube(start, end, radius):
    return trimesh.creation.cylinder(radius=radius, segment=[np.asarray(start, float), np.asarray(end, float)], sections=48)


def union(*meshes):
    return trimesh.util.concatenate(meshes)


def test_fit_pairs_recovers_known_transform():
    rot = Similarity(1.0, Rotation.from_rotvec([0, 0, 0.14]).as_matrix(), np.array([0.05, 0, 0.01]))
    femur = tube([0.1, 0.5, 0], [0.12, 0.9, 0.02], 0.015)
    femur.vertices[:3] += 0.01                                     # sedikit tidak simetris
    bones = {"FEMUR_LEFT": femur}
    targets = {"FEMUR_LEFT": rot.apply(femur.vertices)}
    found = fit_pairs(bones, targets, ["FEMUR_LEFT"], Similarity.identity(), with_scale=False)
    assert np.abs(found.apply(femur.vertices) - targets["FEMUR_LEFT"]).max() < 1e-3


ARM_TOP, ARM_BOTTOM = [0.17, 0.45, 0.0], [0.48, -0.22, 0.0]       # lengan lurus, terbuka ±25°
# Badan dibuat lebih ramping dari lengan supaya kedua tabung tertutup itu tidak saling tumpang di dalam: jarak
# bertanda ke gabungan dua permukaan tertutup yang tumpang tindih tidak bermakna di daerah sambungannya.
SKIN = union(tube([0, -0.4, 0], [0, 0.6, 0], 0.12), tube(ARM_TOP, ARM_BOTTOM, 0.045))


def test_limb_centerline_follows_tilted_tube():
    line = limb_centerline(SkinField(SKIN.vertices, SKIN.faces, samples=200_000), "left", below_y=0.3)
    line = line[line[:, 1] > -0.15]                                  # jauhi tutup ujung tabung
    axis = (np.array(ARM_BOTTOM) - ARM_TOP) / np.linalg.norm(np.subtract(ARM_BOTTOM, ARM_TOP))
    offsets = line - ARM_TOP
    dist = np.linalg.norm(offsets - np.outer(offsets @ axis, axis), axis=1)
    assert len(line) > 20 and dist.max() < 0.004


def test_limb_centerline_on_the_right_side_is_mirrored():
    mirrored = SKIN.copy()
    mirrored.vertices[:, 0] *= -1
    mirrored.invert()
    line = limb_centerline(SkinField(mirrored.vertices, mirrored.faces, samples=200_000), "right", below_y=0.3)
    assert (line[:, 0] < -0.15).all()


def test_repose_arm_puts_bent_arm_inside_straight_tube():
    skin = SkinField(SKIN.vertices, SKIN.faces, samples=200_000)
    shoulder, elbow = np.array([0.18, 0.43, 0]), np.array([0.19, 0.15, 0])
    wrist = elbow + [0.0, -0.08, 0.22]                               # siku menekuk 70° ke depan, seperti CT
    bones = {"CLAVICLE_LEFT": tube([0.02, 0.50, 0.03], [0.12, 0.50, 0.0], 0.008).vertices,
             "SCAPULA_LEFT": tube([0.08, 0.45, -0.08], [0.10, 0.35, -0.09], 0.01).vertices,
             "HUMERUS_LEFT": tube(shoulder, elbow, 0.011).vertices,
             "RADIUS_LEFT": tube(elbow + [0.01, -0.01, 0.0], wrist, 0.008).vertices,
             "ULNA_LEFT": tube(elbow + [-0.01, -0.01, 0.0], wrist, 0.008).vertices,
             "PHALANGE_HAND_3_LEFT": tube(wrist, wrist + [0, -0.02, 0.15], 0.006).vertices,
             "METACARPAL_3_LEFT": tube(wrist, wrist + [0, -0.01, 0.08], 0.006).vertices}
    centerline = limb_centerline(skin, "left", below_y=0.3)
    placed = repose_arm(bones, Similarity.identity(), centerline, skin, "left")
    seg = {"CLAVICLE_LEFT": "girdle", "SCAPULA_LEFT": "girdle", "HUMERUS_LEFT": "upperarm", "RADIUS_LEFT": "forearm",
           "ULNA_LEFT": "forearm", "PHALANGE_HAND_3_LEFT": "hand", "METACARPAL_3_LEFT": "hand"}
    pts = np.concatenate([placed[seg[s]].apply(v) for s, v in bones.items()])
    assert np.mean(skin.signed(pts) > 0.002) <= 0.02


def test_repose_foot_turns_pointed_foot_flat():
    ankle = np.array([0.1, 0.08, -0.05])
    leg = tube(ankle + [0, 0.025, 0], ankle + [0, 0.42, 0], 0.04)       # 5 mm di atas kotak: dua permukaan tertutup tidak boleh tumpang
    sole = trimesh.creation.box([0.09, 0.10, 0.30]).apply_translation([0.1, 0.05, 0.01])    # telapak rata, ke +Z
    shape = union(leg, sole)
    skin = SkinField(shape.vertices, shape.faces, samples=200_000)
    down = Rotation.from_rotvec([0.7, 0, 0])                         # menjinjit ±40°

    def bone(extents, center):
        return down.apply(trimesh.creation.box(extents).subdivide().subdivide().vertices + center) + ankle

    bones = {"TALUS_LEFT": bone([0.03, 0.03, 0.04], [0, 0, 0]),
             "CALCANEUS_LEFT": bone([0.04, 0.04, 0.07], [0, -0.01, -0.03]),
             "METATARSAL_2_LEFT": bone([0.015, 0.015, 0.08], [0, -0.005, 0.1])}
    placed = repose_foot(bones, Similarity.identity(), skin, "left")
    pts = placed.apply(np.concatenate(list(bones.values())))
    main = np.linalg.svd(pts - pts.mean(0))[2][0]
    assert abs(main[2]) > np.cos(np.radians(5))


@pytest.mark.realdata
def test_real_skeleton_fit(raw_dir):
    import json
    from atlas_pipeline.bonehub import find_bonehub, load_bonehub
    from atlas_pipeline.hra_glb import read_hra_glb
    from atlas_pipeline.skeleton_fit import LEG_PAIRS, SEGMENT_FALLBACKS, TRUNK_PAIRS, fit_skeleton
    hra = {m.node: m for m in read_hra_glb(raw_dir / "hra" / "3d-vh-f-united.glb")}
    skin = SkinField(hra["VH_F_skin"].vertices, hra["VH_F_skin"].faces)
    bones = load_bonehub(find_bonehub(raw_dir))
    fit = fit_skeleton(bones, hra, skin)
    out = raw_dir.parent / "work" / "female"
    out.mkdir(parents=True, exist_ok=True)
    (out / "skeleton-report.json").write_text(json.dumps(fit.report, indent=1), encoding="utf-8")
    trunk = {k: v["meanMm"] for k, v in fit.report["bones"].items() if k in TRUNK_PAIRS}
    legs = {k: v["meanMm"] for k, v in fit.report["bones"].items() if any(k in p for p in LEG_PAIRS.values())}
    assert len(trunk) == 30 and max(trunk.values()) <= 5.0, trunk
    assert len(legs) == 8 and max(legs.values()) <= 5.0, legs
    bad = {seg: v for seg, v in fit.report["segments"].items()
           if isinstance(v, dict) and v["outsideFraction"] > 0.02}
    unresolved = {seg: v for seg, v in bad.items()
                  if not any(fit.segment_of[s] == seg for s in SEGMENT_FALLBACKS)}
    assert all(v["outsideFraction"] <= 0.10 for v in unresolved.values()), bad
