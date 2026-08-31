from __future__ import annotations

import base64
import gzip
import json
from pathlib import Path
from urllib.parse import urlencode

import streamlit as st


APP_DIR = Path(__file__).resolve().parent
BUNDLE_DIR = APP_DIR / "bundle"
SKETCH_DIR = APP_DIR / "assets" / "school-sketches"

SCHOOL_SKETCH_SPECS = {
    "eton": {
        "filename": "eton.webp",
        "width": 1200,
        "height": 900,
        "alt": "Pencil illustration of Eton College's collegiate courtyard and memorial",
    },
    "westminster": {
        "filename": "westminster.webp",
        "width": 1200,
        "height": 900,
        "alt": "Pencil illustration of Westminster School's ivy-covered courtyard and Victoria Tower",
    },
    "kcs": {
        "filename": "kcs.webp",
        "width": 1200,
        "height": 1002,
        "alt": "Pencil illustration of King's College School Wimbledon",
    },
    "st-pauls": {
        "filename": "st-pauls.webp",
        "width": 1200,
        "height": 998,
        "alt": "Pencil illustration of St Paul's School memorial pavilion",
    },
    "spgs": {
        "filename": "spgs.webp",
        "width": 1200,
        "height": 900,
        "alt": "Pencil illustration of St Paul's Girls' School",
    },
    "wycombe": {
        "filename": "wycombe.webp",
        "width": 1200,
        "height": 675,
        "alt": "Pencil illustration of Wycombe Abbey beside the water",
    },
}

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


def extend_frontend_for_school_sketches(css: str, javascript: str) -> tuple[str, str]:
    def replace_once(source: str, before: str, after: str, label: str) -> str:
        if source.count(before) != 1:
            raise RuntimeError(f"Unable to apply {label}: expected one bundle match")
        return source.replace(before, after, 1)

    javascript = replace_once(
        javascript,
        "className:`record-masthead${e===`winchester`?` record-masthead-illustrated`:``}`",
        "className:`record-masthead${e===`winchester`||window.__SCHOOL_SKETCHES__?.[e]?` record-masthead-illustrated`:``}`",
        "illustrated masthead predicate",
    )
    javascript = replace_once(
        javascript,
        "e===`winchester`&&(0,N.jsx)(`figure`,{className:`winchester-chapel-portrait`,children:(0,N.jsx)(`img`,{src:Zc,width:1086,height:1448,decoding:`async`,alt:`Pencil illustration of Winchester College chapel`})})",
        "(e===`winchester`||window.__SCHOOL_SKETCHES__?.[e])&&(0,N.jsx)(`figure`,{className:`school-record-portrait school-record-portrait-${e}`,children:(0,N.jsx)(`img`,{src:window.__SCHOOL_SKETCHES__?.[e]?.src??Zc,width:window.__SCHOOL_SKETCHES__?.[e]?.width??1086,height:window.__SCHOOL_SKETCHES__?.[e]?.height??1448,decoding:`async`,alt:window.__SCHOOL_SKETCHES__?.[e]?.alt??`Pencil illustration of Winchester College chapel`})})",
        "school portrait render",
    )

    css = css.replace("winchester-chapel-portrait", "school-record-portrait")
    css = replace_once(
        css,
        ".school-record-portrait img{object-fit:contain;object-position:center;mix-blend-mode:normal;width:auto;max-width:100%;height:auto;max-height:100%;display:block;-webkit-mask-image:linear-gradient(#000 0% 86%,#0000 100%);mask-image:linear-gradient(#000 0% 86%,#0000 100%)}",
        ".school-record-portrait img{object-fit:contain;object-position:center;mix-blend-mode:normal;width:auto;max-width:100%;height:auto;max-height:100%;display:block}.school-record-portrait-winchester img{-webkit-mask-image:linear-gradient(#000 0% 86%,#0000 100%);mask-image:linear-gradient(#000 0% 86%,#0000 100%)}",
        "school portrait styles",
    )
    return css, javascript


def load_school_sketches() -> dict[str, dict[str, str | int]]:
    sketches: dict[str, dict[str, str | int]] = {}
    for school_id, spec in SCHOOL_SKETCH_SPECS.items():
        path = SKETCH_DIR / str(spec["filename"])
        if not path.exists():
            raise FileNotFoundError(f"School sketch is missing: {path}")
        encoded = base64.b64encode(path.read_bytes()).decode("ascii")
        sketches[school_id] = {
            "src": f"data:image/webp;base64,{encoded}",
            "width": int(spec["width"]),
            "height": int(spec["height"]),
            "alt": str(spec["alt"]),
        }
    return sketches


def serialise_query() -> str:
    pairs: list[tuple[str, str]] = []
    for key in st.query_params:
        for value in st.query_params.get_all(key):
            pairs.append((key, value))
    encoded = urlencode(pairs)
    return f"?{encoded}" if encoded else ""


frontend_css, frontend_js = extend_frontend_for_school_sketches(*load_frontend())
initial_query = serialise_query()
school_sketches = load_school_sketches()

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
  <script>
    window.__SCHOOLS_RECORD_QUERY__ = {json.dumps(initial_query)};
    window.__SCHOOL_SKETCHES__ = {json.dumps(school_sketches, ensure_ascii=False)};
  </script>
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
