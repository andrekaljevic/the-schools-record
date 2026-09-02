// Scans every file in dist/ for private source locations and identifiers.
// Mirrors tests/test_privacy.py so the built site is held to the same rule as the Python layer.
import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join, resolve } from 'node:path';

const root = resolve(import.meta.dirname, '..', 'dist');
const PATTERNS = [
  [/drive\.google\.com/i, 'Google Drive location'],
  [/docs\.google\.com/i, 'Google Docs location'],
  [/private-source-[0-9a-f]{16}/, 'private source identifier'],
  [/\/d\/[A-Za-z0-9_-]{25,}/, 'Drive-style document id'],
  [/[?&]id=[A-Za-z0-9_-]{25,}/, 'Drive-style id parameter'],
  [/\/home\/[a-z0-9_-]+\//, 'local filesystem path'],
  [/sourceMappingURL/, 'source map reference'],
];
const TEXT = /\.(html|js|css|json|xml|txt|csv|svg|webmanifest)$/;

function walk(dir, out = []) {
  for (const name of readdirSync(dir)) {
    const path = join(dir, name);
    if (statSync(path).isDirectory()) walk(path, out);
    else if (TEXT.test(name)) out.push(path);
  }
  return out;
}

const files = walk(root);
const findings = [];
for (const file of files) {
  const text = readFileSync(file, 'utf8');
  for (const [pattern, label] of PATTERNS) {
    const match = pattern.exec(text);
    if (match) findings.push(`${file.replace(root, 'dist')}: ${label} (${match[0].slice(0, 40)})`);
  }
}
if (findings.length > 0) {
  console.error(`privacy scan FAILED: ${findings.length} finding(s)`);
  for (const finding of findings.slice(0, 20)) console.error('  ' + finding);
  process.exit(1);
}
console.log(`privacy scan passed: ${files.length} files in dist/ carry no private location, identifier, local path or source map`);
