"""Like-for-like comparison series.

A port of the front-end's ``lib/comparison`` module.  Series are assembled from
frozen values only; the single derived measure (Oxford offer rate) is computed
at display time from the stored offers and applications and is labelled as such.
"""

from __future__ import annotations

import re
from typing import Any

from . import dataset, records

A_LEVEL_DATASETS = frozenset({
    "eton_alevel_primary_sheets",
    "eton_alevel_headline_gap_years",
    "westminster_alevel",
    "st_pauls_alevel",
    "kcs_alevel_only",
    "winchester_alevel",
    "spgs_exam_anchors",
    "wycombe_exam_anchors",
})

METRIC_FIELDS = {
    "a_level_astar": "a_star",
    "a_level_astar_a": "a_star_a",
    "a_level_astar_b": "a_star_b",
    "gcse_grade_9": "grade_9",
    "gcse_grade_9_8": "grade_9_8",
    "gcse_grade_9_7": "grade_9_7",
    "gcse_legacy_astar": "a_star",
    "gcse_legacy_astar_a": "a_star_a",
    "gcse_legacy_astar_b": "a_star_b",
}

_STATUS_LABELS = {"P": "Primary", "S": "Secondary", "D": "Derived", "R": "Reconstructed"}

DESTINATION_DATASETS = frozenset({
    "eton_destinations_2000_2015",
    "eton_later_oxbridge_counts",
    "westminster_destinations",
    "st_pauls_destinations",
    "kcs_destinations",
    "spgs_destinations",
    "wycombe_destinations_and_offers",
    "winchester_destination_and_historic_access",
})

OXBRIDGE_DESTINATION_METRIC = "public-source-b6f5e1ed22afa0a6"


def _coalesce(row: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = row.get(key)
        if value is not None:
            return value
    return None


def evidence_status(row: dict[str, Any]) -> str:
    raw = _coalesce(row, "publication_status", "confidence", "evidence_status")
    if raw is None:
        raw = "Not stated"
    return " / ".join(_STATUS_LABELS.get(part, part) for part in str(raw).split("/"))


def _is_a_level(entry: dict[str, Any], row: dict[str, Any]) -> bool:
    if entry["dataset_id"] not in A_LEVEL_DATASETS:
        return False
    if entry["dataset_id"] in ("spgs_exam_anchors", "wycombe_exam_anchors"):
        return bool(re.search(r"a.?level", str(row.get("level") or ""), re.IGNORECASE))
    return True


def _gcse_scale(entry: dict[str, Any], row: dict[str, Any]) -> str:
    if entry["dataset_id"] in ("westminster_gcse_reformed", "kcs_gcse_detailed_9_1"):
        return "numbered"
    if entry["dataset_id"] == "westminster_gcse_old_scale":
        return "legacy"
    scale = str(row.get("scale") or "").lower()
    if re.search(r"9.?1|number", scale):
        return "numbered"
    if re.search(r"a\*|a.?g|letter", scale):
        return "legacy"
    if entry["dataset_id"] in ("spgs_exam_anchors", "wycombe_exam_anchors") and re.search(
        r"gcse", str(row.get("level") or ""), re.IGNORECASE
    ):
        return "numbered" if row.get("grade_9") is not None else "legacy"
    return "other"


def _metric_value(metric_id: str, entry: dict[str, Any], row: dict[str, Any]) -> float | None:
    if metric_id.startswith("a_level_"):
        if not _is_a_level(entry, row):
            return None
        year = records.row_year(row)
        if year in (2020, 2021):
            return None
        field = METRIC_FIELDS[metric_id]
        if metric_id == "a_level_astar_a" and year is not None and year < 2010:
            field = "grade_a"
        if metric_id == "a_level_astar_b" and year is not None and year < 2010:
            field = "grade_a_b"
        value = row.get(field)
        return value if isinstance(value, (int, float)) and not isinstance(value, bool) else None

    scale = _gcse_scale(entry, row)
    wanted = "legacy" if "legacy" in metric_id else "numbered"
    if scale != wanted:
        return None
    year = records.row_year(row)
    if year in (2020, 2021):
        return None
    field = METRIC_FIELDS[metric_id]
    if entry["dataset_id"] in ("st_pauls_gcse", "kcs_gcse_headline"):
        overrides = (
            {"gcse_grade_9": "top", "gcse_grade_9_8": "top_2", "gcse_grade_9_7": "top_3"}
            if wanted == "numbered"
            else {
                "gcse_legacy_astar": "top",
                "gcse_legacy_astar_a": "top_2",
                "gcse_legacy_astar_b": "top_3",
            }
        )
        field = overrides.get(metric_id, field)
    if entry["dataset_id"] == "winchester_gcse":
        overrides = (
            {
                "gcse_grade_9": "grade_9",
                "gcse_grade_9_8": "top_equivalent",
                "gcse_grade_9_7": "astar_a_equivalent",
            }
            if wanted == "numbered"
            else {
                "gcse_legacy_astar": "top_equivalent",
                "gcse_legacy_astar_a": "astar_a_equivalent",
                "gcse_legacy_astar_b": "astar_b_or_9_6",
            }
        )
        field = overrides.get(metric_id, field)
    value = row.get(field)
    return value if isinstance(value, (int, float)) and not isinstance(value, bool) else None


def _exam_points(metric_id: str) -> list[dict[str, Any]]:
    points: list[dict[str, Any]] = []
    for school in dataset.schools():
        for entry in records.school_datasets(school["id"], ["exam_results"]):
            for row in entry["rows"]:
                value = _metric_value(metric_id, entry, row)
                year = records.row_year(row)
                if value is None or year is None:
                    continue
                points.append({
                    "schoolId": school["id"],
                    "schoolName": school["name"],
                    "year": year,
                    "value": value,
                    "status": evidence_status(row),
                    "datasetId": entry["dataset_id"],
                    "annotation": None,
                })
    return points


def _oxford_offer_rate_points() -> list[dict[str, Any]]:
    points: list[dict[str, Any]] = []
    for school in dataset.schools():
        for entry in records.school_datasets(school["id"], ["university_admissions"]):
            if not entry["dataset_id"].startswith("oxford_strict_"):
                continue
            for row in entry["rows"]:
                year = records.row_year(row)
                applications = row.get("applications")
                offers = row.get("offers")
                if (
                    year is None
                    or not isinstance(applications, (int, float))
                    or isinstance(applications, bool)
                    or not isinstance(offers, (int, float))
                    or isinstance(offers, bool)
                    or applications == 0
                ):
                    continue
                from .format import to_fixed

                points.append({
                    "schoolId": school["id"],
                    "schoolName": school["name"],
                    "year": year,
                    "value": float(to_fixed(offers / applications * 100)),
                    "status": evidence_status(row),
                    "datasetId": entry["dataset_id"],
                    "annotation": "Derived at display time from frozen offers and applications",
                })
    return points


def _oxbridge_destination_points() -> list[dict[str, Any]]:
    points: list[dict[str, Any]] = []
    for school in dataset.schools():
        for entry in records.school_datasets(school["id"], ["university_destinations"]):
            if entry["dataset_id"] not in DESTINATION_DATASETS:
                continue
            for row in entry["rows"]:
                year = records.row_year(row)
                value = row.get("oxbridge")
                if value is None and row.get("metric") == "matriculations":
                    value = row.get("value")
                basis = str(row.get("basis") or "").lower()
                if (
                    year is None
                    or not isinstance(value, (int, float))
                    or isinstance(value, bool)
                    or "offer" in basis
                    or "application" in basis
                ):
                    continue
                points.append({
                    "schoolId": school["id"],
                    "schoolName": school["name"],
                    "year": year,
                    "value": value,
                    "status": evidence_status(row),
                    "datasetId": entry["dataset_id"],
                    "annotation": None,
                })
    return points


def _resolve_conflicts(points: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for point in points:
        grouped.setdefault(f"{point['schoolId']}:{point['year']}", []).append(point)
    resolved = [
        group[0]
        for group in grouped.values()
        if len({point["value"] for point in group}) == 1
    ]
    return sorted(resolved, key=lambda point: (point["year"], point["schoolName"]))


def metrics() -> list[dict[str, Any]]:
    built: list[dict[str, Any]] = []
    for metric in dataset.presentation()["comparison"]["metrics"]:
        metric_id = str(metric["id"])
        if metric_id in METRIC_FIELDS:
            points = _exam_points(metric_id)
        elif metric_id == "oxford_offer_rate":
            points = _oxford_offer_rate_points()
        elif metric_id == OXBRIDGE_DESTINATION_METRIC:
            points = _oxbridge_destination_points()
        else:
            points = []
        if not points:
            continue
        built.append({
            "id": metric_id,
            "label": str(metric["label"]),
            "shortLabel": str(metric["shortLabel"]),
            "definition": str(metric["definition"]),
            "note": str(metric["note"]),
            "domain": str(metric["domain"]),
            "unit": str(metric["unit"]),
            "points": _resolve_conflicts(points),
        })
    return built
