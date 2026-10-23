from pathlib import Path

from atlas_pipeline.bp3d_tables import load_element_concepts


def test_load_element_concepts_inverts_both_tables():
    concepts = load_element_concepts(Path(__file__).parent / "fixtures" / "bp3d")
    assert concepts["FJ1"].isa == frozenset({"FMA5018", "FMA62955"})
    assert concepts["FJ1"].partof == frozenset()
    assert concepts["FJ2"].partof == frozenset({"FMA7088"})
