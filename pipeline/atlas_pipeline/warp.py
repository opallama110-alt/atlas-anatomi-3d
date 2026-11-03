"""Smooth space deformation (thin-plate spline) from matched control points."""
from __future__ import annotations

import numpy as np
import trimesh
from scipy.interpolate import RBFInterpolator

_BUDGET = 4_000_000  # kernel entries evaluated at once (~32 MB)


class ThinPlateWarp:
    def __init__(self, rbf: RBFInterpolator, controls: int):
        self._rbf = rbf
        self._chunk = max(1, _BUDGET // max(1, controls))

    @classmethod
    def fit(cls, sources: np.ndarray, targets: np.ndarray, smoothing: float = 0.0) -> "ThinPlateWarp":
        sources = np.asarray(sources, dtype=np.float64)
        displacement = np.asarray(targets, dtype=np.float64) - sources
        rbf = RBFInterpolator(sources, displacement, kernel="thin_plate_spline", degree=1, smoothing=smoothing)
        return cls(rbf, len(sources))

    def __call__(self, points: np.ndarray) -> np.ndarray:
        points = np.asarray(points, dtype=np.float64)
        out = np.empty_like(points)
        for start in range(0, len(points), self._chunk):
            block = points[start:start + self._chunk]
            out[start:start + self._chunk] = block + self._rbf(block)
        return out


def sample_control_points(vertices: np.ndarray, faces: np.ndarray, count: int, seed: int) -> np.ndarray:
    mesh = trimesh.Trimesh(vertices, faces, process=False)
    points, _ = trimesh.sample.sample_surface_even(mesh, count, seed=seed)
    if len(points) < count:
        extra, _ = trimesh.sample.sample_surface(mesh, count - len(points), seed=seed)
        points = np.concatenate([points, extra])
    return np.asarray(points[:count], dtype=np.float64)
