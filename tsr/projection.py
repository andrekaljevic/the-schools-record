"""The public projection: everything the static frontend is allowed to know.

The Python modules in this package remain the canonical interpretation of the
frozen dataset — selection, ordering, labelling, formatting, comparison series,
chart geometry and the evidence index.  This module turns their output into a
deterministic set of JSON documents for the web frontend, containing only
explicitly whitelisted public fields: formatted display values, the raw values
behind them, public source references (titles withheld where the record
withholds them), pre-rendered chart markup and routing information.  No source
location, private identifier or working note is emitted, and the projection is
checked for private patterns before it is written.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from typing import Any, Sequence

from . import (
    chart,
    comparison,
    components,
    corpora,
    dataset,
    evidence,
    format as fmt,
    records,
    sources,
    trajectory,
)

PRIVATE_PATTERNS = (
    re.compile(r"drive\.google\.com", re.I),
    re.compile(r"docs\.google\.com", re.I),
    re.compile(r"private-source-[0-9a-f]{16}"),
    re.compile(r"/d/[A-Za-z0-9_-]{25,}"),
)

LAST_REVIEWED = "2 September 2026"
LAST_REVIEWED_SHORT = "2 Sep 2026"

SCHOOL_SECTIONS = (
    ("exam-results", "Examination results"),
    ("university-destinations", "University outcomes"),
    ("oxbridge", "Oxford and Cambridge"),
    ("us-universities", "US and overseas universities"),
    ("school-entry", "School entry"),
)

ARTWORK_ALT = {
    "eton": "Pencil illustration of Eton College's collegiate courtyard and memorial",
    "westminster": "Pencil illustration of Westminster School's ivy-covered courtyard and Victoria Tower",
    "kcs": "Pencil illustration of King's College School Wimbledon",
    "st-pauls": "Pencil illustration of St Paul's School memorial pavilion",
    "spgs": "Pencil illustration of St Paul's Girls' School",
    "wycombe": "Pencil illustration of Wycombe Abbey beside the water",
    "winchester": "Pencil illustration of Winchester College chapel",
}


class PrivateLeak(RuntimeError):
    """A private pattern reached the public projection."""


# --- Helpers ------------------------------------------------------------------


def record_slug(record_id: str) -> str:
    """``fig:winchester_gcse:3`` → ``fig/winchester_gcse/3`` (a static route)."""
    return record_id.replace(":", "/")


SERIES_SLUGS = {"public-source-b6f5e1ed22afa0a6": "oxbridge-destinations"}


def series_slug(metric_id: str) -> str:
    """A readable address for a charted series (the metric id stays the state key)."""
    return SERIES_SLUGS.get(metric_id, metric_id.replace("_", "-"))


def canonical_route(route: str) -> str:
    """``/schools/eton/exam-results#ledger`` → ``/schools/eton/exam-results/#ledger``."""
    path, _, fragment = route.partition("#")
    if not path.endswith("/"):
        path += "/"
    return path + ("#" + fragment if fragment else "")


def _source(ref: str) -> dict[str, Any]:
    described = sources.describe(ref)
    return {
        "ref": described["ref"],
        "title": described["title"],
        "withheld": described["withheld"],
        "role": described.get("role"),
        "url": described["url"],
    }


def _sources(refs: Sequence[str]) -> list[dict[str, Any]]:
    seen: dict[str, dict[str, Any]] = {}
    for ref in refs:
        if ref not in seen:
            seen[ref] = _source(ref)
    return list(seen.values())


def _raw(value: Any) -> Any:
    """A JSON-safe copy of a stored value, kept exactly."""
    if isinstance(value, (dict, list)):
        return json.loads(json.dumps(value, ensure_ascii=False))
    return value


def _status_label(row: dict[str, Any]) -> str:
    return evidence.figures_status(row)


def _span(entry: dict[str, Any]) -> str:
    return components.dataset_span(entry)


def _row_schema(rows: Sequence[dict[str, Any]]) -> tuple[list[str], list[str]]:
    summary = fmt.table_fields(rows)
    expanded = [f for f in fmt.table_fields(rows, expanded=True) if f not in components.EXCLUDED_EXPANDED]
    hidden = [f for f in expanded if f not in summary]
    return summary, hidden


def _field(field: str) -> dict[str, Any]:
    spec = dataset.presentation()["fields"].get(field) or dataset.presentation()["fields"].get(field.split(".")[-1]) or {}
    return {"key": field, "label": fmt.field_label(field), "kind": spec.get("kind") or "decimal"}


# --- Ledgers ------------------------------------------------------------------


def _ledger(entry: dict[str, Any], school: dict[str, Any]) -> dict[str, Any]:
    summary, hidden = _row_schema(entry["rows"])
    fields = summary + hidden
    dataset_refs = list(entry.get("source_refs") or [])
    anchors = components.row_anchors(entry)
    index_of = {id(row): index for index, row in enumerate(entry["rows"])}
    rows = []
    for row in records.sorted_rows(entry):
        index = index_of[id(row)]
        cells = {}
        raw = {}
        for field in fields:
            value = fmt.cell_value(row, field)
            cells[field] = fmt.format_value(field, value, row)
            raw[field] = _raw(value)
        row_ids = [str(item) for item in (row.get("source_ids") or [])] if isinstance(row.get("source_ids"), list) else []
        row_refs = list(dict.fromkeys(row_ids or dataset_refs))
        year = records.row_year(row)
        rows.append({
            "index": index,
            "anchor": anchors[index],
            "period": records.period_label(row),
            "year": year,
            "status": _status_label(row),
            "note": row.get("note") if isinstance(row.get("note"), str) else None,
            "cells": cells,
            "raw": raw,
            "blank": [field for field in fields if raw[field] in (None, "")],
            "sources": _sources(row_refs),
            "datasetSourcesOmitted": len([ref for ref in dataset_refs if ref not in row_refs]),
            "recordId": f"fig:{entry['dataset_id']}:{index}",
        })
    years = sorted({row["year"] for row in rows if row["year"] is not None})
    missing = [year for year in range(years[0], years[-1] + 1) if year not in years] if years else []
    corrections_by_period: dict[str, list[str]] = {}
    for item in corpora.corrections(school["id"]):
        corrections_by_period.setdefault(str(item["period"]), []).append(item["id"])
    for row in rows:
        row["corrections"] = corrections_by_period.get(row["period"], [])
    return {
        "id": entry["dataset_id"],
        "label": records.dataset_label(entry),
        "family": records.dataset_family(entry),
        "domain": entry["domain"],
        "school": school["id"],
        "span": _span(entry),
        "missingYears": missing,
        "rowCount": len(entry["rows"]),
        "basis": entry.get("basis"),
        "notes": entry.get("notes"),
        "fields": [_field(f) for f in fields],
        "summaryFields": summary,
        "hiddenFields": hidden,
        "rows": rows,
        "sources": _sources(dataset_refs),
        "csv": components.dataset_csv(entry),
    }


def _granular_ledger(entry: dict[str, Any]) -> dict[str, Any]:
    corpus = corpora.granular_corpus()
    fields = fmt.table_fields(entry["rows"], expanded=True)
    rows = []
    for index, row in enumerate(entry["rows"]):
        cells = {field: fmt.format_value(field, fmt.cell_value(row, field), row) for field in fields}
        raw = {field: _raw(fmt.cell_value(row, field)) for field in fields}
        rows.append({
            "index": index,
            "total": str(row.get("subject") or row.get("destination") or "").upper() == "TOTAL",
            "cells": cells,
            "raw": raw,
            "blank": [field for field in fields if raw[field] in (None, "")],
            "recordId": f"gran:{entry['dataset_id']}:{index}",
        })
    return {
        "id": entry["dataset_id"],
        "label": corpora.granular_label(entry),
        "domain": entry["domain"],
        "period": str(entry["period"]),
        "rowCount": len(entry["rows"]),
        "basis": entry.get("basis"),
        "fields": [_field(f) for f in fields],
        "rows": rows,
        "sourceTitle": corpus.get("source_title"),
        "asAt": corpus.get("as_at"),
        "sourceNote": corpus.get("source_note"),
        "sources": _sources([str(corpus.get("source_ref"))]),
    }


def _latest(entries: Sequence[dict[str, Any]]) -> dict[str, Any] | None:
    candidates = []
    for entry in entries:
        row = records.latest_row(entry)
        if row is not None:
            candidates.append((entry, row, records.row_year(row)))
    dated = [item for item in candidates if item[2] is not None]
    if not dated:
        return None
    entry, row, year = max(dated, key=lambda item: item[2])
    fields = [
        field for field in fmt.table_fields([row])
        if field not in ("year", "cycle", "period", "confidence", "publication_status", "school")
        and fmt.cell_value(row, field) not in (None, "")
    ]
    status_source = row.get("confidence")
    if status_source is None:
        status_source = row.get("publication_status")
    return {
        "datasetId": entry["dataset_id"],
        "label": records.dataset_label(entry),
        "family": records.dataset_family(entry),
        "year": year,
        "period": records.period_label(row),
        "anchor": components.row_anchor(entry["dataset_id"], row),
        "values": [{"label": fmt.field_label(f), "value": fmt.format_value(f, fmt.cell_value(row, f), row)} for f in fields[:components.LATEST_CARD_LIMIT]],
        "moreFields": max(0, len(fields) - components.LATEST_CARD_LIMIT),
        "status": fmt.format_value("confidence", status_source if status_source is not None else "Not stated", row),
    }


# --- Charts -------------------------------------------------------------------


def _panel_payload(panel: dict[str, Any], school: dict[str, Any], year_from: int, year_to: int) -> dict[str, Any]:
    uid = f"trajectory-{school['id']}-{panel['key']}"
    first = min(point["year"] for item in panel["series"] for point in item.points)
    last = max(point["year"] for item in panel["series"] for point in item.points)
    title = f"{school['name']}: {panel['scale']['label']}"
    description = (
        f"Published {panel['scale']['qualification']} results from {first} to {last}, drawn on the same "
        f"year axis as the school's other rulers. Exact values follow in the table."
    )
    common = dict(uid=uid, title=title, description=description, markers=panel["markers"])
    desktop = chart.panel_svg(panel["series"], year_from, year_to, panel["unit"], chart.TRAJECTORY_DESKTOP, css_class="record-panel panel-desktop", **{**common, "uid": uid + "-desktop"})
    mobile = chart.panel_svg(panel["series"], year_from, year_to, panel["unit"], chart.TRAJECTORY_MOBILE, css_class="record-panel panel-mobile", **{**common, "uid": uid + "-mobile"})
    years = sorted({point["year"] for item in panel["series"] for point in item.points})
    lookup = {(item.label, point["year"]): point for item in panel["series"] for point in item.points}
    table = []
    for year in years:
        values = []
        statuses = []
        for item in panel["series"]:
            point = lookup.get((item.label, year))
            values.append(chart.format_value(point["value"], panel["unit"]) if point else None)
            if point:
                statuses.append(point["status"])
        table.append({"year": year, "values": values, "status": "; ".join(dict.fromkeys(statuses))})
    return {
        "key": panel["key"],
        "qualification": panel["scale"]["qualification"],
        "label": panel["scale"]["label"],
        "denominator": panel["scale"]["denominator"],
        "first": first,
        "last": last,
        "series": [{"label": item.label, "colour": item.colour} for item in panel["series"]],
        "note": panel["note"],
        "svgDesktop": desktop,
        "svgMobile": mobile,
        "table": table,
    }


def _trajectory(school: dict[str, Any], metrics: list[dict[str, Any]]) -> dict[str, Any]:
    panels = trajectory.school_ruler_panels(school, metrics)
    if not panels:
        return {"panels": [], "notCharted": [], "yearFrom": None, "yearTo": None, "gapRule": chart.GAP_RULE}
    years = [point["year"] for panel in panels for item in panel["series"] for point in item.points]
    year_from, year_to = chart.display_range(min(years), max(years))
    charted_ids = set().union(*(panel["dataset_ids"] for panel in panels))
    return {
        "panels": [_panel_payload(panel, school, year_from, year_to) for panel in panels],
        "notCharted": [{"label": label, "span": span} for label, span in trajectory.not_charted_ledgers(school["id"], charted_ids)],
        "yearFrom": year_from,
        "yearTo": year_to,
        "gapRule": chart.GAP_RULE,
    }


def _index_panels(metrics: list[dict[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for metric in metrics:
        frame = trajectory.index_frame(metric)
        panels = {}
        for school in dataset.schools():
            points = comparison.school_points(metric, school["id"])
            if not points:
                panels[school["id"]] = None
                continue
            series = (chart.Series(metric["shortLabel"], tuple(points), chart.PANEL_COLOURS[0]),)
            svg = chart.panel_svg(
                series, frame["year_from"], frame["year_to"], metric["unit"], chart.INDEX_LAYOUT,
                uid=f"index-{school['id']}-{metric['id']}",
                title=f"{school['name']}: {metric['label']}",
                description=f"Published values from {points[0]['year']} to {points[-1]['year']} on a ruler shared by every school on this page. Exact values follow in the table.",
                ceiling=frame["ceiling"],
                markers=(trajectory.EXCEPTIONAL_YEARS,) if metric["domain"] == "results" and trajectory._spans_exceptional_years(points) else (),
                css_class="record-panel index-chart",
            )
            latest = points[-1]
            panels[school["id"]] = {
                "svg": svg,
                "latest": {"value": chart.format_value(latest["value"], metric["unit"]), "year": latest["year"], "status": latest["status"]},
                "count": len(points),
                "table": [{"year": p["year"], "value": chart.format_value(p["value"], metric["unit"]), "status": p["status"]} for p in points],
            }
        out[metric["id"]] = {
            "id": metric["id"],
            "slug": series_slug(metric["id"]),
            "label": metric["label"],
            "shortLabel": metric["shortLabel"],
            "definition": metric["definition"],
            "note": metric["note"],
            "unit": metric["unit"],
            "domain": metric["domain"],
            "derived": any(point.get("annotation") for point in metric["points"]),
            "frame": frame,
            "panels": panels,
        }
    return out


# --- Corpora ------------------------------------------------------------------


def _oxbridge_row(record: dict[str, Any]) -> dict[str, Any]:
    family = corpora.oxbridge_family(record)
    return {
        "recordId": f"ox:{record['record_id']}",
        "slug": record_slug(f"ox:{record['record_id']}"),
        "family": record.get("metric_family"),
        "familyLabel": family["label"],
        "scope": family["scope"],
        "schoolId": corpora.oxbridge_school_id(record),
        "year": corpora.oxbridge_year(record),
        "cycle": corpora.oxbridge_year(record),
        "institution": record.get("institution"),
        "applyCentre": record.get("apply_centre_name"),
        "schoolName": record.get("school_name"),
        "subject": record.get("subject"),
        "dimension": record.get("dimension"),
        "dimensionValue": record.get("dimension_value"),
        "periodStart": record.get("period_start"),
        "periodEnd": record.get("period_end"),
        "periodBasis": record.get("period_basis"),
        "applications": evidence.interval_text(record.get("applications")),
        "offers": evidence.interval_text(record.get("offers")),
        "accepted": evidence.interval_text(record.get("acceptances_or_admissions")),
        "shortlisted": evidence.interval_text(record.get("shortlisted")),
        "offerHolders": evidence.interval_text(record.get("offer_holders")),
        "interviewed": evidence.interval_text(record.get("interviewed")),
        "offerRate": evidence._percent_from_fraction(record.get("offer_rate")),
        "acceptedRate": evidence._percent_from_fraction(record.get("acceptance_or_admission_rate")),
        "applicantsPerPlace": record.get("applicants_per_place"),
        "oxfordOffers": evidence.interval_text(record.get("oxford_offers")),
        "cambridgeOffers": evidence.interval_text(record.get("cambridge_offers")),
        "totalOffers": evidence.interval_text(record.get("total_offers")),
        "cohortScope": record.get("cohort_scope"),
        "rank": record.get("rank"),
        "fiveYearAdmissions": evidence.interval_text(record.get("five_year_admissions")),
        "fiveYearHitRate": evidence._percent_from_fraction(record.get("five_year_hit_rate")),
        "publicationDate": record.get("publication_date"),
        "confidence": str(record.get("confidence") or "—").capitalize(),
        "authority": str(record.get("source_authority") or "—").replace("_", " "),
        "note": record.get("notes") or record.get("college_flow_note") or record.get("rounding_note") or None,
    }


def _oxbridge() -> dict[str, Any]:
    corpus = corpora.oxbridge_corpus()
    rows = [_oxbridge_row(record) for record in corpora.oxbridge_records()]
    families = {
        key: {"key": key, **value} for key, value in corpora.OXBRIDGE_FAMILIES.items()
    }
    per_school = {}
    for school in dataset.schools():
        items = [row for row in rows if row["schoolId"] == school["id"]]
        source_ids = list(dict.fromkeys(str(sid) for record in corpora.oxbridge_records(school["id"]) for sid in (record.get("source_ids") or [])))
        low, high = corpora.years_of(row["year"] for row in items)
        per_school[school["id"]] = {
            "rows": items,
            "count": len(items),
            "cycleFrom": low,
            "cycleTo": high,
            "families": [family for family in corpora.OXBRIDGE_FAMILIES if any(row["family"] == family for row in items)],
            "familyCounts": dict(Counter(row["familyLabel"] for row in items)),
            "universities": sorted({row["institution"] for row in items if row["institution"]}),
            "sources": _sources(source_ids),
        }
    return {
        "definitions": corpus.get("metric_definitions", {}),
        "families": families,
        "familyOrder": list(corpora.OXBRIDGE_FAMILIES),
        "universityWide": [row for row in rows if row["scope"] == "university"],
        "historical": [row for row in rows if row["family"] == "historical_five_year_oxbridge_hit_rate"],
        "schools": per_school,
        "total": len(rows),
    }


def _us_row(record: dict[str, Any]) -> dict[str, Any]:
    count = record.get("count")
    if count is None and record.get("count_lower_bound") is not None:
        count_text = f"≥{record['count_lower_bound']}"
    elif count is None and record.get("approximate_count") is not None:
        count_text = f"≈{record['approximate_count']}"
    elif count is None:
        count_text = "named · no count"
    else:
        count_text = evidence.interval_text(count)
    return {
        "recordId": f"us:{record['record_id']}",
        "slug": record_slug(f"us:{record['record_id']}"),
        "schoolId": corpora.school_id_for(record.get("school")),
        "period": str(record.get("period")),
        "year": corpora.us_year(record),
        "institution": record.get("institution_normalized") or record.get("institution_raw") or "—",
        "institutionRaw": record.get("institution_raw"),
        "country": record.get("institution_country"),
        "region": record.get("region"),
        "metricType": record.get("metric_type"),
        "metricLabel": corpora.us_metric_label(record),
        "metricDefinition": record.get("metric_definition"),
        "count": count_text,
        "aggregate": bool(record.get("is_aggregate")),
        "grain": record.get("record_grain"),
        "denominator": evidence.interval_text(record.get("cohort_denominator")),
        "denominatorBasis": record.get("cohort_denominator_basis"),
        "rate": evidence._percent_from_fraction(record.get("rate")),
        "rateDenominator": record.get("rate_denominator"),
        "status": evidence.us_status(record),
        "canonical": bool(record.get("canonical_for_analysis")),
        "conflictGroup": record.get("conflict_group"),
        "notes": record.get("notes"),
    }


def _us() -> dict[str, Any]:
    corpus = corpora.us_corpus()
    rows = [_us_row(record) for record in corpora.us_records()]
    per_school = {}
    for school in dataset.schools():
        items = [row for row in rows if row["schoolId"] == school["id"]]
        items.sort(key=lambda r: (-(r["year"] or 0), r["period"], r["aggregate"], r["institution"]))
        low, high = corpora.years_of(row["year"] for row in items)
        source_ids = list(dict.fromkeys(str(record.get("source_id")) for record in corpora.us_records(school["id"]) if record.get("source_id")))
        per_school[school["id"]] = {
            "rows": items,
            "count": len(items),
            "from": low,
            "to": high,
            "institutions": len({row["institution"] for row in items if not row["aggregate"]}),
            "aggregates": sum(1 for row in items if row["aggregate"]),
            "periods": list(dict.fromkeys(row["period"] for row in items)),
            "metricTypes": sorted({row["metricType"] for row in items}),
            "regions": sorted({row["region"] for row in items if row["region"]}),
            "sources": _sources(source_ids),
        }
    return {
        "grain": corpus.get("grain"),
        "intendedUse": corpus.get("intended_use"),
        "safeguards": corpus.get("safeguards", []),
        "metricTypes": {key: label for key, label in corpora.US_METRIC_TYPES.items()},
        "metricCounts": dict(Counter(row["metricLabel"] for row in rows)),
        "schools": per_school,
        "total": len(rows),
    }


# --- Evidence -----------------------------------------------------------------


def _evidence_records() -> list[dict[str, Any]]:
    out = []
    for item in evidence.index():
        out.append({
            "id": item.id,
            "slug": record_slug(item.id),
            "corpus": item.corpus,
            "corpusLabel": item.corpus_label,
            "schoolId": item.school_id,
            "school": item.school,
            "year": item.year,
            "period": item.period,
            "domain": item.domain,
            "outcome": item.outcome,
            "title": item.title,
            "status": item.status,
            "statusFamily": evidence.status_family(item.status),
            "summary": [{"label": label, "value": value} for label, value in item.summary],
            "detail": [{"label": label, "value": value} for label, value in evidence.detail_fields(item)],
            "sources": _sources(item.refs),
            "route": canonical_route(item.route),
            "datasetId": item.dataset_id,
            "derived": item.corpus == "oxbridge" and "derived" in str(item.raw.get("metric_family", "")),
            "conflictGroup": item.raw.get("conflict_group") if item.corpus == "us" else None,
            "canonical": bool(item.raw.get("canonical_for_analysis")) if item.corpus == "us" else None,
        })
    return out


def _search_index(items: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """The compact index the evidence-search island loads on demand."""
    compact = []
    for record, item in zip(items, evidence.index()):
        tokens = sorted(set(re.findall(r"[a-z0-9][a-z0-9.,%/–-]*", item.search)))
        compact.append({
            "id": record["id"],
            "c": record["corpus"],
            "sc": record["schoolId"],
            "y": record["year"],
            "p": record["period"],
            "d": record["domain"],
            "o": record["outcome"],
            "t": record["title"],
            "st": record["status"],
            "f": record["statusFamily"],
            "ds": record["datasetId"],
            "v": [[pair["label"], pair["value"]] for pair in record["summary"][:3]],
            "q": " ".join(tokens),
        })
    return compact


def _sources_register() -> list[dict[str, Any]]:
    catalog = corpora.source_catalog()
    usage: dict[str, dict[str, Any]] = {}
    for entry in dataset.figures()["datasets"]:
        refs = set(entry.get("source_refs") or [])
        for row in entry["rows"]:
            refs.update(str(item) for item in (row.get("source_ids") or []))
        for ref in refs:
            use = usage.setdefault(ref, {"datasets": set(), "domains": {}, "schools": set()})
            use["datasets"].add(entry["dataset_id"])
            use["domains"][entry["domain"]] = None
            use["schools"].add(corpora.school_id_for(entry["school"]) or "all")

    def natural(value: str) -> list[Any]:
        return [int(part) if part.isdigit() else part.lower() for part in re.split(r"(\d+)", value)]

    register = []
    for key in sorted(catalog, key=natural):
        described = _source(key)
        use = usage.get(key, {"datasets": set(), "domains": {}, "schools": set()})
        register.append({
            **described,
            "linkedDatasets": sorted(use["datasets"]),
            "domains": list(use["domains"]),
            "schools": sorted(use["schools"]),
        })
    return register


# --- School pages -------------------------------------------------------------


def _inventory(school_id: str) -> list[dict[str, Any]]:
    rows = []
    for domain_group, label in (
        (("exam_results",), "Examination results"),
        (("university_admissions",), "University applications"),
        (("university_destinations",), "University destinations"),
    ):
        page = "exam-results" if domain_group[0] == "exam_results" else "university-destinations"
        for entry in records.school_datasets(school_id, list(domain_group)):
            scales: dict[str, list[int]] = {}
            for row in entry["rows"]:
                year = records.row_year(row)
                key = " · ".join(str(row[k]) for k in ("level", "scale") if row.get(k)) or "as published"
                if year is not None:
                    scales.setdefault(key, []).append(year)
            scale_text = "; ".join(
                f"{key} {min(years)}–{max(years)}" if min(years) != max(years) else f"{key} {min(years)}"
                for key, years in scales.items()
            ) or "undated"
            rows.append({
                "section": label,
                "family": records.dataset_family(entry),
                "label": records.dataset_label(entry),
                "href": f"/schools/{school_id}/{page}/#{entry['dataset_id']}",
                "span": _span(entry),
                "scales": scale_text,
                "rows": len(entry["rows"]),
            })
    for entry in corpora.granular_datasets(school_id):
        page = "exam-results" if entry["domain"] == "exam_results" else "university-destinations"
        rows.append({
            "section": "Subject and destination detail",
            "family": "Itemised",
            "label": corpora.granular_label(entry),
            "href": f"/schools/{school_id}/{page}/#{entry['dataset_id']}",
            "span": str(entry["period"]),
            "scales": "counts as printed",
            "rows": len(entry["rows"]),
        })
    ox = corpora.oxbridge_records(school_id)
    if ox:
        low, high = corpora.years_of(corpora.oxbridge_year(item) for item in ox)
        rows.append({
            "section": "Oxford and Cambridge admissions",
            "family": "Apply-centre records",
            "label": "Oxford and Cambridge records",
            "href": f"/schools/{school_id}/oxbridge/",
            "span": f"{low}–{high}",
            "scales": " · ".join(sorted({corpora.oxbridge_family(item)["label"] for item in ox})),
            "rows": len(ox),
        })
    us = corpora.us_records(school_id)
    if us:
        low, high = corpora.years_of(corpora.us_year(item) for item in us)
        rows.append({
            "section": "US and overseas universities",
            "family": "Institution records",
            "label": "US and overseas university records",
            "href": f"/schools/{school_id}/us-universities/",
            "span": f"{low}–{high}",
            "scales": " · ".join(sorted({corpora.us_metric_label(item) for item in us})),
            "rows": len(us),
        })
    return rows


def _school(school: dict[str, Any], metrics: list[dict[str, Any]]) -> dict[str, Any]:
    slug = school["id"]
    exam = records.school_datasets(slug, ["exam_results"])
    university = records.school_datasets(slug, ["university_admissions", "university_destinations"])
    counts = corpora.school_corpus_counts(slug)
    span = records.school_year_span(slug)
    process = corpora.admissions_process(slug) or {}
    ox_low, ox_high = corpora.years_of(corpora.oxbridge_year(item) for item in corpora.oxbridge_records(slug))
    us_low, us_high = corpora.years_of(corpora.us_year(item) for item in corpora.us_records(slug))
    return {
        "id": slug,
        "name": school["name"],
        "short": school["short"],
        "oneLine": school["oneLine"],
        "caution": school["caution"],
        "evidenceWindow": school["evidenceWindow"],
        "spanFrom": span["min"],
        "spanTo": span["max"],
        "artworkAlt": ARTWORK_ALT.get(slug, ""),
        "latestVerifiedYear": records.latest_verified_year(slug),
        "datasetCount": len(records.school_datasets(slug)),
        "examLedgers": len(exam),
        "examRows": sum(len(entry["rows"]) for entry in exam),
        "examFamilies": list(dict.fromkeys(records.dataset_family(entry) for entry in exam)),
        "universityLedgers": len(university),
        "universityRows": sum(len(entry["rows"]) for entry in university),
        "universityFamilies": list(dict.fromkeys(records.dataset_family(entry) for entry in university)),
        "counts": {**counts, "total": sum(counts.values())},
        "oxbridgeSpan": f"{ox_low}–{ox_high}" if ox_low else None,
        "usSpan": f"{us_low}–{us_high}" if us_low else None,
        "entryStatus": process.get("status"),
        "entryFreshness": process.get("freshness"),
        "corrections": len(corpora.corrections(slug)),
        "conflicts": len(corpora.conflicts(slug)),
        "latestExam": _latest(exam),
        "latestUniversity": _latest(university),
        "trajectory": _trajectory(school, metrics),
        "inventory": _inventory(slug),
        "exam": [_ledger(entry, school) for entry in exam],
        "university": [_ledger(entry, school) for entry in university],
        "granularExam": [_granular_ledger(entry) for entry in corpora.granular_datasets(slug) if entry["domain"] == "exam_results"],
        "granularUniversity": [_granular_ledger(entry) for entry in corpora.granular_datasets(slug) if entry["domain"] != "exam_results"],
        "entry": _entry(process) if process else None,
    }


def _entry(process: dict[str, Any]) -> dict[str, Any]:
    """The school-entry evidence, whitelisted field by field (no source location)."""
    return {
        "status": process.get("status"),
        "freshness": process.get("freshness"),
        "entryPoints": [str(item) for item in (process.get("entryPoints") or [])],
        "steps": [{"label": str(step.get("label")), "detail": str(step.get("detail"))} for step in (process.get("steps") or [])],
        "limit": process.get("limit"),
        "sourceTitle": process.get("sourceTitle"),
    }


# --- Corrections, method, comparison, dossier ---------------------------------


def _value_text(value: Any) -> str:
    if isinstance(value, list):
        return " / ".join(_value_text(item) for item in value)
    if isinstance(value, dict):
        return " · ".join(f"{key}: {_value_text(item)}" for key, item in value.items())
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def _rows_for(school_id: str | None, period: str) -> list[dict[str, str]]:
    """Ledger rows carrying the same school and period as a correction (the correction names a metric, not a row)."""
    if not school_id:
        return []
    out = []
    for entry in records.school_datasets(school_id):
        anchors = components.row_anchors(entry)
        page = "exam-results" if entry["domain"] == "exam_results" else "university-destinations"
        for index, row in enumerate(entry["rows"]):
            if records.period_label(row) == period:
                out.append({"label": records.dataset_label(entry), "href": f"/schools/{school_id}/{page}/#{anchors[index]}"})
    return out


def _corrections() -> dict[str, Any]:
    corrections = []
    for item in corpora.corrections():
        corrections.append({
            "rows": _rows_for(corpora.school_id_for(item["school"]), str(item["period"])),
            "id": item["id"],
            "schoolId": corpora.school_id_for(item["school"]),
            "school": item["school"],
            "period": str(item["period"]),
            "metric": item["metric"],
            "old": _value_text(item["old"]),
            "new": _value_text(item["new"]),
            "reason": item["reason"],
            "status": str(item.get("status", "")).replace("_", " ").capitalize(),
            "sources": _sources(item.get("source_refs") or []),
        })
    conflicts = []
    for item in corpora.conflicts():
        values = []
        for candidate in item.get("values") or []:
            if isinstance(candidate, dict) and "value" in candidate:
                values.append({"value": _value_text(candidate["value"]), "basis": candidate.get("basis"), "source": candidate.get("source")})
            else:
                values.append({"value": _value_text(candidate), "basis": None, "source": None})
        conflicts.append({
            "id": item["id"],
            "schoolId": corpora.school_id_for(item["school"]),
            "school": item["school"],
            "period": str(item["period"]),
            "metric": item["metric"],
            "values": values,
            "treatment": item["treatment"],
        })
    return {
        "corrections": corrections,
        "conflicts": conflicts,
        "versionAuthority": [
            {"order": item["order"], "version": item["version"], "controls": item["controls"], "doesNotControl": item.get("does_not_control")}
            for item in corpora.version_authority()
        ],
    }


def _method() -> dict[str, Any]:
    definitions = corpora.definitions()
    return {
        "confidenceCodes": definitions.get("confidence_codes", {}),
        "definitions": {key: text for key, text in definitions.items() if isinstance(text, str)},
        "gradeMapping": definitions.get("grade_mapping", {}),
        "guardrails": corpora.guardrails(),
        "lineage": corpora.lineage(),
        "versionAuthority": _corrections()["versionAuthority"],
        "gradingScales": list(dataset.presentation()["grading_scales"].values()),
        "oxbridgeDefinitions": corpora.oxbridge_corpus().get("metric_definitions", {}),
        "usSafeguards": corpora.us_corpus().get("safeguards", []),
        "sourceReferences": len(corpora.source_catalog()),
    }


def _marker(marker: chart.Marker) -> dict[str, Any]:
    return {"kind": marker.kind, "start": marker.start, "end": marker.end, "label": marker.label, "shortLabel": marker.short_label}


def _metric_markers(metric: dict[str, Any]) -> tuple[chart.Marker, ...]:
    return (trajectory.EXCEPTIONAL_YEARS,) if metric["domain"] == "results" else ()


def _compare(metrics: list[dict[str, Any]]) -> dict[str, Any]:
    all_years = [point["year"] for metric in metrics for point in metric["points"]]
    default = comparison.metric_by_id(metrics, "a_level_astar") or metrics[0]
    ids = [school["id"] for school in dataset.schools()]
    names = {school["id"]: school["name"] for school in dataset.schools()}
    return {
        "yearMin": min(all_years),
        "yearMax": max(all_years),
        "defaultMetric": default["id"],
        "defaultSchools": ids[:2],
        "metrics": [
            {
                "id": metric["id"],
                "label": metric["label"],
                "shortLabel": metric["shortLabel"],
                "definition": metric["definition"],
                "note": metric["note"],
                "domain": metric["domain"],
                "unit": metric["unit"],
                "markers": [_marker(marker) for marker in _metric_markers(metric)],
                "points": [
                    {"schoolId": p["schoolId"], "year": p["year"], "value": p["value"], "status": p["status"], "datasetId": p["datasetId"], "derived": bool(p.get("annotation"))}
                    for p in metric["points"]
                ],
            }
            for metric in metrics
        ],
        "gapRule": chart.GAP_RULE,
        "defaultSvgDesktop": chart.comparison_panel(default, ids[0], ids[1], min(all_years), max(all_years), chart.COMPARISON_DESKTOP, names=names, markers=_metric_markers(default)),
        "defaultSvgMobile": chart.comparison_panel(default, ids[0], ids[1], min(all_years), max(all_years), chart.COMPARISON_MOBILE, names=names, markers=_metric_markers(default)),
    }


def _dossier(metrics: list[dict[str, Any]]) -> dict[str, Any]:
    metric = comparison.metric_by_id(metrics, "a_level_astar")
    points = [p for p in metric["points"] if p["schoolId"] in ("eton", "westminster") and 2015 <= p["year"] <= 2019]
    years = sorted({p["year"] for p in points})
    rows = []
    for year in years:
        row = {"year": year}
        for school_id in ("eton", "westminster"):
            match = next((p for p in points if p["schoolId"] == school_id and p["year"] == year), None)
            row[school_id] = {"value": f"{match['value']:.1f}%", "status": match["status"]} if match else None
        rows.append(row)
    names = {school["id"]: school["name"] for school in dataset.schools()}
    return {
        "metric": {"id": metric["id"], "label": metric["label"], "definition": metric["definition"], "note": metric["note"]},
        "rows": rows,
        "svgDesktop": chart.comparison_panel(metric, "eton", "westminster", 2015, 2019, chart.COMPARISON_DESKTOP, names=names, markers=_metric_markers(metric)),
        "svgMobile": chart.comparison_panel(metric, "eton", "westminster", 2015, 2019, chart.COMPARISON_MOBILE, names=names, markers=_metric_markers(metric)),
        "prepared": LAST_REVIEWED,
    }


# --- Assembly -----------------------------------------------------------------


def build() -> dict[str, Any]:
    """Every projection document, keyed by output path (without extension)."""
    metrics = comparison.metrics()
    counts = corpora.corpus_counts()
    metadata = dataset.metadata()
    span = records.collection_span()
    evidence_records = _evidence_records()
    schools = [_school(school, metrics) for school in dataset.schools()]
    record_ids = {item.id for item in evidence.index()}
    for school in schools:
        for ledger in [*school["exam"], *school["university"]]:
            for row in ledger["rows"]:
                if row["recordId"] not in record_ids:  # pragma: no cover - the evidence index enumerates every row
                    raise RuntimeError(f"ledger row {row['anchor']} has no evidence record")

    documents: dict[str, Any] = {
        "site": {
            "snapshot": metadata["snapshot_version"],
            "baselineCommit": metadata["baseline_commit"],
            "redactions": metadata["source_location_redactions"],
            "lastReviewed": LAST_REVIEWED,
            "lastReviewedShort": LAST_REVIEWED_SHORT,
            "spanFrom": span["min"],
            "spanTo": span["max"],
            "ledgersFrom": min(int(re.search(r"(18|19|20)\d{2}", s["evidenceWindow"]).group(0)) for s in schools if re.search(r"(18|19|20)\d{2}", s["evidenceWindow"])),
            "counts": counts,
            "corrections": len(corpora.corrections()),
            "conflicts": len(corpora.conflicts()),
            "sourceReferences": len(corpora.source_catalog()),
            "schools": [
                {
                    "id": s["id"], "name": s["name"], "short": s["short"], "oneLine": s["oneLine"],
                    "evidenceWindow": s["evidenceWindow"], "latestVerifiedYear": s["latestVerifiedYear"],
                    "datasetCount": s["datasetCount"], "counts": s["counts"], "artworkAlt": s["artworkAlt"],
                    "entryStatus": s["entryStatus"], "corrections": s["corrections"], "conflicts": s["conflicts"],
                }
                for s in schools
            ],
            "sections": [{"key": key, "label": label} for key, label in SCHOOL_SECTIONS],
            "corpusLabels": evidence.CORPUS_LABELS,
            "domainLabels": evidence.DOMAIN_LABELS,
        },
        "index-panels": _index_panels(metrics),
        "compare": _compare(metrics),
        "dossier": _dossier(metrics),
        "oxbridge": _oxbridge(),
        "us": _us(),
        "corrections": _corrections(),
        "method": _method(),
        "evidence-records": evidence_records,
        "evidence-search": _search_index(evidence_records),
        "sources": _sources_register(),
    }
    for school in schools:
        documents[f"schools/{school['id']}"] = school
    return documents


def serialise(document: Any) -> str:
    return json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def scan(text: str, where: str) -> None:
    for pattern in PRIVATE_PATTERNS:
        if pattern.search(text):
            raise PrivateLeak(f"{where} contains a private pattern ({pattern.pattern})")
