import numpy as np
from atlas_pipeline.obj_mesh import parse_obj, side_from_name, to_atlas_space

SAMPLE = """#
# File ID : FJ9999
# Concept ID : FMA12345
# English name : Left test bone
v 0 0 0
v 10 0 0
v 10 10 0
v 0 10 0
vn 0 0 1
vn 0 0 1
vn 0 0 1
vn 0 0 1
f 1//1 2//2 3//3 4//4
"""


def test_parse_obj_reads_header_and_triangulates():
    mesh = parse_obj(SAMPLE)
    assert (mesh.file_id, mesh.concept_id, mesh.name_en) == ("FJ9999", "FMA12345", "Left test bone")
    assert mesh.positions_mm.shape == (4, 3)
    assert mesh.faces.tolist() == [[0, 1, 2], [0, 2, 3]]


def test_to_atlas_space_maps_axes_to_meters_y_up():
    out = to_atlas_space(np.array([[10.0, -100.0, 1500.0]]))
    assert np.allclose(out, [[0.010, 1.5, 0.1]])


def test_side_from_name():
    assert side_from_name("Left femur") == "left"
    assert side_from_name("Right coronary artery") == "right"
    assert side_from_name("Branch of left middle cerebral artery") == "left"
    assert side_from_name("Sternum") == "none"
    assert side_from_name("Leftover tissue") == "none"
