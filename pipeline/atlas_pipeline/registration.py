"""Similarity transforms, Umeyama alignment and ICP between point sets (metres)."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.spatial import cKDTree


@dataclass(frozen=True)
class Similarity:
    """p ↦ scale · rotation · p + translation."""
    scale: float
    rotation: np.ndarray
    translation: np.ndarray

    @classmethod
    def identity(cls) -> "Similarity":
        return cls(1.0, np.eye(3), np.zeros(3))

    def apply(self, points: np.ndarray) -> np.ndarray:
        return self.scale * (np.asarray(points, dtype=np.float64) @ self.rotation.T) + self.translation

    def compose(self, inner: "Similarity") -> "Similarity":
        """The transform that applies `inner` first, then this one."""
        return Similarity(self.scale * inner.scale, self.rotation @ inner.rotation,
                          self.scale * (self.rotation @ inner.translation) + self.translation)

    def inverse(self) -> "Similarity":
        rotation = self.rotation.T
        return Similarity(1.0 / self.scale, rotation, -(rotation @ self.translation) / self.scale)


def rigid_with_scale(src: np.ndarray, dst: np.ndarray, scale: float) -> Similarity:
    """Best rotation and translation for a fixed scale."""
    found = umeyama(scale * np.asarray(src, dtype=np.float64), dst, with_scale=False)
    return Similarity(scale, found.rotation, found.translation)


def umeyama(src: np.ndarray, dst: np.ndarray, with_scale: bool = True) -> Similarity:
    """Least-squares similarity mapping corresponding points src[i] → dst[i]."""
    src = np.asarray(src, dtype=np.float64)
    dst = np.asarray(dst, dtype=np.float64)
    mean_src, mean_dst = src.mean(axis=0), dst.mean(axis=0)
    a, b = src - mean_src, dst - mean_dst
    u, sigma, vt = np.linalg.svd(b.T @ a / len(src))
    d = np.eye(3)
    if np.linalg.det(u @ vt) < 0:
        d[2, 2] = -1
    rotation = u @ d @ vt
    scale = float(np.trace(np.diag(sigma) @ d) / (a ** 2).sum(axis=1).mean()) if with_scale else 1.0
    return Similarity(scale, rotation, mean_dst - scale * rotation @ mean_src)


def icp(src_points: np.ndarray, dst_points: np.ndarray, init: Similarity, with_scale: bool,
        iterations: int = 40, trim: float = 0.9) -> Similarity:
    """Align src to dst (with_scale=False keeps init.scale). Every dst point is paired with its nearest transformed src point, so a dst that covers
    only part of src (e.g. HRA's ilium against BoneHub's whole hip bone) still aligns correctly."""
    src = np.asarray(src_points, dtype=np.float64)
    dst = np.asarray(dst_points, dtype=np.float64)
    tree = cKDTree(src)
    transform = init
    # Converge on all pairs first, then refine without the worst pairs: trimming from the start can stall on
    # sparse shapes, because the far points it drops are the ones that pin the rotation.
    for fraction in (1.0, trim):
        previous = np.inf
        for _ in range(iterations):
            _, idx = tree.query(transform.inverse().apply(dst))
            distance = np.linalg.norm(transform.apply(src[idx]) - dst, axis=1)
            keep = distance <= np.quantile(distance, fraction)
            transform = (umeyama(src[idx[keep]], dst[keep]) if with_scale
                         else rigid_with_scale(src[idx[keep]], dst[keep], init.scale))
            error = float(distance[keep].mean())
            if abs(previous - error) < 1e-9:
                break
            previous = error
    return transform


def mean_distance_mm(src_points: np.ndarray, dst_points: np.ndarray, transform: Similarity) -> tuple[float, float]:
    """Mean and 95th-percentile distance (mm) from each dst point to the nearest transformed src point."""
    distance, _ = cKDTree(transform.apply(src_points)).query(np.asarray(dst_points, dtype=np.float64))
    return float(distance.mean() * 1000), float(np.percentile(distance, 95) * 1000)
