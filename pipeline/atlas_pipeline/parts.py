"""One packaged body part, and the writer that turns a list of parts into GLBs per system plus a draft manifest."""
from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import numpy as np
import trimesh


@dataclass
class Part:
    """A mesh in atlas space (metres, Y up, front +Z, left +X), before the body is moved onto the floor."""
    id: str
    system: str
    side: str
    origin: str
    source: str
    source_ref: str
    names: dict[str, str]
    vertices: np.ndarray
    faces: np.ndarray
    fma: str | None = None
    uberon: str | None = None
    notes: tuple[str, ...] = ()


def body_offset(parts: list[Part]) -> np.ndarray:
    """Translation that puts the floor at y = 0 and the body's X/Z box centre at the origin."""
    everything = np.concatenate([p.vertices for p in parts])
    lo, hi = everything.min(axis=0), everything.max(axis=0)
    return np.array([(lo[0] + hi[0]) / 2, lo[1], (lo[2] + hi[2]) / 2])


def write_body(parts: list[Part], work_dir: Path, body: Literal["male", "female"]) -> dict:
    for part in parts:
        if len(part.faces) == 0:
            raise ValueError(f"{part.id}: bagian tanpa segitiga")
    offset = body_offset(parts)
    out = work_dir / body
    out.mkdir(parents=True, exist_ok=True)
    scenes: dict[str, trimesh.Scene] = defaultdict(trimesh.Scene)
    records = []
    for part in parts:
        positions = part.vertices - offset
        record = {
            "id": part.id,
            "system": part.system,
            "side": part.side,
            "origin": part.origin,
            "source": part.source,
            "sourceRef": part.source_ref,
        }
        if part.fma:
            record["fma"] = part.fma
        if part.uberon:
            record["uberon"] = part.uberon
        record["names"] = part.names
        record["bounds"] = [positions.min(axis=0).tolist(), positions.max(axis=0).tolist()]
        record["file"] = f"{part.system}.glb"
        record["triangles"] = int(len(part.faces))
        if part.notes:
            record["notes"] = list(part.notes)
        records.append(record)
        scenes[part.system].add_geometry(trimesh.Trimesh(positions, part.faces, process=False),
                                         node_name=part.id, geom_name=part.id)
    for system, scene in scenes.items():
        (out / f"{system}.glb").write_bytes(scene.export(file_type="glb", include_normals=True))
    manifest = {"body": body, "parts": records}
    (out / "manifest.draft.json").write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
    return manifest
