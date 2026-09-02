"""Correction reporting."""

from __future__ import annotations

import streamlit as st

from . import forms
from .ui import breadcrumbs, controls, page_hero, write

POLICY = (
    ("Identify the exact record.", "Give the school, dataset, year and field where possible."),
    ("State the definition.", "Explain whether the evidence concerns entries, candidates, offers, acceptances or destinations."),
    ("Provide source detail.", "Describe the originating publication and where it can be checked."),
    ("Review without silent mutation.", "The existing record remains unchanged while the issue is assessed."),
    ("Version any approved revision.", "A future commissioned data update receives a new snapshot, parity accounting and changelog entry."),
)


def corrections() -> None:
    items = "".join(
        f"<li><strong>{title}</strong> {body}</li>" for title, body in POLICY
    )
    write(f"""
<main id="main-content">
  <div class="shell">{breadcrumbs([("Corrections", None)])}</div>
  {page_hero(
      "Editorial accountability",
      "Report a correction",
      "Specific, source-backed reports are reviewed against the record’s definitions and evidence rules.",
      "Submitting a report does not alter this data-frozen edition. Statistical changes require a separate, approved and versioned editorial process.",
  )}
</main>""")

    with controls("tsr-correction-layout"):
        policy_column, form_column = st.columns(2, gap="large")
        with policy_column:
            write(f"""
<article class="prose">
  <h2>Correction policy</h2>
  <ol>{items}</ol>
  <div class="notice notice-warning">
    <strong>No automatic correction</strong>
    <p>An anomaly or conflicting website is not enough to overwrite a production value. Conflicts can be preserved explicitly.</p>
  </div>
</article>""")
        with form_column:
            write("""
<div class="form-intro">
  <p class="eyebrow">Structured report</p>
  <h2>Tell us exactly where to look</h2>
</div>""")
            forms.correction_form()
