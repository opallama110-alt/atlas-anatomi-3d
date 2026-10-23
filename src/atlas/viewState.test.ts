import { initialViewState, isPartVisible, viewReducer } from './viewState';

const femur = { id: 'BP3D:FJ1', system: 'skeletal' as const };
const biceps = { id: 'BP3D:FJ2', system: 'muscular' as const };

test('initial state shows skin, bones and organs but not muscles', () => {
  const s = initialViewState();
  expect(isPartVisible(s, femur)).toBe(true);
  expect(isPartVisible(s, biceps)).toBe(false);
});
test('setBody clears selection, hidden and isolation', () => {
  let s = viewReducer(initialViewState(), { type: 'isolatePart', id: femur.id });
  s = viewReducer(s, { type: 'hidePart', id: 'BP3D:FJ7' });
  s = viewReducer(s, { type: 'setBody', body: 'female' });
  expect([s.selectedId, s.hiddenIds, s.isolatedIds]).toEqual([null, [], null]);
});
test('revealPart turns the system on and unhides', () => {
  let s = viewReducer(initialViewState(), { type: 'hidePart', id: biceps.id });
  s = viewReducer(s, { type: 'revealPart', id: biceps.id, system: 'muscular' });
  expect(isPartVisible(s, biceps)).toBe(true);
  expect(s.selectedId).toBe(biceps.id);
});
test('isolation hides everything else until showAll', () => {
  let s = viewReducer(initialViewState(), { type: 'isolatePart', id: femur.id });
  expect(isPartVisible(s, { id: 'BP3D:FJ3', system: 'skeletal' })).toBe(false);
  s = viewReducer(s, { type: 'showAll' });
  expect(isPartVisible(s, { id: 'BP3D:FJ3', system: 'skeletal' })).toBe(true);
});
test('explode is clamped to 0..1', () => {
  expect(viewReducer(initialViewState(), { type: 'setExplode', amount: 3 }).explode).toBe(1);
});
