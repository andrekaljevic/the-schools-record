"""The like-for-like comparison tool."""

from __future__ import annotations

import csv
import io
from typing import Any

import streamlit as st

from . import comparison, dataset
from .chart import comparison_chart
from .icons import icon
from .ui import breadcrumbs, controls, esc, page_hero, write


@st.cache_data(show_spinner=False)
def _metrics() -> list[dict[str, Any]]:
    return comparison.metrics()


def _clamp(value: Any, low: int, high: int, fallback: int) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return fallback
    return max(low, min(high, number))


def _csv_bytes(metric: dict[str, Any], points: list[dict[str, Any]]) -> bytes:
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(["school", "year", "metric", "value", "unit", "evidence_status", "dataset"])
    for point in points:
        writer.writerow([
            point["schoolName"],
            point["year"],
            metric["label"],
            point["value"],
            metric["unit"],
            point["status"],
            point["datasetId"],
        ])
    return buffer.getvalue().encode("utf-8")


def compare() -> None:
    schools = [{"id": s["id"], "name": s["name"]} for s in dataset.schools()]
    metrics = _metrics()

    write(f"""
<main id="main-content">
  <div class="shell">{breadcrumbs([("Compare", None)])}</div>
  {page_hero(
      "Comparison",
      "Compare like with like",
      "Choose two schools and one precisely defined metric. Shareable URL state, exact-value tables and visible limitations keep the comparison inspectable.",
      "A higher result is not a declaration that one school is better. These records do not control for intake, subject mix, cohort size or educational aims.",
  )}
</main>""")

    if not metrics:
        write('<div class="empty-state"><h2>No comparison series available</h2></div>')
        return

    all_years = [point["year"] for metric in metrics for point in metric["points"]]
    year_min, year_max = min(all_years), max(all_years)

    params = st.query_params
    requested = (params.get("schools") or "").split(",")
    ids = [school["id"] for school in schools]
    first_default = requested[0] if requested and requested[0] in ids else ids[0]
    second_default = (
        requested[1] if len(requested) > 1 and requested[1] in ids else ids[1]
    )
    metric_ids = [metric["id"] for metric in metrics]
    metric_default = params.get("metric") if params.get("metric") in metric_ids else metric_ids[0]
    from_default = _clamp(params.get("from"), year_min, year_max, year_min)
    to_default = _clamp(params.get("to"), year_min, year_max, year_max)
    view_default = "Table" if params.get("view") == "table" else "Chart"

    control_box = controls("tsr-compare")
    control_box.__enter__()
    columns = st.columns([1, 1, 1.5, 0.65, 0.65])
    with columns[0]:
        first = st.selectbox(
            "First school",
            ids,
            index=ids.index(first_default),
            format_func=lambda value: next(s["name"] for s in schools if s["id"] == value),
            key="compare_first",
        )
    with columns[1]:
        second_options = [value for value in ids if value != first]
        if second_default not in second_options:
            second_default = second_options[0]
        second = st.selectbox(
            "Second school",
            second_options,
            index=second_options.index(second_default),
            format_func=lambda value: next(s["name"] for s in schools if s["id"] == value),
            key="compare_second",
        )
    with columns[2]:
        metric_id = st.selectbox(
            "Metric",
            metric_ids,
            index=metric_ids.index(metric_default),
            format_func=lambda value: next(m["label"] for m in metrics if m["id"] == value),
            key="compare_metric",
        )
    with columns[3]:
        year_from = st.number_input(
            "From", min_value=year_min, max_value=year_max, value=from_default, step=1,
            key="compare_from",
        )
    with columns[4]:
        year_to = st.number_input(
            "To", min_value=int(year_from), max_value=year_max,
            value=max(int(year_from), to_default), step=1, key="compare_to",
        )
    control_box.__exit__(None, None, None)

    metric = next(item for item in metrics if item["id"] == metric_id)
    year_from, year_to = int(year_from), int(year_to)
    points = [
        point
        for point in metric["points"]
        if point["schoolId"] in (first, second) and year_from <= point["year"] <= year_to
    ]
    selected = [school for school in schools if school["id"] in (first, second)]
    overlapping = [
        year
        for year in dict.fromkeys(point["year"] for point in points)
        if len({point["schoolId"] for point in points if point["year"] == year}) == 2
    ]

    state = {
        "p": "/compare",
        "schools": f"{first},{second}",
        "metric": metric_id,
        "from": str(year_from),
        "to": str(year_to),
        "view": "table" if st.session_state.get("compare_view", view_default) == "Table" else "chart",
    }
    if {key: params.get(key) for key in state} != state:
        st.query_params.from_dict(state)

    view_box = controls("tsr-view")
    view_box.__enter__()
    view_columns = st.columns([6, 1.15, 1.25])
    with view_columns[1]:
        view = st.radio(
            "View",
            ("Chart", "Table"),
            index=0 if view_default == "Chart" else 1,
            horizontal=True,
            key="compare_view",
            label_visibility="collapsed",
        )
    with view_columns[2]:
        st.download_button(
            "Download CSV",
            data=_csv_bytes(metric, points),
            file_name=f"schools-record-{metric['id']}.csv",
            mime="text/csv",
            key="compare_csv",
        )
    view_box.__exit__(None, None, None)

    legend = "".join(
        f'<span><i class="series-colour colour-{index + 1}"></i>{esc(school["name"])}</span>'
        for index, school in enumerate(
            sorted(selected, key=lambda school: (school["id"] != first,))
        )
    )
    not_comparable = (
        ""
        if overlapping
        else '<div class="not-comparable"><strong>Not directly comparable</strong>'
        "<p>The selected schools do not have overlapping, like-for-like published values "
        "for this metric and period.</p></div>"
    )
    chart = (
        comparison_chart(metric, first, second, year_from, year_to)
        if view == "Chart" and points
        else ""
    )
    rows = "".join(
        f'<tr><th scope="row">{esc(point["schoolName"])}</th><td>{point["year"]}</td>'
        f'<td>{esc(_display(point["value"], metric["unit"]))}</td><td>{esc(point["status"])}</td></tr>'
        for point in points
    )
    table_class = (
        "comparison-table-visible" if view == "Table" else "comparison-table-accessible"
    )
    derived_note = (
        "<p>Calculated rates are generated at display time from frozen source values and are not stored as new public claims.</p>"
        if any(point.get("annotation") for point in points)
        else ""
    )

    write(f"""
<main class="compare-body">
  <section class="shell tsr-result-section">
    <div class="compare-tool">
      <section class="comparison-result" aria-live="polite">
        <header class="comparison-heading">
          <div>
            <p class="eyebrow">Like-for-like view</p>
            <h2>{esc(metric["label"])}</h2>
            <p>{esc(metric["definition"])}</p>
          </div>
        </header>
        <div class="series-legend">{legend}</div>
        {not_comparable}
        {chart}
        <div class="{table_class}">
          <table class="data-table">
            <caption>Exact values for {esc(metric["label"])}</caption>
            <thead><tr><th scope="col">School</th><th scope="col">Year</th><th scope="col">Value</th><th scope="col">Evidence status</th></tr></thead>
            <tbody>{rows}</tbody>
          </table>
        </div>
        <div class="notice notice-warning">
          <strong>Comparison limit</strong>
          <p>{esc(metric["note"])}</p>
          {derived_note}
        </div>
      </section>
    </div>
  </section>
</main>""")


def _display(value: float, unit: str) -> str:
    from .format import to_fixed

    if unit == "percent":
        return f"{to_fixed(value)}%"
    return f"{value:,}"
