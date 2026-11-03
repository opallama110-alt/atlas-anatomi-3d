"""Write tiny GLB files for tests: JSON chunk plus one binary buffer."""
from __future__ import annotations

import json
import struct
from pathlib import Path

import numpy as np

_COMPONENT = {np.dtype(np.float32): 5126, np.dtype(np.uint16): 5123, np.dtype(np.uint32): 5125}


def write_glb(path: Path, nodes: list[dict], meshes: list[tuple[np.ndarray, np.ndarray]]) -> None:
    blob = bytearray()
    views, accessors, gltf_meshes = [], [], []

    def add(array: np.ndarray, kind: str, target: int) -> int:
        while len(blob) % 4:
            blob.append(0)
        data = np.ascontiguousarray(array).tobytes()
        views.append({"buffer": 0, "byteOffset": len(blob), "byteLength": len(data), "target": target})
        blob.extend(data)
        accessor = {"bufferView": len(views) - 1, "componentType": _COMPONENT[array.dtype],
                    "count": int(array.shape[0]) if kind == "VEC3" else int(array.size), "type": kind}
        if kind == "VEC3":
            accessor["min"] = array.min(axis=0).tolist()
            accessor["max"] = array.max(axis=0).tolist()
        accessors.append(accessor)
        return len(accessors) - 1

    for positions, indices in meshes:
        pos = add(np.asarray(positions, np.float32), "VEC3", 34962)
        idx = add(np.asarray(indices).reshape(-1), "SCALAR", 34963)
        gltf_meshes.append({"primitives": [{"attributes": {"POSITION": pos}, "indices": idx}]})
    children = {c for n in nodes for c in n.get("children", [])}
    roots = [i for i in range(len(nodes)) if i not in children]
    document = {"asset": {"version": "2.0"}, "scene": 0, "scenes": [{"nodes": roots}], "nodes": nodes,
                "meshes": gltf_meshes, "accessors": accessors, "bufferViews": views,
                "buffers": [{"byteLength": len(blob)}]}
    text = json.dumps(document).encode("utf-8")
    text += b" " * (-len(text) % 4)
    while len(blob) % 4:
        blob.append(0)
    total = 12 + 8 + len(text) + 8 + len(blob)
    with path.open("wb") as out:
        out.write(struct.pack("<III", 0x46546C67, 2, total))
        out.write(struct.pack("<II", len(text), 0x4E4F534A) + text)
        out.write(struct.pack("<II", len(blob), 0x004E4942) + bytes(blob))
