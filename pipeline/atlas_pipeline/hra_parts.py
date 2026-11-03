"""Choose, name, side and group the HuBMAP HRA female meshes."""
from __future__ import annotations

import re

from .hra_glb import HraMesh
from .parts import Part

# Thin surface patches drawn on top of another mesh (they only cause z-fighting); see test_real_hra_*.
SURFACE_DUPLICATES: frozenset[str] = frozenset({
    "VH_F_gastric_impression_of_liver", "VH_F_suprarenal_impression_of_liver", "VH_F_renal_impression_of_liver",
    "VH_F_duodenal_impression_of_liver", "VH_F_esophageal_impression_of_liver", "VH_F_colic_impression_of_liver",
    "VH_F_bare_area_of_liver", "VH_F_diaphragmatic_surface_of_liver", "VH_F_porta_hepatis",
    # Lobar parts of each lung hilum lie entirely on the hilum mesh itself.
    "VH_F_hilum_upper_L", "VH_F_hilum_lower_L", "VH_F_hilum_upper_R", "VH_F_hilum_middle_R", "VH_F_hilum_lower_R",
})
# Real structures of different systems that share a boundary and both stay (ids are "HRA:<node>"). Overlaps
# inside one system are allowed without listing: they share one colour, so nothing flickers.
ALLOWED_OVERLAPS: frozenset[frozenset[str]] = frozenset(frozenset(pair) for pair in (
    ("HRA:VH_F_central_retinal_vein_L", "HRA:VH_F_central_retinal_artery_L"),
    ("HRA:VH_F_central_retinal_vein_R", "HRA:VH_F_central_retinal_artery_R"),
    ("HRA:VH_F_optic_disc_L", "HRA:VH_F_dura_mater_left"),
    ("HRA:VH_F_optic_disc_L", "HRA:VH_F_left_optic_nerve"),
))

_ANDREASSEN_DUPLICATES = ("anterior_cruciate_ligament", "posterior_cruciate_ligament", "tibial_collateral_ligament",
                          "fibular_collateral_ligament", "rectus_femoris")
_ARTERY = re.compile(r"artery|arteries|aort|carotid|subclavian|brachiocephalic", re.I)
_VEIN = re.compile(r"vein|vena_cava|coronary_sinus", re.I)
_GROUPS = {
    "integumentary_system": "integumentary", "muscular_system": "muscular", "reproductive_system": "reproductive",
    "digestive_system": "digestive", "urinary_system": "urinary", "respiratory_system": "respiratory",
    "lymphatic_system": "lymphatic", "skeletal_system": "connective", "lower_limb": "connective",
}
_PREFIXES = ("VH_F_", "Allen_", "Yao_")


def classify_hra(mesh: HraMesh) -> tuple[str | None, str]:
    path, node = mesh.path, mesh.node
    lower = node.lower()
    if "VH_F_placenta" in path:
        return None, "placenta"
    if ("VH_F_femur_L" in path or "VH_F_femur_R" in path
            or node.startswith(("VH_F_tibia_", "VH_F_fibula_", "VH_F_patella_"))
            or ("VH_F_skeletal_system" in path and "intervertebral_disk" not in lower)):
        return None, "dup-bone"
    if any(key in lower for key in _ANDREASSEN_DUPLICATES):
        return None, "dup-andreassen"
    if node in SURFACE_DUPLICATES:
        return None, "dup-surface"
    if "Yao_lymph_node" in path:
        return "lymphatic", "lymph-node"
    if "VH_F_heart" in path:
        return "cardiac", "heart"
    if _ARTERY.search(node):
        return "arterial", "artery"
    if _VEIN.search(node):
        return "venous", "vein"
    if "VH_F_circulatory_system" in path and (lower.endswith("_trunk") or "branch" in lower):
        return "arterial", "artery"  # pulmonary/celiac trunk and coronary artery branches
    if "VH_F_blood_vasculature" in path:
        raise ValueError(f"pembuluh HRA tanpa aturan: {node}")
    if "VH_F_eyes" in path:
        return "sensory", "eye"
    if "VH_F_nervous_system" in path:
        return "nervous", "nervous"
    if "tonsil" in lower:
        return "lymphatic", "tonsil"
    if "VH_F_muscular_system" in path and "tendon" in lower:
        return "connective", "tendon"
    if len(path) > 1 and path[1].removeprefix("VH_F_") in _GROUPS:
        return _GROUPS[path[1].removeprefix("VH_F_")], "group"
    raise ValueError(f"bagian HRA tanpa aturan: {'/'.join(path)}")


def _strip_prefix(node: str) -> str:
    for prefix in _PREFIXES:
        if node.startswith(prefix):
            return node[len(prefix):]
    return node


def hra_side(node: str) -> str:
    tokens = node.split("_")
    words = [t.lower() for t in tokens]
    if "L" in tokens or "left" in words:
        return "left"
    if "R" in tokens or "right" in words:
        return "right"
    return "none"


def _letter_suffix(node: str) -> str | None:
    last = _strip_prefix(node).split("_")[-1]
    return last if re.fullmatch(r"[a-z]", last) else None


def hra_english_name(node: str, label: str | None) -> str:
    side = hra_side(node)
    suffix = _letter_suffix(node)
    if label:
        words = label.split()
    else:
        tokens = _strip_prefix(node).split("_")
        if suffix:
            tokens = tokens[:-1]
        words = [t for t in tokens if t and t not in ("L", "R")]
    words = [w for w in words if w.lower() not in ("left", "right")]
    core = " ".join(words)
    if side != "none":
        first = core.split(" ", 1)[0]
        if not (first.isupper() or any(ch.isdigit() for ch in first)):
            core = core[:1].lower() + core[1:]
        core = f"{side.capitalize()} {core}"
    name = core[:1].upper() + core[1:]
    if suffix and not name.endswith(f"({suffix})"):
        name = f"{name} ({suffix})"
    return name


def hra_ontology(ontology: str | None) -> tuple[str | None, str | None]:
    if not ontology:
        return None, None
    fma = re.fullmatch(r"FMA[:_]?(\d+)", ontology.strip(), re.I)
    if fma:
        return f"FMA{fma.group(1)}", None
    uberon = re.fullmatch(r"UBERON[:_](\d+)", ontology.strip(), re.I)
    if uberon:
        return None, f"UBERON:{uberon.group(1)}"
    return None, None


def hra_to_parts(meshes: list[HraMesh]) -> tuple[list[Part], list[dict]]:
    parts: list[Part] = []
    excluded: list[dict] = []
    for mesh in meshes:
        system, rule = classify_hra(mesh)
        if system is None:
            excluded.append({"node": mesh.node, "reason": rule})
            continue
        fma, uberon = hra_ontology(mesh.ontology)
        parts.append(Part(f"HRA:{mesh.node}", system, hra_side(mesh.node), "perempuan-asli", "hra", mesh.node,
                          {"en": hra_english_name(mesh.node, mesh.label)}, mesh.vertices, mesh.faces,
                          fma=fma, uberon=uberon))
    return parts, excluded
