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
