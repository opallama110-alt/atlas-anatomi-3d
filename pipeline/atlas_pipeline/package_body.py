"""Turn BodyParts3D OBJ elements into one raw GLB per display system plus a draft manifest."""
from __future__ import annotations

import json
import zipfile
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

import numpy as np
import trimesh

from .bp3d_tables import ElementConcepts, load_element_concepts
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


def build_male(raw_dir: Path, work_dir: Path, labels: dict[str, dict[str, str]]) -> dict:
    elements = _read_elements(raw_dir)
    concepts = load_element_concepts(raw_dir)

    everything = np.concatenate([e.positions for e in elements])
    lo, hi = everything.min(axis=0), everything.max(axis=0)
    offset = np.array([(lo[0] + hi[0]) / 2, lo[1], (lo[2] + hi[2]) / 2])

    out = work_dir / "male"
    out.mkdir(parents=True, exist_ok=True)
    scenes: dict[str, trimesh.Scene] = {}
    parts = []
    by_rule: Counter[str] = Counter()
    defaults = []
    for element in elements:
        system, rule = classify(concepts.get(element.file_id, _NO_CONCEPTS), element.name_en)
        by_rule[rule] += 1
        if rule == "default":
            defaults.append(element.name_en)
        positions = element.positions - offset
        part_id = f"BP3D:{element.file_id}"
        names = {"en": _capitalize(element.name_en), **labels.get(element.concept_id, {})}
        parts.append({
            "id": part_id,
            "system": system,
            "side": side_from_name(element.name_en),
            "origin": "laki-laki-asli",
            "source": "bodyparts3d",
            "sourceRef": element.file_id,
            "fma": element.concept_id,
            "names": names,
            "bounds": [positions.min(axis=0).tolist(), positions.max(axis=0).tolist()],
            "file": f"{system}.glb",
            "triangles": int(len(element.faces)),
        })
        scene = scenes.setdefault(system, trimesh.Scene())
        scene.add_geometry(trimesh.Trimesh(positions, element.faces, process=False),
                           node_name=part_id, geom_name=part_id)

    for system, scene in scenes.items():
        (out / f"{system}.glb").write_bytes(scene.export(file_type="glb", include_normals=True))

    manifest = {"body": "male", "parts": parts}
    (out / "manifest.draft.json").write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
    report = {
        "bySystem": dict(sorted(Counter(p["system"] for p in parts).items())),
        "byRule": dict(sorted(by_rule.items())),
        "default": defaults,
    }
    (out / "classification-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1),
                                                    encoding="utf-8")
    return manifest
