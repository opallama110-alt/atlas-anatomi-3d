import numpy as np
from scipy.spatial.transform import Rotation

from atlas_pipeline.registration import Similarity, icp, mean_distance_mm, umeyama

R30 = Rotation.from_rotvec([0.2, 0.5, 0.1]).as_matrix()
KNOWN = Similarity(1.1, R30, np.array([0.3, -0.2, 0.05]))


def blob(seed=0):
    rng = np.random.default_rng(seed)
    p = rng.normal(size=(2000, 3)) * [0.05, 0.12, 0.03]
    return p[p[:, 0] < 0.04]                      # potong satu sisi supaya tidak simetris


def test_umeyama_recovers_similarity():
    src = blob()
    t = umeyama(src, KNOWN.apply(src))
    assert abs(t.scale - 1.1) < 1e-9 and np.allclose(t.rotation, R30) and np.allclose(t.translation, KNOWN.translation)


def test_umeyama_without_scale_keeps_unit_scale():
    src = blob()
    rigid = Similarity(1.0, R30, np.array([0.1, 0, 0]))
    t = umeyama(src, rigid.apply(src), with_scale=False)
    assert t.scale == 1.0 and np.allclose(t.rotation, R30)


def test_icp_recovers_rigid_from_partial_target():
    rigid = Similarity(1.0, Rotation.from_rotvec([0.05, 0.12, 0.02]).as_matrix(), np.array([0.01, 0.02, 0.0]))  # ±8°
    src = blob()
    dst = rigid.apply(src[src[:, 1] > -0.05])
    found = icp(src, dst, Similarity.identity(), with_scale=False, iterations=60)
    assert mean_distance_mm(src, dst, found)[0] < 1.0


def test_compose_and_inverse_round_trip():
    p = blob()[:10]
    assert np.allclose(KNOWN.inverse().compose(KNOWN).apply(p), p)
    inner = Similarity(2.0, np.eye(3), np.array([1.0, 0, 0]))
    assert np.allclose(KNOWN.compose(inner).apply(p), KNOWN.apply(inner.apply(p)))


def test_rigid_icp_keeps_the_starting_scale():
    src = blob()
    start = Similarity(1.1, np.eye(3), np.zeros(3))
    found = icp(src, start.apply(src), start, with_scale=False)
    assert found.scale == 1.1 and mean_distance_mm(src, start.apply(src), found)[0] < 1e-6
