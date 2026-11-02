import pytest

from atlas_pipeline.bp3d_tables import ElementConcepts
from atlas_pipeline.systems import classify


def ec(isa=(), partof=()):
    return ElementConcepts(frozenset(isa), frozenset(partof))


@pytest.mark.parametrize("concepts,name,expected", [
    (ec(isa={"FMA50720"}, partof={"FMA7088"}), "Right coronary artery", ("arterial", "isa-artery")),
    (ec(isa={"FMA50723"}), "Great saphenous vein", ("venous", "isa-vein")),
    (ec(partof={"FMA7088"}), "Wall of left atrium", ("cardiac", "partof-heart")),
    (ec(partof={"FMA7157"}), "Left lateral ventricle", ("nervous", "nervous")),
    (ec(isa={"FMA5022"}, partof={"FMA7158"}), "Left inferior pharyngeal constrictor", ("muscular", "isa-muscle")),
    (ec(isa={"FMA55107"}, partof={"FMA7158"}), "Thyroid cartilage", ("respiratory", "partof-respiratory")),
    (ec(isa={"FMA55107"}), "Costal cartilage of first rib", ("connective", "connective")),
    (ec(), "Left kidney", ("urinary", "name-urinary")),
    (ec(), "Mystery tissue", ("connective", "default")),
    # Real BodyParts3D elements that the first rule set left unclassified.
    (ec(isa={"FMA86187"}), "Ascending branch of left colic artery", ("arterial", "isa-artery")),
    (ec(), "Abdominal aorta", ("arterial", "name-artery")),
    (ec(), "Dorsal metacarpal vein", ("venous", "name-vein")),
    (ec(), "Left superficial palmar venous arch", ("venous", "name-vein")),
    (ec(isa={"FMA85453"}), "Lateral head of left gastrocnemius", ("muscular", "isa-muscle")),
    (ec(isa={"FMA83143"}), "Left putamen", ("nervous", "nervous")),
    (ec(), "Left optic tract", ("nervous", "name-nervous")),
    (ec(isa={"FMA55107"}), "Thyroid cartilage", ("respiratory", "name-larynx")),
    (ec(isa={"FMA21496"}), "Left long plantar ligament", ("connective", "connective")),
    (ec(), "Left iliotibial tract", ("connective", "name-connective")),
    (ec(), "Hair of head", ("integumentary", "integument")),
    (ec(), "Left deferent duct", ("reproductive", "name-genital")),
    (ec(), "Manubrium", ("skeletal", "name-skeletal")),
    (ec(), "External ear", ("sensory", "sensory")),
    (ec(), "Lip", ("digestive", "name-digestive")),
    (ec(), "Ascending part of left trapezius", ("muscular", "name-muscle")),
    (ec(), "Left corona ciliaris", ("sensory", "sensory")),
    (ec(), "Wall of ventricle", ("cardiac", "name-heart")),
    (ec(), "Left ciliary ganglion", ("nervous", "name-nervous")),
    # Liver segments and ducts: "hepatovenous" and "caudate lobe" are not veins or brain nuclei.
    (ec(), "Hepatovenous segment IX", ("digestive", "name-digestive")),
    (ec(partof={"FMA7152"}), "Hepatovenous segment II", ("digestive", "partof-alimentary")),
    (ec(), "Left duct of caudate lobe of liver", ("digestive", "name-digestive")),
    (ec(), "Right caudate nucleus", ("nervous", "name-nervous")),
])
def test_classify_follows_rule_order(concepts, name, expected):
    assert classify(concepts, name) == expected
