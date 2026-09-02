"""Record components: ledgers, tables, evidence panels."""

from __future__ import annotations

import base64
import csv
import io
from typing import Any, Sequence

from . import dataset, format as fmt, records
from .icons import icon
from .ui import esc, href, link

EXCLUDED_EXPANDED = ("source_url", "source_ids")


def _row_source_refs(entry: dict[str, Any], row: dict[str, Any]) -> list[str]:
    row_ids = row.get("source_ids")
    ids = [str(item) for item in row_ids] if isinstance(row_ids, list) else []
    return list(dict.fromkeys([*(entry.get("source_refs") or []), *ids]))


def _row_status(row: dict[str, Any]) -> str:
    for key in ("publication_status", "confidence", "evidence_status"):
        value = row.get(key)
        if value is not None:
            return str(value)
    return ""


def evidence_disclosure(
    school_name: str,
    dataset_id: str,
    period: str,
    source_refs: Sequence[str],
    status: str,
    note: str | None,
) -> str:
    refs = ", ".join(source_refs) if source_refs else "No public reference recorded"
    note_block = (
        f"<div><dt>Record note</dt><dd>{esc(note)}</dd></div>" if note else ""
    )
    register = (
        f"?p=/evidence&school={esc(school_name)}&dataset={esc(dataset_id)}"
        f"&period={esc(period)}"
    )
    return f"""<details class="evidence-disclosure">
  <summary class="evidence-button">View evidence</summary>
  <div class="evidence-panel">
    <div class="dialog-heading"><div><p class="eyebrow">Evidence for {esc(period)}</p><h2>{esc(school_name)}</h2></div></div>
    <dl class="evidence-definition-list">
      <div><dt>Dataset</dt><dd><code>{esc(dataset_id)}</code></dd></div>
      <div><dt>Evidence status</dt><dd>{esc(status or "Not stated")}</dd></div>
      <div><dt>Public source reference</dt><dd>{esc(refs)}</dd></div>
      {note_block}
    </dl>
    <p class="dialog-privacy-note">Underlying document locations are withheld from the public build. Public references identify the evidence without exposing private research locations.</p>
    <div class="dialog-actions"><a class="text-link" href="{register}" target="_self">Open evidence register</a></div>
  </div>
</details>"""


def data_table(
    entry: dict[str, Any], fields: Sequence[str], school_name: str, suffix: str
) -> str:
    label = records.dataset_label(entry)
    head = "".join(f'<th scope="col">{esc(fmt.field_label(field))}</th>' for field in fields)
    body: list[str] = []
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
        note = row.get("note") if isinstance(row.get("note"), str) else None
        cells.append(
            '<td data-label="Evidence">'
            + evidence_disclosure(
                school_name,
                entry["dataset_id"],
                period,
                _row_source_refs(entry, row),
                _row_status(row),
                note,
            )
            + "</td>"
        )
        body.append(f"<tr>{''.join(cells)}</tr>")
    return f"""<div class="table-scroll" tabindex="0" aria-label="Scrollable table: {esc(label)}">
  <table class="data-table">
    <caption>{esc(label)}. Dashes represent blank values preserved from the frozen record.</caption>
    <thead><tr>{head}<th scope="col">Evidence</th></tr></thead>
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
        writer.writerow(
            ["" if fmt.cell_value(row, field) is None else fmt.cell_value(row, field) for field in fields]
        )
    return buffer.getvalue()


def _csv_download(entry: dict[str, Any]) -> str:
    payload = base64.b64encode(dataset_csv(entry).encode("utf-8")).decode("ascii")
    return (
        f'<a class="button button-quiet" download="{esc(entry["dataset_id"])}.csv" '
        f'href="data:text/csv;charset=utf-8;base64,{payload}">Download CSV</a>'
    )


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
        if len(expanded_fields) > len(summary_fields):
            disclosure = (
                '<details class="column-disclosure"><summary>Show all columns</summary>'
                + data_table(entry, expanded_fields, school_name, "expanded")
                + "</details>"
            )
        cards.append(f"""<article class="dataset-card" id="{esc(entry["dataset_id"])}">
  <header class="dataset-header">
    <div><p class="eyebrow">{esc(entry["domain"].replace("_", " "))}</p><h2>{esc(records.dataset_label(entry))}</h2></div>
    {_csv_download(entry)}
  </header>
  {basis}
  {notes}
  {data_table(entry, summary_fields, school_name, "ordinary")}
  {disclosure}
</article>""")
    return f'<div class="dataset-stack">{"".join(cards)}</div>'


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
        if field not in ("year", "cycle", "period", "confidence", "publication_status")
    ][:4]
    values = "".join(
        f"<div><dt>{esc(fmt.field_label(field))}</dt>"
        f"<dd>{esc(fmt.format_value(field, row.get(field), row))}</dd></div>"
        for field in fields
    )
    status_source = row.get("confidence")
    if status_source is None:
        status_source = row.get("publication_status")
    if status_source is None:
        status_source = "Not stated"
    status = fmt.format_value("confidence", status_source, row)
    return f"""<article class="latest-record">
  <div class="latest-heading">
    <div><p class="eyebrow">Latest existing verified result</p><h2>{esc(records.dataset_label(entry))}</h2></div>
    <p class="latest-year">{esc(year)}</p>
  </div>
  <dl class="latest-values">{values}</dl>
  <p class="latest-footnote">Shown on the source’s published basis. Evidence status: {esc(status)}.</p>
</article>"""
