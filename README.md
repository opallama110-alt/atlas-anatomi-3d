# Atlas Anatomi 3D

Atlas anatomi 3D berlapis untuk belajar, berjalan di browser. Tubuh bisa "dikupas" lapis demi lapis: kulit, otot, tulang, organ dalam, jantung, pembuluh darah, saraf, dan indra. Setiap bagian bisa diklik untuk melihat namanya dalam gaya bahasa ringan atau istilah kesehatan.

Tahap 1 (sekarang) memuat badan laki-laki dari BodyParts3D. Badan perempuan lengkap, jantung berdetak, aliran darah, dan napas menyusul di tahap berikutnya. Rancangan lengkapnya ada di [`docs/superpowers/specs/2026-10-23-atlas-anatomi-3d-design.md`](docs/superpowers/specs/2026-10-23-atlas-anatomi-3d-design.md).

## Menjalankan

Butuh Node.js 22 atau lebih baru.

```sh
npm install
npm run dev
```

Buka <http://localhost:5173>. Tambahkan `?fps=1` di alamat untuk melihat penghitung fps.

### Dari HP

Sambungkan HP ke Wi-Fi yang sama dengan laptop, lalu jalankan:

```sh
npm run dev:hp
```

Buka `http://<IP-laptop>:5173` di browser HP. Alamat IP laptop ditampilkan Vite di terminal, di baris `Network`.

## Cara pakai

- **Atas:** pilih badan, ganti gaya **Istilah** (Ringan / Kesehatan), dan cari bagian tubuh.
- **Bawah:** nyalakan atau matikan lapisan. Tombol **Semua sistem** membuka daftar per sistem.
- **Kanan:** tampak Depan, Samping, Belakang, atau Awal; **Tembus pandang**; dan slider **Urai**.
- **Klik atau ketuk** satu bagian untuk melihat nama, sistem, sisi, dan asal datanya, lalu Isolasi, Sembunyikan, atau Fokus.

## Membangun ulang data

Data olahan sudah ada di `public/models/`, jadi langkah ini tidak wajib. Untuk membangunnya ulang dari sumber, butuh Python 3.13:

```sh
cd pipeline
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
cd ..
npm run models:male
```

Perintah itu mengunduh BodyParts3D ke `data/raw/` (sekitar 143 MB, server sumbernya lambat), mengubahnya menjadi GLB per sistem di `data/work/`, menyederhanakan dan mengompresnya ke `public/models/male/`, lalu memvalidasi hasilnya. `npm run models:validate -- male` hanya menjalankan validasinya.

## Tes

```sh
npm test
npm run typecheck
cd pipeline && .venv/Scripts/python -m pytest -q
```

## Lisensi

- Kode: MIT, lihat [`LICENSE`](LICENSE).
- Data anatomi: lisensi masing-masing sumber, lihat [`ATTRIBUTION.md`](ATTRIBUTION.md). Atribusinya juga bisa dibuka dari tombol **Sumber data** di dalam atlas.
