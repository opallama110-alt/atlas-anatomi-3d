import * as THREE from 'three';
import { toWorldFloatGeometry } from './loadSystem';

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
