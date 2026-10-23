import { buildSearchIndex, searchParts } from './search';

const p = (id: string, en: string, extra = {}) => ({ id, names: { en, ...extra } }) as any;
const index = buildSearchIndex([
  p('a', 'Heart', { id: 'Jantung', la: 'cor' }),
  p('b', 'Left femoral artery', { la: 'arteria femoralis sinistra' }),
  p('c', 'Femur', { id: 'tulang paha' }),
  p('d', 'Cartilage of femur head'),
]);

test('partial Indonesian words match', () => expect(searchParts(index, 'jant')).toEqual(['a']));
test('case, spaces and accents are ignored', () => expect(searchParts(index, '  CÓR ')).toEqual(['a']));
test('ranking: exact, then prefix, then word prefix, then substring', () =>
  expect(searchParts(index, 'femur')).toEqual(['c', 'd']));
test('word prefixes in any name style', () => expect(searchParts(index, 'arteria fem')).toEqual(['b']));
test('no match and empty query return nothing', () => {
  expect(searchParts(index, 'zzz')).toEqual([]);
  expect(searchParts(index, '   ')).toEqual([]);
});
