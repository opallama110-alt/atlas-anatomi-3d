import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { MeshoptDecoder } from 'three/examples/jsm/libs/meshopt_decoder.module.js';

/**
 * Copy a mesh's geometry into world space as plain Float32 positions and normals.
 * The packaged GLBs are quantized (positions and normals stored as normalized
 * integers with a dequantizing node transform), and every geometry in one
 * BatchedMesh must share attribute formats, so everything is unpacked here.
 */
export function toWorldFloatGeometry(mesh: THREE.Mesh): THREE.BufferGeometry {
  const source = mesh.geometry;
  const position = source.getAttribute('position');
  const normal = source.getAttribute('normal');
  const out = new THREE.BufferGeometry();
  const v = new THREE.Vector3();

  const positions = new Float32Array(position.count * 3);
  for (let i = 0; i < position.count; i++) {
    v.fromBufferAttribute(position, i).applyMatrix4(mesh.matrixWorld);
    positions[i * 3] = v.x;
    positions[i * 3 + 1] = v.y;
    positions[i * 3 + 2] = v.z;
  }
  out.setAttribute('position', new THREE.BufferAttribute(positions, 3));

  const indices = source.index
    ? Uint32Array.from(source.index.array as ArrayLike<number>)
    : Uint32Array.from({ length: position.count }, (_, i) => i);
  out.setIndex(new THREE.BufferAttribute(indices, 1));

  if (normal) {
    const normalMatrix = new THREE.Matrix3().getNormalMatrix(mesh.matrixWorld);
    const normals = new Float32Array(normal.count * 3);
    for (let i = 0; i < normal.count; i++) {
      v.fromBufferAttribute(normal, i).applyMatrix3(normalMatrix).normalize();
      normals[i * 3] = v.x;
      normals[i * 3 + 1] = v.y;
      normals[i * 3 + 2] = v.z;
    }
    out.setAttribute('normal', new THREE.BufferAttribute(normals, 3));
  } else {
    out.computeVertexNormals();
  }
  return out;
}

const loader = new GLTFLoader().setMeshoptDecoder(MeshoptDecoder);

/** A download that receives no bytes for this long counts as failed, so the user gets "Coba lagi". */
export const STALL_MS = 20_000;

async function readBody(url: string, signal: AbortSignal, onChunk: (loaded: number, total: number) => void) {
  const response = await fetch(url, { signal });
  if (!response.ok) throw new Error(`HTTP ${response.status}: ${url}`);
  if (!response.body) return response.arrayBuffer();
  const total = Number(response.headers.get('content-length')) || 0;
  const reader = response.body.getReader();
  const chunks: Uint8Array[] = [];
  let loaded = 0;
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    chunks.push(value);
    loaded += value.byteLength;
    onChunk(loaded, total);
  }
  const bytes = new Uint8Array(loaded);
  let offset = 0;
  for (const chunk of chunks) {
    bytes.set(chunk, offset);
    offset += chunk.byteLength;
  }
  return bytes.buffer;
}

/**
 * Download a model file. Fails when no data arrives for `stallMs` (a dead phone
 * connection often hangs without an error), and aborts the request when it does.
 */
export function fetchModel(
  url: string,
  onProgress?: (fraction: number) => void,
  stallMs = STALL_MS,
): Promise<ArrayBuffer> {
  const controller = new AbortController();
  return new Promise<ArrayBuffer>((resolve, reject) => {
    let timer: ReturnType<typeof setTimeout> | undefined;
    const arm = () => {
      clearTimeout(timer);
      timer = setTimeout(() => {
        controller.abort();
        reject(new Error(`No data for ${stallMs} ms: ${url}`));
      }, stallMs);
    };
    arm();
    readBody(url, controller.signal, (loaded, total) => {
      arm();
      if (total > 0) onProgress?.(Math.min(1, loaded / total));
    })
      .then(resolve, reject)
      .finally(() => clearTimeout(timer));
  });
}

/** Load one system GLB and return its part geometries keyed by part id (the glTF node name). */
export async function loadSystemGeometries(
  url: string,
  onProgress?: (fraction: number) => void,
): Promise<Map<string, THREE.BufferGeometry>> {
  const gltf = await loader.parseAsync(await fetchModel(url, onProgress), '');
  gltf.scene.updateMatrixWorld(true);
  const geometries = new Map<string, THREE.BufferGeometry>();
  gltf.scene.traverse((object) => {
    const mesh = object as THREE.Mesh;
    if (!mesh.isMesh) return;
    // GLTFLoader strips ':' from Object3D.name; the original node name is kept in userData.name.
    const id = (mesh.userData.name as string | undefined) ?? mesh.name;
    geometries.set(id, toWorldFloatGeometry(mesh));
    mesh.geometry.dispose();
  });
  onProgress?.(1);
  return geometries;
}
