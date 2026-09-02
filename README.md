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
| `tsr/records.py` | Dataset and row selection, ordering and labelling |
| `tsr/format.py` | Field labels and display formatting |
| `tsr/comparison.py` | Like-for-like comparison series |
| `tsr/chart.py` | The comparison chart, drawn as inline SVG |
| `tsr/components.py` | Data ledgers, evidence panels, latest-record cards |
| `tsr/views_*.py` | One module per group of routes |
| `tsr/forms.py` | Enquiry and correction forms |
| `tsr/styles.py` | Re-scopes the published stylesheet and styles the widgets |
| `data/dataset.json` | The frozen production dataset |
| `assets/site.css` | The published site's own stylesheet, reused verbatim |
| `static/` | School artwork and the sample dossier PDF, served by Streamlit |
| `pages_html/` | Static editorial pages (about, privacy, terms, changelog) |

### Routing

Routes are carried in the `p` query parameter, so every page of the record has
a shareable address: `?p=/schools/winchester/exam-results`. The comparison tool
additionally reflects `schools`, `metric`, `from`, `to` and `view` in the URL,
as the published site did.

### Styling

`assets/site.css` is the published site's stylesheet, unmodified. Because a
Streamlit page shares one DOM with Streamlit's own chrome, `tsr/styles.py`
re-scopes every selector under `.tsr` before injecting it; the site's Tailwind
preflight therefore cannot reach Streamlit's widgets, and the widgets that carry
real interaction are styled back to match the record.

## The frozen data

`data/dataset.json` is a **verbatim extraction** of the immutable data module
inside the published front-end bundle (`bundle/latest.js.gz`, snapshot
`production-818c7c2-data-frozen-v1`, baseline commit `818c7c2`). It holds all
2,277 frozen records: 1,274 figure rows, 83 granular rows, 571 Oxbridge records
and 349 US records.

Nothing in this application alters, infers, recalculates, normalises, rounds,
corrects or replaces a stored figure. Blanks stay blank, ranges keep both
bounds, lower bounds stay lower bounds, estimates keep their classification, and
conflicting source populations remain visible. The only calculated series is the
Oxford offer rate, which is derived at display time from the frozen offers and
applications and is labelled as such — exactly as the published site did.

To reproduce or verify the extraction (requires Node):

```bash
python tools/extract_dataset.py --check   # verify the committed file
python tools/extract_dataset.py           # rewrite it from the bundle
```

`tests/test_frozen_dataset.py` pins the file's SHA-256, its record counts, its
snapshot identity and a set of spot-checked figures, and re-extracts the bundle
when Node is available.

## Parity with the previously hosted site

The rebuild was checked page by page against the published build:

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

The published site posted these forms to server endpoints. This deployment has
no such backend, so submissions are appended to `review-queue/*.jsonl` next to
the application. On Streamlit Community Cloud that storage is ephemeral and is
cleared when the app restarts — wire the forms to a durable destination before
relying on them.

## Regenerating assets

```bash
python -m pip install -r requirements-dev.txt
python tools/build_static_images.py                      # static/schools/*.webp
python tools/build_sample_pdf.py http://127.0.0.1:8502/  # the sample dossier PDF
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
