"""Turn BodyParts3D OBJ elements into one raw GLB per display system plus a draft manifest."""
from __future__ import annotations

import json
import re
import zipfile
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

import numpy as np

from .bp3d_tables import ElementConcepts, load_element_concepts
from .parts import Part, write_body
from .obj_mesh import parse_obj, side_from_name, to_atlas_space
from .systems import classify

ZIP_NAME = "isa_BP3D_4.0_obj_99.zip"
_NO_CONCEPTS = ElementConcepts(frozenset(), frozenset())


@dataclass
class _Element:
    file_id: str
    concept_id: str
    name_en: str
    positions: np.ndarray
    faces: np.ndarray


def _obj_texts(raw_dir: Path) -> Iterator[str]:
    folder = raw_dir / "objs"
    if folder.is_dir():
        for path in sorted(folder.glob("*.obj")):
            yield path.read_text(encoding="utf-8", errors="replace")
        return
    with zipfile.ZipFile(raw_dir / ZIP_NAME) as archive:
        for name in sorted(n for n in archive.namelist() if n.lower().endswith(".obj")):
            yield archive.read(name).decode("utf-8", errors="replace")


def _read_elements(raw_dir: Path) -> list[_Element]:
    elements = []
    for text in _obj_texts(raw_dir):
        mesh = parse_obj(text)
        if len(mesh.faces) == 0:
            raise ValueError(f"{mesh.file_id}: no triangles")
        elements.append(_Element(mesh.file_id, mesh.concept_id, mesh.name_en,
                                 to_atlas_space(mesh.positions_mm), mesh.faces))
    return sorted(elements, key=lambda e: e.file_id)


def _capitalize(name: str) -> str:
    return name[:1].upper() + name[1:]


# BodyParts3D parts whose side label contradicts where they sit (stage 1 review, minor 4).
SIDE_CORRECTIONS: dict[str, str] = {"FJ1469": "right", "FJ1469M": "left", "FJ2190": "left"}
_SWAP = {"Left": "Right", "Right": "Left", "left": "right", "right": "left"}


def _swap_side_words(name: str) -> str:
    return re.sub(r"\b(Left|Right|left|right)\b", lambda m: _SWAP[m.group(1)], name)


def read_bp3d_parts(raw_dir: Path, labels: dict[str, dict[str, str]]
                    ) -> tuple[list[Part], dict[str, str], dict[str, ElementConcepts]]:
    """BodyParts3D parts in atlas space (not yet on the floor), with the classification rule and concepts per part id."""
    elements = _read_elements(raw_dir)
    concepts = load_element_concepts(raw_dir)
    parts: list[Part] = []
    rules: dict[str, str] = {}
    concepts_by_id: dict[str, ElementConcepts] = {}
    for element in elements:
        element_concepts = concepts.get(element.file_id, _NO_CONCEPTS)
        system, rule = classify(element_concepts, element.name_en)
        part_id = f"BP3D:{element.file_id}"
        name_en = _capitalize(element.name_en)
        side = side_from_name(element.name_en)
        names = {"en": name_en, **labels.get(element.concept_id, {})}
        if element.file_id in SIDE_CORRECTIONS:
            side = SIDE_CORRECTIONS[element.file_id]
            names = {"en": _swap_side_words(name_en)}
        parts.append(Part(part_id, system, side, "laki-laki-asli", "bodyparts3d", element.file_id, names,
                          element.positions, element.faces, fma=element.concept_id))
        rules[part_id] = rule
        concepts_by_id[part_id] = element_concepts
    return parts, rules, concepts_by_id


def build_male(raw_dir: Path, work_dir: Path, labels: dict[str, dict[str, str]]) -> dict:
    parts, rules, _ = read_bp3d_parts(raw_dir, labels)
    manifest = write_body(parts, work_dir, "male")
    by_rule = Counter(rules.values())
    report = {
        "bySystem": dict(sorted(Counter(p.system for p in parts).items())),
        "byRule": dict(sorted(by_rule.items())),
        "default": [p.names["en"] for p in parts if rules[p.id] == "default"],
    }
    (work_dir / "male" / "classification-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    return manifest
