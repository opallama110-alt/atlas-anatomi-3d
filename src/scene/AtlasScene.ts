import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { RoomEnvironment } from 'three/examples/jsm/environments/RoomEnvironment.js';
import { systemInfo } from '../atlas/systems';
import type { BodyManifest, SystemId } from '../atlas/types';
import { isPartVisible, type ViewState } from '../atlas/viewState';
import { fitDistance, presetPose, type Box3Like, type CameraPreset } from './cameraPresets';
import { explodeOffset, type Vec3 } from './explode';
import { loadSystemGeometries } from './loadSystem';
import { isTap, type PointerSample } from './picking';
import { SystemBatch } from './SystemBatch';

const FOV = 34;
/** Opacity of the outer layers while "Tembus pandang" (x-ray) is on. */
const XRAY_OPACITY: Partial<Record<SystemId, number>> = { integumentary: 0.18, muscular: 0.55 };
/** Transparent layers draw outside-in: muscle first, then skin. */
const RENDER_ORDER: Partial<Record<SystemId, number>> = { muscular: 1, integumentary: 2 };
const TWEEN_MS = 450;

export interface AtlasSceneEvents {
  onPick(id: string | null): void;
  onLoading(state: { system: SystemId; fraction: number } | null): void;
  onLayerError(system: SystemId, message: string): void;
}

interface CameraTween {
  fromPosition: THREE.Vector3;
  toPosition: THREE.Vector3;
  fromTarget: THREE.Vector3;
  toTarget: THREE.Vector3;
  start: number;
}

export class AtlasScene {
  static isSupported(): boolean {
    try {
      return !!document.createElement('canvas').getContext('webgl2');
    } catch {
      return false;
    }
  }

  private readonly renderer: THREE.WebGLRenderer;
  private readonly scene = new THREE.Scene();
  private readonly camera = new THREE.PerspectiveCamera(FOV, 1, 0.01, 100);
  private readonly controls: OrbitControls;
  private readonly raycaster = new THREE.Raycaster();
  private readonly batches = new Map<SystemId, SystemBatch>();
  private readonly loading = new Map<SystemId, Promise<void>>();
  private readonly lastExplode = new Map<SystemId, number>();
  private readonly resizeObserver: ResizeObserver;
  private manifest: BodyManifest | null = null;
  private baseUrl = '/models';
  private bodyBounds: Box3Like = { min: [-0.35, 0, -0.2], max: [0.35, 1.75, 0.2] };
  private bodyCenter: Vec3 = [0, 0.875, 0];
  private view: ViewState | null = null;
  private generation = 0;
  private dirty = true;
  private frame = 0;
  private tween: CameraTween | null = null;
  private down: PointerSample | null = null;
  private readonly fpsLabel: HTMLDivElement | null = null;
  private fpsFrames = 0;
  private fpsSince = performance.now();

  constructor(private readonly container: HTMLElement, private readonly events: AtlasSceneEvents) {
    this.renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: 'high-performance' });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, window.innerWidth < 768 ? 1.5 : 2));
    this.renderer.setClearColor('#0d1117');
    this.renderer.outputColorSpace = THREE.SRGBColorSpace;
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.1;
    const canvas = this.renderer.domElement;
    canvas.style.display = 'block';
    canvas.style.touchAction = 'none';
    canvas.setAttribute('aria-label', 'Tubuh 3D. Seret untuk memutar, cubit atau gulir untuk zoom, ketuk bagian untuk melihat namanya.');
    container.appendChild(canvas);

    const pmrem = new THREE.PMREMGenerator(this.renderer);
    this.scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
    pmrem.dispose();
    this.scene.add(new THREE.HemisphereLight(0xffffff, 0x445566, 0.8));
    const key = new THREE.DirectionalLight(0xffffff, 1.6);
    key.position.set(-2, 4, 3);
    const rim = new THREE.DirectionalLight(0xe9f0ff, 1.0);
    rim.position.set(2, 2, -3);
    this.scene.add(key, rim);
    const platform = new THREE.Mesh(
      new THREE.CylinderGeometry(0.62, 0.64, 0.025, 96),
      new THREE.MeshStandardMaterial({ color: 0xe9ecef, roughness: 0.6, metalness: 0.05 }),
    );
    platform.position.y = -0.0125;
    this.scene.add(platform);

    this.controls = new OrbitControls(this.camera, canvas);
    this.controls.enableDamping = true;
    this.controls.dampingFactor = 0.08;
    this.controls.minDistance = 0.05;
    this.controls.maxDistance = 12;
    this.controls.addEventListener('change', () => this.requestRender());

    canvas.addEventListener('pointerdown', this.onPointerDown);
    canvas.addEventListener('pointerup', this.onPointerUp);
    this.resizeObserver = new ResizeObserver(() => this.resize());
    this.resizeObserver.observe(container);

    if (new URLSearchParams(window.location.search).get('fps') === '1') {
      this.fpsLabel = document.createElement('div');
      this.fpsLabel.className = 'fps-counter';
      container.appendChild(this.fpsLabel);
    }

    this.resize();
    this.jumpToPose(presetPose('awal', this.bodyBounds, FOV, this.camera.aspect));
    this.frame = requestAnimationFrame(this.tick);
    // Development builds expose the scene for inspection from the browser console.
    if (import.meta.env.DEV) Object.assign(window, { __atlasScene: this });
  }

  setManifest(manifest: BodyManifest, baseUrl: string): void {
    this.generation += 1;
    for (const batch of this.batches.values()) {
      this.scene.remove(batch.mesh);
      batch.dispose();
    }
    this.batches.clear();
    this.loading.clear();
    this.lastExplode.clear();
    this.manifest = manifest;
    this.baseUrl = baseUrl;
    const min: Vec3 = [Infinity, Infinity, Infinity];
    const max: Vec3 = [-Infinity, -Infinity, -Infinity];
    for (const part of manifest.parts) {
      for (let k = 0; k < 3; k++) {
        min[k] = Math.min(min[k], part.bounds[0][k]);
        max[k] = Math.max(max[k], part.bounds[1][k]);
      }
    }
    if (manifest.parts.length) {
      this.bodyBounds = { min, max };
      this.bodyCenter = [0, 1, 2].map((k) => (min[k] + max[k]) / 2) as Vec3;
    }
    this.jumpToPose(presetPose('awal', this.bodyBounds, FOV, this.camera.aspect));
    this.requestRender();
  }

  /** Load the given systems one after another; a failing system reports an error and the rest continue. */
  async ensureSystems(systems: SystemId[]): Promise<void> {
    for (const system of systems) {
      if (!this.batches.has(system)) await this.loadSystem(system);
    }
  }

  applyView(state: ViewState): void {
    this.view = state;
    for (const batch of this.batches.values()) this.applyBatch(batch, state);
    this.requestRender();
  }

  setCameraPreset(preset: CameraPreset): void {
    this.animateTo(presetPose(preset, this.bodyBounds, FOV, this.camera.aspect));
  }

  focusPart(id: string): void {
    const part = this.manifest?.parts.find((p) => p.id === id);
    if (!part) return;
    const offset = explodeOffset(
      [0, 1, 2].map((k) => (part.bounds[0][k] + part.bounds[1][k]) / 2) as Vec3,
      this.bodyCenter,
      this.view?.explode ?? 0,
    );
    const bounds: Box3Like = {
      min: [0, 1, 2].map((k) => part.bounds[0][k] + offset[k]) as Vec3,
      max: [0, 1, 2].map((k) => part.bounds[1][k] + offset[k]) as Vec3,
    };
    const target = [0, 1, 2].map((k) => (bounds.min[k] + bounds.max[k]) / 2) as Vec3;
    const distance = Math.max(0.12, fitDistance(bounds, FOV, this.camera.aspect));
    const direction = this.camera.position.clone().sub(this.controls.target).normalize();
    const position = new THREE.Vector3(...target).addScaledVector(direction, distance);
    this.animateTo({ position: [position.x, position.y, position.z], target });
  }

  dispose(): void {
    cancelAnimationFrame(this.frame);
    this.generation += 1;
    this.resizeObserver.disconnect();
    const canvas = this.renderer.domElement;
    canvas.removeEventListener('pointerdown', this.onPointerDown);
    canvas.removeEventListener('pointerup', this.onPointerUp);
    for (const batch of this.batches.values()) batch.dispose();
    this.batches.clear();
    this.controls.dispose();
    this.renderer.dispose();
    canvas.remove();
    this.fpsLabel?.remove();
  }

  private loadSystem(system: SystemId): Promise<void> {
    const pending = this.loading.get(system);
    if (pending) return pending;
    const manifest = this.manifest;
    const file = manifest?.systems.find((s) => s.id === system);
    if (!manifest || !file) return Promise.resolve();
    const generation = this.generation;
    const promise = (async () => {
      try {
        this.events.onLoading({ system, fraction: 0 });
        const geometries = await loadSystemGeometries(`${this.baseUrl}/${manifest.body}/${file.file}`, (fraction) =>
          this.events.onLoading({ system, fraction }),
        );
        if (generation !== this.generation) return;
        const batch = new SystemBatch(system, geometries, systemInfo(system).color);
        for (const geometry of geometries.values()) geometry.dispose();
        batch.mesh.renderOrder = RENDER_ORDER[system] ?? 0;
        this.batches.set(system, batch);
        this.scene.add(batch.mesh);
        if (this.view) this.applyBatch(batch, this.view);
        this.requestRender();
      } catch (error) {
        if (generation === this.generation) {
          this.events.onLayerError(system, error instanceof Error ? error.message : String(error));
        }
      } finally {
        if (generation === this.generation) {
          this.loading.delete(system);
          this.events.onLoading(null);
        }
      }
    })();
    this.loading.set(system, promise);
    return promise;
  }

  private applyBatch(batch: SystemBatch, state: ViewState): void {
    batch.mesh.visible = state.systems[batch.system];
    batch.setVisibility((id) => isPartVisible(state, { id, system: batch.system }));
    batch.setHighlight(state.selectedId !== null && batch.has(state.selectedId) ? state.selectedId : null);
    batch.setOpacity(state.xray ? XRAY_OPACITY[batch.system] ?? 1 : 1);
    if (this.lastExplode.get(batch.system) !== state.explode) {
      batch.setExplode(state.explode, this.bodyCenter);
      this.lastExplode.set(batch.system, state.explode);
    }
  }

  private readonly onPointerDown = (event: PointerEvent) => {
    this.down = { x: event.clientX, y: event.clientY, t: performance.now() };
  };

  private readonly onPointerUp = (event: PointerEvent) => {
    const down = this.down;
    this.down = null;
    if (!down || !isTap(down, { x: event.clientX, y: event.clientY, t: performance.now() })) return;
    this.events.onPick(this.pickAt(event.clientX, event.clientY));
  };

  private pickAt(clientX: number, clientY: number): string | null {
    const rect = this.renderer.domElement.getBoundingClientRect();
    const pointer = new THREE.Vector2(
      ((clientX - rect.left) / rect.width) * 2 - 1,
      -((clientY - rect.top) / rect.height) * 2 + 1,
    );
    this.raycaster.setFromCamera(pointer, this.camera);
    // While x-ray is on the skin is nearly invisible, so it must not block taps on what lies beneath.
    const pickable = [...this.batches.values()].filter(
      (b) => b.mesh.visible && !(this.view?.xray && b.system === 'integumentary'),
    );
    const hits = this.raycaster.intersectObjects(pickable.map((b) => b.mesh), false);
    for (const hit of hits) {
      const batch = pickable.find((b) => b.mesh === hit.object);
      if (batch && hit.batchId !== undefined) return batch.partIdAt(hit.batchId);
    }
    return null;
  }

  private resize(): void {
    const width = Math.max(1, this.container.clientWidth);
    const height = Math.max(1, this.container.clientHeight);
    this.renderer.setSize(width, height, false);
    this.renderer.domElement.style.width = '100%';
    this.renderer.domElement.style.height = '100%';
    this.camera.aspect = width / height;
    this.camera.updateProjectionMatrix();
    this.requestRender();
  }

  private requestRender(): void {
    this.dirty = true;
  }

  private jumpToPose(pose: { position: Vec3; target: Vec3 }): void {
    this.tween = null;
    this.camera.position.set(...pose.position);
    this.controls.target.set(...pose.target);
    this.controls.update();
    this.requestRender();
  }

  private animateTo(pose: { position: Vec3; target: Vec3 }): void {
    this.tween = {
      fromPosition: this.camera.position.clone(),
      toPosition: new THREE.Vector3(...pose.position),
      fromTarget: this.controls.target.clone(),
      toTarget: new THREE.Vector3(...pose.target),
      start: performance.now(),
    };
    this.requestRender();
  }

  private readonly tick = () => {
    this.frame = requestAnimationFrame(this.tick);
    if (this.tween) {
      const t = Math.min(1, (performance.now() - this.tween.start) / TWEEN_MS);
      const eased = t < 0.5 ? 2 * t * t : 1 - (-2 * t + 2) ** 2 / 2;
      this.camera.position.lerpVectors(this.tween.fromPosition, this.tween.toPosition, eased);
      this.controls.target.lerpVectors(this.tween.fromTarget, this.tween.toTarget, eased);
      if (t >= 1) this.tween = null;
      this.dirty = true;
    }
    const moved = this.controls.update();
    if (!this.dirty && !moved && !this.fpsLabel) return;
    this.dirty = false;
    this.renderer.render(this.scene, this.camera);
    if (this.fpsLabel) {
      this.fpsFrames += 1;
      const now = performance.now();
      if (now - this.fpsSince >= 1000) {
        this.fpsLabel.textContent = `${Math.round((this.fpsFrames * 1000) / (now - this.fpsSince))} fps`;
        this.fpsFrames = 0;
        this.fpsSince = now;
      }
    }
  };
}
