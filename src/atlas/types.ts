export type BodyId = 'female' | 'male';

export type SystemId =
  | 'integumentary'
  | 'muscular'
  | 'skeletal'
  | 'connective'
  | 'digestive'
  | 'respiratory'
  | 'urinary'
  | 'reproductive'
  | 'endocrine'
  | 'lymphatic'
  | 'cardiac'
  | 'arterial'
  | 'venous'
  | 'nervous'
  | 'sensory';

export type Origin = 'perempuan-asli' | 'dipasang-dari-laki-laki' | 'laki-laki-asli';

export type Side = 'left' | 'right' | 'none';

export type Istilah = 'ringan' | 'kesehatan';

export type LayerGroupId = 'kulit' | 'otot' | 'tulang' | 'sendi' | 'organ' | 'jantung-pembuluh' | 'saraf' | 'indra';

/** `ringan` and `kesehatan` hold hand-curated names; `id` and `la` come from Wikidata. */
export interface PartNames {
  en: string;
  id?: string;
  la?: string;
  ringan?: string;
  kesehatan?: string;
}

export type Vec3Tuple = [number, number, number];

export interface PartRecord {
  id: string;
  system: SystemId;
  side: Side;
  origin: Origin;
  source: string;
  sourceRef: string;
  fma?: string;
  names: PartNames;
  bounds: [Vec3Tuple, Vec3Tuple];
  file: string;
  triangles: number;
}

export interface SystemFile {
  id: SystemId;
  file: string;
  bytes: number;
  parts: number;
  triangles: number;
}

export interface BodyManifest {
  version: 1;
  body: BodyId;
  units: 'm';
  up: 'y';
  parts: PartRecord[];
  systems: SystemFile[];
}
