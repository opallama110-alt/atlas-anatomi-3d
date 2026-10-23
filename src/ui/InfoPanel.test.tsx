import { render, screen } from '@testing-library/react';
import { initialViewState } from '../atlas/viewState';
import InfoPanel from './InfoPanel';

const part = { id: 'BP3D:FJ1', system: 'skeletal', side: 'left', origin: 'laki-laki-asli', source: 'bodyparts3d',
  sourceRef: 'FJ1', names: { en: 'Left femur', id: 'tulang paha kiri', la: 'femur sinistrum' },
  bounds: [[0, 0, 0], [1, 1, 1]], file: 'skeletal.glb', triangles: 4 } as const;

test('shows names in the chosen style, side and origin in Indonesian', () => {
  render(<InfoPanel part={part as any} state={{ ...initialViewState(), istilah: 'kesehatan' }} dispatch={vi.fn()} />);
  expect(screen.getByRole('heading', { name: 'femur sinistrum' })).toBeInTheDocument();
  expect(screen.getByText('tulang paha kiri')).toBeInTheDocument();
  expect(screen.getByText('kiri')).toBeInTheDocument();
  expect(screen.getByText('Asli laki-laki (BodyParts3D)')).toBeInTheDocument();
});
