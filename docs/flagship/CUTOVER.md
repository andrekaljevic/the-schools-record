# Cutover, redirects, monitoring and rollback

This plan is written for the day the static frontend replaces the Streamlit deployment. Nothing in it has been
executed: the current public deployment is untouched, `main` is untouched, and no hosting credential exists in the
environment this branch was built in.

## 1. Preconditions

| Item | Check |
| --- | --- |
| Branch | `claude/tsr-flagship-10x` reviewed; CI (`.github/workflows/flagship.yml`) green on the head commit |
| Data | `sha256sum data/dataset.json` = `245f2d8176f8fca0d53f41689f096734dd13e9023af9a67931314334251b9f6f`; `python3 tools/build_public_projection.py --check` passes |
| Origin | `SITE_URL=https://<production host>` exported at build time (canonical URLs, Open Graph, robots, sitemap) |
| Forms | `REVIEW_WEBHOOK_URL` (HTTPS) and optional `REVIEW_WEBHOOK_TOKEN` provisioned on the host; until then every receipt honestly reads "not recorded" |
| Host | Any static host that serves `index.html` for directory paths and honours `_headers` (Cloudflare Pages and Netlify natively; for others, translate `web/public/_headers` into the host's header configuration) |

## 2. Build

```
python3 tools/build_public_projection.py
cd web && npm ci && SITE_URL=https://<production host> npm run verify
```

`npm run verify` runs the type check, unit tests, production build, privacy scan, security scan, budgets and the
browser suite. Deploy the resulting `web/dist` directory (and, on Cloudflare Pages, `web/functions` for the form
endpoints under `/api/`).

## 3. Preview first

Deploy `web/dist` to a preview origin (a Cloudflare Pages preview branch, a Netlify deploy preview, or any static
bucket). Do not point DNS at it. Run the browser suite against the preview:

```
cd web && PLAYWRIGHT_BASE_URL=https://<preview host> npx playwright test
node scripts/lighthouse.mjs https://<preview host>
```

## 4. Redirects from the previous deployment

The Streamlit deployment addressed every page as `/?p=/route&query`. Three layers cover those links:

1. **Same origin.** If the static site is served from the same host, the home page and the 404 page carry
   `web/src/islands/legacy-redirect.ts`, which maps `?p=` links (including `record=`, `series=`, `section=` and
   `school=` parameters) to canonical paths. The mapping is unit-tested (`web/tests/unit/routes.test.ts`) and
   exercised in the browser suite.
2. **Host rules.** Where the host supports query-string redirects (Netlify `_redirects`, Cloudflare Bulk Redirects,
   nginx `map`), add rules for the fixed routes so the redirect happens server-side with a 301; the script remains
   as the fallback for dynamic ones.
3. **Different origin.** If the Streamlit host stays alive on another domain for a grace period, configure it to
   redirect `/` with a `p` parameter to `https://<production host>/?p=…`; the script completes the mapping.

Sub-page paths without trailing slashes (`/schools/eton/exam-results`) are redirected to the trailing-slash form
by the host (Cloudflare Pages, Netlify and GitHub Pages all do this by default).

## 5. Cutover

1. Freeze the Streamlit deployment (no further changes) and record its URL and version.
2. Deploy `web/dist` (built with the production `SITE_URL`) to the production project.
3. Switch DNS or the host's production branch to the new deployment.
4. Immediately after: request `/`, `/schools/winchester/exam-results/`, `/evidence/records/ox/oxford-apply-centre-2006-10092/`,
   `/downloads/ledgers/winchester_gcse.csv`, `/sitemap-index.xml`, `/robots.txt` and one legacy `?p=` link; confirm
   200s, the security headers (`curl -I`), and the redirect.
5. Submit one test correction report and confirm the receipt matches the receiver's state (forwarded when the
   webhook is configured, otherwise "not recorded").

## 6. Monitoring

* **Availability and integrity.** An uptime check on `/` and on one record permalink; a daily job that fetches
  `/sitemap-0.xml` and samples 50 URLs for 200s.
* **Search.** Submit `/sitemap-index.xml` in Search Console; watch coverage for the 2,277 record permalinks and
  the 184 listing pages (listing pages beyond page 1 are `noindex`).
* **Web vitals.** No analytics ship in this edition (see `/privacy/`). If field measurement is wanted later, add a
  privacy-respecting collector that records only the page path and the metric, update `/privacy/` first, and keep
  the CSP `connect-src` limited to that collector.
* **Forms.** Alert when the review endpoint returns non-2xx; the page already tells the submitter, but the operator
  must know too.
* **Headers.** A weekly `curl -I` against `/` compared with `web/public/_headers`.

## 7. Rollback

The previous deployment is not modified by the cutover, so rollback is a routing change:

1. Point DNS or the host's production branch back at the frozen Streamlit deployment.
2. Confirm `/?p=/schools` renders.
3. Record the reason in `docs/flagship/EXECUTION.md` §7.

Rollback needs no data step: both deployments read the same frozen `data/dataset.json`
(SHA-256 `245f2d81…9f6f`), and the static site never writes to it.

## 8. After cutover

* Keep the Streamlit deployment reachable but read-only for one release cycle for comparison, then retire it.
* Retire `streamlit_app.py` and the Streamlit views only after a separate decision; the Python data layer (`tsr/`)
  stays as the canonical interpretation and the source of the projection.
