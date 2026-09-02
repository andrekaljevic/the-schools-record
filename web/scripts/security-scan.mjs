// Checks the built site against the Content-Security-Policy in public/_headers:
// no inline executable script, no event-handler attributes, no javascript: URLs,
// and no script, stylesheet, font, image or fetch target on another origin.
import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join, resolve } from 'node:path';

const root = resolve(import.meta.dirname, '..', 'dist');
const files = [];
(function walk(dir) { for (const name of readdirSync(dir)) { const path = join(dir, name); if (statSync(path).isDirectory()) walk(path); else if (/\.(html|js|css)$/.test(name)) files.push(path); } })(root);

const findings = [];
for (const file of files) {
  const text = readFileSync(file, 'utf8');
  const rel = file.replace(root, 'dist');
  if (file.endsWith('.html')) {
    // The site's own absolute origin (canonical, Open Graph, sitemap) is not a third party.
    const own = /<link rel="canonical" href="(https?:\/\/[^/"]+)/.exec(text)?.[1] ?? '';
    const external = (url) => /^(https?:)?\/\//.test(url) && !(own && url.startsWith(own));
    for (const match of text.matchAll(/<script\b([^>]*)>/g)) {
      const attrs = match[1];
      const type = /type="([^"]+)"/.exec(attrs)?.[1] ?? '';
      if (!/\bsrc=/.test(attrs) && !['application/ld+json', 'application/json'].includes(type)) findings.push(`${rel}: inline executable script (${attrs.trim().slice(0, 60)})`);
      const src = /src="([^"]+)"/.exec(attrs)?.[1];
      if (src && external(src)) findings.push(`${rel}: external script ${src}`);
    }
    for (const match of text.matchAll(/<link\b([^>]*)>/g)) {
      const rel2 = /rel="([^"]+)"/.exec(match[1])?.[1] ?? '';
      const href = /href="([^"]+)"/.exec(match[1])?.[1] ?? '';
      if (/stylesheet|preload|modulepreload|prefetch|icon|manifest|apple-touch-icon/.test(rel2) && external(href)) findings.push(`${rel}: external ${rel2} ${href.slice(0, 80)}`);
    }
    for (const match of text.matchAll(/<(img|source|iframe|object|embed|video|audio)\b[^>]*\b(?:src|srcset)="([^"]+)"/g)) if (external(match[2])) findings.push(`${rel}: external ${match[1]} ${match[2].slice(0, 80)}`);
    if (/\son[a-z]+="/i.test(text)) findings.push(`${rel}: inline event handler attribute`);
    if (/href="javascript:/i.test(text)) findings.push(`${rel}: javascript: URL`);
    if (/<iframe\b/i.test(text)) findings.push(`${rel}: iframe`);
    if (/<meta\s+http-equiv="refresh"/i.test(text)) findings.push(`${rel}: meta refresh`);
  } else if (file.endsWith('.css')) {
    for (const match of text.matchAll(/url\(\s*["']?((?:https?:)?\/\/[^)"']+)/g)) findings.push(`${rel}: external stylesheet resource ${match[1].slice(0, 80)}`);
    if (/@import\s+url\(\s*["']?(?:https?:)?\/\//.test(text)) findings.push(`${rel}: external @import`);
  } else {
    for (const match of text.matchAll(/["'`](https?:\/\/[^"'`\s]+)/g)) {
      if (!/^https:\/\/schema\.org/.test(match[1])) findings.push(`${rel}: script references ${match[1].slice(0, 80)}`);
    }
    if (/document\.cookie|localStorage|sessionStorage|indexedDB/.test(text)) findings.push(`${rel}: browser storage or cookie access`);
  }
}
if (findings.length > 0) {
  console.error(`security scan FAILED: ${findings.length} finding(s)`);
  for (const finding of findings.slice(0, 20)) console.error('  ' + finding);
  process.exit(1);
}
console.log(`security scan passed: ${files.length} files; scripts are same-origin and external, no inline handlers, no third-party resources, no cookies or storage`);
