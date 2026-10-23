import { SYSTEMS } from './systems';
import type { PartNames, PartRecord } from './types';

export interface SearchIndex {
  /** `systemKey` is the part's Indonesian system label, matched after every name. */
  entries: { id: string; keys: string[]; systemKey?: string }[];
}

/** Rank for a match on the system label only, below every name match. */
const SYSTEM_RANK = 4;

const NAME_KEYS: readonly (keyof PartNames)[] = ['en', 'id', 'la', 'ringan', 'kesehatan'];

export function normalizeQuery(s: string): string {
  return s
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .toLowerCase()
    .replace(/\s+/g, ' ')
    .trim();
}

export function buildSearchIndex(parts: (Pick<PartRecord, 'id' | 'names'> & { system?: PartRecord['system'] })[]): SearchIndex {
  const systemLabel = new Map(SYSTEMS.map((s) => [s.id, normalizeQuery(s.label)]));
  return {
    entries: parts.map((part) => ({
      id: part.id,
      keys: [...new Set(NAME_KEYS.map((k) => part.names[k]).filter((n): n is string => !!n).map(normalizeQuery))],
      systemKey: part.system ? systemLabel.get(part.system) : undefined,
    })),
  };
}

/** 0 exact, 1 prefix, 2 every query word starts a name word, 3 substring, null no match. */
function rank(key: string, query: string, words: string[]): number | null {
  if (key === query) return 0;
  if (key.startsWith(query)) return 1;
  const keyWords = key.split(/[^a-z0-9]+/).filter(Boolean);
  if (words.every((w) => keyWords.some((k) => k.startsWith(w)))) return 2;
  if (key.includes(query)) return 3;
  return null;
}

export function searchParts(index: SearchIndex, query: string, limit = 20): string[] {
  const q = normalizeQuery(query);
  if (!q) return [];
  const words = q.split(' ');
  const hits: { id: string; rank: number; length: number }[] = [];
  for (const entry of index.entries) {
    let best: { rank: number; length: number } | null = null;
    for (const key of entry.keys) {
      const r = rank(key, q, words);
      if (r === null) continue;
      if (!best || r < best.rank || (r === best.rank && key.length < best.length)) best = { rank: r, length: key.length };
    }
    if (!best && entry.systemKey && rank(entry.systemKey, q, words) !== null) {
      best = { rank: SYSTEM_RANK, length: Math.min(...entry.keys.map((k) => k.length)) };
    }
    if (best) hits.push({ id: entry.id, ...best });
  }
  hits.sort((a, b) => a.rank - b.rank || a.length - b.length);
  return hits.slice(0, limit).map((h) => h.id);
}
