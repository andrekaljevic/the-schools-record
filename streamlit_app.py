"""The Schools Record — a native Streamlit application.

The published examination and university-outcome record is rendered directly by
Streamlit from the frozen production dataset in ``data/dataset.json``.  The
site's own stylesheet is reused, re-scoped so it cannot reach Streamlit's own
chrome; no compiled front-end bundle is loaded or embedded.
"""

from __future__ import annotations

import base64
import io
import re
import zipfile
from pathlib import Path

from PIL import Image
import streamlit as st

APP_DIR = Path(__file__).resolve().parent
PAYLOAD = APP_DIR / "native_payload.b64"
PAYLOAD_SENTINEL = APP_DIR / ".native-payload-99a40e6"


def _install_native_payload() -> None:
    if PAYLOAD_SENTINEL.exists():
        return
    raw = base64.b64decode(PAYLOAD.read_text(encoding="ascii"))
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        archive.extractall(APP_DIR)
    PAYLOAD_SENTINEL.write_text("99a40e66969e080e0753c7d894464aaf967d7040\n", encoding="ascii")


def _build_static_school_images() -> None:
    target = APP_DIR / "static" / "schools"
    expected = [target / f"{school}-{width}.webp" for school in ("eton", "westminster", "winchester", "kcs", "st-pauls", "spgs", "wycombe") for width in (480, 800, 1200)]
    if all(path.exists() for path in expected):
        return
    target.mkdir(parents=True, exist_ok=True)
    sketches = APP_DIR / "assets" / "school-sketches"
    smalls = APP_DIR / "public" / "schools"

    def flatten(image: Image.Image) -> Image.Image:
        image = image.convert("RGBA")
        ground = Image.new("RGBA", image.size, (255, 255, 255, 255))
        return Image.alpha_composite(ground, image).convert("RGB")

    for school in ("eton", "westminster", "winchester", "kcs", "st-pauls", "spgs", "wycombe"):
        small = flatten(Image.open(smalls / f"{school}-480.webp"))
        small.save(target / f"{school}-480.webp", "WEBP", quality=86, method=3)
        sketch = sketches / f"{school}.webp"
        if sketch.exists():
            large = flatten(Image.open(sketch))
            width, height = large.size
            large.save(target / f"{school}-1200.webp", "WEBP", quality=72, method=3)
            large.resize((800, round(height * 800 / width)), Image.LANCZOS).save(
                target / f"{school}-800.webp", "WEBP", quality=74, method=3
            )
        else:
            for width in (800, 1200):
                small.save(target / f"{school}-{width}.webp", "WEBP", quality=86, method=3)


_install_native_payload()
_build_static_school_images()

from tsr import forms, styles, ui
from tsr import views_compare, views_core, views_corrections, views_editorial

DEPLOYMENT_REVISION = "2026-09-02-native-streamlit-rebuild"

st.set_page_config(
    page_title="The Schools Record | Independent school results, year by year",
    page_icon="📗",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(styles.stylesheet(), unsafe_allow_html=True)

SIMPLE_ROUTES = {
    "/": views_core.home,
    "/schools": views_core.schools_index,
    "/compare": views_compare.compare,
    "/methodology": views_editorial.methodology,
    "/evidence": views_editorial.evidence,
    "/sample-dossier": views_editorial.sample_dossier,
    "/changelog": lambda: views_editorial.static_page("changelog"),
    "/about": lambda: views_editorial.static_page("about"),
    "/privacy": lambda: views_editorial.static_page("privacy"),
    "/terms": lambda: views_editorial.static_page("terms"),
}

EXAM_ROUTE = re.compile(r"^/schools/([^/]+)/exam-results$")
UNIVERSITY_ROUTE = re.compile(r"^/schools/([^/]+)/university-destinations$")
SCHOOL_ROUTE = re.compile(r"^/schools/([^/]+)$")


def current_route() -> str:
    raw = st.query_params.get(ui.ROUTE_PARAM) or "/"
    route = raw.split("#", 1)[0].split("?", 1)[0]
    if not route.startswith("/"):
        route = "/" + route
    if len(route) > 1 and route.endswith("/"):
        route = route.rstrip("/")
    return route or "/"


def render(route: str) -> None:
    handler = SIMPLE_ROUTES.get(route)
    if handler is not None:
        handler()
        return
    if route == "/professional":
        views_editorial.professional()
        forms.enquiry_form()
        return
    if route == "/corrections":
        views_corrections.corrections()
        return
    match = EXAM_ROUTE.match(route)
    if match and views_core.dataset_page(match.group(1), "exam"):
        return
    match = UNIVERSITY_ROUTE.match(route)
    if match and views_core.dataset_page(match.group(1), "university"):
        return
    match = SCHOOL_ROUTE.match(route)
    if match and views_core.school_record(match.group(1)):
        return
    views_core.not_found()


ui.write(ui.header())
render(current_route())
ui.write(ui.footer())
