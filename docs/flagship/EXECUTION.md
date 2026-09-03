# The Schools Record — flagship frontend: execution record

One persistent document. Updated at each milestone. Everything stated here is
backed by a command result recorded in the evidence pack (`docs/flagship/evidence/`).

## 1. Baseline

| Item | Value |
| --- | --- |
| Verified anchor | `d6197a984442583ab93fe440556ecedee6178060` (branch `claude/schools-record-charts-bxekih`) |
| Implementation branch | `claude/tsr-flagship-10x`, created from the anchor |
| Later commit on the chart branch | `d37a9cb` (revision v2, post-remark values) — **not** in this lineage; it changes the dataset SHA and stays on its own branch for separate review |
| `data/dataset.json` SHA-256 | `245f2d8176f8fca0d53f41689f096734dd13e9023af9a67931314334251b9f6f` |
| Snapshot | `production-818c7c2-data-frozen-v1`, baseline commit `818c7c296fed184480d5de05cbd34ad3ba481a46`, 286 source-location redactions |
| Record counts | figures 1,274 · granular 83 · Oxford and Cambridge 571 · US and overseas 349 · total 2,277 · schools 7 |
| Parity oracle | the Streamlit application at the anchor, run locally on port 8502 |
| Environment limits | Node 22.22, npm registry reachable; Chromium 1194 is the only browser that can be installed (Firefox/WebKit downloads are blocked); documentation sites are unreachable, so framework APIs are verified from the installed package typings; no Vercel/Netlify/Cloudflare credentials |

## 2. Architectural decision

**Astro 7 (static output) with vanilla-TypeScript islands.** Chosen over Next.js App Router after a spike against the requirements:

* Every route is static HTML at build time, including the 2,277 record permalinks; editorial and record pages ship no client JavaScript.
* Interactivity (comparison instrument, evidence search and filters, ledger column controls, print) is confined to small `<script type="module">` islands with no framework runtime; total client JavaScript is measured per route and budgeted.
* The tested Python modules stay canonical. `tools/build_public_projection.py` writes a deterministic, whitelisted public projection to `web/src/generated/` (outside `data/`), including chart SVGs already rendered by the Python chart code, so chart, table and download values share one source of truth.
* Where a chart must be interactive (comparison), the drawing geometry is ported to TypeScript and proven against the Python renderer by an automated parity test.
* Forms are progressively enhanced HTML forms posting to a platform-neutral handler (`web/functions/`, Cloudflare Pages Functions runtime; the handler logic is a pure `Request → Response` module tested in isolation) with honeypot, rate limiting and honest receipts.
* Legacy `?p=/route` links are redirected by a tiny inline script on the 404 page plus platform redirect rules.

Next.js was rejected for this product because its static export cannot host the form handler without a server, its runtime is heavier for pages that need no JavaScript, and its routing conventions add nothing the content needs.

## 3. Design thesis

*An evidence ledger, typeset like a serious quarterly and instrumented like a research desk.*

* **Type carries identity.** Newsreader (variable, optical sizes) for display and reading text; Inter (variable) for labels and interface; IBM Plex Mono for every figure that must align. All three are SIL Open Font License, self-hosted and subset. Tabular numerals wherever numbers sit in columns.
* **Rules, not boxes.** Hierarchy is drawn with hairlines, margins and marginal annotation rather than cards and shadows. Brass appears only for the evidence-status and annotation layer; teal only for action and current state.
* **Paper and ink.** Warm paper, near-black ink, a single cool accent. No gradients, no glass, no gold.
* **The data is the picture.** Small multiples on shared rulers, gaps preserved, breaks marked, exact values one click away. The same SVG grammar on the index, the school record, the ledgers, the comparison and the dossier.
* **Distinct page families.** Home states purpose and proof; the index is a comparative collection; the school page is a portrait of a record; ledgers are a reading environment; comparison is an instrument; the evidence centre is a research desk; the dossier is a publication.
* **Motion explains.** Only transform and opacity, only on state change and continuity, fully removed under `prefers-reduced-motion`.

## 4. Acceptance matrix

| Gate | Status | Evidence |
| --- | --- | --- |
| A. Data: SHA, snapshot, counts, existing tests, projection determinism, chart/table/download parity | passed | `evidence/test-results.md` (Data contract; Python 188 tests; chart parity 2,730 cases) |
| B. Feature parity: every route, dataset, row, record, source path, download | passed | `evidence/route-matrix.md`; `tests/test_projection.py` (every row has an anchor and a record; every record has one address); 62 ledger CSVs, 11 comparison CSVs |
| C. Visual regression at nine viewports | passed | `web/tests/e2e/responsive.spec.ts` (overflow and legibility at 9 widths × 12 routes); `evidence/before/`, `evidence/after/` |
| D. Cross-browser | Chromium only | Firefox and WebKit binaries cannot be downloaded in this environment (see §7); no browser-specific API is used beyond `:has()` for the column toggle, which has a print fallback |
| E. Accessibility: axe, keyboard, zoom, reduced motion | passed | axe 0 violations on 25 routes; Lighthouse accessibility 100; keyboard, 200 % zoom and reduced-motion tests |
| F. Performance: production build Lighthouse, budgets | passed | `evidence/lighthouse/README.md` (mobile 95–99, desktop 100); `npm run budgets` |
| G. SEO: canonical paths, metadata, sitemap, structured data | passed | Lighthouse SEO 100; `journeys.spec.ts` (canonical, Open Graph, JSON-LD Dataset/BreadcrumbList/WebSite, sitemap, robots) |
| H. Security and privacy: audit, bundle scan, headers, forms | passed | `npm run privacy`, `npm run security`, `web/public/_headers`, `functions/lib/handler.ts` tests |
| I. Forms and failure states | passed | `handler.test.ts` (8 cases) and the browser journey: no receiver → "not recorded" with a copy to keep |
| J. Print and export | passed | print stylesheet test; ledger and comparison CSV endpoints; sample PDF retained |
| K. User journeys | passed | `journeys.spec.ts` (parent, researcher, journalist, professional, legacy-link visitor) |

## 5. Progress log

* **Stage 1 — baseline.** Branch created from the anchor; dataset SHA, snapshot and counts verified; the full Python suite passed at the anchor (178 tests); the Streamlit oracle was run locally and screenshotted on 15 routes at nine viewports (135 images; a curated set is in `evidence/before/`). Route-and-capability inventory: `tests/test_parity.py` FEATURE_MATRIX (25 capabilities) plus the brief's route list.
* **Stage 2 — benchmarking (transferable principles only).** Adopted: one typographic system with optical sizing and tabular figures (financial and statistical publishing); small multiples on shared rulers with gaps preserved (statistical graphics practice); progressive enhancement with plain HTML forms and no framework runtime (public-sector service patterns); permanent addresses for every record and an explicit provenance panel per figure (data-journalism and archival practice); print as a first-class output (dossiers). Rejected: card-and-shadow dashboards, gradients, hero imagery for its own sake, client-side routing.
* **Stage 3 — vertical slice.** `tsr/projection.py` + `tools/build_public_projection.py` (19 documents, 9.2 MB, deterministic, private-pattern scanned); Astro 7 scaffold; design system (`web/src/styles/global.css`); home, index, school record, ledgers, comparison, record permalink, correction form, 404; reviewed at 390 and 1440 px; fixes applied (chart label clipping, ledger page weight 1.8 MB → 0.8 MB by compacting per-row evidence panels, latin-only fonts).
* **Stage 4 — full product.** Every route in the brief built statically: 2,538 pages including 2,277 record permalinks, per-corpus paginated listings, series pages for the index, per-school corrections, CSV endpoints for every ledger and comparison metric, sitemap, robots, security headers, icons and social card. Islands: comparison instrument (TypeScript port of the Python chart, byte-identical on 2,730 fixture cases), evidence search, school-index filter, corpus filters, forms, legacy-link redirect. Forms post to a platform-neutral handler with honeypot, timing check, rate limit and honest receipts.
* **Stage 5 — audits.** Production build audited: privacy scan and security scan of every built file, budgets, axe on 25 routes, Lighthouse mobile and desktop, `npm audit`. Findings fixed before the jury (contrast tokens, landmark names, heading order, overflow at 320 px, `.invalid` origin handling).
* **Stage 6 — independent jury and two remediation loops.** Four fresh-context reviewers (design director; product and content; data and methodology; engineering, accessibility and security) scored the served build and listed defects; scores and every finding are in `evidence/jury.md`. Loop 1 fixed the high and major findings (unique row anchors with exact record links; gap-aware comparison panels on the shared grammar with a mobile geometry; origin-aware metadata; ledger legibility, status glossary links, stated gaps, correction ↔ row links; keyboard and focus fixes; handler hardening; publisher and contact). Loop 2 re-ran every gate: Python, unit, type check, build, scans, budgets, 53 browser tests, Lighthouse.
* **Stage 7 — delivery.** Cutover, redirect, monitoring and rollback plan in `CUTOVER.md`; evidence pack complete; CI workflow builds with a preview origin and uploads the site as an artifact; no production deployment and no merge to `main`.

## 6. Verified test results

Recorded in `evidence/test-results.md` with the commands that produced them. Headline: Python 188/188; unit 28/28;
type check 0 errors; build 2,538 pages; end-to-end 49/49 including 25 axe audits with 0 violations; Lighthouse
mobile 95–99 / desktop 100 with accessibility, best-practice and SEO at 100; privacy and security scans clean;
all budgets met; `data/dataset.json` SHA-256 unchanged.

## 7. Remaining genuine blockers and open items

* **Preview deployment.** No hosting credential (Vercel, Netlify, Cloudflare) exists in this environment, so no external
  preview URL has been created. The production build is fully reproducible locally (`npm run projection && npm run build
  && npm run preview` in `web/`) and the CI workflow uploads `web/dist` as an artifact on every push to the branch.
* **Firefox and WebKit.** Browser downloads are blocked here; only Chromium 1194 could be installed. The site uses no
  Chromium-specific API, but cross-browser evidence remains to be captured on a machine that can install them.
* **Frozen wording the jury questioned.** Several strings the reviewers found jargon-laden or unsupported are frozen
  dataset text (metric notes such as "excluded by default" and "retained in the Yearbook"; the corrections entry
  C15; the "Pre-U honest" series name; the method definition that says a source "reportedly" rounds). The site now
  explains the first two in place and leaves the rest verbatim: changing them is a versioned editorial decision.
* **Withheld source titles.** The Oxford, Cambridge, US and subject corpora cite references whose titles the reviewed
  edition withheld and for which no public link was approved. The record pages say so and give the route to ask;
  approving further public links is an editorial step outside this brief.
* **Largest ledger page.** St Paul's university outcomes (20 ledgers, about 1,000 rows) is under 900 KB of HTML and
  about 53 KB compressed. Splitting it into family sub-pages would cut the DOM further; it is proposed, not done.
* **Form receiver.** The handler forwards to `REVIEW_WEBHOOK_URL` when configured; until a durable receiver is
  provisioned, every submission is truthfully reported as not recorded. This is by design, not a defect.
* **Production origin.** `SITE_URL` must be set at build time for canonical URLs, Open Graph and the sitemap to carry
  the real domain; the preview build uses a placeholder `.invalid` origin so nothing points at a private host.
