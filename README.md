# The Schools Record

Native Streamlit deployment of The Schools Record.

This branch renders the public record directly with Streamlit from the frozen production dataset rather than embedding the compiled frontend bundle. The frozen data source remains the immutable published bundle in `bundle/latest.js.gz`; runtime materialisation recreates the verified dataset, stylesheet and responsive school artwork before the native views load.

## Run locally

```bash
python -m pip install -r requirements.txt
streamlit run streamlit_app.py
```

The application entry point is `streamlit_app.py`. Routes use the `p` query parameter, for example `?p=/schools/winchester/exam-results`.

The data baseline is frozen. Interface/deployment work must not alter published statistical values.
