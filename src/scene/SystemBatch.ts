import * as THREE from 'three';
import {
  acceleratedRaycast,
  computeBatchedBoundsTree,
  computeBoundsTree,
  disposeBatchedBoundsTree,
  disposeBoundsTree,
} from 'three-mesh-bvh';
import type { SystemId } from '../atlas/types';
import { explodeOffset, type Vec3 } from './explode';

// The batched raycast hands each instance to Mesh.raycast with only a BVH and no
// bounding sphere, so Mesh must use the accelerated raycast too or every ray misses.
THREE.BufferGeometry.prototype.computeBoundsTree = computeBoundsTree;
THREE.BufferGeometry.prototype.disposeBoundsTree = disposeBoundsTree;
THREE.Mesh.prototype.raycast = acceleratedRaycast;
THREE.BatchedMesh.prototype.computeBoundsTree = computeBatchedBoundsTree;
THREE.BatchedMesh.prototype.disposeBoundsTree = disposeBatchedBoundsTree;
THREE.BatchedMesh.prototype.raycast = acceleratedRaycast;

const HIGHLIGHT = new THREE.Color('#6bd9c7');

/**
 * All parts of one display system drawn as a single BatchedMesh: one draw call,
 * with per-part visibility, highlight colour and explode offset.
 * The material is white and each instance carries the system colour, so a
 * highlight replaces the colour instead of tinting it.
 */
export class SystemBatch {
  readonly mesh: THREE.BatchedMesh;
  private readonly ids: string[] = [];
  private readonly instanceOf = new Map<string, number>();
  private readonly centers: Vec3[] = [];
  private readonly baseColor: THREE.Color;
  private highlighted: number | null = null;

  constructor(readonly system: SystemId, geometries: Map<string, THREE.BufferGeometry>, color: string) {
    let vertexCount = 0;
    let indexCount = 0;
    for (const geometry of geometries.values()) {
      vertexCount += geometry.getAttribute('position').count;
      indexCount += geometry.index?.count ?? 0;
    }
    const material = new THREE.MeshStandardMaterial({
      color: 0xffffff,
      roughness: 0.55,
      metalness: 0.05,
      side: THREE.DoubleSide,
    });
    this.mesh = new THREE.BatchedMesh(geometries.size, vertexCount, indexCount, material);
    this.mesh.name = system;
    this.baseColor = new THREE.Color(color);
    const box = new THREE.Box3();
    const center = new THREE.Vector3();
    for (const [id, geometry] of geometries) {
      const instanceId = this.mesh.addInstance(this.mesh.addGeometry(geometry));
      this.ids[instanceId] = id;
      this.instanceOf.set(id, instanceId);
      this.mesh.setColorAt(instanceId, this.baseColor);
      box.setFromBufferAttribute(geometry.getAttribute('position') as THREE.BufferAttribute).getCenter(center);
      this.centers[instanceId] = [center.x, center.y, center.z];
    }
    this.mesh.computeBoundsTree();
  }

  setVisibility(isVisible: (id: string) => boolean): void {
    this.ids.forEach((id, instanceId) => this.mesh.setVisibleAt(instanceId, isVisible(id)));
  }

  setHighlight(id: string | null): void {
    if (this.highlighted !== null) this.mesh.setColorAt(this.highlighted, this.baseColor);
    const instanceId = id === null ? undefined : this.instanceOf.get(id);
    this.highlighted = instanceId ?? null;
    if (instanceId !== undefined) this.mesh.setColorAt(instanceId, HIGHLIGHT);
  }

  setOpacity(opacity: number): void {
    const material = this.mesh.material as THREE.MeshStandardMaterial;
    const transparent = opacity < 1;
    if (material.opacity === opacity && material.transparent === transparent) return;
    material.opacity = opacity;
    material.transparent = transparent;
    material.depthWrite = !transparent;
    material.needsUpdate = true;
  }

  setExplode(amount: number, bodyCenter: Vec3): void {
    const matrix = new THREE.Matrix4();
    this.centers.forEach((partCenter, instanceId) => {
      const [x, y, z] = explodeOffset(partCenter, bodyCenter, amount);
      this.mesh.setMatrixAt(instanceId, matrix.makeTranslation(x, y, z));
    });
    // setMatrixAt does not refresh the bounds the renderer culls the whole batch by.
    this.mesh.computeBoundingSphere();
    this.mesh.computeBoundingBox();
  }

  has(id: string): boolean {
    return this.instanceOf.has(id);
  }

  partIdAt(instanceId: number): string {
    return this.ids[instanceId];
  }

  dispose(): void {
    this.mesh.disposeBoundsTree();
    this.mesh.dispose();
    (this.mesh.material as THREE.Material).dispose();
  }
}
