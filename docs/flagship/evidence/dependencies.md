# Dependencies

## Frontend (web/package.json)

| Package | Version | Role | Licence |
| --- | --- | --- | --- |
| `@astrojs/sitemap` | 3.7.4 | sitemap generation | MIT |
| `@fontsource-variable/inter` | 5.3.0 | Inter variable font, self-hosted | OFL-1.1 |
| `@fontsource-variable/newsreader` | 5.3.0 | Newsreader variable font, self-hosted | OFL-1.1 |
| `@fontsource/ibm-plex-mono` | 5.3.0 | IBM Plex Mono, self-hosted | OFL-1.1 |
| `astro` | 7.2.10 | static site framework | MIT |
| `@astrojs/check` | 0.9.10 | type-checking .astro files (dev) | MIT |
| `@axe-core/playwright` | 4.13.0 | accessibility audit in e2e tests (dev) | MPL-2.0 |
| `@playwright/test` | 1.62.1 | end-to-end tests (dev) | Apache-2.0 |
| `@types/node` | 22.20.1 | Node typings (dev) | MIT |
| `lighthouse` | 13.4.1 | performance audit (dev) | Apache-2.0 |
| `sharp` | 0.35.4 | icon and social-card generation (dev) | Apache-2.0 |
| `typescript` | 5.9.3 | type checker (dev) | Apache-2.0 |
| `vitest` | 4.1.11 | unit tests (dev) | MIT |

`npm audit --audit-level=high`: found 0 vulnerabilities (2 September 2026, 411 packages installed).

No runtime dependency ships to the browser: the client bundles are the site's own TypeScript islands only.

## Data layer (requirements.txt)

| Package | Version | Role |
| --- | --- | --- |
| `streamlit` | 1.62.0 | the parity oracle and the existing application; not used by the static site at runtime |

## External services

None at runtime. Form submissions are forwarded only to a review endpoint configured by the deployment (`REVIEW_WEBHOOK_URL`); with none configured the page says so and the submission is not stored.
