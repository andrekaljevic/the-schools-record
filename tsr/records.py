"""Row and dataset helpers.

Direct ports of the front-end's ``lib/records`` helpers so that the Streamlit
build selects, orders and labels exactly the same rows as the published site.
"""

from __future__ import annotations

import re
from functools import lru_cache
from typing import Any, Iterable, Sequence

from . import dataset

_YEAR_PATTERN = re.compile(r"(?:18|19|20)\d{2}")

# Fields that describe a row rather than carry a published figure.
META_FIELDS = frozenset({
    "year",
    "cycle",
    "period",
    "level",
    "scale",
    "confidence",
    "note",
    "notes",
    "publication_status",
    "source_ids",
    "source_title",
    "source_url",
    "basis",
    "population_type",
    "outcome_type",
    "coverage_status",
})

DATASET_LABELS = {
    "winchester_pre_u_two_ruler_2011_2019": "Cambridge Pre-U results",
    "winchester_mixed_alevel_pre_u_2021": "Mixed A-level and Pre-U result",
    "winchester_alevel": "A-level results",
    "winchester_gcse": "GCSE results",
    "eton_alevel_primary_sheets": "A-level results · official tables",
    "eton_alevel_headline_gap_years": "A-level results · additional years",
    "eton_gcse_primary": "GCSE and IGCSE results",
    "eton_pre_u_rump": "Cambridge Pre-U results",
    "westminster_gcse_old_scale": "GCSE results · legacy scale",
    "westminster_gcse_reformed": "GCSE results · 9–1 scale",
    "westminster_alevel": "A-level results",
    "westminster_pre_u": "Cambridge Pre-U results",
    "st_pauls_gcse": "GCSE and IGCSE results",
    "st_pauls_alevel": "A-level results",
    "kcs_combined_alevel_ib": "A-level and IB published crosswalk",
    "kcs_alevel_only": "A-level results",
    "kcs_ib_hl": "IB Higher Level results",
    "kcs_gcse_headline": "GCSE results",
    "kcs_gcse_detailed_9_1": "GCSE results · 9–1 detail",
    "spgs_exam_anchors": "Published examination results",
    "wycombe_exam_anchors": "Published examination results",
}


def school_aliases(school: dict[str, Any]) -> set[str]:
    return {
        school["name"],
        school["short"],
        school["applyCentreName"],
        school["usName"],
        school["name"].replace(", Wimbledon", " Wimbledon"),
    }


@lru_cache(maxsize=None)
def find_school(school_id: str) -> dict[str, Any] | None:
    for school in dataset.schools():
        if school["id"] == school_id:
            return school
    return None


def school_datasets(
    school_id: str, domains: Sequence[str] | None = None
) -> list[dict[str, Any]]:
    school = find_school(school_id)
    if school is None:
        return []
    aliases = school_aliases(school)
    selected: list[dict[str, Any]] = []
    for entry in dataset.figures()["datasets"]:
        if domains is not None and entry["domain"] not in domains:
            continue
        if entry.get("school") in aliases:
            selected.append(entry)
            continue
        if entry.get("school") != "All seven schools":
            continue
        rows = [row for row in entry["rows"] if str(row.get("school") or "") in aliases]
        if rows:
            selected.append({**entry, "rows": rows})
    return selected


def period_label(row: dict[str, Any]) -> str:
    for key in ("year", "cycle", "period", "period_start", "entry_year"):
        value = row.get(key)
        if value is not None:
            return str(value)
    return "Undated"


def row_year(row: dict[str, Any]) -> int | None:
    years = [int(match) for match in _YEAR_PATTERN.findall(period_label(row))]
    return max(years) if years else None


def sorted_rows(entry: dict[str, Any]) -> list[dict[str, Any]]:
    """Newest first; undated rows keep their original order at the end."""
    return sorted(
        entry["rows"],
        key=lambda row: (0, -(row_year(row) or 0)) if row_year(row) is not None else (1, 0),
    )


def has_figure(row: dict[str, Any]) -> bool:
    for key, value in row.items():
        if key in META_FIELDS or value is None or value == "":
            continue
        if isinstance(value, bool):
            continue
        if isinstance(value, (int, float, dict, list)):
            return True
    return False


def latest_row(entry: dict[str, Any]) -> dict[str, Any] | None:
    for row in sorted_rows(entry):
        if has_figure(row):
            return row
    return None


def latest_verified_year(school_id: str) -> int | None:
    years = [
        row_year(row)
        for entry in school_datasets(school_id)
        for row in entry["rows"]
        if has_figure(row)
    ]
    years = [year for year in years if year is not None]
    return max(years) if years else None


def school_year_span(school_id: str) -> dict[str, int | None]:
    years = [
        row_year(row)
        for entry in school_datasets(school_id)
        for row in entry["rows"]
    ]
    years = [year for year in years if year is not None]
    return {"min": min(years) if years else None, "max": max(years) if years else None}


def dataset_label(entry: dict[str, Any]) -> str:
    label = DATASET_LABELS.get(entry["dataset_id"])
    if label:
        return label
    words = entry["dataset_id"].replace("_", " ")
    return re.sub(r"\b\w", lambda match: match.group(0).upper(), words)


@lru_cache(maxsize=1)
def collection_span() -> dict[str, int]:
    years = [
        row_year(row)
        for entry in dataset.figures()["datasets"]
        for row in entry["rows"]
    ]
    years = [year for year in years if year is not None]
    return {"min": min(years), "max": max(years)}


@lru_cache(maxsize=1)
def frozen_record_count() -> int:
    corpora = dataset.data()["corpora"]
    return (
        sum(len(entry["rows"]) for entry in corpora["figures"]["datasets"])
        + sum(len(entry["rows"]) for entry in corpora["granular"]["datasets"])
        + len(corpora["oxbridge"]["records"])
        + len(corpora["us"]["records"])
    )
