"""Small-multiple figures assembled from the comparison series.

Everything drawn here is taken from ``comparison.metrics`` — the same
like-for-like series the comparison tool uses — so a school's "results by year"
panel and the school index panels can never show a value the comparison tool
would refuse.  No figure is read from the dataset directly, nothing is
interpolated, and rulers that the comparison metrics do not define (Cambridge
Pre-U, IB Higher Level, school-defined crosswalks) are listed as not charted
rather than being folded into a neighbouring series.
"""

from __future__ import annotations

from typing import Any, Sequence

from . import comparison, dataset, records
from .chart import (
    GAP_RULE,
    INDEX_LAYOUT,
    PANEL_COLOURS,
    TRAJECTORY_DESKTOP,
    TRAJECTORY_MOBILE,
    Marker,
    Series,
    ceiling_for,
    display_range,
    format_value,
    panel_svg,
)
from .ui import esc, link

INDEX_DEFAULT_METRIC = "a_level_astar"

EXCEPTIONAL_YEARS = Marker("band", 2020, 2021, "2020–21 not drawn (CAG/TAG)", "2020–21")
A_STAR_INTRODUCED = Marker("rule", 2010, 2010, "A* introduced 2010", "A* 2010")

# One panel per grading ruler.  The metric ids are the comparison tool's own;
# the scale ids point at the frozen ``grading_scales`` presentation records.
RULERS: tuple[dict[str, Any], ...] = (
    {
        "key": "a-level",
        "scale": "a-level",
        "metrics": ("a_level_astar", "a_level_astar_a", "a_level_astar_b"),
        "markers": (A_STAR_INTRODUCED, EXCEPTIONAL_YEARS),
        "pre_2010_note": (
            "Before 2010 the A-or-above and B-or-above series carry the pre-A* "
            "thresholds A and A–B, exactly as the comparison metric defines them; "
            "the A* series begins when the grade did."
        ),
    },
    {
        "key": "gcse-9-1",
        "scale": "gcse-9-1",
        "metrics": ("gcse_grade_9", "gcse_grade_9_8", "gcse_grade_9_7"),
        "markers": (EXCEPTIONAL_YEARS,),
        "pre_2010_note": None,
    },
    {
        "key": "gcse-legacy",
        "scale": "gcse-a-star-g",
        "metrics": ("gcse_legacy_astar", "gcse_legacy_astar_a", "gcse_legacy_astar_b"),
        "markers": (EXCEPTIONAL_YEARS,),
        "pre_2010_note": None,
    },
)


def _spans_exceptional_years(points: Sequence[dict[str, Any]]) -> bool:
    """True when a series reaches 2020 or later, so the CAG/TAG gap falls inside it."""
    years = [point["year"] for point in points]
    return bool(years) and max(years) >= 2020 and min(years) <= 2021


def _status_summary(points_by_label: Sequence[tuple[str, dict[str, Any] | None]]) -> str:
    present = [(label, point["status"]) for label, point in points_by_label if point]
    statuses = list(dict.fromkeys(status for _, status in present))
    if len(statuses) == 1:
        return statuses[0]
    return "; ".join(f"{label}: {status}" for label, status in present)


def _values_table(
    series: Sequence[Series], unit: str, caption: str
) -> str:
    """An exact-value table for a panel: one row per year, one column per series."""
    years = sorted({point["year"] for item in series for point in item.points})
    lookup = {
        (item.label, point["year"]): point for item in series for point in item.points
    }
    head = "".join(f'<th scope="col">{esc(item.label)}</th>' for item in series)
    rows = []
    for year in years:
        cells = []
        for item in series:
            point = lookup.get((item.label, year))
            if point is None:
                cells.append('<td class="blank-value">—</td>')
            else:
                cells.append(f"<td>{esc(format_value(point['value'], unit))}</td>")
        status = _status_summary([(item.label, lookup.get((item.label, year))) for item in series])
        rows.append(
            f'<tr><th scope="row">{year}</th>{"".join(cells)}<td>{esc(status)}</td></tr>'
        )
    return f"""<details class="chart-values">
  <summary>Exact values</summary>
  <div class="table-scroll" tabindex="0">
    <table class="data-table chart-values-table">
      <caption>{esc(caption)}. Dashes are years with no like-for-like published value.</caption>
      <thead><tr><th scope="col">Year</th>{head}<th scope="col">Evidence status</th></tr></thead>
      <tbody>{"".join(rows)}</tbody>
    </table>
  </div>
</details>"""


# --- School index ------------------------------------------------------------


def index_metric_ids(metrics: Sequence[dict[str, Any]]) -> list[str]:
    return [metric["id"] for metric in metrics]


def index_frame(metric: dict[str, Any]) -> dict[str, Any]:
    """The ruler shared by every school's panel for one metric."""
    years = [point["year"] for point in metric["points"]]
    values = [point["value"] for point in metric["points"]]
    year_from, year_to = display_range(min(years), max(years))
    return {
        "year_from": year_from,
        "year_to": year_to,
        "ceiling": ceiling_for(values, metric["unit"]),
    }


def index_panel(metric: dict[str, Any], school: dict[str, Any], frame: dict[str, Any]) -> str:
    """The small panel drawn inside a school's row on the index."""
    points = comparison.school_points(metric, school["id"])
    if not points:
        return (
            '<div class="index-panel index-panel-empty">'
            f'<p><strong>No like-for-like series.</strong> The record holds no '
            f'{esc(metric["shortLabel"])} value for {esc(school["short"])} on this ruler; '
            "its ledgers may report the qualification on another basis.</p></div>"
        )
    series = (Series(metric["shortLabel"], tuple(points), PANEL_COLOURS[0]),)
    uid = f"index-{school['id']}-{metric['id']}"
    svg = panel_svg(
        series,
        frame["year_from"],
        frame["year_to"],
        metric["unit"],
        INDEX_LAYOUT,
        uid=uid,
        title=f"{school['name']}: {metric['label']}",
        description=(
            f"Published values from {points[0]['year']} to {points[-1]['year']} on a ruler "
            f"shared by every school on this page. Exact values follow in the table."
        ),
        ceiling=frame["ceiling"],
        markers=(
            (EXCEPTIONAL_YEARS,)
            if metric["domain"] == "results" and _spans_exceptional_years(points)
            else ()
        ),
        css_class="record-panel index-chart",
    )
    latest = points[-1]
    count = len(points)
    caption = (
        f'<p class="index-panel-caption">'
        f'<span class="index-panel-latest">{esc(format_value(latest["value"], metric["unit"]))}</span>'
        f'<span>latest published, {latest["year"]}</span>'
        f'<span>{count} {"year" if count == 1 else "years"} on this ruler</span></p>'
        f'<p class="index-panel-status">Evidence status: {esc(latest["status"])}</p>'
    )
    table = _values_table(series, metric["unit"], f"{school['name']}, {metric['label']}")
    return f'<div class="index-panel">{svg}{caption}{table}</div>'


# --- School record -----------------------------------------------------------


def _panel_note(ruler: dict[str, Any], series: Sequence[Series]) -> str:
    notes = []
    if ruler["pre_2010_note"] and any(
        point["year"] < 2010 for item in series for point in item.points
    ):
        notes.append(ruler["pre_2010_note"])
    if _spans_exceptional_years([point for item in series for point in item.points]):
        notes.append(
            "Centre-assessed 2020 and teacher-assessed 2021 grades are not drawn; "
            "their absence is not zero and the surrounding years are not joined."
        )
    notes.append(GAP_RULE)
    return " ".join(notes)


def school_ruler_panels(
    school: dict[str, Any], metrics: Sequence[dict[str, Any]]
) -> list[dict[str, Any]]:
    """The school's charted rulers, in record order, with their series and notes."""
    scales = dataset.presentation()["grading_scales"]
    panels: list[dict[str, Any]] = []
    for ruler in RULERS:
        series: list[Series] = []
        for index, metric_id in enumerate(ruler["metrics"]):
            metric = comparison.metric_by_id(list(metrics), metric_id)
            if metric is None:
                continue
            points = comparison.school_points(metric, school["id"])
            if points:
                series.append(Series(metric["shortLabel"], tuple(points), PANEL_COLOURS[index]))
        if not series:
            continue
        unit = "percent"
        scale = scales[ruler["scale"]]
        all_points = [point for item in series for point in item.points]
        markers = tuple(
            marker
            for marker in ruler["markers"]
            if marker is not EXCEPTIONAL_YEARS or _spans_exceptional_years(all_points)
        )
        panels.append({
            "key": ruler["key"],
            "scale": scale,
            "series": series,
            "unit": unit,
            "markers": markers,
            "note": _panel_note(ruler, series),
            "dataset_ids": {
                point["datasetId"] for item in series for point in item.points
            },
        })
    return panels


def not_charted_ledgers(
    school_id: str, charted_dataset_ids: set[str]
) -> list[tuple[str, str]]:
    """Examination ledgers that contribute nothing to any charted ruler."""
    ledgers = []
    for entry in records.school_datasets(school_id, ["exam_results"]):
        if entry["dataset_id"] in charted_dataset_ids:
            continue
        years = [records.row_year(row) for row in entry["rows"]]
        years = [year for year in years if year is not None]
        span = f"{min(years)}–{max(years)}" if years else "undated"
        if years and min(years) == max(years):
            span = str(min(years))
        ledgers.append((records.dataset_label(entry), span))
    return ledgers


def school_trajectory(school: dict[str, Any], metrics: Sequence[dict[str, Any]]) -> str:
    """The "results by year" section body for a school record."""
    panels = school_ruler_panels(school, metrics)
    if not panels:
        return (
            '<div class="empty-state"><h2>No like-for-like series to chart</h2>'
            "<p>The record holds no examination values for this school on a ruler the "
            "comparison tool defines. Its ledgers remain available in full.</p></div>"
        )
    years = [
        point["year"] for panel in panels for item in panel["series"] for point in item.points
    ]
    year_from, year_to = display_range(min(years), max(years))

    articles = []
    for panel in panels:
        uid = f"trajectory-{school['id']}-{panel['key']}"
        legend = "".join(
            f'<span><i class="series-colour" style="background:{item.colour}"></i>{esc(item.label)}</span>'
            for item in panel["series"]
        )
        first = min(point["year"] for item in panel["series"] for point in item.points)
        last = max(point["year"] for item in panel["series"] for point in item.points)
        title = f"{school['name']}: {panel['scale']['label']}"
        description = (
            f"Published {panel['scale']['qualification']} results from {first} to {last}, "
            f"drawn on the same year axis as the school's other rulers. Exact values follow in the table."
        )
        desktop = panel_svg(
            panel["series"], year_from, year_to, panel["unit"], TRAJECTORY_DESKTOP,
            uid=f"{uid}-desktop", title=title, description=description,
            markers=panel["markers"], css_class="record-panel panel-desktop",
        )
        mobile = panel_svg(
            panel["series"], year_from, year_to, panel["unit"], TRAJECTORY_MOBILE,
            uid=f"{uid}-mobile", title=title, description=description,
            markers=panel["markers"], css_class="record-panel panel-mobile",
        )
        table = _values_table(panel["series"], panel["unit"], title)
        articles.append(f"""<article class="trajectory-panel" id="{esc(uid)}">
  <header>
    <div><p class="eyebrow">{esc(panel["scale"]["qualification"])}</p><h3>{esc(panel["scale"]["label"])}</h3></div>
    <p class="panel-denominator">{esc(panel["scale"]["denominator"])} · {first}–{last}</p>
  </header>
  <div class="series-legend">{legend}</div>
  {desktop}
  {mobile}
  <p class="trajectory-footnote">{esc(panel["note"])}</p>
  {table}
</article>""")

    charted_ids = set().union(*(panel["dataset_ids"] for panel in panels))
    omitted = not_charted_ledgers(school["id"], charted_ids)
    omitted_markup = (
        "<p><strong>Recorded, not charted.</strong> These ledgers use rulers the comparison "
        "tool does not define, so they are read in the examination record rather than drawn here:</p>"
        "<ul>" + "".join(f"<li>{esc(label)} · {esc(span)}</li>" for label, span in omitted) + "</ul>"
        if omitted
        else ""
    )
    return f"""<div class="trajectory-grid">
  <div class="trajectory-panels">{"".join(articles)}</div>
  <aside class="trajectory-aside">
    <p class="eyebrow">Reading the panels</p>
    <h2>One ruler per panel</h2>
    <p>Each panel keeps one qualification on its own published scale; the year axis is shared so a change of ruler is visible as a handover, not a jump.</p>
    <p>{esc(GAP_RULE)} Every point is a frozen value from the ledger, on the basis the source published.</p>
    <p>A ledger can hold more years than its panel: a panel draws only the years the comparison metric admits, so an older row kept on another basis is read in the ledger, not drawn.</p>
    {omitted_markup}
    {link(f"/schools/{school['id']}/exam-results", "Open the examination ledgers", "text-link")}
  </aside>
</div>"""
