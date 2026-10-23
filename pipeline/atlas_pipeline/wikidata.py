"""Indonesian and Latin anatomy labels from Wikidata (CC0), keyed by FMA ID.

Wikidata records the Foundational Model of Anatomy identifier as property P1402,
so a structure's FMA concept joins to its Wikidata item exactly, without
matching on names.
"""
from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from pathlib import Path

ENDPOINT = "https://query.wikidata.org/sparql"
USER_AGENT = "atlas-anatomi-3d/0.1 (https://github.com/opallama110-alt/atlas-anatomi-3d)"

SPARQL = """
SELECT ?item ?fma ?idLabel ?laLabel WHERE {
  ?item wdt:P1402 ?fma .
  OPTIONAL { ?item rdfs:label ?idLabel . FILTER(LANG(?idLabel) = "id") }
  OPTIONAL { ?item rdfs:label ?laLabel . FILTER(LANG(?laLabel) = "la") }
}
"""

_Q = re.compile(r"Q(\d+)$")
_DIGITS = re.compile(r"(\d+)")


def _value(binding: dict, key: str) -> str:
    return binding.get(key, {}).get("value", "").strip()


def parse_sparql_json(payload: dict) -> dict[str, dict[str, str]]:
    best: dict[str, tuple[int, dict[str, str]]] = {}
    for binding in payload.get("results", {}).get("bindings", []):
        q_match = _Q.search(_value(binding, "item"))
        fma_match = _DIGITS.search(_value(binding, "fma"))
        if not q_match or not fma_match:
            continue
        key = "FMA" + fma_match.group(1)
        q_number = int(q_match.group(1))
        labels = {lang: text for lang, text in (("id", _value(binding, "idLabel")), ("la", _value(binding, "laLabel")))
                  if text}
        if key not in best or q_number < best[key][0]:
            best[key] = (q_number, labels)
    return {key: labels for key, (_, labels) in best.items() if labels}


def fetch_sparql() -> dict:
    url = ENDPOINT + "?" + urllib.parse.urlencode({"query": SPARQL})
    request = urllib.request.Request(url, headers={
        "Accept": "application/sparql-results+json",
        "User-Agent": USER_AGENT,
    })
    with urllib.request.urlopen(request, timeout=300) as response:
        return json.loads(response.read().decode("utf-8"))


def load_fma_labels(cache: Path, refresh: bool = False) -> dict[str, dict[str, str]]:
    if cache.exists() and not refresh:
        return json.loads(cache.read_text(encoding="utf-8"))
    labels = parse_sparql_json(fetch_sparql())
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(labels, ensure_ascii=False, sort_keys=True, indent=1) + "\n", encoding="utf-8")
    return labels
