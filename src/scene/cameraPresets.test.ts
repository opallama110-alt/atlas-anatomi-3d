import { fitDistance, presetPose } from './cameraPresets';

const body = { min: [-0.3, 0, -0.15], max: [0.3, 1.7, 0.15] } as const;

test('presetPose depan looks at the front', () => {
  const { position, target } = presetPose('depan', body as any, 34, 1);
  expect(position[2]).toBeGreaterThan(target[2]);
  expect(position[0]).toBeCloseTo(target[0]);
});
test('belakang and samping', () => {
  expect(presetPose('belakang', body as any, 34, 1).position[2]).toBeLessThan(0);
  expect(presetPose('samping', body as any, 34, 1).position[0]).toBeGreaterThan(0);
});
test('bigger bounds need more distance', () => {
  const big = { min: [-1, 0, -1], max: [1, 3.4, 1] } as any;
  expect(fitDistance(big, 34, 1)).toBeGreaterThan(fitDistance(body as any, 34, 1));
});
