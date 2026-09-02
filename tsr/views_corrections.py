"""Corrections and published differences, and the correction report form."""

from __future__ import annotations

from typing import Any

import streamlit as st

from . import corpora, dataset, forms, records
from .components import source_list, status_pill
from .icons import icon
from .ui import breadcrumbs, controls, esc, link, page_hero, write

POLICY = (
    ("Identify the exact record.", "Give the school, dataset, year and field where possible."),
    ("State the definition.", "Explain whether the evidence concerns entries, candidates, offers, acceptances or destinations."),
    ("Provide source detail.", "Describe the originating publication and where it can be checked."),
    ("Review without silent mutation.", "The existing record remains unchanged while the issue is assessed."),
    ("Version any approved revision.", "A future commissioned data update receives a new snapshot, parity accounting and changelog entry."),
)


def _value(value: Any) -> str:
    if isinstance(value, list):
        return " / ".join(_value(item) for item in value)
    if isinstance(value, dict):
        return " · ".join(f"{key}: {_value(item)}" for key, item in value.items())
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def _school_link(name: str) -> str:
    school_id = corpora.school_id_for(name)
    school = records.find_school(school_id) if school_id else None
    return link(f"/schools/{school_id}", esc(school["name"])) if school else esc(name)


def _correction(item: dict[str, Any]) -> str:
    return f"""<article class="ledger-entry" id="{esc(item["id"])}">
  <div class="ledger-id"><span>{esc(item["id"])}</span>{status_pill(str(item.get("status", "")).capitalize())}</div>
  <div>
    <h3>{_school_link(item["school"])} · {esc(item["period"])}</h3>
    <p class="ledger-metric">{esc(item["metric"])}</p>
    <p class="ledger-change"><span class="ledger-old">Earlier value {esc(_value(item["old"]))}</span> <span class="ledger-arrow">now</span> <strong>{esc(_value(item["new"]))}</strong></p>
    <p class="ledger-reason">{esc(item["reason"])}</p>
    <details class="dataset-sources"><summary>Sources</summary>{source_list(item.get("source_refs") or [])}</details>
  </div>
</article>"""


def _conflict(item: dict[str, Any]) -> str:
    values = []
    for candidate in item.get("values") or []:
        if isinstance(candidate, dict) and "value" in candidate:
            basis = candidate.get("basis") or ""
            source = candidate.get("source") or ""
            values.append(
                f"<li><strong>{esc(_value(candidate['value']))}</strong>"
                + (f' <span class="ledger-basis">{esc(basis)}</span>' if basis else "")
                + (f' <code class="source-key">{esc(source)}</code>' if source else "")
                + "</li>"
            )
        else:
            values.append(f"<li>{esc(_value(candidate))}</li>")
    return f"""<article class="ledger-entry" id="{esc(item["id"])}">
  <div class="ledger-id"><span>{esc(item["id"])}</span></div>
  <div>
    <h3>{_school_link(item["school"])} · {esc(item["period"])}</h3>
    <p class="ledger-metric">{esc(item["metric"])}</p>
    <ul class="ledger-values">{"".join(values)}</ul>
    <p class="ledger-reason"><strong>Treatment.</strong> {esc(item["treatment"])}</p>
  </div>
</article>"""


def corrections() -> None:
    params = st.query_params
    schools = dataset.schools()
    ids = ["all", *[school["id"] for school in schools]]
    default = params.get("school") if params.get("school") in ids else "all"
    all_corrections = corpora.corrections()
    all_conflicts = corpora.conflicts()
    write(f"""
<main id="main-content">
  <div class="shell">{breadcrumbs([("Corrections", None)])}</div>
  {page_hero(
      "Editorial accountability",
      "Corrections and published differences",
      "When a figure is corrected, the record uses the new value and keeps the earlier value and the reason here. When credible publications disagree, both values are noted with the one the record uses and why.",
      f"{len(all_corrections)} corrections and {len(all_conflicts)} published differences are recorded in the frozen edition. None is applied silently, and this page creates none.",
  )}
</main>""")
    with controls("tsr-index-series"):
        school_id = st.selectbox(
            "Show",
            ids,
            index=ids.index(default),
            format_func=lambda value: "All schools" if value == "all" else next(s["name"] for s in schools if s["id"] == value),
            key="corrections_school",
        )
    if (params.get("school") or "all") != school_id:
        st.query_params.from_dict({"p": "/corrections", **({"school": school_id} if school_id != "all" else {})})
    selected_corrections = corpora.corrections(None if school_id == "all" else school_id)
    selected_conflicts = corpora.conflicts(None if school_id == "all" else school_id)
    corrections_markup = "".join(_correction(item) for item in selected_corrections) or '<div class="empty-state"><h2>No corrections recorded</h2><p>No figure for this school has been corrected in the frozen edition.</p></div>'
    conflicts_markup = "".join(_conflict(item) for item in selected_conflicts) or '<div class="empty-state"><h2>No published differences recorded</h2><p>No competing publication is recorded for this school.</p></div>'
    authority = "".join(
        f"<li><strong>{esc(item['version'])}</strong> controls {esc(item['controls'])}.</li>" for item in corpora.version_authority()
    )
    write(f"""
<main class="corrections-body">
  <section class="section shell tsr-tight-top">
    <div class="section-heading"><div><p class="eyebrow">Corrections</p><h2 id="corrections">What changed, and why</h2></div><p>{len(selected_corrections)} {"correction" if len(selected_corrections) == 1 else "corrections"}. The value now used replaces the earlier value in every ledger and chart; the change and its reason stay here.</p></div>
    <div class="ledger-list">{corrections_markup}</div>
  </section>
  <section class="section shell tsr-tight-top">
    <div class="section-heading"><div><p class="eyebrow">Published differences</p><h2 id="differences">When published figures do not agree</h2></div><p>{len(selected_conflicts)} {"case" if len(selected_conflicts) == 1 else "cases"}. Both values are kept; the treatment says which one the record relies on.</p></div>
    <div class="ledger-list">{conflicts_markup}</div>
  </section>
  <section class="section shell tsr-tight-top content-grid">
    <article class="prose">
      <h2>Which publication controls</h2>
      <p>The source compilations are layered rather than replaced; a later companion does not overwrite a detailed annual table it merely leaves out.</p>
      <ol>{authority}</ol>
      <p>{link("/evidence?section=method", f'How the figures are checked {icon("arrow-right")}', "text-link")}</p>
    </article>
    <aside class="side-index">
      <h2>Seen something wrong?</h2>
      <p class="side-note">Specific, source-backed reports are reviewed against the record’s definitions. The frozen edition is not changed until a versioned editorial review.</p>
      <nav>{link("/corrections/report", "Report a correction")}{link("/evidence", "Evidence centre")}</nav>
    </aside>
  </section>
</main>""")


def report() -> None:
    items = "".join(
        f"<li><strong>{title}</strong> {body}</li>" for title, body in POLICY
    )
    write(f"""
<main id="main-content">
  <div class="shell">{breadcrumbs([("Corrections", "/corrections"), ("Report a correction", None)])}</div>
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
  <p>{link("/corrections", f'Read the corrections already recorded {icon("arrow-right")}', "text-link")}</p>
</article>""")
        with form_column:
            write("""
<div class="form-intro">
  <p class="eyebrow">Structured report</p>
  <h2>Tell us exactly where to look</h2>
</div>""")
            forms.correction_form()
