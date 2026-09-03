"""Stylesheet handling.

``assets/site.css`` is the published site's own stylesheet, reused verbatim as
the source of truth for the design.  Because a Streamlit page shares one DOM
with Streamlit's own chrome, every rule is re-scoped under ``.tsr`` before it is
injected, so the site's Tailwind preflight cannot reach Streamlit's widgets.
"""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE_CSS = ROOT / "assets" / "site.css"

SCOPE = ".tsr"

# At-rules whose bodies are declarations or frames, not selector rules.
_LEAF_AT_RULES = ("@keyframes", "@font-face", "@property", "@page", "@counter-style")

_ROOT_SELECTORS = {"html", "body", ":host", ":root", "*"}


def _scope_selector(selector: str) -> str:
    selector = selector.strip()
    if not selector or selector.startswith("%"):
        return selector
    if selector.startswith("@"):
        return selector
    parts = []
    for single in selector.split(","):
        single = single.strip()
        if not single:
            continue
        if single in ("html", "body", ":host", ":root"):
            parts.append(SCOPE)
        elif single == "*":
            parts.append(f"{SCOPE}, {SCOPE} *")
        elif single.startswith(("::", ":before", ":after", "::backdrop")):
            parts.append(f"{SCOPE} {single}")
        elif re.match(r"^(html|body|:root|:host)([:.\[ >~+])", single):
            head = re.match(r"^(html|body|:root|:host)", single).group(0)
            parts.append(SCOPE + single[len(head):] if single[len(head)] in ":." else f"{SCOPE} {single[len(head):].strip()}")
        else:
            parts.append(f"{SCOPE} {single}")
    return ", ".join(dict.fromkeys(parts))


def _strip_comments(css: str) -> str:
    return re.sub(r"/\*.*?\*/", "", css, flags=re.S)


def scope_css(css: str, scope: str = SCOPE) -> str:
    """Rewrite every selector in ``css`` so it only matches inside ``scope``."""
    css = _strip_comments(css)
    out: list[str] = []
    index = 0
    length = len(css)
    at_stack: list[bool] = []  # True when the current block is a leaf at-rule body

    while index < length:
        char = css[index]
        if char == "}":
            if at_stack:
                at_stack.pop()
            out.append("}")
            index += 1
            continue
        if char in " \n\t\r":
            out.append(char)
            index += 1
            continue

        brace = css.find("{", index)
        semi = css.find(";", index)
        if brace == -1 and semi == -1:
            out.append(css[index:])
            break
        if semi != -1 and (brace == -1 or semi < brace):
            # A standalone statement such as @charset or @import.
            out.append(css[index:semi + 1])
            index = semi + 1
            continue

        prelude = css[index:brace]
        stripped = prelude.strip()
        inside_leaf = any(at_stack)
        if stripped.startswith("@") or inside_leaf:
            is_leaf = stripped.startswith(_LEAF_AT_RULES) or inside_leaf
            at_stack.append(is_leaf)
            out.append(prelude + "{")
        else:
            out.append(_scope_selector(prelude) + "{")
            at_stack.append(False)
            # A plain rule body contains declarations only: copy it verbatim.
            close = css.find("}", brace)
            out.append(css[brace + 1:close])
            out.append("}")
            at_stack.pop()
            index = close + 1
            continue
        index = brace + 1

    return "".join(out)


@lru_cache(maxsize=1)
def site_css() -> str:
    return scope_css(SITE_CSS.read_text(encoding="utf-8"))


# Streamlit's own chrome is removed so the record occupies the full page, and
# the widgets that carry real interaction are restyled to match the record.
APP_CSS = """
:root {
  color-scheme: light;
  --tsr-paper: #f3f0e8;
  --tsr-paper-pale: #faf8f3;
  --tsr-paper-deep: #e8e2d6;
  --tsr-ink: #172322;
  --tsr-ink-soft: #41514e;
  --tsr-teal: #125c58;
  --tsr-teal-dark: #0b3f3c;
  --tsr-line: #c9c0b0;
  --tsr-line-dark: #8b8172;
  --tsr-white: #fffefa;
  --tsr-serif: Georgia, "Times New Roman", Times, serif;
  --tsr-shell: min(100% - 3rem, 1240px);
}
/* The published stylesheet narrows the shell gutter on phones; keep the
   widget containers on the same edge. */
@media (width<=720px) { :root { --tsr-shell: min(100% - 2rem, 1240px); } }
html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"],
[data-testid="stBottomBlockContainer"], .stApp {
  background: var(--tsr-paper) !important;
}
[data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"],
[data-testid="stStatusWidget"], [data-testid="stSidebarCollapsedControl"],
[data-testid="stAppDeployButton"], #MainMenu { display: none !important; }
[data-testid="stMainBlockContainer"], .block-container {
  padding: 0 !important;
  max-width: 100% !important;
  width: 100% !important;
}
[data-testid="stMain"] > [data-testid="stVerticalBlockBorderWrapper"] > div > [data-testid="stVerticalBlock"] { gap: 0 !important; }
[data-testid="stElementContainer"] { margin: 0 !important; }
/* The metadata frame only writes into the document head; keep it out of the layout. */
[data-testid="stIFrame"], iframe[title="st.iframe"] { position: absolute !important; width: 1px !important; height: 1px !important; opacity: 0; pointer-events: none; border: 0; }

/* Streamlit turns raw headings into its own anchored heading component; keep
   the record's own layout and drop the injected hover anchors. */
.tsr [data-testid="stHeadingWithActionElements"] { display: contents !important; }
.tsr [data-testid="stHeaderActionElements"] { display: none !important; }
.tsr h1, .tsr h2, .tsr h3, .tsr h4 { scroll-margin-top: 1.5rem; }
.tsr .tsr-anchor { display: block; height: 0; scroll-margin-top: 1.5rem; }

/* The wordmark's mark is now a drawn brand SVG, not a bordered initials box. */
.tsr .wordmark-mark { border: none !important; width: 34px !important; }
.tsr .wordmark-mark svg { width: 100%; height: 100%; display: block; }

/* Links inside the record follow the record's stylesheet, not Streamlit's. */
.tsr a { text-decoration: inherit !important; }
.tsr .evidence-button, .tsr .index-row h2 a:hover,
.tsr .prose a:not(.button):not(.text-link) { text-decoration: underline !important; }
.tsr .tsr-tight-top { padding-top: 0 !important; }
.tsr .index-search-label { margin-bottom: 0; }
.tsr .school-index-shell { padding-bottom: 1.2rem; }

/* Record-styled disclosure in place of the published site's modal dialog. */
.tsr .evidence-disclosure > summary { list-style: none; cursor: pointer; }
.tsr .evidence-disclosure > summary::-webkit-details-marker { display: none; }
.tsr .evidence-panel {
  border: 1px solid var(--tsr-line-dark);
  background: var(--tsr-paper-pale);
  text-align: left;
  margin-top: 0.6rem;
  min-width: 320px;
}
.tsr .evidence-panel .dialog-heading { padding: 1rem 1.1rem; }
.tsr .evidence-panel .dialog-heading h2 { font-size: 1.35rem; }
.tsr .evidence-panel .evidence-definition-list { padding: 1rem 1.1rem; }
.tsr .evidence-panel .dialog-privacy-note { margin: 0 1.1rem; }
.tsr .evidence-panel .dialog-actions { padding: 1.1rem; }

/* --- Widget containers ------------------------------------------------- */
.st-key-tsr-search, .st-key-tsr-compare, .st-key-tsr-view,
.st-key-tsr-enquiry-form, .st-key-tsr-correction-form, .st-key-tsr-correction-layout {
  width: var(--tsr-shell) !important;
  margin-inline: auto !important;
  font-family: var(--tsr-serif);
}
/* The index controls sit on the shell's left edge, up to 670px wide.  The
   offset is a margin computed from the shell's own centring, never padding:
   padding counted inside the capped width and squeezed the controls to
   nothing on wide screens. */
.st-key-tsr-search, .st-key-tsr-index-series {
  width: min(670px, var(--tsr-shell)) !important;
  margin-inline: calc((100% - var(--tsr-shell)) / 2) 0 !important;
}
.st-key-tsr-search [data-testid="stTextInputRootElement"],
.st-key-tsr-search .react-aria-TextField > div,
.st-key-tsr-search div[data-baseweb="input"] {
  border-radius: 0 !important;
  border: 1px solid var(--tsr-line-dark) !important;
  background: var(--tsr-paper-pale) !important;
}
.st-key-tsr-search input {
  min-height: 56px !important;
  font-family: var(--tsr-serif) !important;
  font-size: 1.05rem !important;
  color: var(--tsr-ink) !important;
  background: transparent !important;
}
.st-key-tsr-compare {
  border: 1px solid var(--tsr-line-dark);
  background: var(--tsr-paper-pale);
  padding: 1rem;
  margin-top: clamp(3rem, 6vw, 5.5rem) !important;
}
.st-key-tsr-view { margin-top: 1.6rem !important; margin-bottom: 0.9rem !important; }
.st-key-tsr-view [role="radiogroup"] label p { text-transform: none !important; letter-spacing: 0 !important; font-size: 0.72rem !important; }
.tsr .tsr-result-section { padding-bottom: clamp(4.5rem, 8vw, 8.5rem); }
.st-key-tsr-compare .stSelectbox [data-testid="stWidgetLabel"] p,
.st-key-tsr-compare .stNumberInput [data-testid="stWidgetLabel"] p,
.st-key-tsr-enquiry-form .stTextInput [data-testid="stWidgetLabel"] p,
.st-key-tsr-enquiry-form .stSelectbox [data-testid="stWidgetLabel"] p,
.st-key-tsr-enquiry-form .stTextArea [data-testid="stWidgetLabel"] p,
.st-key-tsr-correction-form .stTextInput [data-testid="stWidgetLabel"] p,
.st-key-tsr-correction-form .stSelectbox [data-testid="stWidgetLabel"] p,
.st-key-tsr-correction-form .stTextArea [data-testid="stWidgetLabel"] p {
  color: var(--tsr-ink-soft) !important;
  letter-spacing: 0.05em !important;
  text-transform: uppercase !important;
  font-size: 0.68rem !important;
  font-weight: 800 !important;
}
.st-key-tsr-compare div[data-baseweb="select"] > div,
.st-key-tsr-compare div[data-testid="stNumberInputContainer"],
.st-key-tsr-compare [data-testid="stTextInputRootElement"],
.st-key-tsr-enquiry-form div[data-baseweb="select"] > div,
.st-key-tsr-enquiry-form [data-testid="stTextInputRootElement"],
.st-key-tsr-enquiry-form [data-baseweb="textarea"],
.st-key-tsr-correction-form div[data-baseweb="select"] > div,
.st-key-tsr-correction-form [data-testid="stTextInputRootElement"],
.st-key-tsr-correction-form [data-baseweb="textarea"] {
  border-radius: 0 !important;
  border: 1px solid var(--tsr-line-dark) !important;
  background: var(--tsr-white) !important;
  min-height: 46px !important;
}
.st-key-tsr-compare input, .st-key-tsr-compare div[data-baseweb="select"],
.st-key-tsr-enquiry-form input, .st-key-tsr-enquiry-form textarea,
.st-key-tsr-correction-form input, .st-key-tsr-correction-form textarea {
  font-family: var(--tsr-serif) !important;
  color: var(--tsr-ink) !important;
}
.st-key-tsr-view [role="radiogroup"] {
  border: 1px solid var(--tsr-line-dark);
  gap: 0 !important;
}
.st-key-tsr-view [role="radiogroup"] label { padding: 0.45rem 0.8rem !important; margin: 0 !important; }
.st-key-tsr-view button, .tsr-download button,
.st-key-tsr-enquiry-form button, .st-key-tsr-correction-form button {
  border-radius: 3px !important;
  font-family: var(--tsr-serif) !important;
  font-weight: 800 !important;
}
.st-key-tsr-view [data-testid="stDownloadButton"] button {
  border: 1px solid var(--tsr-line-dark) !important;
  background: var(--tsr-paper-pale) !important;
  color: var(--tsr-ink) !important;
  min-height: 44px !important;
}
.st-key-tsr-enquiry-form [data-testid="stFormSubmitButton"] button,
.st-key-tsr-correction-form [data-testid="stFormSubmitButton"] button {
  border: 1px solid var(--tsr-teal-dark) !important;
  background: var(--tsr-teal-dark) !important;
  color: var(--tsr-white) !important;
  min-height: 48px !important;
}
.st-key-tsr-enquiry-form [data-testid="stForm"],
.st-key-tsr-correction-form [data-testid="stForm"] {
  border: 1px solid var(--tsr-line-dark) !important;
  border-radius: 0 !important;
  background: var(--tsr-paper-pale) !important;
  padding: clamp(1.2rem, 3vw, 1.8rem) !important;
}
.st-key-tsr-enquiry-form .stCheckbox p,
.st-key-tsr-correction-form .stCheckbox p {
  font-family: var(--tsr-serif) !important;
  font-size: 0.82rem !important;
  color: var(--tsr-ink-soft) !important;
  text-transform: none !important;
  letter-spacing: 0 !important;
  font-weight: 400 !important;
}
.st-key-tsr-enquiry-form, .st-key-tsr-correction-form {
  width: min(100% - 3rem, 850px) !important;
  padding-bottom: clamp(3rem, 6vw, 5rem);
}
.st-key-tsr-correction-layout { padding-block: clamp(4.5rem, 8vw, 8.5rem); }
.st-key-tsr-correction-form { width: 100% !important; padding-bottom: 0; }
.st-key-tsr-enquiry-form [data-baseweb="select"] > div > div,
.st-key-tsr-enquiry-form textarea,
.st-key-tsr-correction-form [data-baseweb="select"] > div > div,
.st-key-tsr-correction-form textarea,
.st-key-tsr-compare [data-baseweb="select"] > div > div {
  background: var(--tsr-white) !important;
}
.tsr .tsr-flush-bottom { padding-bottom: 0 !important; }

/* --- Small-multiple panels ------------------------------------------------ */
/* The index and school-record panels reuse the comparison chart's inks and
   mono axis labels; they are inline SVG, so they scale with their column. */
.tsr .record-panel { width: 100%; height: auto; display: block; overflow: visible; }
.tsr .panel-label { fill: #5b6865; font-family: var(--mono); }
.tsr .panel-band { fill: var(--paper-deep); }
.tsr .panel-rule { stroke: var(--line-dark); stroke-width: 1px; stroke-dasharray: 3 3; }
.tsr .panel-marker-label { fill: #5b6865; font-family: var(--mono); font-size: 0.82em; letter-spacing: 0.04em; }
.tsr .chart-values { margin-top: 0.5rem; }
.tsr .chart-values > summary {
  cursor: pointer; list-style: none; display: inline-block;
  color: var(--tsr-teal); font-size: 0.72rem; font-weight: 700;
  text-decoration: underline !important; text-underline-offset: 0.18em;
}
.tsr .chart-values > summary::-webkit-details-marker { display: none; }
.tsr .chart-values .table-scroll { margin-top: 0.6rem; }
.tsr .chart-values .data-table, .tsr .chart-values .data-table th, .tsr .chart-values .data-table td { min-width: 0; }
.tsr .series-colour[style] { flex: none; }

/* Index rows: the chart and the key figures share the right-hand column. */
.tsr .index-row-charted {
  grid-template-columns: 68px minmax(0, 1fr) minmax(340px, 0.72fr) 48px;
  grid-template-rows: auto auto;
  align-items: start;
  row-gap: 0.9rem;
}
.tsr .index-row-charted > .index-letter-cell { grid-area: 1 / 1 / 3 / 2; align-self: center; }
.tsr .index-row-charted > .index-copy { grid-area: 1 / 2 / 3 / 3; align-self: center; }
.tsr .index-row-charted > .index-panel { grid-area: 1 / 3 / 2 / 4; }
.tsr .index-row-charted > dl { grid-area: 2 / 3 / 3 / 4; }
.tsr .index-row-charted > .row-action { grid-area: 1 / 4 / 3 / 5; align-self: center; }
.tsr .index-panel { border: 1px solid var(--tsr-line); background: var(--tsr-paper-pale); padding: 0.8rem 0.8rem 0.7rem; min-width: 0; }
.tsr .index-panel-caption {
  display: flex; flex-wrap: wrap; gap: 0.2rem 0.7rem; align-items: baseline;
  margin: 0.4rem 0 0; font-size: 0.7rem; color: var(--tsr-ink-soft);
}
.tsr .index-panel-latest { font: 700 1.15rem/1 var(--mono); color: var(--tsr-ink); font-variant-numeric: tabular-nums; }
.tsr .index-panel-status { margin: 0.25rem 0 0; font-size: 0.68rem; color: var(--tsr-ink-soft); }
.tsr .index-panel-empty { min-height: 120px; display: grid; align-content: center; }
.tsr .index-panel-empty p { margin: 0; font-size: 0.78rem; color: var(--tsr-ink-soft); }
.tsr .index-panel-empty strong { color: var(--tsr-ink); }
.tsr .index-series-note { max-width: 780px; margin: 0.9rem 0 0; }
.tsr .index-series-note p { margin: 0 0 0.35rem; font-size: 0.8rem; color: var(--tsr-ink-soft); }
.tsr .index-series-note p:first-child { font-size: 0.92rem; color: var(--tsr-ink); }
.tsr .index-series-note .text-link { font-size: 0.8rem; }
.st-key-tsr-index-series { margin-top: 1.4rem !important; }
.st-key-tsr-index-series .stSelectbox [data-testid="stWidgetLabel"] p {
  color: var(--tsr-teal) !important; letter-spacing: 0.18em !important; text-transform: uppercase !important;
  font-size: 0.71rem !important; font-weight: 800 !important; font-family: var(--tsr-serif) !important;
}
.st-key-tsr-index-series div[data-baseweb="select"] > div {
  border-radius: 0 !important; border: 1px solid var(--tsr-line-dark) !important;
  background: var(--tsr-paper-pale) !important; min-height: 50px !important;
}
.st-key-tsr-index-series div[data-baseweb="select"], .st-key-tsr-index-series [data-baseweb="select"] > div > div {
  font-family: var(--tsr-serif) !important; color: var(--tsr-ink) !important; background: var(--tsr-paper-pale) !important;
}
@media (width<=980px) {
  .tsr .index-row-charted { grid-template-columns: 58px minmax(0, 1fr) 48px; grid-template-rows: auto auto auto; }
  .tsr .index-row-charted > .index-letter-cell { grid-area: 1 / 1 / 2 / 2; align-self: start; }
  .tsr .index-row-charted > .index-copy { grid-area: 1 / 2 / 2 / 3; align-self: start; }
  .tsr .index-row-charted > .index-panel { grid-area: 2 / 2 / 3 / 3; }
  .tsr .index-row-charted > dl { grid-area: 3 / 2 / 4 / 3; }
  .tsr .index-row-charted > .row-action { grid-area: 1 / 3 / 2 / 4; align-self: start; }
}
@media (width<=720px) {
  .tsr .index-row-charted { grid-template-columns: 44px minmax(0, 1fr) 44px; }
  .tsr .index-row-charted > .index-panel { grid-area: 2 / 2 / 3 / 4; }
  .tsr .index-row-charted > dl { grid-area: 3 / 2 / 4 / 4; }
}

/* School record: results by year, one panel per ruler, shared year axis. */
.tsr .trajectory-section { padding-top: 0; }
.tsr .trajectory-section .section-heading p:last-child { max-width: 46ch; color: var(--tsr-ink-soft); font-size: 0.86rem; margin: 0; }
.tsr .trajectory-grid { display: grid; grid-template-columns: minmax(0, 1.5fr) minmax(270px, 0.5fr); gap: 3rem; align-items: start; }
.tsr .trajectory-panels { display: grid; gap: 1.5rem; min-width: 0; }
.tsr .trajectory-panel { border: 1px solid var(--tsr-line-dark); background: var(--tsr-paper-pale); padding: clamp(1rem, 3vw, 1.6rem); min-width: 0; }
.tsr .trajectory-panel > header {
  display: flex; justify-content: space-between; align-items: baseline; flex-wrap: wrap; gap: 0.4rem 1.5rem;
  border-bottom: 1px solid var(--tsr-line); padding-bottom: 0.9rem; margin-bottom: 0.2rem;
}
.tsr .trajectory-panel h3 { font-size: 1.7rem; line-height: 1.1; margin: 0; }
.tsr .trajectory-panel .eyebrow { margin-bottom: 0.45rem; }
.tsr .trajectory-panel .panel-denominator { margin: 0; font-size: 0.74rem; color: var(--tsr-ink-soft); font-variant-numeric: tabular-nums; }
.tsr .trajectory-panel .series-legend { margin: 0.9rem 0 0.3rem; }
.tsr .trajectory-footnote { margin: 0.6rem 0 0; font-size: 0.72rem; color: var(--tsr-ink-soft); }
.tsr .panel-mobile { display: none; }
.tsr .trajectory-aside { border: 1px solid var(--tsr-line-dark); background: var(--tsr-paper-pale); padding: 2rem; position: sticky; top: 1.5rem; }
.tsr .trajectory-aside h2 { font-size: 2.1rem; margin-bottom: 1.2rem; }
.tsr .trajectory-aside p, .tsr .trajectory-aside li { color: var(--tsr-ink-soft); font-size: 0.84rem; }
.tsr .trajectory-aside p strong { color: var(--tsr-ink); }
.tsr .trajectory-aside ul { padding-left: 1.1rem; margin: 0.5rem 0 1rem; }
.tsr .trajectory-aside .text-link { margin-top: 0.5rem; }
@media (width<=980px) {
  .tsr .trajectory-grid { grid-template-columns: 1fr; gap: 1.5rem; }
  .tsr .trajectory-aside { position: static; }
}
@media (width<=720px) {
  .tsr .panel-desktop { display: none; }
  .tsr .panel-mobile { display: block; }
  .tsr .trajectory-panel h3 { font-size: 1.4rem; }
}

/* --- Sources, ledgers and indexes ------------------------------------------ */
.tsr .source-list { list-style: none; margin: 0; padding: 0; display: grid; gap: 0.45rem; }
.tsr .source-list li { display: grid; grid-template-columns: auto minmax(0, 1fr); gap: 0.25rem 0.7rem; align-items: baseline; font-size: 0.78rem; }
.tsr .source-key { font: 700 0.68rem var(--mono); color: var(--tsr-ink-soft); background: var(--tsr-paper-deep); padding: 0.1rem 0.4rem; white-space: nowrap; }
.tsr .source-link { color: var(--tsr-teal); font-weight: 700; display: inline-flex; align-items: center; gap: 0.3rem; text-decoration: underline !important; text-underline-offset: 0.18em; }
.tsr .source-link svg { width: 0.9em; height: 0.9em; }
.tsr .source-withheld { color: var(--tsr-ink-soft); font-style: italic; }
.tsr .source-role { grid-column: 2; color: var(--tsr-ink-soft); font-size: 0.72rem; }
.tsr .source-none { margin: 0; color: var(--tsr-ink-soft); font-size: 0.78rem; }
.tsr .dataset-sources { margin-top: 0.9rem; }
.tsr .dataset-sources > summary { cursor: pointer; list-style: none; display: inline-block; color: var(--tsr-teal); font-size: 0.74rem; font-weight: 800; text-decoration: underline !important; text-underline-offset: 0.18em; min-height: 32px; }
.tsr .dataset-sources > summary::-webkit-details-marker { display: none; }
.tsr .dataset-sources[open] > summary { margin-bottom: 0.6rem; }
.tsr .data-table .total-row th, .tsr .data-table .total-row td { font-weight: 800; background: var(--tsr-paper-deep); }
.tsr .data-table .cell-note { text-align: left; min-width: 220px; max-width: 420px; font-size: 0.72rem; color: var(--tsr-ink-soft); white-space: normal; }
.tsr .data-table tr[id] { scroll-margin-top: 1.5rem; }
.tsr .trace-link { font-size: 0.7rem; white-space: nowrap; }
.tsr .series-index-section { padding-bottom: 2.5rem; }
.tsr .series-index { border-top: 1px solid var(--tsr-line-dark); padding-top: 1.2rem; margin-bottom: 1.5rem; }
.tsr .series-index ol { list-style: none; margin: 0; padding: 0; display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 0.6rem; }
.tsr .series-index a { display: grid; gap: 0.2rem; border: 1px solid var(--tsr-line); background: var(--tsr-paper-pale); padding: 0.8rem 0.9rem; min-height: 44px; }
.tsr .series-index a:hover { border-color: var(--tsr-teal); }
.tsr .series-index strong { font-family: var(--tsr-serif); font-size: 1.05rem; line-height: 1.2; color: var(--tsr-ink); }
.tsr .series-family { color: var(--tsr-teal); letter-spacing: 0.12em; text-transform: uppercase; font-size: 0.62rem; font-weight: 800; }
.tsr .series-meta { color: var(--tsr-ink-soft); font: 700 0.7rem var(--mono); }
.tsr .granular-heading { margin-top: 4rem; }
.tsr .latest-footnote a { color: var(--tsr-teal); font-weight: 700; text-decoration: underline !important; }
.tsr .latest-values { grid-template-columns: repeat(4, 1fr); }
.tsr .inventory-table th[scope="row"] { text-align: left; font-weight: 700; }
.tsr .inventory-table th[scope="row"] a { color: var(--tsr-teal); text-decoration: underline !important; text-underline-offset: 0.18em; }
.tsr .inventory-table td:first-child { text-align: left; }
.tsr .record-inventory { margin-top: 2.5rem; }

/* --- Home inventory and route cards ----------------------------------------- */
.tsr .inventory-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1.15rem; }
.tsr .inventory-card { border: 1px solid var(--tsr-line); background: var(--tsr-paper-pale); padding: 1.4rem; display: grid; align-content: start; gap: 0.5rem; }
.tsr .inventory-card .eyebrow { margin-bottom: 0.2rem; }
.tsr .inventory-card p { margin: 0; color: var(--tsr-ink-soft); font-size: 0.84rem; }
.tsr .inventory-figure { font: 700 2.4rem/1 var(--mono); color: var(--tsr-ink) !important; font-variant-numeric: tabular-nums; }
.tsr .inventory-note { margin: 1.4rem 0 0; color: var(--tsr-ink-soft); font-size: 0.84rem; }
.tsr .inventory-note a { color: var(--tsr-teal); font-weight: 700; text-decoration: underline !important; }
.tsr .route-card-grid-wide { grid-template-columns: repeat(3, 1fr); }
.tsr .route-card-grid-wide .route-card h2 { font-size: 2.1rem; max-width: none; }
.tsr .route-card-grid-wide .route-card > p:not(.eyebrow) { font-size: 0.86rem; }
.tsr .route-card-grid-wide .route-card .text-link { display: flex; margin-top: 0.6rem; }

/* --- Evidence centre -------------------------------------------------------- */
.tsr .evidence-head { padding-top: 2.5rem; }
.tsr .evidence-inventory { display: grid; grid-template-columns: repeat(5, 1fr); border: 1px solid var(--tsr-line-dark); background: var(--tsr-paper-pale); }
.tsr .evidence-inventory a { display: grid; gap: 0.3rem; padding: 1rem 1.1rem; border-right: 1px solid var(--tsr-line); text-decoration: none !important; }
.tsr .evidence-inventory a:last-child { border-right: 0; }
.tsr .evidence-inventory a:hover { background: var(--tsr-paper-deep); }
.tsr .evidence-inventory strong { font: 700 1.6rem/1 var(--mono); color: var(--tsr-ink); font-variant-numeric: tabular-nums; }
.tsr .evidence-inventory span { color: var(--tsr-ink-soft); font-size: 0.72rem; }
.tsr .evidence-sections { display: flex; flex-wrap: wrap; gap: 0; margin-top: 1.8rem; border-bottom: 1px solid var(--tsr-line-dark); }
.tsr .evidence-sections a { padding: 0.75rem 1.1rem; min-height: 44px; display: inline-flex; align-items: center; font-weight: 800; font-size: 0.8rem; color: var(--tsr-ink-soft); border-bottom: 3px solid transparent; margin-bottom: -1px; }
.tsr .evidence-sections a[aria-current="page"] { color: var(--tsr-ink); border-bottom-color: var(--tsr-teal); }
.st-key-tsr-evidence, .st-key-tsr-corpus {
  width: var(--tsr-shell) !important; margin-inline: auto !important; font-family: var(--tsr-serif);
  border: 1px solid var(--tsr-line-dark); background: var(--tsr-paper-pale); padding: 1rem; margin-top: 1.5rem !important;
}
.st-key-tsr-evidence .stSelectbox [data-testid="stWidgetLabel"] p, .st-key-tsr-evidence .stNumberInput [data-testid="stWidgetLabel"] p, .st-key-tsr-evidence .stTextInput [data-testid="stWidgetLabel"] p,
.st-key-tsr-corpus .stSelectbox [data-testid="stWidgetLabel"] p, .st-key-tsr-corpus .stNumberInput [data-testid="stWidgetLabel"] p {
  color: var(--tsr-ink-soft) !important; letter-spacing: 0.05em !important; text-transform: uppercase !important; font-size: 0.68rem !important; font-weight: 800 !important;
}
.st-key-tsr-evidence div[data-baseweb="select"] > div, .st-key-tsr-evidence div[data-testid="stNumberInputContainer"], .st-key-tsr-evidence [data-testid="stTextInputRootElement"],
.st-key-tsr-corpus div[data-baseweb="select"] > div, .st-key-tsr-corpus div[data-testid="stNumberInputContainer"] {
  border-radius: 0 !important; border: 1px solid var(--tsr-line-dark) !important; background: var(--tsr-white) !important; min-height: 46px !important;
}
.st-key-tsr-evidence input, .st-key-tsr-evidence div[data-baseweb="select"], .st-key-tsr-corpus input, .st-key-tsr-corpus div[data-baseweb="select"] { font-family: var(--tsr-serif) !important; color: var(--tsr-ink) !important; }
.st-key-tsr-evidence [data-baseweb="select"] > div > div, .st-key-tsr-corpus [data-baseweb="select"] > div > div { background: var(--tsr-white) !important; }
.tsr .evidence-results { padding-top: 1.2rem; padding-bottom: clamp(4.5rem, 8vw, 8.5rem); }
.tsr .evidence-list { display: grid; gap: 1rem; }
.tsr .evidence-record { border: 1px solid var(--tsr-line-dark); background: var(--tsr-paper-pale); padding: 1.2rem 1.3rem; scroll-margin-top: 1.5rem; }
.tsr .evidence-record header h3 { font-size: 1.35rem; line-height: 1.2; margin: 0.4rem 0 0.3rem; }
.tsr .record-kicker { display: flex; flex-wrap: wrap; gap: 0.5rem 0.8rem; align-items: center; font-size: 0.72rem; color: var(--tsr-ink-soft); }
.tsr .record-line { margin: 0; font-size: 0.8rem; color: var(--tsr-ink-soft); }
.tsr .record-line a { color: var(--tsr-teal); font-weight: 700; }
.tsr .record-status { white-space: normal; }
.tsr .record-summary { display: flex; flex-wrap: wrap; gap: 0.4rem 1.6rem; margin: 0.9rem 0 0; }
.tsr .record-summary div { display: grid; gap: 0.15rem; }
.tsr .record-summary dt { color: var(--tsr-ink-soft); text-transform: uppercase; letter-spacing: 0.06em; font-size: 0.62rem; }
.tsr .record-summary dd { margin: 0; font: 700 1rem/1.1 var(--mono); font-variant-numeric: tabular-nums; }
.tsr .record-details { margin-top: 0.9rem; }
.tsr .record-details > summary { cursor: pointer; list-style: none; display: inline-block; color: var(--tsr-teal); font-size: 0.74rem; font-weight: 800; text-decoration: underline !important; text-underline-offset: 0.18em; min-height: 32px; }
.tsr .record-details > summary::-webkit-details-marker { display: none; }
.tsr .record-details .evidence-definition-list { padding: 0.8rem 0 0; }
.tsr .record-details .evidence-definition-list div { grid-template-columns: 220px 1fr; }
.tsr .record-note { margin: 0.6rem 0 0; font-size: 0.78rem; color: var(--tsr-ink-soft); }
.tsr .record-sources { margin-top: 1rem; }
.tsr .record-sources .eyebrow { margin-bottom: 0.5rem; }
.tsr .record-actions { display: flex; flex-wrap: wrap; gap: 0.6rem 1.6rem; margin-top: 1rem; }
.tsr .record-focus { border-top: 4px solid var(--tsr-teal); background: var(--tsr-paper-pale); padding: 1.5rem; margin-top: 2rem; }
.tsr .record-focus .evidence-record { border: 0; padding: 0; background: transparent; }
.tsr .claim-banner { border-left: 4px solid var(--brass); background: var(--tsr-paper-deep); padding: 1.2rem 1.4rem; margin-top: 2rem; }
.tsr .claim-banner h2 { font-size: 1.6rem; margin-bottom: 0.4rem; }
.tsr .claim-banner p { margin: 0 0 0.6rem; color: var(--tsr-ink-soft); font-size: 0.86rem; }
.tsr .evidence-pager { display: flex; justify-content: space-between; align-items: center; gap: 1rem; margin-top: 1.5rem; font-size: 0.8rem; color: var(--tsr-ink-soft); }
.tsr .evidence-pager a { color: var(--tsr-teal); font-weight: 800; display: inline-flex; align-items: center; gap: 0.3rem; min-height: 44px; }
.tsr .evidence-pager a:first-child svg { transform: rotate(180deg); }
.tsr .evidence-pager svg { width: 1em; height: 1em; }
.tsr .register-note { max-width: 780px; color: var(--tsr-ink-soft); font-size: 0.84rem; margin: -1.6rem 0 2rem; }
.tsr .evidence-entry h3 { font-size: 1.15rem; }
.tsr .evidence-entry > div:nth-child(2) p.source-role { display: block; margin: 0.3rem 0 0; font-size: 0.74rem; color: var(--tsr-ink-soft); text-transform: none; }
.tsr .side-note { color: var(--tsr-ink-soft); font-size: 0.82rem; margin: 0.6rem 0 0; }

/* --- Corpus explorers ------------------------------------------------------- */
.tsr .corpus-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 1rem; }
.tsr .corpus-card { border: 1px solid var(--tsr-line); background: var(--tsr-paper-pale); padding: 1.3rem; display: grid; align-content: start; gap: 0.4rem; }
.tsr .corpus-card h3 { font-size: 1.5rem; line-height: 1.15; }
.tsr .corpus-card h3 a { color: var(--tsr-ink); }
.tsr .corpus-card p { margin: 0; color: var(--tsr-ink-soft); font-size: 0.82rem; }
.tsr .corpus-figure strong { font: 700 1.6rem/1 var(--mono); color: var(--tsr-ink); }
.tsr .corpus-body .result-count { margin: 1.2rem 0 1.5rem; }
.tsr .corpus-body .result-count a { color: var(--tsr-teal); font-weight: 700; text-decoration: underline !important; }
.tsr .corpus-table { min-width: 720px; }
.tsr .corpus-table .status-pill { margin-left: 0.3rem; font-size: 0.58rem; min-height: 20px; }
.tsr .notice-list { margin: 0.4rem 0 0; padding-left: 1.1rem; font-size: 0.84rem; }
.tsr .entry-steps { margin: 0; }

/* --- Corrections ledger ----------------------------------------------------- */
.tsr .ledger-list { border-top: 1px solid var(--tsr-line-dark); }
.tsr .ledger-entry { display: grid; grid-template-columns: 130px minmax(0, 1fr); gap: 1.5rem; padding: 1.5rem 0; border-bottom: 1px solid var(--tsr-line-dark); scroll-margin-top: 1.5rem; }
.tsr .ledger-id { display: grid; gap: 0.5rem; align-content: start; }
.tsr .ledger-id span:first-child { color: var(--brass); font: 800 0.85rem var(--mono); }
.tsr .ledger-entry h3 { font-size: 1.45rem; line-height: 1.15; }
.tsr .ledger-entry h3 a { color: var(--tsr-ink); }
.tsr .ledger-metric { margin: 0.35rem 0 0.6rem; color: var(--tsr-ink-soft); font-size: 0.86rem; }
.tsr .ledger-change { margin: 0; display: flex; flex-wrap: wrap; align-items: baseline; gap: 0.5rem 0.8rem; font-family: var(--mono); font-size: 0.9rem; }
.tsr .ledger-old { color: var(--tsr-ink-soft); text-decoration: line-through; text-decoration-thickness: 1px; }
.tsr .ledger-arrow { color: var(--tsr-ink-soft); font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.08em; }
.tsr .ledger-change strong { font-size: 1.05rem; }
.tsr .ledger-reason { margin: 0.6rem 0 0; font-size: 0.84rem; color: var(--tsr-ink-soft); }
.tsr .ledger-values { margin: 0.4rem 0 0; padding-left: 1.1rem; font-size: 0.86rem; }
.tsr .ledger-values li + li { margin-top: 0.3rem; }
.tsr .ledger-basis { color: var(--tsr-ink-soft); }
.tsr .corrections-body .prose h2 { margin-top: 0; }

/* --- Forms ------------------------------------------------------------------- */
.tsr .form-success-local { border-top-color: var(--brass); }
.tsr .form-error-block { border-top: 4px solid var(--danger); background: var(--tsr-paper-pale); padding: 2rem; }
.tsr .form-error-block h2, .tsr .form-success h2 { margin-bottom: 1rem; }
.tsr .submission-copy { margin-top: 1rem; }
.tsr .submission-copy > summary { cursor: pointer; color: var(--tsr-teal); font-weight: 800; font-size: 0.78rem; min-height: 32px; }
.tsr .submission-copy pre { white-space: pre-wrap; font: 0.78rem/1.5 var(--mono); background: var(--tsr-paper-deep); padding: 1rem; margin: 0.6rem 0 0; overflow-wrap: anywhere; }

@media (width<=980px) {
  .tsr .inventory-grid { grid-template-columns: repeat(2, 1fr); }
  .tsr .route-card-grid-wide { grid-template-columns: repeat(2, 1fr); }
  .tsr .evidence-inventory { grid-template-columns: repeat(3, 1fr); }
  .tsr .evidence-inventory a:nth-child(3n) { border-right: 0; }
  .tsr .record-details .evidence-definition-list div { grid-template-columns: 150px 1fr; }
}
@media (width<=720px) {
  .tsr .inventory-grid, .tsr .route-card-grid-wide { grid-template-columns: 1fr; }
  .tsr .evidence-inventory { grid-template-columns: 1fr 1fr; }
  .tsr .evidence-inventory a { border-bottom: 1px solid var(--tsr-line); }
  .tsr .evidence-sections a { padding: 0.6rem 0.7rem; font-size: 0.74rem; }
  .st-key-tsr-evidence, .st-key-tsr-corpus { width: min(100% - 2rem, 1240px) !important; padding: 0.8rem; }
  .tsr .record-details .evidence-definition-list div { grid-template-columns: 1fr; gap: 0.2rem; }
  .tsr .ledger-entry { grid-template-columns: 1fr; gap: 0.6rem; }
  .tsr .table-scroll { position: relative; }
  .tsr .table-scroll::after { content: "Scroll sideways for more columns"; display: block; padding: 0.5rem 0.8rem; color: var(--tsr-ink-soft); font: 700 0.66rem var(--mono); letter-spacing: 0.06em; text-transform: uppercase; border-top: 1px solid var(--tsr-line); position: sticky; left: 0; }
  .tsr .latest-values { grid-template-columns: repeat(2, 1fr); }
}
"""


def stylesheet() -> str:
    return f"<style>{site_css()}\n{APP_CSS}</style>"
