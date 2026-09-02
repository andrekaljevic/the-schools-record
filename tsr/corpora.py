"""Typed access to every frozen corpus.

``data/dataset.json`` carries four corpora — the figures ledgers, the granular
subject and destination tables, the Oxford and Cambridge admissions records and
the US-university records — together with the figures corpus' own editorial
apparatus (corrections, published differences, source catalogue, definitions)
and the school-entry process material.  This module reads each of them as it is
and resolves the different school spellings the corpora use onto the record's
seven school identifiers.  Nothing here alters a stored value.
"""

from __future__ import annotations

import re
from functools import lru_cache
from typing import Any, Iterable

from . import dataset

# Spellings used by the other corpora, the corrections ledger and the historical
# secondary tables, in addition to the names carried on each school record.
EXTRA_ALIASES: dict[str, tuple[str, ...]] = {
    "eton": ("Eton",),
    "kcs": (
        "KCS Wimbledon",
        "KCS",
        "King's College School",
        "King's College School Wimbledon",
        "King's College School, Wimbledon",
    ),
    "spgs": ("SPGS", "St Paul's Girls' School", "St Paul's Girls School"),
    "st-pauls": ("St Paul's", "St Paul's School", "St Pauls School"),
    "westminster": ("Westminster",),
    "winchester": ("Winchester",),
    "wycombe": ("Wycombe Abbey School", "Wycombe Abbey"),
}

_APOSTROPHES = "’‘ʼ`´"


def normalise_name(name: Any) -> str:
    """A spelling-insensitive key: apostrophes, punctuation and case removed."""
    text = str(name or "")
    for mark in _APOSTROPHES:
        text = text.replace(mark, "'")
    text = text.replace("'", "")
    text = re.sub(r"[^a-z0-9]+", " ", text.lower())
    return text.strip()


@lru_cache(maxsize=1)
def _alias_index() -> dict[str, str]:
    index: dict[str, str] = {}
    for school in dataset.schools():
        names = {
            school["name"],
            school["short"],
            school["applyCentreName"],
            school["usName"],
            *EXTRA_ALIASES.get(school["id"], ()),
        }
        for name in names:
            index[normalise_name(name)] = school["id"]
    return index


def school_id_for(name: Any) -> str | None:
    """The record's school identifier for any spelling the corpora use."""
    if name is None:
        return None
    return _alias_index().get(normalise_name(name))


def school_ids() -> list[str]:
    return [school["id"] for school in dataset.schools()]


def school(school_id: str) -> dict[str, Any] | None:
    for item in dataset.schools():
        if item["id"] == school_id:
            return item
    return None


# --- Figures corpus apparatus -----------------------------------------------


def figures_corpus() -> dict[str, Any]:
    return dataset.figures()


def corrections(school_id: str | None = None) -> list[dict[str, Any]]:
    items = figures_corpus()["corrections"]
    if school_id is None:
        return list(items)
    return [item for item in items if school_id_for(item.get("school")) == school_id]


def conflicts(school_id: str | None = None) -> list[dict[str, Any]]:
    items = figures_corpus()["conflicts"]
    if school_id is None:
        return list(items)
    return [item for item in items if school_id_for(item.get("school")) == school_id]


def source_catalog() -> dict[str, dict[str, Any]]:
    return figures_corpus()["source_catalog"]


def definitions() -> dict[str, Any]:
    return figures_corpus()["definitions"]


def analytical_findings() -> list[dict[str, Any]]:
    return figures_corpus()["analytical_findings"]


def version_authority() -> list[dict[str, Any]]:
    return figures_corpus()["version_authority"]


def lineage() -> list[dict[str, Any]]:
    return figures_corpus()["lineage"]


def guardrails() -> list[str]:
    return figures_corpus()["implementation_guardrails"]


# --- Granular corpus ---------------------------------------------------------


def granular_corpus() -> dict[str, Any]:
    return dataset.data()["corpora"]["granular"]


def granular_datasets(school_id: str | None = None) -> list[dict[str, Any]]:
    entries = granular_corpus()["datasets"]
    if school_id is None:
        return list(entries)
    return [entry for entry in entries if school_id_for(entry.get("school")) == school_id]


GRANULAR_LABELS = {
    "st_pauls_subject_results_2010_alevel": "A-level results by subject · 2010",
    "st_pauls_subject_results_2010_gcse": "GCSE results by subject · 2010",
    "st_pauls_destinations_2009_by_university": "Leaver destinations by university · 2009",
    "st_pauls_destinations_2009_overseas": "Overseas leaver destinations · 2009",
}


def granular_label(entry: dict[str, Any]) -> str:
    return GRANULAR_LABELS.get(entry["dataset_id"], entry["dataset_id"].replace("_", " "))


# --- Oxbridge corpus ---------------------------------------------------------

OXBRIDGE_FAMILIES: dict[str, dict[str, str]] = {
    "apply_centre_outcomes": {
        "label": "Apply-centre outcomes",
        "scope": "school",
        "summary": "Applications, offers and accepted or admitted outcomes for one school's apply centre, one university, one entry cycle.",
    },
    "derived_combined_oxbridge_apply_centre_outcomes": {
        "label": "Combined Oxford + Cambridge apply-centre outcomes · derived",
        "scope": "school",
        "summary": "The sum of exact, unsuppressed Oxford and Cambridge apply-centre counts for the same named cycle. Derived, and labelled as such.",
    },
    "apply_centre_subject_outcomes_rounded": {
        "label": "Apply-centre outcomes by subject · rounded intervals",
        "scope": "school",
        "summary": "Counts published as intervals rounded down to multiples of five, kept as ranges.",
    },
    "apply_centre_college_outcomes_rounded": {
        "label": "Apply-centre outcomes by college · rounded intervals",
        "scope": "school",
        "summary": "Counts published as intervals rounded down to multiples of five, kept as ranges.",
    },
    "school_published_oxbridge_offers": {
        "label": "School-published Oxbridge offers",
        "scope": "school",
        "summary": "A school's own published offer claim, kept apart from the university apply-centre counts.",
    },
    "historical_five_year_oxbridge_hit_rate": {
        "label": "Historical five-year Oxbridge hit rate · secondary table",
        "scope": "historical",
        "summary": "A 2007 secondary excerpt ranking 100 schools; the five-year period is not stated and the methodology is unclear.",
    },
    "institution_overall_outcomes": {
        "label": "University-wide outcomes",
        "scope": "university",
        "summary": "Whole-university applications, offers and admissions for a cycle.",
    },
    "subject_outcomes": {
        "label": "University subject outcomes",
        "scope": "university",
        "summary": "Applications, offers and admissions for one subject across all applicants.",
    },
    "course_competition": {
        "label": "Course competition",
        "scope": "university",
        "summary": "Applicants per place over an aggregated period; not an offer or acceptance rate.",
    },
    "subject_admissions_process": {
        "label": "Subject admissions process",
        "scope": "university",
        "summary": "Preliminary process counts for one subject and cycle.",
    },
}


def oxbridge_corpus() -> dict[str, Any]:
    return dataset.data()["corpora"]["oxbridge"]


def oxbridge_family(record: dict[str, Any]) -> dict[str, str]:
    family = str(record.get("metric_family") or "")
    return OXBRIDGE_FAMILIES.get(
        family, {"label": family.replace("_", " "), "scope": "university", "summary": ""}
    )


def oxbridge_school_id(record: dict[str, Any]) -> str | None:
    return school_id_for(record.get("apply_centre_name")) or school_id_for(record.get("school_name"))


def oxbridge_records(school_id: str | None = None) -> list[dict[str, Any]]:
    items = oxbridge_corpus()["records"]
    if school_id is None:
        return list(items)
    return [item for item in items if oxbridge_school_id(item) == school_id]


def oxbridge_year(record: dict[str, Any]) -> int | None:
    for key in ("cycle_year", "entry_year", "period_end"):
        value = record.get(key)
        if isinstance(value, int):
            return value
    return None


# --- US corpus ---------------------------------------------------------------

US_METRIC_TYPES: dict[str, str] = {
    "leaver_destination": "Leaver destination",
    "firm_place_destination": "Firm place taken up",
    "accepted_by_university_abroad": "Accepted by a university abroad",
    "prospectus_destination_snapshot": "Prospectus destination snapshot",
    "destination_presence_only": "Destination named · no count",
    "UCAS_acceptance_ST30": "UCAS acceptance · ST30 table",
    "approximate_destination_claim": "Approximate destination claim",
    "reported_places_in_offer_year_narrative": "Reported places · offer-year narrative",
    "trailing_10y_destination": "Trailing ten-year destinations",
    "offer_presence_only": "Offer named · no count",
    "offer": "Offer",
    "offer_lower_bound": "Offers · lower bound",
}

US_SOURCE_TIERS: dict[str, str] = {
    "A_primary_school_direct": "Primary · school-published",
    "B_primary_school_wayback_capture": "Primary · archived school page",
    "A_primary_research_report": "Primary · research report",
    "C_derived_reconciliation": "Derived · reconciliation",
    "D_secondary_media": "Secondary · media",
}


def us_corpus() -> dict[str, Any]:
    return dataset.data()["corpora"]["us"]


def us_records(school_id: str | None = None) -> list[dict[str, Any]]:
    items = us_corpus()["records"]
    if school_id is None:
        return list(items)
    return [item for item in items if school_id_for(item.get("school")) == school_id]


def us_metric_label(record: dict[str, Any]) -> str:
    metric = str(record.get("metric_type") or "")
    return US_METRIC_TYPES.get(metric, metric.replace("_", " "))


def us_year(record: dict[str, Any]) -> int | None:
    years = re.findall(r"(?:19|20)\d{2}", str(record.get("period") or ""))
    return max(int(year) for year in years) if years else None


# --- School entry (admissions process) ---------------------------------------


def admissions_process(school_id: str) -> dict[str, Any] | None:
    for entry in dataset.admissions_process():
        if entry.get("schoolId") == school_id:
            return entry
    return None


# --- Accounting --------------------------------------------------------------


def corpus_counts() -> dict[str, int]:
    figures = sum(len(entry["rows"]) for entry in figures_corpus()["datasets"])
    granular = sum(len(entry["rows"]) for entry in granular_corpus()["datasets"])
    oxbridge = len(oxbridge_corpus()["records"])
    us = len(us_corpus()["records"])
    return {
        "figures": figures,
        "granular": granular,
        "oxbridge": oxbridge,
        "us": us,
        "total": figures + granular + oxbridge + us,
    }


def school_corpus_counts(school_id: str) -> dict[str, int]:
    """How many records of each corpus name this school."""
    from . import records  # local import: records depends on dataset only

    figures = sum(len(entry["rows"]) for entry in records.school_datasets(school_id))
    return {
        "figures": figures,
        "granular": sum(len(entry["rows"]) for entry in granular_datasets(school_id)),
        "oxbridge": len(oxbridge_records(school_id)),
        "us": len(us_records(school_id)),
    }


def years_of(values: Iterable[int | None]) -> tuple[int | None, int | None]:
    years = [value for value in values if isinstance(value, int)]
    return (min(years), max(years)) if years else (None, None)
