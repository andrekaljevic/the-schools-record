"""The evidence index: every frozen record, addressable, searchable and traceable.

Each of the 2,277 frozen records — a figures-ledger row, a granular subject or
destination row, an Oxford and Cambridge admissions record or a US-university
record — is given a stable public identifier and a common description (school,
period, outcome type, evidence status, key values, source references and the
page on which it is displayed).  The index is built at display time from the
frozen dataset and never stores a new value.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any, Iterable, Sequence

from . import corpora, dataset, format as fmt, records, sources
from .format import to_fixed

CORPUS_LABELS = {
    "figures": "School results and destinations",
    "granular": "Subject and destination detail",
    "oxbridge": "Oxford and Cambridge admissions",
    "us": "US and overseas universities",
}

DOMAIN_LABELS = {
    "exam_results": "Examination results",
    "university_admissions": "University applications",
    "university_destinations": "University destinations",
}

STATUS_ORDER = ("Primary", "Secondary", "Derived", "Reconstructed", "Conflict", "Not stated")


@dataclass(frozen=True)
class Record:
    id: str
    corpus: str
    school_id: str | None
    school: str
    year: int | None
    period: str
    domain: str
    outcome: str
    title: str
    status: str
    summary: tuple[tuple[str, str], ...]
    refs: tuple[str, ...]
    route: str
    dataset_id: str | None
    raw: dict[str, Any] = field(compare=False, hash=False)
    search: str = field(default="", compare=False, hash=False)

    @property
    def corpus_label(self) -> str:
        return CORPUS_LABELS[self.corpus]


# --- Helpers ----------------------------------------------------------------


def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, tuple)):
        return " ".join(_text(item) for item in value)
    if isinstance(value, dict):
        return " ".join(f"{key} {_text(item)}" for key, item in value.items())
    return str(value)


def _blob(*parts: Any) -> str:
    return " ".join(_text(part) for part in parts).lower()


def _percent_from_fraction(value: Any) -> str:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return f"{to_fixed(value * 100)}%"
    return "—"


def interval_text(value: Any) -> str:
    """Render an Oxford FOI rounded interval exactly as published."""
    if isinstance(value, dict) and "interval_min" in value:
        low, high = value.get("interval_min"), value.get("interval_max")
        rounding = value.get("rounding") or "published interval"
        return f"{low}–{high} ({rounding})"
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return f"{value:,}" if float(value).is_integer() else str(value)
    return "—" if value in (None, "") else str(value)


def figures_status(row: dict[str, Any]) -> str:
    for key in ("publication_status", "confidence", "evidence_status"):
        value = row.get(key)
        if value is not None:
            return fmt.format_value("confidence", value, row)
    return "Not stated"


def oxbridge_status(record: dict[str, Any]) -> str:
    confidence = str(record.get("confidence") or "Not stated").capitalize()
    authority = str(record.get("source_authority") or "").replace("_", " ")
    return f"{confidence} · {authority}" if authority else confidence


def us_status(record: dict[str, Any]) -> str:
    quality = str(record.get("evidence_quality") or "Not stated").capitalize()
    tier = corpora.US_SOURCE_TIERS.get(str(record.get("source_tier") or ""), "")
    return f"{quality} · {tier}" if tier else quality


def status_family(status: str) -> str:
    """Collapse a status label to one of the register's headline families."""
    lowered = status.lower()
    if "conflict" in lowered:
        return "Conflict"
    if lowered.startswith(("primary", "high")):
        return "Primary"
    if lowered.startswith(("secondary", "medium", "low")):
        return "Secondary"
    if lowered.startswith(("derived", "d ")) or "derived" in lowered:
        return "Derived"
    if lowered.startswith(("reconstructed", "provisional")) or "modelled" in lowered:
        return "Reconstructed"
    if lowered.startswith("d"):
        return "Derived"
    return "Not stated"


# --- Builders ---------------------------------------------------------------


def _figures_records() -> list[Record]:
    built: list[Record] = []
    schools = {school["id"]: school for school in dataset.schools()}
    for entry in dataset.figures()["datasets"]:
        dataset_id = entry["dataset_id"]
        label = records.dataset_label(entry)
        domain = entry["domain"]
        page = "exam-results" if domain == "exam_results" else "university-destinations"
        fields = [
            item
            for item in fmt.table_fields(entry["rows"])
            if item not in ("year", "cycle", "period", "confidence", "publication_status", "level", "scale")
        ]
        for index, row in enumerate(entry["rows"]):
            school_id = corpora.school_id_for(row.get("school") if entry["school"] == "All seven schools" else entry["school"])
            school = schools.get(school_id, {}).get("name", entry["school"])
            period = records.period_label(row)
            values = []
            for item in fields:
                value = fmt.cell_value(row, item)
                if value in (None, "") or isinstance(value, (dict, list)):
                    continue
                values.append((fmt.field_label(item), fmt.format_value(item, value, row)))
                if len(values) == 6:
                    break
            qualification = " · ".join(
                str(row[key]) for key in ("level", "scale") if row.get(key)
            )
            title = f"{label} · {period}" + (f" · {qualification}" if qualification else "")
            route = f"/schools/{school_id}/{page}#{dataset_id}" if school_id else f"/evidence"
            built.append(
                Record(
                    id=f"fig:{dataset_id}:{index}",
                    corpus="figures",
                    school_id=school_id,
                    school=school,
                    year=records.row_year(row),
                    period=period,
                    domain=domain,
                    outcome=DOMAIN_LABELS[domain],
                    title=title,
                    status=figures_status(row),
                    summary=tuple(values),
                    refs=tuple(dict.fromkeys([*(entry.get("source_refs") or []), *(str(item) for item in (row.get("source_ids") or []))])),
                    route=route,
                    dataset_id=dataset_id,
                    raw=row,
                    search=_blob(school, label, period, qualification, dataset_id, domain, row, entry.get("basis")),
                )
            )
    return built


def _granular_records() -> list[Record]:
    built: list[Record] = []
    corpus = corpora.granular_corpus()
    schools = {school["id"]: school for school in dataset.schools()}
    for entry in corpora.granular_datasets():
        dataset_id = entry["dataset_id"]
        label = corpora.granular_label(entry)
        school_id = corpora.school_id_for(entry["school"])
        school = schools.get(school_id, {}).get("name", entry["school"])
        page = "exam-results" if entry["domain"] == "exam_results" else "university-destinations"
        for index, row in enumerate(entry["rows"]):
            subject = row.get("subject") or row.get("destination") or ""
            values = []
            for key, value in row.items():
                if key in ("subject", "destination", "country") or value in (None, ""):
                    continue
                values.append((fmt.field_label(key), fmt.format_value(key, value, row)))
                if len(values) == 6:
                    break
            built.append(
                Record(
                    id=f"gran:{dataset_id}:{index}",
                    corpus="granular",
                    school_id=school_id,
                    school=school,
                    year=records.row_year({"period": entry["period"]}),
                    period=str(entry["period"]),
                    domain=entry["domain"],
                    outcome=DOMAIN_LABELS[entry["domain"]] + " · itemised",
                    title=f"{label} · {subject}" if subject else label,
                    status=f"Primary · {corpus.get('source_title', 'school booklet')}",
                    summary=tuple(values),
                    refs=(str(corpus.get("source_ref")),),
                    route=f"/schools/{school_id}/{page}#{dataset_id}",
                    dataset_id=dataset_id,
                    raw=row,
                    search=_blob(school, label, entry["period"], subject, row, dataset_id, entry.get("basis")),
                )
            )
    return built


def oxbridge_summary(record: dict[str, Any]) -> tuple[tuple[str, str], ...]:
    family = record.get("metric_family")
    values: list[tuple[str, str]] = []
    if family == "historical_five_year_oxbridge_hit_rate":
        values.append(("Rank", str(record.get("rank"))))
        values.append(("Five-year admissions", interval_text(record.get("five_year_admissions"))))
        values.append(("Five-year hit rate", _percent_from_fraction(record.get("five_year_hit_rate"))))
        return tuple(values)
    if family == "course_competition":
        values.append(("Applicants per place", str(record.get("applicants_per_place"))))
        values.append(("Period", f"{record.get('period_start')}–{record.get('period_end')}"))
        return tuple(values)
    if family == "school_published_oxbridge_offers":
        for key, label in (("oxford_offers", "Oxford offers"), ("cambridge_offers", "Cambridge offers"), ("total_offers", "Total offers")):
            values.append((label, interval_text(record.get(key))))
        return tuple(values)
    if family in ("apply_centre_subject_outcomes_rounded", "apply_centre_college_outcomes_rounded"):
        for key, label in (("applications", "Applications"), ("shortlisted", "Shortlisted"), ("offer_holders", "Offer holders")):
            if record.get(key) is not None:
                values.append((label, interval_text(record.get(key))))
        return tuple(values)
    for key, label in (
        ("applications", "Applications"),
        ("offers", "Offers"),
        ("acceptances_or_admissions", "Accepted / admitted"),
        ("interviewed", "Interviewed"),
    ):
        if record.get(key) is not None:
            values.append((label, interval_text(record.get(key))))
    if record.get("offer_rate") is not None:
        values.append(("Offer rate", _percent_from_fraction(record.get("offer_rate"))))
    if record.get("acceptance_or_admission_rate") is not None:
        values.append(("Accepted / admitted rate", _percent_from_fraction(record.get("acceptance_or_admission_rate"))))
    return tuple(values)


def _oxbridge_records() -> list[Record]:
    built: list[Record] = []
    schools = {school["id"]: school for school in dataset.schools()}
    for record in corpora.oxbridge_records():
        family = corpora.oxbridge_family(record)
        school_id = corpora.oxbridge_school_id(record)
        school_name = record.get("apply_centre_name") or record.get("school_name") or record.get("institution") or "University-wide"
        school = schools.get(school_id, {}).get("name", school_name)
        year = corpora.oxbridge_year(record)
        if record.get("period_start") and record.get("period_end"):
            period = f"{record['period_start']}–{record['period_end']}"
        elif year is not None:
            period = str(year)
        else:
            period = str(record.get("publication_date") or record.get("period") or "Undated")
        dimension = record.get("dimension_value") or record.get("subject") or record.get("domicile")
        institution = record.get("institution") or ""
        title = " · ".join(part for part in (family["label"], institution, str(dimension) if dimension else "", period) if part)
        route = f"/schools/{school_id}/oxbridge" if school_id else "/oxbridge"
        built.append(
            Record(
                id=f"ox:{record['record_id']}",
                corpus="oxbridge",
                school_id=school_id,
                school=school,
                year=year,
                period=period,
                domain="university_admissions",
                outcome=family["label"],
                title=title,
                status=oxbridge_status(record),
                summary=oxbridge_summary(record),
                refs=tuple(str(item) for item in (record.get("source_ids") or [])),
                route=route,
                dataset_id=None,
                raw=record,
                search=_blob(school, school_name, institution, family["label"], period, dimension, record),
            )
        )
    return built


def us_summary(record: dict[str, Any]) -> tuple[tuple[str, str], ...]:
    values: list[tuple[str, str]] = []
    if record.get("count") is not None:
        values.append(("Count", interval_text(record["count"])))
    elif record.get("count_lower_bound") is not None:
        values.append(("Count · lower bound", f"≥{record['count_lower_bound']}"))
    elif record.get("approximate_count") is not None:
        values.append(("Count · approximate", f"≈{record['approximate_count']}"))
    else:
        values.append(("Count", "Named, no count"))
    if record.get("cohort_denominator") is not None:
        values.append(("Cohort denominator", interval_text(record["cohort_denominator"])))
    if record.get("rate") is not None:
        values.append(("Rate", _percent_from_fraction(record["rate"])))
    values.append(("Region", str(record.get("region") or "—")))
    return tuple(values)


def _us_records() -> list[Record]:
    built: list[Record] = []
    schools = {school["id"]: school for school in dataset.schools()}
    for record in corpora.us_records():
        school_id = corpora.school_id_for(record.get("school"))
        school = schools.get(school_id, {}).get("name", record.get("school"))
        institution = record.get("institution_normalized") or record.get("institution_raw") or "Aggregate"
        metric = corpora.us_metric_label(record)
        period = str(record.get("period") or "Undated")
        title = f"{institution} · {metric} · {period}"
        built.append(
            Record(
                id=f"us:{record['record_id']}",
                corpus="us",
                school_id=school_id,
                school=school,
                year=corpora.us_year(record),
                period=period,
                domain="university_destinations",
                outcome=metric,
                title=title,
                status=us_status(record),
                summary=us_summary(record),
                refs=(str(record.get("source_id")),) if record.get("source_id") else (),
                route=f"/schools/{school_id}/us-universities" if school_id else "/us-universities",
                dataset_id=None,
                raw=record,
                search=_blob(school, institution, record.get("institution_raw"), metric, period, record.get("region"), record.get("metric_definition"), record.get("notes"), record.get("conflict_group")),
            )
        )
    return built


@lru_cache(maxsize=1)
def index() -> tuple[Record, ...]:
    """Every frozen record, in corpus order, with a stable identifier."""
    return tuple([*_figures_records(), *_granular_records(), *_oxbridge_records(), *_us_records()])


@lru_cache(maxsize=1)
def _by_id() -> dict[str, Record]:
    return {record.id: record for record in index()}


def record(record_id: str) -> Record | None:
    return _by_id().get(record_id)


def counts() -> dict[str, int]:
    tally = {key: 0 for key in CORPUS_LABELS}
    for item in index():
        tally[item.corpus] += 1
    tally["total"] = sum(tally.values())
    return tally


# --- Filters ----------------------------------------------------------------


def filter_records(
    items: Iterable[Record],
    *,
    corpus: str | None = None,
    school_id: str | None = None,
    domain: str | None = None,
    status: str | None = None,
    year_from: int | None = None,
    year_to: int | None = None,
    query: str | None = None,
    dataset_id: str | None = None,
    period: str | None = None,
) -> list[Record]:
    tokens = [token for token in (query or "").lower().split() if token]
    selected: list[Record] = []
    for item in items:
        if corpus and item.corpus != corpus:
            continue
        if school_id and item.school_id != school_id:
            continue
        if domain and item.domain != domain:
            continue
        if status and status_family(item.status) != status:
            continue
        if year_from is not None and (item.year is None or item.year < year_from):
            continue
        if year_to is not None and (item.year is None or item.year > year_to):
            continue
        if dataset_id and item.dataset_id != dataset_id:
            continue
        if period and item.period != period:
            continue
        if tokens and not all(token in item.search for token in tokens):
            continue
        selected.append(item)
    return selected


def records_for_claim(dataset_id: str, period: str) -> list[Record]:
    """The records behind one displayed figure (the "View evidence" link)."""
    return filter_records(index(), dataset_id=dataset_id, period=period)


def domains_present(items: Sequence[Record]) -> list[str]:
    return [domain for domain in DOMAIN_LABELS if any(item.domain == domain for item in items)]


def year_bounds(items: Sequence[Record]) -> tuple[int, int]:
    years = [item.year for item in items if item.year is not None]
    return (min(years), max(years)) if years else (1836, 2026)


# --- Detail fields ----------------------------------------------------------

OXBRIDGE_FIELD_LABELS = {
    "record_id": "Record identifier",
    "metric_family": "Record family",
    "institution": "University",
    "apply_centre_name": "Apply centre",
    "apply_centre_id": "Apply-centre code",
    "school_name": "School as printed",
    "cycle_year": "Entry cycle",
    "entry_year": "Intended entry year",
    "application_window_start_year": "Application window opened",
    "year_basis": "Year basis",
    "applications": "Applications",
    "offers": "Offers",
    "offer_holders": "Offer holders",
    "shortlisted": "Shortlisted",
    "interviewed": "Interviewed",
    "not_invited_or_withdrew": "Not invited or withdrew",
    "acceptances_or_admissions": "Accepted / admitted",
    "offer_rate": "Offer rate",
    "acceptance_or_admission_rate": "Accepted / admitted rate",
    "published_applicants_per_offer": "Applicants per offer · as published",
    "applicants_per_place": "Applicants per place",
    "period_basis": "Period basis",
    "period_start": "Period start",
    "period_end": "Period end",
    "period": "Period",
    "period_note": "Period note",
    "publication_date": "Publication date",
    "rank": "Rank in the published table",
    "five_year_admissions": "Five-year admissions",
    "five_year_hit_rate": "Five-year hit rate",
    "school_type_code": "School type code",
    "school_sector": "Sector",
    "postcode": "Postcode",
    "subject": "Subject",
    "division": "Division",
    "dimension": "Breakdown",
    "dimension_value": "Breakdown value",
    "domicile": "Domicile",
    "derivation": "Derivation",
    "source_authority": "Source authority",
    "source_ids": "Source references",
    "source_metric_labels": "Source metric labels",
    "published_success_rate_label": "Published success-rate label",
    "published_application_share": "Published application share",
    "published_offer_share": "Published offer share",
    "published_acceptance_share": "Published acceptance share",
    "college_flow_note": "College flow note",
    "rounding_note": "Rounding note",
    "suppression": "Suppression",
    "confidence": "Confidence",
    "notes": "Notes",
    "cohort_scope": "Cohort scope",
    "oxford_offers": "Oxford offers",
    "cambridge_offers": "Cambridge offers",
    "total_offers": "Total offers",
}

US_FIELD_LABELS = {
    "record_id": "Record identifier",
    "school": "School as printed",
    "period": "Period",
    "institution_normalized": "Institution",
    "institution_raw": "Institution as printed",
    "institution_country": "Country",
    "region": "Region",
    "metric_type": "Outcome type",
    "metric_definition": "Outcome definition",
    "count": "Count",
    "count_lower_bound": "Count · lower bound",
    "approximate_count": "Count · approximate",
    "is_aggregate": "Aggregate row",
    "record_grain": "Record grain",
    "cohort_denominator": "Cohort denominator",
    "cohort_denominator_basis": "Denominator basis",
    "rate": "Rate",
    "rate_denominator": "Rate denominator",
    "publication_year": "Publication year",
    "evidence_quality": "Evidence quality",
    "source_tier": "Source tier",
    "source_id": "Source reference",
    "source_title": "Source title",
    "source_url": "Source location",
    "source_notes": "Source notes",
    "normalization_confidence": "Name-matching confidence",
    "canonical_for_analysis": "Used for analysis",
    "conflict_group": "Published-difference group",
    "notes": "Notes",
}

PLAIN_KEYS = {
    "cycle_year",
    "entry_year",
    "application_window_start_year",
    "period_start",
    "period_end",
    "publication_year",
    "rank",
    "record_id",
    "apply_centre_id",
    "postcode",
    "school_type_code",
    "conflict_group",
    "source_id",
}

RATE_FIELDS = {
    "offer_rate",
    "acceptance_or_admission_rate",
    "five_year_hit_rate",
    "rate",
    "published_application_share",
    "published_offer_share",
    "published_acceptance_share",
}


def detail_fields(item: Record) -> list[tuple[str, str]]:
    """Every field of the frozen record, labelled and formatted for display."""
    raw = item.raw
    rows: list[tuple[str, str]] = []
    if item.corpus in ("figures", "granular"):
        for path, value in fmt.flatten(raw):
            if path in ("source_ids", "source_url"):
                continue
            rows.append((fmt.field_label(path), fmt.format_value(path, value, raw)))
        return rows
    labels = OXBRIDGE_FIELD_LABELS if item.corpus == "oxbridge" else US_FIELD_LABELS
    for key, value in raw.items():
        if key in ("source_ids", "source_id", "source_url"):
            continue
        if value is None or value == "":
            text = "—"
        elif key in PLAIN_KEYS:
            text = str(value)
        elif key in RATE_FIELDS:
            text = _percent_from_fraction(value)
        elif isinstance(value, bool):
            text = "Yes" if value else "No"
        elif isinstance(value, dict):
            text = interval_text(value)
        elif isinstance(value, list):
            text = ", ".join(str(part) for part in value)
        elif key == "source_tier":
            text = corpora.US_SOURCE_TIERS.get(str(value), str(value))
        elif key == "metric_type":
            text = corpora.us_metric_label(raw)
        elif key == "metric_family":
            text = corpora.oxbridge_family(raw)["label"]
        elif key == "source_title" and str(value) == "Source title withheld":
            text = "Withheld · identified by public reference"
        else:
            text = interval_text(value) if isinstance(value, (int, float)) else str(value).replace("_", " ")
        rows.append((labels.get(key, key.replace("_", " ").capitalize()), text))
    return rows
