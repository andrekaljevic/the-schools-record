"""Display formatting.

A port of the front-end's ``lib/format`` module.  Formatting is presentational
only: it never changes a stored value, fills a blank, or promotes a bounded or
estimated figure to an exact one.
"""

from __future__ import annotations

import re
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Iterable, Sequence

from . import dataset

STATUS_LABELS = {
    "P": "Primary",
    "S": "Secondary",
    "D": "Derived",
    "R": "Reconstructed",
    "high": "High",
    "medium": "Medium",
    "low": "Low",
}

_RANGE_PATTERN = re.compile(r"^(\d+(?:\.\d+)?)\s*[–-]\s*(\d+(?:\.\d+)?)$")

_SUMMARY_FIELDS = (
    "year",
    "cycle",
    "period",
    "level",
    "scale",
    "entries",
    "candidates",
    "cohort",
    "leavers",
    "confidence",
)

_SUMMARY_COUNT_FIELDS = (
    "oxford",
    "cambridge",
    "oxbridge",
    "applications",
    "offers",
    "acceptances",
    "count",
    "value",
)

_COUNT_METRIC_PATTERN = re.compile(r"matriculation|offer|scholarship|raw_count")


def priority_fields() -> list[str]:
    return [
        "year",
        "cycle",
        "period",
        "level",
        "scale",
        "entries",
        "entries_9_1",
        "candidates",
        "cohort",
        "leavers",
        *dataset.presentation()["percentage_fields"],
        "oxford",
        "cambridge",
        "oxbridge",
        "applications",
        "offers",
        "acceptances",
        "count",
        "confidence",
        "publication_status",
    ]


def to_fixed(value: float, places: int = 1) -> str:
    """JavaScript ``Number.prototype.toFixed`` semantics."""
    quantum = Decimal(1).scaleb(-places)
    return str(Decimal(value).quantize(quantum, rounding=ROUND_HALF_UP))


def _group(value: float) -> str:
    return f"{int(Decimal(value).quantize(Decimal(1), rounding=ROUND_HALF_UP)):,}"


def _field_spec(field: str) -> dict[str, Any] | None:
    fields = dataset.presentation()["fields"]
    tail = field.split(".")[-1]
    return fields.get(field) or fields.get(tail)


def field_label(field: str) -> str:
    spec = _field_spec(field)
    if spec and spec.get("label"):
        return str(spec["label"])
    tail = field.split(".")[-1]
    return re.sub(r"\b\w", lambda m: m.group(0).upper(), tail.replace("_", " "))


def format_percent(value: Any) -> str:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return f"{to_fixed(value)}%"
    if not isinstance(value, str):
        return "" if value is None else str(value)
    match = _RANGE_PATTERN.match(value.strip())
    if match:
        return f"{to_fixed(float(match.group(1)))}–{to_fixed(float(match.group(2)))}%"
    return value


def format_value(field: str, value: Any, row: dict[str, Any]) -> str:
    if value is None or value == "":
        return "—"
    spec = _field_spec(field)
    kind = (spec or {}).get("kind")
    numeric = isinstance(value, (int, float)) and not isinstance(value, bool)
    if kind is None:
        kind = "decimal" if numeric else "text"

    if kind == "status":
        return " / ".join(STATUS_LABELS.get(part, part) for part in str(value).split("/"))
    if kind == "boolean":
        return "Yes" if value else "No"
    if kind == "percent":
        return format_percent(value)
    if kind == "approx-percent":
        return f"≈{format_percent(value)}"
    if numeric:
        unit = row.get("unit")
        metric = str(row.get("metric") or "")
        if field == "value" and unit == "percent":
            return f"{to_fixed(value)}%"
        if field == "value" and unit == "approx_count":
            return f"≈{_group(value)}"
        if field == "value" and (unit == "count" or _COUNT_METRIC_PATTERN.search(metric)):
            return _group(value)
        if kind == "rate":
            return f"{to_fixed(value * 100)}%"
        if kind == "approx-count":
            return f"≈{_group(value)}"
        if kind == "minimum-count":
            return f"≥{_group(value)}"
        if kind == "year":
            return str(int(Decimal(value).quantize(Decimal(1), rounding=ROUND_HALF_UP)))
        if kind == "count":
            return _group(value)
        return to_fixed(value)
    return _as_published(value)


def _as_published(value: Any) -> str:
    """Match the published build's ``String(value)`` fallback exactly.

    A nested object reaches this branch only when another row leaves the same
    key empty; the published site prints JavaScript's ``[object Object]`` there
    and its component values are carried by the flattened columns beside it.
    Reproducing it keeps this build at parity rather than silently editing the
    published presentation.
    """
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, dict):
        return "[object Object]"
    if isinstance(value, list):
        return ",".join(str(item) for item in value)
    return str(value)


def flatten(row: dict[str, Any], prefix: str = "") -> list[tuple[str, Any]]:
    flat: list[tuple[str, Any]] = []
    for key, value in row.items():
        path = f"{prefix}.{key}" if prefix else key
        if isinstance(value, list):
            flat.append((path, ", ".join(str(item) for item in value)))
        elif isinstance(value, dict):
            flat.extend(flatten(value, path))
        else:
            flat.append((path, value))
    return flat


def cell_value(row: dict[str, Any], path: str) -> Any:
    current: Any = row
    for part in path.split("."):
        if isinstance(current, dict):
            current = current.get(part)
            if current is None:
                return None
        else:
            return None
    return current


def table_fields(rows: Sequence[dict[str, Any]], expanded: bool = False) -> list[str]:
    seen: dict[str, None] = {}
    for row in rows:
        for path, _ in flatten(row):
            seen.setdefault(path, None)
    priority = priority_fields()
    ordered = [field for field in priority if field in seen]
    ordered += sorted(field for field in seen if field not in priority)
    if expanded:
        return ordered

    def keep(field: str) -> bool:
        if field in _SUMMARY_FIELDS:
            return True
        kind = (dataset.presentation()["fields"].get(field) or {}).get("kind")
        if kind in ("percent", "rate"):
            return True
        return field in _SUMMARY_COUNT_FIELDS

    return [field for field in ordered if keep(field)][:9]
