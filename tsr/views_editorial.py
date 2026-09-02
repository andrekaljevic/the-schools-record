"""Methodology, evidence register, professional pages and legal notices."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import streamlit as st

from . import comparison, dataset
from .chart import comparison_chart
from .icons import icon
from .ui import LAST_REVIEWED, breadcrumbs, esc, link, page_hero, write

TEMPLATES = Path(__file__).resolve().parents[1] / "pages_html"

METHODOLOGY_SECTIONS = (
    ("principles", "Core principles"),
    ("populations", "Populations"),
    ("grading", "Grading systems"),
    ("exceptional", "Exceptional periods"),
    ("outcomes", "Outcome types"),
    ("derived", "Derived presentation"),
    ("limits", "Limitations"),
)

POPULATION_TERMS = (
    ("Candidates or pupils", "People in the reported cohort, where the publication supplies that count."),
    ("Exam entries", "Individual subject-grade entries. One pupil commonly contributes several."),
    ("Applications", "Applications attributed to a named entry cycle and apply centre."),
    ("Offers or admissions", "Positive admissions decisions; not proof of a destination."),
    ("Final destinations", "Places reported as taken up by a leaver or entry-year population."),
)


def _natural_key(value: str) -> list[Any]:
    return [
        int(part) if part.isdigit() else part.lower()
        for part in re.split(r"(\d+)", value)
    ]


def static_page(name: str) -> None:
    write(TEMPLATES.joinpath(f"{name}.html").read_text(encoding="utf-8"))


def methodology() -> None:
    scales = list(dataset.presentation()["grading_scales"].values())
    cards = "".join(
        f"""<section class="method-card">
  <p class="eyebrow">{esc(scale["qualification"])}</p>
  <h3>{esc(scale["label"])}</h3>
  <p><strong>Denominator:</strong> {esc(scale["denominator"])}</p>
  <p>{esc(scale["note"])}</p>
</section>"""
        for scale in scales
    )
    terms = "".join(
        f'<tr><th scope="row">{esc(term)}</th><td>{esc(meaning)}</td></tr>'
        for term, meaning in POPULATION_TERMS
    )
    index = "".join(
        f'<a href="#{anchor}">{esc(label)}</a>' for anchor, label in METHODOLOGY_SECTIONS
    )

    write(f"""
<main id="main-content">
  <div class="shell">{breadcrumbs([("Methodology", None)])}</div>
  {page_hero(
      "Editorial method",
      "Definitions before comparisons",
      "The Schools Record reconstructs published history without pretending that every figure measures the same thing.",
      "We do not treat offers as destinations, pupils as exam entries, or incompatible grading systems as one continuous league table.",
      note_tag="blockquote",
  )}
  <section class="section shell content-grid">
    <article class="prose">
      <span class="tsr-anchor" id="principles"></span><h2>Core principles</h2>
      <p>Each record retains the year or period, qualification, grading system, population, denominator, outcome type and evidence status that are present in the frozen source record. Missing information stays missing. A blank is not zero, and no absent value is interpolated.</p>
      <h3>Source-led</h3>
      <p>Figures are tied to stable public evidence references. Direct document locations and internal research notes are held privately; removing those locations from public output does not change the figure or its evidence classification.</p>
      <h3>Lossless</h3>
      <p>Exact values remain exact, ranges keep both bounds, lower bounds remain lower bounds, and estimates retain their classification. Display precision is preserved.</p>
      <h3>Diagnostic validation only</h3>
      <p>Automated checks may flag an unusual value, duplicate or denominator. They never edit the frozen production record. Production parity outranks a validator’s opinion.</p>
      <span class="tsr-anchor" id="populations"></span><h2>Populations and denominators</h2>
      <p>A pupil can sit several qualifications and generate several subject entries. Candidate counts therefore cannot be substituted for entry counts. Likewise, the cohort used for a destination percentage may not be the cohort used for an application-cycle rate.</p>
      <table>
        <thead><tr><th scope="col">Term</th><th scope="col">Meaning in this record</th></tr></thead>
        <tbody>{terms}</tbody>
      </table>
      <span class="tsr-anchor" id="grading"></span><h2>Grading systems</h2>
      <p>Structural breaks are a feature of the evidence, not an inconvenience to hide. The comparison tool includes a series only when its ruler matches the metric definition.</p>
      <div class="method-grid">{cards}</div>
      <span class="tsr-anchor" id="exceptional"></span><h2>Exceptional periods</h2>
      <p>Centre-assessed grades in 2020 and teacher-assessed grades in 2021 did not arise from ordinary external examinations. Where the frozen record identifies those periods, the distinction remains visible and they are excluded by default from like-for-like examination comparisons.</p>
      <span class="tsr-anchor" id="outcomes"></span><h2>University outcome types</h2>
      <p>Oxford and Cambridge application-cycle evidence can include applications, offers and accepted or admitted outcomes. School publications may instead report a leaver destination. These may concern different populations and time points. The product does not convert between them.</p>
      <span class="tsr-anchor" id="derived"></span><h2>Derived presentation</h2>
      <p>Charts, sorting and display-only rates are deterministic calculations from frozen values. They never estimate a missing value and never overwrite source-published figures. A calculated display is labelled as such.</p>
      <span class="tsr-anchor" id="limits"></span><h2>Limitations</h2>
      <p>This is a record of published outcomes, not a causal measure of teaching quality. It does not control for prior attainment, admissions selectivity, subject choices, cohort composition or school aims. No “winner” is declared.</p>
    </article>
    <aside class="side-index">
      <h2>On this page</h2>
      <nav>{index}</nav>
    </aside>
  </section>
</main>""")


@st.cache_data(show_spinner=False)
def _evidence_register() -> list[tuple[str, list[str], int]]:
    """Reference → (domains in first-seen order, linked dataset count)."""
    register: dict[str, dict[str, dict[str, None]]] = {}
    for entry in dataset.figures()["datasets"]:
        for ref in entry.get("source_refs") or []:
            record = register.setdefault(ref, {"datasets": {}, "domains": {}})
            record["datasets"][entry["dataset_id"]] = None
            record["domains"][entry["domain"]] = None
    ordered = sorted(register.items(), key=lambda item: _natural_key(item[0]))
    return [
        (ref, list(record["domains"]), len(record["datasets"]))
        for ref, record in ordered
    ]


def evidence() -> None:
    ordered = _evidence_register()
    entries = "".join(
        f"""<article class="evidence-entry" id="source-{esc(ref)}">
  <div><p class="source-ref">{esc(ref)}</p></div>
  <div><h3>Public evidence reference {esc(ref)}</h3><p>{esc(" · ".join(domain.replace("_", " ") for domain in domains))}</p></div>
  <dl>
    <div><dt>Linked datasets</dt><dd>{linked}</dd></div>
    <div><dt>Document location</dt><dd>Available on request</dd></div>
  </dl>
</article>"""
        for ref, domains, linked in ordered
    )

    write(f"""
<main id="main-content">
  <div class="shell">{breadcrumbs([("Evidence", None)])}</div>
  {page_hero(
      "Public evidence register",
      "Evidence without private locations",
      "Stable references show what supports each dataset. Direct URLs, archive paths, Drive identifiers and internal research notes are withheld.",
      "Underlying documents can be discussed for legitimate research or correction work. Publication remains subject to rights, privacy and source-security checks.",
  )}
  <section class="section shell">
    <div class="evidence-key">
      <div><span class="status-pill">Official / primary</span><p>Published by the originating school, university, regulator or examination body.</p></div>
      <div><span class="status-pill">Calculated</span><p>Mechanically calculated from an official table, with the source values retained.</p></div>
      <div><span class="status-pill">Estimated / bounded</span><p>Kept visibly distinct from an exact figure, with its method or limits where recorded.</p></div>
    </div>
    <div class="section-heading register-heading">
      <div><p class="eyebrow">Register</p><h2>{len(ordered)} evidence references</h2></div>
      <p>Snapshot {esc(dataset.metadata()["snapshot_version"])}</p>
    </div>
    <div class="evidence-register">{entries}</div>
  </section>
</main>""")


OFFER_ONE = (
    "Examination and university-outcome charts",
    "Definitions, evidence statuses and limitations",
    "Public source references",
    "PDF and structured-data deliverables",
    "Editorial interpretation without causal overclaiming",
)
OFFER_TWO = (
    "Richer, sanitised exports",
    "Bespoke school sets and defined monitoring",
    "Methodological support",
    "Research licensing",
    "Separately commissioned future reconstruction work",
)
PROCESS = (
    ("01", "Define the decision", "Tell us which schools, years and outcome questions matter."),
    ("02", "Confirm the evidence boundary", "We identify what can and cannot be compared before work begins."),
    ("03", "Agree the deliverable", "Scope, timing, format and a human-reviewed proposal are confirmed."),
    ("04", "Deliver with provenance", "Figures arrive with their definitions, evidence status and caveats."),
)


def professional() -> None:
    offer_one = "".join(f"<li>{esc(item)}</li>" for item in OFFER_ONE)
    offer_two = "".join(f"<li>{esc(item)}</li>" for item in OFFER_TWO)
    process = "".join(
        f"<li><span>{number}</span><h3>{esc(title)}</h3><p>{esc(body)}</p></li>"
        for number, title, body in PROCESS
    )

    write(f"""
<main id="main-content">
  <div class="shell">{breadcrumbs([("Professional", None)])}</div>
  <header class="professional-hero">
    <div class="shell">
      <p class="eyebrow">Professional research</p>
      <h1>Evidence made decision-ready</h1>
      <p class="page-intro">For consultants, researchers, journalists, school leaders, communications teams and highly engaged parents who need a defensible comparison rather than a generic ranking.</p>
      <div class="button-row">
        <a class="button button-primary" href="#enquire">Request a sourced comparison</a>
        {link("/sample-dossier", "View a sample dossier", "button button-secondary")}
      </div>
    </div>
  </header>
  <section class="section shell">
    <div class="offer-grid">
      <article class="offer-card">
        {icon("file-text")}
        <p class="eyebrow">Offer 01</p>
        <h2>Sourced school comparison dossier</h2>
        <p>A defined, decision-ready report comparing selected schools and periods using the frozen record.</p>
        <ul>{offer_one}</ul>
        {link("/sample-dossier", f'Inspect the sample {icon("arrow-right")}', "text-link")}
      </article>
      <article class="offer-card">
        {icon("layers")}
        <p class="eyebrow">Offer 02</p>
        <h2>Professional data and research access</h2>
        <p>Scoped access for recurring professional use, built around the same methodological boundaries as the public record.</p>
        <ul>{offer_two}</ul>
        <a class="text-link" href="#enquire">Discuss professional access {icon("arrow-right")}</a>
      </article>
    </div>
    <div class="pricing-note">
      <p class="eyebrow">Scope before price</p>
      <p>Prices are not published in this preview. A proposal depends on the school set, period, intended use, evidence depth, format and deadline. No payment is taken through this site.</p>
    </div>
  </section>
  <section class="professional-process">
    <div class="shell">
      <p class="eyebrow">A restrained process</p>
      <ol>{process}</ol>
    </div>
  </section>
  <section class="section narrow-shell tsr-flush-bottom" id="enquire">
    <div class="form-intro">
      <p class="eyebrow">Start an enquiry</p>
      <h2>Request a sourced comparison</h2>
      <p>Only useful scoping details are requested. Submission creates an internal review item; it does not trigger payment or automated external email.</p>
    </div>
  </section>
</main>""")


def sample_dossier() -> None:
    metric = next(
        (item for item in comparison.metrics() if item["id"] == "a_level_astar"), None
    )
    points = [
        point
        for point in (metric["points"] if metric else [])
        if point["schoolId"] in ("eton", "westminster") and 2015 <= point["year"] <= 2019
    ]
    years = sorted({point["year"] for point in points})

    def cell(school_id: str, year: int) -> tuple[str, str]:
        match = next(
            (
                point
                for point in points
                if point["schoolId"] == school_id and point["year"] == year
            ),
            None,
        )
        if match is None:
            return "—", "—"
        return f"{match['value']:.1f}%", match["status"]

    chart = (
        comparison_chart(metric, "eton", "westminster", 2015, 2019) if points else ""
    )

    rows = []
    for year in years:
        eton_value, eton_status = cell("eton", year)
        west_value, west_status = cell("westminster", year)
        rows.append(
            f'<tr><th scope="row">{year}</th><td>{esc(eton_value)}</td><td>{esc(eton_status)}</td>'
            f"<td>{esc(west_value)}</td><td>{esc(west_status)}</td></tr>"
        )

    write(f"""
<main id="main-content" class="dossier-page">
  <div class="shell">{breadcrumbs([("Professional", "/professional"), ("Sample dossier", None)])}</div>
  <header class="dossier-cover">
    <div class="shell dossier-cover-grid">
      <div>
        <p class="dossier-series">The Schools Record · Professional series</p>
        <p class="eyebrow">Illustrative sample</p>
        <h1>A sourced examination comparison</h1>
        <p class="dossier-subtitle">Eton College and Westminster School · A-level grades at A* · 2015–2019</p>
        <p class="dossier-disclaimer">This sample demonstrates structure and editorial method using the frozen public dataset. It is not a recommendation or a claim that either school is better.</p>
      </div>
      <div class="dossier-stamp"><span>Sample</span><strong>01</strong><p>Prepared<br/>{LAST_REVIEWED}</p></div>
    </div>
  </header>
  <nav class="dossier-actions shell">
    <a class="button button-primary" href="app/static/the-schools-record-sample-dossier.pdf" download>{icon("arrow-down-to-line")} Download sample PDF</a>
    <a class="button button-secondary" href="?p=/professional#enquire" target="_self">Request a sourced comparison</a>
  </nav>
  <section class="dossier-section shell">
    <div class="dossier-number">01</div>
    <article>
      <p class="eyebrow">Executive reading</p>
      <h2>What is being compared</h2>
      <p class="dossier-lead">The share of published A-level subject entries awarded A* in each named examination year. The denominator is entries, not pupils or candidates.</p>
      <div class="dossier-callouts">
        <div><strong>Qualification</strong><span>A level only</span></div>
        <div><strong>Grading system</strong><span>A*–E</span></div>
        <div><strong>Population</strong><span>Published subject entries</span></div>
        <div><strong>Outcome type</strong><span>Exam grade, not destination</span></div>
      </div>
      <div class="notice notice-warning">
        <strong>Interpretive limit</strong>
        <p>The series does not control for subject mix, prior attainment, cohort characteristics or admissions selection. The figures describe published outcomes; they do not identify causes.</p>
      </div>
    </article>
  </section>
  <section class="dossier-section shell">
    <div class="dossier-number">02</div>
    <article>
      <p class="eyebrow">Exact-value exhibit</p>
      <h2>Five-year published record</h2>
      <div class="series-legend"><span><i class="series-colour colour-1"></i>Eton College</span><span><i class="series-colour colour-2"></i>Westminster School</span></div>
      {chart}
      <div class="table-scroll" tabindex="0">
        <table class="data-table dossier-table">
          <caption>A-level entries awarded A*, 2015–2019</caption>
          <thead><tr><th scope="col">Year</th><th scope="col">Eton College</th><th scope="col">Evidence</th><th scope="col">Westminster School</th><th scope="col">Evidence</th></tr></thead>
          <tbody>{"".join(rows)}</tbody>
        </table>
      </div>
      <p class="table-note">Values are rendered directly from the immutable production snapshot. No missing year is estimated and no competing value is averaged.</p>
    </article>
  </section>
  <section class="dossier-section shell">
    <div class="dossier-number">03</div>
    <article>
      <p class="eyebrow">Method note</p>
      <h2>Why the boundary matters</h2>
      <div class="dossier-columns">
        <p>This exhibit deliberately uses an A-level-only ruler. Cambridge Pre-U, IB Higher Level and school-defined mixed-qualification measures are not folded into it, even where a source supplies an equivalence.</p>
        <p>Centre-assessed 2020 and teacher-assessed 2021 values are omitted from the default like-for-like series. Their absence is not treated as zero and the surrounding years are not joined through an inferred value.</p>
      </div>
      <blockquote>Good comparison is often the discipline of refusing a convenient but false equivalence.</blockquote>
    </article>
  </section>
  <section class="dossier-cta">
    <div class="shell">
      <div><p class="eyebrow">Commission a defined dossier</p><h2>Start with the decision you need to make</h2></div>
      <a class="button button-primary" href="?p=/professional#enquire" target="_self">Request a sourced comparison</a>
    </div>
  </section>
</main>""")
