import zipfile

import pytest

from atlas_pipeline import fetch


def test_bonehub_listing_keeps_only_female_stl():
    tree = [
        {"type": "file", "path": "visible_human_3d_models/CT/Mesh/02_Female/THORAX/STERNUM.stl", "size": 3, "lfs": {"oid": "ab"}},
        {"type": "file", "path": "visible_human_3d_models/CT/Mesh/01_Male/THORAX/STERNUM.stl", "size": 3, "lfs": {"oid": "cd"}},
        {"type": "file", "path": "visible_human_3d_models/CT/Mesh/02_Female/README.md", "size": 1},
        {"type": "directory", "path": "visible_human_3d_models/CT/Mesh/02_Female/THORAX"},
    ]
    assert fetch.bonehub_female_files(tree) == [
        ("visible_human_3d_models/CT/Mesh/02_Female/THORAX/STERNUM.stl", 3, "ab")]


def test_require_andreassen_explains_manual_download(tmp_path):
    with pytest.raises(fetch.ManualDownloadMissing) as err:
        fetch.require_andreassen(tmp_path)
    message = str(err.value)
    assert fetch.ANDREASSEN_PAGE in message and "Final 3D STL Models" in message
    assert str(tmp_path / "andreassen") in message


def test_require_andreassen_accepts_zip_with_stl(tmp_path):
    folder = tmp_path / "andreassen"
    folder.mkdir()
    with zipfile.ZipFile(folder / "vhf.zip", "w") as z:
        for i in range(76):
            z.writestr(f"Left/Muscles/m{i}.stl", "solid x\nendsolid x\n")
    assert fetch.require_andreassen(tmp_path) == folder / "vhf.zip"


def test_require_andreassen_rejects_a_zip_without_enough_stl(tmp_path):
    folder = tmp_path / "andreassen"
    folder.mkdir()
    with zipfile.ZipFile(folder / "vhf.zip", "w") as z:
        z.writestr("readme.txt", "x")
    with pytest.raises(fetch.ManualDownloadMissing):
        fetch.require_andreassen(tmp_path)


def test_sha256_mismatch_raises(tmp_path):
    f = tmp_path / "a.stl"
    f.write_bytes(b"abc")
    with pytest.raises(RuntimeError, match="a.stl"):
        fetch.verify_sha256(f, "0" * 64)


class _FakeResponse:
    def __init__(self, data):
        self._data = data

    def read(self, n=-1):
        chunk, self._data = (self._data, b"") if n < 0 else (self._data[:n], self._data[n:])
        return chunk

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def test_known_size_download_retries_after_a_timeout(tmp_path, monkeypatch):
    calls = []

    def flaky(request, timeout):
        calls.append(request.full_url)
        if len(calls) == 1:
            raise TimeoutError("The read operation timed out")
        return _FakeResponse(b"abcdef")

    monkeypatch.setattr(fetch.urllib.request, "urlopen", flaky)
    monkeypatch.setattr(fetch, "RETRY_PAUSE_S", 0)
    fetch.download_known_size("https://example.test/a.stl", tmp_path / "a.stl", 6)
    assert (tmp_path / "a.stl").read_bytes() == b"abcdef" and len(calls) == 2
