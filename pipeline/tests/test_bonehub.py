import pytest

from atlas_pipeline.bonehub import bone_name_en, bone_segment, bone_side


@pytest.mark.parametrize("stem,name,side,segment", [
    ("VERTEBRA_C1", "Atlas", "none", "trunk"), ("VERTEBRA_L6", "Sixth lumbar vertebra", "none", "trunk"),
    ("VERTEBRA_C3", "Third cervical vertebra", "none", "trunk"), ("VERTEBRA_T12", "Twelfth thoracic vertebra", "none", "trunk"),
    ("RIB_8_LEFT", "Left eighth rib", "left", "trunk"), ("HIP_RIGHT", "Right hip bone", "right", "trunk"),
    ("FEMUR_LEFT", "Left femur", "left", "thigh"), ("FIBULA_RIGHT", "Right fibula", "right", "shank"),
    ("PATELLA_LEFT", "Left patella", "left", "patella"),
    ("NAVICULAR_LEFT", "Navicular bone of left foot", "left", "foot"),
    ("PHALANGE_FOOT_1_RIGHT", "Phalanges of right big toe", "right", "foot"),
    ("MEDIAL_CUNEIFORM_LEFT", "Left medial cuneiform bone", "left", "foot"),
    ("METATARSAL_1_LEFT", "Left first metatarsal bone", "left", "foot"),
    ("CLAVICLE_LEFT", "Left clavicle", "left", "girdle"), ("ULNA_LEFT", "Left ulna", "left", "forearm"),
    ("HUMERUS_RIGHT", "Right humerus", "right", "upperarm"),
    ("TRIQUETRUM_RIGHT", "Right triquetral", "right", "hand"),
    ("METACARPAL_5_RIGHT", "Right fifth metacarpal bone", "right", "hand"),
    ("PHALANGE_HAND_3_LEFT", "Phalanges of left middle finger", "left", "hand"),
    ("SKULL_CRANIAL_MAXILLA", "Cranium and maxilla", "none", "trunk"), ("SKULL_MANDIBLE", "Mandible", "none", "trunk"),
    ("SACRUM", "Sacrum and coccyx", "none", "trunk"), ("STERNUM", "Sternum", "none", "trunk"),
    ("CUBOID_LEFT", "Left cuboid bone", "left", "foot"),
])
def test_bone_tables(stem, name, side, segment):
    assert (bone_name_en(stem), bone_side(stem), bone_segment(stem)) == (name, side, segment)


def test_unknown_stem_is_an_error():
    with pytest.raises(ValueError, match="WISHBONE"):
        bone_segment("WISHBONE_LEFT")


def test_find_bonehub_maps_stems_to_files(tmp_path):
    from atlas_pipeline.bonehub import find_bonehub
    (tmp_path / "bonehub" / "02_Female" / "THORAX").mkdir(parents=True)
    (tmp_path / "bonehub" / "02_Female" / "THORAX" / "STERNUM.stl").write_text("solid\nendsolid\n")
    assert find_bonehub(tmp_path) == {"STERNUM": tmp_path / "bonehub" / "02_Female" / "THORAX" / "STERNUM.stl"}
