from __future__ import annotations

import json


def _compact_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _replace_once(source: str, before: str, after: str, label: str) -> str:
    matches = source.count(before)
    if matches != 1:
        raise RuntimeError(
            f"Unable to apply {label}: expected one bundle match, found {matches}"
        )
    return source.replace(before, after, 1)


KCS_ENTRY_SOURCES = {
    "KCS_ALEVEL_IB_2017_2025_PACK": {
        "id": "kcs-alevel-ib-results-2017-2025-chronological",
        "title": "KCS Wimbledon · A-level and IB results · 2017–2025 chronological pack",
        "role": "controlling school-result tables for modern A-level pathway counts, actual A-level takers, A-level entries, IB candidates, IB Higher-Level entries and the unique combined cohort",
    },
    "KCS_GCSE_2017_2025_PACK": {
        "id": "kcs-gcse-igcse-results-2017-2025-chronological",
        "title": "KCS Wimbledon · GCSE and IGCSE results · 2017–2025 chronological pack",
        "role": "controlling modern candidate and subject-entry denominators; records the 2018 Additional Mathematics exclusion and the numbered/lettered entry split",
    },
    "KCS_OKC_1990": {
        "id": "kcs-okc-newsletter-78-summer-1990-results",
        "title": "Old King's Club Newsletter 78 · Summer 1990 examination results",
        "role": "primary contemporary KCS report: A-level candidates and entry-grade counts; GCSE candidates split between Upper and Lower Fifth and entry-grade counts",
    },
    "KCS_OKC_1991": {
        "id": "kcs-okc-newsletter-80-summer-1991-results",
        "title": "Old King's Club Newsletter 80 · Summer 1991 examination results",
        "role": "primary contemporary KCS report: A-level candidates and printed grade counts/percentages; GCSE candidates split between Upper and Lower Fifth with A–C counts only",
    },
    "KCS_OKC_1995": {
        "id": "kcs-okc-newsletter-87-summer-1995-results",
        "title": "Old King's Club Newsletter 87 · Summer 1995 examination results",
        "role": "primary contemporary KCS report: exact A-level candidates/entries and exact GCSE A* count/share; GCSE total denominator not printed",
    },
    "KCS_OKC_1996": {
        "id": "kcs-okc-newsletter-89-summer-1996-results",
        "title": "Old King's Club Newsletter 89 · Summer 1996 examination results",
        "role": "primary contemporary KCS report: exact A-level candidates/entries and exact GCSE entry total",
    },
    "KCS_OKC_1997": {
        "id": "kcs-okc-newsletter-91-summer-1997-results",
        "title": "Old King's Club Newsletter 91 · Summer 1997 examination results",
        "role": "primary contemporary KCS report: exact A-level and GCSE candidate and subject-entry totals",
    },
    "KCS_OKC_2003": {
        "id": "kcs-okc-newsletter-103-summer-2003-results",
        "title": "Old King's Club Newsletter 103 · Summer 2003 examination results",
        "role": "primary contemporary KCS report: A-level, IB, combined Upper Sixth and GCSE candidate counts plus A-level/GCSE subject-exam totals",
    },
    "KCS_OKC_2004": {
        "id": "kcs-okc-newsletter-105-summer-2004-results",
        "title": "Old King's Club Newsletter 105 · Summer 2004 examination results",
        "role": "primary contemporary KCS report: A-level, IB, combined Upper Sixth and GCSE candidate counts plus A-level/GCSE subject-exam totals",
    },
    "KCS_FT_2007": {
        "id": "financial-times-top-schools-2007-results",
        "title": "Financial Times · Top 1,000 Schools · 8 March 2008",
        "role": "secondary league table for 2007 results: 44 A-level-only pupils, 111 IB candidates and 155 combined candidates",
    },
    "KCS_FT_2009": {
        "id": "financial-times-independent-schools-2009-results",
        "title": "Financial Times · Independent schools · 12 September 2009",
        "role": "secondary league table: 135 IB candidates and no A-level candidates",
    },
    "KCS_FT_2011": {
        "id": "financial-times-schools-special-2011-results",
        "title": "Financial Times Schools Special · 10 September 2011",
        "role": "secondary league table: 145 IB candidates and 436 printed IB Higher-Level entries; the printed entry total is retained despite exceeding three per candidate by one",
    },
    "KCS_LEGACY_COHORT_REPORT": {
        "id": "kcs-legacy-cohort-secondary-report",
        "title": "KCS Wimbledon · legacy sixth-form cohort report",
        "role": "secondary synthesis used only for explicitly labelled 2008 lower-bound, 2014, 2016 and 2017 cohort facts where the underlying primary file is not held",
    },
}


KCS_ENTRY_CORRECTIONS = [
    {
        "id": "C27",
        "school": "King's College School Wimbledon",
        "metric": "A-level and IB candidate and grade-entry denominators",
        "period": "2018–2025",
        "old": "grade percentages held without candidate or entry denominators",
        "new": "route pupils, actual A-level takers, A-level entries, IB candidates, IB Higher-Level entries and unique combined cohorts encoded wherever printed",
        "status": "primary_denominator_reconciliation",
        "source_refs": ["KCS_ALEVEL_IB_2017_2025_PACK"],
        "reason": "The school result tables supply exact denominators. Combined entries remain explicitly scoped to A-level entries plus IB Higher-Level entries, and the 2024/25 IB crossover pupil is not double-counted in the combined cohort.",
    },
    {
        "id": "C28",
        "school": "King's College School Wimbledon",
        "metric": "GCSE/IGCSE candidate and subject-entry denominators",
        "period": "2017–2025",
        "old": "2018 and 2019 coverage strings only; later candidate and entry totals absent",
        "new": "candidate and total-entry counts added for every exact modern year held, with numbered/lettered splits and exclusions typed separately",
        "status": "primary_denominator_reconciliation",
        "source_refs": ["KCS_GCSE_2017_2025_PACK"],
        "reason": "The candidate denominator is distinct from the grade-entry denominator. The 2018 total excludes 88 Additional Mathematics entries; 2017 has a pupil count but no safely recoverable exact entry total.",
    },
    {
        "id": "C29",
        "school": "King's College School Wimbledon",
        "metric": "historic examination candidate and entry counts",
        "period": "1990–2017",
        "old": "historic count-bearing reports not represented in the result ledgers",
        "new": "primary newsletter counts and separately labelled secondary league-table cohort facts added without manufacturing missing denominators",
        "status": "historic_source_extension",
        "source_refs": [
            "KCS_OKC_1990",
            "KCS_OKC_1991",
            "KCS_OKC_1995",
            "KCS_OKC_1996",
            "KCS_OKC_1997",
            "KCS_OKC_2003",
            "KCS_OKC_2004",
            "KCS_FT_2007",
            "KCS_FT_2009",
            "KCS_FT_2011",
            "KCS_LEGACY_COHORT_REPORT",
        ],
        "reason": "Only counts actually printed, arithmetically exact from the printed table, or explicitly typed as secondary/lower-bound evidence are encoded. Rounded percentages are not inverted into false exact totals.",
    },
]


KCS_HISTORIC_ALEVEL_ROWS = [
    {
        "year": 1990,
        "candidates": 122,
        "entries": 383,
        "a_count": 111,
        "b_count": 125,
        "c_count": 82,
        "d_count": 44,
        "e_count": 21,
        "confidence": "P",
        "note": "Contemporary school report; grade counts sum exactly to the printed 383 entries.",
        "source_ids": ["KCS_OKC_1990"],
    },
    {
        "year": 1991,
        "candidates": 132,
        "entries": 420,
        "a_count": 167,
        "b_count": 127,
        "c_count": 62,
        "confidence": "P/D",
        "note": "The source prints 132 candidates and A/B/C counts. The 420-entry total is an exact arithmetic reconstruction from the printed counts and percentages, not a separately printed total.",
        "source_ids": ["KCS_OKC_1991"],
    },
    {
        "year": 1995,
        "candidates": 132,
        "entries": 425,
        "confidence": "P",
        "source_ids": ["KCS_OKC_1995"],
    },
    {
        "year": 1996,
        "candidates": 136,
        "entries": 438,
        "confidence": "P",
        "source_ids": ["KCS_OKC_1996"],
    },
    {
        "year": 1997,
        "candidates": 133,
        "entries": 424,
        "confidence": "P",
        "source_ids": ["KCS_OKC_1997"],
    },
    {
        "year": 2003,
        "candidates": 91,
        "entries": 287,
        "confidence": "P",
        "note": "A-level route only; the same report gives 47 IB candidates and a unique combined Upper Sixth cohort of 138.",
        "source_ids": ["KCS_OKC_2003"],
    },
    {
        "year": 2004,
        "candidates": 81,
        "entries": 260,
        "confidence": "P",
        "note": "A-level route only; the same report gives 67 IB candidates and a unique combined Upper Sixth cohort of 148.",
        "source_ids": ["KCS_OKC_2004"],
    },
    {
        "year": 2007,
        "candidates": 44,
        "confidence": "S",
        "note": "Financial Times table reporting 2007 results; A-level-only pupils, separate from 111 IB candidates.",
        "source_ids": ["KCS_FT_2007"],
    },
]


KCS_HISTORIC_COMBINED_ROWS = [
    {
        "year": 2003,
        "candidates": 138,
        "alevel_pathway_pupils": 91,
        "alevel_takers": 91,
        "alevel_entries": 287,
        "ib_candidates": 47,
        "confidence": "P",
        "note": "Unique Upper Sixth route cohort; no combined grade-entry total is asserted because the report does not print IB Higher-Level entries.",
        "source_ids": ["KCS_OKC_2003"],
    },
    {
        "year": 2004,
        "candidates": 148,
        "alevel_pathway_pupils": 81,
        "alevel_takers": 81,
        "alevel_entries": 260,
        "ib_candidates": 67,
        "confidence": "P",
        "note": "Unique Upper Sixth route cohort; no combined grade-entry total is asserted because the report does not print IB Higher-Level entries.",
        "source_ids": ["KCS_OKC_2004"],
    },
    {
        "year": 2007,
        "candidates": 155,
        "alevel_pathway_pupils": 44,
        "alevel_takers": 44,
        "ib_candidates": 111,
        "confidence": "S",
        "note": "Financial Times table reporting 2007 results; route counts reconcile exactly to the combined candidate total.",
        "source_ids": ["KCS_FT_2007"],
    },
    {
        "year": 2008,
        "ib_candidates_min": 120,
        "confidence": "S",
        "note": "Secondary Drive report states only ‘120+’ IB candidates; retained as a lower bound and never as an exact cohort.",
        "source_ids": ["KCS_LEGACY_COHORT_REPORT"],
    },
    {
        "year": 2009,
        "candidates": 135,
        "alevel_pathway_pupils": 0,
        "alevel_takers": 0,
        "ib_candidates": 135,
        "confidence": "S",
        "note": "Financial Times table; KCS was an all-IB sixth form in this result year.",
        "source_ids": ["KCS_FT_2009"],
    },
]


KCS_HISTORIC_IB_ROWS = [
    {
        "year": 2003,
        "candidates": 47,
        "confidence": "P",
        "note": "Candidate count printed; no IB Higher-Level entry denominator printed, so none is inferred.",
        "source_ids": ["KCS_OKC_2003"],
    },
    {
        "year": 2004,
        "candidates": 67,
        "confidence": "P",
        "note": "Candidate count printed; no IB Higher-Level entry denominator printed, so none is inferred.",
        "source_ids": ["KCS_OKC_2004"],
    },
    {
        "year": 2007,
        "candidates": 111,
        "confidence": "S",
        "source_ids": ["KCS_FT_2007"],
    },
    {
        "year": 2008,
        "ib_candidates_min": 120,
        "confidence": "S",
        "note": "Secondary report states only ‘120+’; encoded as a lower bound.",
        "source_ids": ["KCS_LEGACY_COHORT_REPORT"],
    },
    {
        "year": 2009,
        "candidates": 135,
        "confidence": "S",
        "source_ids": ["KCS_FT_2009"],
    },
    {
        "year": 2011,
        "candidates": 145,
        "entries": 436,
        "confidence": "S",
        "note": "The Financial Times prints 436 Higher-Level entries. This is one above the standard three-per-candidate expectation of 435; the published figure is preserved and flagged, not corrected.",
        "source_ids": ["KCS_FT_2011"],
    },
    {
        "year": 2014,
        "candidates": 190,
        "pupils_at_least_40_points": 116,
        "confidence": "S",
        "note": "Secondary Drive report; underlying primary file not held. Last all-IB year.",
        "source_ids": ["KCS_LEGACY_COHORT_REPORT"],
    },
]


KCS_HISTORIC_GCSE_ROWS = [
    {
        "year": 1990,
        "scale": "A–G",
        "candidates": 266,
        "upper_fifth_candidates": 132,
        "lower_fifth_candidates": 134,
        "entries": 1331,
        "a_count": 633,
        "b_count": 415,
        "c_count": 247,
        "d_count": 36,
        "confidence": "P",
        "note": "Candidate total spans the two separately printed year groups; the component counts remain visible.",
        "source_ids": ["KCS_OKC_1990"],
    },
    {
        "year": 1991,
        "scale": "A–G",
        "candidates": 266,
        "upper_fifth_candidates": 131,
        "lower_fifth_candidates": 135,
        "reported_a_c_entries": 1296,
        "a_count": 666,
        "b_count": 412,
        "c_count": 218,
        "confidence": "P",
        "note": "The source prints A–C counts only. 1,296 is not represented as the total entry denominator, which is not recoverable exactly.",
        "source_ids": ["KCS_OKC_1991"],
    },
    {
        "year": 1995,
        "scale": "A*–G",
        "a_star": 26.6,
        "a_star_count": 396,
        "confidence": "P",
        "note": "Exact A* count and printed share; the total-entry denominator is not printed and is not reverse-engineered from the rounded percentage.",
        "source_ids": ["KCS_OKC_1995"],
    },
    {
        "year": 1996,
        "scale": "A*–G",
        "entries": 1550,
        "confidence": "P",
        "source_ids": ["KCS_OKC_1996"],
    },
    {
        "year": 1997,
        "scale": "A*–G",
        "candidates": 153,
        "entries": 1584,
        "confidence": "P",
        "source_ids": ["KCS_OKC_1997"],
    },
    {
        "year": 2003,
        "scale": "A*–G",
        "candidates": 144,
        "entries": 1353,
        "confidence": "P",
        "source_ids": ["KCS_OKC_2003"],
    },
    {
        "year": 2004,
        "scale": "A*–G",
        "candidates": 141,
        "entries": 1333,
        "confidence": "P",
        "source_ids": ["KCS_OKC_2004"],
    },
]


def _insert_rows(
    javascript: str,
    anchor: str,
    rows: list[dict[str, object]],
    label: str,
) -> str:
    inserted = _compact_json(rows)[1:-1] + ","
    return _replace_once(javascript, anchor, anchor + inserted, label)


def apply_kcs_entry_updates(javascript: str) -> str:
    source_anchor = '"WIN_2026_RESULTS_HUB":'
    source_entries = _compact_json(KCS_ENTRY_SOURCES)[1:-1] + ","
    javascript = _replace_once(
        javascript,
        source_anchor,
        source_entries + source_anchor,
        "KCS entry source catalogue",
    )

    metadata_replacements = (
        (
            "basis:`internal combined A-level + IB-HL equivalent; IB 7→A*, 7–6→A*–A, 7–5→A*–B`,source_refs:[`FB13`,`FB146`],notes:`Missing 2015–16 and 2020–21 combined values are not inferred.`",
            "basis:`school-defined combined A-level + IB-HL equivalent; percentage and entry denominator use A-level subject entries plus IB Higher-Level entries only`,source_refs:[`FB13`,`FB146`,`KCS_ALEVEL_IB_2017_2025_PACK`,`KCS_OKC_2003`,`KCS_OKC_2004`,`KCS_FT_2007`,`KCS_FT_2009`,`KCS_FT_2011`,`KCS_LEGACY_COHORT_REPORT`],notes:`Candidate counts are unique route cohorts; entry counts are A-level entries plus IB Higher-Level entries, not all six IB diploma subjects. Missing grade percentages and denominators are not inferred.`",
            "KCS combined A-level/IB metadata",
        ),
        (
            "basis:`A-level-only component`,source_refs:[`FB13`,`FB146`],notes:null",
            "basis:`A-level-only grade percentages, actual takers and subject entries; pathway pupils are separate where an IB crossover pupil also sat an A level`,source_refs:[`FB13`,`FB146`,`KCS_ALEVEL_IB_2017_2025_PACK`,`KCS_OKC_1990`,`KCS_OKC_1991`,`KCS_OKC_1995`,`KCS_OKC_1996`,`KCS_OKC_1997`,`KCS_OKC_2003`,`KCS_OKC_2004`,`KCS_FT_2007`],notes:`Pre-2010 rows remain on the A–E ruler. The 1991 entry total is explicitly marked derived from the printed contemporary table.`",
            "KCS A-level metadata",
        ),
        (
            "basis:`IB higher-level grade bands and mean points`,source_refs:[`FB13`,`FB146`],notes:null",
            "basis:`IB Higher-Level grade bands, mean Diploma points, candidates and printed Higher-Level entry totals`,source_refs:[`FB13`,`FB146`,`KCS_ALEVEL_IB_2017_2025_PACK`,`KCS_OKC_2003`,`KCS_OKC_2004`,`KCS_FT_2007`,`KCS_FT_2009`,`KCS_FT_2011`,`KCS_LEGACY_COHORT_REPORT`],notes:`Higher-Level entry totals are not treated as all-subject IB diploma entries. Candidate × 3 is never substituted for a missing printed denominator.`",
            "KCS IB metadata",
        ),
        (
            "basis:`all-held annual headline rows; scale/coverage changes explicit`,source_refs:[`FB13`,`FB146`],notes:null",
            "basis:`all-held annual headline rows with candidate and subject-entry denominators where printed; scale, coverage and exclusions explicit`,source_refs:[`FB13`,`FB146`,`KCS_GCSE_2017_2025_PACK`,`KCS_OKC_1990`,`KCS_OKC_1991`,`KCS_OKC_1995`,`KCS_OKC_1996`,`KCS_OKC_1997`,`KCS_OKC_2003`,`KCS_OKC_2004`],notes:`Candidate totals, grade-entry totals, numbered/lettered components and excluded Additional Mathematics entries are distinct fields. Rounded percentages are not inverted to manufacture totals.`",
            "KCS GCSE headline metadata",
        ),
        (
            "basis:`9–1 subject component; 2018–19 coverage incomplete`,source_refs:[`FB13`],notes:null",
            "basis:`9–1 subject component with exact candidate and total-entry context; 2018–19 numbered-grade coverage remains a subset`,source_refs:[`FB13`,`KCS_GCSE_2017_2025_PACK`],notes:`The 2018 and 2019 percentage rows cover the numbered-grade component only, while entries records the full published GCSE/IGCSE denominator.`",
            "KCS detailed GCSE metadata",
        ),
    )
    for before, after, label in metadata_replacements:
        javascript = _replace_once(javascript, before, after, label)

    javascript = _replace_once(
        javascript,
        "basis:`leaver-list places taken up; list-sum denominators`,source_refs:[`FB13`,`FB146`],notes:null,rows:",
        "basis:`leaver-list places taken up; list-sum denominators`,source_refs:[`FB13`,`FB146`],notes:`These are destination-list denominators, not examination candidate cohorts. The one-pupil differences against the 2024 and 2025 sixth-form result cohorts are preserved rather than reconciled away.`,rows:",
        "KCS leaver versus exam cohort warning",
    )

    javascript = _replace_once(
        javascript,
        "candidates:{label:`Candidates`,kind:`count`},pupils_straight_9s:",
        "candidates:{label:`Candidates`,kind:`count`},"
        "alevel_pathway_pupils:{label:`A-level pathway pupils`,kind:`count`},"
        "alevel_takers:{label:`Actual A-level takers`,kind:`count`},"
        "alevel_entries:{label:`A-level entries`,kind:`count`},"
        "ib_candidates:{label:`IB candidates`,kind:`count`},"
        "ib_candidates_min:{label:`IB candidates · lower bound`,kind:`minimum-count`},"
        "ib_hl_entries:{label:`IB Higher-Level entries`,kind:`count`},"
        "numbered_entries:{label:`Numbered-grade entries`,kind:`count`},"
        "lettered_entries:{label:`Letter-grade entries`,kind:`count`},"
        "additional_maths_entries_excluded:{label:`Additional Mathematics entries · excluded`,kind:`count`},"
        "upper_fifth_candidates:{label:`Upper Fifth candidates`,kind:`count`},"
        "lower_fifth_candidates:{label:`Lower Fifth candidates`,kind:`count`},"
        "reported_a_c_entries:{label:`Reported A–C entries · partial`,kind:`count`},"
        "pupils_at_least_40_points:{label:`Pupils scoring ≥40 points`,kind:`count`},"
        "count_confidence:{label:`Count evidence`,kind:`status`},"
        "pupils_straight_9s:",
        "KCS count field labels",
    )
    javascript = _replace_once(
        javascript,
        "`entry_count`,`candidates`,`cohort`",
        "`entry_count`,`candidates`,`alevel_pathway_pupils`,`alevel_takers`,`alevel_entries`,`ib_candidates`,`ib_candidates_min`,`ib_hl_entries`,`numbered_entries`,`lettered_entries`,`additional_maths_entries_excluded`,`upper_fifth_candidates`,`lower_fifth_candidates`,`reported_a_c_entries`,`pupils_at_least_40_points`,`cohort`",
        "KCS count field ordering",
    )
    javascript = _replace_once(
        javascript,
        "new Set([`year`,`period`,`entries`,`entries_9_1`,`entry_count`,`candidates`,`mean_points`,`published_pass_rate`])",
        "new Set([`year`,`period`,`entries`,`entries_9_1`,`entry_count`,`candidates`,`alevel_pathway_pupils`,`alevel_takers`,`alevel_entries`,`ib_candidates`,`ib_candidates_min`,`ib_hl_entries`,`numbered_entries`,`lettered_entries`,`additional_maths_entries_excluded`,`upper_fifth_candidates`,`lower_fifth_candidates`,`reported_a_c_entries`,`pupils_at_least_40_points`,`mean_points`,`published_pass_rate`])",
        "KCS visible result count fields",
    )

    javascript = _replace_once(
        javascript,
        "e===`kcs_gcse_headline`?/A\\*/.test(i)?",
        "e===`kcs_gcse_headline`?r<1994?o=`gcse-pre-a-star`:/A\\*/.test(i)?",
        "KCS pre-A-star GCSE ruler",
    )

    javascript = _insert_rows(
        javascript,
        "notes:`Pre-2010 rows remain on the A–E ruler. The 1991 entry total is explicitly marked derived from the printed contemporary table.`,rows:[",
        KCS_HISTORIC_ALEVEL_ROWS,
        "KCS historic A-level count rows",
    )
    javascript = _insert_rows(
        javascript,
        "notes:`Candidate counts are unique route cohorts; entry counts are A-level entries plus IB Higher-Level entries, not all six IB diploma subjects. Missing grade percentages and denominators are not inferred.`,rows:[",
        KCS_HISTORIC_COMBINED_ROWS,
        "KCS historic combined sixth-form count rows",
    )
    javascript = _insert_rows(
        javascript,
        "notes:`Higher-Level entry totals are not treated as all-subject IB diploma entries. Candidate × 3 is never substituted for a missing printed denominator.`,rows:[",
        KCS_HISTORIC_IB_ROWS,
        "KCS historic IB count rows",
    )
    javascript = _insert_rows(
        javascript,
        "notes:`Candidate totals, grade-entry totals, numbered/lettered components and excluded Additional Mathematics entries are distinct fields. Rounded percentages are not inverted to manufacture totals.`,rows:[",
        KCS_HISTORIC_GCSE_ROWS,
        "KCS historic GCSE count rows",
    )

    row_replacements = (
        (
            "{year:2011,a_star_or_7:40.1,astar_a_or_7_6:81.2,astar_b_or_7_5:95.6,confidence:`P`}",
            "{year:2011,candidates:145,alevel_pathway_pupils:0,alevel_takers:0,ib_candidates:145,ib_hl_entries:436,entries:436,a_star_or_7:40.1,astar_a_or_7_6:81.2,astar_b_or_7_5:95.6,count_confidence:`S`,confidence:`P`,note:`Financial Times candidate and Higher-Level entry counts. The printed 436 is one above 145 × 3 and is preserved with a warning.`,source_ids:[`FB13`,`KCS_FT_2011`]}",
            "KCS 2011 combined count context",
        ),
        (
            "{year:2014,a_star_or_7:52.5,astar_a_or_7_6:87,astar_b_or_7_5:95.7,confidence:`P`}",
            "{year:2014,candidates:190,alevel_pathway_pupils:0,alevel_takers:0,ib_candidates:190,a_star_or_7:52.5,astar_a_or_7_6:87,astar_b_or_7_5:95.7,count_confidence:`S`,confidence:`P`,note:`Secondary cohort report; this was the last all-IB year. Grade bands remain from the primary consolidated series.`,source_ids:[`FB13`,`KCS_LEGACY_COHORT_REPORT`]}",
            "KCS 2014 combined count context",
        ),
        (
            "{year:2017,a_star_or_7:51.6,astar_a_or_7_6:88.3,astar_b_or_7_5:97.8,confidence:`P`}",
            "{year:2017,a_star_or_7:51.6,astar_a_or_7_6:88.3,astar_b_or_7_5:97.8,ib_candidates:55,count_confidence:`S`,confidence:`P`,note:`The 55-pupil IB count appears only in a secondary Drive report; no combined cohort denominator is inferred.`,source_ids:[`FB13`,`KCS_LEGACY_COHORT_REPORT`]}",
            "KCS 2017 combined count context",
        ),
        (
            "{year:2018,a_star_or_7:51.5,astar_a_or_7_6:84.6,astar_b_or_7_5:96.8,confidence:`P`}",
            "{year:2018,candidates:193,alevel_pathway_pupils:114,alevel_takers:114,alevel_entries:379,ib_candidates:79,ib_hl_entries:239,entries:618,a_star_or_7:51.5,astar_a_or_7_6:84.6,astar_b_or_7_5:96.8,confidence:`P`,source_ids:[`KCS_ALEVEL_IB_2017_2025_PACK`]}",
            "KCS 2018 combined denominators",
        ),
        (
            "{year:2019,a_star_or_7:49.9,astar_a_or_7_6:84.6,astar_b_or_7_5:96.1,confidence:`P`}",
            "{year:2019,candidates:206,alevel_pathway_pupils:131,alevel_takers:131,alevel_entries:447,ib_candidates:75,ib_hl_entries:227,entries:674,a_star_or_7:49.9,astar_a_or_7_6:84.6,astar_b_or_7_5:96.1,confidence:`P`,source_ids:[`KCS_ALEVEL_IB_2017_2025_PACK`]}",
            "KCS 2019 combined denominators",
        ),
        (
            "{year:2022,a_star_or_7:69.3,astar_a_or_7_6:95.6,astar_b_or_7_5:99.3,confidence:`P`}",
            "{year:2022,candidates:204,alevel_pathway_pupils:137,alevel_takers:137,alevel_entries:496,ib_candidates:67,ib_hl_entries:201,entries:697,a_star_or_7:69.3,astar_a_or_7_6:95.6,astar_b_or_7_5:99.3,count_confidence:`P/D`,confidence:`P`,note:`The unique 204-pupil cohort is the exact sum of the two printed route counts; the combined line does not separately print it.`,source_ids:[`KCS_ALEVEL_IB_2017_2025_PACK`]}",
            "KCS 2022 combined denominators",
        ),
        (
            "{year:2023,a_star_or_7:53.06,astar_a_or_7_6:84.49,astar_b_or_7_5:94.83,confidence:`P`}",
            "{year:2023,candidates:212,alevel_pathway_pupils:159,alevel_takers:159,alevel_entries:575,ib_candidates:53,ib_hl_entries:160,entries:735,a_star_or_7:53.06,astar_a_or_7_6:84.49,astar_b_or_7_5:94.83,confidence:`P`,source_ids:[`KCS_ALEVEL_IB_2017_2025_PACK`]}",
            "KCS 2023 combined denominators",
        ),
        (
            "{year:2024,a_star_or_7:53.11,astar_a_or_7_6:87.28,astar_b_or_7_5:97.35,confidence:`P`}",
            "{year:2024,candidates:216,alevel_pathway_pupils:161,alevel_takers:162,alevel_entries:590,ib_candidates:55,ib_hl_entries:165,entries:755,a_star_or_7:53.11,astar_a_or_7_6:87.28,astar_b_or_7_5:97.35,confidence:`P`,note:`One IB-route pupil also sat one A level. The pupil is included once in the 216-pupil cohort but is included among the 162 actual A-level takers.`,source_ids:[`KCS_ALEVEL_IB_2017_2025_PACK`]}",
            "KCS 2024 combined denominators",
        ),
        (
            "{year:2025,a_star_or_7:54.42,astar_a_or_7_6:88.2,astar_b_or_7_5:96.2,confidence:`P`}",
            "{year:2025,candidates:235,alevel_pathway_pupils:182,alevel_takers:183,alevel_entries:666,ib_candidates:53,ib_hl_entries:159,entries:825,a_star_or_7:54.42,astar_a_or_7_6:88.2,astar_b_or_7_5:96.2,confidence:`P`,note:`One IB-route pupil also sat one A level. The pupil is included once in the 235-pupil cohort but is included among the 183 actual A-level takers.`,source_ids:[`KCS_ALEVEL_IB_2017_2025_PACK`]}",
            "KCS 2025 combined denominators",
        ),
        (
            "{year:2018,a_star:45.6,a_star_a:78.6,a_star_b:95,confidence:`P`}",
            "{year:2018,candidates:114,entries:379,a_star:45.6,a_star_a:78.6,a_star_b:95,confidence:`P`,source_ids:[`KCS_ALEVEL_IB_2017_2025_PACK`]}",
            "KCS 2018 A-level denominators",
        ),
        (
            "{year:2019,a_star:46.5,a_star_a:79.9,a_star_b:94.9,confidence:`P`}",
            "{year:2019,candidates:131,entries:447,a_star:46.5,a_star_a:79.9,a_star_b:94.9,confidence:`P`,source_ids:[`KCS_ALEVEL_IB_2017_2025_PACK`]}",
            "KCS 2019 A-level denominators",
        ),
        (
            "{year:2022,a_star:68.1,a_star_a:94.2,a_star_b:99.2,confidence:`P`}",
            "{year:2022,candidates:137,entries:496,a_star:68.1,a_star_a:94.2,a_star_b:99.2,confidence:`P`,source_ids:[`KCS_ALEVEL_IB_2017_2025_PACK`]}",
            "KCS 2022 A-level denominators",
        ),
        (
            "{year:2023,a_star:50.3,a_star_a:82.8,a_star_b:93.6,confidence:`P`}",
            "{year:2023,candidates:159,entries:575,a_star:50.3,a_star_a:82.8,a_star_b:93.6,confidence:`P`,source_ids:[`KCS_ALEVEL_IB_2017_2025_PACK`]}",
            "KCS 2023 A-level denominators",
        ),
        (
            "{year:2024,a_star:50.7,a_star_a:86.6,a_star_b:96.9,confidence:`P`}",
            "{year:2024,candidates:162,alevel_pathway_pupils:161,entries:590,a_star:50.7,a_star_a:86.6,a_star_b:96.9,confidence:`P`,note:`161 pupils followed the A-level pathway; one IB-route pupil also sat an A level, giving 162 actual takers.`,source_ids:[`KCS_ALEVEL_IB_2017_2025_PACK`]}",
            "KCS 2024 A-level denominators",
        ),
        (
            "{year:2025,a_star:50.75,a_star_a:86.04,a_star_b:95.3,confidence:`P`}",
            "{year:2025,candidates:183,alevel_pathway_pupils:182,entries:666,a_star:50.75,a_star_a:86.04,a_star_b:95.3,confidence:`P`,note:`182 pupils followed the A-level pathway; one IB-route pupil also sat an A level, giving 183 actual takers.`,source_ids:[`KCS_ALEVEL_IB_2017_2025_PACK`]}",
            "KCS 2025 A-level denominators",
        ),
        (
            "{year:2017,grade_7:67.3,grade_7_6:95.2,grade_7_5:99.4,mean_points:42.1,confidence:`P`}",
            "{year:2017,candidates:55,grade_7:67.3,grade_7_6:95.2,grade_7_5:99.4,mean_points:42.1,count_confidence:`S`,confidence:`P`,note:`The 55-pupil candidate count is secondary; the grade bands remain primary.`,source_ids:[`FB13`,`KCS_LEGACY_COHORT_REPORT`]}",
            "KCS 2017 IB candidate count",
        ),
        (
            "{year:2018,grade_7:60.7,grade_7_6:94.1,grade_7_5:99.6,mean_points:41.2,confidence:`P`}",
            "{year:2018,candidates:79,entries:239,grade_7:60.7,grade_7_6:94.1,grade_7_5:99.6,mean_points:41.2,confidence:`P`,source_ids:[`KCS_ALEVEL_IB_2017_2025_PACK`]}",
            "KCS 2018 IB denominators",
        ),
        (
            "{year:2019,grade_7:56.4,grade_7_6:93.8,grade_7_5:98.7,mean_points:40.8,confidence:`P`}",
            "{year:2019,candidates:75,entries:227,grade_7:56.4,grade_7_6:93.8,grade_7_5:98.7,mean_points:40.8,confidence:`P`,source_ids:[`KCS_ALEVEL_IB_2017_2025_PACK`]}",
            "KCS 2019 IB denominators",
        ),
        (
            "{year:2022,grade_7:72.1,grade_7_6:99,grade_7_5:99.5,mean_points:42.1,confidence:`P`}",
            "{year:2022,candidates:67,entries:201,grade_7:72.1,grade_7_6:99,grade_7_5:99.5,mean_points:42.1,confidence:`P`,source_ids:[`KCS_ALEVEL_IB_2017_2025_PACK`]}",
            "KCS 2022 IB denominators",
        ),
        (
            "{year:2023,grade_7:63.75,grade_7_6:90.63,grade_7_5:99.38,mean_points:41.1,confidence:`P`}",
            "{year:2023,candidates:53,entries:160,grade_7:63.75,grade_7_6:90.63,grade_7_5:99.38,mean_points:41.1,confidence:`P`,source_ids:[`KCS_ALEVEL_IB_2017_2025_PACK`]}",
            "KCS 2023 IB denominators",
        ),
        (
            "{year:2024,grade_7:61.8,grade_7_6:89.7,grade_7_5:98.8,mean_points:41.3,confidence:`P`}",
            "{year:2024,candidates:55,entries:165,grade_7:61.8,grade_7_6:89.7,grade_7_5:98.8,mean_points:41.3,confidence:`P`,source_ids:[`KCS_ALEVEL_IB_2017_2025_PACK`]}",
            "KCS 2024 IB denominators",
        ),
        (
            "{year:2025,grade_7:69.8,grade_7_6:97.5,grade_7_5:100,mean_points:42.2,confidence:`P`}",
            "{year:2025,candidates:53,entries:159,grade_7:69.8,grade_7_6:97.5,grade_7_5:100,mean_points:42.2,confidence:`P`,source_ids:[`KCS_ALEVEL_IB_2017_2025_PACK`]}",
            "KCS 2025 IB denominators",
        ),
        (
            "{year:2017,scale:`transition`,top:83.4,top_2:96.8,top_3:null,confidence:`S/P`,note:null}",
            "{year:2017,scale:`transition`,candidates:159,top:83.4,top_2:96.8,top_3:null,confidence:`S/P`,note:`The Times/chronological source prints 159 students. The exact entry total is not printed; the rounded 10.46 entries-per-pupil average is not inverted into a total.`,source_ids:[`FB13`,`KCS_GCSE_2017_2025_PACK`]}",
            "KCS 2017 GCSE candidate count",
        ),
        (
            "{year:2018,scale:`transition`,top:null,top_2:81.7,top_3:96.4,confidence:`S/P`,note:`81.7 is all-course combined top band; separate 9–1-only row is 58.9/86.1/95.9`}",
            "{year:2018,scale:`transition`,candidates:147,entries:1555,numbered_entries:467,lettered_entries:1088,additional_maths_entries_excluded:88,top:null,top_2:81.7,top_3:96.4,confidence:`P`,note:`The 1,555-entry total excludes 88 Additional Mathematics entries. The combined headline band and separate 467-entry numbered subset use different rulers.`,source_ids:[`KCS_GCSE_2017_2025_PACK`]}",
            "KCS 2018 GCSE denominators",
        ),
        (
            "{year:2019,scale:`9-1`,top:57.1,top_2:82.8,top_3:96.3,confidence:`S/P`,note:`v13 detailed row instead prints 57.1/82.9/96.0; retain as source-version conflict`}",
            "{year:2019,scale:`9-1`,candidates:153,entries:1698,numbered_entries:1438,lettered_entries:260,top:57.1,top_2:82.8,top_3:96.3,confidence:`P`,note:`The detailed v13 row prints 57.1/82.9/96.0 while the headline row prints 57.1/82.8/96.3; the conflict remains visible.`,source_ids:[`KCS_GCSE_2017_2025_PACK`]}",
            "KCS 2019 GCSE denominators",
        ),
        (
            "{year:2022,scale:`9-1`,top:73,top_2:90.9,top_3:97.7,confidence:`S/P`,note:null}",
            "{year:2022,scale:`9-1`,candidates:163,entries:1785,top:73,top_2:90.9,top_3:97.7,confidence:`P`,source_ids:[`KCS_GCSE_2017_2025_PACK`]}",
            "KCS 2022 GCSE denominators",
        ),
        (
            "{year:2023,scale:`9-1`,top:67.2,top_2:89.8,top_3:98.1,confidence:`S/P`,note:null}",
            "{year:2023,scale:`9-1`,candidates:155,entries:1706,top:67.2,top_2:89.8,top_3:98.1,confidence:`P`,source_ids:[`KCS_GCSE_2017_2025_PACK`]}",
            "KCS 2023 GCSE denominators",
        ),
        (
            "{year:2024,scale:`9-1`,top:68.8,top_2:92.1,top_3:98.6,confidence:`S/P`,note:null}",
            "{year:2024,scale:`9-1`,candidates:169,entries:1841,top:68.8,top_2:92.1,top_3:98.6,confidence:`P`,note:`The source also prints 10.9 entries per candidate.`,source_ids:[`KCS_GCSE_2017_2025_PACK`]}",
            "KCS 2024 GCSE denominators",
        ),
        (
            "{year:2025,scale:`9-1`,top:70.4,top_2:91.5,top_3:98.2,confidence:`S/P`,note:null}",
            "{year:2025,scale:`9-1`,candidates:156,entries:1687,top:70.4,top_2:91.5,top_3:98.2,confidence:`P`,note:`The source also prints 10.8 entries per candidate.`,source_ids:[`KCS_GCSE_2017_2025_PACK`]}",
            "KCS 2025 GCSE denominators",
        ),
        (
            "{year:2018,grade_9:58.9,grade_9_8:86.1,grade_9_7:95.9,coverage:`467/1,555 entries (30.0%)`,confidence:`P/S`}",
            "{year:2018,candidates:147,entries:1555,numbered_entries:467,lettered_entries:1088,additional_maths_entries_excluded:88,grade_9:58.9,grade_9_8:86.1,grade_9_7:95.9,coverage:`467/1,555 entries (30.0%)`,confidence:`P`,note:`Percentages cover the 467 numbered-grade entries; the full 1,555 denominator excludes 88 Additional Mathematics entries.`,source_ids:[`KCS_GCSE_2017_2025_PACK`]}",
            "KCS detailed 2018 GCSE denominators",
        ),
        (
            "{year:2019,grade_9:57.1,grade_9_8:82.9,grade_9_7:96,coverage:`1,438/1,698 entries (84.7%)`,confidence:`P/S`}",
            "{year:2019,candidates:153,entries:1698,numbered_entries:1438,lettered_entries:260,grade_9:57.1,grade_9_8:82.9,grade_9_7:96,coverage:`1,438/1,698 entries (84.7%)`,confidence:`P`,note:`Percentages cover the 1,438 numbered-grade entries; 260 letter-grade entries complete the full denominator.`,source_ids:[`KCS_GCSE_2017_2025_PACK`]}",
            "KCS detailed 2019 GCSE denominators",
        ),
        (
            "{year:2022,grade_9:73,grade_9_8:90.9,grade_9_7:97.7,coverage:`all-numbered`,confidence:`P/S`}",
            "{year:2022,candidates:163,entries:1785,numbered_entries:1785,grade_9:73,grade_9_8:90.9,grade_9_7:97.7,coverage:`all-numbered`,confidence:`P`,source_ids:[`KCS_GCSE_2017_2025_PACK`]}",
            "KCS detailed 2022 GCSE denominators",
        ),
        (
            "{year:2023,grade_9:67.2,grade_9_8:89.8,grade_9_7:98.1,coverage:`all-numbered`,confidence:`P/S`}",
            "{year:2023,candidates:155,entries:1706,numbered_entries:1706,grade_9:67.2,grade_9_8:89.8,grade_9_7:98.1,coverage:`all-numbered`,confidence:`P`,source_ids:[`KCS_GCSE_2017_2025_PACK`]}",
            "KCS detailed 2023 GCSE denominators",
        ),
        (
            "{year:2024,grade_9:68.77,grade_9_8:92.1,grade_9_7:98.6,coverage:`all-numbered`,confidence:`P/S`}",
            "{year:2024,candidates:169,entries:1841,numbered_entries:1841,grade_9:68.77,grade_9_8:92.1,grade_9_7:98.6,coverage:`all-numbered`,confidence:`P`,source_ids:[`KCS_GCSE_2017_2025_PACK`]}",
            "KCS detailed 2024 GCSE denominators",
        ),
        (
            "{year:2025,grade_9:70.36,grade_9_8:91.5,grade_9_7:98.2,coverage:`all-numbered`,confidence:`P/S`}",
            "{year:2025,candidates:156,entries:1687,numbered_entries:1687,grade_9:70.36,grade_9_8:91.5,grade_9_7:98.2,coverage:`all-numbered`,confidence:`P`,source_ids:[`KCS_GCSE_2017_2025_PACK`]}",
            "KCS detailed 2025 GCSE denominators",
        ),
    )
    for before, after, label in row_replacements:
        javascript = _replace_once(javascript, before, after, label)

    javascript = _replace_once(
        javascript,
        "{year:2010,a_star_or_7:42.5",
        "{year:2016,candidates:195,confidence:`S`,note:`Telegraph combined-equivalent candidate count; route split and entry total not held.`,source_ids:[`KCS_LEGACY_COHORT_REPORT`]},{year:2010,a_star_or_7:42.5",
        "KCS 2016 combined count row",
    )

    c26 = {
        "id": "C26",
        "school": "Winchester College",
        "metric": "GCSE/IGCSE subject-entry denominators",
        "period": "2017–2021",
        "old": "2017, 2018 and 2021 blank; 2020 approximately 1,178",
        "new": "2017 1,359; 2018 1,283; 2020 1,189; 2021 1,258",
        "status": "primary_denominator_reconciliation",
        "source_refs": [
            "FB146",
            "WIN_ACCOUNTS_2018",
            "WIN_GCSE_2020_PDF",
            "WIN_GCSE_2021_PDF",
        ],
        "reason": "Official annual evidence supplies the missing exact denominators. The final 2020 subject table supersedes the earlier approximate OCR, and separately reported Additional Mathematics entries are not added.",
    }
    c26_json = _compact_json(c26)
    additions = ",".join(_compact_json(item) for item in KCS_ENTRY_CORRECTIONS)
    javascript = _replace_once(
        javascript,
        c26_json,
        c26_json + "," + additions,
        "KCS entry correction ledger",
    )
    return javascript
