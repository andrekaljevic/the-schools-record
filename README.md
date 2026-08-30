# The Schools Record

A public, source-led statistical yearbook of examination results, university
pathways and admissions evidence across leading UK independent schools.

This repository contains the self-contained Streamlit deployment of The Schools
Record and its auditable evidence snapshot dated 30 August 2026.

## Run locally

```bash
python -m pip install -r requirements.txt
streamlit run streamlit_app.py
```

The deployment bundle is self-contained and does not load the former
ChatGPT-hosted site.

The compressed interface assets are generated from the canonical application
source and loaded locally by `streamlit_app.py`.
