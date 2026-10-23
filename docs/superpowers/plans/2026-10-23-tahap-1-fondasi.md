# Tahap 1 — Fondasi: Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Atlas 3D yang jalan lokal di browser dengan badan laki-laki BodyParts3D: lapisan bisa dinyalakan/dimatikan, bagian bisa diklik untuk info, bisa dicari, ada sakelar Istilah, tembus pandang, urai, dan preset kamera. Repo GitHub privat sudah dibuat.

**Architecture:** Pipeline Python mengubah OBJ BodyParts3D menjadi GLB mentah per sistem plus manifest. Skrip Node (gltf-transform + meshoptimizer) menyederhanakan dan mengompres GLB ke `public/models/male/`. Aplikasi Vite + React + TypeScript memuat manifest, memuat GLB per sistem saat lapisannya dinyalakan, lalu menggambar setiap sistem sebagai satu `BatchedMesh` three.js.

**Tech Stack:** Python 3.13 (numpy, trimesh, pytest); Node 24 (@gltf-transform/core, @gltf-transform/extensions, @gltf-transform/functions, meshoptimizer); Vite, React 19, TypeScript, three.js, three-mesh-bvh, marked; Vitest + Testing Library + jsdom.

**Spec:** [`docs/superpowers/specs/2026-10-23-atlas-anatomi-3d-design.md`](../specs/2026-10-23-atlas-anatomi-3d-design.md). Rencana ini mencakup tahap 1 dari bagian 11. Tahap 2–7 mendapat rencana sendiri setelah tahap sebelumnya selesai.

## Global Constraints

- Semua teks antarmuka berbahasa Indonesia dan dikumpulkan di `src/ui/strings.ts`.
- Satuan meter, sumbu Y ke atas, lantai di y = 0, tubuh menghadap +Z; sisi kiri tubuh berada di +X.
- Hanya data berlisensi CC BY 4.0 atau CC0. `ATTRIBUTION.md` ikut di repo dan bisa dibuka dari dalam atlas.
- Gambar otot 2D yang dibeli (`G:\My_AI_OS\3_Resources\Anatomi Otot`) tidak pernah di-commit.
- Setiap file yang di-commit di bawah 100 MB. `data/raw/` dan `data/work/` di-ignore; model olahan ada di `public/models/<body>/`.
- Lapisan awal (kulit, tulang, organ) paling besar 40 MB per badan; lapisan lain dimuat saat dibutuhkan.
- Minimal 30 fps di laptop pemilik (Intel Core Ultra 5 125H, Intel Arc terintegrasi, RAM 16 GB) dengan semua lapisan aktif.
- Browser sasaran: Chrome/Edge terbaru di desktop dan Android, WebGL2.
- Nama tidak pernah ditebak: urutan cadangannya ada di `src/atlas/names.ts` (Task 7).
- Nilai asal bagian: `perempuan-asli` dan `dipasang-dari-laki-laki` (dari spec), ditambah `laki-laki-asli` untuk badan laki-laki.
- Repo GitHub privat `opallama110-alt/atlas-anatomi-3d`. Situs statis, tanpa server dan login.

## Review Focus

1. **Tubuh tercermin atau menghadap ke belakang.** Bagian bernama "Left …" harus di +X, wajah di +Z, dan tombol "Depan" harus memperlihatkan wajah. Tes: Task 5 (`test_left_parts_are_positive_x_and_face_is_front`) dan Task 9 (`presetPose depan looks at the front`).
2. **Browser tanpa WebGL2.** Atlas harus menampilkan pesan bahasa Indonesia, bukan layar kosong. Tes: Task 11 (`shows a WebGL2 message when 3D is unsupported`).
3. **Satu file lapisan gagal dimuat** (404, Wi-Fi putus di HP). Muncul pesan dengan tombol "Coba lagi", dan lapisan lain tetap jalan. Tes: Task 11 (`shows a retry banner when a layer fails to load` di `LayerErrorBanner.test.tsx`); perilaku per sistem di `AtlasScene.ensureSystems` (Task 10) diperiksa di browser pada Task 12.
4. **Pencarian dengan huruf besar-kecil, spasi lebih, aksen, kata terpotong, atau tanpa hasil.** "jant" harus menemukan "Jantung", dan kata yang tidak ada memunculkan "Tidak ditemukan". Tes: Task 8 dan Task 11.
5. **Pilihan bagian setelah ganti badan atau lapisan dimatikan.** Ganti badan mengosongkan pilihan, dan memilih bagian tersembunyi lewat pencarian memunculkannya lagi. Tes: Task 8 (`setBody clears selection, hidden and isolation`, `revealPart turns the system on and unhides`).

---

### Task 1: Kerangka repo, app kosong, dan repo GitHub privat

**Files:**
- Create: `.gitignore`, `.gitattributes`, `LICENSE`, `README.md`, `package.json`, `tsconfig.json`, `vite.config.ts`, `index.html`, `src/main.tsx`, `src/App.tsx`, `src/styles.css`, `src/test/setup.ts`
- Test: `src/App.test.tsx`

**Interfaces:**
- Produces: npm scripts `dev` (`vite`), `dev:hp` (`vite --host`), `build` (`tsc --noEmit && vite build`), `test` (`vitest run`), `typecheck` (`tsc --noEmit`).

- [ ] **Step 1: Inisialisasi git dan file abaikan**

`git init -b main`. `.gitignore` berisi: `node_modules/`, `dist/`, `data/raw/`, `data/work/`, `pipeline/.venv/`, `__pycache__/`, `.pytest_cache/`, `.superpowers/`, `*.log`. `.gitattributes` berisi `* text=auto`, `*.glb binary`, `*.bin binary`. `LICENSE`: MIT, "Copyright (c) 2026 opallama110-alt", dengan catatan satu baris bahwa data anatomi berlisensi terpisah (lihat `ATTRIBUTION.md`).

- [ ] **Step 2: Pasang dependensi**

```bash
npm init -y
npm install react react-dom three three-mesh-bvh marked
npm install -D vite @vitejs/plugin-react typescript vitest jsdom @testing-library/react @testing-library/jest-dom @types/react @types/react-dom @types/three @types/node @gltf-transform/core @gltf-transform/extensions @gltf-transform/functions meshoptimizer
```

Set `"type": "module"`, `"private": true`, `"engines": { "node": ">=22" }`, dan script di atas.

- [ ] **Step 3: Tulis tes yang gagal**

```tsx
// src/App.test.tsx
import { render, screen } from '@testing-library/react';
import App from './App';

test('shows the atlas title', () => {
  render(<App />);
  expect(screen.getByRole('heading', { name: 'Atlas Anatomi 3D' })).toBeInTheDocument();
});
```

- [ ] **Step 4: Jalankan, pastikan gagal**

Run: `npx vitest run src/App.test.tsx`
Expected: FAIL, "Failed to resolve import "./App"".

- [ ] **Step 5: Buat app kosong**

`vite.config.ts`: plugin react; `test: { environment: 'jsdom', setupFiles: ['src/test/setup.ts'] }`. `src/test/setup.ts` meng-import `@testing-library/jest-dom/vitest`. `index.html`: `<html lang="id">`, `<title>Atlas Anatomi 3D</title>`. `App.tsx` menampilkan `<h1>Atlas Anatomi 3D</h1>`. `tsconfig.json`: `strict: true`, `jsx: react-jsx`, `moduleResolution: bundler`, `types: ["vitest/globals"]` dengan `test.globals: true`.

- [ ] **Step 6: Jalankan tes, typecheck, dan build**

Run: `npx vitest run && npm run typecheck && npm run build`
Expected: 1 test passed, tanpa error tipe, folder `dist/` terbentuk.

- [ ] **Step 7: Commit awal**

```bash
git add -A
git commit -m "chore: kerangka repo atlas anatomi 3D"
```

- [ ] **Step 8: Buat repo GitHub privat dan push**

```bash
gh repo create opallama110-alt/atlas-anatomi-3d --private --source=. --remote=origin --push --description "Atlas anatomi 3D berlapis untuk belajar, di browser"
```

Expected: URL repo tercetak; `git remote -v` menunjukkan `origin`.

- [ ] **Step 9: Buat branch kerja tahap 1**

Run: `git switch -c tahap-1-fondasi`. Semua task berikutnya di-commit ke branch ini.

---

### Task 2: Pembaca OBJ BodyParts3D dan ruang atlas

**Files:**
- Create: `pipeline/requirements.txt` (`numpy`, `trimesh`, `pytest`), `pipeline/pytest.ini` (`pythonpath = .`, `testpaths = tests`), `pipeline/atlas_pipeline/__init__.py`, `pipeline/atlas_pipeline/obj_mesh.py`
- Test: `pipeline/tests/test_obj_mesh.py`

**Interfaces:**
- Produces:
  - `ObjMesh` (frozen dataclass): `file_id: str`, `concept_id: str`, `name_en: str`, `positions_mm: np.ndarray` (N×3 float64, kerangka BodyParts3D: Z ke atas, depan = −Y), `faces: np.ndarray` (M×3 int64, berbasis 0, sudah jadi segitiga).
  - `parse_obj(text: str) -> ObjMesh`
  - `to_atlas_space(positions_mm: np.ndarray) -> np.ndarray`, yaitu `(x, z, −y) × 0.001` tanpa translasi.
  - `side_from_name(name_en: str) -> Literal["left", "right", "none"]`

- [ ] **Step 1: Siapkan venv**

Run: `cd pipeline && python -m venv .venv && .venv/Scripts/python -m pip install -r requirements.txt`
Expected: numpy, trimesh, dan pytest terpasang.

- [ ] **Step 2: Tulis tes yang gagal**

```python
# pipeline/tests/test_obj_mesh.py
import numpy as np
from atlas_pipeline.obj_mesh import parse_obj, side_from_name, to_atlas_space

SAMPLE = """#
# File ID : FJ9999
# Concept ID : FMA12345
# English name : Left test bone
v 0 0 0
v 10 0 0
v 10 10 0
v 0 10 0
vn 0 0 1
vn 0 0 1
vn 0 0 1
vn 0 0 1
f 1//1 2//2 3//3 4//4
"""

def test_parse_obj_reads_header_and_triangulates():
    mesh = parse_obj(SAMPLE)
    assert (mesh.file_id, mesh.concept_id, mesh.name_en) == ("FJ9999", "FMA12345", "Left test bone")
    assert mesh.positions_mm.shape == (4, 3)
    assert mesh.faces.tolist() == [[0, 1, 2], [0, 2, 3]]

def test_to_atlas_space_maps_axes_to_meters_y_up():
    out = to_atlas_space(np.array([[10.0, -100.0, 1500.0]]))
    assert np.allclose(out, [[0.010, 1.5, 0.1]])

def test_side_from_name():
    assert side_from_name("Left femur") == "left"
    assert side_from_name("Right coronary artery") == "right"
    assert side_from_name("Branch of left middle cerebral artery") == "left"
    assert side_from_name("Sternum") == "none"
    assert side_from_name("Leftover tissue") == "none"
```

- [ ] **Step 3: Jalankan, pastikan gagal**

Run: `cd pipeline && .venv/Scripts/python -m pytest tests/test_obj_mesh.py -q`
Expected: FAIL, `ModuleNotFoundError: No module named 'atlas_pipeline.obj_mesh'`.

- [ ] **Step 4: Implementasi `obj_mesh.py`**

Baca header `# File ID :`, `# Concept ID :`, `# English name :`. Baca baris `v` dan `f`; ambil indeks sebelum `/`; pecah poligon dengan kipas `(0, j, j+1)`. Abaikan `vn`, karena normal dihitung ulang saat ekspor. Sisi ditentukan dengan regex `\bleft\b` / `\bright\b` tanpa membedakan huruf besar-kecil.

- [ ] **Step 5: Jalankan, pastikan lulus**

Run: `cd pipeline && .venv/Scripts/python -m pytest tests/test_obj_mesh.py -q`
Expected: 3 passed.

- [ ] **Step 6: Commit**

```bash
git add pipeline
git commit -m "feat(pipeline): baca OBJ BodyParts3D ke ruang atlas"
```

---

### Task 3: Tabel BodyParts3D dan klasifikasi sistem

**Files:**
- Create: `pipeline/atlas_pipeline/bp3d_tables.py`, `pipeline/atlas_pipeline/systems.py`, `pipeline/tests/fixtures/bp3d/isa_element_parts.txt`, `pipeline/tests/fixtures/bp3d/partof_element_parts.txt`
- Test: `pipeline/tests/test_bp3d_tables.py`, `pipeline/tests/test_systems.py`

**Interfaces:**
- Consumes: tidak ada.
- Produces:
  - `SystemId`: Literal untuk `integumentary, muscular, skeletal, connective, digestive, respiratory, urinary, reproductive, endocrine, lymphatic, cardiac, arterial, venous, nervous, sensory`.
  - `ElementConcepts` (frozen dataclass): `isa: frozenset[str]`, `partof: frozenset[str]`. Isinya semua konsep yang daftar elemennya memuat file itu, jadi sudah termasuk seluruh leluhurnya.
  - `load_element_concepts(raw_dir: Path) -> dict[str, ElementConcepts]`, kuncinya file id `FJ…`. Membaca `isa_element_parts.txt` dan `partof_element_parts.txt` (TSV dengan header `concept id`, `name`, `element file id`).
  - `classify(concepts: ElementConcepts, name_en: str) -> tuple[SystemId, str]`, mengembalikan `(sistem, id aturan)`.
  - `RULES`: tuple aturan berurutan; aturan pertama yang cocok menang.

Tabel aturan (urutan ini wajib):

| # | id aturan | cocok jika | sistem |
|---|---|---|---|
| 1 | `isa-artery` | IS-A memuat FMA50720 | arterial |
| 2 | `isa-vein` | IS-A memuat FMA50723 | venous |
| 3 | `partof-heart` | PART-OF memuat FMA7088 | cardiac |
| 4 | `nervous` | IS-A memuat FMA65132, FMA61284, FMA5865, atau FMA55676; atau PART-OF memuat FMA7157 | nervous |
| 5 | `isa-bone` | IS-A memuat FMA5018 atau FMA12516 | skeletal |
| 6 | `isa-muscle` | IS-A memuat FMA5022 atau FMA32558 | muscular |
| 7 | `partof-respiratory` | PART-OF memuat FMA7158 | respiratory |
| 8 | `partof-alimentary` | PART-OF memuat FMA7152 | digestive |
| 9 | `partof-urinary` | PART-OF memuat FMA7159 | urinary |
| 10 | `partof-genital` | PART-OF memuat FMA7160 | reproductive |
| 11 | `partof-endocrine` | PART-OF memuat FMA9668 | endocrine |
| 12 | `lymphatic` | PART-OF memuat FMA9607, atau nama cocok `spleen\|lymph\|tonsil\|thymus` | lymphatic |
| 13 | `sensory` | PART-OF memuat FMA54450 atau FMA54449, atau nama cocok `eyeball\|lens\|cornea\|retina\|cochlea\|vestibul\|tympan` | sensory |
| 14 | `integument` | PART-OF memuat FMA74657 atau FMA72979, atau IS-A memuat FMA7163 | integumentary |
| 15 | `connective` | IS-A memuat FMA55107, FMA10446, atau FMA9721 | connective |
| 16 | `name-urinary` | nama cocok `kidney\|ureter\|bladder\|urethra` | urinary |
| 17 | `name-genital` | nama cocok `testis\|prostat\|penis\|epididym\|seminal\|deferens\|scrot` | reproductive |
| 18 | `name-endocrine` | nama cocok `adrenal\|suprarenal gland\|thyroid gland\|parathyroid\|pituitary\|hypophysis\|pineal` | endocrine |
| 19 | `name-digestive` | nama cocok `stomach\|esophag\|liver\|pancrea\|gallbladder\|intestin\|colon\|rectum\|duoden\|jejun\|ileum\|cecum\|appendix\|tongue\|salivary\|parotid\|submandibular gland\|sublingual gland` | digestive |
| 20 | `name-respiratory` | nama cocok `trachea\|bronch\|lung\|laryn\|nasal\|pharyn` | respiratory |
| 21 | `default` | selalu | connective |

- [ ] **Step 1: Tulis fixture dan tes yang gagal**

Fixture `isa_element_parts.txt`: baris header, lalu `FMA5018 bone organ FJ1`, `FMA50720 artery FJ2`, `FMA62955 anatomical entity FJ1`, `FMA62955 anatomical entity FJ2` (dipisah tab). Fixture `partof_element_parts.txt`: header, lalu `FMA7088 heart FJ2`.

```python
# pipeline/tests/test_bp3d_tables.py
from pathlib import Path
from atlas_pipeline.bp3d_tables import load_element_concepts

def test_load_element_concepts_inverts_both_tables():
    concepts = load_element_concepts(Path(__file__).parent / "fixtures" / "bp3d")
    assert concepts["FJ1"].isa == frozenset({"FMA5018", "FMA62955"})
    assert concepts["FJ1"].partof == frozenset()
    assert concepts["FJ2"].partof == frozenset({"FMA7088"})
```

```python
# pipeline/tests/test_systems.py
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
```

- [ ] **Step 2: Jalankan, pastikan gagal**

Run: `cd pipeline && .venv/Scripts/python -m pytest tests/test_bp3d_tables.py tests/test_systems.py -q`
Expected: FAIL, modul belum ada.

- [ ] **Step 3: Implementasi `bp3d_tables.py` dan `systems.py`**

`load_element_concepts` membaca kedua TSV dengan `csv` (delimiter tab, encoding utf-8) dan membalik pemetaan konsep → elemen. `classify` berjalan di atas `RULES` sesuai tabel; regex nama tidak peka huruf besar-kecil.

- [ ] **Step 4: Jalankan, pastikan lulus**

Run: `cd pipeline && .venv/Scripts/python -m pytest tests/test_bp3d_tables.py tests/test_systems.py -q`
Expected: 10 passed.

- [ ] **Step 5: Commit**

```bash
git add pipeline
git commit -m "feat(pipeline): klasifikasi sistem BodyParts3D dari tabel IS-A dan PART-OF"
```

---

### Task 4: Label Wikidata (Indonesia dan Latin)

**Files:**
- Create: `pipeline/atlas_pipeline/wikidata.py`, `pipeline/cache/wikidata-fma-labels.json` (dibuat saat dijalankan, di-commit; CC0)
- Test: `pipeline/tests/test_wikidata.py`

**Interfaces:**
- Produces:
  - `SPARQL: str`, query yang mengambil `?item ?fma ?idLabel ?laLabel` untuk semua item dengan P1402, dengan label `id` dan `la` sebagai OPTIONAL.
  - `parse_sparql_json(payload: dict) -> dict[str, dict[str, str]]`, misalnya `"FMA7088" -> {"id": "jantung", "la": "cor"}`.
  - `load_fma_labels(cache: Path, refresh: bool = False) -> dict[str, dict[str, str]]`

Aturan:
- Kunci dinormalkan menjadi `"FMA" + angka`.
- Kalau satu FMA dimiliki beberapa item, pakai item dengan nomor Q terkecil.
- Label di-trim, dan label kosong dihilangkan. FMA yang tidak punya label `id` maupun `la` tidak disimpan.
- Permintaan jaringan memakai header `User-Agent: atlas-anatomi-3d/0.1 (https://github.com/opallama110-alt/atlas-anatomi-3d)`.

- [ ] **Step 1: Tulis tes yang gagal**

```python
# pipeline/tests/test_wikidata.py
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
```

- [ ] **Step 2: Jalankan, pastikan gagal**

Run: `cd pipeline && .venv/Scripts/python -m pytest tests/test_wikidata.py -q`
Expected: FAIL, modul belum ada.

- [ ] **Step 3: Implementasi `wikidata.py`**

Permintaan memakai `urllib.request` ke `https://query.wikidata.org/sparql` dengan `Accept: application/sparql-results+json`. Hasilnya ditulis ke cache (JSON berurutan kunci, UTF-8).

- [ ] **Step 4: Jalankan, pastikan lulus**

Run: `cd pipeline && .venv/Scripts/python -m pytest tests/test_wikidata.py -q`
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add pipeline
git commit -m "feat(pipeline): ambil label Indonesia dan Latin dari Wikidata lewat ID FMA"
```

---

### Task 5: Paket mentah badan laki-laki (GLB per sistem + manifest draf)

**Files:**
- Create: `pipeline/atlas_pipeline/fetch.py`, `pipeline/atlas_pipeline/package_body.py`, `pipeline/atlas_pipeline/__main__.py`, `pipeline/tests/fixtures/bp3d/objs/FJ1.obj`, `FJ2.obj`, `FJ3.obj`
- Test: `pipeline/tests/test_package_body.py`

**Interfaces:**
- Consumes: `parse_obj`, `to_atlas_space`, `side_from_name` (Task 2); `load_element_concepts`, `classify` (Task 3); `load_fma_labels` (Task 4).
- Produces:
  - `fetch_bodyparts3d(raw_dir: Path) -> None`. Mengunduh 7 file dari `https://dbarchive.biosciencedbc.jp/data/bodyparts3d/LATEST/` (`isa_BP3D_4.0_obj_99.zip` dan 6 tabel `isa_*`/`partof_*`). Unduhan bisa dilanjutkan, dan file yang ukurannya sudah sesuai `Content-Length` dilewati.
  - `build_male(raw_dir: Path, work_dir: Path, labels: dict[str, dict[str, str]]) -> dict`. Membaca OBJ dari zip (`zipfile`, tanpa ekstrak) atau dari folder `raw_dir/objs/` bila ada (dipakai fixture). Menulis `work_dir/male/<system>.glb`, `work_dir/male/manifest.draft.json`, dan `work_dir/male/classification-report.json`.
  - CLI: `python -m atlas_pipeline male` menjalankan fetch → label → `build_male` dengan `raw_dir = ../data/raw/bodyparts3d` dan `work_dir = ../data/work`.
- Bentuk part di manifest (kunci camelCase, sama dengan `PartRecord` di Task 7): `id` (`"BP3D:" + file id`), `system`, `side`, `origin` (`"laki-laki-asli"`), `source` (`"bodyparts3d"`), `sourceRef` (file id), `fma` (concept id), `names` (`{"en", "id"?, "la"?}`; `en` diawali huruf kapital), `bounds` (`[[minx,miny,minz],[maxx,maxy,maxz]]` setelah translasi), `file` (`"<system>.glb"`), `triangles`.
- Laporan klasifikasi: `{"bySystem": {system: jumlah}, "byRule": {rule: jumlah}, "default": [nama…]}`.

Translasi seluruh badan: setelah semua bagian diubah ke ruang atlas, kurangi `minY` global dan pusat kotak X/Z global, supaya lantai di y = 0 dan badan di tengah.

- [ ] **Step 1: Tulis fixture dan tes yang gagal**

Ada empat OBJ kecil di `fixtures/bp3d/objs/`, masing-masing satu segitiga (format header sama dengan Task 2):

| File | Nama | Verteks (mm) | Masuk sistem lewat |
|---|---|---|---|
| FJ1 | Left test femur | x 100..120, y 0, z 0..900 | IS-A FMA5018 → skeletal |
| FJ2 | Right test artery | x −120..−100, y 0, z 0..900 | IS-A FMA50720 → arterial |
| FJ3 | Test kidney | x −20..20, y 0, z 900..1000 | aturan nama → urinary |
| FJ4 | Test nose | x −5..5, y −150 (depan), z 1600 | `default` → connective |

Tabel fixture dari Task 3 sudah memasukkan FJ1 di bawah FMA5018 dan FJ2 di bawah FMA50720. FJ3 dan FJ4 sengaja tidak punya baris.

```python
# pipeline/tests/test_package_body.py
import json
from pathlib import Path
import numpy as np
import trimesh
from atlas_pipeline.package_body import build_male

FIX = Path(__file__).parent / "fixtures" / "bp3d"
LABELS = {"FMA5018": {"id": "tulang paha", "la": "femur"}}

def build(tmp_path):
    return build_male(FIX, tmp_path, LABELS)

def test_writes_one_glb_per_system_and_manifest(tmp_path):
    manifest = build(tmp_path)
    files = sorted(p.name for p in (tmp_path / "male").glob("*.glb"))
    assert files == ["arterial.glb", "connective.glb", "skeletal.glb", "urinary.glb"]
    assert len(manifest["parts"]) == 4
    assert json.loads((tmp_path / "male" / "manifest.draft.json").read_text("utf-8")) == manifest

def test_floor_is_zero_and_body_centered(tmp_path):
    parts = build(tmp_path)["parts"]
    lo = np.min([p["bounds"][0] for p in parts], axis=0)
    hi = np.max([p["bounds"][1] for p in parts], axis=0)
    assert abs(lo[1]) < 1e-9
    assert abs((lo[0] + hi[0]) / 2) < 1e-9 and abs((lo[2] + hi[2]) / 2) < 1e-9

def test_left_parts_are_positive_x_and_face_is_front(tmp_path):
    parts = {p["names"]["en"]: p for p in build(tmp_path)["parts"]}
    center_x = lambda p: (p["bounds"][0][0] + p["bounds"][1][0]) / 2
    assert center_x(parts["Left test femur"]) > 0 > center_x(parts["Right test artery"])
    nose_z = parts["Test nose"]["bounds"][1][2]
    assert nose_z == max(p["bounds"][1][2] for p in parts.values())

def test_glb_nodes_are_part_ids(tmp_path):
    build(tmp_path)
    scene = trimesh.load(tmp_path / "male" / "skeletal.glb", force="scene")
    assert set(scene.graph.nodes_geometry) == {"BP3D:FJ1"}

def test_names_side_origin_and_report(tmp_path):
    manifest = build(tmp_path)
    femur = next(p for p in manifest["parts"] if p["id"] == "BP3D:FJ1")
    assert femur["names"] == {"en": "Left test femur", "id": "tulang paha", "la": "femur"}
    assert (femur["side"], femur["origin"], femur["source"]) == ("left", "laki-laki-asli", "bodyparts3d")
    report = json.loads((tmp_path / "male" / "classification-report.json").read_text("utf-8"))
    assert report["default"] == ["Test nose"]
```

- [ ] **Step 2: Jalankan, pastikan gagal**

Run: `cd pipeline && .venv/Scripts/python -m pytest tests/test_package_body.py -q`
Expected: FAIL, modul belum ada.

- [ ] **Step 3: Implementasi `fetch.py`, `package_body.py`, `__main__.py`**

Setiap sistem dibuat sebagai `trimesh.Scene`. Tiap bagian ditambahkan dengan `scene.add_geometry(Trimesh(vertices, faces, process=False), node_name=part_id, geom_name=part_id)`, lalu diekspor dengan `scene.export(file_type="glb", include_normals=True)`. Bagian dengan 0 segitiga ditolak (raise).

- [ ] **Step 4: Jalankan tes, pastikan lulus**

Run: `cd pipeline && .venv/Scripts/python -m pytest -q`
Expected: semua tes pipeline lulus (20 passed).

- [ ] **Step 5: Jalankan dengan data asli**

Run: `cd pipeline && .venv/Scripts/python -m atlas_pipeline male`
Expected: 2234 bagian, 15 file GLB di `data/work/male/`, dan `classification-report.json` dengan `"default": []`. Kalau `default` belum kosong, tambahkan pola nama ke aturan 16–20 (atau aturan baru sebelum `default`) beserta kasus tesnya di `test_systems.py`, lalu ulangi sampai kosong.

Periksa juga contoh ini di laporan: "Wall of left atrium" → cardiac, "Left lateral ventricle" → nervous, "Left femoral artery" → arterial, "Diaphragm" → muscular, "Thyroid cartilage" → respiratory.

- [ ] **Step 6: Commit**

```bash
git add pipeline
git commit -m "feat(pipeline): paket GLB mentah badan laki-laki per sistem"
```

---

### Task 6: Optimasi GLB dan validasi model

**Files:**
- Create: `scripts/lib/models.mjs`, `scripts/optimize-glb.mjs`, `scripts/validate-models.mjs`
- Modify: `package.json` (script `models:male`, `models:validate`)
- Test: `scripts/lib/models.test.mjs`

**Interfaces:**
- Consumes: `data/work/<body>/<system>.glb` dan `manifest.draft.json` (Task 5).
- Produces:
  - `INITIAL_SYSTEMS = ['integumentary','skeletal','cardiac','digestive','respiratory','urinary','reproductive','endocrine','lymphatic']`
  - `INITIAL_BUDGET_BYTES = 40 * 1024 * 1024`
  - `budgetReport(manifest) -> { initialBytes: number, totalBytes: number, overBudget: boolean, bySystem: Record<string, number> }`
  - `findManifestProblems(manifest, nodeNamesBySystem: Record<string, string[]>) -> string[]`. Mendeteksi id ganda, part tanpa node, node tanpa part, part dengan `triangles === 0`, dan `file` yang tidak cocok dengan sistemnya.
  - `public/models/<body>/<system>.glb` dan `public/models/<body>/manifest.json` dengan bentuk `BodyManifest` (Task 7): `version: 1`, `body`, `units: 'm'`, `up: 'y'`, `parts`, `systems: [{ id, file, bytes, parts, triangles }]`.
  - Script npm: `models:male` = `cd pipeline && .venv\\Scripts\\python -m atlas_pipeline male && cd .. && node scripts/optimize-glb.mjs male && node scripts/validate-models.mjs male`; `models:validate` = `node scripts/validate-models.mjs`.

Optimasi tiap GLB: `weld()`, lalu `simplify({ simplifier: MeshoptSimplifier, ratio: 0, error: 0.002 })`, lalu `quantize()`, lalu `meshopt({ encoder: MeshoptEncoder, level: 'medium' })`. Batas galat 0,2% sama dengan Human-Atlas. Jumlah segitiga di manifest diperbarui dari hasil optimasi.

- [ ] **Step 1: Tulis tes yang gagal**

```js
// scripts/lib/models.test.mjs
import { budgetReport, findManifestProblems, INITIAL_BUDGET_BYTES } from './models.mjs';

const manifest = {
  parts: [
    { id: 'BP3D:FJ1', system: 'skeletal', file: 'skeletal.glb', triangles: 10 },
    { id: 'BP3D:FJ2', system: 'muscular', file: 'muscular.glb', triangles: 0 },
  ],
  systems: [
    { id: 'skeletal', file: 'skeletal.glb', bytes: 30 * 1024 * 1024 },
    { id: 'muscular', file: 'muscular.glb', bytes: 20 * 1024 * 1024 },
  ],
};

test('budget counts only initial systems', () => {
  const r = budgetReport(manifest);
  expect(r.initialBytes).toBe(30 * 1024 * 1024);
  expect(r.totalBytes).toBe(50 * 1024 * 1024);
  expect(r.overBudget).toBe(30 * 1024 * 1024 > INITIAL_BUDGET_BYTES);
});

test('finds missing nodes, extra nodes and empty parts', () => {
  const problems = findManifestProblems(manifest, { skeletal: ['BP3D:FJ1', 'BP3D:FJ9'], muscular: [] });
  expect(problems).toEqual(expect.arrayContaining([
    expect.stringContaining('BP3D:FJ2'),
    expect.stringContaining('BP3D:FJ9'),
  ]));
});
```

Tambahkan `scripts/**/*.test.mjs` ke `include` Vitest.

- [ ] **Step 2: Jalankan, pastikan gagal**

Run: `npx vitest run scripts/lib/models.test.mjs`
Expected: FAIL, modul belum ada.

- [ ] **Step 3: Implementasi `models.mjs`, `optimize-glb.mjs`, `validate-models.mjs`**

`validate-models.mjs <body>` membaca nama node dengan `NodeIO` (ekstensi meshopt terdaftar), mencetak ukuran per sistem dan total lapisan awal, lalu keluar dengan kode 1 kalau ada masalah atau `overBudget`.

- [ ] **Step 4: Jalankan tes, pastikan lulus**

Run: `npx vitest run scripts/lib/models.test.mjs`
Expected: 2 passed.

- [ ] **Step 5: Bangun model asli**

Run: `npm run models:male`
Expected: 15 GLB di `public/models/male/`, ukuran per sistem tercetak, "lapisan awal" ≤ 40 MB, exit code 0.

- [ ] **Step 6: Commit (termasuk model olahan)**

```bash
git add scripts package.json public/models/male pipeline/cache
git commit -m "feat(models): optimasi dan validasi GLB badan laki-laki"
```

---

### Task 7: Tipe atlas, sistem dan lapisan, nama, manifest

**Files:**
- Create: `src/atlas/types.ts`, `src/atlas/systems.ts`, `src/atlas/names.ts`, `src/atlas/manifest.ts`
- Test: `src/atlas/names.test.ts`, `src/atlas/systems.test.ts`, `src/atlas/manifest.test.ts`

**Interfaces:**
- Produces (TypeScript):
  - `type BodyId = 'female' | 'male'`
  - `type SystemId` (15 nilai sama dengan Task 3)
  - `type Origin = 'perempuan-asli' | 'dipasang-dari-laki-laki' | 'laki-laki-asli'`
  - `type Side = 'left' | 'right' | 'none'`
  - `type Istilah = 'ringan' | 'kesehatan'`
  - `interface PartNames { en: string; id?: string; la?: string; ringan?: string; kesehatan?: string }`. `ringan` dan `kesehatan` disiapkan untuk daftar kurasi di tahap 6.
  - `interface PartRecord { id; system; side; origin; source; sourceRef; fma?; names: PartNames; bounds: [[number,number,number],[number,number,number]]; file; triangles }`
  - `interface SystemFile { id: SystemId; file: string; bytes: number; parts: number; triangles: number }`
  - `interface BodyManifest { version: 1; body: BodyId; units: 'm'; up: 'y'; parts: PartRecord[]; systems: SystemFile[] }`
  - `type LayerGroupId = 'kulit' | 'otot' | 'tulang' | 'sendi' | 'organ' | 'jantung-pembuluh' | 'saraf' | 'indra'`
  - `SYSTEMS: readonly { id: SystemId; label: string; color: string; initial: boolean }[]`
  - `LAYER_GROUPS: readonly { id: LayerGroupId; label: string; systems: readonly SystemId[] }[]`
  - `systemInfo(id: SystemId)`
  - `displayName(names: PartNames, istilah: Istilah): string`
  - `secondaryName(names: PartNames, istilah: Istilah): string | undefined`
  - `sideLabel(side: Side): string`, yaitu `'kiri' | 'kanan' | ''`
  - `parseManifest(json: unknown): BodyManifest`. Kalau tidak valid, melempar `Error` dengan pesan berawalan `Manifest tidak valid:`.
  - `loadManifest(body: BodyId, baseUrl = '/models'): Promise<BodyManifest>`

Nilai yang ditetapkan:

| Sistem | Label | Warna | Grup | Awal |
|---|---|---|---|---|
| integumentary | Kulit | `#e8c4a8` | kulit | ya |
| muscular | Otot | `#c0504d` | otot | tidak |
| skeletal | Tulang | `#ece6d6` | tulang | ya |
| connective | Sendi & jaringan ikat | `#b9c7c4` | sendi | tidak |
| digestive | Pencernaan | `#e0a370` | organ | ya |
| respiratory | Pernapasan | `#e889a0` | organ | ya |
| urinary | Kemih | `#e3c96a` | organ | ya |
| reproductive | Reproduksi | `#d98cb3` | organ | ya |
| endocrine | Endokrin | `#b48cd9` | organ | ya |
| lymphatic | Limfatik | `#8fbf6a` | organ | ya |
| cardiac | Jantung | `#c8323c` | jantung-pembuluh | ya |
| arterial | Arteri | `#d23a3a` | jantung-pembuluh | tidak |
| venous | Vena | `#3a5fd2` | jantung-pembuluh | tidak |
| nervous | Saraf & otak | `#f2d16b` | saraf | tidak |
| sensory | Indra | `#7fc8d9` | indra | tidak |

Label grup: Kulit, Otot, Tulang, Sendi, Organ, Jantung & pembuluh, Saraf, Indra.

Urutan cadangan nama:
- Gaya Ringan: `ringan → id → kesehatan → la → en`.
- Gaya Kesehatan: `kesehatan → la → ringan → id → en`.
- `secondaryName` mengembalikan nama terbaik dari gaya lain kalau berbeda dari nama utama. Kalau sama, ia mengembalikan `en` kalau berbeda; kalau tidak ada yang berbeda, `undefined`.

- [ ] **Step 1: Tulis tes yang gagal**

```ts
// src/atlas/names.test.ts
import { displayName, secondaryName, sideLabel } from './names';

const full = { en: 'Femur', id: 'tulang paha', la: 'femur' };

test('ringan prefers Indonesian, kesehatan prefers Latin', () => {
  expect(displayName(full, 'ringan')).toBe('tulang paha');
  expect(displayName(full, 'kesehatan')).toBe('femur');
});
test('falls back to English when nothing else exists', () => {
  expect(displayName({ en: 'Wall of ventricle' }, 'ringan')).toBe('Wall of ventricle');
  expect(secondaryName({ en: 'Wall of ventricle' }, 'ringan')).toBeUndefined();
});
test('secondary shows the other style without duplicates', () => {
  expect(secondaryName(full, 'ringan')).toBe('femur');
  expect(secondaryName({ en: 'Heart', la: 'cor' }, 'kesehatan')).toBe('Heart');
});
test('curated names win over Wikidata labels', () => {
  expect(displayName({ ...full, ringan: 'tulang paha (femur)' }, 'ringan')).toBe('tulang paha (femur)');
});
test('side labels are Indonesian', () => {
  expect([sideLabel('left'), sideLabel('right'), sideLabel('none')]).toEqual(['kiri', 'kanan', '']);
});
```

```ts
// src/atlas/systems.test.ts
import { LAYER_GROUPS, SYSTEMS } from './systems';

test('every system belongs to exactly one layer group', () => {
  for (const s of SYSTEMS) expect(LAYER_GROUPS.filter(g => g.systems.includes(s.id))).toHaveLength(1);
});
test('initial systems are skin, bones, heart and organs', () => {
  expect(SYSTEMS.filter(s => s.initial).map(s => s.id).sort()).toEqual(
    ['cardiac', 'digestive', 'endocrine', 'integumentary', 'lymphatic', 'reproductive', 'respiratory', 'skeletal', 'urinary']);
});
```

```ts
// src/atlas/manifest.test.ts
import { parseManifest } from './manifest';

const part = { id: 'BP3D:FJ1', system: 'skeletal', side: 'left', origin: 'laki-laki-asli', source: 'bodyparts3d',
  sourceRef: 'FJ1', fma: 'FMA1', names: { en: 'Femur' }, bounds: [[0, 0, 0], [1, 1, 1]], file: 'skeletal.glb', triangles: 4 };
const ok = { version: 1, body: 'male', units: 'm', up: 'y', parts: [part],
  systems: [{ id: 'skeletal', file: 'skeletal.glb', bytes: 10, parts: 1, triangles: 4 }] };

test('accepts a valid manifest', () => expect(parseManifest(ok).parts[0].id).toBe('BP3D:FJ1'));
test('rejects an unknown system', () =>
  expect(() => parseManifest({ ...ok, parts: [{ ...part, system: 'magic' }] })).toThrow(/^Manifest tidak valid:/));
test('rejects malformed bounds', () =>
  expect(() => parseManifest({ ...ok, parts: [{ ...part, bounds: [[0, 0], [1, 1]] }] })).toThrow(/^Manifest tidak valid:/));
```

- [ ] **Step 2: Jalankan, pastikan gagal**

Run: `npx vitest run src/atlas`
Expected: FAIL, modul belum ada.

- [ ] **Step 3: Implementasi keempat file sesuai Interfaces dan tabel di atas**

- [ ] **Step 4: Jalankan, pastikan lulus**

Run: `npx vitest run src/atlas && npm run typecheck`
Expected: 10 passed, tanpa error tipe.

- [ ] **Step 5: Commit**

```bash
git add src/atlas
git commit -m "feat(atlas): tipe, sistem, lapisan, nama dua gaya, dan manifest"
```

---

### Task 8: State tampilan dan pencarian

**Files:**
- Create: `src/atlas/viewState.ts`, `src/atlas/search.ts`
- Test: `src/atlas/viewState.test.ts`, `src/atlas/search.test.ts`

**Interfaces:**
- Consumes: tipe dari Task 7; `LAYER_GROUPS`, `SYSTEMS`; `displayName`.
- Produces:
  - `interface ViewState { body: BodyId; istilah: Istilah; systems: Record<SystemId, boolean>; xray: boolean; explode: number; selectedId: string | null; hiddenIds: string[]; isolatedIds: string[] | null }`
  - `type ViewAction`:
    - `{ type: 'setBody'; body }`
    - `{ type: 'setIstilah'; istilah }`
    - `{ type: 'toggleSystem'; system }`
    - `{ type: 'setGroup'; group: LayerGroupId; on: boolean }`
    - `{ type: 'setXray'; on: boolean }`
    - `{ type: 'setExplode'; amount: number }`
    - `{ type: 'select'; id: string | null }`
    - `{ type: 'hidePart'; id }`
    - `{ type: 'isolatePart'; id }`
    - `{ type: 'showAll' }`
    - `{ type: 'revealPart'; id; system }`
  - `initialViewState(body: BodyId = 'male'): ViewState`. Sistem awal menyala sesuai `SYSTEMS.initial`; `xray: true`; `istilah: 'ringan'`; `explode: 0`.
  - `viewReducer(state, action): ViewState`
  - `isPartVisible(state, part: { id: string; system: SystemId }): boolean`
  - `normalizeQuery(s: string): string`. Huruf kecil, aksen dibuang (NFD), spasi dirapikan.
  - `buildSearchIndex(parts: PartRecord[]): SearchIndex`. Kuncinya semua nama yang ada (`en`, `id`, `la`, `ringan`, `kesehatan`).
  - `searchParts(index: SearchIndex, query: string, limit = 20): string[]`, mengembalikan id part.

Aturan reducer:
- `setBody` mengosongkan `selectedId`, `hiddenIds`, dan `isolatedIds`.
- `setExplode` dibatasi ke rentang 0..1.
- `hidePart` juga mengosongkan pilihan kalau yang disembunyikan adalah bagian terpilih.
- `isolatePart` mengisi `isolatedIds = [id]` dan memilih bagian itu.
- `showAll` mengosongkan `hiddenIds` dan `isolatedIds`.
- `revealPart` menyalakan sistemnya, menghapus id dari `hiddenIds`, mengosongkan isolasi bila id tidak termasuk, lalu memilih bagian itu.
- `isPartVisible` bernilai benar kalau sistemnya menyala, id tidak disembunyikan, dan (`isolatedIds === null` atau id termasuk di dalamnya).

Peringkat pencarian (angka kecil lebih dulu):
0. salah satu nama sama persis dengan query;
1. nama diawali query;
2. setiap kata query adalah awalan salah satu kata nama;
3. query muncul di tengah nama.

Kalau peringkatnya sama, nama yang lebih pendek didahulukan. Query kosong mengembalikan `[]`.

- [ ] **Step 1: Tulis tes yang gagal**

```ts
// src/atlas/viewState.test.ts
import { initialViewState, isPartVisible, viewReducer } from './viewState';

const femur = { id: 'BP3D:FJ1', system: 'skeletal' as const };
const biceps = { id: 'BP3D:FJ2', system: 'muscular' as const };

test('initial state shows skin, bones and organs but not muscles', () => {
  const s = initialViewState();
  expect(isPartVisible(s, femur)).toBe(true);
  expect(isPartVisible(s, biceps)).toBe(false);
});
test('setBody clears selection, hidden and isolation', () => {
  let s = viewReducer(initialViewState(), { type: 'isolatePart', id: femur.id });
  s = viewReducer(s, { type: 'hidePart', id: 'BP3D:FJ7' });
  s = viewReducer(s, { type: 'setBody', body: 'female' });
  expect([s.selectedId, s.hiddenIds, s.isolatedIds]).toEqual([null, [], null]);
});
test('revealPart turns the system on and unhides', () => {
  let s = viewReducer(initialViewState(), { type: 'hidePart', id: biceps.id });
  s = viewReducer(s, { type: 'revealPart', id: biceps.id, system: 'muscular' });
  expect(isPartVisible(s, biceps)).toBe(true);
  expect(s.selectedId).toBe(biceps.id);
});
test('isolation hides everything else until showAll', () => {
  let s = viewReducer(initialViewState(), { type: 'isolatePart', id: femur.id });
  expect(isPartVisible(s, { id: 'BP3D:FJ3', system: 'skeletal' })).toBe(false);
  s = viewReducer(s, { type: 'showAll' });
  expect(isPartVisible(s, { id: 'BP3D:FJ3', system: 'skeletal' })).toBe(true);
});
test('explode is clamped to 0..1', () => {
  expect(viewReducer(initialViewState(), { type: 'setExplode', amount: 3 }).explode).toBe(1);
});
```

```ts
// src/atlas/search.test.ts
import { buildSearchIndex, searchParts } from './search';

const p = (id: string, en: string, extra = {}) => ({ id, names: { en, ...extra } }) as any;
const index = buildSearchIndex([
  p('a', 'Heart', { id: 'Jantung', la: 'cor' }),
  p('b', 'Left femoral artery', { la: 'arteria femoralis sinistra' }),
  p('c', 'Femur', { id: 'tulang paha' }),
  p('d', 'Cartilage of femur head'),
]);

test('partial Indonesian words match', () => expect(searchParts(index, 'jant')).toEqual(['a']));
test('case, spaces and accents are ignored', () => expect(searchParts(index, '  CÓR ')).toEqual(['a']));
test('ranking: exact, then prefix, then word prefix, then substring', () =>
  expect(searchParts(index, 'femur')).toEqual(['c', 'd']));
test('word prefixes in any name style', () => expect(searchParts(index, 'arteria fem')).toEqual(['b']));
test('no match and empty query return nothing', () => {
  expect(searchParts(index, 'zzz')).toEqual([]);
  expect(searchParts(index, '   ')).toEqual([]);
});
```

- [ ] **Step 2: Jalankan, pastikan gagal**

Run: `npx vitest run src/atlas/viewState.test.ts src/atlas/search.test.ts`
Expected: FAIL, modul belum ada.

- [ ] **Step 3: Implementasi `viewState.ts` dan `search.ts`**

- [ ] **Step 4: Jalankan, pastikan lulus**

Run: `npx vitest run src/atlas && npm run typecheck`
Expected: semua tes `src/atlas` lulus.

- [ ] **Step 5: Commit**

```bash
git add src/atlas
git commit -m "feat(atlas): state tampilan dan pencarian nama dua gaya"
```

---

### Task 9: Geometri per sistem, urai, dan preset kamera

**Files:**
- Create: `src/scene/loadSystem.ts`, `src/scene/SystemBatch.ts`, `src/scene/explode.ts`, `src/scene/cameraPresets.ts`
- Test: `src/scene/loadSystem.test.ts`, `src/scene/explode.test.ts`, `src/scene/cameraPresets.test.ts`

**Interfaces:**
- Consumes: `SystemId` (Task 7).
- Produces:
  - `type Vec3 = [number, number, number]`, `interface Box3Like { min: Vec3; max: Vec3 }`
  - `toWorldFloatGeometry(mesh: THREE.Mesh): THREE.BufferGeometry`. Posisi dan normal menjadi Float32 (kuantisasi dibuka), `mesh.matrixWorld` diterapkan, dan indeks dipertahankan.
  - `loadSystemGeometries(url: string, onProgress?: (fraction: number) => void): Promise<Map<string, THREE.BufferGeometry>>`. Memakai `GLTFLoader` dengan `MeshoptDecoder` dari `three/examples/jsm/libs/meshopt_decoder.module.js`. Kuncinya nama node (= id part).
  - `class SystemBatch`:
    - `constructor(system: SystemId, geometries: Map<string, THREE.BufferGeometry>, color: string)`
    - `readonly mesh: THREE.BatchedMesh`
    - `setVisibility(isVisible: (id: string) => boolean): void`
    - `setHighlight(id: string | null): void`, yang mewarnai bagian terpilih dengan `#6bd9c7`
    - `setOpacity(opacity: number): void`
    - `setExplode(amount: number, bodyCenter: Vec3): void`
    - `partIdAt(instanceId: number): string`
    - `dispose(): void`
  - `explodeOffset(partCenter: Vec3, bodyCenter: Vec3, amount: number): Vec3` = `(partCenter − bodyCenter) ⊙ (1.5, 0.6, 1.5) × amount`
  - `type CameraPreset = 'depan' | 'samping' | 'belakang' | 'awal'`
  - `fitDistance(bounds: Box3Like, fovDeg: number, aspect: number): number`. Jarak supaya seluruh kotak terlihat, ditambah margin 15%.
  - `presetPose(preset: CameraPreset, bounds: Box3Like, fovDeg: number, aspect: number): { position: Vec3; target: Vec3 }`. Target = pusat kotak. Arah kamera: `depan` dari +Z, `belakang` dari −Z, `samping` dari +X, `awal` dari arah (0.35, 0.25, 1) yang dinormalkan.

- [ ] **Step 1: Tulis tes yang gagal**

```ts
// src/scene/explode.test.ts
import { explodeOffset } from './explode';
test('no offset at zero, radial and scaled otherwise', () => {
  expect(explodeOffset([1, 2, 3], [0, 1, 0], 0)).toEqual([0, 0, 0]);
  expect(explodeOffset([1, 2, 3], [0, 1, 0], 1)).toEqual([1.5, 0.6, 4.5]);
});
```

```ts
// src/scene/cameraPresets.test.ts
import { fitDistance, presetPose } from './cameraPresets';
const body = { min: [-0.3, 0, -0.15], max: [0.3, 1.7, 0.15] } as const;
test('presetPose depan looks at the front', () => {
  const { position, target } = presetPose('depan', body as any, 34, 1);
  expect(position[2]).toBeGreaterThan(target[2]);
  expect(position[0]).toBeCloseTo(target[0]);
});
test('belakang and samping', () => {
  expect(presetPose('belakang', body as any, 34, 1).position[2]).toBeLessThan(0);
  expect(presetPose('samping', body as any, 34, 1).position[0]).toBeGreaterThan(0);
});
test('bigger bounds need more distance', () => {
  const big = { min: [-1, 0, -1], max: [1, 3.4, 1] } as any;
  expect(fitDistance(big, 34, 1)).toBeGreaterThan(fitDistance(body as any, 34, 1));
});
```

```ts
// src/scene/loadSystem.test.ts
import * as THREE from 'three';
import { toWorldFloatGeometry } from './loadSystem';
test('dequantizes positions and applies the world matrix', () => {
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.BufferAttribute(new Int16Array([32767, 0, 0]), 3, true));
  g.setAttribute('normal', new THREE.BufferAttribute(new Int8Array([0, 127, 0]), 3, true));
  const mesh = new THREE.Mesh(g);
  mesh.position.set(0, 1, 0);
  mesh.scale.setScalar(2);
  mesh.updateMatrixWorld(true);
  const out = toWorldFloatGeometry(mesh);
  expect(out.getAttribute('position').array).toBeInstanceOf(Float32Array);
  expect(Array.from(out.getAttribute('position').array)).toEqual([2, 1, 0]);
  expect(out.getAttribute('normal').getY(0)).toBeCloseTo(1);
});
```

- [ ] **Step 2: Jalankan, pastikan gagal**

Run: `npx vitest run src/scene`
Expected: FAIL, modul belum ada.

- [ ] **Step 3: Implementasi keempat file**

`SystemBatch` membuat satu `BatchedMesh` (kapasitas = jumlah verteks/indeks semua geometri) dengan `MeshStandardMaterial` (warna sistem, `roughness 0.55`, `metalness 0.05`, `side: DoubleSide`). Setiap geometri ditambahkan dengan `addGeometry` lalu `addInstance`; `partIdAt` memakai peta instanceId → id. Raycast dipercepat dengan `three-mesh-bvh`: pasang `BatchedMesh.prototype.computeBoundsTree = computeBatchedBoundsTree` dan `raycast = acceleratedRaycast`, lalu panggil `computeBoundsTree()` setelah batch selesai dibuat.

- [ ] **Step 4: Jalankan, pastikan lulus**

Run: `npx vitest run src/scene && npm run typecheck`
Expected: 5 passed, tanpa error tipe.

- [ ] **Step 5: Commit**

```bash
git add src/scene
git commit -m "feat(scene): geometri per sistem, urai, dan preset kamera"
```

---

### Task 10: AtlasScene — renderer, lapisan, klik, tembus pandang

**Files:**
- Create: `src/scene/AtlasScene.ts`, `src/scene/picking.ts`
- Test: `src/scene/picking.test.ts`, `src/scene/AtlasScene.test.ts`

**Interfaces:**
- Consumes: `SystemBatch`, `loadSystemGeometries`, `presetPose`, `explodeOffset` (Task 9); `ViewState`, `isPartVisible` (Task 8); `BodyManifest`, `systemInfo` (Task 7).
- Produces:
  - `isTap(down: { x: number; y: number; t: number }, up: { x: number; y: number; t: number }, maxMove = 6, maxMs = 500): boolean`
  - `interface AtlasSceneEvents { onPick(id: string | null): void; onLoading(state: { system: SystemId; fraction: number } | null): void; onLayerError(system: SystemId, message: string): void }`
  - `class AtlasScene`:
    - `static isSupported(): boolean`, benar jika `canvas.getContext('webgl2')` tidak null
    - `constructor(container: HTMLElement, events: AtlasSceneEvents)`
    - `setManifest(manifest: BodyManifest, baseUrl: string): void`, membuang batch lama
    - `ensureSystems(systems: SystemId[]): Promise<void>`. Memuat sistem yang belum ada satu per satu. Kegagalan satu sistem memanggil `onLayerError` tanpa membatalkan sistem lain, dan sistem itu bisa dicoba ulang.
    - `applyView(state: ViewState): void`
    - `setCameraPreset(preset: CameraPreset): void`
    - `focusPart(id: string): void`
    - `dispose(): void`

Perilaku yang ditetapkan:
- Render hanya saat ada perubahan atau kontrol sedang berayun (damping).
- Latar gelap `#0d1117`; ada platform bundar putih di lantai, seperti di video DeepMind.
- Saat `xray` aktif: opasitas kulit 0,18 (`depthWrite: false`) dan otot 0,55. Saat `xray` mati, keduanya opak.
- Klik hanya dihitung kalau `isTap`. Bagian yang tersembunyi tidak bisa terkena klik.
- `?fps=1` di URL menampilkan penghitung fps kecil untuk pengecekan performa.

- [ ] **Step 1: Tulis tes yang gagal**

```ts
// src/scene/picking.test.ts
import { isTap } from './picking';
test('short, still presses are taps; drags are not', () => {
  expect(isTap({ x: 0, y: 0, t: 0 }, { x: 3, y: 4, t: 200 })).toBe(true);
  expect(isTap({ x: 0, y: 0, t: 0 }, { x: 20, y: 0, t: 200 })).toBe(false);
  expect(isTap({ x: 0, y: 0, t: 0 }, { x: 0, y: 0, t: 900 })).toBe(false);
});
```

```ts
// src/scene/AtlasScene.test.ts
import { AtlasScene } from './AtlasScene';
test('reports no support when WebGL2 is missing', () => {
  const spy = vi.spyOn(HTMLCanvasElement.prototype, 'getContext').mockReturnValue(null);
  expect(AtlasScene.isSupported()).toBe(false);
  spy.mockRestore();
});
```

- [ ] **Step 2: Jalankan, pastikan gagal**

Run: `npx vitest run src/scene/picking.test.ts src/scene/AtlasScene.test.ts`
Expected: FAIL, modul belum ada.

- [ ] **Step 3: Implementasi `picking.ts` dan `AtlasScene.ts`**

- [ ] **Step 4: Jalankan, pastikan lulus**

Run: `npx vitest run src/scene && npm run typecheck`
Expected: semua tes `src/scene` lulus.

- [ ] **Step 5: Commit**

```bash
git add src/scene
git commit -m "feat(scene): renderer atlas, muat lapisan per sistem, klik, tembus pandang"
```

---

### Task 11: Antarmuka bahasa Indonesia

**Files:**
- Create: `src/ui/strings.ts`, `src/ui/useAtlas.ts`, `src/ui/AtlasApp.tsx`, `src/ui/TopBar.tsx`, `src/ui/SearchBox.tsx`, `src/ui/LayerBar.tsx`, `src/ui/ViewTools.tsx`, `src/ui/InfoPanel.tsx`, `src/ui/LayerErrorBanner.tsx`, `src/ui/AttributionDialog.tsx`
- Modify: `src/App.tsx`, `src/styles.css`, `src/App.test.tsx`
- Test: `src/ui/LayerBar.test.tsx`, `src/ui/InfoPanel.test.tsx`, `src/ui/SearchBox.test.tsx`, `src/ui/LayerErrorBanner.test.tsx`

**Interfaces:**
- Consumes: semua yang di atas.
- Produces:
  - `useAtlas(): { state: ViewState; dispatch: Dispatch<ViewAction>; manifest: BodyManifest | null; parts: Map<string, PartRecord>; loading: { system: SystemId; fraction: number } | null; layerErrors: Partial<Record<SystemId, string>>; retryLayer(system: SystemId): void; sceneRef: RefObject<HTMLDivElement> }`
  - `App` selalu menampilkan judul, lalu `AtlasApp` (yang memakai `useAtlas`) kalau `AtlasScene.isSupported()`, atau pesan `noWebgl` kalau tidak. Dengan begitu `useAtlas` tidak pernah jalan di browser tanpa WebGL2.
  - `LayerErrorBanner` menerima props `{ errors: Partial<Record<SystemId, string>>; onRetry(system: SystemId): void }` dan tidak menampilkan apa pun kalau `errors` kosong.
  - Komponen menerima `state`, `dispatch`, dan data yang dibutuhkan lewat props. Tidak ada state global lain.

Teks yang ditetapkan (`strings.ts`):

| Kunci | Teks |
|---|---|
| title | `Atlas Anatomi 3D` |
| bodyFemale | `Perempuan` |
| bodyMale | `Laki-laki` |
| femaleSoon | `Badan perempuan menyusul di tahap 2` |
| istilah | `Istilah` |
| istilahRingan | `Ringan` |
| istilahKesehatan | `Kesehatan` |
| searchPlaceholder | `Cari bagian tubuh…` |
| notFound | `Tidak ditemukan` |
| allSystems | `Semua sistem` |
| depan / samping / belakang / awal | `Depan` / `Samping` / `Belakang` / `Awal` |
| xray | `Tembus pandang` |
| explode | `Urai` |
| isolate / hide / focus / showAll | `Isolasi` / `Sembunyikan` / `Fokus` / `Tampilkan semua` |
| system / side / origin | `Sistem` / `Sisi` / `Asal data` |
| originMale | `Asli laki-laki (BodyParts3D)` |
| originFemale | `Asli perempuan` |
| originFitted | `Dipasang dari model laki-laki` |
| attribution | `Sumber data` |
| noWebgl | `Browser ini belum bisa menampilkan 3D karena WebGL2 tidak tersedia. Coba buka di Chrome atau Edge terbaru.` |
| layerError | `Gagal memuat lapisan {sistem}.` |
| retry | `Coba lagi` |
| loading | `Memuat {sistem}… {persen}%` |

Tata letak:
- **Atas:** judul, sakelar badan (Perempuan nonaktif dengan tooltip `femaleSoon`), sakelar Istilah, dan kotak cari dengan daftar hasil.
- **Bawah:** tombol grup lapisan, plus tombol `Semua sistem` yang membuka daftar centang per sistem.
- **Kanan:** preset kamera, `Tembus pandang`, dan slider `Urai`.
- **Panel info:** nama utama, nama kedua (kecil), sistem, sisi, asal data, serta tombol Isolasi/Sembunyikan/Fokus/Tampilkan semua.
- **Lebar < 768 px:** panel info menjadi lembar dari bawah, bar lapisan bisa digeser ke samping, dan alat kamera dilipat ke satu tombol menu.
- `AttributionDialog` merender `ATTRIBUTION.md` (import `?raw`) dengan `marked`.

- [ ] **Step 1: Tulis tes yang gagal**

```tsx
// src/ui/LayerBar.test.tsx
import { fireEvent, render, screen } from '@testing-library/react';
import { initialViewState } from '../atlas/viewState';
import LayerBar from './LayerBar';
test('clicking a group dispatches setGroup', () => {
  const dispatch = vi.fn();
  render(<LayerBar state={initialViewState()} dispatch={dispatch} />);
  fireEvent.click(screen.getByRole('button', { name: 'Otot' }));
  expect(dispatch).toHaveBeenCalledWith({ type: 'setGroup', group: 'otot', on: true });
});
```

```tsx
// src/ui/InfoPanel.test.tsx
import { render, screen } from '@testing-library/react';
import { initialViewState } from '../atlas/viewState';
import InfoPanel from './InfoPanel';
const part = { id: 'BP3D:FJ1', system: 'skeletal', side: 'left', origin: 'laki-laki-asli', source: 'bodyparts3d',
  sourceRef: 'FJ1', names: { en: 'Left femur', id: 'tulang paha kiri', la: 'femur sinistrum' },
  bounds: [[0, 0, 0], [1, 1, 1]], file: 'skeletal.glb', triangles: 4 } as const;
test('shows names in the chosen style, side and origin in Indonesian', () => {
  render(<InfoPanel part={part as any} state={{ ...initialViewState(), istilah: 'kesehatan' }} dispatch={vi.fn()} />);
  expect(screen.getByRole('heading', { name: 'femur sinistrum' })).toBeInTheDocument();
  expect(screen.getByText('tulang paha kiri')).toBeInTheDocument();
  expect(screen.getByText('kiri')).toBeInTheDocument();
  expect(screen.getByText('Asli laki-laki (BodyParts3D)')).toBeInTheDocument();
});
```

```tsx
// src/ui/SearchBox.test.tsx
import { fireEvent, render, screen } from '@testing-library/react';
import { buildSearchIndex } from '../atlas/search';
import { initialViewState } from '../atlas/viewState';
import SearchBox from './SearchBox';
const parts = [{ id: 'a', system: 'cardiac', names: { en: 'Heart', id: 'Jantung' } }] as any;
test('shows "Tidak ditemukan" and reveals a found part', () => {
  const dispatch = vi.fn();
  render(<SearchBox index={buildSearchIndex(parts)} parts={new Map(parts.map((p: any) => [p.id, p]))}
    state={initialViewState()} dispatch={dispatch} />);
  const box = screen.getByPlaceholderText('Cari bagian tubuh…');
  fireEvent.change(box, { target: { value: 'zzz' } });
  expect(screen.getByText('Tidak ditemukan')).toBeInTheDocument();
  fireEvent.change(box, { target: { value: 'jant' } });
  fireEvent.click(screen.getByRole('option', { name: /Jantung/ }));
  expect(dispatch).toHaveBeenCalledWith({ type: 'revealPart', id: 'a', system: 'cardiac' });
});
```

```tsx
// src/ui/LayerErrorBanner.test.tsx
import { fireEvent, render, screen } from '@testing-library/react';
import LayerErrorBanner from './LayerErrorBanner';
test('shows a retry banner when a layer fails to load', () => {
  const onRetry = vi.fn();
  render(<LayerErrorBanner errors={{ muscular: 'Gagal memuat lapisan Otot.' }} onRetry={onRetry} />);
  expect(screen.getByText('Gagal memuat lapisan Otot.')).toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: 'Coba lagi' }));
  expect(onRetry).toHaveBeenCalledWith('muscular');
});
```

Tambahkan ke `src/App.test.tsx`:

```tsx
test('shows a WebGL2 message when 3D is unsupported', () => {
  vi.spyOn(AtlasScene, 'isSupported').mockReturnValue(false);
  render(<App />);
  expect(screen.getByText(/WebGL2 tidak tersedia/)).toBeInTheDocument();
});
```

- [ ] **Step 2: Jalankan, pastikan gagal**

Run: `npx vitest run src/ui src/App.test.tsx`
Expected: FAIL, komponen belum ada.

- [ ] **Step 3: Implementasi `strings.ts`, `useAtlas.ts`, komponen, `App.tsx`, dan `styles.css`**

`useAtlas` memuat manifest, membuat `AtlasScene` di `sceneRef`, lalu memanggil `ensureSystems` untuk sistem yang menyala setiap kali `state.systems` berubah. Ia meneruskan `applyView(state)` setiap kali state berubah, dan menyalurkan `onPick` ke `dispatch({ type: 'select', id })`.

- [ ] **Step 4: Jalankan semua tes**

Run: `npx vitest run && npm run typecheck`
Expected: semua tes lulus, tanpa error tipe.

- [ ] **Step 5: Commit**

```bash
git add src
git commit -m "feat(ui): antarmuka bahasa Indonesia: lapisan, cari, info, istilah, kamera"
```

---

### Task 12: Atribusi, README, dan pemeriksaan akhir

**Files:**
- Create: `ATTRIBUTION.md`
- Modify: `README.md`

**Interfaces:**
- Consumes: semua task sebelumnya.

- [ ] **Step 1: Tulis `ATTRIBUTION.md`**

Isi minimal:
- **BodyParts3D**, © The Database Center for Life Science, CC BY 4.0. Sertakan tautan lisensi `https://dbarchive.biosciencedbc.jp/en/bodyparts3d/lic.html`, tautan unduhan, dan catatan bahwa komentar CC BY-SA 2.1 JP di dalam file OBJ sudah digantikan lisensi resmi terbaru.
- **Daftar adaptasi:** mm Z-atas → m Y-atas, translasi ke lantai, penyederhanaan meshoptimizer dengan galat 0,2%, kuantisasi dan kompresi meshopt, serta pengelompokan sistem.
- **Wikidata**, CC0, untuk label Indonesia dan Latin lewat P1402.
- **Human-Atlas**, MIT, sebagai acuan teknik. Sertakan teks lisensi MIT kalau ada kode yang diambil.

- [ ] **Step 2: Tulis `README.md`**

README berbahasa Indonesia dan berisi:
- apa ini;
- cara menjalankan: `npm install`, `npm run dev`, dan `npm run dev:hp` untuk membuka dari HP lewat Wi-Fi yang sama, dengan alamat `http://<IP-laptop>:5173`;
- cara membangun ulang data: venv pipeline, lalu `npm run models:male`;
- lisensi kode (MIT) dan lisensi data (lihat `ATTRIBUTION.md`).

- [ ] **Step 3: Jalankan semua pemeriksaan**

Run: `npx vitest run && npm run typecheck && npm run build && npm run models:validate -- male && cd pipeline && .venv/Scripts/python -m pytest -q`
Expected: semua lulus, build berhasil, dan validasi model exit 0.

- [ ] **Step 4: Pemeriksaan di browser (desktop)**

Jalankan `npm run dev`, lalu buka `http://localhost:5173/?fps=1` di panel browser. Periksa:
- badan laki-laki tampil dengan kulit tembus pandang, tulang, dan organ;
- menyalakan Otot memuat lapisan otot (indikator memuat muncul);
- klik tulang paha memunculkan panel info dengan sisi "kiri"/"kanan" yang benar;
- sakelar Istilah mengganti nama;
- mengetik "jant" lalu memilih hasil akan memfokuskan jantung;
- tombol Depan memperlihatkan wajah;
- Urai dan Tembus pandang bekerja;
- dengan semua sistem menyala, fps ≥ 30;
- konsol tanpa error.

- [ ] **Step 5: Pemeriksaan di layar HP**

Ubah ukuran panel browser ke 375×812. Periksa: panel info muncul dari bawah, bar lapisan bisa digeser, alat kamera ada di tombol menu, dan semua tombol masih bisa diketuk.

- [ ] **Step 6: Commit dan push branch**

```bash
git add ATTRIBUTION.md README.md
git commit -m "docs: atribusi data dan panduan menjalankan atlas"
git push -u origin tahap-1-fondasi
```

Expected: branch `tahap-1-fondasi` ada di GitHub. Menggabungkan ke `main` (lewat PR atau merge langsung) menunggu persetujuan pemilik.

---

## Tahap berikutnya

Setiap tahap berikut mendapat rencana sendiri setelah tahap sebelumnya selesai, karena hasilnya menentukan detail rencana berikut. Contohnya, galat registrasi di tahap 2 menentukan cara memasang bagian dari model laki-laki.

2. Badan perempuan lengkap (HRA, BoneHub, Andreassen, dan bagian BodyParts3D yang dipasang).
3. Jantung berdetak dan bisa dimasuki.
4. Aliran darah ke seluruh tubuh dan Ikuti darah.
5. Napas, zoom alveolus, dan Ikuti udara.
6. Nama dan penjelasan dua gaya.
7. Bonus: berdiri, jalan, lari.
