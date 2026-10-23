import { isTap } from './picking';

test('short, still presses are taps; drags are not', () => {
  expect(isTap({ x: 0, y: 0, t: 0 }, { x: 3, y: 4, t: 200 })).toBe(true);
  expect(isTap({ x: 0, y: 0, t: 0 }, { x: 20, y: 0, t: 200 })).toBe(false);
  expect(isTap({ x: 0, y: 0, t: 0 }, { x: 0, y: 0, t: 900 })).toBe(false);
});
