import numpy as np
import trimesh

from atlas_pipeline.skin_field import SkinField


def test_signed_distance_and_clamp_on_a_sphere():
    s = trimesh.creation.icosphere(subdivisions=4, radius=0.1)
    field = SkinField(s.vertices, s.faces, samples=50_000)
    d = field.signed(np.array([[0, 0, 0], [0.12, 0, 0]]))
    assert abs(d[0] + 0.1) < 0.003 and abs(d[1] - 0.02) < 0.003
    assert abs(np.linalg.norm(field.clamp_inside(np.array([[0, 0.13, 0]]))) - 0.099) < 0.003


def test_clamp_leaves_points_already_inside():
    s = trimesh.creation.icosphere(subdivisions=4, radius=0.1)
    field = SkinField(s.vertices, s.faces, samples=50_000)
    inside = np.array([[0.0, 0.02, 0.0]])
    assert np.array_equal(field.clamp_inside(inside), inside)
