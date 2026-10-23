"""BodyParts3D concept tables.

`isa_element_parts.txt` and `partof_element_parts.txt` list, for every concept,
the element files (FJ...) it is made of. A concept lists every element below it,
so inverting the tables gives each element its full set of ancestor concepts.
"""
from __future__ import annotations

import csv
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ElementConcepts:
    isa: frozenset[str]
    partof: frozenset[str]


def _element_to_concepts(table: Path) -> dict[str, set[str]]:
    result: dict[str, set[str]] = defaultdict(set)
    if not table.exists():
        return result
    with table.open(encoding="utf-8", newline="") as handle:
        rows = csv.reader(handle, delimiter="\t")
        next(rows, None)
        for row in rows:
            if len(row) >= 3:
                result[row[2].strip()].add(row[0].strip())
    return result


def load_element_concepts(raw_dir: Path) -> dict[str, ElementConcepts]:
    isa = _element_to_concepts(raw_dir / "isa_element_parts.txt")
    partof = _element_to_concepts(raw_dir / "partof_element_parts.txt")
    return {
        file_id: ElementConcepts(frozenset(isa.get(file_id, ())), frozenset(partof.get(file_id, ())))
        for file_id in set(isa) | set(partof)
    }
