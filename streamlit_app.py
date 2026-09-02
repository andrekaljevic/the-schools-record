from __future__ import annotations

import base64
import gzip
import json
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components


APP_DIR = Path(__file__).resolve().parent
BUNDLE_DIR = APP_DIR / "bundle"
IMAGE_DIR = APP_DIR / "public" / "schools"
DEPLOYMENT_REVISION = "2026-09-02-data-frozen-public-rebuild"
SCHOOLS = ("eton", "westminster", "winchester", "kcs", "st-pauls", "spgs", "wycombe")

st.set_page_config(
    page_title="The Schools Record | Independent school results, year by year",
    page_icon="SR",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def read_gzip_text(filename: str) -> str:
    path = BUNDLE_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"The rebuilt public application asset is missing: {path}")
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        return handle.read()


def load_school_images() -> dict[str, dict[str, str | int]]:
    images: dict[str, dict[str, str | int]] = {}
    for school_id in SCHOOLS:
        path = IMAGE_DIR / f"{school_id}-480.webp"
        if not path.exists():
            raise FileNotFoundError(f"School artwork is missing: {path}")
        images[school_id] = {
            "src": f"data:image/webp;base64,{base64.b64encode(path.read_bytes()).decode('ascii')}",
            "width": 480,
            "height": 360,
        }
    return images


frontend_css = read_gzip_text("latest.css.gz")
frontend_js = read_gzip_text("latest.js.gz")
school_images = load_school_images()

# Protect the inline containers from literal closing tags in compiled output.
safe_css = frontend_css.replace("</style", "<\\/style")
safe_js = frontend_js.replace("</script", "<\\/script")

document = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
  <meta name="theme-color" content="#f4f1ea" />
  <meta name="description" content="A source-led longitudinal record of examination results and university outcomes from highly selective UK independent schools." />
  <title>The Schools Record | Independent school results, year by year</title>
  <style>
    html, body {{ margin: 0; min-height: 100%; overflow-x: hidden; background: #f4f1ea; }}
    {safe_css}
  </style>
</head>
<body>
  <div id="root"></div>
  <script>
    window.__STREAMLIT_EMBED__ = true;
    window.__SCHOOL_SKETCHES__ = {json.dumps(school_images, ensure_ascii=False)};
    window.__SCHOOLS_RECORD_DEPLOYMENT__ = {json.dumps(DEPLOYMENT_REVISION)};
  </script>
  <script type="module">{safe_js}</script>
  <script>
    (() => {{
      let lastHeight = 0;
      const resize = () => {{
        const height = Math.max(document.body.scrollHeight, document.documentElement.scrollHeight);
        if (height === lastHeight) return;
        lastHeight = height;
        window.parent.postMessage({{
          isStreamlitMessage: true,
          type: "streamlit:setFrameHeight",
          height: height + 2,
        }}, "*");
      }};
      new ResizeObserver(resize).observe(document.documentElement);
      window.addEventListener("load", resize);
      window.addEventListener("hashchange", () => window.setTimeout(resize, 50));
      [0, 100, 300, 1000, 2500].forEach((delay) => window.setTimeout(resize, delay));
    }})();
  </script>
</body>
</html>"""

st.markdown(
    """
    <style>
      html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
        background: #f4f1ea;
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
      [data-testid="stElementContainer"] { margin: 0 !important; }
      [data-testid="stIFrame"] iframe {
        display: block;
        width: 100%;
        border: 0;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

components.html(document, height=1200, scrolling=False)
