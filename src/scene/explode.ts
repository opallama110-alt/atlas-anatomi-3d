export type Vec3 = [number, number, number];

/** Spread a part away from the body centre: wide sideways and front-to-back, gentler vertically. */
const SPREAD: Vec3 = [1.5, 0.6, 1.5];

export function explodeOffset(partCenter: Vec3, bodyCenter: Vec3, amount: number): Vec3 {
  // `+ 0` turns a negative zero into zero so offsets compare cleanly.
  return [0, 1, 2].map((k) => (partCenter[k] - bodyCenter[k]) * SPREAD[k] * amount + 0) as Vec3;
}
