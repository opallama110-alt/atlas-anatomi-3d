# Tahap 2 — Badan Perempuan Lengkap: Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Badan Perempuan bisa dipilih di atlas: kulit dan organ dari HuBMAP HRA, kerangka dari BoneHub, otot tungkai dari Andreassen dkk., sisanya dipasang dari BodyParts3D. Setiap bagian membawa asal `perempuan-asli` atau `dipasang-dari-laki-laki` yang tampil di panel info, dan semua bagian dipasang bisa disorot sekaligus.

**Architecture:** Pipeline Python baru (`python -m atlas_pipeline female`) membaca empat sumber ke kerangka koordinat HRA, lalu menulis GLB mentah per sistem dan manifest draf ke `data/work/female/`. Tulang BoneHub ditempatkan per ruas: batang tubuh dengan satu transformasi kaku + skala, tungkai per tulang ke tulang HRA, dan lengan, tangan, serta telapak kaki "ditekuk ulang" mengikuti bentuk kulit HRA. Otot Andreassen dan bagian BodyParts3D dipindahkan dengan thin-plate spline yang dibangun dari pasangan titik tulang (ditambah kulit untuk BodyParts3D). Skrip Node yang sudah ada menyederhanakan, mengompres, dan memvalidasi hasilnya ke `public/models/female/`; aplikasi memuatnya seperti badan laki-laki.

**Tech Stack:** Python 3.13 (numpy, scipy, trimesh, pytest) — tanpa dependensi baru; Node 24 (gltf-transform + meshoptimizer); Vite 8 + React 19 + TypeScript 7 + three.js 0.186; Vitest.

**Spec:** [`docs/superpowers/specs/2026-10-23-atlas-anatomi-3d-design.md`](../specs/2026-10-23-atlas-anatomi-3d-design.md), terutama bagian 6 (sumber), 7 (menyatukan data), 10, dan 15 (risiko). Rencana ini mencakup tahap 2 dari bagian 11. Gaya dan struktur mengikuti [rencana tahap 1](2026-10-23-tahap-1-fondasi.md).

## Temuan pengintaian data (3 November 2026)

Sebelum menulis rencana ini, isi JSON GLB HRA dibaca lewat *range request*, dan 31 STL contoh BoneHub (±110 MB, di scratchpad, tidak di-commit) diunduh untuk uji registrasi. Hasilnya menentukan desain:

| Temuan | Akibat untuk rencana |
|---|---|
| HRA v1.10: 956 mesh, 7,76 juta segitiga, satuan meter, Y ke atas, depan +Z, kiri +X. Setiap node membawa `extras.label` dan `extras.ontologyid` (313 FMA, 429 UBERON, 214 kosong). | Kerangka HRA langsung jadi kerangka atlas. Nama dari label, label Indonesia/Latin lewat FMA dan UBERON. |
| BoneHub: 143 STL perempuan (289,5 MB), milimeter, Z ke atas, depan −Y, kiri +X. Sumbunya sama dengan BodyParts3D, jadi `to_atlas_space` bisa dipakai ulang. `HIP_LEFT/RIGHT` sudah mencakup ilium, ischium, dan pubis. | HRA v1.5 tidak perlu diunduh. |
| Registrasi batang tubuh BoneHub → HRA (C7–L6, sakrum, sternum, panggul): skala 1,004, rata-rata galat 1,2–4,4 mm per tulang. | Satu transformasi kaku + skala cukup untuk batang tubuh, kepala, dan rusuk. |
| Tungkai HRA diputar ±8° dari pose CT (berdiri, kaki lurus). Panjang tulangnya sama (selisih < 0,5%). Pencocokan per tulang: femur 2,5–4,7 mm, tibia 2,8 mm, patela 1,4–2,3 mm. | Paha, tempurung lutut, dan betis dicocokkan per tulang ke tulang HRA. |
| Kulit HRA berpose berdiri dengan lengan terbuka (pose A), telapak kaki rata. CT berpose berbaring: siku menekuk, tangan di atas paha, kaki menjinjit. Dengan transformasi batang tubuh, 20–100% verteks lengan, tangan, dan kaki BoneHub ada di luar kulit (sampai 11 cm). | Lengan, tangan, dan telapak kaki harus ditekuk ulang per ruas mengikuti kulit HRA (Task 6). Lengan HRA terpisah dari badan di bawah ketiak (y < 0,37), jadi garis tengah lengan bisa diambil dari potongan kulit. |
| BoneHub tidak punya tulang rawan iga, tulang hioid, dan sesamoid kaki. Ujung tulang di dekat siku tidak lengkap karena CT terpotong. | Tulang rawan iga, hioid, dan sesamoid dipasang dari BodyParts3D. Humerus, radius, dan ulna diberi catatan. |
| Halaman unduhan Andreassen (`digitalcommons.du.edu`) menolak unduhan skrip (HTTP 403). | File itu (87,8 MB) diunduh pemilik lewat browser satu kali. Pipeline tidak mengakali proteksi situs. |
| Tidak ada sumber yang punya kelenjar tiroid (HRA dan BodyParts3D 4.0). | Tiroid tidak ada di kedua badan; dicatat sebagai keterbatasan. |

## Global Constraints

- Semua teks antarmuka berbahasa Indonesia dan dikumpulkan di `src/ui/strings.ts`.
- Satuan meter, sumbu Y ke atas, lantai di y = 0, tubuh menghadap +Z; sisi kiri tubuh berada di +X.
- Hanya data berlisensi CC BY 4.0 atau CC0. `ATTRIBUTION.md` ikut di repo dan bisa dibuka dari dalam atlas.
- Gambar otot 2D yang dibeli (`G:\My_AI_OS\3_Resources\Anatomi Otot`) tidak pernah di-commit.
- Setiap file yang di-commit di bawah 100 MB. `data/raw/` dan `data/work/` di-ignore; model olahan ada di `public/models/<body>/`.
- Lapisan awal (kulit, tulang, organ) paling besar 40 MB per badan; lapisan lain dimuat saat dibutuhkan.
- Minimal 30 fps di laptop pemilik (Intel Core Ultra 5 125H, Intel Arc terintegrasi, RAM 16 GB) dengan semua lapisan aktif.
- Nama tidak pernah ditebak: label Indonesia dan Latin hanya lewat ID FMA atau UBERON; selebihnya nama Inggris.
- Asal setiap bagian badan perempuan hanya `perempuan-asli` atau `dipasang-dari-laki-laki`, dan selalu terlihat di panel info. Semua bagian `dipasang-dari-laki-laki` bisa disorot sekaligus (spec 7.5).
- Kerangka perempuan seluruhnya dari BoneHub; tulang HRA yang dobel tidak ditampilkan (spec 7.2). Otot tungkai dari Andreassen; otot BodyParts3D yang sama tidak dipakai (spec 7.3).
- Pipeline deterministik: semua sampel acak memakai seed tetap, sehingga `npm run models:female` menghasilkan model yang sama dari data mentah yang sama.
- Unduhan yang diblokir situs tidak diakali (tanpa memalsukan browser); pipeline berhenti dengan pesan bahasa Indonesia yang menjelaskan unduhan manualnya.
- Push branch fitur boleh. Merge atau push ke `main` hanya dengan persetujuan pemilik, karena setiap push ke `main` diterbitkan ke GitHub Pages.

## Review Focus

1. **Badan perempuan tercermin atau menghadap ke belakang** setelah empat sumber digabung. Bagian bernama "Left …" harus di +X dan wajah di +Z. Tes: Task 9 (`test_side_mismatches_flags_left_part_on_the_right`), Task 10 (`test_assembled_body_keeps_left_positive_x_and_front_positive_z`, perakitan gagal bila ada sisi yang salah), dan pemeriksaan browser di Task 15.
2. **Bagian ganda dari dua sumber**, misalnya dua femur, dua jantung, atau pembuluh dobel. Tes: Task 4 (pengecualian HRA), Task 8 (pemilihan BodyParts3D), dan Task 9 (`test_duplicate_names_across_sources`), yang membuat perakitan gagal.
3. **Tulang atau otot menembus kulit setelah posenya disesuaikan** (jari, telapak kaki, bahu). Tes: Task 6 (`test_repose_arm_puts_bent_arm_inside_straight_tube` dan tes data asli dengan ambang), Task 9 (`outside_skin`), dan Task 10 (perakitan gagal bila melewati ambang).
4. **Ganti badan saat lapisan masih dimuat** (Perempuan lalu Laki-laki dengan cepat). Chip "Memuat…" harus benar, dan manifest badan lain ditolak. Tes: Task 14 (`LoadingTracker`) dan Task 12 (`rejects a manifest for another body`).
5. **File Andreassen belum diunduh, atau unduhan otomatis putus/rusak.** Pipeline harus berhenti dengan pesan yang menjelaskan langkah manualnya, bukan error Python mentah. Tes: Task 1 (`test_require_andreassen_explains_manual_download`, `test_sha256_mismatch_raises`).

---

### Task 1: Data mentah badan perempuan

**Files:**
- Modify: `pipeline/atlas_pipeline/fetch.py`, `pipeline/pytest.ini`
- Create: `pipeline/tests/conftest.py`
- Test: `pipeline/tests/test_fetch.py`

**Interfaces:**
- Produces:
  - `HRA_FEMALE_URL = "https://cdn.humanatlas.io/digital-objects/ref-organ/united-female/v1.10/assets/3d-vh-f-united.glb"`, `HRA_FEMALE_BYTES = 374_505_632`
  - `fetch_hra_female(raw_dir: Path) -> Path` → `raw_dir/"hra"/"3d-vh-f-united.glb"`, memakai `_download` yang sudah ada (bisa dilanjutkan).
  - `BONEHUB_TREE_URL = "https://huggingface.co/api/datasets/BoneHub/visible-human-3d-models/tree/main/visible_human_3d_models/CT/Mesh/02_Female?recursive=1"`, `BONEHUB_FILE_URL = "https://huggingface.co/datasets/BoneHub/visible-human-3d-models/resolve/main/{path}"`
  - `bonehub_female_files(tree: list[dict]) -> list[tuple[str, int, str]]`: `(path, size, sha256)` untuk entri `type == "file"` yang berakhiran `.stl` di bawah `02_Female/`. sha256 diambil dari `lfs.oid`.
  - `fetch_bonehub_female(raw_dir: Path) -> dict[str, Path]`: stem file (misalnya `FEMUR_LEFT`) → `raw_dir/"bonehub"/"02_Female"/<FOLDER>/<FILE>.stl`. Setiap file diverifikasi sha256-nya.
  - `verify_sha256(path: Path, expected: str) -> None`, melempar `RuntimeError` bila tidak cocok.
  - `ANDREASSEN_PAGE = "https://digitalcommons.du.edu/visiblehuman/1/"`
  - `class ManualDownloadMissing(RuntimeError)`
  - `require_andreassen(raw_dir: Path) -> Path`: tepat satu `*.zip` di `raw_dir/"andreassen"` yang bisa dibuka `zipfile` dan berisi ≥ 76 anggota `.stl`. Kalau tidak, melempar `ManualDownloadMissing` dengan pesan yang memuat `ANDREASSEN_PAGE`, label tombol `Final 3D STL Models (87.8 MB)`, dan folder tujuan.
  - Penanda pytest `realdata`: tes yang butuh data mentah asli. Tes ini dilewati secara bawaan dan dijalankan dengan `-m realdata`. Fixture `raw_dir` di `conftest.py` mengarah ke `<repo>/data/raw` dan melewati tes bila foldernya tidak ada.

- [ ] **Step 1: Siapkan worktree untuk data dan venv**

Folder `data/` di worktree belum ada. Buat junction ke data checkout utama (tidak di-commit), lalu venv pipeline:

```powershell
New-Item -ItemType Junction -Path data -Target F:\Proyek\Atlas-Anatomi-3D\data
cd pipeline; python -m venv .venv; .venv\Scripts\python -m pip install -r requirements.txt
```

Expected: `data\raw\bodyparts3d` terlihat dari worktree; `.venv\Scripts\python -m pytest -q` lulus (tes tahap 1).

- [ ] **Step 2: Tulis tes yang gagal**

```python
# pipeline/tests/test_fetch.py
import zipfile, pytest
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
    folder = tmp_path / "andreassen"; folder.mkdir()
    with zipfile.ZipFile(folder / "vhf.zip", "w") as z:
        for i in range(76):
            z.writestr(f"Left/Muscles/m{i}.stl", "solid x\nendsolid x\n")
    assert fetch.require_andreassen(tmp_path) == folder / "vhf.zip"

def test_sha256_mismatch_raises(tmp_path):
    f = tmp_path / "a.stl"; f.write_bytes(b"abc")
    with pytest.raises(RuntimeError, match="a.stl"):
        fetch.verify_sha256(f, "0" * 64)
```

Tambahkan ke `pytest.ini`: `markers = realdata: butuh data mentah di data/raw` dan `addopts = -m "not realdata"`.

- [ ] **Step 3: Jalankan, pastikan gagal**

Run: `cd pipeline && .venv/Scripts/python -m pytest tests/test_fetch.py -q`
Expected: FAIL, `AttributeError: module 'atlas_pipeline.fetch' has no attribute 'bonehub_female_files'`.

- [ ] **Step 4: Implementasi fungsi di `fetch.py` dan fixture `raw_dir` di `conftest.py`**

Daftar file BoneHub diambil dari `BONEHUB_TREE_URL` (JSON). Pesan `ManualDownloadMissing` (teks tetap):

```
File otot Andreassen belum ada. Unduh sekali lewat browser:
1. Buka https://digitalcommons.du.edu/visiblehuman/1/
2. Klik "Download" di samping "Final 3D STL Models (87.8 MB)".
3. Simpan file .zip itu di folder <raw_dir>\andreassen\ lalu jalankan ulang.
Situs ini menolak unduhan otomatis, jadi langkah ini tidak bisa dilakukan skrip.
```

- [ ] **Step 5: Jalankan, pastikan lulus**

Run: `cd pipeline && .venv/Scripts/python -m pytest -q`
Expected: semua tes lulus (tes tahap 1 dan 4 tes baru).

- [ ] **Step 6: Unduh data asli**

Run: `cd pipeline && .venv/Scripts/python -c "from pathlib import Path; from atlas_pipeline import fetch; r=Path('../data/raw'); print(fetch.fetch_hra_female(r).stat().st_size, len(fetch.fetch_bonehub_female(r)))"`
Expected: `374505632 143`. Minta pemilik meletakkan zip Andreassen di `data/raw/andreassen/` (lihat pesan di Step 4); Task 7 dan seterusnya butuh file itu.

- [ ] **Step 7: Commit**

```bash
git add pipeline
git commit -m "feat(pipeline): unduh HRA dan BoneHub perempuan, periksa zip Andreassen manual"
```

---

### Task 2: Bagian bersama, penulis badan, dan koreksi sisi BodyParts3D

**Files:**
- Create: `pipeline/atlas_pipeline/parts.py`
- Modify: `pipeline/atlas_pipeline/package_body.py`
- Test: `pipeline/tests/test_parts.py`, `pipeline/tests/test_package_body.py`

**Interfaces:**
- Consumes: `parse_obj`, `to_atlas_space`, `side_from_name`, `load_element_concepts`, `classify` (tahap 1).
- Produces:
  - `@dataclass class Part`: `id: str`, `system: SystemId`, `side: Side`, `origin: str`, `source: str`, `source_ref: str`, `names: dict[str, str]`, `vertices: np.ndarray` (N×3, meter, ruang atlas sebelum translasi), `faces: np.ndarray` (M×3), `fma: str | None = None`, `uberon: str | None = None`, `notes: tuple[str, ...] = ()`.
  - `write_body(parts: list[Part], work_dir: Path, body: Literal["male", "female"]) -> dict`. Translasi global seperti tahap 1: kurangi pusat kotak X/Z dan `minY` dari semua bagian. Menulis `work_dir/<body>/<system>.glb` (nama node = id) dan `manifest.draft.json`. Bentuk part sama dengan tahap 1 (`sourceRef`, `bounds`, `file`, `triangles`); `fma`, `uberon`, dan `notes` hanya ditulis bila ada. Bagian tanpa segitiga ditolak (`ValueError`).
  - `read_bp3d_parts(raw_dir: Path, labels: dict[str, dict[str, str]]) -> tuple[list[Part], dict[str, str], dict[str, ElementConcepts]]`: bagian BodyParts3D (asal `laki-laki-asli`), id aturan klasifikasi per id bagian, dan konsep per id bagian.
  - `SIDE_CORRECTIONS: dict[str, Side] = {"FJ1469": "right", "FJ1469M": "left", "FJ2190": "left"}` (temuan kecil tahap 1 no. 4). Bagian yang dikoreksi mendapat sisi baru, kata "Left"/"Right" di `names.en` ditukar, dan label `id`/`la` dibuang, karena label Wikidata itu milik konsep sisi yang salah.
  - `build_male` tetap dengan tanda tangan yang sama dan memakai `read_bp3d_parts` + `write_body`.

- [ ] **Step 1: Tulis tes yang gagal**

```python
# pipeline/tests/test_parts.py
import json
import numpy as np
from atlas_pipeline.parts import Part, write_body

def tri(x0):
    return np.array([[x0, 1.0, 0.0], [x0 + 0.1, 1.0, 0.0], [x0, 2.0, 0.1]]), np.array([[0, 1, 2]])

def test_write_body_translates_and_writes_optional_fields(tmp_path):
    v1, f = tri(0.2); v2, _ = tri(-0.4)
    parts = [Part("BH:FEMUR_LEFT", "skeletal", "left", "perempuan-asli", "bonehub", "FEMUR_LEFT",
                  {"en": "Left femur"}, v1, f, fma="FMA24474", notes=("pose-disesuaikan",)),
             Part("HRA:x", "digestive", "none", "perempuan-asli", "hra", "x", {"en": "X"}, v2, f, uberon="UBERON:1")]
    manifest = write_body(parts, tmp_path, "female")
    femur, other = manifest["parts"]
    assert femur["bounds"][0][1] == 0.0 and femur["notes"] == ["pose-disesuaikan"] and "uberon" not in femur
    assert other["uberon"] == "UBERON:1" and "notes" not in other and "fma" not in other
    assert sorted(p.name for p in (tmp_path / "female").glob("*.glb")) == ["digestive.glb", "skeletal.glb"]
    assert json.loads((tmp_path / "female" / "manifest.draft.json").read_text("utf-8")) == manifest
```

Tambahkan ke `test_package_body.py`:

```python
def test_side_corrections_flip_side_and_drop_labels(tmp_path, monkeypatch):
    from atlas_pipeline import package_body
    monkeypatch.setattr(package_body, "SIDE_CORRECTIONS", {"FJ1": "right"})
    femur = next(p for p in build(tmp_path)["parts"] if p["id"] == "BP3D:FJ1")
    assert femur["side"] == "right" and femur["names"] == {"en": "Right test femur"}
```

- [ ] **Step 2: Jalankan, pastikan gagal**

Run: `cd pipeline && .venv/Scripts/python -m pytest tests/test_parts.py tests/test_package_body.py -q`
Expected: FAIL, modul `atlas_pipeline.parts` belum ada.

- [ ] **Step 3: Implementasi `parts.py`, lalu ubah `package_body.py` supaya memakainya**

- [ ] **Step 4: Jalankan semua tes pipeline**

Run: `cd pipeline && .venv/Scripts/python -m pytest -q`
Expected: semua lulus, termasuk tes tahap 1 untuk `build_male` tanpa perubahan.

- [ ] **Step 5: Bangun ulang badan laki-laki**

Run: `npm run models:male`
Expected: exit 0, 2234 bagian. `git diff --stat public/models/male` hanya menyentuh `manifest.json` (tiga sisi dan nama yang dikoreksi). Kalau GLB ikut berubah, periksa apakah urutan bagian berubah; hasilnya harus identik.

- [ ] **Step 6: Commit**

```bash
git add pipeline public/models/male/manifest.json
git commit -m "refactor(pipeline): penulis badan bersama; koreksi tiga sisi BodyParts3D yang tertukar"
```

---

### Task 3: Pembaca GLB HRA

**Files:**
- Create: `pipeline/atlas_pipeline/hra_glb.py`, `pipeline/tests/helpers/__init__.py`, `pipeline/tests/helpers/glb.py`
- Test: `pipeline/tests/test_hra_glb.py`

**Interfaces:**
- Produces:
  - `@dataclass(frozen=True) class HraMesh`: `node: str`, `path: tuple[str, ...]` (nama leluhur dari akar sampai node itu sendiri), `label: str | None`, `ontology: str | None` (nilai `extras.label` dan `extras.ontologyid`; `"-"` atau kosong menjadi `None`), `vertices: np.ndarray` (ruang dunia, float64), `faces: np.ndarray` (int64; semua primitive digabung).
  - `read_hra_glb(path: Path) -> list[HraMesh]`, dengan urutan node sesuai file. Pembacanya ditulis sendiri (chunk JSON + chunk BIN dengan numpy, `np.memmap`), supaya `extras` tidak hilang. Transformasi node (matrix, atau TRS) disusun dari akar ke daun.
  - Helper tes `write_glb(path: Path, nodes: list[dict], meshes: list[tuple[np.ndarray, np.ndarray]]) -> None`. Setiap dict node memakai kunci glTF (`name`, `children`, `mesh`, `translation`, `rotation`, `scale`, `extras`).

- [ ] **Step 1: Tulis tes yang gagal**

```python
# pipeline/tests/test_hra_glb.py
import numpy as np, pytest
from atlas_pipeline.hra_glb import read_hra_glb
from tests.helpers.glb import write_glb

SQUARE = (np.array([[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0]], np.float32), np.array([0, 1, 2, 0, 2, 3], np.uint16))

def test_reads_world_space_through_parent_transforms(tmp_path):
    nodes = [{"name": "VH_F", "children": [1], "translation": [0, 1, 0]},
             {"name": "VH_F_skin", "mesh": 0, "scale": [2, 2, 2],
              "rotation": [0, 0, 0.7071068, 0.7071068]}]          # 90° tentang Z
    write_glb(tmp_path / "a.glb", nodes, [SQUARE])
    (mesh,) = read_hra_glb(tmp_path / "a.glb")
    assert mesh.path == ("VH_F", "VH_F_skin")
    assert np.allclose(mesh.vertices[1], [0, 3, 0], atol=1e-6)   # (1,0,0) ×2 → putar 90° → (0,2,0) → +1 di Y
    assert mesh.faces.tolist() == [[0, 1, 2], [0, 2, 3]]

def test_reads_extras_and_dash_means_none(tmp_path):
    nodes = [{"name": "a", "mesh": 0, "extras": {"label": "Left ora serrata", "ontologyid": "FMA:58602"}},
             {"name": "b", "mesh": 0, "extras": {"label": "-", "ontologyid": "-"}}]
    write_glb(tmp_path / "b.glb", nodes, [SQUARE])
    a, b = read_hra_glb(tmp_path / "b.glb")
    assert (a.label, a.ontology) == ("Left ora serrata", "FMA:58602")
    assert (b.label, b.ontology) == (None, None)

@pytest.mark.realdata
def test_real_hra_has_956_meshes_in_atlas_axes(raw_dir):
    meshes = {m.node: m for m in read_hra_glb(raw_dir / "hra" / "3d-vh-f-united.glb")}
    assert len(meshes) == 956
    skin = meshes["VH_F_skin"].vertices
    assert abs(skin[:, 1].min() + 0.793) < 0.002 and abs(skin[:, 1].max() - 0.865) < 0.002
    assert meshes["VH_F_left_apical_bronchopulmonary_segment"].vertices[:, 0].mean() > 0
    assert meshes["VH_F_sternum"].vertices[:, 2].mean() > meshes["VH_F_thoracic_vertebra_5"].vertices[:, 2].mean()
```

- [ ] **Step 2: Jalankan, pastikan gagal**

Run: `cd pipeline && .venv/Scripts/python -m pytest tests/test_hra_glb.py -q`
Expected: FAIL, modul belum ada.

- [ ] **Step 3: Implementasi `hra_glb.py` dan helper `write_glb`**

- [ ] **Step 4: Jalankan, pastikan lulus (termasuk data asli)**

Run: `cd pipeline && .venv/Scripts/python -m pytest tests/test_hra_glb.py -q && .venv/Scripts/python -m pytest tests/test_hra_glb.py -m realdata -q`
Expected: 2 passed, lalu 1 passed.

- [ ] **Step 5: Commit**

```bash
git add pipeline
git commit -m "feat(pipeline): baca GLB HRA perempuan beserta label dan ID ontologi"
```

---

### Task 4: Bagian HRA — pilih, beri nama, sisi, dan sistem

**Files:**
- Create: `pipeline/atlas_pipeline/hra_parts.py`, `pipeline/atlas_pipeline/checks.py`
- Test: `pipeline/tests/test_hra_parts.py`, `pipeline/tests/test_checks.py`

**Interfaces:**
- Consumes: `HraMesh` (Task 3), `Part` (Task 2).
- Produces:
  - `classify_hra(mesh: HraMesh) -> tuple[SystemId | None, str]`: sistem (atau `None` bila tidak dipakai) dan id aturan/alasan.
  - `hra_side(node: str) -> Side`: token `L`/`R` yang dipisah garis bawah (huruf besar), atau kata `left`/`right`.
  - `hra_english_name(node: str, label: str | None) -> str`
  - `hra_ontology(ontology: str | None) -> tuple[str | None, str | None]`: `"FMA:58602"` → `("FMA58602", None)`, `"UBERON:0002336"` → `(None, "UBERON:0002336")`.
  - `SURFACE_DUPLICATES: frozenset[str]`, `ALLOWED_OVERLAPS: frozenset[frozenset[str]]`
  - `hra_to_parts(meshes: list[HraMesh]) -> tuple[list[Part], list[dict]]`: bagian (`id = "HRA:" + node`, asal `perempuan-asli`, sumber `hra`, `source_ref = node`) dan daftar yang tidak dipakai (`{"node", "reason"}`).
  - `checks.coincident_pairs(meshes: Sequence[tuple[str, np.ndarray, np.ndarray]], tol_m: float = 0.0005, min_fraction: float = 0.9) -> list[tuple[str, str, float]]`: pasangan `(lebih kecil, lebih besar, fraksi)` ketika ≥ 90% verteks mesh yang lebih kecil (luas permukaannya) berjarak ≤ 0,5 mm dari permukaan mesh lain. Saringan awal memakai tumpang-tindih kotak batas; jarak memakai KD-tree atas sampel permukaan (seed 11).

Aturan `classify_hra`, berurutan; aturan pertama yang cocok menang:

| # | id aturan | cocok jika | hasil |
|---|---|---|---|
| 1 | `placenta` | path memuat `VH_F_placenta` | tidak dipakai |
| 2 | `dup-bone` | path memuat `VH_F_femur_L`/`VH_F_femur_R` (semua turunannya, termasuk tulang rawan sendi lutut); node `VH_F_tibia_*`, `VH_F_fibula_*`, `VH_F_patella_*`; atau di `VH_F_skeletal_system` dan nama tidak memuat `intervertebral_disk` | tidak dipakai |
| 3 | `dup-andreassen` | node memuat `anterior_cruciate_ligament`, `posterior_cruciate_ligament`, `tibial_collateral_ligament`, `fibular_collateral_ligament`, atau `rectus_femoris` | tidak dipakai |
| 4 | `dup-surface` | node ada di `SURFACE_DUPLICATES` | tidak dipakai |
| 5 | `lymph-node` | path memuat `Yao_lymph_node` | lymphatic |
| 6 | `heart` | path memuat `VH_F_heart` | cardiac |
| 7 | `artery` | nama cocok `artery\|arteries\|aort\|carotid\|subclavian\|brachiocephalic`, atau path memuat `VH_F_circulatory_system` dan nama berakhiran `_trunk` | arterial |
| 8 | `vein` | nama cocok `vein\|vena_cava\|coronary_sinus` | venous |
| 9 | `vessel-unknown` | path memuat `VH_F_blood_vasculature` | raise `ValueError` (harus ditambah aturan) |
| 10 | `eye` | path memuat `VH_F_eyes` | sensory |
| 11 | `nervous` | path memuat `VH_F_nervous_system` | nervous |
| 12 | `tonsil` | nama memuat `tonsil` | lymphatic |
| 13 | `tendon` | path memuat `VH_F_muscular_system` dan nama memuat `tendon` | connective |
| 14 | `group` | grup tingkat atas: `integumentary_system`→integumentary, `muscular_system`→muscular, `reproductive_system`→reproductive, `digestive_system`→digestive, `urinary_system`→urinary, `respiratory_system`→respiratory, `lymphatic_system`→lymphatic, `skeletal_system`→connective (cakram antarruas), `lower_limb`→connective | sesuai grup |
| 15 | `unknown` | selalu | raise `ValueError` |

Nilai awal `SURFACE_DUPLICATES`: delapan tambalan permukaan hati (`VH_F_gastric_impression_of_liver`, `…_suprarenal_impression_of_liver`, `…_renal_impression_of_liver`, `…_duodenal_impression_of_liver`, `…_esophageal_impression_of_liver`, `…_colic_impression_of_liver`, `VH_F_bare_area_of_liver`, `VH_F_diaphragmatic_surface_of_liver`) dan `VH_F_porta_hepatis`. Pasangan lain dari data asli diselesaikan di Step 5.

Aturan nama Inggris: kalau ada `label`, pakai label itu; kalau tidak, nama node tanpa awalan `VH_F_`/`Allen_`/`Yao_`, dengan garis bawah menjadi spasi. Kata sisi dibuang lalu dipasang ulang di depan ("Left …"/"Right …"). Token huruf tunggal di akhir nama node ditambahkan sebagai " (k)". Huruf pertama dikapitalkan.

- [ ] **Step 1: Tulis tes yang gagal**

```python
# pipeline/tests/test_hra_parts.py
import numpy as np, pytest
from atlas_pipeline.hra_glb import HraMesh
from atlas_pipeline.hra_parts import classify_hra, hra_english_name, hra_ontology, hra_side

def m(*path, label=None):
    return HraMesh(path[-1], ("VH_F",) + path, label, None, np.zeros((3, 3)), np.array([[0, 1, 2]]))

@pytest.mark.parametrize("mesh,expected", [
    (m("VH_F_reproductive_system", "VH_F_placenta", "VH_F_amnion"), (None, "placenta")),
    (m("VH_F_lower_limb", "VH_F_lower_limb_L", "VH_F_knee_L", "VH_F_knee_joint_L", "VH_F_femur_L", "VH_F_articular_cartilage_of_knee_L"), (None, "dup-bone")),
    (m("VH_F_skeletal_system", "VH_F_vertebral_column", "VH_F_vertebra", "VH_F_thoracic_vertebra_5"), (None, "dup-bone")),
    (m("VH_F_skeletal_system", "VH_F_vertebral_column", "VH_F_intervertebral_joint", "VH_F_intervertebral_disk_of_third_lumbar_vertebra"), ("connective", "group")),
    (m("VH_F_lower_limb", "VH_F_lower_limb_L", "VH_F_ligaments_of_knee_L", "VH_F_anterior_cruciate_ligament_of_knee_L"), (None, "dup-andreassen")),
    (m("VH_F_lower_limb", "VH_F_lower_limb_L", "VH_F_knee_L", "VH_F_knee_joint_L", "VH_F_meniscus_L"), ("connective", "group")),
    (m("VH_F_lymphatic_system", "Yao_lymph_node", "Yao_blood_vasculature"), ("lymphatic", "lymph-node")),
    (m("VH_F_circulatory_system", "VH_F_heart", "VH_F_valve", "VH_F_mitral_valve"), ("cardiac", "heart")),
    (m("VH_F_circulatory_system", "VH_F_blood_vasculature", "VH_F_pulmonary_trunk"), ("arterial", "artery")),
    (m("VH_F_circulatory_system", "VH_F_blood_vasculature", "VH_F_coronary_sinus"), ("venous", "vein")),
    (m("VH_F_lymphatic_system", "VH_F_spleen", "VH_F_splenic_vein"), ("venous", "vein")),
    (m("VH_F_nervous_system", "VH_F_eyes", "VH_F_lens_L"), ("sensory", "eye")),
    (m("VH_F_digestive_system", "VH_F_palatine_tonsil", "VH_F_palatine_tonsil_L"), ("lymphatic", "tonsil")),
    (m("VH_F_muscular_system", "VH_F_muscles_of_knee", "VH_F_muscles_of_knee_L", "VH_F_tendon_of_quadriceps_femoris_L"), ("connective", "tendon")),
    (m("VH_F_digestive_system", "VH_F_liver", "VH_F_gastric_impression_of_liver"), (None, "dup-surface")),
])
def test_classify_hra_follows_rule_order(mesh, expected):
    assert classify_hra(mesh) == expected

def test_unknown_vessel_is_an_error():
    with pytest.raises(ValueError, match="VH_F_mystery_duct"):
        classify_hra(m("VH_F_circulatory_system", "VH_F_blood_vasculature", "VH_F_mystery_duct"))

@pytest.mark.parametrize("node,side", [("VH_F_L_lung_upper_lobe", "left"), ("Allen_corpus_callosum_R", "right"),
    ("VH_F_left_renal_artery", "left"), ("VH_F_renal_papilla_L_k", "left"), ("VH_F_trachea", "none"), ("VH_F_Lymph", "none")])
def test_hra_side(node, side):
    assert hra_side(node) == side

@pytest.mark.parametrize("node,label,name", [
    ("VH_F_ora_serrata_of_retina_L", "Left ora serrata", "Left ora serrata"),
    ("VH_F_renal_papilla_L_k", "renal papilla", "Left renal papilla (k)"),
    ("Allen_cerebral_aqueduct_L", None, "Left cerebral aqueduct"),
    ("VH_F_descending_aorta_a", None, "Descending aorta (a)"),
    ("VH_F_right_ureter", None, "Right ureter"),
])
def test_hra_english_name(node, label, name):
    assert hra_english_name(node, label) == name

def test_hra_ontology():
    assert hra_ontology("FMA:58602") == ("FMA58602", None)
    assert hra_ontology("UBERON:0002336") == (None, "UBERON:0002336")
    assert hra_ontology(None) == (None, None)
```

```python
# pipeline/tests/test_checks.py
import numpy as np
from atlas_pipeline.checks import coincident_pairs

def grid(n, z=0.0, size=0.1):
    xs = np.linspace(0, size, n); v = np.array([[x, y, z] for x in xs for y in xs])
    f = [[i * n + j, i * n + j + 1, (i + 1) * n + j] for i in range(n - 1) for j in range(n - 1)]
    return v, np.array(f)

def test_coincident_pairs_finds_patch_on_surface_and_ignores_offset_copy():
    big_v, big_f = grid(20); patch_v, patch_f = grid(6, size=0.04); far_v, far_f = grid(6, z=0.01, size=0.04)
    pairs = coincident_pairs([("big", big_v, big_f), ("patch", patch_v, patch_f), ("far", far_v, far_f)])
    assert [(a, b) for a, b, _ in pairs] == [("patch", "big")]
```

- [ ] **Step 2: Jalankan, pastikan gagal**

Run: `cd pipeline && .venv/Scripts/python -m pytest tests/test_hra_parts.py tests/test_checks.py -q`
Expected: FAIL, modul belum ada.

- [ ] **Step 3: Implementasi `hra_parts.py` dan `checks.coincident_pairs`**

- [ ] **Step 4: Jalankan, pastikan lulus**

Run: `cd pipeline && .venv/Scripts/python -m pytest -q`
Expected: semua lulus.

- [ ] **Step 5: Selesaikan pasangan bertumpuk di data asli**

Tulis tes data asli di `test_hra_parts.py`:

```python
@pytest.mark.realdata
def test_real_hra_has_no_unresolved_coincident_surfaces(raw_dir):
    parts, excluded = hra_to_parts(read_hra_glb(raw_dir / "hra" / "3d-vh-f-united.glb"))
    pairs = coincident_pairs([(p.id, p.vertices, p.faces) for p in parts])
    unresolved = [p for p in pairs if frozenset(p[:2]) not in ALLOWED_OVERLAPS]
    assert unresolved == [], unresolved
    assert not [p for p in parts if p.system is None]
```

Run: `cd pipeline && .venv/Scripts/python -m pytest tests/test_hra_parts.py -m realdata -q`

Setiap pasangan yang muncul diselesaikan dengan salah satu dari dua cara: mesh yang lebih kecil dimasukkan ke `SURFACE_DUPLICATES` bila ia hanya tambalan permukaan dari mesh lain, atau pasangannya dimasukkan ke `ALLOWED_OVERLAPS` bila keduanya struktur nyata yang kebetulan berbagi permukaan (misalnya katup pada dinding ruang jantung). Catat setiap keputusan di bagian "Catatan keputusan" di akhir rencana ini. Ulangi sampai tes lulus.

- [ ] **Step 6: Commit**

```bash
git add pipeline docs/superpowers/plans/2026-11-03-tahap-2-perempuan.md
git commit -m "feat(pipeline): pilih, namai, dan kelompokkan bagian HRA perempuan"
```

---

### Task 5: Registrasi, thin-plate spline, dan medan jarak kulit

**Files:**
- Create: `pipeline/atlas_pipeline/registration.py`, `pipeline/atlas_pipeline/warp.py`, `pipeline/atlas_pipeline/skin_field.py`
- Test: `pipeline/tests/test_registration.py`, `pipeline/tests/test_warp.py`, `pipeline/tests/test_skin_field.py`

**Interfaces:**
- Produces:
  - `@dataclass(frozen=True) class Similarity`: `scale: float`, `rotation: np.ndarray` (3×3), `translation: np.ndarray` (3). Method `apply(points) -> np.ndarray` = `s·R·p + t`, `compose(inner: Similarity) -> Similarity` (terapkan `inner` dulu), `inverse() -> Similarity`, dan classmethod `identity()`.
  - `umeyama(src: np.ndarray, dst: np.ndarray, with_scale: bool = True) -> Similarity` untuk pasangan titik yang sudah berpadanan.
  - `icp(src_points: np.ndarray, dst_points: np.ndarray, init: Similarity, with_scale: bool, iterations: int = 40, trim: float = 0.9) -> Similarity`. Setiap iterasi mencari titik `src` terdekat (setelah ditransformasi) untuk setiap titik `dst`, membuang 10% pasangan terjauh, lalu `umeyama`. Arahnya dst → src supaya target parsial (misalnya ilium HRA terhadap tulang panggul BoneHub yang utuh) tetap benar.
  - `mean_distance_mm(src_points: np.ndarray, dst_points: np.ndarray, transform: Similarity) -> tuple[float, float]`: rata-rata dan persentil 95 jarak dari `dst` ke `src` yang sudah ditransformasi, dalam mm.
  - `class ThinPlateWarp`: `fit(sources: np.ndarray, targets: np.ndarray, smoothing: float = 0.0) -> ThinPlateWarp` (classmethod), `__call__(points: np.ndarray) -> np.ndarray`. Isinya `scipy.interpolate.RBFInterpolator(sources, targets - sources, kernel="thin_plate_spline", degree=1, smoothing=smoothing)`, dievaluasi per potongan 100.000 titik, ditambah `points`.
  - `sample_control_points(vertices: np.ndarray, faces: np.ndarray, count: int, seed: int) -> np.ndarray`: `trimesh.sample.sample_surface_even`, ditambah `sample_surface` bila hasilnya kurang dari `count`.
  - `class SkinField`: `__init__(vertices, faces, samples: int = 800_000, seed: int = 7)`, `signed(points) -> np.ndarray` (meter, positif di luar kulit; titik sampel terdekat dari KD-tree dan normal segitiganya), `clamp_inside(points, margin: float = 0.001) -> np.ndarray` (titik dengan `signed > −margin` digeser ke dalam sepanjang normal sampai `−margin`), dan atribut `points: np.ndarray` (sampel permukaan).

- [ ] **Step 1: Tulis tes yang gagal**

```python
# pipeline/tests/test_registration.py
import numpy as np
from scipy.spatial.transform import Rotation
from atlas_pipeline.registration import Similarity, icp, mean_distance_mm, umeyama

R30 = Rotation.from_rotvec([0.2, 0.5, 0.1]).as_matrix()
KNOWN = Similarity(1.1, R30, np.array([0.3, -0.2, 0.05]))

def blob(seed=0):
    rng = np.random.default_rng(seed)
    p = rng.normal(size=(2000, 3)) * [0.05, 0.12, 0.03]
    return p[p[:, 0] < 0.04]                      # potong satu sisi supaya tidak simetris

def test_umeyama_recovers_similarity():
    src = blob(); t = umeyama(src, KNOWN.apply(src))
    assert abs(t.scale - 1.1) < 1e-9 and np.allclose(t.rotation, R30) and np.allclose(t.translation, KNOWN.translation)

def test_icp_recovers_rigid_from_partial_target():
    rigid = Similarity(1.0, Rotation.from_rotvec([0.05, 0.12, 0.02]).as_matrix(), np.array([0.01, 0.02, 0.0]))  # ±8°, seperti tungkai HRA
    src = blob(); dst = rigid.apply(src[src[:, 1] > -0.05])
    found = icp(src, dst, Similarity.identity(), with_scale=False, iterations=60)
    assert mean_distance_mm(src, dst, found)[0] < 1.0

def test_compose_and_inverse_round_trip():
    p = blob()[:10]
    assert np.allclose(KNOWN.inverse().compose(KNOWN).apply(p), p)
```

```python
# pipeline/tests/test_warp.py
import numpy as np, trimesh
from atlas_pipeline.warp import ThinPlateWarp, sample_control_points

def test_tps_interpolates_controls():
    rng = np.random.default_rng(1); src = rng.uniform(-1, 1, (50, 3)); dst = src + rng.normal(0, 0.05, (50, 3))
    assert np.allclose(ThinPlateWarp.fit(src, dst)(src), dst, atol=1e-6)

def test_tps_reproduces_affine_maps_far_from_controls():
    rng = np.random.default_rng(2); src = rng.uniform(-1, 1, (40, 3))
    A = np.array([[1.1, 0.1, 0], [0, 0.9, 0.2], [0, 0, 1.0]]); b = np.array([0.3, 0, -0.1])
    far = rng.uniform(-5, 5, (100, 3))
    assert np.allclose(ThinPlateWarp.fit(src, src @ A.T + b)(far), far @ A.T + b, atol=1e-6)

def test_control_points_are_deterministic():
    box = trimesh.creation.box()
    a = sample_control_points(box.vertices, box.faces, 30, seed=3)
    assert a.shape == (30, 3) and np.array_equal(a, sample_control_points(box.vertices, box.faces, 30, seed=3))
```

```python
# pipeline/tests/test_skin_field.py
import numpy as np, trimesh
from atlas_pipeline.skin_field import SkinField

def test_signed_distance_and_clamp_on_a_sphere():
    s = trimesh.creation.icosphere(subdivisions=4, radius=0.1)
    field = SkinField(s.vertices, s.faces, samples=50_000)
    d = field.signed(np.array([[0, 0, 0], [0.12, 0, 0]]))
    assert abs(d[0] + 0.1) < 0.003 and abs(d[1] - 0.02) < 0.003
    assert abs(np.linalg.norm(field.clamp_inside(np.array([[0, 0.13, 0]]))) - 0.099) < 0.003
```

- [ ] **Step 2: Jalankan, pastikan gagal**

Run: `cd pipeline && .venv/Scripts/python -m pytest tests/test_registration.py tests/test_warp.py tests/test_skin_field.py -q`
Expected: FAIL, modul belum ada.

- [ ] **Step 3: Implementasi ketiga modul sesuai Interfaces**

- [ ] **Step 4: Jalankan, pastikan lulus**

Run: `cd pipeline && .venv/Scripts/python -m pytest -q`
Expected: semua lulus.

- [ ] **Step 5: Commit**

```bash
git add pipeline
git commit -m "feat(pipeline): registrasi ICP, thin-plate spline, dan jarak bertanda ke kulit"
```

---

### Task 6: Kerangka perempuan dari BoneHub

**Files:**
- Create: `pipeline/atlas_pipeline/bonehub.py`, `pipeline/atlas_pipeline/skeleton_fit.py`
- Test: `pipeline/tests/test_bonehub.py`, `pipeline/tests/test_skeleton_fit.py`

**Interfaces:**
- Consumes: `HraMesh` (Task 3); `Similarity`, `umeyama`, `icp`, `mean_distance_mm`, `SkinField` (Task 5); `Part` (Task 2); `to_atlas_space` (tahap 1).
- Produces:
  - `Segment = Literal["trunk", "thigh", "patella", "shank", "foot", "girdle", "upperarm", "forearm", "hand"]`
  - `bone_name_en(stem: str) -> str`, `bone_side(stem: str) -> Side`, `bone_segment(stem: str) -> Segment`
  - `load_bonehub(paths: dict[str, Path]) -> dict[str, trimesh.Trimesh]`: STL dalam meter dengan sumbu atlas (`to_atlas_space`), masih di kerangka CT.
  - `TRUNK_PAIRS: dict[str, tuple[str, ...]]`: stem BoneHub → node HRA, yaitu `VERTEBRA_C1…C7` → `VH_F_cervical_vertebra_1…7`, `T1…T12` → `VH_F_thoracic_vertebra_1…12`, `L1…L6` → `VH_F_lumbar_vertebra_1…6`, `SACRUM` → (`VH_F_sacrum`, `VH_F_coccyx`), `STERNUM` → (`VH_F_sternum`, `VH_F_manubrium`), `HIP_LEFT`/`HIP_RIGHT` → `VH_F_ilium_compact_bone_L`/`_R`.
  - `LEG_PAIRS: dict[str, dict[str, tuple[str, ...]]]`: ruas → stem → node, untuk `thigh` (`FEMUR_*` → `VH_F_femur_*`), `patella` (`PATELLA_*` → `VH_F_patella_*`), dan `shank` (`TIBIA_*` + `FIBULA_*` → `VH_F_tibia_*` + `VH_F_fibula_*`). Ruas tungkai dicocokkan per sisi.
  - `fit_pairs(bones: dict[str, trimesh.Trimesh], targets: dict[str, np.ndarray], stems: Sequence[str], init: Similarity, with_scale: bool) -> Similarity`
  - `limb_centerline(skin: SkinField, side: Side, below_y: float) -> np.ndarray`: titik garis tengah lengan (K×3, dari atas ke bawah), dari pusat komponen kulit terluar (|x| > 0,15 m) pada potongan setiap 1 cm di bawah `below_y`. Komponen dicari dengan graf radius 12 mm (`cKDTree.query_pairs` + `scipy.sparse.csgraph.connected_components`).
  - `repose_arm(bones: dict[str, np.ndarray], parent: Similarity, centerline: np.ndarray, skin: SkinField, side: Side) -> dict[Segment, Similarity]` untuk `girdle`, `upperarm`, `forearm`, dan `hand`.
  - `repose_foot(bones: dict[str, np.ndarray], parent: Similarity, skin: SkinField, side: Side) -> Similarity`
  - `@dataclass class SkeletonFit`: `trunk: Similarity`, `placement: dict[str, Similarity]` (per stem), `segment_of: dict[str, str]` (stem → `"<ruas>-<sisi>"`), `report: dict`, `fallback: frozenset[str]` (stem yang diganti tulang BodyParts3D).
  - `SEGMENT_FALLBACKS: frozenset[str] = frozenset()` (diisi di Step 6 hanya bila perlu).
  - `fit_skeleton(bones: dict[str, trimesh.Trimesh], hra: dict[str, HraMesh], skin: SkinField) -> SkeletonFit`
  - `bones_to_parts(bones: dict[str, trimesh.Trimesh], fit: SkeletonFit, fma_by_stem: dict[str, str]) -> list[Part]`: `id = "BH:" + stem`, sistem `skeletal`, asal `perempuan-asli`, sumber `bonehub`. Catatan `pose-disesuaikan` untuk semua ruas selain `trunk`; `siku-tidak-lengkap` untuk `HUMERUS_*`, `RADIUS_*`, dan `ULNA_*`. Stem di `fit.fallback` dilewati.

Nama Inggris BoneHub (dibuat dengan aturan, mengikuti gaya BodyParts3D supaya padanannya mudah): `VERTEBRA_C1` → "Atlas", `C2` → "Axis", `C3`–`C7`/`T*`/`L*` → "Third cervical vertebra", "Fifth thoracic vertebra", "Sixth lumbar vertebra"; `RIB_8_LEFT` → "Left eighth rib"; `SACRUM` → "Sacrum and coccyx"; `STERNUM` → "Sternum"; `SKULL_CRANIAL_MAXILLA` → "Cranium and maxilla"; `SKULL_MANDIBLE` → "Mandible"; `HIP_LEFT` → "Left hip bone"; `NAVICULAR_LEFT` → "Navicular bone of left foot"; `CUBOID_LEFT` → "Left cuboid bone"; `TRIQUETRUM_LEFT` → "Left triquetral"; `MEDIAL_CUNEIFORM_LEFT` → "Left medial cuneiform bone"; `METATARSAL_1_LEFT` → "Left first metatarsal bone"; `METACARPAL_1_LEFT` → "Left first metacarpal bone"; `PHALANGE_HAND_1…5_LEFT` → "Phalanges of left thumb / index finger / middle finger / ring finger / little finger"; `PHALANGE_FOOT_1…5_LEFT` → "Phalanges of left big toe / second toe / third toe / fourth toe / little toe"; selebihnya "Left " + nama tulang dalam huruf kecil (misalnya "Left humerus").

Algoritma penempatan (`fit_skeleton`). Ini satu-satunya bagian yang tidak ditentukan oleh tes:

1. **Batang tubuh:** `trunk = fit_pairs(…, TRUNK_PAIRS, init = umeyama(pusat tulang BoneHub, pusat tulang HRA), with_scale=True)`. Transformasi ini berlaku untuk tengkorak, tulang belakang, rusuk, sternum, sakrum, dan tulang panggul.
2. **Tungkai:** per sisi, `thigh`, `patella`, dan `shank` masing-masing `fit_pairs(…, init=trunk, with_scale=False)` dengan skala tetap `trunk.scale`. Telapak kaki mulai dari transformasi `shank`.
3. **Titik sendi di kerangka CT** (setelah `trunk`):
   - sendi sternoklavikula = verteks klavikula dengan |x| terkecil;
   - bahu = pusat verteks humerus dalam 25 mm dari ujung proksimalnya, diukur sepanjang sumbu utama humerus;
   - siku = titik tengah antara ujung distal humerus dan rata-rata ujung proksimal radius dan ulna (siku BoneHub tidak lengkap, jadi tidak ada permukaan sendi);
   - pergelangan = pusat 15 mm terdistal radius;
   - ujung tangan = pusat 10 mm terdistal `PHALANGE_HAND_3_*`;
   - pergelangan kaki = pusat talus;
   - sumbu telapak kaki = dari titik terbelakang kalkaneus ke ujung distal `METATARSAL_2_*`.
4. **Gelang bahu** (`CLAVICLE_*` + `SCAPULA_*` bersama): putar di sendi sternoklavikula, ±25°, dengan meminimalkan `mean(relu(skin.signed(p) + 0.003)²)` (Powell, mulai dari identitas).
5. **Lengan atas, lengan bawah, tangan** mengikuti garis tengah lengan (`limb_centerline` di bawah y ketiak = y tertinggi yang punya komponen lengan terpisah):
   - target siku = titik di garis tengah yang berjarak |siku − bahu| dari bahu baru;
   - target pergelangan = titik berjarak |pergelangan − siku| dari target siku;
   - target ujung tangan = titik terbawah garis tengah.
   Setiap ruas diputar dengan rotasi terkecil di sendi proksimalnya supaya vektor sendi→sendi CT berimpit dengan vektor target. Normal telapak tangan CT (sumbu utama terkecil verteks `METACARPAL_2…5`) lalu diputar mengelilingi sumbu tangan ke normal telapak kulit (sumbu utama terkecil titik kulit tangan di bawah target pergelangan). Tanda yang dipilih adalah yang sudutnya lebih kecil, dan putaran yang sama diterapkan ke lengan bawah.
6. **Telapak kaki:** putar di pergelangan kaki supaya sumbu telapak CT berimpit dengan sumbu kulit kaki (dari tumit, z terkecil, ke ujung jari, z terbesar, pada titik kulit 3 cm di bawah pergelangan kaki dalam pita x tungkai itu) dan normal telapak menghadap +Y.
7. **Penghalusan:** setiap ruas di langkah 4–6 dioptimalkan lokal (rotasi ±10° di sendinya, geser ±10 mm) dengan biaya `mean(relu(skin.signed(p) + margin)²)`. Margin: gelang bahu 3 mm, lengan atas 8 mm, lengan bawah 5 mm, tangan 2 mm, telapak kaki 2 mm. Ruas anak mengikuti perubahan ruas induknya.
8. **Penerimaan per ruas** (dicatat di `report`): fraksi verteks dengan `signed > 2 mm`. Nilai ≤ 2% lulus; 2–10% dipakai dan dicatat di "Catatan keputusan"; > 10% membuat stem ruas itu masuk `SEGMENT_FALLBACKS` (diganti tulang BodyParts3D yang dipasang di Task 8) dan dicatat.

- [ ] **Step 1: Tulis tes yang gagal**

```python
# pipeline/tests/test_bonehub.py
import pytest
from atlas_pipeline.bonehub import bone_name_en, bone_segment, bone_side

@pytest.mark.parametrize("stem,name,side,segment", [
    ("VERTEBRA_C1", "Atlas", "none", "trunk"), ("VERTEBRA_L6", "Sixth lumbar vertebra", "none", "trunk"),
    ("RIB_8_LEFT", "Left eighth rib", "left", "trunk"), ("HIP_RIGHT", "Right hip bone", "right", "trunk"),
    ("FEMUR_LEFT", "Left femur", "left", "thigh"), ("FIBULA_RIGHT", "Right fibula", "right", "shank"),
    ("NAVICULAR_LEFT", "Navicular bone of left foot", "left", "foot"),
    ("PHALANGE_FOOT_1_RIGHT", "Phalanges of right big toe", "right", "foot"),
    ("CLAVICLE_LEFT", "Left clavicle", "left", "girdle"), ("ULNA_LEFT", "Left ulna", "left", "forearm"),
    ("TRIQUETRUM_RIGHT", "Right triquetral", "right", "hand"),
    ("PHALANGE_HAND_3_LEFT", "Phalanges of left middle finger", "left", "hand"),
    ("SKULL_CRANIAL_MAXILLA", "Cranium and maxilla", "none", "trunk"),
])
def test_bone_tables(stem, name, side, segment):
    assert (bone_name_en(stem), bone_side(stem), bone_segment(stem)) == (name, side, segment)
```

```python
# pipeline/tests/test_skeleton_fit.py
import numpy as np, pytest, trimesh
from scipy.spatial.transform import Rotation
from atlas_pipeline.registration import Similarity
from atlas_pipeline.skeleton_fit import fit_pairs, limb_centerline, repose_arm, repose_foot
from atlas_pipeline.skin_field import SkinField

def tube(start, end, radius):
    start, end = np.asarray(start, float), np.asarray(end, float)
    c = trimesh.creation.cylinder(radius=radius, segment=[start, end], sections=48)
    return c

def union(*meshes):
    return trimesh.util.concatenate(meshes)

def test_fit_pairs_recovers_known_transform():
    rot = Similarity(1.0, Rotation.from_rotvec([0, 0, 0.14]).as_matrix(), np.array([0.05, 0, 0.01]))
    bones = {"FEMUR_LEFT": tube([0.1, 0.5, 0], [0.12, 0.9, 0.02], 0.015)}
    bones["FEMUR_LEFT"].vertices[:3] += 0.01                       # sedikit tidak simetris
    targets = {"FEMUR_LEFT": rot.apply(bones["FEMUR_LEFT"].vertices)}
    found = fit_pairs(bones, targets, ["FEMUR_LEFT"], Similarity.identity(), with_scale=False)
    assert np.abs(found.apply(bones["FEMUR_LEFT"].vertices) - targets["FEMUR_LEFT"]).max() < 1e-3

ARM_TOP, ARM_BOTTOM = [0.17, 0.45, 0.0], [0.48, -0.22, 0.0]       # lengan lurus, terbuka ±25°, cukup panjang untuk tangan
SKIN = union(tube([0, -0.4, 0], [0, 0.6, 0], 0.15), tube(ARM_TOP, ARM_BOTTOM, 0.045))

def test_limb_centerline_follows_tilted_tube():
    line = limb_centerline(SkinField(SKIN.vertices, SKIN.faces, samples=200_000), "left", below_y=0.3)
    line = line[line[:, 1] > -0.15]                                  # jauhi tutup ujung tabung
    axis = (np.array(ARM_BOTTOM) - ARM_TOP) / np.linalg.norm(np.subtract(ARM_BOTTOM, ARM_TOP))
    offsets = line - ARM_TOP; dist = np.linalg.norm(offsets - np.outer(offsets @ axis, axis), axis=1)
    assert len(line) > 20 and dist.max() < 0.004

def test_repose_arm_puts_bent_arm_inside_straight_tube():
    skin = SkinField(SKIN.vertices, SKIN.faces, samples=200_000)
    shoulder, elbow = np.array([0.18, 0.43, 0]), np.array([0.19, 0.15, 0])
    wrist = elbow + [0.0, -0.08, 0.22]                               # siku menekuk 70° ke depan, seperti CT
    bones = {"CLAVICLE_LEFT": tube([0.02, 0.50, 0.03], [0.12, 0.50, 0.0], 0.008).vertices,    # gelang bahu di dalam badan
             "SCAPULA_LEFT": tube([0.08, 0.45, -0.08], [0.10, 0.35, -0.09], 0.01).vertices,
             "HUMERUS_LEFT": tube(shoulder, elbow, 0.011).vertices,
             "RADIUS_LEFT": tube(elbow + [0.01, -0.01, 0.0], wrist, 0.008).vertices,
             "ULNA_LEFT": tube(elbow + [-0.01, -0.01, 0.0], wrist, 0.008).vertices,
             "PHALANGE_HAND_3_LEFT": tube(wrist, wrist + [0, -0.02, 0.15], 0.006).vertices,
             "METACARPAL_3_LEFT": tube(wrist, wrist + [0, -0.01, 0.08], 0.006).vertices}
    centerline = limb_centerline(skin, "left", below_y=0.3)
    placed = repose_arm(bones, Similarity.identity(), centerline, skin, "left")
    seg = {"CLAVICLE_LEFT": "girdle", "SCAPULA_LEFT": "girdle", "HUMERUS_LEFT": "upperarm", "RADIUS_LEFT": "forearm",
           "ULNA_LEFT": "forearm", "PHALANGE_HAND_3_LEFT": "hand", "METACARPAL_3_LEFT": "hand"}
    pts = np.concatenate([placed[seg[s]].apply(v) for s, v in bones.items()])
    assert np.mean(skin.signed(pts) > 0.002) <= 0.02

def test_repose_foot_turns_pointed_foot_flat():
    ankle = np.array([0.1, 0.08, -0.05])
    leg = tube(ankle, ankle + [0, 0.42, 0], 0.04)
    sole = trimesh.creation.box([0.09, 0.07, 0.26]).apply_translation([0.1, 0.035, 0.03])   # telapak rata, ke +Z
    shape = union(leg, sole)
    skin = SkinField(shape.vertices, shape.faces, samples=200_000)
    down = Rotation.from_rotvec([0.7, 0, 0])                         # menjinjit ±40°
    def bone(extents, center):
        return down.apply(trimesh.creation.box(extents).subdivide().subdivide().vertices + center) + ankle
    bones = {"TALUS_LEFT": bone([0.03, 0.03, 0.04], [0, 0, 0]),
             "CALCANEUS_LEFT": bone([0.04, 0.04, 0.07], [0, -0.01, -0.03]),
             "METATARSAL_2_LEFT": bone([0.015, 0.015, 0.08], [0, -0.005, 0.1])}
    placed = repose_foot(bones, Similarity.identity(), skin, "left")
    pts = placed.apply(np.concatenate(list(bones.values())))
    main = np.linalg.svd(pts - pts.mean(0))[2][0]
    assert abs(main[2]) > np.cos(np.radians(5))
```

- [ ] **Step 2: Jalankan, pastikan gagal**

Run: `cd pipeline && .venv/Scripts/python -m pytest tests/test_bonehub.py tests/test_skeleton_fit.py -q`
Expected: FAIL, modul belum ada.

- [ ] **Step 3: Implementasi `bonehub.py`**

- [ ] **Step 4: Implementasi `skeleton_fit.py` sesuai algoritma di atas**

Fungsi titik sendi menerima kamus stem → verteks, supaya tes sintetis di Step 1 bisa memakai potongan tulang yang sama. Di tes, `repose_foot` memakai stem `TALUS_*`, `CALCANEUS_*`, dan `METATARSAL_2_*`.

- [ ] **Step 5: Jalankan, pastikan lulus**

Run: `cd pipeline && .venv/Scripts/python -m pytest -q`
Expected: semua lulus.

- [ ] **Step 6: Periksa dengan data asli**

Tulis `test_real_skeleton_fit` (realdata) yang memuat 143 tulang dan HRA, menjalankan `fit_skeleton`, lalu menyimpan `report` ke `data/work/female/skeleton-report.json`. Tes ini memastikan:
- rata-rata galat setiap tulang `TRUNK_PAIRS` ≤ 5 mm (pengintaian: 1,2–4,4 mm);
- rata-rata galat setiap tulang `LEG_PAIRS` ≤ 5 mm (pengintaian: 1,4–4,7 mm);
- setiap ruas yang ditekuk ulang ≤ 2% verteks di luar kulit lebih dari 2 mm, atau stemnya ada di `SEGMENT_FALLBACKS`.

Run: `cd pipeline && .venv/Scripts/python -m pytest tests/test_skeleton_fit.py -m realdata -q`

Kalau ada ruas yang gagal, ikuti aturan penerimaan di langkah 8 algoritma, lalu catat angka dan keputusannya di "Catatan keputusan".

- [ ] **Step 7: Commit**

```bash
git add pipeline docs/superpowers/plans/2026-11-03-tahap-2-perempuan.md
git commit -m "feat(pipeline): kerangka perempuan BoneHub di ruang HRA, lengan dan kaki ditekuk ulang"
```

---

### Task 7: Otot dan sendi tungkai dari Andreassen

**Files:**
- Create: `pipeline/atlas_pipeline/andreassen.py`
- Test: `pipeline/tests/test_andreassen.py`

**Interfaces:**
- Consumes: `SkeletonFit`, `load_bonehub` (Task 6); `ThinPlateWarp`, `sample_control_points`, `icp`, `mean_distance_mm` (Task 5); `Part` (Task 2); `require_andreassen` (Task 1).
- Produces:
  - `ANDREASSEN_MUSCLES: tuple[tuple[str, str], ...]`: 38 pasang (kunci, templat nama Inggris BodyParts3D dengan `{side}`/`{Side}`), misalnya `("gluteus maximus", "{Side} gluteus maximus")`, `("biceps femoris long", "Long head of {side} biceps femoris")`, `("gastrocnemius lateral", "Lateral head of {side} gastrocnemius")`, `("peroneus longus", "{Side} fibularis longus")`, `("inferior gemellus", "{Side} gemellus inferior")`, `("semitendinosus", "{Side} semitendinosus")`. Ke-38 kunci mengikuti Tabel 3 makalah Andreassen: adductor brevis/longus/magnus, biceps femoris long/short, extensor digitorum longus, extensor hallucis longus, flexor digitorum longus, flexor hallucis longus, gastrocnemius lateral/medial, gluteus maximus/medius/minimus, gracilis, iliacus, inferior gemellus, obturator externus/internus, pectineus, peroneus longus, piriformis, plantaris, popliteus, psoas major, quadratus femoris, rectus femoris, sartorius, semimembranosus, semitendinosus, soleus, superior gemellus, tensor fasciae latae, tibialis anterior/posterior, vastus intermedius/lateralis/medialis.
  - `@dataclass class TissueItem`: `kind: Literal["muscle", "ligament", "cartilage", "bone"]`, `key: str`, `side: Side`, `name_en: str`, `member: str`, `vertices: np.ndarray`, `faces: np.ndarray`.
  - `classify_member(member: str) -> tuple[str, str, Side] | None`: `(kind, key, side)`, atau `None` untuk lemak. Pencocokan memakai kata kunci di seluruh path yang sudah dinormalkan (huruf kecil, pemisah menjadi spasi, salah ketik `l` untuk `I` di awal kata diperbaiki, "semitendonosus" → "semitendinosus"). Anggota yang tidak dikenal melempar `ValueError` yang menyebut nama anggotanya.
  - `read_andreassen(zip_path: Path) -> list[TissueItem]`: STL (mm) ke sumbu atlas lewat `to_atlas_space`, dibaca langsung dari zip tanpa diekstrak.
  - `align_andreassen(items: list[TissueItem], bones_ct: dict[str, trimesh.Trimesh]) -> tuple[list[TissueItem], float]`: bandingkan femur dan tibia Andreassen dengan BoneHub. Kalau rata-rata jaraknya > 3 mm, semua item digeser dengan `icp` kaku (femur + tibia + panggul). Kembaliannya item dan galat awal dalam mm.
  - `warp_ct_tissue(items: list[TissueItem], bones_ct: dict[str, trimesh.Trimesh], fit: SkeletonFit) -> list[TissueItem]`: `ThinPlateWarp` dari 40 titik kontrol per tulang (seed 21) untuk tulang panggul, sakrum, L1–L6, dan semua tulang tungkai dan kaki. Sumbernya posisi CT dan targetnya `fit.placement[stem].apply(...)`.
  - `tissue_to_parts(items: list[TissueItem], fma_by_key: dict[tuple[str, Side], str]) -> list[Part]`: hanya `muscle`, `ligament`, dan `cartilage`. `id = f"AND:{kind}:{key.replace(' ', '-')}:{side}"`, sistem `muscular` untuk otot dan `connective` untuk sisanya, asal `perempuan-asli`, sumber `andreassen`, `source_ref = member`, catatan `pose-disesuaikan`. Nama Inggris otot dari templat; nama ligamen dan tulang rawan dari nama file yang dirapikan, dengan sisi di depan.

- [ ] **Step 1: Tulis tes yang gagal**

```python
# pipeline/tests/test_andreassen.py
import numpy as np, pytest, trimesh
from atlas_pipeline.andreassen import ANDREASSEN_MUSCLES, TissueItem, classify_member, tissue_to_parts, warp_ct_tissue
from atlas_pipeline.registration import Similarity
from atlas_pipeline.skeleton_fit import SkeletonFit

@pytest.mark.parametrize("member,expected", [
    ("VHF/Left/Muscles/Semitendonosus.stl", ("muscle", "semitendinosus", "left")),
    ("VHF/Right/Muscles/lliacus.stl", ("muscle", "iliacus", "right")),
    ("Gastrocnemius_Lateral_L.stl", ("muscle", "gastrocnemius lateral", "left")),
    ("R_Biceps_Femoris_Short.stl", ("muscle", "biceps femoris short", "right")),
    ("VHF/Left/Bones/Femur.stl", ("bone", "femur", "left")),
    ("VHF/Left/Ligaments/Anterior_Cruciate.stl", ("ligament", "anterior cruciate", "left")),
    ("VHF/Right/Cartilage/Tibiofemoral_Cartilage.stl", ("cartilage", "tibiofemoral", "right")),
    ("VHF/Left/Fat/Outer_Fat.stl", None),
])
def test_classify_member_handles_typos_and_sides(member, expected):
    assert classify_member(member) == expected

def test_unknown_member_is_an_error():
    with pytest.raises(ValueError, match="Mystery"):
        classify_member("VHF/Left/Muscles/Mystery.stl")

def test_muscle_table_has_38_muscles_named_like_bodyparts3d():
    assert len(ANDREASSEN_MUSCLES) == 38
    box = trimesh.creation.box()
    item = TissueItem("muscle", "biceps femoris long", "left", "", "m.stl", box.vertices, box.faces)
    (part,) = tissue_to_parts([item], {("biceps femoris long", "left"): "FMA22357"})
    assert (part.id, part.names["en"], part.fma, part.origin) == (
        "AND:muscle:biceps-femoris-long:left", "Long head of left biceps femoris", "FMA22357", "perempuan-asli")

def test_warp_ct_tissue_follows_bone_placements():
    femur = trimesh.creation.cylinder(radius=0.02, segment=[[0.1, 0.5, 0], [0.1, 0.9, 0]])
    shift = Similarity(1.0, np.eye(3), np.array([0.05, 0.0, 0.0]))
    fit = SkeletonFit(Similarity.identity(), {"FEMUR_LEFT": shift}, {"FEMUR_LEFT": "thigh-left"}, {}, frozenset())
    muscle = TissueItem("muscle", "vastus lateralis", "left", "", "m.stl", femur.vertices + [0.03, 0, 0], femur.faces)
    (moved,) = warp_ct_tissue([muscle], {"FEMUR_LEFT": femur}, fit)
    assert np.allclose(moved.vertices, muscle.vertices + [0.05, 0, 0], atol=1e-4)
```

- [ ] **Step 2: Jalankan, pastikan gagal**

Run: `cd pipeline && .venv/Scripts/python -m pytest tests/test_andreassen.py -q`
Expected: FAIL, modul belum ada.

- [ ] **Step 3: Implementasi `andreassen.py`**

- [ ] **Step 4: Jalankan, pastikan lulus**

Run: `cd pipeline && .venv/Scripts/python -m pytest -q`
Expected: semua lulus.

- [ ] **Step 5: Periksa zip asli**

Tulis `test_real_andreassen` (realdata): semua anggota zip terklasifikasi, ada tepat 76 otot (38 per sisi), dan galat awal `align_andreassen` dilaporkan (harapannya ≤ 3 mm, karena BoneHub dibuat dari CT selaras milik Andreassen).

Run: `cd pipeline && .venv/Scripts/python -m pytest tests/test_andreassen.py -m realdata -q`

Kalau nama anggota zip asli tidak cocok dengan pola, tambahkan kasusnya ke tes parametris di Step 1 dulu, lalu perbaiki `classify_member`. Catat galat awal dan struktur zip di "Catatan keputusan".

- [ ] **Step 6: Commit**

```bash
git add pipeline docs/superpowers/plans/2026-11-03-tahap-2-perempuan.md
git commit -m "feat(pipeline): 76 otot dan sendi tungkai Andreassen, dipindah mengikuti kerangka"
```

---

### Task 8: Bagian BodyParts3D yang dipasang ke badan perempuan

**Files:**
- Create: `pipeline/atlas_pipeline/crosswalk.py`, `pipeline/atlas_pipeline/bp3d_fitted.py`
- Test: `pipeline/tests/test_crosswalk.py`, `pipeline/tests/test_bp3d_fitted.py`

**Interfaces:**
- Consumes: `Part`, `read_bp3d_parts` (Task 2); `ElementConcepts` (tahap 1); `ANDREASSEN_MUSCLES` (Task 7); `ThinPlateWarp`, `sample_control_points`, `icp`, `umeyama`, `SkinField` (Task 5); `SkeletonFit`, `SEGMENT_FALLBACKS`, `bone_segment` (Task 6).
- Produces:
  - `bonehub_stem_for(name_en: str) -> str | None`: stem BoneHub untuk nama tulang BodyParts3D. Contoh: "Fifth thoracic vertebra" → `VERTEBRA_T5`, "Atlas" → `VERTEBRA_C1`, "Body of sternum"/"Manubrium"/"Xiphoid process" → `STERNUM`, tulang tengkorak (frontal, occipital, parietal, temporal, sphenoid, ethmoid, vomer, lacrimal, nasal, palatine, maxilla, zygomatic, inferior nasal concha) → `SKULL_CRANIAL_MAXILLA`, "Mandible" → `SKULL_MANDIBLE`, "Left hip bone" → `HIP_LEFT`, falang → `PHALANGE_HAND_n_*`/`PHALANGE_FOOT_n_*` per jari, dan karpal, tarsal, metakarpal, metatarsal, serta rusuk per nama.
  - `FIT_ONLY_BONES = ("Hyoid bone", "Sesamoid bone of left foot", "Sesamoid bone of right foot")`, `is_tooth(name_en: str) -> bool` (nama memuat `tooth`).
  - `andreassen_key_for(name_en: str) -> tuple[str, Side] | None`: kebalikan dari templat `ANDREASSEN_MUSCLES`. "Left adductor minimus" juga dipetakan ke `("adductor magnus", "left")`.
  - `select_fitted(parts: list[Part], concepts: dict[str, ElementConcepts], hra_vessel_names: set[str]) -> tuple[list[Part], list[dict]]`: bagian yang dipasang dan laporan `{"id", "name", "decision", "reason"}` untuk semua bagian. `hra_vessel_names` berisi nama Inggris pembuluh HRA dalam huruf kecil tanpa akhiran " (x)".
  - `fit_bp3d(selected: list[Part], bp3d_bones: list[Part], bp3d_skin: Part | None, female_bones: dict[str, np.ndarray], skin: SkinField) -> list[Part]`. `female_bones` adalah stem → verteks yang sudah ditempatkan. Kembaliannya bagian dengan asal `dipasang-dari-laki-laki` dan sumber `bodyparts3d` (id `BP3D:<FJ>` tetap). Urutan kerjanya:
    1. transformasi awal global = `umeyama` dari pusat tulang BodyParts3D ke pusat tulang perempuan, untuk semua stem berpasangan (translasi saja bila stemnya kurang dari tiga);
    2. per stem, `icp` dengan skala dari gabungan tulang BodyParts3D ke tulang perempuan; 24 titik kontrol (seed 31) per stem dipetakan dengan transformasi tulang itu;
    3. `warp1 = ThinPlateWarp.fit(kontrol tulang)`;
    4. 4.000 titik pada `bp3d_skin` setelah `warp1`, berpasangan dengan titik kulit HRA terdekat bila jaraknya < 3 cm dan normalnya searah (dot > 0,5). `warp2 = ThinPlateWarp.fit(pasangan kulit + titik kontrol tulang dengan perpindahan nol, smoothing=1e-3)`. Bila `bp3d_skin` adalah `None`, `warp2` adalah identitas;
    5. setiap verteks = `skin.clamp_inside(warp2(warp1(v)), margin=0.001)`.

Aturan `select_fitted` per sistem bagian laki-laki (dicek berurutan dalam setiap baris):

| Sistem | Dipasang | Tidak dipasang (alasan) |
|---|---|---|
| muscular | semua yang lain | punya padanan Andreassen (`andreassen-dup`); otot ekstraokular, yaitu nama yang persis cocok `^(Left\|Right) (medial\|lateral\|superior\|inferior) (rectus\|oblique)$` (`hra-eye`) |
| skeletal | `FIT_ONLY_BONES`, dan tulang yang stem BoneHub-nya ada di `SEGMENT_FALLBACKS` | punya padanan BoneHub (`bonehub`); gigi (`hra-teeth`) |
| connective | semua yang lain, termasuk tulang rawan iga | `Intervertebral disk…` (`hra-disk`) |
| respiratory | nama cocok `cuneiform cartilage\|conus elasticus\|vocal ligament\|epiglottic ligament\|pharyngeal raphe` | selebihnya (`hra-airway`) |
| digestive | `Esophagus`, `Stomach`, `Lip` | selebihnya (`hra-digestive`) |
| endocrine | semua (kelenjar adrenal, hipofisis) | — |
| arterial, venous | semua yang lain | nama (huruf kecil) ada di `hra_vessel_names` (`hra-vessel`); nama cocok `aort\|vena cava\|pulmonary (trunk\|artery\|vein)\|coronary\|cardiac vein\|coronary sinus\|brachiocephalic trunk\|mesenteric\|colic\|renal (artery\|vein)\|hepatic\|portal\|splenic\|celiac\|rectal\|sigmoid\|cystic\|ileocolic\|pancreaticoduodenal\|ophthalmic\|retinal\|ciliary\|uterine` (`hra-territory`); `testicular\|cremaster\|penis\|penile\|scrot\|prostat\|vesicul\|deferen` (`male-only`) |
| nervous | PART-OF memuat FMA9903 (sistem saraf tepi), atau nama cocok `nerve\|ganglion\|plexus\|ramus` | PART-OF memuat FMA50801 (otak) atau FMA7647 (sumsum tulang belakang), atau nama cocok `ventricle\|aqueduct\|choroid plexus\|tentorium\|optic (nerve\|chiasm\|tract)` (`hra-cns`) |
| sensory | nama cocok `external ear\|lacrimal\|nasolacrimal\|retinaculum` dan bagian telinga | bagian bola mata (`hra-eye`) |
| integumentary, cardiac, lymphatic, urinary kecuali `ureter`, reproductive | — | `hra-skin`, `hra-heart`, `hra-lymphatic`, `hra-urinary`, `male-only` |

Ureter BodyParts3D tidak dipasang karena HRA punya `VH_F_left_ureter`/`VH_F_right_ureter`; uretra laki-laki tidak dipasang (`male-only`).

- [ ] **Step 1: Tulis tes yang gagal**

```python
# pipeline/tests/test_crosswalk.py
import json, re
from pathlib import Path
import pytest
from atlas_pipeline.crosswalk import FIT_ONLY_BONES, andreassen_key_for, bonehub_stem_for, is_tooth

@pytest.mark.parametrize("name,stem", [
    ("Fifth thoracic vertebra", "VERTEBRA_T5"), ("Atlas", "VERTEBRA_C1"), ("Axis", "VERTEBRA_C2"),
    ("Body of sternum", "STERNUM"), ("Xiphoid process", "STERNUM"), ("Left temporal bone", "SKULL_CRANIAL_MAXILLA"),
    ("Mandible", "SKULL_MANDIBLE"), ("Left hip bone", "HIP_LEFT"), ("Left eighth rib", "RIB_8_LEFT"),
    ("Proximal phalanx of left thumb", "PHALANGE_HAND_1_LEFT"), ("Distal phalanx of right little toe", "PHALANGE_FOOT_5_RIGHT"),
    ("Navicular bone of left foot", "NAVICULAR_LEFT"), ("Left triquetral", "TRIQUETRUM_LEFT"),
    ("Left first metatarsal bone", "METATARSAL_1_LEFT"), ("Right fifth metacarpal bone", "METACARPAL_5_RIGHT"),
    ("Hyoid bone", None),
])
def test_bonehub_stem_for(name, stem):
    assert bonehub_stem_for(name) == stem

def test_every_male_bone_has_a_female_counterpart_or_rule():
    manifest = json.loads((Path(__file__).parents[2] / "public/models/male/manifest.json").read_text("utf-8"))
    loose = [p["names"]["en"] for p in manifest["parts"] if p["system"] == "skeletal"
             and bonehub_stem_for(p["names"]["en"]) is None and p["names"]["en"] not in FIT_ONLY_BONES
             and not is_tooth(p["names"]["en"])]
    assert loose == []

def test_andreassen_key_for():
    assert andreassen_key_for("Long head of right biceps femoris") == ("biceps femoris long", "right")
    assert andreassen_key_for("Left adductor minimus") == ("adductor magnus", "left")
    assert andreassen_key_for("Left fibularis brevis") is None
```

```python
# pipeline/tests/test_bp3d_fitted.py
import numpy as np, pytest, trimesh
from atlas_pipeline.bp3d_tables import ElementConcepts
from atlas_pipeline.bp3d_fitted import fit_bp3d, select_fitted
from atlas_pipeline.parts import Part
from atlas_pipeline.skin_field import SkinField

BOX = trimesh.creation.box(extents=[0.01, 0.01, 0.01])
def part(name, system, fj="FJ1"):
    return Part(f"BP3D:{fj}", system, "none", "laki-laki-asli", "bodyparts3d", fj, {"en": name}, BOX.vertices, BOX.faces)
NONE = ElementConcepts(frozenset(), frozenset())

@pytest.mark.parametrize("name,system,partof,kept", [
    ("Left gluteus maximus", "muscular", (), False), ("Left deltoid", "muscular", (), True),
    ("Left medial rectus", "muscular", (), False), ("Rectus capitis anterior", "muscular", (), True),
    ("Hyoid bone", "skeletal", (), True), ("Left femur", "skeletal", (), False), ("Lower secondary canine tooth", "skeletal", (), False),
    ("Left first costal cartilage", "connective", (), True), ("Intervertebral disk of axis", "connective", (), False),
    ("Stomach", "digestive", (), True), ("Liver", "digestive", (), False), ("Left adrenal gland", "endocrine", (), True),
    ("Left renal artery", "arterial", (), False), ("Left femoral artery", "arterial", (), True),
    ("Brachiocephalic trunk", "arterial", (), False), ("Left testicular artery", "arterial", (), False),
    ("Left sciatic nerve", "nervous", ("FMA9903",), True), ("Pons", "nervous", ("FMA50801",), False),
    ("External ear", "sensory", (), True), ("Left lens", "sensory", (), False),
    ("Skin", "integumentary", (), False), ("Urethra", "urinary", (), False), ("Spleen", "lymphatic", (), False),
])
def test_select_fitted_rules(name, system, partof, kept):
    p = part(name, system)
    selected, report = select_fitted([p], {p.id: ElementConcepts(frozenset(), frozenset(partof))}, {"left renal artery"})
    assert (selected == [p]) is kept and len(report) == 1

def test_fit_bp3d_follows_bones_and_stays_inside_skin():
    femur = trimesh.creation.cylinder(radius=0.02, segment=[[0.1, 0.5, 0], [0.1, 0.9, 0]])
    bone = Part("BP3D:FJ9", "skeletal", "left", "laki-laki-asli", "bodyparts3d", "FJ9", {"en": "Left femur"}, femur.vertices, femur.faces)
    shell = trimesh.creation.cylinder(radius=0.06, segment=[[0.15, 0.4, 0], [0.15, 1.0, 0]])
    skin = SkinField(shell.vertices, shell.faces, samples=100_000)
    muscle = part("Left vastus lateralis", "muscular", "FJ8")
    muscle = Part(**{**muscle.__dict__, "vertices": femur.vertices + [0.035, 0, 0]})
    (fitted,) = fit_bp3d([muscle], [bone], None, {"FEMUR_LEFT": femur.vertices + [0.05, 0, 0]}, skin)
    assert fitted.origin == "dipasang-dari-laki-laki"
    assert abs(fitted.vertices[:, 0].mean() - (muscle.vertices[:, 0].mean() + 0.05)) < 0.01
    assert (skin.signed(fitted.vertices) <= 0).all()
```

- [ ] **Step 2: Jalankan, pastikan gagal**

Run: `cd pipeline && .venv/Scripts/python -m pytest tests/test_crosswalk.py tests/test_bp3d_fitted.py -q`
Expected: FAIL, modul belum ada.

- [ ] **Step 3: Implementasi `crosswalk.py` dan `bp3d_fitted.py`**

Sebelum aturan sistem saraf dipakai, pastikan ID FMA-nya benar: di `partof_parts_list_e.txt`, FMA9903 harus "peripheral nervous system", FMA50801 "brain", dan FMA7647 "spinal cord". Kalau berbeda, perbaiki ID di aturan dan di tes.

- [ ] **Step 4: Jalankan, pastikan lulus**

Run: `cd pipeline && .venv/Scripts/python -m pytest -q`
Expected: semua lulus.

- [ ] **Step 5: Commit**

```bash
git add pipeline
git commit -m "feat(pipeline): pilih dan pasang bagian BodyParts3D ke badan perempuan"
```

---

### Task 9: Pemeriksaan otomatis

**Files:**
- Modify: `pipeline/atlas_pipeline/checks.py`
- Test: `pipeline/tests/test_checks.py`

**Interfaces:**
- Consumes: `Part` (Task 2), `SkinField` (Task 5).
- Produces:
  - `OUTSIDE_MM = 5.0`, `OUTSIDE_FRACTION = 0.02`
  - `outside_skin(parts: list[Part], skin: SkinField) -> list[dict]`: untuk setiap bagian di luar sistem `integumentary`: `{"id", "fraction", "max_mm"}`, dengan `fraction` = bagian verteks yang > `OUTSIDE_MM` di luar kulit (maksimal 3.000 verteks per bagian, seed 41).
  - `contained_fraction(points: np.ndarray, container_points: np.ndarray) -> float`: fraksi titik di dalam selubung cembung (`scipy.spatial.Delaunay.find_simplex >= 0`).
  - `vessel_gaps(fitted: list[Part], hra: list[Part], within_m: float = 0.03) -> list[dict]`: untuk setiap pembuluh dipasang, pembuluh HRA terdekat dalam 3 cm dan celahnya dalam mm, `{"fitted", "hra", "gap_mm"}`, urut dari celah terbesar. Hanya laporan, tidak menggagalkan apa pun.
  - `side_mismatches(parts: list[Part], tolerance_m: float = 0.05) -> list[str]`: id bagian yang pusat x-nya melewati ±0,05 m tetapi bertentangan dengan sisinya. Koordinatnya ruang atlas, sebelum translasi (kiri di +X).
  - `duplicate_names(parts: list[Part]) -> list[tuple[str, str]]`: pasangan id dari **sumber berbeda** dengan `names.en` (huruf kecil, tanpa akhiran " (x)") dan sisi yang sama.

- [ ] **Step 1: Tulis tes yang gagal**

Tambahkan ke `test_checks.py`:

```python
import trimesh
from atlas_pipeline.checks import contained_fraction, duplicate_names, outside_skin, side_mismatches, vessel_gaps
from atlas_pipeline.parts import Part
from atlas_pipeline.skin_field import SkinField

def P(id, en, side, source, verts, system="muscular"):
    return Part(id, system, side, "perempuan-asli", source, id, {"en": en}, np.asarray(verts, float), np.array([[0, 1, 2]]))

def test_outside_skin_measures_the_part_that_pokes_out():
    sphere = trimesh.creation.icosphere(subdivisions=4, radius=0.1)
    pts = np.array([[0, 0, 0], [0.0, 0.05, 0], [0.13, 0, 0], [0, 0.13, 0]])
    (row,) = outside_skin([P("a", "A", "none", "hra", pts)], SkinField(sphere.vertices, sphere.faces, samples=50_000))
    assert abs(row["fraction"] - 0.5) < 1e-9 and abs(row["max_mm"] - 30) < 3

def test_contained_fraction_in_a_cube():
    cube = trimesh.creation.box().vertices
    assert contained_fraction(np.array([[0, 0, 0], [0.4, 0.4, 0.4], [2, 0, 0], [0, 0, 3]]), cube) == 0.5

def test_vessel_gaps_reports_millimetres():
    a = P("BP3D:FJ1", "Right subclavian artery", "right", "bodyparts3d", [[0, 0, 0], [0.01, 0, 0], [0.02, 0, 0]], "arterial")
    b = P("HRA:x", "Brachiocephalic artery", "none", "hra", [[0.025, 0, 0], [0.03, 0, 0], [0.04, 0, 0]], "arterial")
    assert vessel_gaps([a], [b]) == [{"fitted": "BP3D:FJ1", "hra": "HRA:x", "gap_mm": pytest.approx(5.0)}]

def test_side_mismatches_flags_left_part_on_the_right():
    tri = lambda x: [[x, 1, 0], [x + 0.01, 1, 0], [x, 1.1, 0]]
    parts = [P("a", "Left femur", "left", "bonehub", tri(-0.12)), P("b", "Left x", "left", "hra", tri(0.1)),
             P("c", "Left y", "left", "hra", tri(-0.02))]
    assert side_mismatches(parts) == ["a"]

def test_duplicate_names_across_sources():
    v = [[0, 0, 0], [1, 0, 0], [0, 1, 0]]
    parts = [P("HRA:a", "Left ureter", "left", "hra", v), P("BP3D:FJ1", "left ureter", "left", "bodyparts3d", v),
             P("HRA:b", "Renal papilla (a)", "left", "hra", v), P("HRA:c", "Renal papilla (b)", "left", "hra", v)]
    assert duplicate_names(parts) == [("HRA:a", "BP3D:FJ1")]
```

(`import pytest` ada di kepala file.)

- [ ] **Step 2: Jalankan, pastikan gagal**

Run: `cd pipeline && .venv/Scripts/python -m pytest tests/test_checks.py -q`
Expected: FAIL, `ImportError`.

- [ ] **Step 3: Implementasi kelima fungsi di `checks.py`**

- [ ] **Step 4: Jalankan, pastikan lulus**

Run: `cd pipeline && .venv/Scripts/python -m pytest -q`
Expected: semua lulus.

- [ ] **Step 5: Commit**

```bash
git add pipeline
git commit -m "feat(pipeline): periksa bagian yang menembus kulit, sisi, nama ganda, dan celah pembuluh"
```

---

### Task 10: Rakit badan perempuan dan jalankan dengan data asli

**Files:**
- Create: `pipeline/atlas_pipeline/package_female.py`
- Modify: `pipeline/atlas_pipeline/__main__.py`, `pipeline/atlas_pipeline/wikidata.py`, `pipeline/cache/` (cache UBERON baru, CC0)
- Test: `pipeline/tests/test_package_female.py`, `pipeline/tests/test_wikidata.py`

**Interfaces:**
- Consumes: semua task 1–9.
- Produces:
  - `load_uberon_labels(cache: Path, refresh: bool = False) -> dict[str, dict[str, str]]`: sama dengan `load_fma_labels`, tetapi untuk properti P1554 (UBERON ID). Kunci dinormalkan menjadi `"UBERON:" + 7 digit` dari nilai `UBERON_0002107`, `UBERON:0002107`, atau `0002107`. Cache di `pipeline/cache/wikidata-uberon-labels.json`.
  - `class AssemblyError(RuntimeError)`
  - `assemble_female(groups: dict[str, list[Part]], work_dir: Path, outside: list[dict], allowed_outside: frozenset[str]) -> dict`. `groups` berisi kunci `hra`, `bonehub`, `andreassen`, dan `bodyparts3d`. Fungsi ini melempar `AssemblyError` (dengan daftar id) bila ada id ganda, asal di luar `perempuan-asli`/`dipasang-dari-laki-laki`, `side_mismatches`, `duplicate_names`, atau baris `outside` dengan `fraction > OUTSIDE_FRACTION` yang id-nya tidak ada di `allowed_outside`. Kalau semuanya bersih, ia memanggil `write_body(…, "female")`.
  - `ALLOWED_OUTSIDE: frozenset[str] = frozenset()`: bagian asli perempuan yang boleh sedikit keluar dari kulit, masing-masing dengan alasan di "Catatan keputusan".
  - `build_female(raw_dir: Path, work_dir: Path, labels_fma, labels_uberon) -> dict`. Urutannya: baca HRA (`hra_to_parts`), muat BoneHub, `fit_skeleton`, Andreassen (`read` → `align` → `warp_ct_tissue`), BodyParts3D (`read_bp3d_parts` → `select_fitted` → `fit_bp3d`), lalu `fma_by_stem` dan `fma_by_key` dari padanan BodyParts3D (hanya bila tepat satu bagian BodyParts3D berpadanan). Label `id`/`la` dipasang lewat FMA dulu, lalu UBERON. Pemeriksaan: `outside_skin`; paru HRA ≥ 98% di dalam selubung cembung rusuk + sternum + vertebra toraks BoneHub; region otak `Allen_*` ≥ 99% di dalam selubung `SKULL_CRANIAL_MAXILLA`; dan `vessel_gaps`. Terakhir `assemble_female`. Semua angka ditulis ke `data/work/female/build-report.json` (`skeleton`, `andreassen`, `selection`, `excludedHra`, `checks`).
  - CLI `python -m atlas_pipeline female`: unduh HRA, BoneHub, dan BodyParts3D, `require_andreassen`, muat label FMA dan UBERON, lalu `build_female` dengan `raw_dir = data/raw`, `work_dir = data/work`. Yang dicetak hanya ringkasan (jumlah per sistem, per asal, dan hasil pemeriksaan).

- [ ] **Step 1: Tulis tes yang gagal**

```python
# pipeline/tests/test_package_female.py
import json, numpy as np, pytest
from atlas_pipeline.package_female import AssemblyError, assemble_female
from atlas_pipeline.parts import Part

def tri(x, y=1.0, z=0.0):
    return np.array([[x, y, z], [x + 0.01, y, z], [x, y + 0.05, z + 0.01]]), np.array([[0, 1, 2]])

def P(id, en, side, source, x, system="skeletal", origin="perempuan-asli", y=1.0, z=0.0):
    v, f = tri(x, y, z); return Part(id, system, side, origin, source, id, {"en": en}, v, f)

GROUPS = {
    "hra": [P("HRA:VH_F_skin", "Skin", "none", "hra", -0.2, "integumentary", y=-0.79), P("HRA:nose", "Nose", "none", "hra", 0.0, "integumentary", y=0.8, z=0.12)],
    "bonehub": [P("BH:FEMUR_LEFT", "Left femur", "left", "bonehub", 0.12)],
    "andreassen": [P("AND:muscle:soleus:right", "Right soleus", "right", "andreassen", -0.1, "muscular")],
    "bodyparts3d": [P("BP3D:FJ1", "Left deltoid", "left", "bodyparts3d", 0.2, "muscular", "dipasang-dari-laki-laki")],
}

def test_assembled_body_keeps_left_positive_x_and_front_positive_z(tmp_path):
    parts = {p["id"]: p for p in assemble_female(GROUPS, tmp_path, [], frozenset())["parts"]}
    cx = lambda p: (p["bounds"][0][0] + p["bounds"][1][0]) / 2
    assert cx(parts["BH:FEMUR_LEFT"]) > 0 > cx(parts["AND:muscle:soleus:right"])
    assert parts["HRA:nose"]["bounds"][1][2] == max(p["bounds"][1][2] for p in parts.values())
    assert min(p["bounds"][0][1] for p in parts.values()) == 0.0
    assert {p["origin"] for p in parts.values()} == {"perempuan-asli", "dipasang-dari-laki-laki"}

def test_assembly_rejects_wrong_side_duplicates_and_male_origin(tmp_path):
    for bad in (P("BH:x", "Left x", "left", "bonehub", -0.3),
                P("BP3D:FJ2", "Left femur", "left", "bodyparts3d", 0.12, origin="dipasang-dari-laki-laki"),
                P("BP3D:FJ3", "Thing", "none", "bodyparts3d", 0.0, origin="laki-laki-asli")):
        with pytest.raises(AssemblyError, match=bad.id):
            assemble_female({**GROUPS, "extra": [bad]}, tmp_path, [], frozenset())

def test_assembly_fails_when_a_part_pokes_out_unless_allowed(tmp_path):
    outside = [{"id": "BH:FEMUR_LEFT", "fraction": 0.3, "max_mm": 12.0}]
    with pytest.raises(AssemblyError, match="BH:FEMUR_LEFT"):
        assemble_female(GROUPS, tmp_path, outside, frozenset())
    assert assemble_female(GROUPS, tmp_path, outside, frozenset({"BH:FEMUR_LEFT"}))["body"] == "female"
```

Tambahkan ke `test_wikidata.py` tes `parse_sparql_json` untuk UBERON: nilai `UBERON_0002107` dan `0002107` sama-sama menjadi kunci `UBERON:0002107`.

- [ ] **Step 2: Jalankan, pastikan gagal**

Run: `cd pipeline && .venv/Scripts/python -m pytest tests/test_package_female.py tests/test_wikidata.py -q`
Expected: FAIL, modul `package_female` belum ada.

- [ ] **Step 3: Implementasi `package_female.py`, `load_uberon_labels`, dan perintah `female` di `__main__.py`**

- [ ] **Step 4: Jalankan semua tes pipeline**

Run: `cd pipeline && .venv/Scripts/python -m pytest -q`
Expected: semua lulus.

- [ ] **Step 5: Jalankan dengan data asli**

Run: `cd pipeline && .venv/Scripts/python -m atlas_pipeline female`
Expected: exit 0, 15 file GLB di `data/work/female/`, `build-report.json` tanpa kegagalan, dan setiap bagian berasal `perempuan-asli` atau `dipasang-dari-laki-laki`.

Kalau perakitan gagal, perbaiki penyebabnya, jangan menurunkan ambang:
- **sisi salah:** periksa `hra_side` atau tabel BoneHub;
- **nama ganda:** tambahkan aturan pengecualian di Task 4 atau Task 8 beserta kasus tesnya;
- **bagian menembus kulit:** perbaiki penempatan di Task 6/7. Bagian asli perempuan baru boleh masuk `ALLOWED_OUTSIDE` bila ia memang struktur di permukaan kulit (misalnya puting dan areola) atau bila galatnya sisa pose yang sudah dicoba diperbaiki, dengan alasan dan angkanya dicatat.

Catat juga di "Catatan keputusan": jumlah bagian per sumber, ruas yang ditekuk ulang beserta angkanya, dan tiga celah pembuluh terbesar.

- [ ] **Step 6: Commit**

```bash
git add pipeline docs/superpowers/plans/2026-11-03-tahap-2-perempuan.md
git commit -m "feat(pipeline): rakit badan perempuan dari HRA, BoneHub, Andreassen, dan BodyParts3D"
```

---

### Task 11: Optimasi, validasi, dan anggaran unduhan

**Files:**
- Modify: `scripts/lib/models.mjs`, `scripts/optimize-glb.mjs`, `scripts/validate-models.mjs`, `package.json`
- Test: `scripts/lib/models.test.mjs`

**Interfaces:**
- Consumes: `data/work/female/*.glb` dan `manifest.draft.json` (Task 10).
- Produces:
  - `SIMPLIFY_ERROR = 0.002`, `SIMPLIFY_ERROR_OVERRIDES: Record<string, Partial<Record<string, number>>> = { female: {} }`, `simplifyError(body: string, system: string) -> number`.
  - `findSideProblems(manifest) -> string[]`: peringatan untuk bagian yang |pusat x| > 0,05 m tetapi sisinya bertentangan (temuan kecil tahap 1 no. 4). `validate-models` mencetaknya sebagai `PERINGATAN:` tanpa menggagalkan.
  - `findManifestProblems` juga melaporkan bagian badan `female` yang asalnya bukan `perempuan-asli` atau `dipasang-dari-laki-laki`.
  - Script npm `models:female` = `cd pipeline && .venv\\Scripts\\python -m atlas_pipeline female && cd .. && node --max-old-space-size=8192 scripts/optimize-glb.mjs female && node scripts/validate-models.mjs female`.
  - `public/models/female/<system>.glb` dan `manifest.json` (`body: 'female'`).

- [ ] **Step 1: Tulis tes yang gagal**

Tambahkan ke `scripts/lib/models.test.mjs`:

```js
import { findSideProblems, simplifyError, SIMPLIFY_ERROR_OVERRIDES } from './models.mjs';

test('budget flags initial layers above 40 MB', () => {
  const over = { parts: [], systems: [{ id: 'skeletal', bytes: 30 * 1048576 }, { id: 'digestive', bytes: 11 * 1048576 }, { id: 'muscular', bytes: 99 * 1048576 }] };
  const r = budgetReport(over);
  expect(r.initialBytes).toBe(41 * 1048576);
  expect(r.overBudget).toBe(true);
});

test('side problems ignore parts near the midline', () => {
  const part = (id, side, x) => ({ id, side, bounds: [[x - 0.01, 0, 0], [x + 0.01, 1, 0]] });
  expect(findSideProblems({ parts: [part('a', 'left', -0.2), part('b', 'left', 0.2), part('c', 'right', 0.03)] })).toEqual([expect.stringContaining('a')]);
});

test('female parts must be original or fitted', () => {
  const m = { body: 'female', parts: [{ id: 'x', system: 'skeletal', file: 'skeletal.glb', triangles: 1, origin: 'laki-laki-asli' }], systems: [] };
  expect(findManifestProblems(m, { skeletal: ['x'] })).toEqual([expect.stringContaining('x')]);
});

test('simplify error uses overrides per body and system', () => {
  SIMPLIFY_ERROR_OVERRIDES.female.integumentary = 0.004;
  expect(simplifyError('female', 'integumentary')).toBe(0.004);
  expect(simplifyError('female', 'skeletal')).toBe(0.002);
  expect(simplifyError('male', 'integumentary')).toBe(0.002);
  delete SIMPLIFY_ERROR_OVERRIDES.female.integumentary;
});
```

- [ ] **Step 2: Jalankan, pastikan gagal**

Run: `npx vitest run scripts/lib/models.test.mjs`
Expected: FAIL, ekspor belum ada.

- [ ] **Step 3: Implementasi di `models.mjs`; `optimize-glb.mjs` memakai `simplifyError(body, id)`; `validate-models.mjs` mencetak peringatan sisi; tambahkan script npm**

- [ ] **Step 4: Jalankan, pastikan lulus**

Run: `npx vitest run scripts/lib/models.test.mjs`
Expected: semua lulus.

- [ ] **Step 5: Bangun model perempuan**

Run: `npm run models:female`
Expected: 15 GLB di `public/models/female/`, ukuran per sistem tercetak, "lapisan awal" ≤ 40 MB, tanpa `PERINGATAN:` sisi, exit 0. Periksa juga `npm run models:validate -- male`: exit 0 tanpa peringatan sisi.

Kalau lapisan awal melebihi 40 MB, naikkan `SIMPLIFY_ERROR_OVERRIDES.female` untuk sistem awal yang terbesar, satu per satu ke 0,004, lalu ke 0,006 bila masih perlu, sampai lolos. Catat nilainya dan ukuran akhirnya di "Catatan keputusan".

- [ ] **Step 6: Commit (termasuk model olahan)**

```bash
git add scripts package.json public/models/female docs/superpowers/plans/2026-11-03-tahap-2-perempuan.md
git commit -m "feat(models): optimasi dan validasi GLB badan perempuan"
```

---

### Task 12: Atlas — manifest, asal dan sumber, catatan, tombol Perempuan

**Files:**
- Create: `src/atlas/sources.ts`, `src/ui/TopBar.test.tsx`
- Modify: `src/atlas/types.ts`, `src/atlas/manifest.ts`, `src/atlas/viewState.ts`, `src/ui/strings.ts`, `src/ui/InfoPanel.tsx`, `src/ui/TopBar.tsx`, `src/ui/useAtlas.ts`, `src/scene/AtlasScene.ts`
- Test: `src/atlas/manifest.test.ts`, `src/ui/InfoPanel.test.tsx`, `src/ui/TopBar.test.tsx`

**Interfaces:**
- Consumes: `public/models/female/manifest.json` (Task 11).
- Produces:
  - `type NoteKey = 'pose-disesuaikan' | 'siku-tidak-lengkap'`; `PartRecord` mendapat `uberon?: string` dan `notes?: NoteKey[]`.
  - `sourceLabel(source: string): string` dengan `hra` → `HuBMAP HRA`, `bonehub` → `BoneHub`, `andreassen` → `Andreassen dkk. 2023`, `bodyparts3d` → `BodyParts3D`; sumber lain tampil apa adanya.
  - `parseManifest(json, expectedBody?: BodyId)`: menolak `names.id`/`la`/`ringan`/`kesehatan` yang bukan teks, `notes` yang bukan `NoteKey`, dan badan yang berbeda dari `expectedBody` (temuan kecil no. 8). `loadManifest(body, baseUrl)` meneruskan `body` sebagai `expectedBody`.
  - `initialViewState(body: BodyId = 'female')`; `useAtlas` mulai dengan badan Perempuan.
  - Teks baru di `strings.ts` (dan `femaleSoon` dihapus):

| Kunci | Teks |
|---|---|
| bodySwitch | `Badan` |
| canvasLabel | `Tubuh 3D. Seret untuk memutar, cubit atau gulir untuk zoom, ketuk bagian untuk melihat namanya.` |
| originMale | `Asli laki-laki ({sumber})` |
| originFemale | `Asli perempuan ({sumber})` |
| originFitted | `Dipasang dari model laki-laki ({sumber})` |
| notes | `Catatan` |
| notePoseDisesuaikan | `Bagian ini asli perempuan, tetapi posisinya disesuaikan dengan pose berdiri.` |
| noteSikuTidakLengkap | `Ujung tulang di dekat siku tidak lengkap di data sumber, karena CT-nya terpotong di situ.` |

  - `TopBar`: tombol Perempuan aktif dan mengirim `setBody` `female`; `aria-label` grup memakai `STRINGS.bodySwitch`. `AtlasScene` memakai `STRINGS.canvasLabel` (temuan kecil no. 3).
  - `InfoPanel`: asal dengan `fill(..., { sumber: sourceLabel(part.source) })`, ditambah daftar catatan di bawah judul `Catatan` bila ada.

- [ ] **Step 1: Tulis tes yang gagal**

```ts
// tambahan src/atlas/manifest.test.ts
import { loadManifest } from './manifest';
test('rejects non-text Indonesian or Latin names', () =>
  expect(() => parseManifest({ ...ok, parts: [{ ...part, names: { en: 'Femur', id: 7 } }] })).toThrow(/^Manifest tidak valid:/));
test('accepts known notes and rejects unknown ones', () => {
  expect(parseManifest({ ...ok, parts: [{ ...part, notes: ['pose-disesuaikan'] }] }).parts[0].notes).toEqual(['pose-disesuaikan']);
  expect(() => parseManifest({ ...ok, parts: [{ ...part, notes: ['rahasia'] }] })).toThrow(/^Manifest tidak valid:/);
});
test('rejects a manifest for another body', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, json: async () => ok }));
  await expect(loadManifest('female', '/models')).rejects.toThrow(/^Manifest tidak valid:/);
  vi.unstubAllGlobals();
});
```

```tsx
// tambahan src/ui/InfoPanel.test.tsx
test('fitted parts say they come from the male model, with the source', () => {
  render(<InfoPanel part={{ ...part, origin: 'dipasang-dari-laki-laki' } as any} state={initialViewState()} dispatch={vi.fn()} />);
  expect(screen.getByText('Dipasang dari model laki-laki (BodyParts3D)')).toBeInTheDocument();
});
test('original female bones show their source and notes', () => {
  const bone = { ...part, origin: 'perempuan-asli', source: 'bonehub', notes: ['siku-tidak-lengkap'] };
  render(<InfoPanel part={bone as any} state={initialViewState()} dispatch={vi.fn()} />);
  expect(screen.getByText('Asli perempuan (BoneHub)')).toBeInTheDocument();
  expect(screen.getByText(/CT-nya terpotong/)).toBeInTheDocument();
});
```

```tsx
// src/ui/TopBar.test.tsx
import { fireEvent, render, screen } from '@testing-library/react';
import { initialViewState } from '../atlas/viewState';
import { STRINGS } from './strings';
import TopBar from './TopBar';
test('the female body can be chosen', () => {
  const dispatch = vi.fn();
  render(<TopBar state={initialViewState('male')} dispatch={dispatch} search={null} />);
  expect(screen.getByRole('group', { name: STRINGS.bodySwitch })).toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: 'Perempuan' }));
  expect(dispatch).toHaveBeenCalledWith({ type: 'setBody', body: 'female' });
});
```

- [ ] **Step 2: Jalankan, pastikan gagal**

Run: `npx vitest run src/atlas src/ui`
Expected: FAIL pada tes baru.

- [ ] **Step 3: Implementasi sesuai Interfaces**

- [ ] **Step 4: Jalankan semua tes dan typecheck**

Run: `npx vitest run && npm run typecheck`
Expected: semua lulus, tanpa error tipe.

- [ ] **Step 5: Commit**

```bash
git add src
git commit -m "feat(ui): badan Perempuan bisa dipilih; asal, sumber, dan catatan bagian di panel info"
```

---

### Task 13: Sorot bagian dipasang

**Files:**
- Modify: `src/atlas/viewState.ts`, `src/scene/SystemBatch.ts`, `src/scene/AtlasScene.ts`, `src/ui/ViewTools.tsx`, `src/ui/AtlasApp.tsx`, `src/ui/strings.ts`
- Create: `src/ui/ViewTools.test.tsx`
- Test: `src/atlas/viewState.test.ts`, `src/scene/SystemBatch.test.ts`, `src/ui/ViewTools.test.tsx`

**Interfaces:**
- Consumes: `PartRecord.origin` (manifest).
- Produces:
  - `ViewState.highlightFitted: boolean` (awal `false`); aksi `{ type: 'setHighlightFitted'; on: boolean }`.
  - `SystemBatch.setTint(ids: ReadonlySet<string> | null): void` dengan warna `#f0a04b`. Urutan warna per bagian: terpilih (`#6bd9c7`), lalu diwarnai, lalu warna sistem.
  - `AtlasScene.setManifest` mengumpulkan id bagian `dipasang-dari-laki-laki`; `applyBatch` memanggil `setTint(state.highlightFitted ? fittedIds : null)`.
  - `ViewTools` mendapat prop `hasFitted: boolean` dan kotak centang `STRINGS.highlightFitted` = `Sorot bagian dipasang`, nonaktif bila `hasFitted` salah. `title` = `STRINGS.highlightFittedHint` = `Warnai semua bagian yang dipasang dari model laki-laki`.

- [ ] **Step 1: Tulis tes yang gagal**

```ts
// tambahan src/atlas/viewState.test.ts
test('highlighting fitted parts is a view setting', () => {
  expect(initialViewState().highlightFitted).toBe(false);
  expect(viewReducer(initialViewState(), { type: 'setHighlightFitted', on: true }).highlightFitted).toBe(true);
});
```

```ts
// tambahan src/scene/SystemBatch.test.ts (pakai helper geometri yang sudah ada di file itu)
test('tint colours fitted parts and the selection still wins', () => {
  const batch = new SystemBatch('muscular', geometries(['a', 'b', 'c']), '#c0504d');
  batch.setTint(new Set(['a', 'b']));
  batch.setHighlight('b');
  expect(colorOf(batch, 'a')).toBe('f0a04b');
  expect(colorOf(batch, 'b')).toBe('6bd9c7');
  expect(colorOf(batch, 'c')).toBe('c0504d');
  batch.setTint(null);
  expect(colorOf(batch, 'a')).toBe('c0504d');
});
```

`colorOf(batch, id)` = `getHexString()` dari `batch.mesh.getColorAt(instanceId, new THREE.Color())`; tambahkan ke helper tes bila belum ada.

```tsx
// src/ui/ViewTools.test.tsx
import { fireEvent, render, screen } from '@testing-library/react';
import { initialViewState } from '../atlas/viewState';
import ViewTools from './ViewTools';
test('the fitted highlight toggle dispatches, and is disabled without fitted parts', () => {
  const dispatch = vi.fn();
  const { rerender } = render(<ViewTools state={initialViewState()} dispatch={dispatch} onPreset={vi.fn()} hasFitted />);
  fireEvent.click(screen.getByLabelText('Sorot bagian dipasang'));
  expect(dispatch).toHaveBeenCalledWith({ type: 'setHighlightFitted', on: true });
  rerender(<ViewTools state={initialViewState()} dispatch={dispatch} onPreset={vi.fn()} hasFitted={false} />);
  expect(screen.getByLabelText('Sorot bagian dipasang')).toBeDisabled();
});
```

- [ ] **Step 2: Jalankan, pastikan gagal**

Run: `npx vitest run src/atlas/viewState.test.ts src/scene/SystemBatch.test.ts src/ui/ViewTools.test.tsx`
Expected: FAIL.

- [ ] **Step 3: Implementasi sesuai Interfaces**

- [ ] **Step 4: Jalankan semua tes dan typecheck**

Run: `npx vitest run && npm run typecheck`
Expected: semua lulus.

- [ ] **Step 5: Commit**

```bash
git add src
git commit -m "feat(ui): sorot semua bagian yang dipasang dari model laki-laki"
```

---

### Task 14: Perbaikan kecil dari tahap 1

Temuan kecil review akhir tahap 1 no. 1, 2, 5, 6, dan 7. No. 3 dan 8 sudah masuk Task 12, no. 4 masuk Task 2 dan Task 11, dan no. 9 tetap ditunda (lihat akhir rencana).

**Files:**
- Create: `src/scene/loadingTracker.ts`
- Modify: `src/atlas/viewState.ts`, `src/scene/AtlasScene.ts`, `src/ui/useAtlas.ts`, `src/ui/InfoPanel.tsx`, `src/ui/SearchBox.tsx`
- Test: `src/scene/loadingTracker.test.ts`, `src/atlas/viewState.test.ts`, `src/atlas/search.test.ts`, `src/scene/AtlasScene.test.ts`

**Interfaces:**
- Produces:
  - `class LoadingTracker<K>`: `start(key: K)`, `progress(key: K, fraction: number)`, `finish(key: K)`, `current(): { key: K; fraction: number } | null` (sistem yang paling akhir dimulai dan belum selesai), `clear()`. `AtlasScene` memanggil `onLoading` dengan `current()` setiap kali ada perubahan, dan `clear()` saat `setManifest` (no. 7).
  - `ViewState.selectedSystem: SystemId | null`. Aksi `select` menjadi `{ type: 'select'; id: string | null; system?: SystemId }`, dan `isolatePart` menjadi `{ type: 'isolatePart'; id: string; system: SystemId }`. `toggleSystem`/`setGroup` yang mematikan sistem bagian terpilih juga mengosongkan pilihan; `isolatePart` menyalakan sistemnya (no. 2). `AtlasSceneEvents.onPick(pick: { id: string; system: SystemId } | null)`.
  - `AtlasScene.isSupported()` melepas konteks ujinya lewat `WEBGL_lose_context`. `dispose()` juga membuang geometri dan material alas, tekstur lingkungan, dan memanggil `renderer.forceContextLoss()` (no. 5).
  - Tween kamera dihentikan saat OrbitControls mengirim `start` (no. 6).

- [ ] **Step 1: Tulis tes yang gagal**

```ts
// src/scene/loadingTracker.test.ts
import { LoadingTracker } from './loadingTracker';
test('the newest unfinished load is shown until all are done', () => {
  const t = new LoadingTracker<string>();
  t.start('a'); t.start('b'); t.progress('a', 0.5);
  expect(t.current()).toEqual({ key: 'b', fraction: 0 });
  t.finish('b');
  expect(t.current()).toEqual({ key: 'a', fraction: 0.5 });
  t.finish('a');
  expect(t.current()).toBeNull();
});
```

```ts
// tambahan src/atlas/viewState.test.ts
test('turning off the layer of the selected part clears the selection', () => {
  let s = viewReducer(initialViewState(), { type: 'select', id: femur.id, system: 'skeletal' });
  s = viewReducer(s, { type: 'toggleSystem', system: 'skeletal' });
  expect([s.selectedId, s.selectedSystem]).toEqual([null, null]);
});
test('isolating a part whose layer is off turns the layer on', () => {
  const s = viewReducer(initialViewState(), { type: 'isolatePart', id: biceps.id, system: 'muscular' });
  expect(isPartVisible(s, biceps)).toBe(true);
});
```

Ubah pemanggilan `isolatePart` di tes lama supaya membawa `system`.

```ts
// tambahan src/atlas/search.test.ts
test('rank 1 (name starts with the query) beats rank 3 (query inside the name)', () => {
  const i = buildSearchIndex([p('x', 'Subclavian artery'), p('y', 'Clavicle'), p('z', 'Clavicle of left')]);
  expect(searchParts(i, 'clav')).toEqual(['y', 'z', 'x']);
});
```

```ts
// tambahan src/scene/AtlasScene.test.ts
test('isSupported releases its probe context', () => {
  const loseContext = vi.fn();
  const spy = vi.spyOn(HTMLCanvasElement.prototype, 'getContext').mockReturnValue({ getExtension: () => ({ loseContext }) } as any);
  expect(AtlasScene.isSupported()).toBe(true);
  expect(loseContext).toHaveBeenCalled();
  spy.mockRestore();
});
```

- [ ] **Step 2: Jalankan, pastikan gagal**

Run: `npx vitest run src/scene src/atlas`
Expected: FAIL pada tes baru.

- [ ] **Step 3: Implementasi `loadingTracker.ts`, perubahan reducer, dan perbaikan `AtlasScene`; sesuaikan `useAtlas`, `InfoPanel` (isolasi membawa sistem), dan `SearchBox`**

- [ ] **Step 4: Jalankan semua tes dan typecheck**

Run: `npx vitest run && npm run typecheck`
Expected: semua lulus.

- [ ] **Step 5: Commit**

```bash
git add src
git commit -m "fix: pilihan ikut lapisan, chip memuat yang benar, tween berhenti saat diseret, konteks WebGL dilepas"
```

---

### Task 15: Atribusi, README, dan pemeriksaan akhir

**Files:**
- Modify: `ATTRIBUTION.md`, `README.md`, bagian "Catatan keputusan" di rencana ini

**Interfaces:**
- Consumes: semua task sebelumnya.

- [ ] **Step 1: Tambahkan tiga sumber ke `ATTRIBUTION.md`**

Setiap sumber berisi kalimat atribusi, tautan lisensi CC BY 4.0, tautan unduhan, sitasi, dan daftar adaptasi:
- **HuBMAP Human Reference Atlas**, *3D Reference Organ Set for Female* v1.10. Adaptasi: plasenta dan strukturnya tidak dipakai; tulang yang dobel dengan BoneHub, ligamen dan tulang rawan lutut yang dobel dengan Andreassen, serta tambalan permukaan hati tidak dipakai; mesh disederhanakan, dikuantisasi, dan dikompres; bagian dikelompokkan ke sistem tampilan.
- **BoneHub**, *Visible Human Full-Skeleton 3D Bone Models* (Alavi dan Asseln, 2026, doi:10.57967/hf/10464). Adaptasi: mm Z-atas → m Y-atas; batang tubuh dipindah dengan satu transformasi kaku + skala ke kerangka HRA; tungkai dicocokkan per tulang; lengan, tangan, dan telapak kaki diputar di sendinya agar cocok dengan pose berdiri kulit HRA; bentuk tulang tidak diubah. Sebutkan juga keterbatasan sumber: siku tidak lengkap, falang digabung per jari, dan tidak ada tulang rawan iga maupun hioid.
- **Andreassen dkk. (2023)**, *Three Dimensional Lower Extremity Musculoskeletal Geometry of the Visible Human Female and Male*, Sci Data 10:34, doi:10.1038/s41597-022-01905-2, data doi:10.56902/COB.vh.2022.1. Adaptasi: 76 otot, ligamen lutut, dan tulang rawan sendi dipindah dengan thin-plate spline mengikuti tulang BoneHub; tulang dan lemaknya tidak dipakai.
- Tambahkan ke bagian BodyParts3D: bagian yang dipasang ke badan perempuan dipindah dengan thin-plate spline dari pasangan tulang dan kulit, lalu ditekan ke dalam kulit bila menembus; labelnya selalu "Dipasang dari model laki-laki".
- Tambahkan Wikidata UBERON (P1554) ke bagian Wikidata.

- [ ] **Step 2: Perbarui `README.md`**

Tambahkan cara membangun badan perempuan: unduh zip Andreassen lewat browser ke `data/raw/andreassen/` (dengan langkah dari pesan Task 1), lalu `npm run models:female`. Sebutkan ukuran unduhan otomatis (HRA 374,5 MB, BoneHub 289,5 MB) dan bahwa memori Node dinaikkan untuk langkah optimasi.

- [ ] **Step 3: Jalankan semua pemeriksaan**

Run: `npx vitest run && npm run typecheck && npm run build && npm run models:validate -- male && npm run models:validate -- female && cd pipeline && .venv/Scripts/python -m pytest -q && .venv/Scripts/python -m pytest -m realdata -q`
Expected: semua lulus, build berhasil, dan kedua validasi model exit 0.

- [ ] **Step 4: Pemeriksaan di browser (desktop)**

Jalankan `npm run dev`, buka `http://localhost:5173/?fps=1` di panel browser. Periksa:
- atlas terbuka dengan badan Perempuan;
- tombol Depan memperlihatkan wajah, dan klik tulang paha kiri memunculkan sisi "kiri" dengan pusat di +X (cek di konsol: `__atlasScene` dan bounds bagian `BH:FEMUR_LEFT`);
- mematikan Kulit dan Otot memperlihatkan organ dan kerangka utuh, termasuk rusuk, tulang rawan iga, lengan, dan tangan di dalam kulit;
- klik otot tungkai menunjukkan "Asli perempuan (Andreassen dkk. 2023)", dan klik otot lengan menunjukkan "Dipasang dari model laki-laki (BodyParts3D)";
- klik humerus menampilkan catatan siku dan pose;
- "Sorot bagian dipasang" mewarnai semua bagian dipasang, dan pilihan tetap berwarna teal;
- pindah ke Laki-laki lalu kembali ke Perempuan saat lapisan masih dimuat: chip "Memuat…" benar dan konsol tanpa error;
- dengan semua sistem menyala, fps ≥ 30.

- [ ] **Step 5: Pemeriksaan di layar HP**

Ubah ukuran panel browser ke 375×812. Panel info dengan catatan tetap terbaca, dan sakelar badan serta "Sorot bagian dipasang" masih bisa diketuk.

- [ ] **Step 6: Commit dan push branch**

```bash
git add ATTRIBUTION.md README.md docs/superpowers/plans/2026-11-03-tahap-2-perempuan.md
git commit -m "docs: atribusi HRA, BoneHub, dan Andreassen; cara membangun badan perempuan"
git push -u origin HEAD
```

Expected: branch fitur ada di GitHub. Merge ke `main` (yang langsung terbit ke GitHub Pages) menunggu persetujuan pemilik.

---

## Keputusan yang perlu dicek pemilik

1. **Pose badan perempuan = pose berdiri kulit HRA.** Tulang lengan, tangan, dan telapak kaki BoneHub diputar di sendinya agar masuk ke kulit itu. Bentuk tulangnya asli; posisinya ditandai "disesuaikan". Pilihan lain adalah memakai pose berbaring CT (siku menekuk, tangan di paha, kaki menjinjit). Pilihan itu ditolak karena kulit HRA, payudara, dan organnya berpose berdiri, dan kulit CT berlubang di siku.
2. **Zip Andreassen diunduh pemilik sekali lewat browser** (87,8 MB), karena situsnya menolak unduhan skrip.
3. **HRA v1.5 tidak dipakai:** tulang panggul BoneHub sudah mencakup ischium dan pubis.
4. **Plasenta, amnion, dan tali pusat tidak ikut** di paket (spec: disembunyikan secara bawaan).
5. **Kelenjar tiroid tidak ada di kedua badan,** karena tidak ada di HRA maupun BodyParts3D 4.0.
6. **Atlas terbuka dengan badan Perempuan** sebagai fokus utama.
7. **Ligamen dan tulang rawan lutut dari Andreassen** (satu CT dengan tulang BoneHub). Meniskus dan ligamen patela tetap dari HRA.
8. **Yang dipasang dari BodyParts3D:** otot di luar tungkai dan mata, saraf tepi, pembuluh di luar wilayah HRA (kepala, leher, lengan, tungkai, dinding tubuh), esofagus, lambung, bibir, kelenjar adrenal, hipofisis, hioid, sesamoid kaki, tulang rawan iga dan jaringan ikat lain, telinga, dan saluran air mata. Gigi, kulit, rambut, organ reproduksi laki-laki, jantung, paru dan saluran napas utama, dan mata tidak dipasang.
9. **Bagian dipasang yang menembus kulit ditekan 1 mm ke dalam kulit.** Bentuknya memang perkiraan; bagian asli perempuan tidak pernah ditekan.

## Temuan kecil yang ditunda

1. (dari tahap 1, no. 9) Belum ada error boundary bila `WebGLRenderer` gagal dibuat walau `isSupported()` benar, dan konteks WebGL yang hilang belum ditangani. Tidak terkait badan perempuan.
2. "Flexor retinaculum" BodyParts3D masuk sistem Indra karena aturan nama `retina`; seharusnya Sendi & jaringan ikat. Membetulkannya mengubah klasifikasi badan laki-laki, jadi ditunda ke tahap 6.

## Catatan keputusan (diisi saat eksekusi)

_Setiap keputusan saat eksekusi dicatat di sini: angka registrasi, pasangan permukaan bertumpuk yang diselesaikan, ruas yang ditekuk ulang, `ALLOWED_OUTSIDE`, penyesuaian galat penyederhanaan, dan ukuran akhir._

- **Task 4 — pasangan permukaan HRA.** Di data asli ada 858 bagian HRA yang dipakai dan 98 yang tidak. Pemeriksaan permukaan bertumpuk menemukan 99 pasangan. Hampir semuanya struktur nyata yang bersarang dalam satu sistem (lapisan mata, inti otak di dalam substansia alba, segmen hati di bawah kapsulnya, isi kelenjar getah bening). Karena warnanya sama, tidak ada yang berkedip, jadi pasangan dalam satu sistem diizinkan tanpa didaftar. Lima mesh "hilum atas/tengah/bawah" paru seluruhnya terletak di atas mesh hilum, jadi masuk `SURFACE_DUPLICATES`. Empat pasangan lintas sistem (vena/arteri retina sentral; diskus optikus dengan dura dan saraf optik) masuk `ALLOWED_OVERLAPS`. Dua cabang arteri koroner tanpa kata "artery" (`left_marginal_branch`, `posterior_left_ventricular_branch`) ditangkap aturan baru: nama dengan "branch" di sistem sirkulasi menjadi arteri, setelah aturan vena.
