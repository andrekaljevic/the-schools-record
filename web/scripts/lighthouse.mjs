// Lighthouse audits of the production build served locally, written to docs/flagship/evidence/lighthouse/.
// Usage: node scripts/lighthouse.mjs [baseUrl]   (CHROMIUM_PATH selects the browser binary)
import { mkdirSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';
import lighthouse from 'lighthouse';
import * as chromeLauncher from 'chrome-launcher';

const base = process.argv[2] ?? 'http://127.0.0.1:4321';
const out = resolve(import.meta.dirname, '..', '..', 'docs', 'flagship', 'evidence', 'lighthouse');
mkdirSync(out, { recursive: true });
const routes = ['/', '/schools/', '/schools/westminster/', '/schools/winchester/exam-results/', '/compare/', '/evidence/', '/evidence/records/ox/oxford-apply-centre-2006-10092/', '/sample-dossier/'];

const chrome = await chromeLauncher.launch({ chromePath: process.env.CHROMIUM_PATH, chromeFlags: ['--headless=new', '--no-sandbox', '--disable-gpu'] });
const rows = [];
try {
  for (const formFactor of ['mobile', 'desktop']) {
    for (const route of routes) {
      const result = await lighthouse(`${base}${route}`, { port: chrome.port, output: 'json', logLevel: 'error', onlyCategories: ['performance', 'accessibility', 'best-practices', 'seo'], formFactor, screenEmulation: formFactor === 'desktop' ? { mobile: false, width: 1350, height: 940, deviceScaleFactor: 1, disabled: false } : undefined, throttlingMethod: 'simulate', throttling: formFactor === 'desktop' ? { rttMs: 40, throughputKbps: 10240, cpuSlowdownMultiplier: 1, requestLatencyMs: 0, downloadThroughputKbps: 0, uploadThroughputKbps: 0 } : undefined });
      const lhr = result.lhr;
      const score = (key) => Math.round((lhr.categories[key]?.score ?? 0) * 100);
      const metric = (id) => lhr.audits[id]?.numericValue ?? null;
      const row = { formFactor, route, performance: score('performance'), accessibility: score('accessibility'), bestPractices: score('best-practices'), seo: score('seo'), lcpMs: Math.round(metric('largest-contentful-paint') ?? 0), cls: Number((metric('cumulative-layout-shift') ?? 0).toFixed(3)), tbtMs: Math.round(metric('total-blocking-time') ?? 0), fcpMs: Math.round(metric('first-contentful-paint') ?? 0), totalBytes: Math.round(metric('total-byte-weight') ?? 0) };
      rows.push(row);
      writeFileSync(resolve(out, `${formFactor}${route.replace(/\//g, '_') || '_'}.json`), JSON.stringify({ requestedUrl: lhr.requestedUrl, fetchTime: lhr.fetchTime, lighthouseVersion: lhr.lighthouseVersion, categories: Object.fromEntries(Object.entries(lhr.categories).map(([k, v]) => [k, v.score])), audits: Object.fromEntries(['largest-contentful-paint', 'cumulative-layout-shift', 'total-blocking-time', 'first-contentful-paint', 'total-byte-weight', 'speed-index'].map((id) => [id, { score: lhr.audits[id]?.score, numericValue: lhr.audits[id]?.numericValue, displayValue: lhr.audits[id]?.displayValue }])) }, null, 2));
      console.log(`${formFactor.padEnd(7)} ${route.padEnd(58)} perf ${row.performance} a11y ${row.accessibility} bp ${row.bestPractices} seo ${row.seo}  LCP ${row.lcpMs}ms CLS ${row.cls} TBT ${row.tbtMs}ms`);
    }
  }
} finally {
  await chrome.kill();
}
const table = ['# Lighthouse', '', `Lighthouse ${rows.length ? 'run' : ''} against the production build served locally (simulated throttling; a shared build container, so absolute timings are indicative and scores are the durable signal).`, '', '| Form factor | Route | Performance | Accessibility | Best practices | SEO | LCP | CLS | TBT | Bytes |', '| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |', ...rows.map((r) => `| ${r.formFactor} | \`${r.route}\` | ${r.performance} | ${r.accessibility} | ${r.bestPractices} | ${r.seo} | ${r.lcpMs} ms | ${r.cls} | ${r.tbtMs} ms | ${Math.round(r.totalBytes / 1024)} KB |`), ''];
writeFileSync(resolve(out, 'README.md'), table.join('\n'));
