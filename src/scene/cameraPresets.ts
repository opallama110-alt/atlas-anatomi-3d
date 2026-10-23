import type { Vec3 } from './explode';

export type CameraPreset = 'depan' | 'samping' | 'belakang' | 'awal';

export interface Box3Like {
  min: Vec3;
  max: Vec3;
}

const normalize = (v: Vec3): Vec3 => {
  const length = Math.hypot(...v);
  return [v[0] / length, v[1] / length, v[2] / length];
};

/** The body faces +Z, so "depan" (front) looks from +Z. */
const DIRECTIONS: Record<CameraPreset, Vec3> = {
  depan: [0, 0, 1],
  belakang: [0, 0, -1],
  samping: [1, 0, 0],
  awal: normalize([0.35, 0.25, 1]),
};

const center = (b: Box3Like): Vec3 => [0, 1, 2].map((k) => (b.min[k] + b.max[k]) / 2) as Vec3;

/** Distance at which the bounding sphere of `bounds` fits the narrower field of view, plus a 15% margin. */
export function fitDistance(bounds: Box3Like, fovDeg: number, aspect: number): number {
  const radius = 0.5 * Math.hypot(...([0, 1, 2].map((k) => bounds.max[k] - bounds.min[k]) as Vec3));
  const vertical = (fovDeg * Math.PI) / 180;
  const horizontal = 2 * Math.atan(Math.tan(vertical / 2) * aspect);
  return (radius / Math.sin(Math.min(vertical, horizontal) / 2)) * 1.15;
}

export function presetPose(preset: CameraPreset, bounds: Box3Like, fovDeg: number, aspect: number): { position: Vec3; target: Vec3 } {
  const target = center(bounds);
  const distance = fitDistance(bounds, fovDeg, aspect);
  const direction = DIRECTIONS[preset];
  return { position: [0, 1, 2].map((k) => target[k] + direction[k] * distance) as Vec3, target };
}
