# Lighthouse

Lighthouse run against the production build served locally (simulated throttling; a shared build container, so absolute timings are indicative and scores are the durable signal).

| Form factor | Route | Performance | Accessibility | Best practices | SEO | LCP | CLS | TBT | Bytes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| mobile | `/` | 95 | 100 | 100 | 100 | 2557 ms | 0 | 0 ms | 271 KB |
| mobile | `/schools/` | 98 | 100 | 100 | 100 | 2106 ms | 0 | 0 ms | 229 KB |
| mobile | `/schools/westminster/` | 94 | 100 | 100 | 100 | 3006 ms | 0 | 0 ms | 372 KB |
| mobile | `/schools/winchester/exam-results/` | 95 | 100 | 100 | 100 | 2555 ms | 0 | 0 ms | 318 KB |
| mobile | `/compare/` | 94 | 100 | 100 | 100 | 2703 ms | 0 | 0 ms | 298 KB |
| mobile | `/evidence/` | 97 | 100 | 100 | 100 | 2255 ms | 0 | 0 ms | 252 KB |
| mobile | `/evidence/records/ox/oxford-apply-centre-2006-10092/` | 99 | 100 | 100 | 100 | 1953 ms | 0 | 0 ms | 196 KB |
| mobile | `/sample-dossier/` | 95 | 100 | 100 | 100 | 2556 ms | 0 | 0 ms | 265 KB |
| desktop | `/` | 100 | 100 | 100 | 100 | 727 ms | 0 | 0 ms | 599 KB |
| desktop | `/schools/` | 100 | 100 | 100 | 100 | 484 ms | 0 | 0 ms | 229 KB |
| desktop | `/schools/westminster/` | 100 | 100 | 100 | 100 | 686 ms | 0 | 0 ms | 372 KB |
| desktop | `/schools/winchester/exam-results/` | 100 | 100 | 100 | 100 | 566 ms | 0 | 0 ms | 318 KB |
| desktop | `/compare/` | 100 | 100 | 100 | 100 | 587 ms | 0 | 0 ms | 298 KB |
| desktop | `/evidence/` | 100 | 100 | 100 | 100 | 550 ms | 0 | 0 ms | 252 KB |
| desktop | `/evidence/records/ox/oxford-apply-centre-2006-10092/` | 100 | 100 | 100 | 100 | 444 ms | 0 | 0 ms | 196 KB |
| desktop | `/sample-dossier/` | 100 | 100 | 100 | 100 | 563 ms | 0 | 0 ms | 265 KB |
