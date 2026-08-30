from __future__ import annotations

import base64
import gzip
import json
from pathlib import Path
from urllib.parse import urlencode

import streamlit as st


APP_DIR = Path(__file__).resolve().parent
BUNDLE_DIR = APP_DIR / "bundle"

st.set_page_config(
    page_title="The Schools Record — Longitudinal Evidence",
    page_icon="SR",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def load_connector_asset(directory: str) -> str | None:
    parts = sorted((BUNDLE_DIR / "connector" / directory).glob("part-*"))
    if not parts:
        return None
    encoded = "".join(part.read_text(encoding="ascii") for part in parts)
    return gzip.decompress(base64.b64decode(encoded)).decode("utf-8")


def load_frontend() -> tuple[str, str]:
    connector_css = load_connector_asset("css")
    connector_js = load_connector_asset("js")
    if connector_css is not None and connector_js is not None:
        return connector_css, connector_js

    css_path = BUNDLE_DIR / "app.css.gz"
    js_path = BUNDLE_DIR / "app.js.gz"
    if not css_path.exists() or not js_path.exists():
        raise FileNotFoundError(
            "The Schools Record front-end bundle is missing. Run the Vite build before deployment."
        )
    with gzip.open(css_path, "rt", encoding="utf-8") as css_file:
        css = css_file.read()
    with gzip.open(js_path, "rt", encoding="utf-8") as js_file:
        javascript = js_file.read()
    return css, javascript


def serialise_query() -> str:
    pairs: list[tuple[str, str]] = []
    for key in st.query_params:
        for value in st.query_params.get_all(key):
            pairs.append((key, value))
    encoded = urlencode(pairs)
    return f"?{encoded}" if encoded else ""


frontend_css, frontend_js = load_frontend()
initial_query = serialise_query()

# Prevent literal closing tags in the compiled assets from terminating their
# inline containers when Streamlit creates the isolated application document.
safe_css = frontend_css.replace("</style", "<\\/style")
safe_js = frontend_js.replace("</script", "<\\/script")

document = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <meta name="theme-color" content="#f3f1eb" />
  <meta name="description" content="A sourced statistical yearbook of examination results, university pathways and school-admissions evidence across leading UK independent schools." />
  <title>The Schools Record — Longitudinal Evidence</title>
  <style>{safe_css}</style>
</head>
<body>
  <div id="root"></div>
  <script>window.__SCHOOLS_RECORD_QUERY__ = {json.dumps(initial_query)};</script>
  <script type="module">{safe_js}</script>
</body>
</html>"""

st.markdown(
    """
    <style>
      html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
        background: #f3f1eb;
      }
      [data-testid="stHeader"], [data-testid="stToolbar"],
      [data-testid="stDecoration"], #MainMenu, footer {
        display: none !important;
      }
      [data-testid="stMainBlockContainer"], .block-container {
        width: 100% !important;
        max-width: none !important;
        padding: 0 !important;
      }
      [data-testid="stElementContainer"] {
        margin: 0 !important;
      }
      [data-testid="stIFrame"] iframe {
        display: block;
        width: 100%;
        border: 0;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

st.iframe(document, height=1400)
