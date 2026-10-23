import type { Istilah, PartNames, Side } from './types';

/** Fallback order per style. Names are never guessed: English is the last resort. */
const CHAINS: Record<Istilah, readonly (keyof PartNames)[]> = {
  ringan: ['ringan', 'id', 'kesehatan', 'la', 'en'],
  kesehatan: ['kesehatan', 'la', 'ringan', 'id', 'en'],
};

export function displayName(names: PartNames, istilah: Istilah): string {
  for (const key of CHAINS[istilah]) {
    const value = names[key]?.trim();
    if (value) return value;
  }
  return names.en;
}

export function secondaryName(names: PartNames, istilah: Istilah): string | undefined {
  const primary = displayName(names, istilah);
  const other = displayName(names, istilah === 'ringan' ? 'kesehatan' : 'ringan');
  if (other !== primary) return other;
  if (names.en && names.en !== primary) return names.en;
  return undefined;
}

export function sideLabel(side: Side): string {
  if (side === 'left') return 'kiri';
  if (side === 'right') return 'kanan';
  return '';
}
