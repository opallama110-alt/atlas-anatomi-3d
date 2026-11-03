"""Names, sides and skeleton segments of the BoneHub Visible Human Female bones (one STL per bone)."""
from __future__ import annotations

import re
from pathlib import Path

import trimesh

from .obj_mesh import to_atlas_space

ORDINALS = ("first", "second", "third", "fourth", "fifth", "sixth", "seventh", "eighth", "ninth", "tenth",
            "eleventh", "twelfth")
FINGERS = ("thumb", "index finger", "middle finger", "ring finger", "little finger")
TOES = ("big toe", "second toe", "third toe", "fourth toe", "little toe")

_FOOT = {"TALUS", "CALCANEUS", "NAVICULAR", "CUBOID", "MEDIAL_CUNEIFORM", "INTERMEDIATE_CUNEIFORM",
         "LATERAL_CUNEIFORM"}
_HAND = {"SCAPHOID", "LUNATE", "TRIQUETRUM", "PISIFORM", "TRAPEZIUM", "TRAPEZOID", "CAPITATE", "HAMATE"}
_LIMB = {"FEMUR": "thigh", "PATELLA": "patella", "TIBIA": "shank", "FIBULA": "shank", "CLAVICLE": "girdle",
         "SCAPULA": "girdle", "HUMERUS": "upperarm", "RADIUS": "forearm", "ULNA": "forearm", "HIP": "trunk"}
_PLAIN_NAMES = {"TRIQUETRUM": "triquetral", "CUBOID": "cuboid bone", "HIP": "hip bone",
                "MEDIAL_CUNEIFORM": "medial cuneiform bone", "INTERMEDIATE_CUNEIFORM": "intermediate cuneiform bone",
                "LATERAL_CUNEIFORM": "lateral cuneiform bone"}
_REGION = {"C": "cervical", "T": "thoracic", "L": "lumbar"}


def _split(stem: str) -> tuple[str, str]:
    """('FEMUR', 'left') for 'FEMUR_LEFT'; ('VERTEBRA_T5', 'none') for midline bones."""
    match = re.fullmatch(r"(.+)_(LEFT|RIGHT)", stem)
    return (match.group(1), match.group(2).lower()) if match else (stem, "none")


def bone_side(stem: str) -> str:
    return _split(stem)[1]


def bone_segment(stem: str) -> str:
    base, _ = _split(stem)
    if base.startswith(("VERTEBRA_", "RIB_")) or base in {"SACRUM", "STERNUM", "SKULL_CRANIAL_MAXILLA",
                                                          "SKULL_MANDIBLE"}:
        return "trunk"
    if base in _LIMB:
        return _LIMB[base]
    if base in _FOOT or base.startswith(("METATARSAL_", "PHALANGE_FOOT_")):
        return "foot"
    if base in _HAND or base.startswith(("METACARPAL_", "PHALANGE_HAND_")):
        return "hand"
    raise ValueError(f"tulang BoneHub tidak dikenal: {stem}")


def bone_name_en(stem: str) -> str:
    base, side = _split(stem)
    bone_segment(stem)  # raises on unknown stems
    fixed = {"VERTEBRA_C1": "Atlas", "VERTEBRA_C2": "Axis", "SACRUM": "Sacrum and coccyx", "STERNUM": "Sternum",
             "SKULL_CRANIAL_MAXILLA": "Cranium and maxilla", "SKULL_MANDIBLE": "Mandible"}
    if base in fixed:
        return fixed[base]
    vertebra = re.fullmatch(r"VERTEBRA_([CTL])(\d+)", base)
    if vertebra:
        return f"{ORDINALS[int(vertebra.group(2)) - 1].capitalize()} {_REGION[vertebra.group(1)]} vertebra"
    if base == "NAVICULAR":
        return f"Navicular bone of {side} foot"
    numbered = re.fullmatch(r"(RIB|METATARSAL|METACARPAL|PHALANGE_HAND|PHALANGE_FOOT)_(\d+)", base)
    if numbered:
        kind, n = numbered.group(1), int(numbered.group(2))
        if kind == "PHALANGE_HAND":
            return f"Phalanges of {side} {FINGERS[n - 1]}"
        if kind == "PHALANGE_FOOT":
            return f"Phalanges of {side} {TOES[n - 1]}"
        noun = {"RIB": "rib", "METATARSAL": "metatarsal bone", "METACARPAL": "metacarpal bone"}[kind]
        return f"{side.capitalize()} {ORDINALS[n - 1]} {noun}"
    return f"{side.capitalize()} {_PLAIN_NAMES.get(base, base.lower())}"


def find_bonehub(raw_dir: Path) -> dict[str, Path]:
    """Stem → STL path for the downloaded female bones under raw_dir/bonehub/02_Female/."""
    return {path.stem: path for path in sorted((raw_dir / "bonehub" / "02_Female").glob("*/*.stl"))}


def load_bonehub(paths: dict[str, Path]) -> dict[str, trimesh.Trimesh]:
    """STL files (mm, CT frame) as meshes in metres with atlas axes, still in the CT frame."""
    bones = {}
    for stem, path in sorted(paths.items()):
        mesh = trimesh.load(path, file_type="stl", process=True, force="mesh")  # merges the per-face STL vertices
        bones[stem] = trimesh.Trimesh(to_atlas_space(mesh.vertices), mesh.faces, process=False)
    return bones
