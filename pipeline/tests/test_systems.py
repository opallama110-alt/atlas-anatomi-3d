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
])
def test_classify_follows_rule_order(concepts, name, expected):
    assert classify(concepts, name) == expected
