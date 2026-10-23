/**
 * Check a packaged body: every manifest part has a mesh node, nothing is empty,
 * and the initial layers fit the download budget.
 * Usage: node scripts/validate-models.mjs <body>
 */
import fs from 'node:fs';
import path from 'node:path';
import { NodeIO } from '@gltf-transform/core';
import { ALL_EXTENSIONS } from '@gltf-transform/extensions';
import { MeshoptDecoder } from 'meshoptimizer';
import { budgetReport, findManifestProblems, INITIAL_BUDGET_BYTES } from './lib/models.mjs';

const body = process.argv[2];
if (!body) {
  console.error('usage: node scripts/validate-models.mjs <body>');
  process.exit(2);
}
const root = path.resolve(path.dirname(new URL(import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, '$1')), '..');
const dir = path.join(root, 'public', 'models', body);

await MeshoptDecoder.ready;
const io = new NodeIO()
  .registerExtensions(ALL_EXTENSIONS)
  .registerDependencies({ 'meshopt.decoder': MeshoptDecoder });

const manifest = JSON.parse(fs.readFileSync(path.join(dir, 'manifest.json'), 'utf8'));
const nodeNamesBySystem = {};
for (const system of manifest.systems) {
  const doc = await io.read(path.join(dir, system.file));
  nodeNamesBySystem[system.id] = doc.getRoot().listNodes().filter((n) => n.getMesh()).map((n) => n.getName());
}

const problems = findManifestProblems(manifest, nodeNamesBySystem);
const report = budgetReport(manifest);
const mb = (bytes) => (bytes / 1048576).toFixed(1);
for (const [id, bytes] of Object.entries(report.bySystem)) console.log(`${id.padEnd(14)} ${mb(bytes).padStart(6)} MB`);
console.log(`lapisan awal: ${mb(report.initialBytes)} MB (batas ${mb(INITIAL_BUDGET_BYTES)} MB)`);
console.log(`total: ${mb(report.totalBytes)} MB, ${manifest.parts.length} bagian`);
for (const problem of problems.slice(0, 50)) console.error(`MASALAH: ${problem}`);
if (problems.length > 50) console.error(`… dan ${problems.length - 50} masalah lain`);
if (problems.length || report.overBudget) {
  console.error(report.overBudget ? 'GAGAL: lapisan awal melebihi batas' : `GAGAL: ${problems.length} masalah`);
  process.exit(1);
}
console.log('OK');
