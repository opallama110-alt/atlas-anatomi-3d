import { AtlasScene } from './AtlasScene';

test('reports no support when WebGL2 is missing', () => {
  const spy = vi.spyOn(HTMLCanvasElement.prototype, 'getContext').mockReturnValue(null);
  expect(AtlasScene.isSupported()).toBe(false);
  spy.mockRestore();
});
