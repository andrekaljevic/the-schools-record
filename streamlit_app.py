"""The Schools Record — a native Streamlit application.

The published examination and university-outcome record is rendered directly by
Streamlit from the frozen production dataset in ``data/dataset.json``.  The
site's own stylesheet is reused, re-scoped so it cannot reach Streamlit's own
chrome; no compiled front-end bundle is loaded or embedded.
"""

from __future__ import annotations

import re
from pathlib import Path

import streamlit as st

from tsr import forms, meta, styles, ui
from tsr import (
    views_compare,
    views_core,
    views_corpora,
    views_corrections,
    views_editorial,
    views_evidence,
)

DEPLOYMENT_REVISION = "2026-09-02-native-parity-restoration"

FAVICON = Path(__file__).resolve().parent / "assets" / "logo-mark.svg"


def current_route() -> str:
    raw = st.query_params.get(ui.ROUTE_PARAM) or "/"
    route = raw.split("#", 1)[0].split("?", 1)[0]
    if not route.startswith("/"):
        route = "/" + route
    if len(route) > 1 and route.endswith("/"):
        route = route.rstrip("/")
    return route or "/"


ROUTE = current_route()

st.set_page_config(
    page_title=meta.for_route(ROUTE)["title"],
    page_icon=str(FAVICON),
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(styles.stylesheet(), unsafe_allow_html=True)

SIMPLE_ROUTES = {
    "/": views_core.home,
    "/schools": views_core.schools_index,
    "/compare": views_compare.compare,
    "/methodology": views_editorial.methodology,
    "/evidence": views_evidence.evidence_centre,
    "/oxbridge": views_corpora.oxbridge,
    "/us-universities": views_corpora.us_universities,
    "/corrections": views_corrections.corrections,
    "/corrections/report": views_corrections.report,
    "/sample-dossier": views_editorial.sample_dossier,
    "/changelog": lambda: views_editorial.static_page("changelog"),
    "/about": lambda: views_editorial.static_page("about"),
    "/privacy": lambda: views_editorial.static_page("privacy"),
    "/terms": lambda: views_editorial.static_page("terms"),
}

SCHOOL_PAGE = re.compile(r"^/schools/([^/]+)/(exam-results|university-destinations|oxbridge|us-universities|school-entry)$")
SCHOOL_ROUTE = re.compile(r"^/schools/([^/]+)$")


def render(route: str) -> None:
    handler = SIMPLE_ROUTES.get(route)
    if handler is not None:
        handler()
        return
    if route == "/professional":
        views_editorial.professional()
        forms.enquiry_form()
        return
    match = SCHOOL_PAGE.match(route)
    if match:
        slug, page = match.groups()
        if page == "exam-results" and views_core.dataset_page(slug, "exam"):
            return
        if page == "university-destinations" and views_core.dataset_page(slug, "university"):
            return
        if page == "oxbridge" and views_core.find_school(slug):
            views_corpora.oxbridge(slug)
            return
        if page == "us-universities" and views_core.find_school(slug):
            views_corpora.us_universities(slug)
            return
        if page == "school-entry" and views_corpora.school_entry(slug):
            return
    match = SCHOOL_ROUTE.match(route)
    if match and views_core.school_record(match.group(1)):
        return
    views_core.not_found()


ui.write(ui.header())
render(ROUTE)
ui.write(ui.footer())
st.iframe(meta.head_script(ROUTE), height=1)
