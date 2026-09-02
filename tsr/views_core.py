"""Home, school index, school records and dataset ledgers."""

from __future__ import annotations

from typing import Any, Sequence

import streamlit as st

from . import comparison, components, dataset, records, trajectory
from .icons import icon
from .ui import (
    LAST_REVIEWED_SHORT,
    artwork,
    breadcrumbs,
    controls,
    esc,
    link,
    page_hero,
    write,
)

@st.cache_data(show_spinner=False)
def _dataset_stack(slug: str, domains: tuple[str, ...], school_name: str) -> str:
    """Ledger markup is deterministic for a frozen dataset, so build it once."""
    return components.dataset_stack(records.school_datasets(slug, list(domains)), school_name)


@st.cache_data(show_spinner=False)
def _metrics() -> list[dict[str, Any]]:
    return comparison.metrics()


@st.cache_data(show_spinner=False)
def _index_panels(metric_id: str) -> dict[str, str]:
    """Every school's index panel for one metric, drawn on one shared ruler."""
    metric = comparison.metric_by_id(_metrics(), metric_id)
    frame = trajectory.index_frame(metric)
    return {
        school["id"]: trajectory.index_panel(metric, school, frame)
        for school in dataset.schools()
    }


@st.cache_data(show_spinner=False)
def _school_trajectory(slug: str) -> str:
    return trajectory.school_trajectory(records.find_school(slug), _metrics())


HOME_QUESTIONS = (
    ("How have results changed?", "Follow the published record year by year without smoothing away gaps."),
    ("What does an Oxbridge figure mean?", "See whether it records an application, offer, acceptance or final destination."),
    ("Which years are comparable?", "Grading reforms, qualification changes and exceptional years remain visibly separate."),
    ("What population is measured?", "Candidate, pupil and subject-entry denominators are never treated as interchangeable."),
)


def home() -> None:
    span = records.collection_span()
    total = records.frozen_record_count()
    schools = dataset.schools()

    cards = []
    for index, school in enumerate(schools):
        feature = " school-card-feature" if index == 0 else ""
        inner = (
            artwork(school["id"], decorative=True)
            + '<div class="school-card-copy">'
            + f'<p class="card-meta">{esc(school["evidenceWindow"])}</p>'
            + f'<h3>{esc(school["name"])}</h3>'
            + f'<p>{esc(school["oneLine"])}</p>'
            + f'<span class="card-action">View record {icon("arrow-right")}</span>'
            + "</div>"
        )
        cards.append(
            f'<article class="school-card{feature}">'
            + link(f'/schools/{school["id"]}', inner, attrs=f' aria-label="View {esc(school["name"])}"')
            + "</article>"
        )

    questions = "".join(
        f"<li><span>{index + 1:02d}</span><div><h3>{esc(title)}</h3><p>{esc(body)}</p></div></li>"
        for index, (title, body) in enumerate(HOME_QUESTIONS)
    )

    write(f"""
<main id="main-content">
  <section class="home-hero shell">
    <div class="hero-copy">
      <p class="eyebrow">The independent evidence record</p>
      <h1>Independent school results, year by year.</h1>
      <p class="hero-deck">Published examination results and university outcomes from seven highly selective UK schools, reconstructed as a careful historical record.</p>
      <div class="button-row">
        {link("/schools", f'Explore schools {icon("arrow-right")}', "button button-primary")}
        {link("/compare", "Compare schools", "button button-secondary")}
      </div>
    </div>
    <div class="hero-ledger" aria-label="Coverage of the record">
      <p class="ledger-kicker">The founding collection</p>
      <dl>
        <div><dt>Schools</dt><dd>{len(schools)}</dd></div>
        <div><dt>Historical span</dt><dd>{span["min"]}–{span["max"]}</dd></div>
        <div><dt>Frozen records</dt><dd>{total:,}</dd></div>
        <div><dt>Last reviewed</dt><dd>{LAST_REVIEWED_SHORT}</dd></div>
      </dl>
      <p class="ledger-note">The collection is deliberately focused. It does not imply that only these schools matter.</p>
    </div>
  </section>

  <section class="principle-band">
    <div class="shell principle-inner">{icon("scale")}<p>We do not treat offers as destinations, pupils as exam entries, or incompatible grading systems as one continuous league table.</p></div>
  </section>

  <section class="section shell" aria-labelledby="collection-title">
    <div class="section-heading">
      <div><p class="eyebrow">Browse the collection</p><h2 id="collection-title">Seven school records</h2></div>
      {link("/schools", f'Search all schools {icon("arrow-right")}', "text-link")}
    </div>
    <div class="school-grid">{"".join(cards)}</div>
  </section>

  <section class="question-section">
    <div class="shell question-layout">
      <div class="question-intro">
        <p class="eyebrow">Read the evidence properly</p>
        <h2>Questions a league table cannot answer</h2>
        <p>The record starts with definitions, not rankings. Every figure keeps the context needed to interpret it.</p>
        {link("/methodology", f'Read the methodology {icon("arrow-right")}', "text-link")}
      </div>
      <ol class="question-list">{questions}</ol>
    </div>
  </section>

  <section class="section shell professional-callout">
    <div class="callout-icon">{icon("book-open")}</div>
    <div>
      <p class="eyebrow">For professional work</p>
      <h2>Decision-ready, sourced school comparisons</h2>
      <p>Commission a defined comparison dossier or discuss recurring access for research, journalism, consultancy and school leadership.</p>
    </div>
    <div class="button-row">
      {link("/sample-dossier", "View a sample dossier", "button button-primary")}
      {link("/professional", "Professional access", "button button-secondary")}
    </div>
  </section>

  <section class="search-ribbon">
    <div class="shell">
      {icon("search")}
      <p><strong>Looking for a particular school?</strong> Start with the searchable school index.</p>
      {link("/schools", f'Explore schools {icon("arrow-right")}', "text-link light-link")}
    </div>
  </section>
</main>""")


def schools_index() -> None:
    entries = [
        {
            **school,
            "latestYear": records.latest_verified_year(school["id"]),
            "datasets": len(records.school_datasets(school["id"])),
        }
        for school in dataset.schools()
    ]

    write(f"""
<main id="main-content">
  <div class="shell">{breadcrumbs([("Schools", None)])}</div>
  {page_hero(
      "The founding collection",
      "School records",
      "Explore examination results, university destinations and application-cycle evidence without collapsing unlike measures into a ranking.",
      "Seven highly selective UK independent schools. The collection is focused, not exhaustive, and carries no claim that these are the only schools worth examining.",
  )}
  <section class="section shell school-index-shell">
    <p class="eyebrow index-search-label">Search schools</p>
  </section>
</main>""")

    with controls("tsr-search"):
        query = st.text_input(
            "Search schools",
            key="school-search",
            placeholder="Search by school name",
            label_visibility="collapsed",
        )

    needle = (query or "").lower().strip()
    matches = [
        entry
        for entry in entries
        if needle in f'{entry["name"]} {entry["short"]}'.lower()
    ]

    # One like-for-like series is drawn in every row on a ruler shared by all
    # seven schools, so the index can be read across schools and across years
    # without becoming a ranking.  The series is one of the comparison tool's
    # own metrics, chosen here and reflected in the URL.
    metrics = _metrics()
    metric_ids = trajectory.index_metric_ids(metrics)
    params = st.query_params
    requested = params.get("series")
    default_id = (
        requested
        if requested in metric_ids
        else trajectory.INDEX_DEFAULT_METRIC
        if trajectory.INDEX_DEFAULT_METRIC in metric_ids
        else metric_ids[0]
    )
    with controls("tsr-index-series"):
        metric_id = st.selectbox(
            "Charted series",
            metric_ids,
            index=metric_ids.index(default_id),
            format_func=lambda value: next(m["label"] for m in metrics if m["id"] == value),
            key="index_series",
        )
    if params.get("series") != metric_id:
        params["series"] = metric_id
    metric = comparison.metric_by_id(metrics, metric_id)
    panels = _index_panels(metric_id)
    derived_note = (
        "<p>Calculated rates are generated at display time from frozen source values and are not stored as new public claims.</p>"
        if any(point.get("annotation") for point in metric["points"])
        else ""
    )
    compare_link = (
        f'<a class="text-link" href="?p=/compare&amp;metric={esc(metric_id)}" target="_self">'
        f'Compare two schools on this series {icon("arrow-right")}</a>'
    )
    write(f"""
<main class="school-index-series">
  <section class="shell tsr-tight-top">
    <div class="index-series-note">
      <p>{esc(metric["definition"])}</p>
      <p><strong>Comparison limit.</strong> {esc(metric["note"])}</p>
      {derived_note}
      <p>{esc(trajectory.GAP_RULE)} Rows stay in alphabetical order: a higher line is not a claim that one school is better.</p>
      {compare_link}
    </div>
  </section>
</main>""")

    rows = []
    for entry in matches:
        rows.append(f"""<article class="index-row index-row-charted">
  <div class="index-letter-cell"><p class="index-letter" aria-hidden="true">{esc(entry["name"][0])}</p></div>
  <div class="index-copy">
    <h2>{link(f'/schools/{entry["id"]}', esc(entry["name"]))}</h2>
    <p>{esc(entry["oneLine"])}</p>
  </div>
  {panels[entry["id"]]}
  <dl>
    <div><dt>Available years</dt><dd>{esc(entry["evidenceWindow"])}</dd></div>
    <div><dt>Datasets</dt><dd>{entry["datasets"]}</dd></div>
    <div><dt>Latest verified year</dt><dd>{entry["latestYear"] if entry["latestYear"] else "—"}</dd></div>
  </dl>
  {link(f'/schools/{entry["id"]}', icon("arrow-right"), "row-action", f' aria-label="View {esc(entry["name"])}"')}
</article>""")
    if not matches:
        rows.append(
            '<div class="empty-state"><h2>No school found</h2>'
            "<p>Try another spelling. The founding collection currently contains seven schools.</p></div>"
        )

    write(f"""
<main class="school-index-results">
  <section class="section shell tsr-tight-top">
    <p class="result-count" aria-live="polite">{len(matches)} {"school" if len(matches) == 1 else "schools"}</p>
    <div class="index-list">{"".join(rows)}</div>
  </section>
</main>""")


def school_record(slug: str) -> bool:
    school = records.find_school(slug)
    if school is None:
        return False
    exam = records.school_datasets(slug, ["exam_results"])
    university = records.school_datasets(
        slug, ["university_admissions", "university_destinations"]
    )
    applications = records.school_datasets(slug, ["university_admissions"])
    span = records.school_year_span(slug)

    write(f"""
<main id="main-content">
  <div class="shell">{breadcrumbs([("Schools", "/schools"), (school["name"], None)])}</div>
  <header class="school-hero shell">
    <div>
      <p class="eyebrow">School record · {span["min"]}–{span["max"]}</p>
      <h1>{esc(school["name"])}</h1>
      <p class="page-intro">{esc(school["oneLine"])}</p>
      <div class="button-row">
        {link(f"/schools/{slug}/exam-results", "Examination results", "button button-primary")}
        {link(f"/schools/{slug}/university-destinations", "University outcomes", "button button-secondary")}
      </div>
    </div>
    {artwork(slug, eager=True)}
  </header>

  <section class="section shell school-summary-grid">
    <div>{components.latest_record(exam)}</div>
    <aside class="record-caution">
      <p class="eyebrow">Read with care</p>
      <h2>Record boundary</h2>
      <p>{esc(school["caution"])}</p>
      {link("/methodology", f'Review the methodology {icon("arrow-right")}', "text-link")}
    </aside>
  </section>

  <section class="section shell trajectory-section" aria-labelledby="trajectory-title">
    <div class="section-heading">
      <div><p class="eyebrow">Published trajectory</p><h2 id="trajectory-title">Results by year</h2></div>
      <p>The school’s like-for-like examination series, one panel per grading ruler, drawn from the same frozen values the comparison tool uses.</p>
    </div>
    {_school_trajectory(slug)}
  </section>

  <section class="school-route-band">
    <div class="shell route-card-grid">
      <article class="route-card">
        {icon("graduation-cap")}
        <p class="eyebrow">{len(exam)} datasets</p>
        <h2>Examination results</h2>
        <p>A-level, GCSE, IB and Cambridge Pre-U records, each retained on the scale and denominator supplied by the source.</p>
        {link(f"/schools/{slug}/exam-results", f'Open examination record {icon("arrow-right")}', "text-link")}
      </article>
      <article class="route-card">
        {icon("library-big")}
        <p class="eyebrow">{len(university)} datasets</p>
        <h2>University outcomes</h2>
        <p>Application-cycle figures and final destinations are labelled precisely and kept apart.</p>
        {link(f"/schools/{slug}/university-destinations", f'Open university record {icon("arrow-right")}', "text-link")}
      </article>
    </div>
  </section>

  <section class="section shell">
    <div class="record-inventory">
      <p class="eyebrow">At a glance</p>
      <dl>
        <div><dt>Reviewed period</dt><dd>{esc(school["evidenceWindow"])}</dd></div>
        <div><dt>Examination datasets</dt><dd>{len(exam)}</dd></div>
        <div><dt>University datasets</dt><dd>{len(university)}</dd></div>
        <div><dt>Application-cycle datasets</dt><dd>{len(applications)}</dd></div>
      </dl>
    </div>
  </section>
</main>""")
    return True


def dataset_page(slug: str, kind: str) -> bool:
    school = records.find_school(slug)
    if school is None:
        return False
    is_exam = kind == "exam"
    domains = ["exam_results"] if is_exam else ["university_admissions", "university_destinations"]
    entries = records.school_datasets(slug, domains)
    title = "Examination results" if is_exam else "University outcomes"
    intro = (
        "Published grade-entry results are presented on their original qualification and grading scales. Structural breaks remain visible."
        if is_exam
        else "Applications, offers, acceptances and final destinations remain distinct. Read each dataset’s basis before comparing years."
    )
    notice_title = "Check the grading system" if is_exam else "Check the outcome type"
    notice_body = (
        "A-level, Cambridge Pre-U, IB and old- and new-scale GCSE results are not one continuous measure. The ledgers below retain those boundaries."
        if is_exam
        else "An offer is not an acceptance; an application-cycle acceptance is not automatically a leaver destination. The record does not convert one into another."
    )

    write(f"""
<main id="main-content">
  <div class="shell">{breadcrumbs([("Schools", "/schools"), (school["name"], f"/schools/{slug}"), (title, None)])}</div>
  <header class="page-hero">
    <div class="shell page-hero-grid">
      <div>
        <p class="eyebrow">{esc(school["name"])}</p>
        <h1>{esc(title)}</h1>
        <p class="page-intro">{esc(intro)}</p>
      </div>
      <aside class="page-note">
        <strong>{len(entries)} public datasets</strong>
        <p>{esc(school["caution"])}</p>
      </aside>
    </div>
  </header>

  <section class="section shell dataset-introduction">
    {components.latest_record(entries)}
    <div class="notice notice-warning">
      <strong>{esc(notice_title)}</strong>
      <p>{esc(notice_body)}</p>
      {link("/methodology", "How comparability works", "text-link")}
    </div>
  </section>

  <section class="ledger-section shell" aria-label="{esc(title)} datasets">
    {_dataset_stack(slug, tuple(domains), school["name"])}
  </section>
</main>""")
    return True


def not_found() -> None:
    write(f"""
<main id="main-content" class="section narrow-shell">
  <p class="eyebrow">Not found</p>
  <h1>That page is not in the record</h1>
  <p>The address may be incomplete or out of date.</p>
  {link("/", "Return home", "button button-primary")}
</main>""")
