import { LAYER_GROUPS, SYSTEMS } from './systems';

test('every system belongs to exactly one layer group', () => {
  for (const s of SYSTEMS) expect(LAYER_GROUPS.filter(g => g.systems.includes(s.id))).toHaveLength(1);
});
test('initial systems are skin, bones, heart and organs', () => {
  expect(SYSTEMS.filter(s => s.initial).map(s => s.id).sort()).toEqual(
    ['cardiac', 'digestive', 'endocrine', 'integumentary', 'lymphatic', 'reproductive', 'respiratory', 'skeletal', 'urinary']);
});
