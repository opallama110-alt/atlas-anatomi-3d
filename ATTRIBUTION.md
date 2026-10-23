# Sumber data anatomi

Kode aplikasi ini berlisensi MIT (lihat `LICENSE`). Data anatomi **tidak**: setiap sumber di bawah punya lisensinya sendiri, dan atribusinya wajib ikut setiap kali data ini disebarkan.

## BodyParts3D — badan laki-laki

BodyParts3D, © The Database Center for Life Science, licensed under CC Attribution 4.0 International.

- Lisensi: https://dbarchive.biosciencedbc.jp/en/bodyparts3d/lic.html
- Unduhan: https://dbarchive.biosciencedbc.jp/en/bodyparts3d/download.html
- Teks lisensi: https://creativecommons.org/licenses/by/4.0/
- Data yang dipakai: `isa_BP3D_4.0_obj_99.zip` (BodyParts3D 4.0, 2.234 mesh) serta tabel `isa_*` dan `partof_*` untuk nama dan hubungan konsep.
- Publikasi: Mitsuhashi dkk. (2009), *BodyParts3D: 3D structure database for anatomical concepts*. https://doi.org/10.1093/nar/gkn613

Komentar di dalam file OBJ masih menyebut lisensi lama CC BY-SA 2.1 Japan. Halaman lisensi resmi di atas (diperbarui 27 Februari 2025) menggantikannya dan secara tegas mengizinkan penyebaran ulang dan adaptasi di bawah CC BY 4.0.

**Adaptasi yang dilakukan:**

- satuan dan sumbu diubah dari milimeter dengan Z ke atas menjadi meter dengan Y ke atas (sumbu `(x, z, −y)`);
- seluruh badan digeser supaya berdiri di lantai (y = 0) dan berada di tengah;
- setiap mesh disederhanakan dengan meshoptimizer (batas galat 0,2% dari ukuran bagian itu), lalu dikuantisasi dan dikompres dengan `EXT_meshopt_compression`;
- setiap bagian dikelompokkan ke satu sistem tampilan (kulit, otot, tulang, organ, jantung, arteri, vena, saraf, dan seterusnya) berdasarkan pohon IS-A dan PART-OF BodyParts3D, ditambah aturan nama; aturannya ada di `pipeline/atlas_pipeline/systems.py`.

Semua 2.234 mesh tetap ada, dan setiap bagian menyimpan ID file BodyParts3D (`sourceRef`) serta ID konsep FMA (`fma`) di `public/models/male/manifest.json`.

## Wikidata — nama Indonesia dan Latin

Label bahasa Indonesia dan Latin diambil dari Wikidata, yang didedikasikan ke domain publik di bawah CC0 1.0.

- Sumber: https://www.wikidata.org/ (properti P1402, Foundational Model of Anatomy ID)
- Lisensi: https://creativecommons.org/publicdomain/zero/1.0/
- Cache: `pipeline/cache/wikidata-fma-labels.json`

Label dicocokkan lewat ID FMA, bukan lewat nama. Kalau satu ID FMA dimiliki beberapa item, dipakai item dengan nomor Q terkecil. Bagian yang tidak punya label tampil dengan nama gaya lain atau nama Inggris; nama tidak ditebak.

## Human-Atlas — acuan teknik

[Human-Atlas](https://github.com/slorksmo/Human-Atlas) (MIT) dipakai sebagai acuan cara mengolah BodyParts3D, menggabungkan geometri per sistem, dan memilih bagian. Tidak ada kode Human-Atlas yang disalin ke repo ini.
