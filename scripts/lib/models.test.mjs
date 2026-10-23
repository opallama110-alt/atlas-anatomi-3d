import { budgetReport, findManifestProblems, INITIAL_BUDGET_BYTES } from './models.mjs';

const manifest = {
  parts: [
    { id: 'BP3D:FJ1', system: 'skeletal', file: 'skeletal.glb', triangles: 10 },
    { id: 'BP3D:FJ2', system: 'muscular', file: 'muscular.glb', triangles: 0 },
  ],
  systems: [
    { id: 'skeletal', file: 'skeletal.glb', bytes: 30 * 1024 * 1024 },
    { id: 'muscular', file: 'muscular.glb', bytes: 20 * 1024 * 1024 },
  ],
};

test('budget counts only initial systems', () => {
  const r = budgetReport(manifest);
  expect(r.initialBytes).toBe(30 * 1024 * 1024);
  expect(r.totalBytes).toBe(50 * 1024 * 1024);
  expect(r.overBudget).toBe(30 * 1024 * 1024 > INITIAL_BUDGET_BYTES);
});

test('finds missing nodes, extra nodes and empty parts', () => {
  const problems = findManifestProblems(manifest, { skeletal: ['BP3D:FJ1', 'BP3D:FJ9'], muscular: [] });
  expect(problems).toEqual(expect.arrayContaining([
    expect.stringContaining('BP3D:FJ2'),
    expect.stringContaining('BP3D:FJ9'),
  ]));
});
