"""Command line entry: `python -m atlas_pipeline male`."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from .fetch import fetch_bodyparts3d
from .package_body import build_male
from .wikidata import load_fma_labels

REPO = Path(__file__).resolve().parents[2]
RAW_BP3D = REPO / "data" / "raw" / "bodyparts3d"
WORK = REPO / "data" / "work"
LABEL_CACHE = REPO / "pipeline" / "cache" / "wikidata-fma-labels.json"


def main(argv: list[str]) -> int:
    if argv != ["male"]:
        print("usage: python -m atlas_pipeline male", file=sys.stderr)
        return 2
    fetch_bodyparts3d(RAW_BP3D)
    labels = load_fma_labels(LABEL_CACHE)
    manifest = build_male(RAW_BP3D, WORK, labels)
    report = json.loads((WORK / "male" / "classification-report.json").read_text(encoding="utf-8"))
    print(json.dumps({"parts": len(manifest["parts"]), "bySystem": report["bySystem"],
                      "default": len(report["default"])}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
