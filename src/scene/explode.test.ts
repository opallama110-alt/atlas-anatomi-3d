import { explodeOffset } from './explode';

test('no offset at zero, radial and scaled otherwise', () => {
  expect(explodeOffset([1, 2, 3], [0, 1, 0], 0)).toEqual([0, 0, 0]);
  expect(explodeOffset([1, 2, 3], [0, 1, 0], 1)).toEqual([1.5, 0.6, 4.5]);
});
