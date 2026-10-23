"""Read BodyParts3D OBJ files and move their geometry into atlas space.

BodyParts3D stores millimetres with Z up and the front of the body at -Y.
The atlas uses metres with Y up and the body facing +Z.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

import numpy as np

_HEADER = re.compile(r"^#\s*(File ID|Concept ID|English name)\s*:\s*(.*?)\s*$")
_LEFT = re.compile(r"\bleft\b", re.IGNORECASE)
_RIGHT = re.compile(r"\bright\b", re.IGNORECASE)


@dataclass(frozen=True)
class ObjMesh:
    file_id: str
    concept_id: str
    name_en: str
    positions_mm: np.ndarray
    faces: np.ndarray


def parse_obj(text: str) -> ObjMesh:
    header: dict[str, str] = {}
    positions: list[tuple[float, float, float]] = []
    faces: list[tuple[int, int, int]] = []
    for line in text.splitlines():
        if line.startswith("#"):
            match = _HEADER.match(line)
            if match:
                header[match.group(1)] = match.group(2)
        elif line.startswith("v "):
            x, y, z = line.split()[1:4]
            positions.append((float(x), float(y), float(z)))
        elif line.startswith("f "):
            polygon = [int(token.split("/")[0]) - 1 for token in line.split()[1:]]
            for j in range(1, len(polygon) - 1):
                faces.append((polygon[0], polygon[j], polygon[j + 1]))
    return ObjMesh(
        file_id=header.get("File ID", ""),
        concept_id=header.get("Concept ID", ""),
        name_en=header.get("English name", ""),
        positions_mm=np.asarray(positions, dtype=np.float64).reshape(-1, 3),
        faces=np.asarray(faces, dtype=np.int64).reshape(-1, 3),
    )


def to_atlas_space(positions_mm: np.ndarray) -> np.ndarray:
    """Map (x, y, z) millimetres to (x, z, -y) metres, without translation."""
    x, y, z = positions_mm[:, 0], positions_mm[:, 1], positions_mm[:, 2]
    return np.stack([x, z, -y], axis=1) * 0.001


def side_from_name(name_en: str) -> Literal["left", "right", "none"]:
    if _LEFT.search(name_en):
        return "left"
    if _RIGHT.search(name_en):
        return "right"
    return "none"
