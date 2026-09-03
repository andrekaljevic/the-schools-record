"""Record components: ledgers, tables, evidence panels, indexes."""

from __future__ import annotations

import base64
import csv
import io
import re
from typing import Any, Sequence

from . import corpora, dataset, format as fmt, records, sources
from .icons import icon
from .ui import esc, href, link

EXCLUDED_EXPANDED = ("source_url", "source_ids")


def slugify(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(value).lower()).strip("-") or "row"


def row_anchor(dataset_id: str, row: dict[str, Any], index: int | None = None) -> str:
    """The stable address of one ledger row.

    ``{dataset_id}-{period}`` for the first row with a period; when later rows
    share that period (an undated destination list, a year published on two
    scales) each carries its index in the frozen dataset, which is also the
    index in its evidence record id.
    """
    anchor = f"{dataset_id}-{slugify(records.period_label(row))}"
    return anchor if index is None else f"{anchor}-r{index}"


def row_anchors(entry: dict[str, Any]) -> dict[int, str]:
    """Row index → unique anchor for every row of a dataset."""
    seen: set[str] = set()
    anchors: dict[int, str] = {}
    for index, row in enumerate(entry["rows"]):
        slug = slugify(records.period_label(row))
        anchors[index] = row_anchor(entry["dataset_id"], row, index if slug in seen else None)
        seen.add(slug)
    return anchors


def _row_source_refs(entry: dict[str, Any], row: dict[str, Any]) -> list[str]:
    """The references cited for one row, falling back to the dataset's own."""
    row_ids = row.get("source_ids")
    ids = [str(item) for item in row_ids] if isinstance(row_ids, list) else []
    return list(dict.fromkeys(ids or (entry.get("source_refs") or [])))


def _row_status(row: dict[str, Any]) -> str:
    for key in ("publication_status", "confidence", "evidence_status"):
        value = row.get(key)
        if value is not None:
            return str(value)
    return ""


def source_list(refs: Sequence[str]) -> str:
    """The public description of each source reference, linked where approved."""
    items = []
    for source in sources.linked_sources(list(refs)):
        ref = esc(source["ref"])
        title = esc(source["title"])
        role = f'<span class="source-role">{esc(source["role"])}</span>' if source.get("role") else ""
        if source["url"]:
            head = (
                f'<a class="source-link" href="{esc(source["url"])}" target="_blank" rel="noreferrer noopener">'
                f"{title} {icon('arrow-right')}</a>"
            )
        elif source["withheld"]:
            head = f'<span class="source-withheld">{title}</span>'
        else:
            head = f"<span>{title}</span>"
        items.append(f'<li><code class="source-key">{ref}</code>{head}{role}</li>')
    if not items:
        return '<p class="source-none">No public reference recorded.</p>'
    return f'<ul class="source-list">{"".join(items)}</ul>'


def evidence_disclosure(
    school_name: str,
    dataset_id: str,
    period: str,
    source_refs: Sequence[str],
    status: str,
    note: str | None,
    dataset_refs: int = 0,
) -> str:
    note_block = (
        f"<div><dt>Record note</dt><dd>{esc(note)}</dd></div>" if note else ""
    )
    dataset_line = (
        f'<div><dt>Dataset sources</dt><dd><a href="#{esc(dataset_id)}-sources">{dataset_refs} further {"reference" if dataset_refs == 1 else "references"} listed under the ledger</a></dd></div>'
        if dataset_refs
        else ""
    )
    register = (
        f"?p=/evidence&school={esc(school_name)}&dataset={esc(dataset_id)}"
        f"&period={esc(period)}"
    )
    status_label = fmt.format_value("confidence", status, {}) if status else "Not stated"
    return f"""<details class="evidence-disclosure">
  <summary class="evidence-button">View evidence</summary>
  <div class="evidence-panel">
    <div class="dialog-heading"><div><p class="eyebrow">Evidence for {esc(period)}</p><h2>{esc(school_name)}</h2></div></div>
    <dl class="evidence-definition-list">
      <div><dt>Dataset</dt><dd><code>{esc(dataset_id)}</code></dd></div>
      <div><dt>Evidence status</dt><dd>{esc(status_label)}</dd></div>
      <div><dt>Row sources</dt><dd>{source_list(source_refs)}</dd></div>
      {dataset_line}
      {note_block}
    </dl>
    <p class="dialog-privacy-note">Private working documents are withheld. A public reference identifies the evidence; where the source is itself public, its link is given.</p>
    <div class="dialog-actions"><a class="text-link" href="{register}" target="_self">Trace this figure in the evidence centre {icon("arrow-right")}</a></div>
  </div>
</details>"""


def data_table(
    entry: dict[str, Any], fields: Sequence[str], school_name: str, suffix: str
) -> str:
    label = records.dataset_label(entry)
    head = "".join(f'<th scope="col">{esc(fmt.field_label(field))}</th>' for field in fields)
    body: list[str] = []
    anchors = row_anchors(entry)
    index_of = {id(row): index for index, row in enumerate(entry["rows"])}
    for row in records.sorted_rows(entry):
        period = records.period_label(row)
        cells = []
        for field in fields:
            value = fmt.cell_value(row, field)
            blank = ' class="blank-value"' if value is None or value == "" else ""
            cells.append(
                f'<td data-label="{esc(fmt.field_label(field))}"{blank}>'
                f"{esc(fmt.format_value(field, value, row))}</td>"
            )
        if suffix == "ordinary":
            note = row.get("note") if isinstance(row.get("note"), str) else None
            row_refs = _row_source_refs(entry, row)
            dataset_refs = [ref for ref in (entry.get("source_refs") or []) if ref not in row_refs]
            cells.append(
                '<td data-label="Source">'
                + evidence_disclosure(
                    school_name,
                    entry["dataset_id"],
                    period,
                    row_refs,
                    _row_status(row),
                    note,
                    len(dataset_refs),
                )
                + "</td>"
            )
        anchor = anchors[index_of[id(row)]] if suffix == "ordinary" else ""
        attrs = f' id="{esc(anchor)}"' if anchor else ""
        body.append(f"<tr{attrs}>{''.join(cells)}</tr>")
    source_head = '<th scope="col">Source</th>' if suffix == "ordinary" else ""
    return f"""<div class="table-scroll" tabindex="0" aria-label="Scrollable table: {esc(label)}">
  <table class="data-table">
    <caption>{esc(label)}. Dashes represent blank values preserved from the frozen record. {len(fields)} columns; scroll sideways on a narrow screen.</caption>
    <thead><tr>{head}{source_head}</tr></thead>
    <tbody>{''.join(body)}</tbody>
  </table>
  <span class="sr-only">End of {esc(suffix)} table</span>
</div>"""


def dataset_csv(entry: dict[str, Any]) -> str:
    fields = [
        field
        for field in fmt.table_fields(entry["rows"], expanded=True)
    ]
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(fields)
    for row in records.sorted_rows(entry):
        writer.writerow([_csv_value(fmt.cell_value(row, field)) for field in fields])
    return buffer.getvalue()


def _csv_value(value: Any) -> Any:
    """A stored value as a CSV cell: blanks stay blank and lists are joined, never printed as Python literals."""
    if value is None:
        return ""
    if isinstance(value, list):
        return "; ".join(str(item) for item in value)
    return value


def _csv_download(entry: dict[str, Any]) -> str:
    payload = base64.b64encode(dataset_csv(entry).encode("utf-8")).decode("ascii")
    return (
        f'<a class="button button-quiet" download="{esc(entry["dataset_id"])}.csv" '
        f'href="data:text/csv;charset=utf-8;base64,{payload}">Download CSV</a>'
    )


def dataset_span(entry: dict[str, Any]) -> str:
    years = [records.row_year(row) for row in entry["rows"]]
    years = [year for year in years if year is not None]
    if not years:
        return "undated"
    return str(min(years)) if min(years) == max(years) else f"{min(years)}–{max(years)}"


def series_index(entries: Sequence[dict[str, Any]], title: str = "In this record") -> str:
    """A jump list of every ledger on the page, typed by qualification or outcome family."""
    if not entries:
        return ""
    items = "".join(
        f'<li><a href="#{esc(entry["dataset_id"])}"><span class="series-family">{esc(records.dataset_family(entry))}</span>'
        f'<strong>{esc(records.dataset_label(entry))}</strong>'
        f'<span class="series-meta">{esc(dataset_span(entry))} · {len(entry["rows"])} {"row" if len(entry["rows"]) == 1 else "rows"}</span></a></li>'
        for entry in entries
    )
    return f"""<nav class="series-index" aria-label="{esc(title)}">
  <p class="eyebrow">{esc(title)}</p>
  <ol>{items}</ol>
</nav>"""


def dataset_stack(entries: Sequence[dict[str, Any]], school_name: str) -> str:
    cards: list[str] = []
    for entry in entries:
        summary_fields = fmt.table_fields(entry["rows"])
        expanded_fields = [
            field
            for field in fmt.table_fields(entry["rows"], expanded=True)
            if field not in EXCLUDED_EXPANDED
        ]
        basis = (
            f'<p class="dataset-basis"><strong>Basis:</strong> {esc(entry["basis"])}</p>'
            if entry.get("basis")
            else ""
        )
        notes = (
            f'<p class="dataset-note">{esc(entry["notes"])}</p>' if entry.get("notes") else ""
        )
        disclosure = ""
        hidden_fields = [field for field in expanded_fields if field not in summary_fields]
        if hidden_fields:
            hidden = [fmt.field_label(field) for field in hidden_fields]
            identity = [field for field in summary_fields if field in ("year", "cycle", "period", "school", "level", "scale")]
            disclosure = (
                f'<details class="column-disclosure"><summary>Show the remaining columns · {esc(", ".join(hidden))}</summary>'
                + data_table(entry, [*identity, *hidden_fields], school_name, "expanded")
                + "</details>"
            )
        refs = entry.get("source_refs") or []
        cards.append(f"""<article class="dataset-card" id="{esc(entry["dataset_id"])}">
  <header class="dataset-header">
    <div><p class="eyebrow">{esc(records.dataset_family(entry))} · {esc(dataset_span(entry))} · {len(entry["rows"])} rows</p><h2>{esc(records.dataset_label(entry))}</h2></div>
    {_csv_download(entry)}
  </header>
  {basis}
  {notes}
  {data_table(entry, summary_fields, school_name, "ordinary")}
  {disclosure}
  <details class="dataset-sources" id="{esc(entry["dataset_id"])}-sources"><summary>Dataset sources · {len(refs)} public {"reference" if len(refs) == 1 else "references"}</summary>{source_list(refs)}</details>
</article>""")
    return f'<div class="dataset-stack">{"".join(cards)}</div>'


def granular_stack(entries: Sequence[dict[str, Any]], school_name: str) -> str:
    """Subject-level and itemised tables from the granular corpus."""
    if not entries:
        return ""
    corpus = corpora.granular_corpus()
    cards = []
    for entry in entries:
        fields = fmt.table_fields(entry["rows"], expanded=True)
        head = "".join(f'<th scope="col">{esc(fmt.field_label(field))}</th>' for field in fields)
        body = []
        for row in entry["rows"]:
            cells = []
            for field in fields:
                value = fmt.cell_value(row, field)
                blank = ' class="blank-value"' if value is None or value == "" else ""
                cells.append(f'<td data-label="{esc(fmt.field_label(field))}"{blank}>{esc(fmt.format_value(field, value, row))}</td>')
            total = str(row.get("subject") or row.get("destination") or "").upper() == "TOTAL"
            row_class = ' class="total-row"' if total else ""
            body.append(f"<tr{row_class}>{''.join(cells)}</tr>")
        cards.append(f"""<article class="dataset-card dataset-card-granular" id="{esc(entry["dataset_id"])}">
  <header class="dataset-header">
    <div><p class="eyebrow">Subject and destination detail · {esc(entry["period"])} · {len(entry["rows"])} rows</p><h2>{esc(corpora.granular_label(entry))}</h2></div>
  </header>
  <p class="dataset-basis"><strong>Basis:</strong> {esc(entry.get("basis"))}</p>
  <div class="table-scroll" tabindex="0" aria-label="Scrollable table: {esc(corpora.granular_label(entry))}">
    <table class="data-table">
      <caption>{esc(corpora.granular_label(entry))}. Counts as printed by the school; the TOTAL row is the school's own.</caption>
      <thead><tr>{head}</tr></thead>
      <tbody>{"".join(body)}</tbody>
    </table>
  </div>
  <details class="dataset-sources"><summary>Source · {esc(corpus.get("source_title"))} · as at {esc(corpus.get("as_at"))}</summary>
    <p class="dataset-note">{esc(corpus.get("source_note"))}</p>{source_list([str(corpus.get("source_ref"))])}
  </details>
</article>""")
    return f'<div class="dataset-stack">{"".join(cards)}</div>'


LATEST_CARD_LIMIT = 8


def latest_record(entries: Sequence[dict[str, Any]]) -> str:
    candidates = []
    for entry in entries:
        row = records.latest_row(entry)
        if row is not None:
            candidates.append((entry, row, records.row_year(row)))
    candidates = [item for item in candidates if item[2] is not None] + [
        item for item in candidates if item[2] is None
    ]
    if not candidates:
        return (
            '<div class="empty-state"><h2>No published result recovered</h2>'
            "<p>The frozen record contains no statistical value for this section.</p></div>"
        )
    entry, row, year = max(
        candidates, key=lambda item: (item[2] if item[2] is not None else float("-inf"))
    )
    fields = [
        field
        for field in fmt.table_fields([row])
        if field not in ("year", "cycle", "period", "confidence", "publication_status", "school")
        and fmt.cell_value(row, field) not in (None, "")
    ]
    shown = fields[:LATEST_CARD_LIMIT]
    more = len(fields) - len(shown)
    values = "".join(
        f"<div><dt>{esc(fmt.field_label(field))}</dt>"
        f"<dd>{esc(fmt.format_value(field, fmt.cell_value(row, field), row))}</dd></div>"
        for field in shown
    )
    status_source = row.get("confidence")
    if status_source is None:
        status_source = row.get("publication_status")
    if status_source is None:
        status_source = "Not stated"
    status = fmt.format_value("confidence", status_source, row)
    more_note = (
        f' {more} further published {"field" if more == 1 else "fields"} in the ledger below.'
        if more > 0
        else ""
    )
    return f"""<article class="latest-record">
  <div class="latest-heading">
    <div><p class="eyebrow">Latest existing verified result · {esc(records.dataset_family(entry))}</p><h2>{esc(records.dataset_label(entry))}</h2></div>
    <p class="latest-year">{esc(year)}</p>
  </div>
  <dl class="latest-values">{values}</dl>
  <p class="latest-footnote">Shown on the source’s published basis. Evidence status: {esc(status)}.{esc(more_note)} <a href="#{esc(entry["dataset_id"])}">Open this ledger</a>.</p>
</article>"""


def status_pill(text: str) -> str:
    return f'<span class="status-pill">{esc(text)}</span>'


def summary_list(pairs: Sequence[tuple[str, str]]) -> str:
    return (
        '<dl class="record-summary">'
        + "".join(f"<div><dt>{esc(label)}</dt><dd>{esc(value)}</dd></div>" for label, value in pairs)
        + "</dl>"
    )
