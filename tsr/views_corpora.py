"""The Oxford and Cambridge corpus, the US-university corpus and school entry."""

from __future__ import annotations

from collections import Counter
from typing import Any, Sequence

import streamlit as st

from . import corpora, dataset, evidence, records
from .components import source_list, status_pill
from .icons import icon
from .ui import breadcrumbs, controls, esc, link, page_hero, write

OX_FAMILY_ORDER = (
    "apply_centre_outcomes",
    "derived_combined_oxbridge_apply_centre_outcomes",
    "school_published_oxbridge_offers",
    "apply_centre_subject_outcomes_rounded",
    "apply_centre_college_outcomes_rounded",
    "historical_five_year_oxbridge_hit_rate",
    "institution_overall_outcomes",
    "subject_outcomes",
    "course_competition",
    "subject_admissions_process",
)


def _trace(record_id: str) -> str:
    return f'<a class="text-link trace-link" href="?p=/evidence&amp;record={esc(record_id)}" target="_self">Trace</a>'


def _pct(value: Any) -> str:
    return evidence._percent_from_fraction(value)


def _cell(value: Any) -> str:
    text = evidence.interval_text(value)
    return f'<td class="blank-value">—</td>' if text == "—" else f"<td>{esc(text)}</td>"


def _table(caption: str, head: Sequence[str], rows: Sequence[str]) -> str:
    header = "".join(f'<th scope="col">{esc(item)}</th>' for item in head)
    return f"""<div class="table-scroll" tabindex="0" aria-label="Scrollable table: {esc(caption)}">
  <table class="data-table corpus-table">
    <caption>{esc(caption)}</caption>
    <thead><tr>{header}</tr></thead>
    <tbody>{"".join(rows)}</tbody>
  </table>
</div>"""


# --- Oxford and Cambridge -----------------------------------------------------


def _oxbridge_family_block(family: str, items: list[dict[str, Any]], school_scope: bool) -> str:
    spec = corpora.OXBRIDGE_FAMILIES[family]
    rows: list[str] = []
    if family in ("apply_centre_outcomes", "derived_combined_oxbridge_apply_centre_outcomes", "institution_overall_outcomes", "subject_outcomes", "subject_admissions_process"):
        head = ["Cycle", "University"] + (["Subject"] if family in ("subject_outcomes", "subject_admissions_process") else []) + (["Apply centre"] if not school_scope and family.startswith(("apply", "derived")) else []) + ["Applications", "Offers", "Accepted / admitted", "Offer rate", "Accepted rate", "Confidence", "Source authority", "Record"]
        for record in sorted(items, key=lambda r: (-(corpora.oxbridge_year(r) or 0), str(r.get("institution")), str(r.get("subject") or ""), str(r.get("apply_centre_name") or ""))):
            cells = [f"<td>{esc(corpora.oxbridge_year(record) or '—')}</td>", f"<td>{esc(record.get('institution') or '—')}</td>"]
            if family in ("subject_outcomes", "subject_admissions_process"):
                cells.append(f"<td>{esc(record.get('subject') or '—')}</td>")
            if not school_scope and family.startswith(("apply", "derived")):
                cells.append(f"<td>{esc(record.get('apply_centre_name') or '—')}</td>")
            cells += [_cell(record.get("applications")), _cell(record.get("offers")), _cell(record.get("acceptances_or_admissions")),
                      f"<td>{esc(_pct(record.get('offer_rate')))}</td>", f"<td>{esc(_pct(record.get('acceptance_or_admission_rate')))}</td>",
                      f"<td>{esc(str(record.get('confidence') or '—').capitalize())}</td>", f"<td>{esc(str(record.get('source_authority') or '—').replace('_', ' '))}</td>",
                      f"<td>{_trace('ox:' + record['record_id'])}</td>"]
            rows.append(f"<tr>{''.join(cells)}</tr>")
    elif family in ("apply_centre_subject_outcomes_rounded", "apply_centre_college_outcomes_rounded"):
        head = ["Period", "University", "Breakdown", "Applications", "Shortlisted", "Offer holders", "Note", "Record"]
        for record in sorted(items, key=lambda r: (str(r.get("period_start")), str(r.get("dimension_value")))):
            note = record.get("college_flow_note") or record.get("rounding_note") or ""
            rows.append(
                f"<tr><td>{esc(record.get('period_start'))}–{esc(record.get('period_end'))}</td><td>{esc(record.get('institution') or '—')}</td>"
                f"<td>{esc(record.get('dimension_value') or '—')}</td>{_cell(record.get('applications'))}{_cell(record.get('shortlisted'))}{_cell(record.get('offer_holders'))}"
                f"<td class=\"cell-note\">{esc(note) if note else '—'}</td><td>{_trace('ox:' + record['record_id'])}</td></tr>"
            )
    elif family == "school_published_oxbridge_offers":
        head = ["Cycle", "Oxford offers", "Cambridge offers", "Total", "Cohort scope", "Note", "Record"]
        for record in sorted(items, key=lambda r: -(corpora.oxbridge_year(r) or 0)):
            rows.append(
                f"<tr><td>{esc(corpora.oxbridge_year(record) or '—')}</td>{_cell(record.get('oxford_offers'))}{_cell(record.get('cambridge_offers'))}{_cell(record.get('total_offers'))}"
                f"<td class=\"cell-note\">{esc(record.get('cohort_scope') or '—')}</td><td class=\"cell-note\">{esc(record.get('notes') or '—')}</td><td>{_trace('ox:' + record['record_id'])}</td></tr>"
            )
    elif family == "historical_five_year_oxbridge_hit_rate":
        head = ["Rank", "School as printed", "Five-year admissions", "Five-year hit rate", "Published", "Record"]
        for record in sorted(items, key=lambda r: int(r.get("rank") or 0)):
            rows.append(
                f"<tr><td>{esc(record.get('rank'))}</td><td>{esc(record.get('school_name'))}</td>{_cell(record.get('five_year_admissions'))}<td>{esc(_pct(record.get('five_year_hit_rate')))}</td>"
                f"<td>{esc(record.get('publication_date') or '—')}</td><td>{_trace('ox:' + record['record_id'])}</td></tr>"
            )
    elif family == "course_competition":
        head = ["Period", "University", "Subject", "Applicants per place", "Note", "Record"]
        for record in sorted(items, key=lambda r: str(r.get("subject"))):
            rows.append(
                f"<tr><td>{esc(record.get('period_start'))}–{esc(record.get('period_end'))}</td><td>{esc(record.get('institution'))}</td><td>{esc(record.get('subject'))}</td>"
                f"<td>{esc(record.get('applicants_per_place'))}</td><td class=\"cell-note\">{esc(record.get('notes') or '—')}</td><td>{_trace('ox:' + record['record_id'])}</td></tr>"
            )
    else:
        head = ["Record", "Summary"]
        for record in items:
            item = evidence.record("ox:" + record["record_id"])
            rows.append(f"<tr><td>{_trace('ox:' + record['record_id'])}</td><td>{esc(item.title if item else record['record_id'])}</td></tr>")
    note = ""
    if family == "historical_five_year_oxbridge_hit_rate":
        note = '<p class="dataset-note">A 2007 secondary two-page excerpt. The five-year period is not stated and the methodology is unclear; the table is retained as it was published and is never mixed with the apply-centre records.</p>'
    if family.startswith("derived"):
        note = '<p class="dataset-note">Derived at source from exact, unsuppressed Oxford and Cambridge counts for the same named cycle; shown only where both universities use the same entry-cycle year.</p>'
    if family.endswith("rounded"):
        note = '<p class="dataset-note">Published as intervals rounded down to multiples of five. The record keeps the interval; no midpoint is invented.</p>'
    return f"""<article class="dataset-card" id="oxbridge-{esc(family)}">
  <header class="dataset-header"><div><p class="eyebrow">{esc(spec['summary'])}</p><h2>{esc(spec['label'])} · {len(items)} {"record" if len(items) == 1 else "records"}</h2></div></header>
  {note}
  {_table(spec['label'], head, rows)}
</article>"""


def _oxbridge_overview() -> str:
    cards = []
    for school in dataset.schools():
        items = corpora.oxbridge_records(school["id"])
        years = [corpora.oxbridge_year(item) for item in items]
        low, high = corpora.years_of(years)
        families = Counter(corpora.oxbridge_family(item)["label"] for item in items)
        family_text = " · ".join(f"{label} ({count})" for label, count in families.most_common(3))
        cards.append(f"""<article class="corpus-card">
  <p class="eyebrow">{esc(school["short"])}</p>
  <h3>{link(f"/schools/{school['id']}/oxbridge", esc(school["name"]))}</h3>
  <p class="corpus-figure"><strong>{len(items)}</strong> records · cycles {low}–{high}</p>
  <p>{esc(family_text)}</p>
  {link(f"/schools/{school['id']}/oxbridge", f'Open the school’s records {icon("arrow-right")}', "text-link")}
</article>""")
    return f'<div class="corpus-grid">{"".join(cards)}</div>'


def oxbridge(school_id: str | None = None) -> None:
    school = records.find_school(school_id) if school_id else None
    corpus = corpora.oxbridge_corpus()
    definitions = corpus.get("metric_definitions", {})
    items = corpora.oxbridge_records(school_id) if school else corpora.oxbridge_records()
    crumbs = [("Schools", "/schools"), (school["name"], f"/schools/{school_id}"), ("Oxford and Cambridge records", None)] if school else [("Oxford and Cambridge records", None)]
    title = f"Oxford and Cambridge records" if school else "Oxford and Cambridge admissions records"
    write(f"""
<main id="main-content">
  <div class="shell">{breadcrumbs(crumbs)}</div>
  {page_hero(
      school["name"] if school else "Second corpus · 571 records",
      title,
      "Apply-centre applications, offers and accepted or admitted outcomes by university and entry cycle, with the rounded subject and college releases, the school's own offer claims and the historical secondary table kept apart.",
      esc(definitions.get("cycle_year", "")) + " This is university apply-centre evidence: it is not a school-entry acceptance rate and not a leaver-destination measure.",
  )}
</main>""")

    if not school:
        university_items = [item for item in items if corpora.oxbridge_family(item)["scope"] == "university"]
        historical = [item for item in items if item.get("metric_family") == "historical_five_year_oxbridge_hit_rate"]
        blocks = "".join(
            _oxbridge_family_block(family, [item for item in university_items if item.get("metric_family") == family], False)
            for family in OX_FAMILY_ORDER
            if any(item.get("metric_family") == family for item in university_items)
        )
        write(f"""
<main class="corpus-body">
  <section class="section shell">
    <div class="section-heading"><div><p class="eyebrow">By school</p><h2>Apply-centre records</h2></div><p>{len(items) - len(university_items) - len(historical) + sum(1 for h in historical if corpora.oxbridge_school_id(h))} school records across the seven schools.</p></div>
    {_oxbridge_overview()}
  </section>
  <section class="section shell tsr-tight-top">
    <div class="section-heading"><div><p class="eyebrow">Context</p><h2>University-wide records</h2></div><p>Whole-university and subject figures that sit behind the apply-centre counts.</p></div>
    <div class="dataset-stack">{blocks}</div>
  </section>
  <section class="section shell tsr-tight-top">
    <div class="section-heading"><div><p class="eyebrow">Historical</p><h2>2007 five-year table</h2></div><p>{len(historical)} rows as published; secondary evidence with an unstated period.</p></div>
    <div class="dataset-stack">{_oxbridge_family_block("historical_five_year_oxbridge_hit_rate", historical, False)}</div>
  </section>
</main>""")
        return

    universities = ["all", *sorted({str(item.get("institution")) for item in items if item.get("institution")})]
    families = ["all", *[family for family in OX_FAMILY_ORDER if any(item.get("metric_family") == family for item in items)]]
    years = [corpora.oxbridge_year(item) for item in items]
    low, high = corpora.years_of(years)
    params = st.query_params
    with controls("tsr-corpus"):
        columns = st.columns([1.2, 1.6, 0.7, 0.7])
        with columns[0]:
            university = st.selectbox("University", universities, index=universities.index(params.get("university")) if params.get("university") in universities else 0, format_func=lambda v: "All universities" if v == "all" else v, key="ox_university")
        with columns[1]:
            family = st.selectbox("Record family", families, index=families.index(params.get("family")) if params.get("family") in families else 0, format_func=lambda v: "All families" if v == "all" else corpora.OXBRIDGE_FAMILIES[v]["label"], key="ox_family")
        with columns[2]:
            year_from = st.number_input("From cycle", min_value=low or 2006, max_value=high or 2026, value=low or 2006, step=1, key="ox_from")
        with columns[3]:
            year_to = st.number_input("To cycle", min_value=int(year_from), max_value=high or 2026, value=high or 2026, step=1, key="ox_to")
    selected = [
        item for item in items
        if (university == "all" or item.get("institution") == university)
        and (family == "all" or item.get("metric_family") == family)
        and (corpora.oxbridge_year(item) is None or int(year_from) <= corpora.oxbridge_year(item) <= int(year_to))
    ]
    blocks = "".join(
        _oxbridge_family_block(fam, [item for item in selected if item.get("metric_family") == fam], True)
        for fam in OX_FAMILY_ORDER
        if any(item.get("metric_family") == fam for item in selected)
    )
    if not blocks:
        blocks = '<div class="empty-state"><h2>No records match</h2><p>Widen the cycle range or choose another family. A missing cycle is never interpolated.</p></div>'
    source_ids = list(dict.fromkeys(str(sid) for item in items for sid in (item.get("source_ids") or [])))
    write(f"""
<main class="corpus-body">
  <section class="section shell tsr-tight-top">
    <p class="result-count" aria-live="polite">{len(selected)} of {len(items)} records · {link(f"/schools/{school_id}/university-destinations", "the school's university ledgers")} keep the figures-corpus cycle tables and destinations separately</p>
    <div class="dataset-stack">{blocks}</div>
    <details class="dataset-sources"><summary>Sources behind this school's records · {len(source_ids)} references</summary>{source_list(source_ids)}</details>
    <div class="notice notice-warning"><strong>Suppression and rounding</strong><p>{esc(definitions.get("suppression", ""))}</p></div>
  </section>
</main>""")


# --- US and overseas universities ---------------------------------------------


def _us_overview() -> str:
    cards = []
    for school in dataset.schools():
        items = corpora.us_records(school["id"])
        years = [corpora.us_year(item) for item in items]
        low, high = corpora.years_of(years)
        institutions = {item.get("institution_normalized") for item in items if item.get("institution_normalized")}
        aggregates = sum(1 for item in items if item.get("is_aggregate"))
        cards.append(f"""<article class="corpus-card">
  <p class="eyebrow">{esc(school["short"])}</p>
  <h3>{link(f"/schools/{school['id']}/us-universities", esc(school["name"]))}</h3>
  <p class="corpus-figure"><strong>{len(items)}</strong> records · {low}–{high}</p>
  <p>{len(institutions)} named institutions · {aggregates} aggregate rows</p>
  {link(f"/schools/{school['id']}/us-universities", f'Open the school’s records {icon("arrow-right")}', "text-link")}
</article>""")
    return f'<div class="corpus-grid">{"".join(cards)}</div>'


def us_universities(school_id: str | None = None) -> None:
    school = records.find_school(school_id) if school_id else None
    corpus = corpora.us_corpus()
    items = corpora.us_records(school_id) if school else corpora.us_records()
    crumbs = [("Schools", "/schools"), (school["name"], f"/schools/{school_id}"), ("US and overseas university records", None)] if school else [("US and overseas university records", None)]
    write(f"""
<main id="main-content">
  <div class="shell">{breadcrumbs(crumbs)}</div>
  {page_hero(
      school["name"] if school else "Third corpus · 349 records",
      "US and overseas university records",
      "Named institutions and explicit aggregates by school and period, each typed by outcome: a leaver destination, a firm place, an acceptance, a named offer or a presence-only mention.",
      "Aggregate rows are never summed with institution rows; a named institution without a count is never read as one; and where two official versions disagree both stay visible.",
  )}
</main>""")
    safeguards = "".join(f"<li>{esc(item)}</li>" for item in corpus.get("safeguards", []))
    if not school:
        types = Counter(corpora.us_metric_label(item) for item in items)
        type_rows = "".join(f'<tr><th scope="row">{esc(label)}</th><td>{count}</td></tr>' for label, count in types.most_common())
        write(f"""
<main class="corpus-body">
  <section class="section shell">
    <div class="section-heading"><div><p class="eyebrow">By school</p><h2>Records by school</h2></div><p>{esc(corpus.get("grain", ""))}</p></div>
    {_us_overview()}
  </section>
  <section class="section shell tsr-tight-top content-grid">
    <article class="prose">
      <h2>Outcome types in this corpus</h2>
      <table><thead><tr><th scope="col">Outcome type</th><th scope="col">Records</th></tr></thead><tbody>{type_rows}</tbody></table>
      <h3>Safeguards</h3>
      <ul>{safeguards}</ul>
    </article>
    <aside class="side-index"><h2>Related</h2><nav>{link("/evidence?corpus=us", "Search these records")}{link("/oxbridge", "Oxford and Cambridge records")}{link("/methodology", "Methodology")}</nav></aside>
  </section>
</main>""")
        return

    periods = ["all", *sorted({str(item.get("period")) for item in items}, key=lambda p: (-(corpora.us_year({"period": p}) or 0), p))]
    outcome_types = ["all", *sorted({str(item.get("metric_type")) for item in items})]
    regions = ["all", *sorted({str(item.get("region")) for item in items})]
    params = st.query_params
    with controls("tsr-corpus"):
        columns = st.columns([1, 1.4, 1, 1])
        with columns[0]:
            period = st.selectbox("Period", periods, index=periods.index(params.get("period")) if params.get("period") in periods else 0, format_func=lambda v: "All periods" if v == "all" else v, key="us_period")
        with columns[1]:
            outcome = st.selectbox("Outcome type", outcome_types, index=0, format_func=lambda v: "All outcome types" if v == "all" else corpora.US_METRIC_TYPES.get(v, v), key="us_outcome")
        with columns[2]:
            region = st.selectbox("Region", regions, index=0, format_func=lambda v: "All regions" if v == "all" else v, key="us_region")
        with columns[3]:
            aggregates = st.selectbox("Rows", ("all", "institution", "aggregate"), index=0, format_func=lambda v: {"all": "Institutions and aggregates", "institution": "Named institutions only", "aggregate": "Aggregate rows only"}[v], key="us_rows")
    selected = [
        item for item in items
        if (period == "all" or str(item.get("period")) == period)
        and (outcome == "all" or item.get("metric_type") == outcome)
        and (region == "all" or str(item.get("region")) == region)
        and (aggregates == "all" or (aggregates == "aggregate") == bool(item.get("is_aggregate")))
    ]
    selected.sort(key=lambda r: (-(corpora.us_year(r) or 0), str(r.get("period")), bool(r.get("is_aggregate")), str(r.get("institution_normalized") or r.get("institution_raw"))))
    rows = []
    for record in selected:
        count = record.get("count")
        if count is None and record.get("count_lower_bound") is not None:
            count_text = f"≥{record['count_lower_bound']}"
        elif count is None and record.get("approximate_count") is not None:
            count_text = f"≈{record['approximate_count']}"
        elif count is None:
            count_text = "named · no count"
        else:
            count_text = evidence.interval_text(count)
        institution = record.get("institution_normalized") or record.get("institution_raw") or "—"
        flags = []
        if record.get("is_aggregate"):
            flags.append(status_pill("Aggregate"))
        if record.get("conflict_group"):
            flags.append(status_pill("Version kept" if record.get("canonical_for_analysis") else "Alternative version"))
        rows.append(
            f"<tr><td>{esc(record.get('period'))}</td><td>{esc(institution)} {' '.join(flags)}</td><td>{esc(corpora.us_metric_label(record))}</td>"
            f"<td>{esc(count_text)}</td>{_cell(record.get('cohort_denominator'))}<td>{esc(_pct(record.get('rate')))}</td><td>{esc(record.get('region') or '—')}</td>"
            f"<td>{esc(evidence.us_status(record))}</td><td>{_trace('us:' + record['record_id'])}</td></tr>"
        )
    table = _table(f"{school['name']} · US and overseas university records", ["Period", "Institution", "Outcome type", "Count", "Cohort denominator", "Rate", "Region", "Evidence", "Record"], rows) if rows else '<div class="empty-state"><h2>No records match</h2><p>Change the period or outcome type. A missing year is never interpolated.</p></div>'
    source_ids = list(dict.fromkeys(str(item.get("source_id")) for item in items if item.get("source_id")))
    write(f"""
<main class="corpus-body">
  <section class="section shell tsr-tight-top">
    <p class="result-count" aria-live="polite">{len(selected)} of {len(items)} records · {link(f"/schools/{school_id}/university-destinations", "the school's destination ledgers")} carry the published totals these rows itemise</p>
    {table}
    <details class="dataset-sources"><summary>Sources behind this school's records · {len(source_ids)} references</summary>{source_list(source_ids)}</details>
    <div class="notice notice-warning"><strong>Read each row on its own basis</strong><ul class="notice-list">{safeguards}</ul></div>
  </section>
</main>""")


# --- School entry -------------------------------------------------------------


def school_entry(school_id: str) -> bool:
    school = records.find_school(school_id)
    process = corpora.admissions_process(school_id)
    if school is None or process is None:
        return False
    entry_points = "".join(f"<li>{esc(item)}</li>" for item in process.get("entryPoints") or [])
    steps = "".join(
        f'<li><span>{index + 1:02d}</span><div><h3>{esc(step.get("label"))}</h3><p>{esc(step.get("detail"))}</p></div></li>'
        for index, step in enumerate(process.get("steps") or [])
    )
    source = esc(process.get("sourceTitle") or "No school-authored entry guide in the reviewed corpus")
    write(f"""
<main id="main-content">
  <div class="shell">{breadcrumbs([("Schools", "/schools"), (school["name"], f"/schools/{school_id}"), ("School entry", None)])}</div>
  <header class="page-hero">
    <div class="shell page-hero-grid">
      <div>
        <p class="eyebrow">{esc(school["name"])} · school entry</p>
        <h1>Published process and known limits</h1>
        <p class="page-intro">What the reviewed evidence establishes about how pupils enter the school, and what it does not. This is school admissions evidence; university admissions are recorded separately.</p>
      </div>
      <aside class="page-note"><strong>{esc(process.get("status"))}</strong><p>Evidence freshness: {esc(process.get("freshness"))}</p></aside>
    </div>
  </header>
  <section class="section shell content-grid">
    <article class="prose">
      <h2>Entry points evidenced</h2>
      <ul>{entry_points}</ul>
      <h2>Process as published</h2>
      <ol class="question-list entry-steps">{steps}</ol>
      <h2>What is not known</h2>
      <div class="notice notice-warning"><strong>Evidence boundary</strong><p>{esc(process.get("limit"))}</p></div>
    </article>
    <aside class="side-index">
      <h2>Source</h2>
      <p class="side-note">{source}</p>
      <nav>{link(f"/schools/{school_id}", "Back to the school record")}{link(f"/schools/{school_id}/oxbridge", "University admissions records")}{link("/methodology", "Methodology")}</nav>
    </aside>
  </section>
</main>""")
    return True
