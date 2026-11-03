"""Download BodyParts3D 4.0 source files into data/raw, resuming partial files."""
from __future__ import annotations

import hashlib
import json
import time
import urllib.request
import zipfile
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


# --- Badan perempuan (tahap 2) -------------------------------------------------

HRA_FEMALE_URL = ("https://cdn.humanatlas.io/digital-objects/ref-organ/united-female/v1.10/assets/"
                  "3d-vh-f-united.glb")
HRA_FEMALE_BYTES = 374_505_632

BONEHUB_TREE_URL = ("https://huggingface.co/api/datasets/BoneHub/visible-human-3d-models/tree/main/"
                    "visible_human_3d_models/CT/Mesh/02_Female?recursive=1")
BONEHUB_FILE_URL = "https://huggingface.co/datasets/BoneHub/visible-human-3d-models/resolve/main/{path}"
_BONEHUB_ROOT = "visible_human_3d_models/CT/Mesh/"

ANDREASSEN_PAGE = "https://digitalcommons.du.edu/visiblehuman/1/"
ANDREASSEN_MIN_STL = 76


class ManualDownloadMissing(RuntimeError):
    """A raw file the site refuses to serve to scripts has not been downloaded by hand yet."""


def fetch_hra_female(raw_dir: Path) -> Path:
    target = raw_dir / "hra" / "3d-vh-f-united.glb"
    target.parent.mkdir(parents=True, exist_ok=True)
    _download(HRA_FEMALE_URL, target)
    if target.stat().st_size != HRA_FEMALE_BYTES:
        raise RuntimeError(f"{target.name}: expected {HRA_FEMALE_BYTES} bytes, got {target.stat().st_size}")
    return target


def bonehub_female_files(tree: list[dict]) -> list[tuple[str, int, str]]:
    """(path, size, sha256) of every female STL in a Hugging Face tree listing."""
    files = []
    for entry in tree:
        path = entry.get("path", "")
        if entry.get("type") != "file" or not path.lower().endswith(".stl") or "/02_Female/" not in path:
            continue
        files.append((path, int(entry["size"]), entry.get("lfs", {}).get("oid", "")))
    return sorted(files)


def verify_sha256(path: Path, expected: str) -> None:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while block := handle.read(CHUNK):
            digest.update(block)
    if digest.hexdigest() != expected:
        raise RuntimeError(f"{path.name}: sha256 {digest.hexdigest()} tidak cocok dengan {expected}")


def _json(url: str):
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=120) as response:
        return json.loads(response.read().decode("utf-8"))


RETRY_PAUSE_S = 5
RETRIES = 4


def download_known_size(url: str, target: Path, size: int) -> None:
    """Download a file whose size is already known (no HEAD request), resuming and retrying on network errors."""
    last: Exception | None = None
    for attempt in range(RETRIES):
        have = target.stat().st_size if target.exists() else 0
        if have == size:
            return
        if have > size:
            target.unlink()
            have = 0
        headers = {"User-Agent": USER_AGENT}
        if have:
            headers["Range"] = f"bytes={have}-"
        try:
            request = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(request, timeout=120) as response, target.open("ab" if have else "wb") as out:
                while block := response.read(CHUNK):
                    out.write(block)
        except (OSError, TimeoutError) as error:  # URLError and socket timeouts are OSErrors
            last = error
            time.sleep(RETRY_PAUSE_S * (attempt + 1))
    if not target.exists() or target.stat().st_size != size:
        raise RuntimeError(f"{target.name}: unduhan gagal setelah {RETRIES} kali ({last})")


def fetch_bonehub_female(raw_dir: Path) -> dict[str, Path]:
    """Download the 143 female BoneHub STL files; returns file stem → local path."""
    out: dict[str, Path] = {}
    for path, size, sha256 in bonehub_female_files(_json(BONEHUB_TREE_URL)):
        target = raw_dir / "bonehub" / path[len(_BONEHUB_ROOT):]
        target.parent.mkdir(parents=True, exist_ok=True)
        download_known_size(BONEHUB_FILE_URL.format(path=path), target, size)
        if sha256:
            verify_sha256(target, sha256)
        out[target.stem] = target
    return out


def require_andreassen(raw_dir: Path) -> Path:
    folder = raw_dir / "andreassen"
    zips = sorted(folder.glob("*.zip")) if folder.is_dir() else []
    if len(zips) == 1 and zipfile.is_zipfile(zips[0]):
        with zipfile.ZipFile(zips[0]) as archive:
            stl = [n for n in archive.namelist() if n.lower().endswith(".stl")]
        if len(stl) >= ANDREASSEN_MIN_STL:
            return zips[0]
    raise ManualDownloadMissing(
        "File otot Andreassen belum ada. Unduh sekali lewat browser:\n"
        f"1. Buka {ANDREASSEN_PAGE}\n"
        '2. Klik "Download" di samping "Final 3D STL Models (87.8 MB)".\n'
        f"3. Simpan file .zip itu di folder {folder} lalu jalankan ulang.\n"
        "Situs ini menolak unduhan otomatis, jadi langkah ini tidak bisa dilakukan skrip.")
