"""Download BodyParts3D 4.0 source files into data/raw, resuming partial files."""
from __future__ import annotations

import urllib.request
from pathlib import Path

BASE_URL = "https://dbarchive.biosciencedbc.jp/data/bodyparts3d/LATEST/"
BODYPARTS3D_FILES = (
    "isa_BP3D_4.0_obj_99.zip",
    "isa_parts_list_e.txt",
    "isa_inclusion_relation_list.txt",
    "isa_element_parts.txt",
    "partof_parts_list_e.txt",
    "partof_inclusion_relation_list.txt",
    "partof_element_parts.txt",
)
USER_AGENT = "atlas-anatomi-3d/0.1 (https://github.com/opallama110-alt/atlas-anatomi-3d)"
CHUNK = 1 << 20


def _remote_size(url: str) -> int:
    request = urllib.request.Request(url, method="HEAD", headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=120) as response:
        return int(response.headers["Content-Length"])


def _download(url: str, target: Path) -> None:
    expected = _remote_size(url)
    have = target.stat().st_size if target.exists() else 0
    if have == expected:
        return
    if have > expected:
        target.unlink()
        have = 0
    headers = {"User-Agent": USER_AGENT}
    if have:
        headers["Range"] = f"bytes={have}-"
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=600) as response, target.open("ab" if have else "wb") as out:
        while block := response.read(CHUNK):
            out.write(block)
    if target.stat().st_size != expected:
        raise RuntimeError(f"{target.name}: expected {expected} bytes, got {target.stat().st_size}")


def fetch_bodyparts3d(raw_dir: Path) -> None:
    raw_dir.mkdir(parents=True, exist_ok=True)
    for name in BODYPARTS3D_FILES:
        _download(BASE_URL + name, raw_dir / name)
