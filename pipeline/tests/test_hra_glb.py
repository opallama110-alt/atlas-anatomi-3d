import numpy as np
import pytest

from atlas_pipeline.hra_glb import read_hra_glb
from tests.helpers.glb import write_glb

SQUARE = (np.array([[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0]], np.float32), np.array([0, 1, 2, 0, 2, 3], np.uint16))


def test_reads_world_space_through_parent_transforms(tmp_path):
    nodes = [{"name": "VH_F", "children": [1], "translation": [0, 1, 0]},
             {"name": "VH_F_skin", "mesh": 0, "scale": [2, 2, 2],
              "rotation": [0, 0, 0.7071068, 0.7071068]}]          # 90° tentang Z
    write_glb(tmp_path / "a.glb", nodes, [SQUARE])
    (mesh,) = read_hra_glb(tmp_path / "a.glb")
    assert mesh.path == ("VH_F", "VH_F_skin")
    assert np.allclose(mesh.vertices[1], [0, 3, 0], atol=1e-6)   # (1,0,0) ×2 → putar 90° → (0,2,0) → +1 di Y
    assert mesh.faces.tolist() == [[0, 1, 2], [0, 2, 3]]


def test_reads_extras_and_dash_means_none(tmp_path):
    nodes = [{"name": "a", "mesh": 0, "extras": {"label": "Left ora serrata", "ontologyid": "FMA:58602"}},
             {"name": "b", "mesh": 0, "extras": {"label": "-", "ontologyid": "-"}}]
    write_glb(tmp_path / "b.glb", nodes, [SQUARE])
    a, b = read_hra_glb(tmp_path / "b.glb")
    assert (a.label, a.ontology) == ("Left ora serrata", "FMA:58602")
    assert (b.label, b.ontology) == (None, None)


def test_concatenates_primitives_and_applies_a_matrix(tmp_path):
    nodes = [{"name": "m", "mesh": 0, "matrix": [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 5, 0, 0, 1]}]
    write_glb(tmp_path / "c.glb", nodes, [SQUARE])
    (mesh,) = read_hra_glb(tmp_path / "c.glb")
    assert np.allclose(mesh.vertices[:, 0], [5, 6, 6, 5])


@pytest.mark.realdata
def test_real_hra_has_956_meshes_in_atlas_axes(raw_dir):
    meshes = {m.node: m for m in read_hra_glb(raw_dir / "hra" / "3d-vh-f-united.glb")}
    assert len(meshes) == 956
    skin = meshes["VH_F_skin"].vertices
    assert abs(skin[:, 1].min() + 0.793) < 0.002 and abs(skin[:, 1].max() - 0.865) < 0.002
    assert meshes["VH_F_left_apical_bronchopulmonary_segment"].vertices[:, 0].mean() > 0
    assert meshes["VH_F_sternum"].vertices[:, 2].mean() > meshes["VH_F_thoracic_vertebra_5"].vertices[:, 2].mean()
