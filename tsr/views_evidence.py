"""The evidence centre: records, sources and method."""

from __future__ import annotations

import re
from typing import Any, Sequence

import streamlit as st

from . import corpora, dataset, evidence, records
from .components import source_list, status_pill, summary_list
from .icons import icon
from .ui import breadcrumbs, controls, esc, link, page_hero, write

PAGE_SIZE = 25

SECTIONS = (
    ("records", "Records"),
    ("sources", "Sources"),
    ("method", "How the figures are checked"),
)

STATUS_FAMILIES = ("Primary", "Secondary", "Derived", "Reconstructed", "Conflict", "Not stated")


def _int(value: Any, fallback: int | None = None) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback


def _url(**params: Any) -> str:
    parts = ["p=/evidence"]
    for key, value in params.items():
        if value in (None, "", "all", 0, False):
            continue
        parts.append(f"{key}={esc(str(value))}")
    return "?" + "&".join(parts)


@st.cache_data(show_spinner=False)
def _record_card(record_id: str, open_details: bool) -> str:
    item = evidence.record(record_id)
    if item is None:
        return ""
    school_link = (
        link(f"/schools/{item.school_id}", esc(item.school))
        if item.school_id
        else f"<span>{esc(item.school)}</span>"
    )
    details = "".join(
        f"<div><dt>{esc(label)}</dt><dd>{esc(value)}</dd></div>"
        for label, value in evidence.detail_fields(item)
    )
    derived_note = (
        "<p class=\"record-note\">Derived record: calculated by the source corpus from other frozen counts and labelled as such.</p>"
        if item.corpus == "oxbridge" and "derived" in str(item.raw.get("metric_family", ""))
        else ""
    )
    conflict_note = ""
    if item.corpus == "us" and item.raw.get("conflict_group"):
        conflict_note = (
            f"<p class=\"record-note\">Part of published-difference group <code>{esc(item.raw['conflict_group'])}</code>: "
            + ("this version is the one used for analysis." if item.raw.get("canonical_for_analysis") else "another published version of this figure is used for analysis; this one is kept visible.")
            + "</p>"
        )
    ledger = link(item.route, f"Open where this figure is displayed {icon('arrow-right')}", "text-link")
    open_attr = " open" if open_details else ""
    return f"""<article class="evidence-record" id="{esc(item.id)}">
  <header>
    <div class="record-kicker">{status_pill(item.corpus_label)}<span>{esc(item.outcome)}</span></div>
    <h3>{esc(item.title)}</h3>
    <p class="record-line">{school_link} · <span>{esc(item.period)}</span> · <span class="record-status">Evidence status: {esc(item.status)}</span></p>
  </header>
  {summary_list(item.summary)}
  <details class="record-details"{open_attr}>
    <summary>Show details</summary>
    {derived_note}{conflict_note}
    <dl class="evidence-definition-list">{details}</dl>
    <div class="record-sources"><p class="eyebrow">Public sources</p>{source_list(item.refs)}</div>
    <div class="record-actions">{ledger}<a class="text-link" href="{_url(record=item.id)}" target="_self">Permanent link to this record</a></div>
  </details>
</article>"""


def _inventory() -> str:
    counts = evidence.counts()
    corrections = len(corpora.corrections())
    conflicts = len(corpora.conflicts())
    cards = "".join(
        f'<a href="{_url(section="records", corpus=key)}" target="_self"><strong>{counts[key]:,}</strong><span>{esc(label)}</span></a>'
        for key, label in evidence.CORPUS_LABELS.items()
    )
    return f"""<div class="evidence-inventory">
  {cards}
  <a href="?p=/corrections" target="_self"><strong>{corrections + conflicts}</strong><span>corrections and published differences</span></a>
</div>"""


def _section_nav(active: str) -> str:
    items = []
    for key, label in SECTIONS:
        current = ' aria-current="page"' if key == active else ""
        items.append(f'<a href="{_url(section=key)}" target="_self"{current}>{esc(label)}</a>')
    items = "".join(items)
    return f'<nav class="evidence-sections" aria-label="Evidence sections">{items}</nav>'


def _claim_banner(school: str | None, dataset_id: str, period: str, matched: Sequence[evidence.Record]) -> str:
    entry = next((item for item in dataset.figures()["datasets"] if item["dataset_id"] == dataset_id), None)
    label = records.dataset_label(entry) if entry else dataset_id
    where = f"{esc(school)} · " if school else ""
    count = len(matched)
    return f"""<div class="claim-banner">
  <p class="eyebrow">Tracing a displayed figure</p>
  <h2>{where}{esc(label)} · {esc(period)}</h2>
  <p>{count} frozen {"record" if count == 1 else "records"} carry this figure. Each is shown below with its published fields and public sources.</p>
  <a class="text-link" href="?p=/evidence" target="_self">Clear and search everything {icon("arrow-right")}</a>
</div>"""


def _records_section(params: Any) -> None:
    all_records = evidence.index()
    schools = [{"id": s["id"], "name": s["name"]} for s in dataset.schools()]
    school_ids = [s["id"] for s in schools]

    requested_record = params.get("record")
    claim_dataset = params.get("dataset")
    claim_period = params.get("period")
    claim_school = params.get("school") if claim_dataset else None
    claim_school_id = corpora.school_id_for(claim_school) if claim_school else None

    corpus_options = ["all", *evidence.CORPUS_LABELS]
    corpus_default = params.get("corpus") if params.get("corpus") in corpus_options else "all"
    school_default = params.get("school") if params.get("school") in school_ids else (claim_school_id or "all")
    domain_options = ["all", *evidence.DOMAIN_LABELS]
    domain_default = params.get("domain") if params.get("domain") in domain_options else "all"
    status_options = ["all", *STATUS_FAMILIES]
    status_default = params.get("status") if params.get("status") in status_options else "all"
    low, high = evidence.year_bounds(all_records)
    from_default = max(low, min(high, _int(params.get("from"), low) or low))
    to_default = max(from_default, min(high, _int(params.get("to"), high) or high))

    if requested_record:
        detail = _record_card(requested_record, True)
        if detail:
            write(f'<main class="evidence-body"><section class="shell"><div class="record-focus"><p class="eyebrow">Record</p>{detail}</div></section></main>')
        else:
            write('<main class="evidence-body"><section class="shell"><div class="empty-state"><h2>No such record</h2><p>The identifier is not in the frozen index.</p></div></section></main>')

    matched_claim: list[evidence.Record] = []
    if claim_dataset and claim_period:
        matched_claim = evidence.records_for_claim(claim_dataset, claim_period)
        write(f'<main class="evidence-body"><section class="shell">{_claim_banner(claim_school, claim_dataset, claim_period, matched_claim)}</section></main>')

    with controls("tsr-evidence"):
        top = st.columns([2.2, 1, 1])
        with top[0]:
            query = st.text_input("Search records", value=params.get("q") or "", key="evidence_q", placeholder="School, year, subject, university or measure")
        with top[1]:
            corpus = st.selectbox("Record type", corpus_options, index=corpus_options.index(corpus_default), format_func=lambda v: "All records" if v == "all" else evidence.CORPUS_LABELS[v], key="evidence_corpus")
        with top[2]:
            school_choice = st.selectbox("School", ["all", *school_ids], index=(["all", *school_ids]).index(school_default), format_func=lambda v: "All schools" if v == "all" else next(s["name"] for s in schools if s["id"] == v), key="evidence_school")
        bottom = st.columns([1.2, 1.2, 0.7, 0.7])
        with bottom[0]:
            domain = st.selectbox("Outcome", domain_options, index=domain_options.index(domain_default), format_func=lambda v: "All outcomes" if v == "all" else evidence.DOMAIN_LABELS[v], key="evidence_domain")
        with bottom[1]:
            status = st.selectbox("Evidence status", status_options, index=status_options.index(status_default), format_func=lambda v: "Any status" if v == "all" else v, key="evidence_status")
        with bottom[2]:
            year_from = st.number_input("From", min_value=low, max_value=high, value=from_default, step=1, key="evidence_from")
        with bottom[3]:
            year_to = st.number_input("To", min_value=int(year_from), max_value=high, value=max(int(year_from), to_default), step=1, key="evidence_to")

    year_from, year_to = int(year_from), int(year_to)
    state = {
        "q": query.strip() or None,
        "corpus": None if corpus == "all" else corpus,
        "school": None if school_choice == "all" else school_choice,
        "domain": None if domain == "all" else domain,
        "status": None if status == "all" else status,
        "from": None if year_from == low else str(year_from),
        "to": None if year_to == high else str(year_to),
    }
    current = {key: params.get(key) for key in state}
    if not (claim_dataset and claim_period) and current != state:
        keep = {"p": "/evidence"}
        for key, value in state.items():
            if value is not None:
                keep[key] = value
        if requested_record:
            keep["record"] = requested_record
        st.query_params.from_dict(keep)

    items = matched_claim if (claim_dataset and claim_period) else all_records
    results = evidence.filter_records(
        items,
        corpus=state["corpus"],
        school_id=state["school"],
        domain=state["domain"],
        status=state["status"],
        year_from=year_from if year_from != low else None,
        year_to=year_to if year_to != high else None,
        query=state["q"],
    )
    page = max(1, _int(params.get("page"), 1) or 1)
    pages = max(1, -(-len(results) // PAGE_SIZE))
    page = min(page, pages)
    start = (page - 1) * PAGE_SIZE
    shown = results[start:start + PAGE_SIZE]

    def page_url(number: int) -> str:
        return _url(**{k: v for k, v in state.items()}, dataset=claim_dataset, period=claim_period, page=number if number > 1 else None)

    pager = ""
    if pages > 1:
        prev_link = f'<a href="{page_url(page - 1)}" target="_self">{icon("arrow-right")} Previous</a>' if page > 1 else "<span></span>"
        next_link = f'<a href="{page_url(page + 1)}" target="_self">Next {icon("arrow-right")}</a>' if page < pages else "<span></span>"
        pager = f'<nav class="evidence-pager" aria-label="Result pages">{prev_link}<span>Page {page} of {pages}</span>{next_link}</nav>'

    cards = "".join(_record_card(item.id, False) for item in shown)
    if not shown:
        cards = (
            '<div class="empty-state"><h2>No matching records</h2>'
            "<p>Try a school name, a different year or a broader search. A missing record is never manufactured.</p></div>"
        )
    write(f"""
<main class="evidence-body">
  <section class="shell evidence-results">
    <p class="result-count" aria-live="polite">{len(results):,} {"record" if len(results) == 1 else "records"}{" · showing " + str(start + 1) + "–" + str(start + len(shown)) if len(results) > PAGE_SIZE else ""}</p>
    <div class="evidence-list">{cards}</div>
    {pager}
  </section>
</main>""")


@st.cache_data(show_spinner=False)
def _sources_section() -> str:
    catalog = corpora.source_catalog()
    usage: dict[str, dict[str, Any]] = {}
    for entry in dataset.figures()["datasets"]:
        refs = set(entry.get("source_refs") or [])
        for row in entry["rows"]:
            refs.update(str(item) for item in (row.get("source_ids") or []))
        for ref in refs:
            use = usage.setdefault(ref, {"datasets": set(), "domains": {}, "schools": set()})
            use["datasets"].add(entry["dataset_id"])
            use["domains"][entry["domain"]] = None
            use["schools"].add(entry["school"])

    def natural(value: str) -> list[Any]:
        return [int(part) if part.isdigit() else part.lower() for part in re.split(r"(\d+)", value)]

    rows = []
    for key in sorted(catalog, key=natural):
        from . import sources as source_register

        described = source_register.describe(key)
        use = usage.get(key, {"datasets": set(), "domains": {}, "schools": set()})
        title = (
            f'<a class="source-link" href="{esc(described["url"])}" target="_blank" rel="noreferrer noopener">{esc(described["title"])} {icon("arrow-right")}</a>'
            if described["url"]
            else (f'<span class="source-withheld">{esc(described["title"])}</span>' if described["withheld"] else esc(described["title"]))
        )
        role = f'<p class="source-role">{esc(described["role"])}</p>' if described.get("role") else ""
        domains = " · ".join(evidence.DOMAIN_LABELS.get(d, d) for d in use["domains"])
        rows.append(f"""<article class="evidence-entry" id="source-{esc(key)}">
  <div><p class="source-ref">{esc(key)}</p></div>
  <div><h3>{title}</h3>{role}<p>{esc(domains) if domains else "Cited by the Oxford, Cambridge or US corpora"}</p></div>
  <dl>
    <div><dt>Linked datasets</dt><dd>{len(use["datasets"])}</dd></div>
    <div><dt>Location</dt><dd>{"Public link above" if described["url"] else "Withheld · available on request"}</dd></div>
  </dl>
</article>""")
    linked = sum(1 for key in catalog if key in usage)
    public = sum(1 for key in catalog if source_register.public_link(key))
    oxbridge_sources = len(corpora.oxbridge_corpus().get("sources") or [])
    return f"""<main class="evidence-body">
  <section class="section shell">
    <div class="evidence-key">
      <div><span class="status-pill">Official / primary</span><p>Published by the originating school, university, regulator or examination body.</p></div>
      <div><span class="status-pill">Calculated</span><p>Mechanically calculated from an official table, with the source values retained.</p></div>
      <div><span class="status-pill">Estimated / bounded</span><p>Kept visibly distinct from an exact figure, with its method or limits where recorded.</p></div>
    </div>
    <div class="section-heading register-heading">
      <div><p class="eyebrow">Register</p><h2>{len(catalog)} source references</h2></div>
      <p>{linked} cited by the ledgers · {public} with an approved public link · {oxbridge_sources} further Oxford and Cambridge documents identified by reference only · snapshot {esc(dataset.metadata()["snapshot_version"])}</p>
    </div>
    <p class="register-note">A reference is stable even when its document is private. First-party school pages, public-body releases and Internet Archive captures kept by the reviewed public edition are linked; private working documents, archive paths and research notes are not, and their titles are withheld.</p>
    <div class="evidence-register">{"".join(rows)}</div>
  </section>
</main>"""


@st.cache_data(show_spinner=False)
def _method_section() -> str:
    definitions = corpora.definitions()
    codes = definitions.get("confidence_codes", {})
    code_rows = "".join(
        f'<tr><th scope="row">{esc(code)}</th><td>{esc(meaning)}</td></tr>' for code, meaning in codes.items()
    )
    term_cards = "".join(
        f'<section class="method-card"><p class="eyebrow">Definition</p><h3>{esc(term.replace("_", " ").capitalize())}</h3><p>{esc(text)}</p></section>'
        for term, text in definitions.items()
        if isinstance(text, str)
    )
    grade_map = definitions.get("grade_mapping", {})
    grade_cards = "".join(
        f'<section class="method-card"><p class="eyebrow">Grade mapping</p><h3>{esc(key.replace("_", " ").upper() if key != "kcs_ib" else "KCS internal IB headline")}</h3><p>{esc(text)}</p></section>'
        for key, text in grade_map.items()
    )
    guardrails = "".join(f"<li>{esc(item)}</li>" for item in corpora.guardrails())
    authority = "".join(
        f'<tr><th scope="row">{item["order"]}</th><td>{esc(item["version"])}</td><td>{esc(item["controls"])}</td><td>{esc(item.get("does_not_control") or "—")}</td></tr>'
        for item in corpora.version_authority()
    )
    lineage = "".join(
        f'<li><time>{esc(item["versions"])}</time><div><h3>{esc(item["phase"].capitalize())}</h3><p>{esc(item["effect"])}</p></div></li>'
        for item in corpora.lineage()
    )
    oxbridge_defs = corpora.oxbridge_corpus().get("metric_definitions", {})
    oxbridge_rows = "".join(
        f'<tr><th scope="row">{esc(key.replace("_", " ").capitalize())}</th><td>{esc(text)}</td></tr>' for key, text in oxbridge_defs.items()
    )
    us_safeguards = "".join(f"<li>{esc(item)}</li>" for item in corpora.us_corpus().get("safeguards", []))
    return f"""<main class="evidence-body">
  <section class="section shell content-grid">
    <article class="prose">
      <h2>How the figures are checked</h2>
      <p>Every figure keeps the definition its publisher used. Where a later, better source corrects an earlier value, the record uses the corrected value and keeps the change visible; where credible publications disagree, both values stay visible with the treatment applied. {link("/corrections", "Read the corrections and published differences", "text-link")}</p>
      <h3>Evidence status codes</h3>
      <table><thead><tr><th scope="col">Code</th><th scope="col">Meaning</th></tr></thead><tbody>{code_rows}</tbody></table>
      <h3>Definitions used by the ledgers</h3>
      <div class="method-grid">{term_cards}</div>
      <h3>Grade mappings</h3>
      <div class="method-grid">{grade_cards}</div>
      <h3>Rules the presentation follows</h3>
      <ol>{guardrails}</ol>
      <h3>Which compilation controls</h3>
      <p>The source compilations are layered: a later companion does not overwrite a detailed annual table it merely elides.</p>
      <table><thead><tr><th scope="col">Order</th><th scope="col">Version</th><th scope="col">Controls</th><th scope="col">Does not control</th></tr></thead><tbody>{authority}</tbody></table>
      <h3>Lineage of the compilation</h3>
      <ol class="timeline">{lineage}</ol>
      <h3>Oxford and Cambridge records</h3>
      <table><tbody>{oxbridge_rows}</tbody></table>
      <h3>US and overseas university records</h3>
      <ul>{us_safeguards}</ul>
    </article>
    <aside class="side-index">
      <h2>Related</h2>
      <nav>{link("/methodology", "Methodology")}{link("/corrections", "Corrections and published differences")}{link("/oxbridge", "Oxford and Cambridge records")}{link("/us-universities", "US university records")}</nav>
    </aside>
  </section>
</main>"""


def evidence_centre() -> None:
    params = st.query_params
    section = params.get("section") if params.get("section") in dict(SECTIONS) else "records"
    if params.get("record") or params.get("dataset"):
        section = "records"
    write(f"""
<main id="main-content">
  <div class="shell">{breadcrumbs([("Evidence", None)])}</div>
  {page_hero(
      "Evidence centre",
      "Every record, traceable",
      "Search the 2,277 frozen records across all four corpora, move from a displayed figure back to its public sources, and read how the figures are checked.",
      "Private working documents stay private. Each record is identified by stable public references, and linked where the source is itself public.",
  )}
  <section class="shell evidence-head">
    {_inventory()}
    {_section_nav(section)}
  </section>
</main>""")
    if section == "records":
        _records_section(params)
    elif section == "sources":
        write(_sources_section())
    else:
        write(_method_section())
