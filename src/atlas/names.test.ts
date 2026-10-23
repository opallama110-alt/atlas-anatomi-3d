import { displayName, secondaryName, sideLabel } from './names';

const full = { en: 'Femur', id: 'tulang paha', la: 'femur' };

test('ringan prefers Indonesian, kesehatan prefers Latin', () => {
  expect(displayName(full, 'ringan')).toBe('tulang paha');
  expect(displayName(full, 'kesehatan')).toBe('femur');
});
test('falls back to English when nothing else exists', () => {
  expect(displayName({ en: 'Wall of ventricle' }, 'ringan')).toBe('Wall of ventricle');
  expect(secondaryName({ en: 'Wall of ventricle' }, 'ringan')).toBeUndefined();
});
test('secondary shows the other style without duplicates', () => {
  expect(secondaryName(full, 'ringan')).toBe('femur');
  expect(secondaryName({ en: 'Heart', la: 'cor' }, 'kesehatan')).toBe('Heart');
});
test('curated names win over Wikidata labels', () => {
  expect(displayName({ ...full, ringan: 'tulang paha (femur)' }, 'ringan')).toBe('tulang paha (femur)');
});
test('side labels are Indonesian', () => {
  expect([sideLabel('left'), sideLabel('right'), sideLabel('none')]).toEqual(['kiri', 'kanan', '']);
});
