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
