import numpy as np
import trimesh

from atlas_pipeline.warp import ThinPlateWarp, sample_control_points


def test_tps_interpolates_controls():
    rng = np.random.default_rng(1)
    src = rng.uniform(-1, 1, (50, 3))
    dst = src + rng.normal(0, 0.05, (50, 3))
    assert np.allclose(ThinPlateWarp.fit(src, dst)(src), dst, atol=1e-6)


def test_tps_reproduces_affine_maps_far_from_controls():
    rng = np.random.default_rng(2)
    src = rng.uniform(-1, 1, (40, 3))
    A = np.array([[1.1, 0.1, 0], [0, 0.9, 0.2], [0, 0, 1.0]])
    b = np.array([0.3, 0, -0.1])
    far = rng.uniform(-5, 5, (100, 3))
    assert np.allclose(ThinPlateWarp.fit(src, src @ A.T + b)(far), far @ A.T + b, atol=1e-6)


def test_control_points_are_deterministic():
    box = trimesh.creation.box()
    a = sample_control_points(box.vertices, box.faces, 30, seed=3)
    assert a.shape == (30, 3) and np.array_equal(a, sample_control_points(box.vertices, box.faces, 30, seed=3))
