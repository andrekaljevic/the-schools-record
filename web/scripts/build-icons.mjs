// Generates the raster icons and the social card from the SVG sources with sharp.
// Run once (npm run icons); the outputs are committed so a build needs no image tooling.
import sharp from 'sharp';
import { readFileSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';

const root = resolve(import.meta.dirname, '..');
const out = (name) => resolve(root, 'public', name);
const favicon = readFileSync(out('favicon.svg'));

for (const [name, size] of [['icon-192.png', 192], ['icon-512.png', 512], ['apple-touch-icon.png', 180], ['favicon-32.png', 32]]) {
  await sharp(favicon, { density: 384 }).resize(size, size).png().toFile(out(name));
}

// favicon.ico: an ICO container holding the 32px PNG (supported by every current browser).
const png = readFileSync(out('favicon-32.png'));
const header = Buffer.alloc(6 + 16);
header.writeUInt16LE(0, 0); header.writeUInt16LE(1, 2); header.writeUInt16LE(1, 4);
header.writeUInt8(32, 6); header.writeUInt8(32, 7); header.writeUInt8(0, 8); header.writeUInt8(0, 9);
header.writeUInt16LE(1, 10); header.writeUInt16LE(32, 12); header.writeUInt32LE(png.length, 14); header.writeUInt32LE(22, 18);
writeFileSync(out('favicon.ico'), Buffer.concat([header, png]));

const card = `<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630">
  <rect width="1200" height="630" fill="#f3f0e8"/>
  <rect x="0" y="0" width="1200" height="8" fill="#172322"/>
  <rect x="80" y="96" width="52" height="52" fill="#172322"/>
  <text x="106" y="132" text-anchor="middle" font-family="Georgia, serif" font-size="24" fill="#f3f0e8">SR</text>
  <text x="150" y="132" font-family="Georgia, serif" font-size="30" fill="#172322">The Schools Record</text>
  <text x="80" y="280" font-family="Georgia, serif" font-size="68" fill="#172322">Independent school results,</text>
  <text x="80" y="360" font-family="Georgia, serif" font-size="68" fill="#172322">year by year.</text>
  <text x="80" y="450" font-family="Helvetica, Arial, sans-serif" font-size="24" fill="#41514e">A source-led public record for seven leading UK schools.</text>
  <text x="80" y="486" font-family="Helvetica, Arial, sans-serif" font-size="24" fill="#41514e">Definitions before comparisons. Never a ranking.</text>
  <line x1="80" y1="540" x2="1120" y2="540" stroke="#172322" stroke-width="2"/>
  <text x="80" y="580" font-family="Helvetica, Arial, sans-serif" font-size="20" letter-spacing="3" fill="#9a6d2e">FROZEN EDITION · 2,277 RECORDS · 1836–2026</text>
</svg>`;
await sharp(Buffer.from(card)).png().toFile(out('social-card.png'));
console.log('icons written');
