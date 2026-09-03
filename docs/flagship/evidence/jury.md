# Independent jury

Four reviewers with fresh context assessed the served production build on 2–3 September 2026, each with a
different remit and no access to the author's notes. They were instructed to change nothing and to score from
1 to 10 with justification, then list defects most severe first. Their scores are recorded here as given, before
remediation; the remediation column records what was done in the loop that followed and what was not, with the
reason. A second, shorter loop confirmed the fixes with the automated gates (see `test-results.md`).

## Scores as given (before remediation)

| Reviewer | Dimension scores | Mean |
| --- | --- | --- |
| Design director | identity 9 · layout 7 · data presentation 7 · editorial 8 · IA 8 · interaction 7 · accessibility 8 · polish 8 · trust 8 · craft 8 | 7.8 |
| Product and content | arrival 8 · findability 7 · honesty 7 · tables and charts 6 · provenance 5 · navigation 8 · mobile 7 · forms 8 · editorial pages 7 · trust 7 | 7.0 |
| Data and methodology | completeness 7 · fidelity 9 · charts 7 · labelling 7 · provenance 5 · downloads 9 · honesty 7 · privacy 10 | 7.6 |
| Engineering, accessibility, security | code 7 · types and tests 7 · progressive enhancement 6 · keyboard and screen reader 6 · security 8 · privacy 9 · build and CI 7 · performance 7 · maintainability 7 · release readiness 6 | 7.0 |

## Findings and remediation

| # | Severity | Finding (reviewer) | Remediation |
| --- | --- | --- | --- |
| 1 | High | 614 ledger rows shared an anchor with another row and 607 rows linked to another row's record (data) | Fixed. Anchors are unique (`-r{index}` appended only where a period repeats); each row's record id is its own frozen index; guarded by `tests/test_projection.py` |
| 2 | Blocker | Canonical, Open Graph, structured data and robots pointed at a placeholder `.invalid` host (design, product, engineering) | Fixed. Absolute addresses are emitted only when `SITE_URL` is set; the verified build uses the served origin; a test fails on any `.invalid` host; no canonical on the 404 page |
| 3 | Medium | The comparison chart joined non-consecutive years, contradicting the site's own gap rule (data, design) | Fixed. The comparison page now draws with the same panel grammar as the index and school records: gaps preserved, 2020–21 band marked, a mobile geometry, byte-identical TypeScript port proven on 5,460 cases |
| 4 | Major | 26–46-column ledgers: caption hidden inside the scroller, no scroll cue, undefined status tokens, duplicate "Evidence" headings (design, product) | Fixed. Caption text sits above the scroller; scroll shadows on both edges; every status links to the status-code glossary; the last column is "Record"; per-row disclosure names include the period |
| 5 | Major | Selects that navigate on change (WCAG 3.2.2); duplicated corrections filter (engineering, design) | Fixed. The series select needs an Apply button; the corrections page uses links only |
| 6 | Major | Evidence search: no error path, focus lost after paging, over-broad live region on compare (engineering) | Fixed. Failure message with a browse link; pager buttons with focus moved to the count; a one-line status region on compare |
| 7 | Major | Silent gaps in ledgers (product) | Fixed. Each ledger states the years within its span that have no row; nothing is estimated |
| 8 | Major | Corrections and ledgers not linked both ways (product) | Fixed. A corrected row's evidence panel names its correction; each correction lists the rows for that school and period |
| 9 | Major | No publisher or contact (product) | Fixed. About and footer state who publishes and the two routes to write in |
| 10 | Major | Rate limiter shared one bucket for unidentified clients and never evicted; function responses lacked security headers (engineering) | Fixed. Unidentified clients are never pooled; stale keys are evicted; every handler response carries CSP, HSTS, nosniff; the serverless limitation is documented |
| 11 | Minor | Correction receipt read "Enquiry not recorded" (DOM-shadowed dataset); consent checkbox without an id; "Reference ." when empty (engineering, product) | Fixed and covered by the browser suite |
| 12 | Minor | Precision claim in methodology; "excluded by default" and "Yearbook" unexplained; Oxbridge hero sentence fragment; "Rank" column on a never-a-ranking site; 1836 span (data, product) | Fixed in copy: the methodology states the display precision; the compare and index pages explain what "by default" and "Yearbook" mean here; "Rank as printed (2007 source)"; the home page says where the ledgers begin |
| 13 | Minor | CSV downloads printed Python list literals; TypeScript escaping differed from Python's (data) | Fixed. Lists are joined; `&#x27;` on both sides |
| 14 | Minor | Hero blocks bottom-aligned; small table text; sub-24px targets; dashed third series needed; select clipping; long record titles (design, product) | Fixed. Cap-line alignment, 12px minimum type, larger targets, dashed third series, wider selects, record titles split into title and subhead |
| 15 | Minor | Home loads full-size artwork for small cards; sitemap lists noindex pages; `chrome-launcher` undeclared; obsolete `interest-cohort` (engineering) | Fixed. `srcset`/`sizes` on artwork; sitemap filter; dependency declared; directive removed |
| 16 | Minor | Python browser tests skipped silently in CI (engineering) | Fixed. Playwright is in `requirements.txt` and installed in the data-layer job |
| — | Open | No public link on Oxford/Cambridge, US and subject records; titles withheld (product, data) | Not changed: the reviewed edition approved no public link for those references, and the brief forbids inventing or exposing locations. The record pages now say so and give the route to ask |
| — | Open | Internal vocabulary in frozen text ("Pre-U honest", "The Bible", C15 wording, "reportedly") and an unlabelled derived column (`fold_pp`) (data, design, product) | Not changed: these strings are frozen dataset content; changing them is a versioned editorial decision, not a presentation fix. Listed in `EXECUTION.md` §7 for the editors |
| — | Open | Largest ledger page (St Paul's, 20 ledgers) is 830 KB of HTML (engineering) | Reduced where safe (no per-source `title` attributes, compact evidence cells). `content-visibility` was tried and removed: its placeholder sizing overlapped the footer for automated tools. Splitting the page by ledger family is proposed, not done |
| — | Open | Firefox and WebKit not exercised (engineering) | Environment cannot download those browsers; see `EXECUTION.md` §7 |
