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

/* Streamlit turns raw headings into its own anchored heading component; keep
   the record's own layout and drop the injected hover anchors. */
.tsr [data-testid="stHeadingWithActionElements"] { display: contents !important; }
.tsr [data-testid="stHeaderActionElements"] { display: none !important; }
.tsr h1, .tsr h2, .tsr h3, .tsr h4 { scroll-margin-top: 1.5rem; }
.tsr .tsr-anchor { display: block; height: 0; scroll-margin-top: 1.5rem; }

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
.st-key-tsr-search { max-width: 670px; margin-inline: 0 !important; padding-left: max(1.5rem, calc((100vw - 1240px) / 2)); }
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
"""


def stylesheet() -> str:
    return f"<style>{site_css()}\n{APP_CSS}</style>"
