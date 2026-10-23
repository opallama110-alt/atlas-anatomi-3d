import { render, screen } from '@testing-library/react';
import App from './App';
import { AtlasScene } from './scene/AtlasScene';

test('shows the atlas title', () => {
  render(<App />);
  expect(screen.getByRole('heading', { name: 'Atlas Anatomi 3D' })).toBeInTheDocument();
});

test('shows a WebGL2 message when 3D is unsupported', () => {
  vi.spyOn(AtlasScene, 'isSupported').mockReturnValue(false);
  render(<App />);
  expect(screen.getByText(/WebGL2 tidak tersedia/)).toBeInTheDocument();
});
