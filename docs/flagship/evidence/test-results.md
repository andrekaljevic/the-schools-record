# Verified test results

All results below were produced on 2 September 2026 from branch `claude/tsr-flagship-10x`, working tree at the
commit that carries this file. Commands are given so they can be re-run.

## Data contract

| Check | Result |
| --- | --- |
| `sha256sum data/dataset.json` before any work | `245f2d8176f8fca0d53f41689f096734dd13e9023af9a67931314334251b9f6f` |
| `sha256sum data/dataset.json` after the build and every test run | `245f2d8176f8fca0d53f41689f096734dd13e9023af9a67931314334251b9f6f` |
| `git status -- data/` | clean (no file under `data/` modified) |
| Snapshot / baseline commit / redactions | `production-818c7c2-data-frozen-v1` / `818c7c296fed184480d5de05cbd34ad3ba481a46` / 286 |
| Record counts (projection manifest = application) | figures 1,274 · granular 83 · Oxford and Cambridge 571 · US and overseas 349 · total 2,277 · schools 7 |
| Projection determinism | two consecutive builds byte-identical (`tests/test_projection.py`, `tools/build_public_projection.py --check`) |

## Python data layer — `python3 -m unittest discover -s tests`

```
Ran 188 tests in 181.339s
OK
```

178 tests inherited from the anchor commit (unchanged) plus 10 new projection-contract tests. No existing test was
weakened, skipped, deleted or rewritten.

## Frontend unit tests — `cd web && npm run test:unit`

```
Test Files  4 passed (4)
     Tests  28 passed (28)
```

Includes the chart parity test: the TypeScript comparison chart reproduces the canonical Python renderer byte for
byte on 2,730 fixture cases (every metric × every ordered school pair × six year windows).

## Type check — `cd web && npm run check`

```
Result (86 files): 0 errors, 0 warnings, 1 hint
```

## Production build — `cd web && npm run build`

```
2538 page(s) built in 8.70s
```

## End-to-end, journeys, accessibility and responsive — `cd web && npm run test:e2e`

```
49 passed (1.5m)
```

* axe-core (WCAG 2.2 A/AA + best practice) on 25 routes: 0 violations.
* Keyboard: skip link, mobile menu, focus order; reduced motion; 200 % zoom without horizontal scroll.
* Journeys: legacy `?p=` redirects; ledger row → evidence panel → permanent record; column toggle and CSV download;
  comparison state in the URL with redraw; evidence search, filters and claim tracing; school index filter and
  series switch; Oxbridge filters; correction form validation and honest failure receipt; metadata, JSON-LD,
  sitemap and robots; print styles; no third-party requests and no cookies.
* Responsive: no horizontal overflow and no text under 11 px on 12 routes at 320, 375, 390, 430, 768, 1024,
  1280, 1440 and 1920 px wide.

## Accessibility

axe: 0 violations on every audited route (above). Lighthouse accessibility: 100 on every audited route (below).
Colour contrast was re-tokenised after the first run (brass text darkened to #7a5520 on light grounds and lightened
to #d7b46e on ink grounds; muted text darkened to #5c6662) so every text colour meets 4.5:1.

## Performance — `cd web && node scripts/lighthouse.mjs`

See `lighthouse/README.md` for the full table. Summary (production build served locally, simulated throttling):

| | Performance | Accessibility | Best practices | SEO | CLS | TBT |
| --- | --- | --- | --- | --- | --- | --- |
| Mobile (8 routes) | 95–99 | 100 | 100 | 100 | 0 | 0 ms |
| Desktop (8 routes) | 100 | 100 | 100 | 100 | 0 | 0 ms |

## Budgets — `cd web && npm run budgets`

All budgets met: CSS 48.6 KB total; fonts 200 KB total (five latin-subset woff2 files); client JavaScript per
route ≤ 5.3 KB (0 on record and editorial pages); editorial pages ≤ 99 KB HTML; largest ledger page
(St Paul's university outcomes, 20 ledgers, ~1,000 rows) 831 KB HTML, 46 KB gzipped; record permalinks ≤ 14 KB.

## Security and privacy

* `npm run privacy` — 2,629 built files: no Google Drive or Docs location, no private source identifier, no
  Drive-style id, no local filesystem path, no source-map reference.
* `npm run security` — 2,550 files: every script is same-origin and external (CSP `script-src 'self'`), no inline
  event handlers, no `javascript:` URLs, no iframes, no third-party stylesheet, font, image or fetch target, no
  cookie or browser-storage access.
* `npm audit --audit-level=high` — see `dependencies.md`.
* Headers (`web/public/_headers`): CSP, HSTS, X-Content-Type-Options, X-Frame-Options, Referrer-Policy,
  Permissions-Policy, COOP, CORP, cache control. `style-src` allows inline styles only because the canonical
  Python chart SVGs carry inline font sizes; scripts are never inline.
* Forms: honeypot, minimum fill time, length limits, rate limit, HTTPS-only forwarding; the receipt states
  "not recorded" unless a configured endpoint confirmed receipt (unit-tested in `web/tests/unit/handler.test.ts`).
