import { render, screen } from '@testing-library/react';
import App from './App';

test('shows the atlas title', () => {
  render(<App />);
  expect(screen.getByRole('heading', { name: 'Atlas Anatomi 3D' })).toBeInTheDocument();
});
