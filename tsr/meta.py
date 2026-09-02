"""Page titles, descriptions and shareable metadata for every route.

Streamlit renders the record client-side, so the only metadata it can set
reliably before the page loads is the document title.  Each route therefore
sets its own title through ``st.set_page_config``; the description, Open Graph
fields and a schema.org Dataset description are written into the document head
after render by a small, guarded script that cannot affect the page if it
fails.  Nothing here reads or changes a figure.
"""

from __future__ import annotations

import json
import re
from typing import Any

from . import corpora, dataset, records

SITE = "The Schools Record"
DEFAULT_TITLE = f"{SITE} | Independent school results, year by year"
DEFAULT_DESCRIPTION = (
    "A public, source-led record of examination results, university destinations "
    "and admissions evidence for seven leading UK independent schools, kept on "
    "their published definitions and never collapsed into a ranking."
)

STATIC_TITLES: dict[str, tuple[str, str]] = {
    "/": (DEFAULT_TITLE, DEFAULT_DESCRIPTION),
    "/schools": ("School records", "Seven school records: examination results, university outcomes, Oxford and Cambridge admissions and US-university evidence, year by year."),
    "/compare": ("Compare like with like", "Compare two schools on one precisely defined measure with an exact-value table and visible comparability limits."),
    "/methodology": ("Methodology", "Definitions before comparisons: populations, grading systems, exceptional years, outcome types and derived presentation."),
    "/evidence": ("Evidence centre", "Search every frozen record, trace a displayed figure to its source references, and read how the figures are checked."),
    "/oxbridge": ("Oxford and Cambridge admissions records", "Apply-centre applications, offers and admissions by school and cycle, with university-wide context and historical tables."),
    "/us-universities": ("US and overseas university records", "Named US and overseas destinations, offers and acceptances by school and year, with aggregates and published differences flagged."),
    "/corrections": ("Corrections and published differences", "Every recorded correction and every case where credible publications disagree, in plain English, with the value the record uses."),
    "/corrections/report": ("Report a correction", "Report a specific, evidenced correction. The frozen edition is not changed until a versioned editorial review."),
    "/professional": ("Professional access", "Sourced comparison dossiers and professional research access built on the frozen record."),
    "/sample-dossier": ("Sample dossier", "An illustrative sourced examination comparison."),
    "/changelog": ("Changelog", "Material releases and any versioned statistical revision."),
    "/about": ("About", "A permanent public record of school outcomes, not a ranking."),
    "/privacy": ("Privacy", "What the record collects and how private source locations are protected."),
    "/terms": ("Terms", "How the record may be used."),
}

_SCHOOL_PAGES = {
    "exam-results": ("Examination results", "Published A-level, GCSE and IGCSE, IB and Cambridge Pre-U results, each on its published scale."),
    "university-destinations": ("University outcomes", "Applications, offers, acceptances and final destinations, kept apart."),
    "oxbridge": ("Oxford and Cambridge records", "Apply-centre applications, offers and admissions by university and entry cycle."),
    "us-universities": ("US and overseas university records", "Named institutions, counts and outcome types by year."),
    "school-entry": ("School entry", "Published admissions process evidence and known gaps."),
}


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def for_route(route: str) -> dict[str, Any]:
    """Title, description and structured data for a route."""
    if route in STATIC_TITLES:
        title, description = STATIC_TITLES[route]
        return {"title": title if route == "/" else f"{title} | {SITE}", "description": description, "dataset": route == "/"}
    match = re.match(r"^/schools/([^/]+)(?:/([^/]+))?$", route)
    if match:
        school = records.find_school(match.group(1))
        if school is not None:
            page = match.group(2)
            if page is None:
                return {
                    "title": f"{school['name']} | {SITE}",
                    "description": _clean(f"{school['name']} record, {school['evidenceWindow']}. {school['oneLine']}"),
                    "dataset": True,
                }
            if page in _SCHOOL_PAGES:
                label, description = _SCHOOL_PAGES[page]
                return {
                    "title": f"{school['name']} · {label} | {SITE}",
                    "description": _clean(f"{school['name']}: {description}"),
                    "dataset": True,
                }
    return {"title": f"Not found | {SITE}", "description": DEFAULT_DESCRIPTION, "dataset": False}


def structured_data(route: str) -> dict[str, Any]:
    """A schema.org Dataset description of the frozen record."""
    metadata = dataset.metadata()
    counts = corpora.corpus_counts()
    span = records.collection_span()
    return {
        "@context": "https://schema.org",
        "@type": "Dataset",
        "name": "The Schools Record · frozen public dataset",
        "description": DEFAULT_DESCRIPTION,
        "version": metadata["snapshot_version"],
        "temporalCoverage": f"{span['min']}/{span['max']}",
        "isAccessibleForFree": True,
        "license": "Use figures only with the year, population, denominator, qualification, outcome type, evidence status and caveat displayed with them.",
        "variableMeasured": [
            "Examination grade shares by qualification and scale",
            "University applications, offers and acceptances by entry cycle",
            "Leaver destinations by institution",
        ],
        "size": f"{counts['total']} frozen records",
        "spatialCoverage": [school["name"] for school in dataset.schools()],
    }


def head_script(route: str) -> str:
    """Script that writes description, Open Graph and Dataset metadata into the page head."""
    meta = for_route(route)
    payload = {
        "title": meta["title"],
        "description": meta["description"],
        "dataset": structured_data(route) if meta["dataset"] else None,
    }
    return (
        "<script>(function(){try{var m=" + json.dumps(payload, ensure_ascii=False) + ";"
        "var d=window.parent&&window.parent.document;if(!d)return;"
        "function set(sel,attrs){var e=d.head.querySelector(sel);if(!e){e=d.createElement('meta');"
        "Object.keys(attrs).forEach(function(k){if(k!=='content')e.setAttribute(k,attrs[k]);});d.head.appendChild(e);}"
        "e.setAttribute('content',attrs.content);}"
        "d.title=m.title;"
        "set('meta[name=\"description\"]',{name:'description',content:m.description});"
        "set('meta[property=\"og:title\"]',{property:'og:title',content:m.title});"
        "set('meta[property=\"og:description\"]',{property:'og:description',content:m.description});"
        "set('meta[property=\"og:type\"]',{property:'og:type',content:'website'});"
        "set('meta[property=\"og:site_name\"]',{property:'og:site_name',content:'The Schools Record'});"
        "set('meta[name=\"twitter:card\"]',{name:'twitter:card',content:'summary'});"
        "var link=d.head.querySelector('link[rel=\"canonical\"]');if(!link){link=d.createElement('link');link.setAttribute('rel','canonical');d.head.appendChild(link);}"
        "link.setAttribute('href',window.parent.location.origin+window.parent.location.pathname+window.parent.location.search);"
        "var old=d.getElementById('tsr-dataset-jsonld');if(old)old.remove();"
        "if(m.dataset){var s=d.createElement('script');s.type='application/ld+json';s.id='tsr-dataset-jsonld';s.text=JSON.stringify(m.dataset);d.head.appendChild(s);}"
        "var hash=window.parent.location.hash;if(hash&&hash.length>1){var tries=0;var t=setInterval(function(){tries++;var el=d.getElementById(decodeURIComponent(hash.slice(1)));"
        "if(el){el.scrollIntoView({block:'start'});clearInterval(t);}else if(tries>20){clearInterval(t);}},250);}"
        "}catch(e){}})();</script>"
    )
