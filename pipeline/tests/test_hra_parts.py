import numpy as np
import pytest

from atlas_pipeline.checks import coincident_pairs
from atlas_pipeline.hra_glb import HraMesh, read_hra_glb
from atlas_pipeline.hra_parts import (ALLOWED_OVERLAPS, classify_hra, hra_english_name, hra_ontology, hra_side,
                                      hra_to_parts)


def m(*path, label=None):
    return HraMesh(path[-1], ("VH_F",) + path, label, None, np.zeros((3, 3)), np.array([[0, 1, 2]]))


@pytest.mark.parametrize("mesh,expected", [
    (m("VH_F_reproductive_system", "VH_F_placenta", "VH_F_amnion"), (None, "placenta")),
    (m("VH_F_lower_limb", "VH_F_lower_limb_L", "VH_F_knee_L", "VH_F_knee_joint_L", "VH_F_femur_L", "VH_F_articular_cartilage_of_knee_L"), (None, "dup-bone")),
    (m("VH_F_skeletal_system", "VH_F_vertebral_column", "VH_F_vertebra", "VH_F_thoracic_vertebra_5"), (None, "dup-bone")),
    (m("VH_F_skeletal_system", "VH_F_vertebral_column", "VH_F_intervertebral_joint", "VH_F_intervertebral_disk_of_third_lumbar_vertebra"), ("connective", "group")),
    (m("VH_F_lower_limb", "VH_F_lower_limb_L", "VH_F_ligaments_of_knee_L", "VH_F_anterior_cruciate_ligament_of_knee_L"), (None, "dup-andreassen")),
    (m("VH_F_lower_limb", "VH_F_lower_limb_L", "VH_F_knee_L", "VH_F_knee_joint_L", "VH_F_meniscus_L"), ("connective", "group")),
    (m("VH_F_lymphatic_system", "Yao_lymph_node", "Yao_blood_vasculature"), ("lymphatic", "lymph-node")),
    (m("VH_F_circulatory_system", "VH_F_heart", "VH_F_valve", "VH_F_mitral_valve"), ("cardiac", "heart")),
    (m("VH_F_circulatory_system", "VH_F_blood_vasculature", "VH_F_pulmonary_trunk"), ("arterial", "artery")),
    (m("VH_F_circulatory_system", "VH_F_blood_vasculature", "VH_F_coronary_sinus"), ("venous", "vein")),
    (m("VH_F_circulatory_system", "VH_F_blood_vasculature", "VH_F_left_marginal_branch"), ("arterial", "artery")),
    (m("VH_F_circulatory_system", "VH_F_blood_vasculature", "VH_F_right_branch_of_portal_vein"), ("venous", "vein")),
    (m("VH_F_lymphatic_system", "VH_F_spleen", "VH_F_splenic_vein"), ("venous", "vein")),
    (m("VH_F_nervous_system", "VH_F_eyes", "VH_F_lens_L"), ("sensory", "eye")),
    (m("VH_F_digestive_system", "VH_F_palatine_tonsil", "VH_F_palatine_tonsil_L"), ("lymphatic", "tonsil")),
    (m("VH_F_muscular_system", "VH_F_muscles_of_knee", "VH_F_muscles_of_knee_L", "VH_F_tendon_of_quadriceps_femoris_L"), ("connective", "tendon")),
    (m("VH_F_digestive_system", "VH_F_liver", "VH_F_gastric_impression_of_liver"), (None, "dup-surface")),
])
def test_classify_hra_follows_rule_order(mesh, expected):
    assert classify_hra(mesh) == expected


def test_unknown_vessel_is_an_error():
    with pytest.raises(ValueError, match="VH_F_mystery_duct"):
        classify_hra(m("VH_F_circulatory_system", "VH_F_blood_vasculature", "VH_F_mystery_duct"))


@pytest.mark.parametrize("node,side", [("VH_F_L_lung_upper_lobe", "left"), ("Allen_corpus_callosum_R", "right"),
    ("VH_F_left_renal_artery", "left"), ("VH_F_renal_papilla_L_k", "left"), ("VH_F_trachea", "none"), ("VH_F_Lymph", "none")])
def test_hra_side(node, side):
    assert hra_side(node) == side


@pytest.mark.parametrize("node,label,name", [
    ("VH_F_ora_serrata_of_retina_L", "Left ora serrata", "Left ora serrata"),
    ("VH_F_renal_papilla_L_k", "renal papilla", "Left renal papilla (k)"),
    ("Allen_cerebral_aqueduct_L", None, "Left cerebral aqueduct"),
    ("VH_F_descending_aorta_a", None, "Descending aorta (a)"),
    ("VH_F_right_ureter", None, "Right ureter"),
])
def test_hra_english_name(node, label, name):
    assert hra_english_name(node, label) == name


def test_hra_ontology():
    assert hra_ontology("FMA:58602") == ("FMA58602", None)
    assert hra_ontology("UBERON:0002336") == (None, "UBERON:0002336")
    assert hra_ontology(None) == (None, None)


def test_hra_to_parts_builds_parts_and_lists_exclusions():
    keep = HraMesh("VH_F_left_ureter", ("VH_F", "VH_F_urinary_system", "VH_F_left_ureter"), None, "FMA:3",
                   np.array([[0.1, 0, 0], [0.11, 0, 0], [0.1, 0.1, 0]]), np.array([[0, 1, 2]]))
    drop = m("VH_F_reproductive_system", "VH_F_placenta", "VH_F_amnion")
    parts, excluded = hra_to_parts([keep, drop])
    (part,) = parts
    assert (part.id, part.system, part.side, part.origin, part.source, part.fma) == (
        "HRA:VH_F_left_ureter", "urinary", "left", "perempuan-asli", "hra", "FMA3")
    assert part.names == {"en": "Left ureter"}
    assert excluded == [{"node": "VH_F_amnion", "reason": "placenta"}]


@pytest.mark.realdata
def test_real_hra_has_no_unresolved_coincident_surfaces(raw_dir):
    parts, excluded = hra_to_parts(read_hra_glb(raw_dir / "hra" / "3d-vh-f-united.glb"))
    system = {p.id: p.system for p in parts}
    pairs = coincident_pairs([(p.id, p.vertices, p.faces) for p in parts])
    unresolved = [p for p in pairs if system[p[0]] != system[p[1]] and frozenset(p[:2]) not in ALLOWED_OVERLAPS]
    assert unresolved == [], unresolved
    assert not [p for p in parts if p.system is None]
