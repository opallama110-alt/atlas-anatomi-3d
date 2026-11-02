import { AtlasScene } from './AtlasScene';

afterEach(() => vi.restoreAllMocks());

test('reports no support when WebGL2 is missing', () => {
  vi.spyOn(HTMLCanvasElement.prototype, 'getContext').mockReturnValue(null);
  expect(AtlasScene.isSupported()).toBe(false);
});

test('reports support when a WebGL2 context is available', () => {
  const getContext = vi
    .spyOn(HTMLCanvasElement.prototype, 'getContext')
    .mockReturnValue({} as WebGL2RenderingContext);
  expect(AtlasScene.isSupported()).toBe(true);
  expect(getContext).toHaveBeenCalledWith('webgl2');
});
