"""Automatic checks on assembled body parts."""
from __future__ import annotations

from typing import Sequence

import numpy as np
from scipy.spatial import cKDTree


def _areas(vertices: np.ndarray, faces: np.ndarray) -> float:
    a, b, c = (vertices[faces[:, k]] for k in range(3))
    return float(np.linalg.norm(np.cross(b - a, c - a), axis=1).sum() / 2)


def point_triangle_distance(points: np.ndarray, a: np.ndarray, b: np.ndarray, c: np.ndarray) -> np.ndarray:
    """Distance from each point to its paired triangle (all arrays N×3), Ericson's closest-point regions."""
    ab, ac, ap = b - a, c - a, points - a
    d1, d2 = np.einsum("ij,ij->i", ab, ap), np.einsum("ij,ij->i", ac, ap)
    bp = points - b
    d3, d4 = np.einsum("ij,ij->i", ab, bp), np.einsum("ij,ij->i", ac, bp)
    cp = points - c
    d5, d6 = np.einsum("ij,ij->i", ab, cp), np.einsum("ij,ij->i", ac, cp)
    va, vb, vc = d3 * d6 - d5 * d4, d5 * d2 - d1 * d6, d1 * d4 - d3 * d2
    closest = np.empty_like(points)
    done = np.zeros(len(points), bool)

    def take(mask, value):
        nonlocal done
        mask = mask & ~done
        closest[mask] = value[mask]
        done |= mask

    take((d1 <= 0) & (d2 <= 0), a)
    take((d3 >= 0) & (d4 <= d3), b)
    with np.errstate(divide="ignore", invalid="ignore"):
        v = d1 / (d1 - d3)
        take((vc <= 0) & (d1 >= 0) & (d3 <= 0), a + v[:, None] * ab)
        take((d6 >= 0) & (d5 <= d6), c)
        w = d2 / (d2 - d6)
        take((vb <= 0) & (d2 >= 0) & (d6 <= 0), a + w[:, None] * ac)
        w2 = (d4 - d3) / ((d4 - d3) + (d5 - d6))
        take((va <= 0) & ((d4 - d3) >= 0) & ((d5 - d6) >= 0), b + w2[:, None] * (c - b))
        denom = 1.0 / (va + vb + vc)
        inside = a + (vb * denom)[:, None] * ab + (vc * denom)[:, None] * ac
    take(np.ones(len(points), bool), inside)
    return np.linalg.norm(points - closest, axis=1)


class SurfaceDistance:
    """Approximate distance from points to a triangle mesh: exact distance to the k triangles with nearest centroids."""

    def __init__(self, vertices: np.ndarray, faces: np.ndarray, k: int = 16):
        self.a, self.b, self.c = (vertices[faces[:, i]] for i in range(3))
        self.tree = cKDTree((self.a + self.b + self.c) / 3)
        self.k = min(k, len(faces))

    def __call__(self, points: np.ndarray) -> np.ndarray:
        _, idx = self.tree.query(points, k=self.k)
        idx = idx.reshape(len(points), -1)
        best = np.full(len(points), np.inf)
        for column in idx.T:
            best = np.minimum(best, point_triangle_distance(points, self.a[column], self.b[column], self.c[column]))
        return best


def coincident_pairs(meshes: Sequence[tuple[str, np.ndarray, np.ndarray]], tol_m: float = 0.0005,
                     min_fraction: float = 0.9) -> list[tuple[str, str, float]]:
    """Pairs (smaller, larger, fraction) where most of the smaller mesh lies on the other mesh's surface."""
    rng = np.random.default_rng(11)
    info = []
    for name, vertices, faces in meshes:
        sample = vertices if len(vertices) <= 2000 else vertices[rng.choice(len(vertices), 2000, replace=False)]
        info.append((name, vertices, faces, _areas(vertices, faces), vertices.min(axis=0), vertices.max(axis=0), sample))
    distances: dict[int, SurfaceDistance] = {}
    pairs = []
    for i, (name_a, _, _, area_a, lo_a, hi_a, sample_a) in enumerate(info):
        for j, (name_b, vertices_b, faces_b, area_b, lo_b, hi_b, _) in enumerate(info):
            if i == j or area_a > area_b or (area_a == area_b and i > j):
                continue
            if np.any(lo_a > hi_b + tol_m) or np.any(hi_a < lo_b - tol_m):
                continue
            inside_box = np.all((sample_a >= lo_b - tol_m) & (sample_a <= hi_b + tol_m), axis=1)
            if inside_box.mean() < min_fraction:
                continue
            if j not in distances:
                distances[j] = SurfaceDistance(vertices_b, faces_b)
            fraction = float(np.mean(distances[j](sample_a) <= tol_m))
            if fraction >= min_fraction:
                pairs.append((name_a, name_b, fraction))
    return pairs
