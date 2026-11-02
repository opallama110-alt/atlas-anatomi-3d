import { render, screen } from '@testing-library/react';
import App from './App';
import { AtlasScene } from './scene/AtlasScene';

// The real atlas needs WebGL, which jsdom lacks; a stand-in shows which branch App took.
vi.mock('./ui/AtlasApp', () => ({ default: () => <div data-testid="atlas-app" /> }));

afterEach(() => vi.restoreAllMocks());

test('shows the atlas title', () => {
  render(<App />);
  expect(screen.getByRole('heading', { name: 'Atlas Anatomi 3D' })).toBeInTheDocument();
});

test('shows a WebGL2 message when 3D is unsupported', () => {
  vi.spyOn(AtlasScene, 'isSupported').mockReturnValue(false);
  render(<App />);
  expect(screen.getByText(/WebGL2 tidak tersedia/)).toBeInTheDocument();
  expect(screen.queryByTestId('atlas-app')).not.toBeInTheDocument();
});

test('shows the atlas and no WebGL2 message when 3D is supported', () => {
  vi.spyOn(AtlasScene, 'isSupported').mockReturnValue(true);
  render(<App />);
  expect(screen.getByTestId('atlas-app')).toBeInTheDocument();
  expect(screen.queryByText(/WebGL2 tidak tersedia/)).not.toBeInTheDocument();
});
