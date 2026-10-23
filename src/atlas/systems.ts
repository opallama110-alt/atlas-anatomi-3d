import type { LayerGroupId, SystemId } from './types';

export interface SystemInfo {
  id: SystemId;
  label: string;
  color: string;
  /** Shown, and therefore downloaded, when a body first loads. */
  initial: boolean;
}

export interface LayerGroup {
  id: LayerGroupId;
  label: string;
  systems: readonly SystemId[];
}

export const SYSTEMS: readonly SystemInfo[] = [
  { id: 'integumentary', label: 'Kulit', color: '#e8c4a8', initial: true },
  { id: 'muscular', label: 'Otot', color: '#c0504d', initial: false },
  { id: 'skeletal', label: 'Tulang', color: '#ece6d6', initial: true },
  { id: 'connective', label: 'Sendi & jaringan ikat', color: '#b9c7c4', initial: false },
  { id: 'digestive', label: 'Pencernaan', color: '#e0a370', initial: true },
  { id: 'respiratory', label: 'Pernapasan', color: '#e889a0', initial: true },
  { id: 'urinary', label: 'Kemih', color: '#e3c96a', initial: true },
  { id: 'reproductive', label: 'Reproduksi', color: '#d98cb3', initial: true },
  { id: 'endocrine', label: 'Endokrin', color: '#b48cd9', initial: true },
  { id: 'lymphatic', label: 'Limfatik', color: '#8fbf6a', initial: true },
  { id: 'cardiac', label: 'Jantung', color: '#c8323c', initial: true },
  { id: 'arterial', label: 'Arteri', color: '#d23a3a', initial: false },
  { id: 'venous', label: 'Vena', color: '#3a5fd2', initial: false },
  { id: 'nervous', label: 'Saraf & otak', color: '#f2d16b', initial: false },
  { id: 'sensory', label: 'Indra', color: '#7fc8d9', initial: false },
];

export const LAYER_GROUPS: readonly LayerGroup[] = [
  { id: 'kulit', label: 'Kulit', systems: ['integumentary'] },
  { id: 'otot', label: 'Otot', systems: ['muscular'] },
  { id: 'tulang', label: 'Tulang', systems: ['skeletal'] },
  { id: 'sendi', label: 'Sendi', systems: ['connective'] },
  { id: 'organ', label: 'Organ', systems: ['digestive', 'respiratory', 'urinary', 'reproductive', 'endocrine', 'lymphatic'] },
  { id: 'jantung-pembuluh', label: 'Jantung & pembuluh', systems: ['cardiac', 'arterial', 'venous'] },
  { id: 'saraf', label: 'Saraf', systems: ['nervous'] },
  { id: 'indra', label: 'Indra', systems: ['sensory'] },
];

export const SYSTEM_IDS: readonly SystemId[] = SYSTEMS.map((s) => s.id);

export function systemInfo(id: SystemId): SystemInfo {
  const info = SYSTEMS.find((s) => s.id === id);
  if (!info) throw new Error(`Sistem tidak dikenal: ${id}`);
  return info;
}
