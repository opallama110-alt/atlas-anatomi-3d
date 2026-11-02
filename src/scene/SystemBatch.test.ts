import * as THREE from 'three';
import { SystemBatch } from './SystemBatch';

function cube(x: number) {
  const geometry = new THREE.BoxGeometry(0.2, 0.2, 0.2).translate(x, 0, 0);
  geometry.deleteAttribute('uv');
  return geometry;
}

function batchOfTwo() {
  const batch = new SystemBatch('skeletal', new Map([['A', cube(0)], ['B', cube(1)]]), '#ffffff');
  batch.mesh.updateMatrixWorld(true);
  return batch;
}

const rayAt = (x: number) => new THREE.Raycaster(new THREE.Vector3(x, 0, 5), new THREE.Vector3(0, 0, -1));

test('a ray through a part hits it and reports its id', () => {
  const batch = batchOfTwo();
  const hits = rayAt(1).intersectObject(batch.mesh, false);
  expect(hits.length).toBeGreaterThan(0);
  expect(batch.partIdAt(hits[0].batchId!)).toBe('B');
});

test('exploding moves the culling bounds with the parts', () => {
  const batch = batchOfTwo();
  batch.mesh.computeBoundingSphere(); // the renderer does this on the first frame and culls the whole batch by it
  batch.setExplode(2, [0, 0, 0]); // part B (centre x = 1) moves to x = 1 + 1 * 1.5 * 2 = 4
  expect(batch.mesh.boundingSphere!.containsPoint(new THREE.Vector3(4, 0, 0))).toBe(true);
  expect(rayAt(4).intersectObject(batch.mesh, false).length).toBeGreaterThan(0);
});

test('hidden parts cannot be hit', () => {
  const batch = batchOfTwo();
  batch.setVisibility((id) => id !== 'B');
  expect(rayAt(1).intersectObject(batch.mesh, false)).toHaveLength(0);
  expect(rayAt(0).intersectObject(batch.mesh, false).length).toBeGreaterThan(0);
});
