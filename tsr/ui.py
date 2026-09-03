"""Shared chrome and HTML helpers."""

from __future__ import annotations

import html
import re
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterable, Sequence

import streamlit as st

from . import dataset
from .icons import icon

LAST_REVIEWED = "2 September 2026"
LAST_REVIEWED_SHORT = "2 Sep 2026"

BRAND_MARK = (Path(__file__).resolve().parents[1] / "assets" / "logo-mark.svg").read_text(encoding="utf-8")

NAV_ITEMS = (
    ("Schools", "/schools"),
    ("Compare", "/compare"),
    ("Methodology", "/methodology"),
    ("Evidence", "/evidence"),
    ("Professional", "/professional"),
)

ROUTE_PARAM = "p"


def esc(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def href(path: str) -> str:
    """Map an in-record path onto this deployment's query-string router."""
    if path.startswith("#") or path.startswith("http") or path.startswith("mailto:"):
        return path
    fragment = ""
    if "#" in path:
        path, fragment = path.split("#", 1)
        fragment = f"#{fragment}"
    if "?" in path:
        route, query = path.split("?", 1)
        return f"?{ROUTE_PARAM}={route}&{query}{fragment}"
    return f"?{ROUTE_PARAM}={path}{fragment}"


def link(path: str, label: str, css_class: str = "", attrs: str = "") -> str:
    classes = f' class="{css_class}"' if css_class else ""
    return f'<a{classes} href="{href(path)}" target="_self"{attrs}>{label}</a>'


_INDENT = re.compile(r"\s*\n\s*")


def write(markup: str) -> None:
    """Render a block of record markup into the page.

    Source indentation is collapsed first: Streamlit renders through a Markdown
    pass, which would otherwise treat indented markup as a code block.
    """
    st.markdown(
        f'<div class="tsr">{_INDENT.sub(" ", markup).strip()}</div>',
        unsafe_allow_html=True,
    )


@contextmanager
def controls(key: str):
    """A Streamlit container the record's stylesheet can target by key."""
    with st.container(key=key):
        yield


def header() -> str:
    nav = "".join(link(path, esc(label)) for label, path in NAV_ITEMS)
    return f"""
<header class="site-header">
  <a class="skip-link" href="#main-content">Skip to content</a>
  <div class="masthead shell">
    {link("/", f'<span class="wordmark-mark" aria-hidden="true">{BRAND_MARK}</span><span>The Schools Record</span>', "wordmark", ' aria-label="The Schools Record, home"')}
    <nav class="desktop-nav" aria-label="Primary navigation">{nav}</nav>
    <details class="mobile-menu"><summary>Menu</summary>
      <nav aria-label="Mobile navigation">{nav}</nav>
    </details>
  </div>
</header>"""


def footer() -> str:
    snapshot = esc(dataset.metadata()["snapshot_version"])
    items = (
        ("About", "/about"),
        ("Evidence centre", "/evidence"),
        ("Oxford and Cambridge records", "/oxbridge"),
        ("US university records", "/us-universities"),
        ("Corrections", "/corrections"),
        ("Privacy", "/privacy"),
        ("Terms", "/terms"),
        ("Changelog", "/changelog"),
    )
    nav = "".join(link(path, esc(label)) for label, path in items)
    return f"""
<footer class="site-footer">
  <div class="shell footer-grid">
    <div><strong>The Schools Record</strong><p>A source-led longitudinal record. Figures retain their original definitions and limits.</p></div>
    <nav aria-label="Footer navigation">{nav}</nav>
    <p class="footer-meta">Snapshot {snapshot}<br/>Last reviewed {LAST_REVIEWED}</p>
  </div>
</footer>"""


def breadcrumbs(items: Sequence[tuple[str, str | None]]) -> str:
    entries = []
    for label, path in items:
        if path:
            entries.append(f"<li>{link(path, esc(label))}</li>")
        else:
            entries.append(f'<li><span aria-current="page">{esc(label)}</span></li>')
    return f'<nav class="breadcrumbs" aria-label="Breadcrumb"><ol>{"".join(entries)}</ol></nav>'


ARTWORK_ALT = {
    "eton": "Pencil illustration of Eton College's collegiate courtyard and memorial",
    "westminster": "Pencil illustration of Westminster School's ivy-covered courtyard and Victoria Tower",
    "kcs": "Pencil illustration of King's College School Wimbledon",
    "st-pauls": "Pencil illustration of St Paul's School memorial pavilion",
    "spgs": "Pencil illustration of St Paul's Girls' School",
    "wycombe": "Pencil illustration of Wycombe Abbey beside the water",
    "winchester": "Pencil illustration of Winchester College chapel",
}


def artwork(school_id: str, decorative: bool = False, eager: bool = False) -> str:
    alt = "" if decorative else ARTWORK_ALT.get(school_id, "")
    loading = "eager" if eager else "lazy"
    priority = "high" if eager else "auto"
    base = "app/static/schools"
    return f"""<picture class="school-artwork artwork-{esc(school_id)}">
  <source media="(max-width: 520px)" srcset="{base}/{esc(school_id)}-480.webp"/>
  <source media="(max-width: 960px)" srcset="{base}/{esc(school_id)}-800.webp"/>
  <img src="{base}/{esc(school_id)}-1200.webp" width="1200" height="900" loading="{loading}" fetchpriority="{priority}" decoding="async" alt="{esc(alt)}"/>
</picture>"""


def arrow() -> str:
    return icon("arrow-right")


def page_hero(eyebrow: str, title: str, intro: str, note: str, note_tag: str = "p", note_class: str = "page-note") -> str:
    return f"""
<header class="page-hero">
  <div class="shell page-hero-grid">
    <div>
      <p class="eyebrow">{esc(eyebrow)}</p>
      <h1>{esc(title)}</h1>
      <p class="page-intro">{esc(intro)}</p>
    </div>
    <{note_tag} class="{note_class}">{note}</{note_tag}>
  </div>
</header>"""
