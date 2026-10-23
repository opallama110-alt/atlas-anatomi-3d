import json

import pytest

from atlas_pipeline import wikidata


def row(item, fma, id_label=None, la_label=None):
    r = {"item": {"value": f"http://www.wikidata.org/entity/{item}"}, "fma": {"value": fma}}
    if id_label is not None:
        r["idLabel"] = {"value": id_label}
    if la_label is not None:
        r["laLabel"] = {"value": la_label}
    return r


def test_parse_keeps_lowest_q_and_drops_empty_labels():
    payload = {"results": {"bindings": [
        row("Q2000", "7088", "jantung (duplikat)"),
        row("Q1073", "7088", " jantung ", "cor"),
        row("Q5", "5018", "", "os"),
    ]}}
    assert wikidata.parse_sparql_json(payload) == {
        "FMA7088": {"id": "jantung", "la": "cor"},
        "FMA5018": {"la": "os"},
    }


def test_load_uses_cache_without_network(tmp_path, monkeypatch):
    cache = tmp_path / "labels.json"
    cache.write_text(json.dumps({"FMA1": {"id": "x"}}), encoding="utf-8")
    monkeypatch.setattr(wikidata.urllib.request, "urlopen",
                        lambda *a, **k: pytest.fail("network used"))
    assert wikidata.load_fma_labels(cache) == {"FMA1": {"id": "x"}}
