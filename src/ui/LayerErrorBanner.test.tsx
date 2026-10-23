import { fireEvent, render, screen } from '@testing-library/react';
import LayerErrorBanner from './LayerErrorBanner';

test('shows a retry banner when a layer fails to load', () => {
  const onRetry = vi.fn();
  render(<LayerErrorBanner errors={{ muscular: 'Gagal memuat lapisan Otot.' }} onRetry={onRetry} />);
  expect(screen.getByText('Gagal memuat lapisan Otot.')).toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: 'Coba lagi' }));
  expect(onRetry).toHaveBeenCalledWith('muscular');
});
