import numpy as np

from atlas_pipeline.checks import coincident_pairs


def grid(n, z=0.0, size=0.1):
    xs = np.linspace(0, size, n)
    v = np.array([[x, y, z] for x in xs for y in xs])
    f = [[i * n + j, i * n + j + 1, (i + 1) * n + j] for i in range(n - 1) for j in range(n - 1)]
    return v, np.array(f)


def test_coincident_pairs_finds_patch_on_surface_and_ignores_offset_copy():
    big_v, big_f = grid(20)
    patch_v, patch_f = grid(6, size=0.04)
    far_v, far_f = grid(6, z=0.01, size=0.04)
    pairs = coincident_pairs([("big", big_v, big_f), ("patch", patch_v, patch_f), ("far", far_v, far_f)])
    assert [(a, b) for a, b, _ in pairs] == [("patch", "big")]
