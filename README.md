# The Schools Record

A public, source-led statistical yearbook of examination results, university
pathways and admissions evidence across leading UK independent schools.

This repository contains the self-contained Streamlit deployment of The Schools
Record and its auditable evidence snapshot dated 2 September 2026. Traced
St Paul’s and Winchester historical extensions were added in September 2026.

## KCS Wimbledon examination-count audit

The KCS result ledgers now carry the exact candidate and subject-entry
denominators recovered from the school result tables and contemporary Old
King's Club reports. A-level pathway pupils, actual A-level takers, IB
candidates and IB Higher-Level entries remain separate, including the 2024 and
2025 crossover pupil. Combined sixth-form entry totals use only A-level entries
plus IB Higher-Level entries. GCSE candidate totals, numbered/lettered entry
components and excluded Additional Mathematics entries are also typed
separately. Historic secondary league-table figures and lower bounds remain
explicitly labelled and are never silently promoted to primary exact data.

## Winchester historical GCSE extension

The Winchester GCSE ledger now begins with the introduction of A* in 1994 and
uses the same three entry-grade fields in every legacy-scale year: A*, A*/A and
A*–B. It records the recovered 1996, 1997, 2004–06, 2011 and 2012 bands, retains
the full suppression intervals in the row notes while displaying their upper
endpoints to one decimal place, and leaves unrecovered annual cells blank. It
does not substitute pupil-level five-grade thresholds or government subsets
that excluded substantial IGCSE provision.

## Winchester results and destinations audit

The Winchester audit restores the official 2010–20 Cambridge Pre-U spine,
quarantines the mixed A-level/Pre-U teacher-assessed result for 2021, and adds
the school’s exact 2003–09 A-level tables. Conflicting source populations remain
visible rather than being averaged. University evidence is outcome-typed so
forecasts, offers, admissions, places, matriculations and final destinations do
not masquerade as a single series; published destination rounding is retained
without renormalisation. Current evidence includes the controlling 2024/25
offer totals and the separately labelled initial 2026 Oxbridge total.

The 2010 Pre-U row now carries an explicitly modelled reconstruction: 339
entries, 18.9% D1, 52.2% D1–D2, 79.1% D1–D3, 90.0% D1–M1 and 95.0% D1–M2.
The interface identifies these as estimates rather than school-published exact
figures, retains Winchester’s original narrative bands, and displays the
defensible ranges and denominator alternatives in the evidence detail.

## St Paul’s historical extension

The deployment applies a fail-closed, source-catalogued patch to both supported
front-end bundle formats. It adds the recovered GCSE/IGCSE years 1999–2009 and
A-level evidence spanning 1992–2009, while keeping legacy points, ranks, pupil
thresholds, and grade-entry percentages as distinct measures. It also enriches
the first-party leaver-destination rows and replaces the secondary 2015 Oxbridge
figure of 49 with the school prospectus total of 41 (Oxford 20 plus Cambridge
21). The university section now keeps UCAS-cycle applications, offers and
accepted outcomes separate from final leaver destinations and calendar-entry
year tables. Complete institution ledgers are included wherever recovered,
with strict-USA and Oxbridge counts, denominators and source conflicts exposed
rather than silently reconciled.

## Run locally

```bash
python -m pip install -r requirements.txt
streamlit run streamlit_app.py
```

The deployment bundle is self-contained and does not load the former
ChatGPT-hosted site.

The compressed interface assets are generated from the canonical application
source and loaded locally by `streamlit_app.py`.

Run the historical-data regression suite with:

```bash
python -m unittest discover -s tests -v
```
