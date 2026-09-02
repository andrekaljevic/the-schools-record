# Lighthouse

Lighthouse run against the production build served locally (simulated throttling; a shared build container, so absolute timings are indicative and scores are the durable signal).

| Form factor | Route | Performance | Accessibility | Best practices | SEO | LCP | CLS | TBT | Bytes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| mobile | `/` | 95 | 100 | 100 | 100 | 2563 ms | 0 | 0 ms | 269 KB |
| mobile | `/schools/` | 99 | 100 | 100 | 100 | 2117 ms | 0 | 0 ms | 226 KB |
| mobile | `/schools/westminster/` | 96 | 100 | 100 | 100 | 2557 ms | 0 | 0 ms | 299 KB |
| mobile | `/schools/winchester/exam-results/` | 95 | 100 | 100 | 100 | 2706 ms | 0 | 0 ms | 311 KB |
| mobile | `/compare/` | 96 | 100 | 100 | 100 | 2554 ms | 0 | 0 ms | 286 KB |
| mobile | `/evidence/` | 97 | 100 | 100 | 100 | 2417 ms | 0 | 0 ms | 248 KB |
| mobile | `/evidence/records/ox/oxford-apply-centre-2006-10092/` | 99 | 100 | 100 | 100 | 2103 ms | 0 | 0 ms | 193 KB |
| mobile | `/sample-dossier/` | 96 | 100 | 100 | 100 | 2413 ms | 0 | 0 ms | 260 KB |
| desktop | `/` | 100 | 100 | 100 | 100 | 708 ms | 0 | 0 ms | 1408 KB |
| desktop | `/schools/` | 100 | 100 | 100 | 100 | 486 ms | 0 | 0 ms | 226 KB |
| desktop | `/schools/westminster/` | 100 | 100 | 100 | 100 | 765 ms | 0 | 0 ms | 477 KB |
| desktop | `/schools/winchester/exam-results/` | 100 | 100 | 100 | 100 | 522 ms | 0 | 0 ms | 311 KB |
| desktop | `/compare/` | 100 | 100 | 100 | 100 | 563 ms | 0 | 0 ms | 286 KB |
| desktop | `/evidence/` | 100 | 100 | 100 | 100 | 523 ms | 0 | 0 ms | 248 KB |
| desktop | `/evidence/records/ox/oxford-apply-centre-2006-10092/` | 100 | 100 | 100 | 100 | 403 ms | 0 | 0 ms | 193 KB |
| desktop | `/sample-dossier/` | 100 | 100 | 100 | 100 | 524 ms | 0 | 0 ms | 260 KB |
