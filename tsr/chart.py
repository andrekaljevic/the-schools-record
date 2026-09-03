"""The comparison chart, drawn as the published site draws it."""

from __future__ import annotations

import math
from typing import Any, Sequence

from .format import to_fixed
from .ui import esc

SERIES_COLOURS = ("#125c58", "#9a6d2e")


def num(value: float) -> str:
    """Render a coordinate the way the published SVG renders it."""
    number = float(value)
    if number.is_integer():
        return str(int(number))
    return repr(number)


def _format_point(value: float, unit: str) -> str:
    if unit == "percent":
        return f"{to_fixed(value)}%"
    return f"{value:,}" if float(value).is_integer() else f"{value:,}"


def comparison_chart(
    metric: dict[str, Any],
    first: str,
    second: str,
    year_from: int,
    year_to: int,
) -> str:
    points = [
        point
        for point in metric["points"]
        if point["schoolId"] in (first, second)
        and year_from <= point["year"] <= year_to
    ]
    years = sorted({point["year"] for point in points})
    ceiling = 100 if metric["unit"] == "percent" else max(
        [1, *[point["value"] for point in points]]
    )

    def x(year: float) -> float:
        return 62 + (year - year_from) / max(1, year_to - year_from) * 810

    def y(value: float) -> float:
        return 30 + (1 - value / max(1, ceiling)) * 302

    grid = []
    for fraction in (0, 0.25, 0.5, 0.75, 1):
        value = ceiling * (1 - fraction)
        line_y = 30 + fraction * 302
        label = f"{round(value)}%" if metric["unit"] == "percent" else str(round(value))
        grid.append(
            f'<g><line x1="62" x2="872" y1="{num(line_y)}" y2="{num(line_y)}" class="chart-gridline"></line>'
            f'<text x="50" y="{num(line_y + 4)}" text-anchor="end" class="chart-label">{esc(label)}</text></g>'
        )

    step = max(1, math.ceil(len(years) / 7))
    ticks = [
        f'<text x="{num(x(year))}" y="368" text-anchor="middle" class="chart-label">{year}</text>'
        for index, year in enumerate(years)
        if index % step == 0 or len(years) < 8
    ]

    series = []
    for index, school_id in enumerate((first, second)):
        own = sorted(
            (point for point in points if point["schoolId"] == school_id),
            key=lambda point: point["year"],
        )
        colour = SERIES_COLOURS[index]
        polyline = ""
        if len(own) > 1:
            path = " ".join(
                f'{num(x(point["year"]))},{num(y(point["value"]))}' for point in own
            )
            polyline = (
                f'<polyline points="{path}" fill="none" stroke="{colour}" '
                'stroke-width="3" stroke-linejoin="round"></polyline>'
            )
        circles = "".join(
            f'<circle cx="{num(x(point["year"]))}" cy="{num(y(point["value"]))}" r="5" fill="{colour}">'
            f'<title>{esc(point["schoolName"])}, {point["year"]}: '
            f'{esc(_format_point(point["value"], metric["unit"]))}</title></circle>'
            for point in own
        )
        series.append(f"<g>{polyline}{circles}</g>")

    return f"""<div class="chart-wrap">
  <svg class="comparison-chart" viewBox="0 0 900 390" role="img" aria-labelledby="chart-title chart-description">
    <title id="chart-title">{esc(metric["label"])}</title>
    <desc id="chart-description">Two school series from {year_from} to {year_to}. Exact values follow in the accessible table.</desc>
    {"".join(grid)}
    {"".join(ticks)}
    {"".join(series)}
  </svg>
</div>"""


# --- Small-multiple panels ---------------------------------------------------
#
# The record's other charts share the comparison chart's language — the same
# two inks, the same mono axis labels, the same 0–100 ruler for percentages —
# but are drawn as small multiples so that schools sit side by side on one
# ruler without being overlaid as a league table.  Every point is a frozen
# value (or the labelled Oxford offer rate) taken from ``comparison.metrics``;
# lines join consecutive published years only, so a gap in a line is a gap in
# the record, never an interpolation.

from dataclasses import dataclass

SERIES_INK = "#41514e"
PANEL_COLOURS = (SERIES_COLOURS[0], SERIES_COLOURS[1], SERIES_INK)
GAP_RULE = (
    "Lines join consecutive published years only; a break in a line is a gap "
    "in the record, not an estimate."
)


@dataclass(frozen=True)
class Layout:
    """Geometry of a panel in SVG user units."""

    width: int
    height: int
    left: int
    right: int
    top: int
    bottom: int
    font: int
    ticks: int
    grid: tuple[float, ...]
    radius: float
    stroke: float


INDEX_LAYOUT = Layout(340, 132, 46, 332, 16, 104, 11, 4, (0, 0.5, 1), 3.2, 2)
TRAJECTORY_DESKTOP = Layout(860, 300, 56, 846, 24, 246, 12, 8, (0, 0.25, 0.5, 0.75, 1), 4, 2.5)
TRAJECTORY_MOBILE = Layout(360, 236, 44, 350, 20, 190, 11, 4, (0, 0.5, 1), 3.2, 2)


@dataclass(frozen=True)
class Series:
    label: str
    points: tuple  # comparison points sorted by year
    colour: str


@dataclass(frozen=True)
class Marker:
    """An editorial marker: a shaded band of excluded years or a dated rule."""

    kind: str  # "band" or "rule"
    start: int
    end: int
    label: str
    short_label: str


def format_value(value: float, unit: str) -> str:
    return _format_point(value, unit)


def _coord(value: float) -> str:
    return num(round(float(value), 2))


def display_range(year_from: int, year_to: int) -> tuple[int, int]:
    """Pad a one- or two-year span so a lone point does not sit on the frame."""
    while year_to - year_from < 2:
        year_from -= 1
        year_to += 1
    return year_from, year_to


def year_ticks(year_from: int, year_to: int, target: int) -> list[int]:
    span = year_to - year_from
    step = max(1, math.ceil(span / max(1, target - 1)))
    ticks = list(range(year_from, year_to + 1, step))
    if ticks[-1] != year_to:
        if (year_to - ticks[-1]) * 2 >= step:
            ticks.append(year_to)
        else:
            ticks[-1] = year_to
    return ticks


def ceiling_for(values: Sequence[float], unit: str) -> float:
    """The top of the ruler: always 100 for a percentage, a round number for a count."""
    if unit == "percent":
        return 100
    top = max([1, *values])
    step = 10 if top <= 100 else 50 if top <= 500 else 100
    return max(step, math.ceil(top / step) * step)


def runs(points: Sequence[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    """Split a year-sorted series into runs of consecutive published years."""
    grouped: list[list[dict[str, Any]]] = []
    for point in points:
        if grouped and point["year"] == grouped[-1][-1]["year"] + 1:
            grouped[-1].append(point)
        else:
            grouped.append([point])
    return grouped


def _grid_label(value: float, unit: str) -> str:
    rounded = int(round(value))
    return f"{rounded}%" if unit == "percent" else f"{rounded:,}"


def panel_svg(
    series: Sequence[Series],
    year_from: int,
    year_to: int,
    unit: str,
    layout: Layout,
    *,
    uid: str,
    title: str,
    description: str,
    ceiling: float | None = None,
    markers: Sequence[Marker] = (),
    css_class: str = "record-panel",
) -> str:
    year_from, year_to = display_range(year_from, year_to)
    values = [point["value"] for item in series for point in item.points]
    top = ceiling if ceiling is not None else ceiling_for(values, unit)

    def x(year: float) -> float:
        return layout.left + (year - year_from) / (year_to - year_from) * (layout.right - layout.left)

    def y(value: float) -> float:
        return layout.top + (1 - value / top) * (layout.bottom - layout.top)

    parts: list[str] = []

    # Editorial markers sit behind the grid.
    short = layout.width < 500
    for marker in markers:
        if marker.kind == "band" and (marker.end < year_from or marker.start > year_to):
            continue
        if marker.kind == "rule" and not (year_from < marker.start <= year_to):
            continue
        label = esc(marker.short_label if short else marker.label)
        if marker.kind == "band":
            x0 = x(max(year_from, marker.start - 0.5))
            x1 = x(min(year_to, marker.end + 0.5))
            parts.append(
                f'<rect x="{_coord(x0)}" y="{_coord(layout.top)}" width="{_coord(x1 - x0)}" '
                f'height="{_coord(layout.bottom - layout.top)}" class="panel-band"></rect>'
                f'<text x="{_coord((x0 + x1) / 2)}" y="{_coord(layout.top - 6)}" text-anchor="middle" '
                f'class="panel-marker-label">{label}</text>'
            )
        else:
            xr = x(marker.start - 0.5)
            parts.append(
                f'<line x1="{_coord(xr)}" x2="{_coord(xr)}" y1="{_coord(layout.top)}" y2="{_coord(layout.bottom)}" class="panel-rule"></line>'
                f'<text x="{_coord(xr + 5)}" y="{_coord(layout.top - 6)}" text-anchor="start" '
                f'class="panel-marker-label">{label}</text>'
            )

    for fraction in layout.grid:
        value = top * fraction
        line_y = y(value)
        parts.append(
            f'<g><line x1="{layout.left}" x2="{layout.right}" y1="{_coord(line_y)}" y2="{_coord(line_y)}" class="chart-gridline"></line>'
            f'<text x="{layout.left - 8}" y="{_coord(line_y + layout.font * 0.35)}" text-anchor="end" '
            f'class="panel-label">{esc(_grid_label(value, unit))}</text></g>'
        )

    tick_y = layout.height - 8
    for year in year_ticks(year_from, year_to, layout.ticks):
        parts.append(
            f'<text x="{_coord(x(year))}" y="{tick_y}" text-anchor="middle" class="panel-label">{year}</text>'
        )

    for item in series:
        points = sorted(item.points, key=lambda point: point["year"])
        for run in runs(points):
            if len(run) > 1:
                path = " L ".join(f'{_coord(x(point["year"]))},{_coord(y(point["value"]))}' for point in run)
                parts.append(
                    f'<path d="M {path}" fill="none" stroke="{item.colour}" stroke-width="{num(layout.stroke)}" '
                    'stroke-linejoin="round" stroke-linecap="round"></path>'
                )
        for point in points:
            parts.append(
                f'<circle cx="{_coord(x(point["year"]))}" cy="{_coord(y(point["value"]))}" r="{num(layout.radius)}" fill="{item.colour}">'
                f'<title>{esc(item.label)}, {point["year"]}: {esc(format_value(point["value"], unit))} · {esc(point["status"])}</title></circle>'
            )

    return (
        f'<svg class="{esc(css_class)}" viewBox="0 0 {layout.width} {layout.height}" role="img" '
        f'aria-labelledby="{esc(uid)}-title {esc(uid)}-desc" style="font-size:{layout.font}px">'
        f'<title id="{esc(uid)}-title">{esc(title)}</title>'
        f'<desc id="{esc(uid)}-desc">{esc(description)}</desc>'
        + "".join(parts)
        + "</svg>"
    )


# --- The comparison instrument on the panel grammar --------------------------
#
# The published comparison chart above is kept byte for byte for the reference
# build.  The comparison page itself draws with the same small-multiple grammar
# as the index and the school records, so a gap in a line is a gap in the record
# there too, the 2020–21 band is marked, and a phone gets its own panel geometry.

COMPARISON_DESKTOP = TRAJECTORY_DESKTOP
COMPARISON_MOBILE = TRAJECTORY_MOBILE


def comparison_series(
    metric: dict[str, Any], first: str, second: str, year_from: int, year_to: int
) -> tuple[Series, ...]:
    """Two school series from a comparison metric, in the order chosen."""
    out = []
    for index, school_id in enumerate((first, second)):
        points = sorted(
            (
                point
                for point in metric["points"]
                if point["schoolId"] == school_id and year_from <= point["year"] <= year_to
            ),
            key=lambda point: point["year"],
        )
        label = points[0]["schoolName"] if points else school_id
        out.append(Series(label, tuple(points), SERIES_COLOURS[index]))
    return tuple(out)


def comparison_panel(
    metric: dict[str, Any],
    first: str,
    second: str,
    year_from: int,
    year_to: int,
    layout: Layout,
    *,
    names: dict[str, str] | None = None,
    markers: Sequence[Marker] = (),
) -> str:
    series = comparison_series(metric, first, second, year_from, year_to)
    if names:
        series = tuple(Series(names.get(item.label, item.label), item.points, item.colour) for item in series)
        series = tuple(
            Series(names.get(school_id, item.label), item.points, item.colour)
            for school_id, item in zip((first, second), series)
        )
    mobile = layout.width < 500
    uid = f"comparison-{metric['id']}-{'mobile' if mobile else 'desktop'}"
    return panel_svg(
        series,
        year_from,
        year_to,
        metric["unit"],
        layout,
        uid=uid,
        title=metric["label"],
        description=(
            f"{series[0].label} and {series[1].label}, {year_from} to {year_to}. "
            "Lines join consecutive published years only. Exact values follow in the table."
        ),
        markers=markers,
        css_class=f"record-panel comparison-panel {'panel-mobile' if mobile else 'panel-desktop'}",
    )
