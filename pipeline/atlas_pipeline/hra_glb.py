"""Read the HuBMAP HRA united-female GLB into world-space meshes, keeping node names and `extras`.

The reader is written by hand (JSON chunk plus a memory-mapped BIN chunk) because general loaders drop the
per-node `extras` that carry HRA's labels and ontology IDs.
"""
from __future__ import annotations

import json
import struct
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from scipy.spatial.transform import Rotation

_DTYPES = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
_WIDTH = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}


@dataclass(frozen=True)
class HraMesh:
    node: str
    path: tuple[str, ...]
    label: str | None
    ontology: str | None
    vertices: np.ndarray
    faces: np.ndarray


def _clean(value: object) -> str | None:
    text = str(value).strip() if value is not None else ""
    return None if text in ("", "-") else text


def _local_matrix(node: dict) -> np.ndarray:
    if "matrix" in node:
        return np.array(node["matrix"], dtype=np.float64).reshape(4, 4).T
    matrix = np.eye(4)
    rotation = Rotation.from_quat(node.get("rotation", [0, 0, 0, 1])).as_matrix()
    matrix[:3, :3] = rotation @ np.diag(node.get("scale", [1, 1, 1]))
    matrix[:3, 3] = node.get("translation", [0, 0, 0])
    return matrix


def _read_chunks(path: Path) -> tuple[dict, np.memmap]:
    with path.open("rb") as handle:
        magic, version, _ = struct.unpack("<III", handle.read(12))
        if magic != 0x46546C67 or version != 2:
            raise ValueError(f"{path.name}: bukan GLB versi 2")
        json_length, _ = struct.unpack("<II", handle.read(8))
        document = json.loads(handle.read(json_length).decode("utf-8"))
        bin_offset = 12 + 8 + json_length + 8
    binary = np.memmap(path, dtype=np.uint8, mode="r", offset=bin_offset)
    return document, binary


def _accessor(document: dict, binary: np.memmap, index: int) -> np.ndarray:
    accessor = document["accessors"][index]
    view = document["bufferViews"][accessor["bufferView"]]
    dtype = np.dtype(_DTYPES[accessor["componentType"]])
    width = _WIDTH[accessor["type"]]
    stride = view.get("byteStride", width * dtype.itemsize)
    start = view.get("byteOffset", 0) + accessor.get("byteOffset", 0)
    count = accessor["count"]
    raw = binary[start:start + stride * (count - 1) + width * dtype.itemsize]
    array = np.ndarray((count, width), dtype=dtype, buffer=np.ascontiguousarray(raw).data,
                       strides=(stride, dtype.itemsize))
    return np.array(array)


def read_hra_glb(path: Path) -> list[HraMesh]:
    document, binary = _read_chunks(path)
    nodes = document["nodes"]
    out: list[tuple[int, HraMesh]] = []

    def walk(index: int, parent: np.ndarray, ancestors: tuple[str, ...]) -> None:
        node = nodes[index]
        world = parent @ _local_matrix(node)
        here = ancestors + (node.get("name", f"node{index}"),)
        if "mesh" in node:
            vertices, faces, offset = [], [], 0
            for primitive in document["meshes"][node["mesh"]]["primitives"]:
                positions = _accessor(document, binary, primitive["attributes"]["POSITION"]).astype(np.float64)
                if "indices" in primitive:
                    triangles = _accessor(document, binary, primitive["indices"]).reshape(-1, 3).astype(np.int64)
                else:
                    triangles = np.arange(len(positions), dtype=np.int64).reshape(-1, 3)
                vertices.append(positions)
                faces.append(triangles + offset)
                offset += len(positions)
            stacked = np.concatenate(vertices)
            world_positions = stacked @ world[:3, :3].T + world[:3, 3]
            extras = node.get("extras", {})
            out.append((index, HraMesh(here[-1], here, _clean(extras.get("label")), _clean(extras.get("ontologyid")),
                               world_positions, np.concatenate(faces))))
        for child in node.get("children", []):
            walk(child, world, here)

    scene = document["scenes"][document.get("scene", 0)]
    for root in scene["nodes"]:
        walk(root, np.eye(4), ())
    return [mesh for _, mesh in sorted(out, key=lambda item: item[0])]
