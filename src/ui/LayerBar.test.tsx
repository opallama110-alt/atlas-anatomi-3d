import { fireEvent, render, screen } from '@testing-library/react';
import { initialViewState } from '../atlas/viewState';
import LayerBar from './LayerBar';

test('clicking a group dispatches setGroup', () => {
  const dispatch = vi.fn();
  render(<LayerBar state={initialViewState()} dispatch={dispatch} />);
  fireEvent.click(screen.getByRole('button', { name: 'Otot' }));
  expect(dispatch).toHaveBeenCalledWith({ type: 'setGroup', group: 'otot', on: true });
});
