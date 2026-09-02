"""The Schools Record — a native Streamlit application.

The published examination and university-outcome record is rendered directly by
Streamlit from the frozen production dataset in ``data/dataset.json``.  The
site's own stylesheet is reused, re-scoped so it cannot reach Streamlit's own
chrome; no compiled front-end bundle is loaded or embedded.
"""

from __future__ import annotations

import re

import streamlit as st

from deployment_bootstrap import ensure_runtime_assets

ensure_runtime_assets()

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
