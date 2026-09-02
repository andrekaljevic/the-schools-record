// Performance budgets for the production build (uncompressed bytes on disk).
import { readdirSync, readFileSync, statSync } from 'node:fs';
import { gzipSync } from 'node:zlib';
import { join, resolve } from 'node:path';

const dist = resolve(import.meta.dirname, '..', 'dist');
const BUDGETS = {
  cssTotal: 60_000,
  jsPerRoute: 25_000,
  fontsTotal: 220_000,
  htmlEditorial: 120_000,
  htmlLedgerLargest: 900_000,
  htmlRecordPermalink: 40_000,
};
const ROUTES = {
  editorial: ['index.html', 'schools/index.html', 'schools/westminster/index.html', 'compare/index.html', 'methodology/index.html', 'evidence/index.html', 'corrections/index.html', 'professional/index.html', 'sample-dossier/index.html'],
  ledgers: ['schools/st-pauls/university-destinations/index.html', 'schools/winchester/exam-results/index.html', 'schools/kcs/exam-results/index.html'],
  records: ['evidence/records/ox/oxford-apply-centre-2006-10092/index.html', 'evidence/records/fig/winchester_gcse/3/index.html'],
};
const assets = readdirSync(join(dist, '_astro')).map((name) => ({ name, size: statSync(join(dist, '_astro', name)).size }));
const sum = (pattern) => assets.filter((asset) => pattern.test(asset.name)).reduce((total, asset) => total + asset.size, 0);
const size = (file) => statSync(join(dist, file)).size;
const gz = (file) => gzipSync(readFileSync(join(dist, file))).length;

const results = [];
const check = (label, actual, budget) => { results.push({ label, actual, budget, ok: actual <= budget }); };
check('CSS total', sum(/\.css$/), BUDGETS.cssTotal);
check('Fonts total', sum(/\.woff2$/), BUDGETS.fontsTotal);
for (const file of ROUTES.editorial) {
  const html = readFileSync(join(dist, file), 'utf8');
  const scripts = [...html.matchAll(/src="\/_astro\/([^"]+\.js)"/g)].map((match) => match[1]);
  const js = scripts.reduce((total, name) => total + (assets.find((asset) => asset.name === name)?.size ?? 0), 0);
  check(`JS on /${file.replace('index.html', '')}`, js, BUDGETS.jsPerRoute);
  check(`HTML /${file.replace('index.html', '')}`, size(file), BUDGETS.htmlEditorial);
}
for (const file of ROUTES.ledgers) check(`HTML ledger /${file.replace('index.html', '')}`, size(file), BUDGETS.htmlLedgerLargest);
for (const file of ROUTES.records) check(`HTML record /${file.replace('index.html', '')}`, size(file), BUDGETS.htmlRecordPermalink);

let failed = 0;
for (const result of results) {
  if (!result.ok) failed += 1;
  console.log(`${result.ok ? 'ok  ' : 'FAIL'} ${result.label.padEnd(64)} ${String(result.actual).padStart(9)} / ${result.budget}`);
}
console.log(`largest ledger page gzipped: ${gz('schools/st-pauls/university-destinations/index.html')} bytes`);
if (failed > 0) { console.error(`${failed} budget(s) exceeded`); process.exit(1); }
console.log('all budgets met');
