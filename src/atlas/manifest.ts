import { SYSTEM_IDS } from './systems';
import type { BodyId, BodyManifest } from './types';

const SIDES = ['left', 'right', 'none'];
const ORIGINS = ['perempuan-asli', 'dipasang-dari-laki-laki', 'laki-laki-asli'];

type Loose = Record<string, unknown>;

function fail(reason: string): never {
  throw new Error(`Manifest tidak valid: ${reason}`);
}

const isObject = (value: unknown): value is Loose => typeof value === 'object' && value !== null && !Array.isArray(value);

const isVec3 = (value: unknown) =>
  Array.isArray(value) && value.length === 3 && value.every((n) => typeof n === 'number' && Number.isFinite(n));

export function parseManifest(json: unknown): BodyManifest {
  if (!isObject(json)) fail('bukan objek JSON');
  if (json.version !== 1) fail('versi harus 1');
  if (json.body !== 'female' && json.body !== 'male') fail(`badan tidak dikenal (${String(json.body)})`);
  if (json.units !== 'm' || json.up !== 'y') fail('satuan harus meter dan sumbu atas Y');
  if (!Array.isArray(json.parts) || !Array.isArray(json.systems)) fail('parts dan systems harus berupa daftar');

  for (const part of json.parts as unknown[]) {
    if (!isObject(part) || typeof part.id !== 'string') fail('bagian tanpa id');
    const where = `bagian ${part.id}`;
    if (!SYSTEM_IDS.includes(part.system as never)) fail(`${where}: sistem tidak dikenal (${String(part.system)})`);
    if (!SIDES.includes(part.side as string)) fail(`${where}: sisi tidak dikenal`);
    if (!ORIGINS.includes(part.origin as string)) fail(`${where}: asal tidak dikenal`);
    if (!isObject(part.names) || typeof part.names.en !== 'string') fail(`${where}: nama Inggris wajib ada`);
    if (!Array.isArray(part.bounds) || part.bounds.length !== 2 || !part.bounds.every(isVec3)) fail(`${where}: batas rusak`);
    if (typeof part.file !== 'string' || typeof part.triangles !== 'number') fail(`${where}: file atau segitiga rusak`);
  }
  for (const system of json.systems as unknown[]) {
    if (!isObject(system) || !SYSTEM_IDS.includes(system.id as never)) fail('file sistem tidak dikenal');
    if (typeof system.file !== 'string' || typeof system.bytes !== 'number') fail(`sistem ${String(system.id)}: file rusak`);
  }
  return json as unknown as BodyManifest;
}

export async function loadManifest(body: BodyId, baseUrl = '/models'): Promise<BodyManifest> {
  const response = await fetch(`${baseUrl}/${body}/manifest.json`);
  if (!response.ok) throw new Error(`Manifest ${body} gagal dimuat (HTTP ${response.status})`);
  return parseManifest(await response.json());
}
