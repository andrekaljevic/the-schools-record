# The Schools Record — static frontend

A static site (Astro 7, TypeScript islands, no framework runtime) built from a deterministic public projection of
the frozen dataset. The Python package `tsr/` in the repository root is the canonical interpretation of the data;
this directory only renders what it projects.

```
python3 ../tools/build_public_projection.py   # writes src/generated/ (never touches data/)
npm ci
npm run dev                                   # http://localhost:4321
npm run build && npm run preview              # production build in dist/
npm run verify                                # check, unit, build, privacy, security, budgets, e2e
```

Set `SITE_URL=https://your.host` when building for a real origin (canonical URLs, Open Graph, robots, sitemap).
Forms post to `/api/enquiry` and `/api/correction`; the handler in `functions/lib/handler.ts` forwards to
`REVIEW_WEBHOOK_URL` (HTTPS) when configured and otherwise tells the submitter, truthfully, that nothing was stored.

| Directory | Contents |
| --- | --- |
| `src/generated/` | the projection (generated, ignored by git) |
| `src/lib/` | typed loaders, routes, metadata, the chart port, helpers |
| `src/layouts/`, `src/components/`, `src/pages/` | the site |
| `src/islands/` | client scripts: comparison instrument, evidence search, filters, forms, legacy redirects |
| `src/styles/global.css` | the design system |
| `functions/` | platform-neutral form handler and its Cloudflare Pages bindings |
| `scripts/` | privacy scan, security scan, budgets, Lighthouse, icon generation |
| `tests/unit/`, `tests/e2e/` | Vitest and Playwright suites; `tests/fixtures/comparison-charts.json` pins chart parity |
