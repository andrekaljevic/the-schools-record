# The Schools Record

A public, source-led statistical yearbook of examination results, university
pathways and admissions evidence across seven leading UK independent schools.

This repository is the **native Streamlit deployment** of The Schools Record.
It renders the record directly with Streamlit from the frozen production
dataset. It does not load, embed or iframe a compiled front-end bundle.

## Run locally

```bash
python -m pip install -r requirements.txt
streamlit run streamlit_app.py
```

Run the regression suite with:

```bash
python -m unittest discover -s tests -v
```

## How it is built

| Path | Purpose |
| --- | --- |
| `streamlit_app.py` | Entry point: page config, stylesheet injection, header, router, footer |
| `tsr/dataset.py` | Loads the frozen dataset |
| `tsr/corpora.py` | Typed access to all four corpora, the corrections and differences ledgers, the source catalogue and school-entry material; resolves every school spelling the corpora use |
| `tsr/records.py` | Figures-ledger selection, ordering, labelling and qualification families |
| `tsr/format.py` | Field labels, display formatting and ledger column selection |
| `tsr/comparison.py` | Like-for-like comparison series |
| `tsr/chart.py` | The comparison chart and the small-multiple panels, drawn as inline SVG |
| `tsr/trajectory.py` | Index panels and school results-by-year panels, assembled from the comparison series |
| `tsr/evidence.py` | The evidence index: a stable identifier, description and public route for every frozen record |
| `tsr/sources.py` | Public source references and the approved public links behind them |
| `tsr/components.py` | Data ledgers, evidence panels, series indexes, granular tables, latest-record cards |
| `tsr/views_core.py` | Home, school index, school records, examination and university ledgers |
| `tsr/views_evidence.py` | The evidence centre: records, sources, how the figures are checked |
| `tsr/views_corpora.py` | Oxford and Cambridge records, US-university records, school entry |
| `tsr/views_corrections.py` | Corrections and published differences; the correction report |
| `tsr/views_compare.py`, `tsr/views_editorial.py` | Comparison tool; methodology, professional and static pages |
| `tsr/forms.py`, `tsr/review_queue.py` | Enquiry and correction forms and where their submissions go |
| `tsr/meta.py` | Page titles, descriptions and shareable metadata per route |
| `tsr/styles.py` | Re-scopes the published stylesheet and styles the widgets |
| `data/dataset.json` | The frozen production dataset |
| `data/public_sources.json` | The approved public source links, derived from the reviewed public build |
| `assets/site.css` | The published site's own stylesheet, reused verbatim |
| `static/` | School artwork and the sample dossier PDF, served by Streamlit |
| `pages_html/` | Static editorial pages (about, privacy, terms, changelog) |

### Routing

Routes are carried in the `p` query parameter, so every page of the record has
a shareable address: `?p=/schools/winchester/exam-results`. The comparison tool
additionally reflects `schools`, `metric`, `from`, `to` and `view` in the URL,
as the published site did; the school index reflects `series`; the evidence
centre reflects its filters, `page`, `section` and `record`.

| Route | Content |
| --- | --- |
| `/` | Overview, the four-corpus inventory and the seven school cards |
| `/schools` | The school index with one like-for-like series panel per school |
| `/schools/{id}` | School record: latest result, results by year, what the record holds, every section |
| `/schools/{id}/exam-results` | Examination ledgers, series index, subject-level detail where held |
| `/schools/{id}/university-destinations` | Application-cycle and destination ledgers, itemised destination lists where held |
| `/schools/{id}/oxbridge` | The school's Oxford and Cambridge admissions records, filterable |
| `/schools/{id}/us-universities` | The school's US and overseas university records, filterable |
| `/schools/{id}/school-entry` | Published school-admissions process evidence and known gaps |
| `/compare` | The like-for-like comparison tool |
| `/evidence` | Evidence centre: search all 2,277 records (`section=records`), the source register (`sources`), how the figures are checked (`method`); `record=` opens one record, `dataset=…&period=…` traces a displayed figure |
| `/oxbridge`, `/us-universities` | Corpus homes: by-school summaries, university-wide context, the 2007 historical table |
| `/corrections` | Every recorded correction and published difference, filterable by school |
| `/corrections/report` | The correction report form |
| `/methodology`, `/professional`, `/sample-dossier`, `/about`, `/privacy`, `/terms`, `/changelog` | Editorial pages |

### The four corpora

The 2,277 frozen records are four corpora, and each has a public path:

* **Figures** (1,274 rows in 62 ledgers) — the school examination and
  university ledgers. Every ledger shows every field that carries a published
  figure: identity, denominators, counts, percentages and the evidence status,
  with no column cap; only annotations wait behind "Show the remaining
  columns". Each row has an anchor, an evidence panel with its row-level and
  dataset-level sources, and a link that traces the figure in the evidence
  centre.
* **Granular** (83 rows) — St Paul's 2010 subject-level results and 2009
  itemised destination lists, shown as their own tables on the St Paul's
  examination and university pages.
* **Oxford and Cambridge** (571 records) — apply-centre outcomes by university
  and cycle, derived combined outcomes, rounded subject and college releases,
  the schools' own offer claims, university-wide outcomes, subject outcomes,
  course competition and the 2007 five-year table. Records naming a collection
  school are on that school's Oxbridge page; the rest are on `/oxbridge`.
* **US and overseas universities** (349 records) — named institutions and
  explicit aggregates by school, period and outcome type, with aggregates,
  alternative published versions and canonical status flagged.

`tsr/evidence.py` gives every record a stable identifier (`fig:…`, `gran:…`,
`ox:…`, `us:…`) and a permanent link, and `tests/test_parity.py` fails if any
record loses its public page.

### Sources and privacy

The frozen dataset identifies evidence by stable reference keys and carries no
document locations. The reviewed public build kept links to first-party school
pages, public-body releases and Internet Archive captures while redacting every
private working document; `tools/build_public_sources.py` applies exactly that
patch pipeline to the retained reference build and writes the surviving links
for the references the dataset cites to `data/public_sources.json`.
`tsr/sources.py` refuses to load any private location, withheld titles stay
withheld, and `tests/test_privacy.py` renders every route and fails on any
Drive or Docs link or private identifier.

### Corrections and published differences

The figures corpus records 29 locked corrections and 26 cases where credible
publications disagree. `/corrections` shows each in plain English — the
earlier value, the value the record uses, the reason, the sources and the
treatment — together with which compilation controls. The report form is
separate, at `/corrections/report`.

### Forms and the review queue

Submissions go through `tsr/review_queue.py`. With `TSR_REVIEW_WEBHOOK_URL`
(and optionally `TSR_REVIEW_WEBHOOK_TOKEN`) configured, each submission is
POSTed as JSON and confirmed only on a 2xx response. Without it, submissions
are appended to `review-queue/*.jsonl` (or `TSR_REVIEW_QUEUE_DIR`), and the
page says plainly that this deployment has no durable review store, shows a
copy of the submission to keep, and reports a failed write as a failure.

### Metadata

Each route sets its own page title; the description, Open Graph fields, a
canonical link and a schema.org Dataset description are written into the
document head after render by a guarded script (`tsr/meta.py`).

### Styling

`assets/site.css` is the published site's stylesheet, unmodified. Because a
Streamlit page shares one DOM with Streamlit's own chrome, `tsr/styles.py`
re-scopes every selector under `.tsr` before injecting it; the site's Tailwind
preflight therefore cannot reach Streamlit's widgets, and the widgets that carry
real interaction are styled back to match the record.

### Charts

Three chart placements share one visual language with the comparison chart:

* **School index** — every row carries a small panel of one like-for-like
  series (default: A-level grades at A*, switchable to any comparison metric
  and reflected in the `series` URL parameter). All seven panels share one
  ruler, so schools can be read against each other by year without a ranking.
* **School record** — a "Results by year" section with one panel per grading
  ruler (A level, GCSE 9–1, legacy GCSE A*–G). Panels share a year axis so a
  change of ruler reads as a handover; the 2010 introduction of A* and the
  2020–21 CAG/TAG years are marked; ledgers on rulers the comparison tool does
  not define (Pre-U, IB, crosswalks) are listed as recorded but not charted.
* **Sample dossier** — the comparison chart above the exact-value exhibit.

Every plotted point is a point from `tsr/comparison.py`, so nothing can be
drawn that the comparison tool would refuse. Lines join consecutive published
years only: a break in a line is a gap in the record, never an interpolation.
Each panel carries an "Exact values" disclosure. `tests/test_charts.py` pins
the rendered markup and checks that drawing every chart leaves the dataset
untouched.

## The frozen data

`data/dataset.json` is the immutable data module inside the published front-end
bundle (`bundle/latest.js.gz`, snapshot `production-818c7c2-data-frozen-v1`,
baseline commit `818c7c2`) **plus the recorded revisions** in
`data/revisions.json`. It holds all 2,277 records: 1,274 figure rows, 83
granular rows, 571 Oxbridge records and 349 US records.

### Revisions

Every statistical change since the frozen snapshot is a versioned revision.
`data/revisions.json` records each change with the dataset, row, field, the
exact value replaced and the value now used, the row note before and after, and
the ledger entry that documents it. `tools/apply_revisions.py` rebuilds the
dataset as *bundle extraction + revisions* and refuses to apply a change whose
`from` value is not exactly what the data holds:

```bash
python tools/apply_revisions.py            # rebuild data/dataset.json
python tools/apply_revisions.py --check    # verify the committed file
```

The current snapshot is `production-818c7c2-data-revised-v2`. Revision v2
reverses the five locked examination-result corrections (C01, C02, C03, C05,
C06) because the earlier published figures are the post-remark results; each
reversal is a new corrections-ledger entry (`R-C01` …) and the superseded entry
stays visible with its status changed. `tests/test_frozen_dataset.py` pins the
file's SHA-256, the frozen snapshot's own SHA-256, the record counts, the
snapshot identity, the revised values and the untouched locked entries, and
rebuilds the file from the bundle when Node is available.

Nothing in this application alters, infers, recalculates, normalises, rounds,
corrects or replaces a stored figure. Blanks stay blank, ranges keep both
bounds, lower bounds stay lower bounds, estimates keep their classification, and
conflicting source populations remain visible. The only calculated series is the
Oxford offer rate, which is derived at display time from the frozen offers and
applications and is labelled as such — exactly as the published site did.

To reproduce or verify the extraction (requires Node):

```bash
python tools/extract_dataset.py --check          # the bundle still yields the frozen snapshot
python tools/apply_revisions.py --check          # the committed file is snapshot + revisions
```


### Tests

| Module | Guards |
| --- | --- |
| `tests/test_frozen_dataset.py` | The dataset's checksum, counts, snapshot identity and spot-checked figures |
| `tests/test_streamlit_record.py` | Row selection, formatting, comparison series and the pinned comparison chart |
| `tests/test_charts.py` | The index and results-by-year panels: determinism, the segment rule, exact values |
| `tests/test_parity.py` | Reachability of every dataset, row and record; the feature matrix of the final public product; a crawl of every internal link; representative high-complexity ledgers; exact displayed values |
| `tests/test_privacy.py` | No private location in any public output; the review queue never claims receipt it cannot prove |
| `tests/test_responsive.py` | Representative pages at phone width in a real browser (skipped without Playwright and Chromium) |
| `tests/test_*_history.py`, `test_kcs_entry_counts.py`, `test_premium_presentation.py`, `test_public_experience_updates.py` | The historical patch modules that document the reference build |

## Parity with the previously hosted site

The native rebuild reproduces the final reviewed public product — the reference
build in `bundle/app.js.gz` with its data and public-experience patches — not
merely the shallower interim build it was first ported from. Its evidence
centre, corrections and published-differences ledgers, Oxford and Cambridge
and US-university records, school-entry material, row-level source tracing and
approved public links are all native pages now. Two things from older bundles
are deliberately not restored: private document links (redacted by the final
public-experience pass) and the bulk CSV index and per-table download handlers
that the same pass removed; per-ledger CSV downloads remain. The internal
analytical findings carried in the figures corpus are not rendered either: they
are working notes rather than published figures.

The rebuild was also checked page by page against the interim published build:

* every data table on every school page renders identical values, columns,
  ordering, evidence statuses and blank cells;
* the comparison chart SVG is byte-identical for the default state, and is
  pinned by `tests/fixtures/published_comparison_chart.svg`;
* the visible text of every page matches, apart from Streamlit's own widget
  labels;
* the evidence register lists the same 91 references with the same linkage.

Two interactions differ because Streamlit provides no equivalent:

* **Evidence panels** open as an inline disclosure rather than a modal dialog,
  since the published modal depended on client-side JavaScript.
* **Print** is left to the browser; the published toolbar button called
  `window.print()`.

One inherited artefact is deliberately preserved rather than corrected: in the
expanded columns of `cambridge_and_combined_st_paul_s_school`, a composite value
prints as `[object Object]`, as it does on the published site. Its component
figures are carried by the flattened columns beside it.

## Enquiries and corrections

The published site posted these forms to server endpoints. See "Forms and the
review queue" above: configure `TSR_REVIEW_WEBHOOK_URL` for durable receipt;
without it the page says so and never claims more than a local write.

## Regenerating assets

```bash
python -m pip install -r requirements-dev.txt
python tools/build_static_images.py                      # static/schools/*.webp
python tools/build_sample_pdf.py http://127.0.0.1:8502/  # the sample dossier PDF
python tools/build_public_sources.py                     # data/public_sources.json
```

## Historical material

`bundle/` holds the compiled builds of the previously hosted site and is kept as
the provenance of `data/dataset.json`; it is not loaded at runtime. The
`site_patches.py`, `kcs_entry_updates.py`, `winchester_entry_updates.py`,
`premium_presentation.py` and `public_experience_updates.py` modules are the
historical data and presentation patches applied to those bundles, retained with
their tests as an audit trail. The notes below record what those passes
established.

### KCS Wimbledon examination-count audit

The KCS result ledgers carry the exact candidate and subject-entry denominators
recovered from the school result tables and contemporary Old King's Club
reports. A-level pathway pupils, actual A-level takers, IB candidates and IB
Higher-Level entries remain separate, including the 2024 and 2025 crossover
pupil. Combined sixth-form entry totals use only A-level entries plus IB
Higher-Level entries. GCSE candidate totals, numbered/lettered entry components
and excluded Additional Mathematics entries are typed separately. Historic
secondary league-table figures and lower bounds remain explicitly labelled and
are never silently promoted to primary exact data.

### Winchester historical GCSE extension

The Winchester GCSE ledger begins with the introduction of A* in 1994 and uses
the same three entry-grade fields in every legacy-scale year: A*, A*/A and A*–B.
It records the recovered 1996, 1997, 2004–06, 2011 and 2012 bands, retains the
full suppression intervals in the row notes while displaying their upper
endpoints to one decimal place, and leaves unrecovered annual cells blank. It
does not substitute pupil-level five-grade thresholds or government subsets that
excluded substantial IGCSE provision.

### Winchester results and destinations audit

The Winchester audit restores the official 2010–20 Cambridge Pre-U spine,
quarantines the mixed A-level/Pre-U teacher-assessed result for 2021, and adds
the school's exact 2003–09 A-level tables. Conflicting source populations remain
visible rather than being averaged. University evidence is outcome-typed so
forecasts, offers, admissions, places, matriculations and final destinations do
not masquerade as a single series; published destination rounding is retained
without renormalisation. Current evidence includes the controlling 2024/25 offer
totals and the separately labelled initial 2026 Oxbridge total.

The 2010 Pre-U row carries an explicitly modelled reconstruction: 339 entries,
18.9% D1, 52.2% D1–D2, 79.1% D1–D3, 90.0% D1–M1 and 95.0% D1–M2. The interface
identifies these as estimates rather than school-published exact figures,
retains Winchester's original narrative bands, and displays the defensible
ranges and denominator alternatives in the evidence detail.

### St Paul's historical extension

The record adds the recovered GCSE/IGCSE years 1999–2009 and A-level evidence
spanning 1992–2009, while keeping legacy points, ranks, pupil thresholds and
grade-entry percentages as distinct measures. It enriches the first-party
leaver-destination rows and replaces the secondary 2015 Oxbridge figure of 49
with the school prospectus total of 41 (Oxford 20 plus Cambridge 21). The
university section keeps UCAS-cycle applications, offers and accepted outcomes
separate from final leaver destinations and calendar-entry year tables. Complete
institution ledgers are included wherever recovered, with strict-USA and
Oxbridge counts, denominators and source conflicts exposed rather than silently
reconciled.
