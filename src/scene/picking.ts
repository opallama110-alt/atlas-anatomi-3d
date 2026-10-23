export interface PointerSample {
  x: number;
  y: number;
  t: number;
}

/** A press counts as a tap (select) only if the pointer barely moved and was released quickly; anything else is an orbit drag. */
export function isTap(down: PointerSample, up: PointerSample, maxMove = 6, maxMs = 500): boolean {
  return Math.hypot(up.x - down.x, up.y - down.y) <= maxMove && up.t - down.t <= maxMs;
}
