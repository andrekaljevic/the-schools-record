# Route matrix

Generated from the production build (`web/dist`).

| Route | Pages | Oracle equivalent | Status |
| --- | --- | --- | --- |
| `/` | 1 | ?p=/ | built |
| `/404.html` | 1 | unknown ?p= route | built |
| `/about/` | 1 | ?p=/about | built |
| `/changelog/` | 1 | ?p=/changelog | built |
| `/compare/` | 1 | ?p=/compare | built |
| `/corrections/` | 1 | ?p=/corrections | built |
| `/corrections/report/` | 1 | ?p=/corrections/report | built |
| `/corrections/schools/{school}/` | 7 | ?p=/corrections&school={school} | built |
| `/data/evidence-search.json` | 1 | (search index; internal) | built |
| `/downloads/compare/{metric}.csv` | 11 | comparison download button | built |
| `/downloads/ledgers/{dataset}.csv` | 62 | per-ledger download button | built |
| `/evidence/` | 1 | ?p=/evidence | built |
| `/evidence/browse/{corpus}/{page}/ (paginated listings)` | 184 | ?p=/evidence&corpus=…&page=… | built |
| `/evidence/method/` | 1 | ?p=/evidence&section=method | built |
| `/evidence/records/{corpus}/{id}/ (record permalinks)` | 2277 | ?p=/evidence&record={id} | built |
| `/evidence/sources/` | 1 | ?p=/evidence&section=sources | built |
| `/methodology/` | 1 | ?p=/methodology | built |
| `/oxbridge/` | 1 | ?p=/oxbridge | built |
| `/privacy/` | 1 | ?p=/privacy | built |
| `/professional/` | 1 | ?p=/professional | built |
| `/sample-dossier/` | 1 | ?p=/sample-dossier | built |
| `/schools/` | 1 | ?p=/schools | built |
| `/schools/series/{metric}/` | 10 | ?p=/schools&series={metric} | built |
| `/schools/{school}/` | 7 | ?p=/schools/{school} | built |
| `/schools/{school}/{section}/` | 35 | ?p=/schools/{school}/{section} | built |
| `/sitemap-0.xml` | 1 | none | built |
| `/sitemap-index.xml` | 1 | none | built |
| `/terms/` | 1 | ?p=/terms | built |
| `/us-universities/` | 1 | ?p=/us-universities | built |

Total files with a route: 2614

Legacy `/?p=…` links are redirected by `web/src/islands/legacy-redirect.ts` (home and 404 pages); the mapping is unit-tested in `web/tests/unit/routes.test.ts`.
