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

# Fields the frozen presentation spec leaves unlabelled ("unresolved rulers"):
# a published band whose exact grade meaning depends on the row's scale.  The
# labels say so rather than guessing a grade.
UNRESOLVED_LABELS = {
    "top": "Top band · as published",
    "top_2": "Top two bands · as published",
    "top_3": "Top three bands · as published",
    "top_equivalent": "Top band · published crosswalk",
    "astar_a_equivalent": "% A*–A · published crosswalk",
    "astar_b_or_9_6": "% A*–B or 9–6 · published crosswalk",
    "d1_d3_honest_astar_a": "% D1–D3 · A*/A-equivalent",
    "d1_m1_published": "% D1–M1 · published ruler",
    "distinction_or_merit_pass": "% distinction or merit pass",
    "pass": "% pass · as published",
    "fold_pp": "Published-ruler fold · percentage points",
    "strict_oxbridge": "Combined Oxbridge",
}

# Row fields that describe or annotate a figure rather than carry one.  They
# belong in the evidence panel and the expanded view, not the ledger summary.
DETAIL_ONLY_FIELDS = frozenset({
    "note",
    "notes",
    "source_ids",
    "source_url",
    "source_title",
    "basis",
    "coverage",
    "coverage_status",
    "population_type",
    "outcome_type",
    "estimate_basis",
    "estimate_range_summary",
})

_STATUS_FIELDS = ("confidence", "publication_status", "evidence_status")

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
    fields = dataset.presentation()["fields"]
    exact = fields.get(field)
    if exact and exact.get("label"):
        return str(exact["label"])
    tail = field.split(".")[-1]
    by_tail = fields.get(tail)
    if by_tail and by_tail.get("label"):
        label = str(by_tail["label"])
    else:
        label = UNRESOLVED_LABELS.get(tail) or re.sub(
            r"\b\w", lambda m: m.group(0).upper(), tail.replace("_", " ")
        )
    if "." in field:
        head = field.split(".")[0]
        prefix = UNRESOLVED_LABELS.get(head) or head.replace("_", " ").capitalize()
        if not label.lower().startswith(prefix.lower()):
            label = f"{prefix} · {label}"
    return label


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
    """The columns of a ledger.

    The summary view shows every field that carries a published figure or
    identifies the row — year, scale, every denominator and count, every
    percentage and rate, and the evidence status — without a cap on their
    number, because a ledger's meaning often lies in its denominator
    architecture.  Only annotations (notes, bases, source lists) and columns
    that are blank in every row wait behind "Show all columns".
    """
    seen: dict[str, list[Any]] = {}
    for row in rows:
        for path, value in flatten(row):
            seen.setdefault(path, []).append(value)
    priority = priority_fields()
    ordered = [field for field in priority if field in seen]
    ordered += [field for field in seen if field not in priority]
    if expanded:
        return ordered

    def keep(field: str) -> bool:
        tail = field.split(".")[-1]
        if tail in DETAIL_ONLY_FIELDS:
            return False
        values = [value for value in seen[field] if value not in (None, "")]
        if not values:
            return False
        if tail in _STATUS_FIELDS or field in _SUMMARY_FIELDS:
            return True
        if any(isinstance(value, str) and len(value) > 40 for value in values):
            return False
        return True

    kept = [field for field in ordered if keep(field)]

    def group(field: str) -> int:
        tail = field.split(".")[-1]
        if tail in _STATUS_FIELDS:
            return 3
        if field in _SUMMARY_FIELDS or tail in ("school", "metric", "unit"):
            return 0
        values = [value for value in seen[field] if value not in (None, "")]
        if all(isinstance(value, (int, float)) and not isinstance(value, bool) for value in values):
            return 1
        return 2

    # Identity first, then figures, then short published wording, then the
    # evidence status; the order within each group is preserved.
    return sorted(kept, key=lambda field: group(field))
