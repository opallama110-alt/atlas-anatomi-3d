# Atlas Anatomi 3D — Rancangan

**Tanggal:** 23 Oktober 2026
**Status:** draf, menunggu persetujuan pemilik
**Lokasi:** folder `G:\My_AI_OS\2_Areas\Atlas-Anatomi-3D`, repo GitHub privat `opallama110-alt/atlas-anatomi-3d`

## 1. Maksud

Atlas anatomi 3D yang jalan di browser untuk mempelajari seluruh tubuh manusia secara berlapis. Pemilik ingin bisa "mengupas" tubuh: mematikan kulit, lalu otot, untuk melihat organ dan tulang di baliknya, dan mengeklik tiap bagian untuk tahu nama dan fungsinya. Setelah itu, pemilik ingin melihat tubuh itu bekerja: jantung berdetak, darah mengalir ke seluruh tubuh, dan udara masuk ke paru-paru sampai oksigennya masuk ke darah. Pemilik juga ingin bisa ikut "jalan-jalan" bersama sel darah dan udara.

Atlas ini berdiri sendiri dan tidak terhubung ke OurLife.

### Kenapa dibuat

Acuan utamanya [atlas.taim.best](https://atlas.taim.best) (repo [slorksmo/Human-Atlas](https://github.com/slorksmo/Human-Atlas), lisensi MIT). Pemilik pernah memakainya untuk belajar dan suka cara lapisannya bisa dinyalakan dan dimatikan. Kekurangannya:

- **Badan perempuannya hampir tanpa otot.** Datanya (HuBMAP Human Reference Atlas) hanya punya otot mata dan lutut. 76 otot kaki ditempel dari dataset lain, sedangkan lengan dan badan atas tidak punya otot sama sekali.
- **Tulangnya sebagian pinjaman.** Tengkorak, rusuk, lengan, dan kaki perempuan memakai tulang dari badan laki-laki.
- **Tidak ada gerak.** Jantung tidak berdetak, dan tidak ada aliran darah maupun napas.

Acuan kedua adalah video DeepMind "Gemini 4 Argon" (21 Oktober 2026, <https://x.com/GoogleDeepMind/status/2112974723659247896>). Video itu menunjukkan badan perempuan yang dibuat dari tiga sumber terbuka yang sama (Human-Atlas, BodyParts3D, HuBMAP): lapisan yang bisa dinyalakan saat tubuh bergerak, otot lengkap, dan zoom ke dalam jantung yang berdetak dengan sel darah merah mengalir.

### Untuk siapa

Untuk pemilik sendiri, sebagai bahan belajar. Repo-nya privat, tapi bisa dijadikan publik atau dionlinekan nanti karena semua datanya berlisensi yang mengizinkan itu.

## 2. Tujuan

1. **Dua badan:** perempuan (fokus utama) dan laki-laki, dipilih dari tombol di atas.
2. **Lapisan yang bisa dinyalakan dan dimatikan:** kulit, otot, tulang, sendi dan jaringan ikat, organ dalam (dikelompokkan per sistem), jantung, arteri, vena, saraf dan otak, serta indra. Beberapa lapisan bisa tampil bersamaan, dan kulit atau otot bisa dibuat tembus pandang.
3. **Badan perempuan lengkap:** otot dari kepala sampai kaki, kerangka lengkap, dan semua organ dalam utama.
4. **Klik untuk info:** setiap bagian bisa diklik atau diketuk. Panel info menampilkan nama, sistem, sisi tubuh, asal datanya, dan penjelasan singkat untuk bagian-bagian utama. Bagian bisa diisolasi, disembunyikan, atau difokuskan.
5. **Sakelar Istilah (Ringan / Kesehatan)** mengganti gaya nama dan penjelasan di seluruh atlas:
   - **Ringan:** bahasa Indonesia sehari-hari, misalnya "tulang paha" dan "otot dada besar".
   - **Kesehatan:** istilah medis berbasis Latin seperti di kuliah kesehatan, misalnya "os femur", "m. pectoralis major", dan "arteri femoralis".
   - Nama dari gaya yang sedang tidak dipilih tetap tampil kecil di bawahnya.
6. **Cari:** cari bagian berdasarkan nama gaya Ringan, gaya Kesehatan, Latin, atau Inggris.
7. **Jantung berdetak di kedua badan,** yang bisa di-zoom sampai masuk ke ruang-ruangnya (atrium, ventrikel, sekat, katup, otot papilaris). Di dalamnya, darah bergerak mengikuti fase detak.
8. **Aliran darah ke seluruh tubuh di kedua badan:** sel darah merah bergerak di semua pembuluh yang ada di model. Darah keluar dari jantung lewat arteri, kembali lewat vena, dan melewati paru-paru (sirkulasi paru).
   - Warnanya merah terang saat kaya oksigen, gelap kebiruan saat miskin oksigen.
   - Iramanya ikut detak jantung.
   - Dari dekat, bentuk sel darah merah (cakram cekung) terlihat.
9. **Napas dan pertukaran oksigen di kedua badan:** udara masuk lewat hidung, tenggorokan, trakea, dan bronkus sampai ke paru-paru. Paru mengembang dan diafragma turun; saat buang napas, udara keluar membawa CO₂. Tampilan zoom ke alveolus menunjukkan oksigen masuk ke sel darah merah dan CO₂ keluar. Bagian ini sudah disetujui lewat mockup tiga panel ([`docs/superpowers/mockups/napas-oksigen.html`](../mockups/napas-oksigen.html)): seluruh tubuh, zoom paru, dan isi alveolus. Ketiga panel itu adalah tingkat zoom yang tampil satu per satu, bukan tiga tampilan sekaligus.
10. **Mode ikuti**, sebagai tambahan dari kamera bebas:
    - **Ikuti darah:** kamera ikut satu sel darah merah dari jantung, lewat arteri sampai tujuan (bawaannya ujung kaki), menyeberang lewat sambungan kapiler ke vena, kembali ke jantung kanan, lewat paru-paru (di sini warnanya berubah jadi merah terang), lalu kembali ke jantung kiri.
    - **Ikuti udara:** kamera ikut udara dari hidung, tenggorokan, trakea, dan bronkus, lalu masuk tanpa putus ke adegan alveolus, tempat oksigen pindah ke sel darah merah.
    - Pemilik bisa keluar dari mode ikuti kapan saja dan lanjut dengan kamera bebas dari posisi itu.
11. **Kontrol animasi:** tombol nyala/mati "Aliran darah" dan "Napas", tombol "Ikuti darah" dan "Ikuti udara", pengatur kecepatan, dan tombol jeda. Detak (±70 kali/menit) dan napas (±15 kali/menit) berjalan pada satu jam yang sama.
12. **Bisa dipakai di laptop dan HP** lewat browser modern. Selama atlas belum dionlinekan, HP membukanya dari laptop lewat Wi-Fi yang sama (server lokal yang bisa diakses dari jaringan rumah).
13. **Bonus, dikerjakan paling akhir:** animasi berdiri, jalan, dan lari seperti di video DeepMind.

### Ukuran keberhasilan

Pemilik bisa melakukan ini dengan lancar di laptopnya:

1. Buka atlas dan pilih badan Perempuan.
2. Matikan kulit dan otot, lalu lihat organ dalam dan kerangka.
3. Klik jantung, lalu masuk ke dalamnya dan lihat jantung berdetak.
4. Nyalakan Aliran darah dan lihat darah bergerak di seluruh tubuh. Lalu tekan Ikuti darah dan ikuti satu sel darah dari jantung ke ujung kaki, kembali ke jantung, lewat paru-paru, sampai ke jantung kiri lagi.
5. Nyalakan Napas, lalu tekan Ikuti udara dan ikuti udara dari hidung sampai oksigennya masuk ke sel darah di alveolus.
6. Klik otot mana pun dan baca nama serta asal datanya. Ganti sakelar Istilah, lalu lihat nama dan penjelasannya berubah gaya.
7. Pindah ke badan Laki-laki dan ulangi langkah 3 sampai 5.

## 3. Bukan tujuan

- Terhubung ke OurLife atau dipakai di sana.
- Alat klinis atau diagnosis.
- Login, akun, server, atau database. Atlas ini situs statis.
- Simulasi fisika aliran darah yang akurat (CFD). Aliran darah dan napas adalah animasi untuk belajar, bukan simulasi medis.
- Memodelkan pembuluh kapiler satu per satu. Ukurannya mikroskopis dan tidak ada di data mana pun.
- Variasi anatomi antar-individu, kondisi penyakit, atau kehamilan sebagai fitur. Struktur plasenta dari sumber data disembunyikan secara bawaan.
- Bahasa Arab seperti di atlas.taim.best.
- Mengonlinekan atlas (deploy). Atlas dijalankan lokal sampai pemilik meminta dionlinekan.

## 4. Anti-tujuan

Pemilik belum menyebut apa pun. Tiga hal ini keputusan Claude dan bisa dikoreksi:

- **Bagian pinjaman tampil seolah asli.** Struktur yang dipasang dari model laki-laki tidak boleh terlihat seperti milik badan perempuan. Asal setiap bagian harus selalu terlihat.
- **Nama yang ditebak dan salah,** baik gaya Ringan maupun Kesehatan. Lebih baik tampil istilah Inggris daripada terjemahan ngawur.
- **Atlas yang patah-patah** di laptop pemilik sampai tidak enak dipakai belajar. Laptopnya Intel Core Ultra 5 125H dengan grafis Intel Arc terintegrasi dan RAM 16 GB.

## 5. Kendala

- **Lisensi:** hanya data yang boleh diubah dan disebarkan ulang (CC BY 4.0 atau CC0). Atribusi lengkap ikut di repo (`ATTRIBUTION.md`) dan bisa dibuka dari dalam atlas.
- **Gambar otot 2D yang dibeli** (`G:\My_AI_OS\3_Resources\Anatomi Otot`) tidak masuk repo, karena lisensi stoknya belum jelas mengizinkan disebarkan. Gambar itu boleh dipakai di komputer sebagai acuan nama otot.
- **GitHub:** tiap file harus di bawah 100 MB. Data mentah (ratusan MB) tidak di-commit dan diunduh ulang lewat skrip. Data hasil olahan yang sudah dikompres di-commit.
- **Perangkat pemilik:** Windows 11, Node 24, Python 3.13, git dengan git-lfs, dan ffmpeg. Ruang kosong di drive G: sekitar 815 GB.
- **Browser:** Chrome atau Edge terbaru di desktop dan Android, dengan WebGL2.

## 6. Sumber data

| Bagian | Badan perempuan | Badan laki-laki |
|---|---|---|
| Kulit dan permukaan tubuh | HuBMAP HRA (kulit, jaringan lemak) | BodyParts3D |
| Organ dalam | HuBMAP HRA, ditambah organ yang tidak dimiliki HRA dari BodyParts3D yang dipasang ke badan perempuan | BodyParts3D |
| Jantung | HuBMAP HRA: 4 ruang, sekat, 4 katup, 5 otot papilaris, pembuluh koroner | BodyParts3D: rongga 4 ruang, dinding atrium dan ventrikel, daun katup satu per satu |
| Tulang | BoneHub Visible Human Female: 143 tulang asli perempuan | BodyParts3D (296 bagian) |
| Otot | 76 otot tungkai asli perempuan (Andreassen dkk. 2023), sisanya dari BodyParts3D yang dipasang ke badan perempuan | BodyParts3D (402 bagian) |
| Pembuluh darah | HRA (110 pembuluh: aorta, vena kava, paru, koroner, organ perut dan panggul), ditambah pembuluh kepala, leher, lengan, dan tungkai dari BodyParts3D yang dipasang | BodyParts3D (±1.040 bagian) |
| Saraf dan otak | HRA (otak 283 region, sumsum tulang belakang, saraf mata), ditambah saraf tepi dari BodyParts3D yang dipasang | BodyParts3D |
| Saluran napas dan paru | HRA (laring, trakea, bronkus sampai tingkat segmen, paru per segmen), ditambah rongga hidung dan faring dari BodyParts3D bila tersedia | BodyParts3D (trakea, pohon bronkial per segmen, rongga hidung, faring); permukaan paru lihat bagian 9 |

Sumber dan lisensinya:

- **HuBMAP Human Reference Atlas**, *3D Reference Organ Set for Female* v1.10 (CC BY 4.0). File: `https://cdn.humanatlas.io/digital-objects/ref-organ/united-female/v1.10/assets/3d-vh-f-united.glb` (374 MB, 956 mesh). Rilis v1.5 dipakai untuk mengembalikan ischium dan pubis yang hilang di v1.10, sama seperti di Human-Atlas. HRA juga punya organ referensi laki-laki (misalnya `lung-male`) dengan lisensi yang sama.
- **BoneHub**, *Visible Human Full-Skeleton 3D Bone Models* (CC BY 4.0, diperbarui 20 Oktober 2026): <https://huggingface.co/datasets/BoneHub/visible-human-3d-models>. Berisi 143 tulang perempuan dalam format STL (±304 MB).
- **Andreassen dkk. (2023)**, *Three Dimensional Lower Extremity Musculoskeletal Geometry of the Visible Human Female and Male*, Scientific Data 10:34 (CC BY 4.0): <https://digitalcommons.du.edu/visiblehuman/1/>. Yang dipakai paket STL perempuan.
- **BodyParts3D 4.0**, © Database Center for Life Science (CC BY 4.0). File: `https://dbarchive.biosciencedbc.jp/data/bodyparts3d/LATEST/isa_BP3D_4.0_obj_99.zip`, beserta tabel nama dan konsepnya.
- **Wikidata** (CC0): label bahasa Indonesia dan Latin, dicocokkan lewat ID Foundational Model of Anatomy (properti P1402). Saat ini sekitar 900 item anatomi berlabel Indonesia dan sekitar 2.000 berlabel Latin.
- **Human-Atlas** (MIT): acuan teknik untuk penggabungan geometri, pemilihan bagian, dan langkah konversi data. Kode yang diambil tetap menyertakan pemberitahuan lisensinya.

HRA, BoneHub, dan Andreassen sama-sama berasal dari satu orang, yaitu *Visible Human Female* dari NLM. Karena itu ketiganya bisa disatukan jauh lebih akurat daripada menggabungkan tubuh dua orang berbeda.

## 7. Menyatukan data menjadi satu badan perempuan

Semua data diubah ke satuan meter dengan sumbu Y ke atas. Tubuh berdiri di lantai (y = 0) dan menghadap +Z.

Kerangka koordinat dasarnya adalah HRA perempuan.

1. **BoneHub dan Andreassen ke HRA.** BoneHub memakai CT "aligned" dari Andreassen, jadi keduanya seharusnya sudah satu kerangka koordinat; builder memeriksa ini lebih dulu.
   - Satu transformasi kaku ditambah skala dipasang dari kerangka CT ke HRA. Pencocokannya memakai permukaan tulang yang ada di kedua sumber (vertebra, sternum, manubrium, pelvis, femur, tibia, fibula, patella) dengan ICP.
   - Galat diukur dan dilaporkan per tulang.
   - Kalau HRA ternyata sudah di-pose ulang dan galatnya besar, pakai pencocokan per daerah seperti di Human-Atlas.
2. **Kerangka perempuan seluruhnya dari BoneHub.** Tulang HRA yang dobel (vertebra, sternum, pelvis, tulang lutut) tidak ditampilkan, supaya kerangka berasal dari satu sumber yang konsisten.
3. **Otot tungkai dari Andreassen** (76 otot). Otot yang sama dari BodyParts3D tidak dipakai supaya tidak dobel. Daftar padanan namanya ditulis eksplisit.
4. **Bagian BodyParts3D yang dipasang ke badan perempuan.** Ini mencakup otot di luar tungkai; pembuluh kepala, leher, lengan, dan tungkai; saraf tepi; serta organ yang tidak ada di HRA (lambung, esofagus, tiroid, kelenjar adrenal, diafragma). Bagian-bagian ini dipindahkan dengan deformasi lentur (thin-plate spline atau RBF) yang dibangun dari dua jenis pasangan titik:
   - tulang BodyParts3D ↔ tulang BoneHub dengan nama yang sama,
   - kulit BodyParts3D ↔ kulit HRA.
5. **Label asal.** Setiap bagian membawa atribut `perempuan-asli` atau `dipasang-dari-laki-laki`. Atlas selalu menampilkan asal ini di panel info, dan semua bagian `dipasang-dari-laki-laki` bisa disorot sekaligus.
6. **Pemeriksaan otomatis:**
   - tidak ada otot atau organ yang menembus kulit melebihi ambang tertentu,
   - paru berada di dalam rongga dada dan otak di dalam tengkorak,
   - ujung pembuluh dari dua sumber bersambung (jarak celahnya dilaporkan).

**Badan laki-laki** memakai BodyParts3D apa adanya. Satuannya diubah dari milimeter dengan Z ke atas menjadi meter dengan Y ke atas. Pengelompokan sistemnya dibuat ulang dari tabel konsep BodyParts3D; misalnya ventrikel otak tidak boleh masuk ke kelompok jantung.

## 8. Tampilan dan interaksi

Seluruh antarmuka berbahasa Indonesia.

- **Atas:** pilihan badan (Perempuan / Laki-laki), sakelar Istilah (Ringan / Kesehatan), dan kolom cari.
- **Bawah:** tombol lapisan (Kulit, Otot, Tulang, Organ, Jantung & pembuluh, Saraf, dan seterusnya), lalu tombol aliran (Aliran darah, Napas), tombol ikuti (Ikuti darah, Ikuti udara), pengatur kecepatan, dan jeda.
- **Kanan:** kontrol kamera (putar, geser, tampak depan/samping/belakang, reset), mode tembus pandang, dan mode urai (explode).
- **Panel info** saat bagian diklik:
  - nama sesuai sakelar Istilah, dengan nama gaya lainnya kecil di bawahnya,
  - sistem, sisi, dan asal data,
  - penjelasan singkat untuk bagian utama,
  - tombol Isolasi, Sembunyikan, dan Fokus.
- **Di HP:** panel info menjadi lembar yang muncul dari bawah, dan kontrol dibuat ringkas.

### Nama dua gaya

**Gaya Ringan** diambil berurutan dari:

1. daftar kurasi tangan untuk sekitar 300 bagian yang paling sering dibuka;
2. label Indonesia dari Wikidata lewat ID FMA;
3. susunan berbasis aturan dari nama dasar yang sudah ada (kiri/kanan, cabang, nomor).

**Gaya Kesehatan** diambil berurutan dari:

1. daftar kurasi tangan untuk sekitar 300 bagian yang sama, dalam bentuk yang lazim di kuliah kesehatan di Indonesia (Latin, atau serapan seperti "arteri femoralis" dan "nervus ischiadicus");
2. label Latin dari Wikidata lewat ID FMA;
3. susunan berbasis aturan dari nama dasar yang sudah ada (misalnya dexter/sinister).

Kalau satu gaya tidak punya nama untuk sebuah bagian, atlas menampilkan nama gaya lainnya atau nama Inggris. Nama tidak pernah ditebak.

### Penjelasan dua gaya

Penjelasan singkat ditulis untuk bagian utama: organ, tulang besar, otot besar, pembuluh utama, bagian jantung, dan saluran napas. Tiap penjelasan punya dua versi:

- **Ringan:** bahasa sehari-hari, pendek.
- **Kesehatan:** lebih teknis, memakai istilah medis.

Sakelar Istilah mengganti versi yang tampil. Kalau baru ada satu versi, versi itu yang tampil. Isi penjelasan merujuk sumber terbuka seperti *OpenStax Anatomy and Physiology 2e* (CC BY 4.0). Bagian lain mendapat penjelasan umum per sistem.

## 9. Gerak: jantung, darah, dan napas

Semua gerak ada di kedua badan. Di setiap tahap, badan perempuan dikerjakan lebih dulu, lalu badan laki-laki.

**Satu jam bersama** menggerakkan semuanya: detak ±70 kali/menit dan napas ±15 kali/menit. Kecepatannya bisa diatur dari 0,25× sampai 2×, dan semuanya bisa dijeda.

### Jantung berdetak

- Dinding atrium berkontraksi lebih dulu, lalu ventrikel. Gerak ini dibuat dengan deformasi per-vertex di shader berdasarkan fase detak.
- Katup membuka dan menutup sesuai fase.
- Kamera bisa masuk ke dalam jantung, dan dinding bagian dalam tetap terlihat (render dua sisi, ditambah potongan bila perlu).
- Di dalam jantung, darah bergerak mengikuti jalur ruang:
  - vena kava → atrium kanan → katup trikuspid → ventrikel kanan → katup pulmonal → arteri pulmonal;
  - vena pulmonal → atrium kiri → katup mitral → ventrikel kiri → katup aorta → aorta.
- Kedua jantung dibagi dengan cara berbeda:
  - HRA (perempuan): 4 ruang, sekat, 4 katup utuh, dan 5 otot papilaris.
  - BodyParts3D (laki-laki): rongga 4 ruang, dinding atrium dan ventrikel, dan tiap daun katup terpisah.
  Karena itu, animasi detak dan jalur darah di dalam jantung dibuat untuk masing-masing badan.

### Aliran darah ke seluruh tubuh

- Pipeline data menghitung garis tengah (centerline) setiap pembuluh, lalu menyambungkannya menjadi satu jaringan berarah: arteri menjauhi jantung, vena menuju jantung, ditambah sirkulasi paru.
- **Sambungan kapiler:** setiap ujung arteri kecil disambungkan ke ujung vena kecil terdekat di daerah tubuh yang sama. Sambungan ini menggantikan kapiler, supaya jalur darah dari jantung ke ujung tubuh dan kembali selalu utuh. Di paru-paru, ujung arteri pulmonal disambungkan ke awal vena pulmonal dengan cara yang sama.
- Di atlas, partikel sel darah merah bergerak di sepanjang jaringan itu. Kecepatannya menyesuaikan ukuran pembuluh, dan di arteri alirannya berdenyut mengikuti detak.
- Warna partikel:
  - merah terang di arteri sistemik dan vena pulmonal,
  - gelap kebiruan di vena sistemik dan arteri pulmonal,
  - berubah warna saat melewati sambungan kapiler (di jaringan tubuh jadi gelap, di paru-paru jadi merah terang).
- Pada aliran umum (banyak partikel sekaligus), partikel boleh tampak memudar di sambungan kapiler.
- Dari jauh, partikel berupa titik kecil. Dari dekat, bentuknya cakram cekung.
- Di HP, jumlah partikel dikurangi otomatis.

### Napas

- Paru-paru mengembang dan mengempis, dan diafragma turun-naik.
- Partikel udara bergerak di dalam saluran napas mengikuti garis tengahnya. Warnanya biru muda saat masuk (kaya O₂) dan abu-abu saat keluar (membawa CO₂).
- Saat melewati paru-paru, partikel darah sirkulasi paru berubah dari gelap kebiruan menjadi merah terang.
- **Zoom ke alveolus** adalah adegan 3D tersendiri yang dibuat dengan kode. Isinya gugus alveolus, jaring kapiler, sel darah merah, serta molekul O₂ dan CO₂ yang berpindah. Adegan ini dibuka dari paru-paru (lewat tombol atau zoom dalam), seperti panel 2 dan 3 di mockup.
- **Paru laki-laki:** BodyParts3D tidak punya permukaan paru, hanya pohon bronkial per segmen. Builder memeriksa dulu apakah mesh segmen itu bisa dipakai sebagai bentuk paru. Kalau tidak bisa, paru laki-laki diambil dari HRA `lung-male` yang dipasang ke badan laki-laki (CC BY 4.0).

### Mode ikuti

- **Ikuti darah:**
  - Tujuan dipilih dari beberapa pilihan: ujung kaki (bawaan), tangan, otak, ginjal, dan usus.
  - Rutenya: ventrikel kiri → aorta → arteri menuju tujuan → sambungan kapiler → vena kembali → atrium kanan → ventrikel kanan → arteri pulmonal → sambungan kapiler paru → vena pulmonal → atrium kiri → ventrikel kiri.
  - Kamera mengikuti sedikit di belakang sel darah, di dalam rongga pembuluh, jadi dinding dalam pembuluh harus terlihat.
  - Saat sel melewati sambungan kapiler paru, tampilan boleh singgah sebentar ke adegan alveolus untuk menunjukkan oksigen masuk.
- **Ikuti udara:**
  - Rutenya: lubang hidung → rongga hidung → faring → laring → trakea → bronkus utama → bronkus lobar → bronkus segmen.
  - Di ujung bronkus, tampilan masuk tanpa putus ke adegan alveolus, lalu kamera melihat oksigen pindah ke sel darah merah.
- Keduanya mengikuti jam bersama: aliran berdenyut saat jantung memompa, dan udara bergerak sesuai tarik dan buang napas.
- Pemilik bisa keluar kapan saja, lalu kamera bebas melanjutkan dari posisi terakhir.

### Bonus: berdiri, jalan, lari

Kerangka diberi rig sederhana dan setiap bagian ikut bergerak bersama tulang terdekat. Siklus jalan dan lari dibuat prosedural dengan kecepatan langkah yang bisa diatur. Bonus ini dikerjakan paling akhir, dan boleh dibatalkan kalau hasilnya merusak bentuk tubuh.

## 10. Arsitektur teknis

- **Aplikasi web:** Vite + React + TypeScript + three.js (rilis stabil terbaru). Hasil build-nya situs statis di `dist/`, dan dijalankan lokal dengan `npm run dev`.
- **Kode viewer ditulis baru**, dengan Human-Atlas sebagai acuan teknik. Alasannya:
  - kode Human-Atlas sangat padat dan membawa dependensi yang tidak dibutuhkan (vinext, plugin Cloudflare, plugin OpenAI Sites);
  - atlas ini butuh banyak animasi, yang lebih mudah ditambahkan pada kode yang rapi.
  Potongan kode yang diambil dari Human-Atlas tetap menyertakan pemberitahuan lisensi MIT.
- **Geometri digabung per sistem** (BatchedMesh, atau geometri gabungan dengan indeks bagian), supaya ribuan bagian tetap ringan digambar. Visibilitas, sorotan, dan posisi urai tiap bagian diatur dari GPU.
- **Pipeline data** (Python/Node, dijalankan lokal) melewati tahap: unduh → normalisasi satuan dan sumbu → registrasi → deformasi → penyederhanaan mesh → garis tengah pembuluh dan saluran napas → sambungan kapiler → pengemasan → validasi.
- **Format runtime:**
  - per badan ada manifest JSON (id, nama dua gaya, sistem, sisi, asal, sumber, batas);
  - geometri terkompresi per sistem, dimuat saat lapisannya pertama kali dinyalakan;
  - data jaringan pembuluh (termasuk sambungan kapiler), saluran napas, jalur jantung, dan rute mode ikuti.
- **Target ukuran unduhan:** lapisan awal (kulit, tulang, organ) paling besar 40 MB per badan. Lapisan lain dimuat saat dibutuhkan.
- **Target performa:**
  - minimal 30 fps di laptop pemilik dengan semua lapisan dan aliran aktif,
  - minimal 30 fps di HP Android kelas menengah dengan mode hemat. Pengujian awal memakai emulasi HP di browser, lalu pengaturan mode hemat disetel ulang di HP pemilik saat pertama dicoba lewat Wi-Fi.
- **Lokasi data:** data mentah di `data/raw/` (di-ignore git), data olahan di `public/models/`.
- **Pengujian:**
  - skrip validasi data: buffer mesh, nama, asal, jaringan pembuluh yang terhubung, rute mode ikuti yang utuh, dan tidak ada bagian yang menembus kulit;
  - pemeriksaan tipe dengan `tsc`;
  - pemeriksaan di browser: memilih bagian, lapisan, cari, isolasi, sakelar Istilah, animasi, mode ikuti, dan ukuran layar HP.

## 11. Urutan kerja

Setiap tahap berakhir dengan atlas yang sudah bisa dipakai.

1. **Fondasi:** repo, pipeline badan laki-laki, dan viewer dasar (lapisan, klik, cari, panel info, antarmuka bahasa Indonesia).
2. **Badan perempuan lengkap:** HRA, BoneHub, Andreassen, dan bagian BodyParts3D yang dipasang, lengkap dengan label asal.
3. **Jantung berdetak** dan bisa dimasuki, di badan perempuan lalu laki-laki.
4. **Aliran darah** ke seluruh tubuh dan **Ikuti darah**, di badan perempuan lalu laki-laki.
5. **Napas**, zoom alveolus, dan **Ikuti udara**, di badan perempuan lalu laki-laki.
6. **Nama dan penjelasan dua gaya** (Ringan dan Kesehatan) untuk bagian utama. Tahap ini bisa berjalan bersamaan dengan tahap lain.
7. **Bonus:** berdiri, jalan, lari.

## 12. Yang diputuskan pemilik

- Atlas berdiri sendiri untuk belajar, bukan untuk OurLife.
- Lapisan bisa dinyalakan dan dimatikan untuk mengupas tubuh sampai organ dalam.
- Badan perempuan lengkap: otot kepala sampai kaki, kerangka lengkap, dan semua organ dalam.
- Jantung berdetak yang bisa di-zoom sampai ke dalam.
- Darah mengalir di seluruh jaringan pembuluh.
- Napas: udara masuk ke paru-paru dan oksigennya disaring masuk ke darah, sesuai mockup tiga panel.
- Jantung berdetak, aliran darah, dan napas ada di kedua badan.
- Ada mode ikuti (Ikuti darah dan Ikuti udara) selain kamera bebas.
- Ada sakelar untuk mengganti istilah antara bahasa ringan dan bahasa kesehatan.
- Badan laki-laki tetap ada, setiap bagian bisa diklik untuk nama dan penjelasan, dan animasi jalan/lari hanya bonus.
- Semua pilihan teknis diserahkan ke Claude.

## 13. Keputusan Claude (tolong dicek)

- Situs statis React + Three.js, tanpa server.
- Untuk badan perempuan, bagian-bagian ini diambil dari model laki-laki lalu dipasang, dengan label yang selalu terlihat:
  - otot di luar tungkai,
  - pembuluh kepala, leher, dan anggota gerak,
  - saraf tepi,
  - organ yang tidak ada di HRA.
- Kerangka perempuan seluruhnya dari BoneHub.
- Sakelar Istilah juga mengganti gaya penjelasan, bukan hanya nama.
- Nama hanya dipakai bila sumbernya jelas; selebihnya tampil nama gaya lain atau Inggris.
- Tujuan Ikuti darah dipilih dari ujung kaki (bawaan), tangan, otak, ginjal, dan usus.
- Di setiap tahap animasi, badan perempuan dikerjakan dulu, lalu laki-laki.
- Paru laki-laki diambil dari HRA `lung-male` kalau BodyParts3D tidak bisa dipakai.
- Folder `G:\My_AI_OS\2_Areas\Atlas-Anatomi-3D` dan repo privat `atlas-anatomi-3d`.
- Kode viewer ditulis baru, dengan Human-Atlas sebagai acuan.
- Gambar otot 2D yang dibeli tidak masuk repo.
- Target ukuran unduhan dan performa di bagian 10.
- Selama belum dionlinekan, HP membuka atlas dari laptop lewat Wi-Fi. Patokan "HP kelas menengah" disetel ulang dengan HP pemilik.
- Tiga panel mockup napas tampil satu per satu sebagai tingkat zoom.
- Tiga anti-tujuan di bagian 4.

## 14. Diserahkan ke builder

- Pilihan library pipeline (misalnya trimesh, meshoptimizer, gltf-transform), parameter penyederhanaan, format biner, dan algoritma garis tengah.
- Struktur folder kode, warna tiap sistem, detail tampilan, dan jumlah partikel.
- Cara menampilkan dinding dalam jantung dan pembuluh saat kamera masuk.
- Cara memilih ujung vena untuk setiap sambungan kapiler.

## 15. Risiko

- **Bentuk otot perempuan di luar tungkai** adalah perkiraan dari model laki-laki. Ini diterima, dengan label asal yang jelas.
- **Registrasi BoneHub ke HRA** bisa meleset kalau HRA sudah di-pose ulang. Rencana cadangannya pencocokan per daerah.
- **Sambungan pembuluh** antara HRA (badan) dan BodyParts3D (kepala dan anggota gerak) bisa bercelah. Mode ikuti butuh jaringan yang benar-benar bersambung, jadi setiap celah harus dijembatani dan dilaporkan.
- **Pekerjaan animasi hampir dua kali lipat** karena ada di kedua badan, dan kedua jantungnya dibagi dengan cara berbeda.
- **Ukuran data dan performa di HP**, karena ada ribuan bagian dan banyak partikel.
- **Nama dan penjelasan dua gaya** butuh sumber terbuka dan kurasi supaya isinya tidak mengarang.
- **HRA tidak punya** lambung, esofagus, tiroid, dan kelenjar adrenal. Semuanya diisi dari model laki-laki yang dipasang.
