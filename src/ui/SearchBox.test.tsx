import { fireEvent, render, screen } from '@testing-library/react';
import { buildSearchIndex } from '../atlas/search';
import { initialViewState } from '../atlas/viewState';
import SearchBox from './SearchBox';

const parts = [{ id: 'a', system: 'cardiac', names: { en: 'Heart', id: 'Jantung' } }] as any;

test('shows "Tidak ditemukan" and reveals a found part', () => {
  const dispatch = vi.fn();
  render(<SearchBox index={buildSearchIndex(parts)} parts={new Map(parts.map((p: any) => [p.id, p]))}
    state={initialViewState()} dispatch={dispatch} />);
  const box = screen.getByPlaceholderText('Cari bagian tubuh…');
  fireEvent.change(box, { target: { value: 'zzz' } });
  expect(screen.getByText('Tidak ditemukan')).toBeInTheDocument();
  fireEvent.change(box, { target: { value: 'jant' } });
  fireEvent.click(screen.getByRole('option', { name: /Jantung/ }));
  expect(dispatch).toHaveBeenCalledWith({ type: 'revealPart', id: 'a', system: 'cardiac' });
});
