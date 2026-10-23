/** Shared checks for the packaged anatomy models in public/models/<body>/. */

/** Layers shown when a body first loads: skin, bones, heart, and the organ systems. */
export const INITIAL_SYSTEMS = [
  'integumentary', 'skeletal', 'cardiac', 'digestive', 'respiratory',
  'urinary', 'reproductive', 'endocrine', 'lymphatic',
];

export const INITIAL_BUDGET_BYTES = 40 * 1024 * 1024;

export function budgetReport(manifest) {
  const bySystem = {};
  let initialBytes = 0;
  let totalBytes = 0;
  for (const system of manifest.systems) {
    bySystem[system.id] = system.bytes;
    totalBytes += system.bytes;
    if (INITIAL_SYSTEMS.includes(system.id)) initialBytes += system.bytes;
  }
  return { initialBytes, totalBytes, overBudget: initialBytes > INITIAL_BUDGET_BYTES, bySystem };
}

export function findManifestProblems(manifest, nodeNamesBySystem) {
  const problems = [];
  const seen = new Set();
  const partIdsBySystem = new Map();
  for (const part of manifest.parts) {
    if (seen.has(part.id)) problems.push(`id ganda: ${part.id}`);
    seen.add(part.id);
    if (part.file !== `${part.system}.glb`) problems.push(`file tidak cocok dengan sistem: ${part.id} (${part.file})`);
    if (part.triangles === 0) problems.push(`bagian tanpa segitiga: ${part.id}`);
    if (!(nodeNamesBySystem[part.system] ?? []).includes(part.id)) {
      problems.push(`bagian tanpa node di ${part.system}.glb: ${part.id}`);
    }
    if (!partIdsBySystem.has(part.system)) partIdsBySystem.set(part.system, new Set());
    partIdsBySystem.get(part.system).add(part.id);
  }
  for (const [system, nodes] of Object.entries(nodeNamesBySystem)) {
    for (const node of nodes) {
      if (!partIdsBySystem.get(system)?.has(node)) problems.push(`node tanpa bagian di ${system}.glb: ${node}`);
    }
  }
  return problems;
}
