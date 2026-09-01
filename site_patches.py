from __future__ import annotations

import json


def _compact_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _replace_once(source: str, before: str, after: str, label: str) -> str:
    matches = source.count(before)
    if matches != 1:
        raise RuntimeError(f"Unable to apply {label}: expected one bundle match, found {matches}")
    return source.replace(before, after, 1)


ST_PAULS_SOURCES = {
    "SPS_DFE_HISTORIC": {
        "id": "st-pauls-dfe-historic-results",
        "title": "DfE · historical school-performance downloads",
        "url": "https://www.compare-school-performance.service.gov.uk/download-data",
        "role": "official historical pupil-threshold and points measures; not interchangeable with grade-entry shares",
    },
    "SPS_GCSE_GUARDIAN_2000": {
        "id": "st-pauls-gcse-2000-guardian",
        "title": "The Guardian · independent-school GCSE table 2000",
        "url": "https://www.theguardian.com/education/performance2000/table/0,,398221,00.html",
        "role": "contemporary official-data table carrying rank, five-grade threshold and old-tariff points",
    },
    "SPS_GCSE_GUARDIAN_2001": {
        "id": "st-pauls-gcse-2001-guardian",
        "title": "The Guardian · Richmond secondary-school table 2001",
        "url": "https://www.theguardian.com/education/secondaryschooltable/0,,-4306076,00.html?index=12&view=1",
        "role": "contemporary official-data table carrying cohort and pupil-threshold measures",
    },
    "SPS_GCSE_GUARDIAN_2002": {
        "id": "st-pauls-gcse-2002-guardian",
        "title": "The Guardian · St Paul’s tops the 2002 GCSE table",
        "url": "https://www.theguardian.com/education/2002/aug/30/schools.gcses2002",
        "role": "contemporary ISC-table report carrying candidate count and old-tariff points",
    },
    "SPS_GCSE_GUARDIAN_2003": {
        "id": "st-pauls-gcse-2003-guardian",
        "title": "The Guardian · independent-school GCSE report 2003",
        "url": "https://www.theguardian.com/education/2003/aug/29/schools.publicschools",
        "role": "contemporary rank report; no exact St Paul’s grade distribution recovered",
    },
    "SPS_GCSE_GUARDIAN_2004": {
        "id": "st-pauls-gcse-2004-guardian",
        "title": "The Guardian · independent-school GCSE report 2004",
        "url": "https://www.theguardian.com/education/2004/sep/03/schools.publicschools",
        "role": "contemporary ISC-table report carrying rank, cohort and old-tariff points",
    },
    "SPS_GCSE_GUARDIAN_2005": {
        "id": "st-pauls-gcse-2005-guardian",
        "title": "The Guardian · ISC GCSE table 2005",
        "url": "https://www.theguardian.com/education/gcses/table/0,16426,1561652,00.html",
        "role": "contemporary table cross-check for rank, cohort and old-tariff points",
    },
    "SPS_2002_EXAM_CC": {
        "id": "st-pauls-2002-exam-results-common-crawl",
        "title": "St Paul’s School · 2002 examination results · Common Crawl recovery",
        "url": "https://index.commoncrawl.org/CC-MAIN-2009-2010-index?url=www.stpaulsschool.org.uk/st-pauls/academic/archive/2002-exam-results&output=json",
        "role": "first-party page recovered at ARC offset 69,280,402; supplies 92.5% GCSE A*/A and 92.5% A-level A/B school headlines",
    },
    "SPS_GCSE_2005_2009_WAYBACK": {
        "id": "st-pauls-gcse-2005-2009-wayback",
        "title": "St Paul’s School · GCSE summary 2005–09 · Wayback",
        "url": "https://web.archive.org/web/20100905081802id_/http://www.stpaulsschool.org.uk/academic/exam-results/gcse-summary-last-five-years",
        "role": "direct school five-year final grid; A*, A*–A and A*–B grade-entry shares",
    },
    "SPS_ALEVEL_1992_TIMES_IA": {
        "id": "st-pauls-alevel-1992-times",
        "title": "The Times · independent-school A-level table · 29 August 1992",
        "url": "https://archive.org/stream/NewsUK1992UKEnglish/Aug%2029%201992%2C%20The%20Times%2C%20%2364424%2C%20UK%20%28en%29_djvu.txt",
        "role": "contemporary rank, cohort and old UCCA-points evidence",
    },
    "SPS_ALEVEL_1993_FT_IA": {
        "id": "st-pauls-alevel-1993-ft",
        "title": "Financial Times · independent-school A-level table · 28 August 1993",
        "url": "https://archive.org/stream/FinancialTimes1993UKEnglish/Aug%2028%201993%2C%20Financial%20Times%2C%20%23729%2C%20UK%20%28en%29_djvu.txt",
        "role": "contemporary rank and old UCCA-points evidence",
    },
    "SPS_ALEVEL_1994_TIMES_IA": {
        "id": "st-pauls-alevel-1994-times",
        "title": "The Times · independent-school A-level table · 27 August 1994",
        "url": "https://archive.org/stream/NewsUK1994UKEnglish/Aug%2027%201994%2C%20The%20Times%2C%20%2365044%2C%20UK%20%28en%29_djvu.txt",
        "role": "contemporary rank, cohort and old UCCA-points evidence",
    },
    "SPS_ALEVEL_1996_TIMES_IA": {
        "id": "st-pauls-alevel-1996-times",
        "title": "The Times · independent-school A-level table · 23 August 1996",
        "url": "https://archive.org/stream/NewsUK1996UKEnglish/Aug%2023%201996%2C%20The%20Times%2C%20%2365666%2C%20UK%20%28en%29_djvu.txt",
        "role": "contemporary rank, cohort and university-entrance-points evidence",
    },
    "SPS_ALEVEL_1997_FT_IA": {
        "id": "st-pauls-alevel-1997-ft",
        "title": "Financial Times · independent-school A-level table · 30 August 1997",
        "url": "https://archive.org/stream/FinancialTimes1997UKEnglish/Aug%2030%201997%2C%20Financial%20Times%2C%20%2333030%2C%20UK%20%28en%29_djvu.txt",
        "role": "contemporary rank and old points measures; General Studies excluded",
    },
    "SPS_ALEVEL_1998_FT_IA": {
        "id": "st-pauls-alevel-1998-ft",
        "title": "Financial Times · independent-school A-level table · 29 August 1998",
        "url": "https://archive.org/stream/FinancialTimes1998UKEnglish/Aug%2029%201998%2C%20Financial%20Times%2C%20%2329%2C%20UK%20%28en%29_djvu.txt",
        "role": "contemporary rank and old points measures; General Studies excluded",
    },
    "SPS_ALEVEL_1999_INDEPENDENT": {
        "id": "st-pauls-alevel-1999-independent",
        "title": "The Independent · independent-school A-level table 1999",
        "url": "https://www.independent.co.uk/news/education/education-news/secondary-school-league-tables-top-independent-schools-at-alevel-1128432.html",
        "role": "contemporary old-scale points evidence",
    },
    "SPS_ALEVEL_2000_TES": {
        "id": "st-pauls-alevel-2000-tes",
        "title": "TES · independent-school A-level analysis 2000",
        "url": "https://www.tes.com/magazine/archive/independents-widen-top-level-grade-lead?amp=",
        "role": "contemporary per-pupil and per-entry old-scale rankings",
    },
    "SPS_ALEVEL_2002_GUARDIAN": {
        "id": "st-pauls-alevel-2002-guardian",
        "title": "The Guardian · independent-school A-level table 2002",
        "url": "https://www.theguardian.com/education/alevels2002/table/0,12321,779730,00.html",
        "role": "contemporary league-table rank and score cross-check",
    },
    "SPS_ALEVEL_2004_GUARDIAN": {
        "id": "st-pauls-alevel-2004-guardian",
        "title": "The Guardian · independent-school A-level table 2004",
        "url": "https://www.theguardian.com/education/2004/aug/27/alevels2004.alevels",
        "role": "contemporary rank, cohort and UCAS/QCA points evidence",
    },
    "SPS_ALEVEL_2005_INDEPENDENT": {
        "id": "st-pauls-alevel-2005-independent",
        "title": "The Independent · independent-school A-level table 2005",
        "url": "https://www.independent.co.uk/news/education/education-news/secondary-school-league-tables-the-top-50-independent-schools-at-alevel-6111232.html",
        "role": "contemporary points-table cross-check",
    },
    "SPS_ALEVEL_2006_ISC": {
        "id": "st-pauls-alevel-2006-isc",
        "title": "ISC · Year 13 boys examination workbook 2006",
        "url": "https://www.isc.co.uk/media/2474/2006_examresults_year13_boys_isc.xls",
        "role": "raw ISC counts retained as a competing population against the school’s five-year headline",
    },
    "SPS_ALEVEL_2007_ISC": {
        "id": "st-pauls-alevel-2007-isc",
        "title": "ISC · Year 13 boys examination workbook 2007",
        "url": "https://www.isc.co.uk/media/2475/2007_examresults_year13_boys_isc.xls",
        "role": "raw ISC counts corroborating the rounded school headline",
    },
    "SPS_ALEVEL_2005_2009_WAYBACK": {
        "id": "st-pauls-alevel-2005-2009-wayback",
        "title": "St Paul’s School · A-level summary 2005–09 · Wayback",
        "url": "https://web.archive.org/web/20100905081757id_/http://www.stpaulsschool.org.uk/academic/exam-results/a-level-summary-last-five-years",
        "role": "direct school five-year final grid; pre-A* A, A–B and A–C grade-entry shares",
    },
    "SPS_DEST_2009_BOOKLET": {
        "id": "st-pauls-destinations-2009-booklet",
        "title": "St Paul’s Annual Information 2010–11 · 2009 leaver destinations",
        "url": "https://drive.google.com/file/d/1xw7xhqdmf8KFwtMHWf-E4FC-7cYpDP6O/view",
        "role": "first-party full institution table; 182 leavers",
    },
    "SPS_DEST_2011_BOOKLET": {
        "id": "st-pauls-destinations-2011-booklet",
        "title": "St Paul’s Annual Information 2011–12 · 2011 leaver destinations",
        "url": "https://drive.google.com/file/d/1yc4yaDv7Wgk95KqEfK7QONadjwEkSg8F/view",
        "role": "first-party full institution table; 175 leavers",
    },
    "SPS_DEST_2013_BOOKLET": {
        "id": "st-pauls-destinations-2013-booklet",
        "title": "St Paul’s Annual Information 2014–15 · 2013 leaver destinations",
        "url": "https://drive.google.com/file/d/1rXF9LhMV8hCyfKhkdKosVTWxmlYK0Chb/view",
        "role": "first-party full institution table; 174 leavers",
    },
    "SPS_DEST_2014_PAGE": {
        "id": "st-pauls-destinations-2014-page",
        "title": "St Paul’s School · University Destinations 2014",
        "url": "https://www.stpaulsschool.org.uk/ivy-league-and-oxbridge-offers-up-on-last-year/",
        "role": "first-party final destination categories; medicine overlaps university categories",
    },
    "SPS_DEST_2015_PAGE": {
        "id": "st-pauls-destinations-2015-page",
        "title": "St Paul’s School · University Destinations of 2015 leavers",
        "url": "https://www.stpaulsschool.org.uk/university-destinations/",
        "role": "first-party reconciliation: 153 UK plus 28 North American university-bound leavers",
    },
    "SPS_DEST_2015_PROSPECTUS": {
        "id": "st-pauls-destinations-2015-prospectus",
        "title": "St Paul’s School · Annual Prospectus 2016 · 2015 destinations",
        "url": "https://web.archive.org/web/20170717103245id_/http://www.stpaulsschool.org.uk/assets/img/banners/Copy-of-Annual-Prospectus-2016-Updated-for-website.pdf",
        "role": "first-party full institution table: 181 university-bound plus three other leavers",
    },
}


ST_PAULS_GCSE_HISTORY = [
    {
        "year": 1999,
        "scale": "A*-G legacy threshold",
        "top": None,
        "top_2": None,
        "top_3": None,
        "five_plus_a_star_c": 99,
        "confidence": "P",
        "note": "99% achieved at least five A*–C grades. This pupil threshold is not a grade-entry distribution.",
        "source_ids": ["SPS_DFE_HISTORIC"],
    },
    {
        "year": 2000,
        "scale": "A*-G legacy points",
        "top": None,
        "top_2": None,
        "top_3": None,
        "rank": 3,
        "five_plus_a_star_c": 100,
        "legacy_points_per_pupil": 75.8,
        "confidence": "S",
        "note": "Old ISC tariff (A*=8, A=7, etc.); not comparable with later grade-entry percentages.",
        "source_ids": ["SPS_GCSE_GUARDIAN_2000"],
    },
    {
        "year": 2001,
        "scale": "A*-G legacy points",
        "top": None,
        "top_2": None,
        "top_3": None,
        "candidates": 169,
        "five_plus_a_star_c": 100,
        "five_plus_a_g": 100,
        "legacy_points_per_pupil": 76.0,
        "four_year_average_five_plus_a_star_c": 99.5,
        "confidence": "S",
        "note": "Official-data press table; old points basis, not a grade-entry ladder.",
        "source_ids": ["SPS_GCSE_GUARDIAN_2001"],
    },
    {
        "year": 2002,
        "scale": "A*-G",
        "top": None,
        "top_2": 92.5,
        "top_3": None,
        "rank": 1,
        "candidates": 164,
        "five_plus_a_star_c": 100,
        "legacy_points_per_candidate": 78.8,
        "pupils_at_least_11_a_stars": 14,
        "confidence": "P/S",
        "note": "The school headline says 92.5% of ‘GCSE boys’ achieved A* or A; denominator wording is retained. Other fields come from the contemporary ISC table.",
        "source_ids": ["SPS_2002_EXAM_CC", "SPS_GCSE_GUARDIAN_2002"],
    },
    {
        "year": 2003,
        "scale": "A*-G legacy rank only",
        "top": None,
        "top_2": None,
        "top_3": None,
        "rank": 3,
        "confidence": "S",
        "note": "Rank only; no exact points, cohort or grade distribution was recovered.",
        "source_ids": ["SPS_GCSE_GUARDIAN_2003"],
    },
    {
        "year": 2004,
        "scale": "A*-G legacy points",
        "top": None,
        "top_2": None,
        "top_3": None,
        "rank": 1,
        "candidates": 165,
        "five_plus_a_star_c": 100,
        "isc_points_per_pupil": 81.9,
        "dfe_pupils": 161,
        "dfe_gcse_gnvq_points": 605.9,
        "confidence": "S/P",
        "note": "ISC and DfE figures use different point systems and denominators; they are not merged into the grade-share series.",
        "source_ids": ["SPS_GCSE_GUARDIAN_2004", "SPS_DFE_HISTORIC"],
    },
    {
        "year": 2005,
        "scale": "A*-G",
        "top": 74.3,
        "top_2": 94.8,
        "top_3": 99.9,
        "rank": 1,
        "candidates": 160,
        "isc_points_per_candidate": 81.3,
        "dfe_gcse_gnvq_points": 601.3,
        "confidence": "P",
        "note": "School final grade-entry ladder controls. Contemporary points-table measures are retained as separate fields.",
        "source_ids": ["SPS_GCSE_2005_2009_WAYBACK", "SPS_GCSE_GUARDIAN_2005"],
    },
    {
        "year": 2006,
        "scale": "A*-G",
        "top": 70.9,
        "top_2": 93.4,
        "top_3": 99.2,
        "confidence": "P_CONFLICT",
        "note": "Direct school final grid controls. A separate transcription gives 69.7/93.3/99.3 and remains a quarantined competing version.",
        "source_ids": ["SPS_GCSE_2005_2009_WAYBACK"],
    },
    {
        "year": 2007,
        "scale": "A*-G",
        "top": 79.3,
        "top_2": 96.6,
        "top_3": 100.0,
        "candidates": 177,
        "pupils_all_astars": 45,
        "pupils_all_but_one_a_star": 29,
        "confidence": "P",
        "note": "Final school grade-entry ladder; pupil-profile counts are separate context.",
        "source_ids": ["SPS_GCSE_2005_2009_WAYBACK"],
    },
    {
        "year": 2008,
        "scale": "A*-G",
        "top": 83.4,
        "top_2": 98.4,
        "top_3": 99.8,
        "confidence": "P",
        "note": "Direct school final grid; mixed GCSE/IGCSE cohort.",
        "source_ids": ["SPS_GCSE_2005_2009_WAYBACK"],
    },
    {
        "year": 2009,
        "scale": "A*-G",
        "top": 80.2,
        "top_2": 97.5,
        "top_3": 99.8,
        "confidence": "P",
        "note": "Direct school final grid; mixed GCSE/IGCSE cohort.",
        "source_ids": ["SPS_GCSE_2005_2009_WAYBACK"],
    },
]


def _empty_alevel_row(year: int, confidence: str, note: str, source_ids: list[str]) -> dict[str, object]:
    return {
        "year": year,
        "a_star": None,
        "a_star_a": None,
        "a_star_b": None,
        "grade_a_c": None,
        "confidence": confidence,
        "note": note,
        "source_ids": source_ids,
    }


ST_PAULS_ALEVEL_HISTORY = [
    {
        **_empty_alevel_row(1992, "S", "Old UCCA points per candidate; not a grade-entry percentage.", ["SPS_ALEVEL_1992_TIMES_IA"]),
        "rank": 3,
        "legacy_points_per_candidate": 28.3,
        "candidates": 144,
    },
    {
        **_empty_alevel_row(1993, "S", "Old UCCA points per pupil; 30 points equalled three A grades.", ["SPS_ALEVEL_1993_FT_IA"]),
        "rank": 1,
        "legacy_points_per_pupil": 29.4,
    },
    {
        **_empty_alevel_row(1994, "S", "Old UCCA points per candidate; not a grade-entry percentage.", ["SPS_ALEVEL_1994_TIMES_IA"]),
        "rank": 2,
        "legacy_points_per_candidate": 30.7,
        "candidates": 135,
    },
    {
        **_empty_alevel_row(1996, "S", "Contemporary university-entrance points measure; three failures among more than 500 entries.", ["SPS_ALEVEL_1996_TIMES_IA"]),
        "rank": 1,
        "legacy_points_per_pupil": 31.43,
        "candidates": 160,
    },
    {
        **_empty_alevel_row(1997, "S", "Financial Times measures; General Studies excluded.", ["SPS_ALEVEL_1997_FT_IA"]),
        "rank": 5,
        "ft_score": 1.40,
        "legacy_points_per_entry": 8.60,
        "legacy_points_per_pupil": 30.23,
    },
    {
        **_empty_alevel_row(1998, "S", "Financial Times measures; General Studies excluded.", ["SPS_ALEVEL_1998_FT_IA"]),
        "rank": 3,
        "five_year_rank": 2,
        "ft_score": 1.34,
        "legacy_points_per_entry": 9.11,
        "legacy_points_per_pupil": 31.78,
    },
    {
        **_empty_alevel_row(1999, "S", "A-level or vocational-equivalent points; cohort not stated.", ["SPS_ALEVEL_1999_INDEPENDENT"]),
        "legacy_points_per_pupil": 32.2,
    },
    {
        **_empty_alevel_row(2000, "S", "Old UCAS scale; General Studies excluded.", ["SPS_ALEVEL_2000_TES"]),
        "rank_by_points_per_pupil": 3,
        "legacy_points_per_pupil": 31.61,
        "rank_by_points_per_entry": 5,
        "legacy_points_per_entry": 9.04,
    },
    {
        "year": 2002,
        "a_star": None,
        "a_star_a": None,
        "a_star_b": 92.5,
        "grade_a_c": None,
        "as_grade_a_c": 96.3,
        "rank": 5,
        "legacy_score": 427,
        "confidence": "P/S",
        "note": "The school says 92.5% of ‘A Level boys’ scored A or B and 96.3% of AS takers scored A–C; denominator wording is retained.",
        "source_ids": ["SPS_2002_EXAM_CC", "SPS_ALEVEL_2002_GUARDIAN"],
    },
    {
        **_empty_alevel_row(2003, "S", "ISC narrative rank only; exact score and grade distribution were not recovered.", ["FB146"]),
        "rank": 8,
    },
    {
        **_empty_alevel_row(2004, "S/P", "UCAS/QCA points measures; not comparable with the later grade-entry ladder.", ["SPS_ALEVEL_2004_GUARDIAN", "SPS_DFE_HISTORIC"]),
        "rank": 5,
        "legacy_score": 444,
        "dfe_points_per_student": 445.4,
        "dfe_points_per_entry": 114.3,
        "candidates": 170,
    },
    {
        "year": 2005,
        "a_star": None,
        "a_star_a": 78.5,
        "a_star_b": 96.2,
        "grade_a_c": 99.6,
        "legacy_score": 444.7,
        "confidence": "P",
        "note": "Direct school final grid controls; contemporary points-table score is retained separately.",
        "source_ids": ["SPS_ALEVEL_2005_2009_WAYBACK", "SPS_ALEVEL_2005_INDEPENDENT"],
    },
    {
        "year": 2006,
        "a_star": None,
        "a_star_a": 85.0,
        "a_star_b": 97.7,
        "grade_a_c": 98.6,
        "confidence": "P_CONFLICT",
        "note": "School final grid controls. ISC raw counts produce 82.31% A, 97.20% A–B and 98.60% A–C; the populations are not silently merged.",
        "source_ids": ["SPS_ALEVEL_2005_2009_WAYBACK", "SPS_ALEVEL_2006_ISC"],
    },
    {
        "year": 2007,
        "a_star": None,
        "a_star_a": 86.5,
        "a_star_b": 97.8,
        "grade_a_c": 99.6,
        "confidence": "P",
        "note": "Direct school final grid; ISC raw-count reconstruction corroborates rounding.",
        "source_ids": ["SPS_ALEVEL_2005_2009_WAYBACK", "SPS_ALEVEL_2007_ISC"],
    },
    {
        "year": 2008,
        "a_star": None,
        "a_star_a": 83.3,
        "a_star_b": 96.0,
        "grade_a_c": 99.2,
        "confidence": "P",
        "note": "Direct school final grid; pre-A* scale.",
        "source_ids": ["SPS_ALEVEL_2005_2009_WAYBACK"],
    },
    {
        "year": 2009,
        "a_star": None,
        "a_star_a": 90.6,
        "a_star_b": 98.2,
        "grade_a_c": 99.5,
        "confidence": "P",
        "note": "Direct school final grid; A* was not awarded at A level before 2010.",
        "source_ids": ["SPS_ALEVEL_2005_2009_WAYBACK"],
    },
]


def apply_st_pauls_history(javascript: str) -> str:
    javascript = _replace_once(
        javascript,
        "id:`st-pauls`,name:`St Paul’s School`,short:`St Paul’s`,applyCentreName:`St Paul's School`,usName:`St Paul's School`,accent:`#00856a`,evidenceWindow:`2009–2026`",
        "id:`st-pauls`,name:`St Paul’s School`,short:`St Paul’s`,applyCentreName:`St Paul's School`,usName:`St Paul's School`,accent:`#00856a`,evidenceWindow:`1992–2026`",
        "St Paul’s evidence window",
    )

    source_anchor = '"SPS_2026_ALEVEL_RELEASE":'
    source_entries = _compact_json(ST_PAULS_SOURCES)[1:-1] + ","
    javascript = _replace_once(
        javascript,
        source_anchor,
        source_entries + source_anchor,
        "St Paul’s source catalogue",
    )

    field_catalog_anchor = (
        "subjects:{label:`Subjects`,kind:`count`},"
        "rank:{label:`Rank`,kind:`count`},a_star_count:"
    )
    historic_field_catalogue = (
        "subjects:{label:`Subjects`,kind:`count`},"
        "five_plus_a_star_c:{label:`% pupils with ≥5 A*–C`,kind:`percent`},"
        "five_plus_a_g:{label:`% pupils with ≥5 A*–G`,kind:`percent`},"
        "four_year_average_five_plus_a_star_c:{label:`Four-year average · % with ≥5 A*–C`,kind:`percent`},"
        "legacy_points_per_candidate:{label:`Legacy points per candidate`,kind:`decimal`},"
        "legacy_points_per_pupil:{label:`Legacy points per pupil`,kind:`decimal`},"
        "legacy_points_per_entry:{label:`Legacy points per entry`,kind:`decimal`},"
        "isc_points_per_candidate:{label:`ISC points per candidate`,kind:`decimal`},"
        "isc_points_per_pupil:{label:`ISC points per pupil`,kind:`decimal`},"
        "dfe_gcse_gnvq_points:{label:`DfE GCSE/GNVQ points`,kind:`decimal`},"
        "dfe_points_per_student:{label:`DfE points per student`,kind:`decimal`},"
        "dfe_points_per_entry:{label:`DfE points per entry`,kind:`decimal`},"
        "legacy_score:{label:`Legacy league-table score`,kind:`decimal`},"
        "ft_score:{label:`Financial Times score`,kind:`decimal`},"
        "as_grade_a_c:{label:`% AS grades A–C`,kind:`percent`},"
        "pupils_at_least_11_a_stars:{label:`Pupils with ≥11 A*s`,kind:`count`},"
        "pupils_all_but_one_a_star:{label:`Pupils with all but one grade at A*`,kind:`count`},"
        "dfe_pupils:{label:`DfE pupils`,kind:`count`},"
        "five_year_rank:{label:`Five-year rank`,kind:`count`},"
        "rank_by_points_per_pupil:{label:`Rank by points per pupil`,kind:`count`},"
        "rank_by_points_per_entry:{label:`Rank by points per entry`,kind:`count`},"
        "university_bound:{label:`University-bound leavers`,kind:`count`},"
        "uk_universities:{label:`UK universities`,kind:`count`},"
        "us_universities:{label:`US universities`,kind:`count`},"
        "us_canada:{label:`US & Canada`,kind:`count`},"
        "north_america:{label:`North America`,kind:`count`},"
        "ucl_imperial:{label:`UCL + Imperial`,kind:`count`},"
        "medicine:{label:`Medicine`,kind:`count`},"
        "europe:{label:`Europe`,kind:`count`},"
        "other:{label:`Other`,kind:`count`},"
        "rank:{label:`Rank`,kind:`count`},a_star_count:"
    )
    javascript = _replace_once(
        javascript,
        field_catalog_anchor,
        historic_field_catalogue,
        "St Paul’s historic field catalogue",
    )

    javascript = _replace_once(
        javascript,
        "dataset_id:`st_pauls_gcse`,school:`St Paul's School`,domain:`exam_results`,basis:`all held annual rows; old-scale top/top2/top3=A*/A*–A/A*–B; new-scale=9/9–8/9–7`,source_refs:[`FB146`],notes:null",
        "dataset_id:`st_pauls_gcse`,school:`St Paul's School`,domain:`exam_results`,basis:`annual grade-entry rows plus explicitly typed pre-2005 legacy thresholds, ranks and points; old-scale top/top2/top3=A*/A*–A/A*–B; new-scale=9/9–8/9–7`,source_refs:[`FB146`,`SPS_2002_EXAM_CC`,`SPS_GCSE_2005_2009_WAYBACK`],notes:`Legacy points and pupil thresholds are retained as separate fields and are never plotted as grade-entry percentages.`",
        "St Paul’s GCSE dataset metadata",
    )
    old_gcse_start = "rows:[{year:2009,scale:`A*-G`,top:80.2,top_2:97.5,top_3:99.8,confidence:`P/S`,note:null},{year:2010"
    new_gcse_start = "rows:[" + _compact_json(ST_PAULS_GCSE_HISTORY)[1:-1] + ",{year:2010"
    javascript = _replace_once(
        javascript,
        old_gcse_start,
        new_gcse_start,
        "St Paul’s GCSE history rows",
    )

    javascript = _replace_once(
        javascript,
        "dataset_id:`st_pauls_alevel`,school:`St Paul's School`,domain:`exam_results`,basis:`all held annual rows; 2009 has no A* cell; 2020–21 blank by design`,source_refs:[`FB146`],notes:null",
        "dataset_id:`st_pauls_alevel`,school:`St Paul's School`,domain:`exam_results`,basis:`annual grade-entry rows and separately typed historic points/ranks; before 2010 the displayed ladder is A, A–B and A–C because A* did not exist; 2020–21 blank by design`,source_refs:[`FB146`,`SPS_2002_EXAM_CC`,`SPS_ALEVEL_2005_2009_WAYBACK`],notes:`Historic point systems are not treated as a continuous trend and do not populate the grade-share chart.`",
        "St Paul’s A-level dataset metadata",
    )
    old_alevel_start = "rows:[{year:2009,a_star:null,a_star_a:90.6,a_star_b:98.2,confidence:`P/S`,note:null},{year:2010"
    new_alevel_start = "rows:[" + _compact_json(ST_PAULS_ALEVEL_HISTORY)[1:-1] + ",{year:2010"
    javascript = _replace_once(
        javascript,
        old_alevel_start,
        new_alevel_start,
        "St Paul’s A-level history rows",
    )

    destination_replacements = {
        "{year:2005,leavers:168,oxford:36,cambridge:23,oxbridge:59,basis:`P Annual Information`}":
            "{year:2005,leavers:168,oxford:36,cambridge:23,oxbridge:59,us_universities:15,confidence:`S/P`,basis:`source-attached Annual Information lead; underlying booklet not independently reopened`,source_ids:[`FB146`]}",
        "{year:2009,leavers:182,oxford:42,cambridge:23,oxbridge:65,basis:`P Annual Information`}":
            "{year:2009,leavers:182,oxford:42,cambridge:23,oxbridge:65,us_canada:22,confidence:`P`,basis:`final leaver destinations; full institution table`,source_ids:[`SPS_DEST_2009_BOOKLET`]}",
        "{year:2011,leavers:175,oxford:43,cambridge:30,oxbridge:73,basis:`P Annual Information`}":
            "{year:2011,leavers:175,oxford:43,cambridge:30,oxbridge:73,us_canada:15,confidence:`P`,basis:`final leaver destinations; full institution table`,source_ids:[`SPS_DEST_2011_BOOKLET`]}",
        "{year:2013,leavers:174,oxford:18,cambridge:32,oxbridge:50,basis:`P Annual Information`}":
            "{year:2013,leavers:174,oxford:18,cambridge:32,oxbridge:50,us_canada:25,europe:2,other:3,confidence:`P`,basis:`final leaver destinations; full institution table`,source_ids:[`SPS_DEST_2013_BOOKLET`]}",
        "{year:2014,leavers:null,oxford:null,cambridge:null,oxbridge:56,basis:`P school news`}":
            "{year:2014,leavers:null,oxford:null,cambridge:null,oxbridge:56,north_america:24,ucl_imperial:34,medicine:15,confidence:`P`,basis:`final destination categories; medicine overlaps university categories`,source_ids:[`SPS_DEST_2014_PAGE`]}",
        "{year:2015,leavers:null,oxford:null,cambridge:null,oxbridge:49,basis:`S external`}":
            "{year:2015,leavers:184,university_bound:181,uk_universities:153,oxford:20,cambridge:21,oxbridge:41,us_canada:28,other:3,confidence:`P`,basis:`full final table: 181 university-bound plus 3 other leavers`,source_ids:[`SPS_DEST_2015_PROSPECTUS`,`SPS_DEST_2015_PAGE`]}",
    }
    for index, (before, after) in enumerate(destination_replacements.items(), start=1):
        javascript = _replace_once(
            javascript,
            before,
            after,
            f"St Paul’s destination row {index}",
        )

    javascript = _replace_once(
        javascript,
        "{id:`C12`,school:`St Paul's Girls' School`,metric:`2025 A-level A*–A`,period:2025,old:null,new:88.7,status:`resolved_later_official_sheet`,source_refs:[`SPGS_2025_ALEVEL_SHEET`],reason:`The later official provisional subject-grade sheet supplies the previously uncaptured band.`}",
        "{id:`C12`,school:`St Paul's Girls' School`,metric:`2025 A-level A*–A`,period:2025,old:null,new:88.7,status:`resolved_later_official_sheet`,source_refs:[`SPGS_2025_ALEVEL_SHEET`],reason:`The later official provisional subject-grade sheet supplies the previously uncaptured band.`},{id:`C13`,school:`St Paul's School`,metric:`GCSE final primary ladder`,period:`2005–2009`,old:`missing or P/S`,new:`direct school five-year grid`,status:`primary_archive_lock`,source_refs:[`SPS_GCSE_2005_2009_WAYBACK`],reason:`The archived first-party rolling table supplies all three final cumulative bands.`},{id:`C14`,school:`St Paul's School`,metric:`2015 final Oxbridge destinations`,period:2015,old:49,new:41,status:`primary_prospectus_controls`,source_refs:[`SPS_DEST_2015_PROSPECTUS`,`SPS_DEST_2015_PAGE`],reason:`The full school table gives Oxford 20 plus Cambridge 21; 49 was secondary and is rejected.`}",
        "St Paul’s correction ledger",
    )
    javascript = _replace_once(
        javascript,
        "{id:`WX06`,school:`Westminster School`,period:2004,metric:`A-level A`,values:[{value:83,source:`WEST_WAYBACK_RESULTS_1988_2009`,basis:`contemporaneous deep-spine capture`},{value:84,source:`WEST_WAYBACK_RESULTS_2010`,basis:`later redesigned school table`}],treatment:`Carry 83 from the contemporaneous school capture; retain 84 as a redesign-era conflict.`}",
        "{id:`WX06`,school:`Westminster School`,period:2004,metric:`A-level A`,values:[{value:83,source:`WEST_WAYBACK_RESULTS_1988_2009`,basis:`contemporaneous deep-spine capture`},{value:84,source:`WEST_WAYBACK_RESULTS_2010`,basis:`later redesigned school table`}],treatment:`Carry 83 from the contemporaneous school capture; retain 84 as a redesign-era conflict.`},{id:`SP01`,school:`St Paul's School`,period:2006,metric:`A-level A / A–B / A–C`,values:[{value:[85,97.7,98.6],source:`SPS_ALEVEL_2005_2009_WAYBACK`,basis:`school final rolling table`},{value:[82.31,97.2,98.6],source:`SPS_ALEVEL_2006_ISC`,basis:`ISC raw counts 470 A, 85 B and 8 C from 571 entries`}],treatment:`Display the school final grid in the headline series; retain the ISC population as an explicit denominator conflict and do not average.`}",
        "St Paul’s A-level 2006 conflict ledger",
    )

    javascript = _replace_once(
        javascript,
        "datasets:45,rows:555",
        "datasets:45,rows:580",
        "scope row count",
    )
    return javascript
