import * as THREE from 'three';
import { fetchModel, toWorldFloatGeometry } from './loadSystem';

/** A fetch whose body sends the given chunks, each `gapMs` apart, then closes (or never closes when `hang`). */
function stubFetch(chunks: number[], gapMs: number, { hang = false, status = 200 } = {}) {
  const total = chunks.reduce((sum, n) => sum + n, 0);
  vi.stubGlobal('fetch', vi.fn(async () => {
    const body = new ReadableStream<Uint8Array>({
      async start(controller) {
        for (const size of chunks) {
          await new Promise((resolve) => setTimeout(resolve, gapMs));
          controller.enqueue(new Uint8Array(size));
        }
        if (!hang) controller.close();
      },
    });
    return new Response(body, { status, headers: { 'content-length': String(total) } });
  }));
}

describe('fetchModel', () => {
  beforeEach(() => vi.useFakeTimers());
  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
  });

  test('a download that stops sending data fails instead of loading forever', async () => {
    stubFetch([10], 100, { hang: true });
    const result = fetchModel('/models/male/integumentary.glb', undefined, 1000);
    const failed = expect(result).rejects.toThrow(/1000 ms/);
    await vi.advanceTimersByTimeAsync(1200);
    await failed;
  });

  test('a slow download that keeps sending data finishes and reports progress', async () => {
    stubFetch([10, 10, 10, 10], 800);
    const progress: number[] = [];
    const result = fetchModel('/models/male/muscular.glb', (f) => progress.push(f), 1000);
    await vi.advanceTimersByTimeAsync(4000);
    expect((await result).byteLength).toBe(40);
    expect(progress).toEqual([0.25, 0.5, 0.75, 1]);
  });

  test('a missing file fails', async () => {
    stubFetch([], 0, { status: 404 });
    await expect(fetchModel('/models/male/none.glb', undefined, 1000)).rejects.toThrow(/404/);
  });
});

test('dequantizes positions and applies the world matrix', () => {
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.BufferAttribute(new Int16Array([32767, 0, 0]), 3, true));
  g.setAttribute('normal', new THREE.BufferAttribute(new Int8Array([0, 127, 0]), 3, true));
  const mesh = new THREE.Mesh(g);
  mesh.position.set(0, 1, 0);
  mesh.scale.setScalar(2);
  mesh.updateMatrixWorld(true);
  const out = toWorldFloatGeometry(mesh);
  expect(out.getAttribute('position').array).toBeInstanceOf(Float32Array);
  expect(Array.from(out.getAttribute('position').array)).toEqual([2, 1, 0]);
  expect(out.getAttribute('normal').getY(0)).toBeCloseTo(1);
});
