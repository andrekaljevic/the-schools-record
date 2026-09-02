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


WINCHESTER_GCSE_ENTRY_SOURCES = {
    "WIN_GCSE_2020_PDF": {
        "id": "winchester-gcse-2020-official-pdf",
        "title": "Winchester College · GCSE Results Summer 2020 · final",
        "url": "https://www.winchestercollege.org/assets/files/uploads/GCSE%20Results%20Summer%202020_FINAL.pdf",
        "role": "official complete subject table; 1,189 GCSE/IGCSE entries, with 58 Additional Mathematics entries reported separately",
    },
    "WIN_GCSE_2021_PDF": {
        "id": "winchester-gcse-2021-official-pdf",
        "title": "Winchester College · IGCSE and GCSE results 2021 · official",
        "url": "https://web.archive.org/web/20211023173550id_/https://www.winchestercollege.org/assets/files/uploads/igcse-and-gcse-results-2021-official.pdf",
        "role": "official complete subject table; 1,258 GCSE/IGCSE entries, with 59 Additional Mathematics entries reported separately",
    },
}


WINCHESTER_GCSE_ENTRY_CORRECTION = {
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


_WINCHESTER_C25 = {
    "id": "C25",
    "school": "Winchester College",
    "metric": "2026 Oxbridge offers",
    "period": 2026,
    "old": "not represented",
    "new": "38 initial offers reported to date",
    "status": "provisional_current_year_addition",
    "source_refs": ["WIN_OXBRIDGE_2026_INITIAL"],
    "reason": "The March 2026 first-party newsletter supplies a current annual count, explicitly labelled initial and provisional rather than a final destination outcome.",
}


def apply_winchester_gcse_entry_updates(javascript: str) -> str:
    source_anchor = '"WIN_2026_RESULTS_HUB":'
    source_entries = _compact_json(WINCHESTER_GCSE_ENTRY_SOURCES)[1:-1] + ","
    javascript = _replace_once(
        javascript,
        source_anchor,
        source_entries + source_anchor,
        "Winchester GCSE entry source catalogue",
    )

    javascript = _replace_once(
        javascript,
        "source_refs:[`FB139`,`FB139A`,`FB141`,`FB146`,`WIN_GCSE_HMC_1997`,`WIN_GCSE_2006_ISC`,`WIN_GCSE_2011_DFE_GCSE`,`WIN_GCSE_2011_DFE_IGCSE`,`WIN_GCSE_2012_DFE`]",
        "source_refs:[`FB139`,`FB139A`,`FB141`,`FB146`,`WIN_GCSE_HMC_1997`,`WIN_GCSE_2006_ISC`,`WIN_GCSE_2011_DFE_GCSE`,`WIN_GCSE_2011_DFE_IGCSE`,`WIN_GCSE_2012_DFE`,`WIN_ACCOUNTS_2018`,`WIN_GCSE_2020_PDF`,`WIN_GCSE_2021_PDF`]",
        "Winchester GCSE denominator metadata sources",
    )

    replacements = (
        (
            "{year:2017,scale:`transition`,entries:null,grade_9:null,top_equivalent:62.5,astar_a_equivalent:90.5,astar_b_or_9_6:98.5,confidence:`P/S`,note:`bands are 9–8/9–7/9–6`}",
            "{year:2017,scale:`transition`,entries:1359,grade_9:null,top_equivalent:62.5,astar_a_equivalent:90.5,astar_b_or_9_6:98.5,confidence:`P`,note:`Official annual-account denominator; bands are 9–8/9–7/9–6.`,source_ids:[`FB146`]}",
        ),
        (
            "{year:2018,scale:`9-1/IGCSE`,entries:null,grade_9:null,top_equivalent:68.4,astar_a_equivalent:92.1,astar_b_or_9_6:98.9,confidence:`P`,note:`image 9–7=91.1 conflicts with official 92.1`}",
            "{year:2018,scale:`9-1/IGCSE`,entries:1283,grade_9:null,top_equivalent:68.4,astar_a_equivalent:92.1,astar_b_or_9_6:98.9,confidence:`P`,note:`Official signed accounts supply 1,283 entries; image 9–7=91.1 conflicts with the official 92.1 headline.`,source_ids:[`WIN_ACCOUNTS_2018`]}",
        ),
        (
            "{year:2020,scale:`9-1 CAG`,entries:1178,grade_9:48,top_equivalent:null,astar_a_equivalent:93.1,astar_b_or_9_6:null,confidence:`S/R`,note:`pandemic CAG; quarantined`}",
            "{year:2020,scale:`9-1 CAG`,entries:1189,grade_9:48,top_equivalent:null,astar_a_equivalent:93.1,astar_b_or_9_6:null,confidence:`P`,note:`Pandemic CAG; quarantined. Official final subject table totals 1,189 GCSE/IGCSE entries; 58 Additional Mathematics entries are separate and excluded.`,source_ids:[`WIN_GCSE_2020_PDF`]}",
        ),
        (
            "{year:2021,scale:`9-1 TAG`,entries:null,grade_9:63,top_equivalent:84.7,astar_a_equivalent:94.7,astar_b_or_9_6:null,confidence:`S`,note:`pandemic TAG; quarantined`}",
            "{year:2021,scale:`9-1 TAG`,entries:1258,grade_9:63,top_equivalent:84.7,astar_a_equivalent:94.7,astar_b_or_9_6:null,confidence:`P`,note:`Pandemic TAG; quarantined. Official subject table totals 1,258 GCSE/IGCSE entries; 59 Additional Mathematics entries are separate and excluded.`,source_ids:[`WIN_GCSE_2021_PDF`]}",
        ),
    )
    for before, after in replacements:
        year = after.split("year:", 1)[1].split(",", 1)[0]
        javascript = _replace_once(
            javascript,
            before,
            after,
            f"Winchester {year} GCSE entry denominator",
        )

    c25 = _compact_json(_WINCHESTER_C25)
    javascript = _replace_once(
        javascript,
        c25,
        c25 + "," + _compact_json(WINCHESTER_GCSE_ENTRY_CORRECTION),
        "Winchester GCSE entry correction ledger",
    )
    return javascript
