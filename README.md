# The Schools Record

A public, source-led statistical yearbook of examination results, university
pathways and admissions evidence across leading UK independent schools.

This repository contains the self-contained Streamlit deployment of The Schools
Record and its auditable evidence snapshot dated 30 August 2026. A traced
St Paul’s historical extension was added on 1 September 2026.

## St Paul’s historical extension

The deployment applies a fail-closed, source-catalogued patch to both supported
front-end bundle formats. It adds the recovered GCSE/IGCSE years 1999–2009 and
A-level evidence spanning 1992–2009, while keeping legacy points, ranks, pupil
thresholds, and grade-entry percentages as distinct measures. It also enriches
the first-party leaver-destination rows and replaces the secondary 2015 Oxbridge
figure of 49 with the school prospectus total of 41 (Oxford 20 plus Cambridge
21).

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
