/**
 * Simplify and compress the raw per-system GLBs from the Python pipeline.
 * Usage: node scripts/optimize-glb.mjs <body>
 *
 * Reads data/work/<body>/<system>.glb and manifest.draft.json, writes
 * public/models/<body>/<system>.glb and manifest.json. Geometry is simplified
 * to a 0.2% relative error bound per mesh, quantized, and meshopt-compressed.
 */
import fs from 'node:fs';
import path from 'node:path';
import { NodeIO } from '@gltf-transform/core';
import { ALL_EXTENSIONS } from '@gltf-transform/extensions';
import { meshopt, quantize, simplify, weld } from '@gltf-transform/functions';
import { MeshoptEncoder, MeshoptSimplifier } from 'meshoptimizer';

const body = process.argv[2];
if (!body) {
  console.error('usage: node scripts/optimize-glb.mjs <body>');
  process.exit(2);
}
const root = path.resolve(path.dirname(new URL(import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, '$1')), '..');
const workDir = path.join(root, 'data', 'work', body);
const outDir = path.join(root, 'public', 'models', body);
fs.mkdirSync(outDir, { recursive: true });

await MeshoptSimplifier.ready;
await MeshoptEncoder.ready;
const io = new NodeIO()
  .registerExtensions(ALL_EXTENSIONS)
  .registerDependencies({ 'meshopt.encoder': MeshoptEncoder });

const triangleCount = (mesh) =>
  mesh.listPrimitives().reduce((sum, prim) => {
    const indices = prim.getIndices();
    return sum + (indices ? indices.getCount() : prim.getAttribute('POSITION').getCount()) / 3;
  }, 0);

const draft = JSON.parse(fs.readFileSync(path.join(workDir, 'manifest.draft.json'), 'utf8'));
const trianglesById = new Map();
const systems = [];
for (const file of fs.readdirSync(workDir).filter((f) => f.endsWith('.glb')).sort()) {
  const id = path.basename(file, '.glb');
  const doc = await io.read(path.join(workDir, file));
  await doc.transform(
    weld(),
    simplify({ simplifier: MeshoptSimplifier, ratio: 0, error: 0.002 }),
    quantize(),
    meshopt({ encoder: MeshoptEncoder, level: 'medium' }),
  );
  let triangles = 0;
  let parts = 0;
  for (const node of doc.getRoot().listNodes()) {
    const mesh = node.getMesh();
    if (!mesh) continue;
    const count = triangleCount(mesh);
    trianglesById.set(node.getName(), count);
    triangles += count;
    parts += 1;
  }
  const target = path.join(outDir, file);
  await io.write(target, doc);
  const bytes = fs.statSync(target).size;
  systems.push({ id, file, bytes, parts, triangles });
  console.log(`${id.padEnd(14)} ${String(parts).padStart(4)} bagian  ${String(triangles).padStart(9)} segitiga  ${(bytes / 1048576).toFixed(1).padStart(6)} MB`);
}

const parts = draft.parts.map((part) => ({ ...part, triangles: trianglesById.get(part.id) ?? 0 }));
const manifest = { version: 1, body, units: 'm', up: 'y', parts, systems };
fs.writeFileSync(path.join(outDir, 'manifest.json'), JSON.stringify(manifest));
console.log(`manifest: ${parts.length} bagian, ${systems.length} sistem`);
