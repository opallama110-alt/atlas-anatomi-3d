/** Every user-facing text in the atlas, in Indonesian. */
export const STRINGS = {
  title: 'Atlas Anatomi 3D',
  bodyFemale: 'Perempuan',
  bodyMale: 'Laki-laki',
  femaleSoon: 'Badan perempuan menyusul di tahap 2',
  istilah: 'Istilah',
  istilahRingan: 'Ringan',
  istilahKesehatan: 'Kesehatan',
  searchPlaceholder: 'Cari bagian tubuh…',
  notFound: 'Tidak ditemukan',
  allSystems: 'Semua sistem',
  depan: 'Depan',
  samping: 'Samping',
  belakang: 'Belakang',
  awal: 'Awal',
  xray: 'Tembus pandang',
  explode: 'Urai',
  isolate: 'Isolasi',
  hide: 'Sembunyikan',
  focus: 'Fokus',
  showAll: 'Tampilkan semua',
  system: 'Sistem',
  side: 'Sisi',
  origin: 'Asal data',
  originMale: 'Asli laki-laki (BodyParts3D)',
  originFemale: 'Asli perempuan',
  originFitted: 'Dipasang dari model laki-laki',
  attribution: 'Sumber data',
  noWebgl: 'Browser ini belum bisa menampilkan 3D karena WebGL2 tidak tersedia. Coba buka di Chrome atau Edge terbaru.',
  layerError: 'Gagal memuat lapisan {sistem}.',
  retry: 'Coba lagi',
  loading: 'Memuat {sistem}… {persen}%',
  close: 'Tutup',
  camera: 'Kamera',
  layers: 'Lapisan',
  partInfo: 'Info bagian',
  manifestError: 'Data badan gagal dimuat. Muat ulang halaman untuk mencoba lagi.',
} as const;

/** Fill `{key}` placeholders, e.g. fill(STRINGS.loading, { sistem: 'Otot', persen: 40 }). */
export function fill(template: string, values: Record<string, string | number>): string {
  return template.replace(/\{(\w+)\}/g, (match, key: string) => (key in values ? String(values[key]) : match));
}
