"""Signed distance to the skin, from a dense sample of its surface (positive outside)."""
from __future__ import annotations

import numpy as np
import trimesh
from scipy.spatial import cKDTree


class SkinField:
    def __init__(self, vertices: np.ndarray, faces: np.ndarray, samples: int = 800_000, seed: int = 7):
        mesh = trimesh.Trimesh(vertices, faces, process=False)
        points, face_index = trimesh.sample.sample_surface(mesh, samples, seed=seed)
        self.points = np.asarray(points, dtype=np.float64)
        self.normals = np.asarray(mesh.face_normals[face_index], dtype=np.float64)
        self._tree = cKDTree(self.points)

    def _nearest(self, points: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        points = np.asarray(points, dtype=np.float64)
        _, index = self._tree.query(points)
        return points, index

    def signed(self, points: np.ndarray) -> np.ndarray:
        points, index = self._nearest(points)
        return np.einsum("ij,ij->i", points - self.points[index], self.normals[index])

    def clamp_inside(self, points: np.ndarray, margin: float = 0.001) -> np.ndarray:
        points, index = self._nearest(points)
        signed = np.einsum("ij,ij->i", points - self.points[index], self.normals[index])
        out = points.copy()
        mask = signed > -margin
        out[mask] -= (signed[mask] + margin)[:, None] * self.normals[index[mask]]
        return out
