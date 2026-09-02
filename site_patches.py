from __future__ import annotations

import json


def _compact_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _replace_once(source: str, before: str, after: str, label: str) -> str:
    matches = source.count(before)
    if matches != 1:
        raise RuntimeError(f"Unable to apply {label}: expected one bundle match, found {matches}")
    return source.replace(before, after, 1)


def _replace_one_of_once(
    source: str,
    alternatives: tuple[tuple[str, str], ...],
    label: str,
) -> str:
    """Apply one version-specific replacement and reject ambiguous bundle shapes."""
    matches = [
        (before, after)
        for before, after in alternatives
        if source.count(before) == 1
    ]
    if len(matches) != 1:
        found = sum(source.count(before) for before, _ in alternatives)
        raise RuntimeError(
            f"Unable to apply {label}: expected one supported bundle match, found {found}"
        )
    before, after = matches[0]
    return source.replace(before, after, 1)


def _replace_dataset_once(
    source: str,
    dataset_id: str,
    replacements: list[dict[str, object]],
    label: str,
    *,
    expected_rows: int,
    expected_signatures: tuple[str, ...],
) -> str:
    """Replace one compiled dataset while failing closed on an unexpected bundle."""
    marker = f"{{dataset_id:`{dataset_id}`"
    if source.count(marker) != 1:
        raise RuntimeError(
            f"Unable to apply {label}: expected one {dataset_id!r} dataset marker"
        )
    start = source.index(marker)
    boundary = source.find("},{dataset_id:", start)
    if boundary < 0:
        raise RuntimeError(f"Unable to apply {label}: dataset boundary was not found")
    existing = source[start : boundary + 1]
    row_count = existing.count("{year:") + existing.count("{period:")
    if row_count != expected_rows:
        raise RuntimeError(
            f"Unable to apply {label}: expected {expected_rows} compiled rows, found {row_count}"
        )
    missing = [signature for signature in expected_signatures if signature not in existing]
    if missing:
        raise RuntimeError(
            f"Unable to apply {label}: expected compiled signatures are missing"
        )
    replacement = ",".join(_compact_json(dataset) for dataset in replacements)
    return source[:start] + replacement + source[boundary + 1 :]


WINCHESTER_SOURCES = {
    "WIN_GCSE_HMC_1997": {
        "id": "winchester-gcse-hmc-inspection-1997",
        "title": "Winchester College · HMC inspection report · October 1997",
        "url": "https://web.archive.org/web/20040501054423id_/http://www.wincoll.ac.uk/academic/inspector.asp",
        "role": "first-party inspection evidence for the 1996 and 1997 whole-school A*/A and A*–B entry shares",
    },
    "WIN_GCSE_DFE_HISTORIC": {
        "id": "winchester-gcse-dfe-historic-downloads",
        "title": "DfE · historical school-performance downloads",
        "url": "https://www.compare-school-performance.service.gov.uk/download-data",
        "role": "official historic pupil thresholds; excluded Winchester IGCSEs in several years and therefore cannot populate whole-school entry-grade bands",
    },
    "WIN_GCSE_2001_ISBI": {
        "id": "winchester-gcse-2001-isbi-profile",
        "title": "Winchester College · archived ISBI school-updated profile",
        "url": "https://web.archive.org/web/20030515195823id_/http://www.isbi.com/isbi-viewschool/408-WINCHESTER_COLLEGE.html",
        "role": "strongly attributed summer-2001 entry/pass total; pass threshold is unstated and is not recast as a requested grade band",
    },
    "WIN_GCSE_2004_TIMES_REPRODUCTION": {
        "id": "winchester-gcse-2004-times-reproduction",
        "title": "The Times Top 500 · 2004 GCSE table · archived reproduction",
        "url": "https://www.albioncom.ru/countries/great-britain/srednee-obrazovanie/rejtingi-chastnyh-shkol-i-shkol-pansionov-velikobritanii/arhiv-rejtingov-shkol-pansionov-velikobritanii-do-2014-goda",
        "role": "secondary reproduction of the contemporary Times table; supplies the rounded 87.0% A*/A band only",
    },
    "WIN_GCSE_2005_TIMES_TRANSCRIPTION": {
        "id": "winchester-gcse-2005-times-transcription",
        "title": "The Times · independent-school GCSE analysis 2005 · contemporary transcription",
        "url": "https://arltblog.wordpress.com/2005/09/06/gcse-results-show-that-the-top-schools-teach-latin/",
        "role": "contemporary transcription carrying 50.9% A* and 90.9% A*/A for 132 candidates",
    },
    "WIN_GCSE_2006_ISC": {
        "id": "winchester-gcse-2006-isc",
        "title": "ISC · Year 11 examination results 2006",
        "url": "https://www.isc.co.uk/research/exam-results/exam-results-2006/",
        "role": "official final post-remarks counts: 1,069 entries, including 502 A*, 429 A and 109 B grades",
    },
    "WIN_GCSE_2011_DFE_GCSE": {
        "id": "winchester-gcse-2011-dfe-gcse",
        "title": "DfE · 2011 full GCSE subject file",
        "url": "https://webarchive.nationalarchives.gov.uk/ukgwa/20120908140957id_/http://www.education.gov.uk/schools/performance/2011/download/1_GCSE_FULL.zip",
        "role": "official subject-level GCSE cumulative bands with lawful small-cell suppression",
    },
    "WIN_GCSE_2011_DFE_IGCSE": {
        "id": "winchester-gcse-2011-dfe-igcse",
        "title": "DfE · 2011 IGCSE subject file",
        "url": "https://webarchive.nationalarchives.gov.uk/ukgwa/20120908140957id_/http://www.education.gov.uk/schools/performance/2011/download/4_iGCSE.zip",
        "role": "official exact IGCSE cumulative bands; combined with the suppressed GCSE component only as a bounded reconstruction",
    },
    "WIN_GCSE_2011_SCHOOL": {
        "id": "winchester-gcse-2011-school-headline",
        "title": "Winchester College · GCSE Results 2011",
        "url": "https://web.archive.org/web/20120430171904id_/http://www.winchestercollege.org/gcse-results-",
        "role": "first-party 99.2% A*–C headline used to tighten, but not overstate, the official suppression interval",
    },
    "WIN_GCSE_2012_DFE": {
        "id": "winchester-gcse-2012-dfe-underlying-data",
        "title": "DfE · 2012 KS4 underlying school-level data",
        "url": "https://webarchive.nationalarchives.gov.uk/ukgwa/20140111002934id_/http://www.education.gov.uk/schools/performance/2012/download/2012_KS4_Underlying_Data_School_Level.zip",
        "role": "official 1,191-entry file; 1,185 grades disclosed and six lawfully suppressed, producing exact percentage intervals",
    },
    "WIN_PREU_2010_PAGE": {
        "id": "winchester-pre-u-2010-results-page",
        "title": "Winchester College · Cambridge Pre-U results 2010",
        "url": "https://web.archive.org/web/20120507094642id_/http://www.winchestercollege.org/cambridge-pre-u-results-",
        "role": "first-party narrative only: nearly one-fifth D1, about one-third D2 itself and over three-quarters D1–D3; no exact table survives",
    },
    "WIN_PREU_2011_PDF": {
        "id": "winchester-pre-u-2011-pdf",
        "title": "Winchester College · Pre-U results 2011",
        "url": "https://web.archive.org/web/20120205020119id_/http://www.winchestercollege.org/UserFiles/pdfs/pre%20u%202011.pdf",
        "role": "official complete subject and total grade-count table",
    },
    "WIN_PREU_2012_PDF": {
        "id": "winchester-pre-u-2012-pdf",
        "title": "Winchester College · Pre-U results 2012",
        "url": "https://web.archive.org/web/20161118135039id_/http://www.winchestercollege.org/UserFiles/pdfs/2012%20Pre%20U%20Results.pdf",
        "role": "official annual Pre-U distribution",
    },
    "WIN_PREU_2013_PDF": {
        "id": "winchester-pre-u-2013-revised-pdf",
        "title": "Winchester College · revised Pre-U results 2013",
        "url": "https://web.archive.org/web/20140710091715id_/http://www.winchestercollege.org/UserFiles/pdfs/pre-U_results_revised.pdf",
        "role": "official revised annual Pre-U distribution",
    },
    "WIN_PREU_2014_PDF": {
        "id": "winchester-pre-u-2014-pdf",
        "title": "Winchester College · Pre-U results 2014",
        "url": "https://web.archive.org/web/20150613062522id_/http://www.winchestercollege.org/UserFiles/pdfs/pre-u_results-2014.pdf",
        "role": "official annual Pre-U distribution",
    },
    "WIN_PREU_2015_ORIGINAL_PDF": {
        "id": "winchester-pre-u-2015-original-pdf",
        "title": "Winchester College · Pre-U results by subject 2015 · original version",
        "url": "https://web.archive.org/web/20160119184909id_/http://www.winchestercollege.org/UserFiles/pdfs/pre-u_results_by_subject-20150813_for_website.pdf",
        "role": "official complete 443-entry grade table; controlling annual version",
    },
    "WIN_ACCOUNTS_2015": {
        "id": "winchester-accounts-2015",
        "title": "Winchester College · signed financial statements 2015",
        "url": "https://web.archive.org/web/20160330195140id_/http://www.winchestercollege.org/UserFiles/Winchester%20College%20Financial%20Statements%2031%20August%202015%20Signed.pdf",
        "role": "later 444-entry Pre-U version and university-place evidence; retained as a competing source, not merged with the original result table",
    },
    "WIN_PREU_2016_PAGE": {
        "id": "winchester-pre-u-2016-results-page",
        "title": "Winchester College · examinations and universities · 2016 capture",
        "url": "https://web.archive.org/web/20180409133837id_/http%3A%2F%2Fwww.winchestercollege.org%2Fexams-and-universities",
        "role": "first-party cumulative Pre-U headlines; no surviving entry-count table",
    },
    "WIN_PREU_2017_PDF": {
        "id": "winchester-pre-u-2017-pdf",
        "title": "Winchester College · Pre-U summer results 2017",
        "url": "https://web.archive.org/web/20181223050819id_/http://www.winchestercollege.org:80/UserFiles/Pre-U%20summer%202017%20results%20for%20website.xlsx.pdf",
        "role": "official annual grade counts; primary D1–M1 computation controls",
    },
    "WIN_ACCOUNTS_2018": {
        "id": "winchester-accounts-2018",
        "title": "Winchester College · signed accounts 2018",
        "url": "https://web.archive.org/web/20211130031905id_/https://www.winchestercollege.org/assets/files/uploads/Winchester%20College%20Accounts%202018%20-%20FINAL%20SIGNED.pdf",
        "role": "official Pre-U headline and university-offer evidence",
    },
    "WIN_PREU_2019_PDF": {
        "id": "winchester-pre-u-2019-pdf",
        "title": "Winchester College · Pre-U summer results 2019",
        "url": "https://web.archive.org/web/20190919111217id_/https://www.winchestercollege.org/assets/files/uploads/Pre%20U%20Results%20Summer%202019.pdf",
        "role": "official annual grade-count table; controls D1, D1–M1 and D1–M2",
    },
    "WIN_ACCOUNTS_2020": {
        "id": "winchester-accounts-2020",
        "title": "Winchester College · signed annual accounts 2020",
        "url": "https://web.archive.org/web/20220211185131id_/https://www.winchestercollege.org/assets/files/uploads/winchester-college-annual-accounts-2020.pdf",
        "role": "official centre-assessed Pre-U headline and university-offer evidence",
    },
    "WIN_MIXED_RESULTS_2021_PDF": {
        "id": "winchester-mixed-pre-u-a-level-2021-pdf",
        "title": "Winchester College · combined Pre-U and A-level results 2021",
        "url": "https://web.archive.org/web/20211023181756id_/https://www.winchestercollege.org/assets/files/uploads/pre-u-results-summer-2021-official.pdf",
        "role": "official 450-entry teacher-assessed mixed-qualification ruler; deliberately separated from pure Pre-U",
    },
    "WIN_ALEVEL_2003_2009_SCHOOL": {
        "id": "winchester-alevel-2003-2009-school-table",
        "title": "Winchester College · examination results 2003–2009",
        "url": "https://web.archive.org/web/20090829142933id_/http://www.wincoll.ac.uk/Home.aspx?m=0&cat=42",
        "role": "official seven-year school table; controlling A and A–B entry shares",
    },
    "WIN_ALEVEL_2003_TIMES": {
        "id": "winchester-alevel-2003-times-variant",
        "title": "The Times · Winchester A-level results 2003",
        "url": "https://www.thetimes.com/uk/education/article/troubled-school-has-top-results-nxjjpqd93q0",
        "role": "contemporary conflicting 559-entry, 73.2%-A population; retained as a comparator only",
    },
    "WIN_ALEVEL_2006_ISC": {
        "id": "winchester-alevel-2006-isc-variant",
        "title": "ISC · Year 13 boys examination workbook 2006",
        "url": "https://www.isc.co.uk/media/2474/2006_examresults_year13_boys_isc.xls",
        "role": "narrower 546-full-A-level-entry population plus 128 AS entries; never merged with the school 641-entry table",
    },
    "WIN_OXBRIDGE_GUARDIAN_2001_2006": {
        "id": "winchester-oxbridge-guardian-2001-2006",
        "title": "The Guardian · Oxbridge school admissions analysis",
        "url": "https://www.theguardian.com/uk/2007/mar/05/schools.oxbridgeandelitism",
        "role": "Oxford and Cambridge successful-application/admission counts for 2001 and 2006",
    },
    "WIN_OXBRIDGE_SUTTON_2002_2008": {
        "id": "winchester-oxbridge-sutton-trust-2002-2008",
        "title": "Sutton Trust · university admissions by individual schools",
        "url": "https://www.suttontrust.com/our-research/university-admissions-individual-schools/",
        "role": "multi-year Oxbridge admission aggregates; not annual final-destination observations",
    },
    "WIN_ANNUAL_REPORT_2008": {
        "id": "winchester-annual-report-2008",
        "title": "Winchester College · development annual report 2008",
        "url": "https://web.archive.org/web/20150504192437id_/http://www.winchestercollege.org/UserFiles/pdfs/Development%20-%20Annual%20report%2008.pdf",
        "role": "first-party 2009-cycle Oxbridge offer evidence and terminology cross-check",
    },
    "WIN_DESTINATIONS_2010_PAGE": {
        "id": "winchester-destinations-2010-page",
        "title": "Winchester College · examinations and universities · 2010",
        "url": "https://web.archive.org/web/20100418040159id_/http://www.winchestercollege.org/exams-and-universities",
        "role": "first-party annual Oxbridge places and rolling-total evidence",
    },
    "WIN_DESTINATIONS_2011_PAGE": {
        "id": "winchester-destinations-2011-page",
        "title": "Winchester College · examinations and universities · 2011",
        "url": "https://web.archive.org/web/20110514050159id_/https://www.winchestercollege.org/exams-and-universities",
        "role": "first-party rolling total from which the annual 44 is derived",
    },
    "WIN_DESTINATIONS_2012_PAGE": {
        "id": "winchester-destinations-2012-page",
        "title": "Winchester College · examinations and universities · 2012",
        "url": "https://web.archive.org/web/20120205020119id_/https://www.winchestercollege.org/exams-and-universities",
        "role": "first-party 17 Oxford plus 21 Cambridge annual split",
    },
    "WIN_DESTINATIONS_2010_2019_PDF": {
        "id": "winchester-destinations-2010-2019-pdf",
        "title": "Winchester College · leavers' destinations 2010–2019",
        "url": "https://web.archive.org/web/20201026100234id_/https://www.winchestercollege.org/assets/files/uploads/WinColl_5016_LeaversDestination_2010-19_v2.0.pdf",
        "role": "official rounded ten-year destination distribution; published labels total 99%",
    },
    "WIN_DESTINATIONS_2020_PDF": {
        "id": "winchester-destinations-2020-pdf",
        "title": "Winchester College · leavers' destinations 2020",
        "url": "https://web.archive.org/web/20201026104822id_/https://www.winchestercollege.org/assets/files/uploads/WinColl_5016_LeaversDestination_2020_v2.0.pdf",
        "role": "official rounded annual destination distribution; published labels total 95% and are not renormalised",
    },
    "WIN_DESTINATIONS_2021_IMAGE": {
        "id": "winchester-destinations-2021-image",
        "title": "Winchester College · leavers' destinations 2021",
        "url": "https://web.archive.org/web/20211113102435id_/https://www.winchestercollege.org/assets/img/resized/standard/leavers-destinations-sept21.png",
        "role": "official overall destination-category graphic; a separate component graphic conflicts and is not merged",
    },
    "WIN_DESTINATIONS_2022_UK_IMAGE": {
        "id": "winchester-destinations-2022-uk-image",
        "title": "Winchester College · UK destinations 2022",
        "url": "https://web.archive.org/web/20230820145307id_/https://www.winchestercollege.org/assets/img/resized/standard/uk-destinations-2022.png",
        "role": "official exact Oxford and Cambridge destination counts",
    },
    "WIN_DESTINATIONS_2022_OVERALL_IMAGE": {
        "id": "winchester-destinations-2022-overall-image",
        "title": "Winchester College · overall leavers' destinations 2022",
        "url": "https://web.archive.org/web/20230820145307id_/https://www.winchestercollege.org/assets/img/resized/standard/leavers-destinations-2022.png",
        "role": "official complete overall destination-category distribution",
    },
    "WIN_CURRENT_RESULTS_2025": {
        "id": "winchester-exam-results-futures-2025",
        "title": "Winchester College · Exam Results & Futures · 2024/2025",
        "url": "https://www.winchestercollege.org/learning/exam-results-destinations/",
        "role": "dedicated controlling current page: A-level 44% A*, 75% A*–A and 92% A*–B; 39 Oxbridge offers, 50 US offers, 9 Ivy League, 17 Ivy League Plus and cohort 156",
    },
    "WIN_ALEVEL_2025_INITIAL": {
        "id": "winchester-alevel-results-initial-2025",
        "title": "Winchester College · Winchester Weekly · 27 August 2025",
        "url": "https://www.winchestercollege.org/news-diary/news/newsletters/winchester-weekly-27-august-2025/",
        "role": "official initial A-level headline of 42% A*, 74% A*–A and 91% A*–B; superseded in the controlling current results page but retained as a source version",
    },
    "WIN_CURRENT_SIXTH_FORM_2025": {
        "id": "winchester-sixth-form-achievements-2025",
        "title": "Winchester College · Sixth Form achievements 2025",
        "url": "https://www.winchestercollege.org/school-life/sixth-form/",
        "role": "official companion page carrying the conflicting 47-US-offer variant",
    },
    "WIN_OXBRIDGE_2026_INITIAL": {
        "id": "winchester-oxbridge-offers-spring-2026",
        "title": "Winchester College · Window on Winchester · Spring 2026",
        "url": "https://www.winchestercollege.org/news-diary/news/newsletters/window-on-winchester-spring-2026/",
        "role": "official initial, to-date total of 38 Oxford and Cambridge offers; the release names early US institutions but publishes no US-offer total",
    },
}


def _empty_winchester_gcse_row(
    year: int,
    note: str,
    source_ids: list[str],
    confidence: str = "P/S",
) -> dict[str, object]:
    return {
        "year": year,
        "scale": "A*-G",
        "top_equivalent": None,
        "astar_a_equivalent": None,
        "astar_b_or_9_6": None,
        "confidence": confidence,
        "publication_status": "No defensible whole-school three-band entry distribution recovered",
        "note": note,
        "source_ids": source_ids,
    }


_NO_THREE_BAND_PROFILE = (
    "No year-specific whole-school A*, A*/A or A*–B entry distribution was recovered. "
    "The cells remain blank rather than being estimated."
)


WINCHESTER_GCSE_HISTORY = [
    _empty_winchester_gcse_row(1994, _NO_THREE_BAND_PROFILE, ["FB146"], "R"),
    _empty_winchester_gcse_row(1995, _NO_THREE_BAND_PROFILE, ["FB146"], "R"),
    {
        "year": 1996,
        "scale": "A*-G",
        "top_equivalent": None,
        "astar_a_equivalent": 86.0,
        "astar_b_or_9_6": 97.7,
        "confidence": "P",
        "note": "Official HMC comparison; source-rounded whole-school entry shares. A* was not reported separately.",
        "source_ids": ["WIN_GCSE_HMC_1997"],
    },
    {
        "year": 1997,
        "scale": "A*-G",
        "entries": 849,
        "top_equivalent": None,
        "astar_a_equivalent": 85.0,
        "astar_b_or_9_6": 97.4,
        "confidence": "P",
        "note": "Official HMC result; source-rounded whole-school entry shares. A* was not reported separately.",
        "source_ids": ["WIN_GCSE_HMC_1997"],
    },
    _empty_winchester_gcse_row(1998, _NO_THREE_BAND_PROFILE, ["FB146"], "R"),
    _empty_winchester_gcse_row(1999, _NO_THREE_BAND_PROFILE, ["FB146"], "R"),
    _empty_winchester_gcse_row(
        2000,
        "Contemporary government figures are pupil thresholds over a recognised-GCSE subset and omit substantial IGCSE provision; they cannot populate these entry-grade bands.",
        ["WIN_GCSE_DFE_HISTORIC"],
    ),
    {
        **_empty_winchester_gcse_row(
            2001,
            "The school-updated profile is strongly attributable to summer 2001 and gives 815 entries and 810 ‘passes’, but does not define the pass threshold; none of the three requested bands can be inferred.",
            ["WIN_GCSE_2001_ISBI", "WIN_GCSE_DFE_HISTORIC"],
        ),
        "entries": 815,
    },
    _empty_winchester_gcse_row(
        2002,
        "Government figures cover a recognised-GCSE subset and omit substantial IGCSE provision; they cannot populate these whole-school entry-grade bands.",
        ["WIN_GCSE_DFE_HISTORIC"],
    ),
    _empty_winchester_gcse_row(
        2003,
        "Government figures cover a recognised-GCSE subset and omit substantial IGCSE provision; they cannot populate these whole-school entry-grade bands.",
        ["WIN_GCSE_DFE_HISTORIC"],
    ),
    {
        "year": 2004,
        "scale": "A*-G",
        "top_equivalent": None,
        "astar_a_equivalent": 87.0,
        "astar_b_or_9_6": None,
        "confidence": "S",
        "note": "Rounded whole-school GCSE/IGCSE-style result in a reproduction of The Times Top 500; A* and A*–B were not reported.",
        "source_ids": ["WIN_GCSE_2004_TIMES_REPRODUCTION"],
    },
    {
        "year": 2005,
        "scale": "A*-G",
        "candidates": 132,
        "top_equivalent": 50.9,
        "astar_a_equivalent": 90.9,
        "astar_b_or_9_6": None,
        "confidence": "S",
        "note": "Contemporary Times transcription; A*–B was not reported.",
        "source_ids": ["WIN_GCSE_2005_TIMES_TRANSCRIPTION"],
    },
    {
        "year": 2006,
        "scale": "A*-G",
        "entries": 1069,
        "top_equivalent": 47.0,
        "astar_a_equivalent": 87.1,
        "astar_b_or_9_6": 97.3,
        "confidence": "P",
        "note": "Recomputed from official final counts: A*=502, A=429 and B=109 of 1,069 entries; displayed to one decimal place.",
        "source_ids": ["WIN_GCSE_2006_ISC"],
    },
    _empty_winchester_gcse_row(
        2007,
        "The surviving government row is a recognised-qualification pupil measure distorted by IGCSE exclusions; no whole-school entry-grade distribution was recovered.",
        ["WIN_GCSE_DFE_HISTORIC"],
    ),
    _empty_winchester_gcse_row(
        2008,
        "The surviving government row is a recognised-qualification pupil measure distorted by IGCSE exclusions; no whole-school entry-grade distribution was recovered.",
        ["WIN_GCSE_DFE_HISTORIC"],
    ),
    _empty_winchester_gcse_row(
        2009,
        "The surviving government row is a recognised-qualification pupil measure distorted by IGCSE exclusions; no whole-school entry-grade distribution was recovered.",
        ["WIN_GCSE_DFE_HISTORIC"],
    ),
    _empty_winchester_gcse_row(
        2010,
        "Accredited IGCSEs entered the official pupil measures, but the surviving 100% five-grade headline is not an entry-grade distribution and cannot populate A*, A*/A or A*–B.",
        ["WIN_GCSE_DFE_HISTORIC"],
    ),
    {
        "year": 2011,
        "scale": "A*-G",
        "top_equivalent": None,
        "astar_a_equivalent": 90.7,
        "astar_b_or_9_6": None,
        "confidence": "P/R",
        "note": "Upper endpoint, rounded to one decimal place, of the feasible 90.40–90.69% A*/A interval reconstructed from DfE-suppressed cells and Winchester's 99.2% A*–C headline. A* and A*–B are not separately recoverable; feasible denominators are 1,040–1,042.",
        "source_ids": ["WIN_GCSE_2011_DFE_GCSE", "WIN_GCSE_2011_DFE_IGCSE", "WIN_GCSE_2011_SCHOOL"],
    },
    {
        "year": 2012,
        "scale": "A*-G",
        "entries": 1191,
        "top_equivalent": 69.0,
        "astar_a_equivalent": 93.5,
        "astar_b_or_9_6": 99.0,
        "confidence": "P/R",
        "note": "Upper endpoints, rounded to one decimal place, of the DfE-suppression intervals: A* 68.51–69.02%, A*/A 93.03–93.53% and A*–B 98.49–98.99%. Disclosed grades are A*=816, A=292 and B=65; six of 1,191 entries are suppressed.",
        "source_ids": ["WIN_GCSE_2012_DFE"],
    },
]


WINCHESTER_PRE_U_HISTORY = [
    {
        "year": 2010,
        "entries": None,
        "d1": None,
        "d1_d2": None,
        "d1_d3_honest_astar_a": None,
        "d1_m1_published": None,
        "d1_m2": None,
        "d1_m3": None,
        "confidence": "P/NARRATIVE",
        "publication_status": "Official narrative survives; exact grade counts and percentages do not",
        "narrative_d1": "nearly one-fifth",
        "narrative_d2_grade_itself": "about one-third",
        "narrative_d1_d3": "over three-quarters",
        "note": "The source wording is retained verbatim in substance and is not converted into point estimates.",
        "source_ids": ["WIN_PREU_2010_PAGE"],
    },
    {
        "year": 2011,
        "entries": 326,
        "d1": 25.2,
        "d1_d2": 51.8,
        "d1_d3_honest_astar_a": 79.8,
        "d1_m1_published": 90.8,
        "d1_m2": 95.1,
        "d1_m3": 98.8,
        "confidence": "P",
        "note": "Official complete total and subject table.",
        "fold_pp": 11.0,
        "source_ids": ["WIN_PREU_2011_PDF"],
    },
    {
        "year": 2012,
        "entries": 341,
        "d1": 20.5,
        "d1_d2": 50.1,
        "d1_d3_honest_astar_a": 80.1,
        "d1_m1_published": 89.1,
        "d1_m2": 94.7,
        "d1_m3": 97.9,
        "confidence": "P",
        "note": "Official annual table; the newly recovered D1 and D1–M3 endpoints complete the published ladder.",
        "fold_pp": 9.0,
        "source_ids": ["WIN_PREU_2012_PDF"],
    },
    {
        "year": 2013,
        "entries": 426,
        "d1": 20.2,
        "d1_d2": 50.5,
        "d1_d3_honest_astar_a": 79.1,
        "d1_m1_published": 90.6,
        "d1_m2": 95.8,
        "d1_m3": 98.1,
        "confidence": "P",
        "note": "Official revised annual table controls.",
        "fold_pp": 11.5,
        "source_ids": ["WIN_PREU_2013_PDF"],
    },
    {
        "year": 2014,
        "entries": 468,
        "d1": 21.2,
        "d1_d2": 51.1,
        "d1_d3_honest_astar_a": 79.5,
        "d1_m1_published": 89.3,
        "d1_m2": 94.7,
        "d1_m3": 97.2,
        "confidence": "P",
        "note": "Official annual table.",
        "fold_pp": 9.8,
        "source_ids": ["WIN_PREU_2014_PDF"],
    },
    {
        "year": 2015,
        "entries": 443,
        "d1": 21.0,
        "d1_d2": 47.4,
        "d1_d3_honest_astar_a": 75.2,
        "d1_m1_published": 84.2,
        "d1_m2": 92.8,
        "d1_m3": 97.3,
        "confidence": "P/CONFLICT",
        "note": "The complete original 443-entry table controls. Later signed accounts report 444 entries and rounded bands of 20.9%, 47.3%, 75.0% and 97.3%; their printed 99.4% pass rate is arithmetically impossible for any integer numerator over 444. The two versions are never mixed.",
        "fold_pp": 9.0,
        "source_ids": ["WIN_PREU_2015_ORIGINAL_PDF", "WIN_ACCOUNTS_2015"],
    },
    {
        "year": 2016,
        "entries": None,
        "d1": None,
        "d1_d2": 49.9,
        "d1_d3_honest_astar_a": 75.4,
        "d1_m1_published": 86.1,
        "d1_m2": 92.8,
        "d1_m3": None,
        "confidence": "P",
        "note": "Official cumulative headlines. The reported 120 is a pupil count, not a subject-entry denominator, and is therefore not placed in Entries.",
        "fold_pp": 10.7,
        "source_ids": ["WIN_PREU_2016_PAGE"],
    },
    {
        "year": 2017,
        "entries": 470,
        "d1": 19.4,
        "d1_d2": 47.9,
        "d1_d3_honest_astar_a": 71.3,
        "d1_m1_published": 84.0,
        "d1_m2": 92.3,
        "d1_m3": 96.6,
        "confidence": "P/CONFLICT",
        "note": "The official raw-count computation of 84.0% D1–M1 controls. A later secondary companion's approximately 82% candidate remains in the conflict register only.",
        "fold_pp": 12.7,
        "source_ids": ["WIN_PREU_2017_PDF", "FB146"],
    },
    {
        "year": 2018,
        "entries": 509,
        "d1": 21.8,
        "d1_d2": 49.3,
        "d1_d3_honest_astar_a": 74.5,
        "d1_m1_published": 86.4,
        "d1_m2": 92.3,
        "d1_m3": 95.5,
        "pre_u_pass": 98.6,
        "confidence": "P/R",
        "note": "Official signed-account percentages. Integer bands are uniquely reconstructable, but the displayed cumulative percentages remain the directly published values.",
        "fold_pp": 11.9,
        "source_ids": ["WIN_ACCOUNTS_2018"],
    },
    {
        "year": 2019,
        "entries": 476,
        "d1": 20.2,
        "d1_d2": 42.4,
        "d1_d3_honest_astar_a": 67.4,
        "d1_m1_published": 81.5,
        "d1_m2": 92.6,
        "d1_m3": 96.6,
        "confidence": "P/CONFLICT",
        "note": "Official grade counts control: D1–M1 is 81.5% and D1–M2 is 92.6%. The former's approximately 81.2% secondary candidate remains a comparator; 92.7% cannot arise from an integer numerator over 476.",
        "fold_pp": 14.1,
        "source_ids": ["WIN_PREU_2019_PDF", "FB146"],
    },
    {
        "year": 2020,
        "scale": "D1-P3 CAG",
        "entries": 469,
        "d1": 24.9,
        "d1_d2": 56.1,
        "d1_d3_honest_astar_a": 81.0,
        "d1_m1_published": None,
        "d1_m2": None,
        "d1_m3": 99.1,
        "pre_u_pass": 99.8,
        "d1_count": 117,
        "d2_count": 146,
        "d3_count": 117,
        "m1_m3_count": 85,
        "p1_p3_count": 3,
        "u_count": 1,
        "confidence": "P/R",
        "note": "Pandemic centre-assessed grades; quarantined from examined-year comparisons. The six integer bands are mathematically unique reconstructions from the signed accounts' one-decimal percentages, not printed raw counts.",
        "source_ids": ["WIN_ACCOUNTS_2020"],
    },
]


WINCHESTER_MIXED_RESULTS_2021 = [
    {
        "year": 2021,
        "level": "A-level/Pre-U",
        "scale": "mixed TAG equivalence ruler",
        "entries": 450,
        "a_star": 52.4,
        "a_star_a": 80.2,
        "a_star_b": 92.2,
        "published_pass_rate": 98.9,
        "confidence": "P",
        "note": "Teacher-assessed pandemic year combining A-level and Pre-U entries. This source-defined crosswalk is intentionally quarantined and cannot extend either pure qualification trend.",
        "source_ids": ["WIN_MIXED_RESULTS_2021_PDF"],
    }
]


WINCHESTER_ALEVEL_HISTORY = [
    {
        "year": 2003,
        "entries": 506,
        "grade_a": 75.9,
        "grade_a_b": 93.3,
        "a_count": 384,
        "b_count": 88,
        "c_count": 23,
        "d_count": 6,
        "e_count": 2,
        "unclassified_residual": 3,
        "confidence": "P/CONFLICT",
        "note": "The official school seven-year table controls. A contemporary ISC/Times population reports 559 entries, 409 A grades and 73.2% A; it is preserved as a denominator conflict and is not averaged or merged.",
        "source_ids": ["WIN_ALEVEL_2003_2009_SCHOOL", "WIN_ALEVEL_2003_TIMES"],
    },
    {
        "year": 2004,
        "entries": 625,
        "grade_a": 73.4,
        "grade_a_b": 94.1,
        "a_count": 459,
        "b_count": 129,
        "c_count": 30,
        "d_count": 7,
        "e_count": 0,
        "unclassified_residual": 0,
        "confidence": "P",
        "note": "Official school seven-year table.",
        "source_ids": ["WIN_ALEVEL_2003_2009_SCHOOL"],
    },
    {
        "year": 2005,
        "entries": 571,
        "grade_a": 69.9,
        "grade_a_b": 91.2,
        "a_count": 399,
        "b_count": 122,
        "c_count": 34,
        "d_count": 9,
        "e_count": 6,
        "unclassified_residual": 1,
        "confidence": "P",
        "note": "Official school seven-year table.",
        "source_ids": ["WIN_ALEVEL_2003_2009_SCHOOL"],
    },
    {
        "year": 2006,
        "entries": 641,
        "grade_a": 71.3,
        "grade_a_b": 91.3,
        "a_count": 457,
        "b_count": 128,
        "c_count": 37,
        "d_count": 13,
        "e_count": 5,
        "unclassified_residual": 1,
        "confidence": "P/CONFLICT",
        "note": "The school 641-entry table controls. ISC separately reports a narrower 546 full-A-level entries plus 128 AS entries; the populations are not merged.",
        "source_ids": ["WIN_ALEVEL_2003_2009_SCHOOL", "WIN_ALEVEL_2006_ISC"],
    },
    {
        "year": 2007,
        "entries": 610,
        "grade_a": 80.2,
        "grade_a_b": 96.9,
        "a_count": 489,
        "b_count": 102,
        "c_count": 15,
        "d_count": 4,
        "e_count": 0,
        "unclassified_residual": 0,
        "confidence": "P",
        "note": "Official school seven-year table.",
        "source_ids": ["WIN_ALEVEL_2003_2009_SCHOOL"],
    },
    {
        "year": 2008,
        "entries": 578,
        "grade_a": 80.4,
        "grade_a_b": 93.8,
        "a_count": 465,
        "b_count": 77,
        "c_count": 23,
        "d_count": 8,
        "e_count": 4,
        "unclassified_residual": 1,
        "confidence": "P",
        "note": "Official school seven-year table.",
        "source_ids": ["WIN_ALEVEL_2003_2009_SCHOOL"],
    },
    {
        "year": 2009,
        "entries": 562,
        "grade_a": 77.8,
        "grade_a_b": 94.3,
        "a_count": 437,
        "b_count": 93,
        "c_count": 21,
        "d_count": 9,
        "e_count": 2,
        "unclassified_residual": 0,
        "confidence": "P",
        "note": "Official school seven-year table.",
        "source_ids": ["WIN_ALEVEL_2003_2009_SCHOOL"],
    },
    {
        "year": 2022,
        "entries": None,
        "a_star": 41.7,
        "a_star_a": 76.3,
        "a_star_b": 92.5,
        "confidence": "P",
        "note": "Post-pandemic qualification year; retained as published.",
        "source_ids": ["FB146"],
    },
    {
        "year": 2023,
        "entries": None,
        "a_star": 42.4,
        "a_star_a": 79.6,
        "a_star_b": 93.6,
        "confidence": "P",
        "note": "Post-remark PDF controls over provisional 40.7/77.9.",
        "source_ids": ["FB146"],
    },
    {
        "year": 2024,
        "entries": None,
        "a_star": 29.6,
        "a_star_a": 68.9,
        "a_star_b": 90.0,
        "confidence": "P",
        "note": "Reversion to stricter grading.",
        "source_ids": ["FB146"],
    },
    {
        "year": 2025,
        "entries": None,
        "a_star": 44.0,
        "a_star_a": 75.0,
        "a_star_b": 92.0,
        "confidence": "P/CONFLICT",
        "note": "The dedicated current results page controls at 44% A*, 75% A*–A and 92% A*–B. Winchester's initial 27 August 2025 newsletter reported 42%, 74% and 91%; that official earlier version remains in the conflict register.",
        "source_ids": ["WIN_CURRENT_RESULTS_2025", "WIN_ALEVEL_2025_INITIAL"],
    },
    {
        "year": 2026,
        "entries": None,
        "pupils_at_least_3_astars_pct_approx": 25,
        "confidence": "P",
        "publication_status": "Pending detailed publication — no exact 2026 A-level grade-entry bands released as of 2 September 2026",
        "note": "The official post says around a quarter of pupils achieved at least three A* grades. That pupil-level profile is context only and is not recast as an entry percentage.",
        "source_ids": ["WIN_2026_RESULTS_HUB", "WIN_2026_ALEVEL_POST"],
    },
]


WINCHESTER_ACCESS_HISTORY = [
    {"period": "1836", "metric": "percent_of_leavers_to_oxbridge", "value": 64, "unit": "percent", "outcome_type": "historic destination estimate", "confidence": "S", "source_ids": ["FB140", "FB146"]},
    {"period": "1893", "metric": "percent_of_over_16_leavers_to_oxbridge", "value": 56.6, "unit": "percent", "outcome_type": "historic destination estimate", "confidence": "S", "source_ids": ["FB140", "FB146"]},
    {"period": "1893", "metric": "percent_of_all_leavers_to_any_university", "value": 49, "unit": "percent", "outcome_type": "historic destination estimate", "confidence": "S", "source_ids": ["FB140", "FB146"]},
    {"period": "1886-1900", "metric": "open_oxbridge_scholarships_cumulative", "value": 146, "unit": "count", "outcome_type": "scholarships", "confidence": "S", "source_ids": ["FB140", "FB146"]},
    {"period": "c.1968", "metric": "oxbridge_raw_count_per_year", "value": 80, "unit": "approx_count", "outcome_type": "approximate annual access", "confidence": "S", "source_ids": ["FB140", "FB146"]},
    {"period": "2000", "metric": "expected_oxbridge_take_up_rate", "value": 40, "unit": "percent", "outcome_type": "expectation, not realised outcome", "confidence": "S", "note": "Contemporary approximate expectation only.", "source_ids": ["FB140", "FB146"]},
    {"period": "2001", "metric": "successful_applications_or_admissions", "value": 47, "oxford": 30, "cambridge": 17, "outcome_type": "successful applications/admissions", "confidence": "P", "source_ids": ["WIN_OXBRIDGE_GUARDIAN_2001_2006"]},
    {"period": "2002", "metric": "forecast_oxbridge_rate", "value": "30–40%", "outcome_type": "forecast, not realised outcome", "confidence": "S", "note": "Retained only as a forecast range.", "source_ids": ["FB140", "FB146"]},
    {"period": "2002-2006", "metric": "oxbridge_admissions_aggregate", "value": 230, "rate_pct": 36.0, "outcome_type": "multi-year admissions aggregate", "denominator_basis": "university entrants", "confidence": "P", "source_ids": ["WIN_OXBRIDGE_SUTTON_2002_2008"]},
    {"period": "2006", "metric": "successful_applications_or_admissions", "value": 56, "oxford": 38, "cambridge": 18, "outcome_type": "successful applications/admissions", "confidence": "P", "source_ids": ["WIN_OXBRIDGE_GUARDIAN_2001_2006"]},
    {"period": "2007-2008", "metric": "oxbridge_admissions_aggregate", "value": 63, "leavers": 208, "rate_pct": 30.3, "outcome_type": "two-year admissions aggregate", "denominator_basis": "higher-education entrants", "confidence": "P", "source_ids": ["WIN_OXBRIDGE_SUTTON_2002_2008"]},
    {"period": "2009", "metric": "oxbridge_places_or_offers", "value": 51, "oxford": 33, "cambridge": 18, "rate_pct": 37.5, "outcome_type": "source terminology conflict: places versus offers", "confidence": "P/CONFLICT", "note": "The school page says places; the annual report says conditional/firm offers secured. No final-destination label is imposed.", "source_ids": ["WIN_ALEVEL_2003_2009_SCHOOL", "WIN_ANNUAL_REPORT_2008"]},
    {"period": "2010", "metric": "oxbridge_places", "value": 45, "rate_pct": 33.5, "outcome_type": "school-reported places", "confidence": "P", "source_ids": ["WIN_DESTINATIONS_2010_PAGE"]},
    {"period": "2011", "metric": "derived_oxbridge_matriculations", "value": 44, "outcome_type": "derived annual matriculations", "confidence": "D/P", "note": "Five-cycle official total 238 less the preceding nested four-cycle total 194; not directly printed as an annual count.", "source_ids": ["WIN_DESTINATIONS_2010_PAGE", "WIN_DESTINATIONS_2011_PAGE"]},
    {"period": "2012", "metric": "matriculations", "value": 38, "oxford": 17, "cambridge": 21, "outcome_type": "matriculations", "confidence": "P", "source_ids": ["WIN_DESTINATIONS_2012_PAGE"]},
    {"period": "2013", "metric": "offers", "value": 41, "outcome_type": "school-reported offers", "confidence": "P", "source_ids": ["FB140", "FB146"]},
    {"period": "2013", "metric": "reported_oxbridge_destinations", "value": 40, "outcome_type": "secondary reported destinations", "confidence": "S", "note": "Good Schools Guide figure; retained separately from the 41-offer row.", "source_ids": ["FB146"]},
    {"period": "2014", "metric": "matriculations", "value": 43, "oxford": 31, "cambridge": 12, "outcome_type": "matriculations", "confidence": "P", "note": "Strict acceptances are 44; the one-place basis gap remains explicit.", "source_ids": ["FB140", "FB146"]},
    {"period": "2015", "metric": "oxbridge_places", "value": 44, "outcome_type": "places, including deferred 2016", "confidence": "P", "source_ids": ["WIN_ACCOUNTS_2015"]},
    {"period": "2015", "metric": "premier_us_places", "value": 16, "outcome_type": "places at premier US universities", "confidence": "P", "source_ids": ["WIN_ACCOUNTS_2015"]},
    {"period": "2016", "metric": "matriculations", "value": 27, "oxford": 13, "cambridge": 14, "outcome_type": "matriculations", "confidence": "P", "note": "Strict acceptances are 26; the one-place basis gap remains explicit.", "source_ids": ["FB140", "FB146"]},
    {"period": "2007/08-2014/15", "metric": "average_matriculations_per_year", "value": 45, "outcome_type": "multi-year average matriculations", "confidence": "P", "source_ids": ["WIN_ACCOUNTS_2015"]},
    {"period": "2010-2018", "metric": "matriculation_rate", "value": 33, "unit": "percent", "outcome_type": "multi-year matriculation rate", "confidence": "P", "source_ids": ["FB140", "FB146"]},
    {"period": "2017", "metric": "oxbridge_places", "value": 37, "outcome_type": "places for 2017 or deferred 2018", "confidence": "P", "source_ids": ["FB140", "FB146"]},
    {"period": "2017", "metric": "premier_us_places", "value": 18, "outcome_type": "US places", "confidence": "P", "source_ids": ["FB140", "FB146"]},
    {"period": "2017-2021", "metric": "cambridge_offers_five_cycles", "value": 61, "outcome_type": "five-cycle offer aggregate", "confidence": "P", "source_ids": ["FB140", "FB146"]},
    {"period": "2018", "metric": "oxbridge_offers", "value": 37, "outcome_type": "signed-account offers", "confidence": "P/CONFLICT", "note": "A stricter application ledger carries 36; both source populations remain visible.", "source_ids": ["WIN_ACCOUNTS_2018", "FB146"]},
    {"period": "2018", "metric": "north_american_places", "value": 11, "outcome_type": "North American places", "confidence": "P", "source_ids": ["WIN_ACCOUNTS_2018"]},
    {"period": "2009-2018", "metric": "offers_cumulative", "value": 401, "outcome_type": "ten-year offer aggregate", "confidence": "P", "source_ids": ["WIN_ACCOUNTS_2018"]},
    {"period": "2020", "metric": "oxbridge_offers", "value": 25, "outcome_type": "offers", "confidence": "P", "source_ids": ["WIN_ACCOUNTS_2020"]},
    {"period": "2020", "metric": "premier_north_american_places", "value": 7, "outcome_type": "North American places", "confidence": "P", "source_ids": ["WIN_ACCOUNTS_2020"]},
    {"period": "2023", "metric": "offers", "value": 31, "rate_pct": 17, "outcome_type": "school-reported offers", "confidence": "P", "source_ids": ["FB140", "FB146"]},
    {"period": "2024/25", "metric": "oxbridge_offers", "value": 39, "cohort": 156, "arithmetic_offer_cohort_ratio_pct": 25.0, "outcome_type": "offers", "confidence": "P/D", "note": "39 ÷ 156 = 25.0% arithmetically, but the source does not establish that prior-leaver inclusion matches the displayed cohort. The arithmetic ratio is labelled and is not promoted as an official offer rate; the former 21% is retired.", "source_ids": ["WIN_CURRENT_RESULTS_2025"]},
    {"period": "2024/25", "metric": "us_offers", "value": 50, "ivy_offers": 9, "ivy_league_plus_offers": 17, "outcome_type": "offers", "confidence": "P/CONFLICT", "note": "The dedicated results page's 50 controls. The official Sixth Form page carries 47 and remains a source variant.", "source_ids": ["WIN_CURRENT_RESULTS_2025", "WIN_CURRENT_SIXTH_FORM_2025"]},
    {"period": "2024/25", "metric": "us_offers_companion_page_variant", "value": 47, "outcome_type": "official companion-page offer variant", "confidence": "P/CONFLICT", "source_ids": ["WIN_CURRENT_SIXTH_FORM_2025"]},
    {"period": "2024/25", "metric": "uk_entrants_to_russell_group", "value": 90, "unit": "percent", "outcome_type": "UK entrant destinations", "confidence": "P", "source_ids": ["WIN_CURRENT_RESULTS_2025"]},
    {"period": "2024/25", "metric": "other_international_universities", "value": 5, "unit": "count", "outcome_type": "number of other international universities, not offers", "confidence": "P", "source_ids": ["WIN_CURRENT_RESULTS_2025"]},
    {"period": "2024/25", "metric": "oxford_choral_and_organ_scholarships", "value": 6, "unit": "count", "outcome_type": "scholarships", "confidence": "P", "source_ids": ["WIN_CURRENT_RESULTS_2025"]},
    {"period": "2026", "metric": "oxbridge_offers_initial", "value": 38, "outcome_type": "initial offers reported to date", "confidence": "P/PROVISIONAL", "publication_status": "Initial total published in spring 2026; later revisions remain possible", "note": "The official release says 38 Oxford and Cambridge offers 'to date'. It also names early US offers from Stanford, Yale, Columbia, Chicago and Duke but gives no US total, so no numerical US row is created.", "source_ids": ["WIN_OXBRIDGE_2026_INITIAL"]},
]


WINCHESTER_DESTINATION_DISTRIBUTIONS = [
    {
        "period": "2010-2019",
        "outcome_type": "final leaver destination distribution",
        "oxford_pct": 17,
        "cambridge_pct": 13,
        "ucl_pct": 8,
        "durham_pct": 8,
        "bristol_pct": 8,
        "imperial_pct": 6,
        "edinburgh_pct": 6,
        "north_america_pct": 4,
        "published_labels_total_pct": 99,
        "coverage_status": "selected named categories transcribed from the official rounded graphic",
        "confidence": "P",
        "note": "The source's complete rounded labels total 99%. Only the named categories recovered into this ledger are shown here; they are not resummed or renormalised.",
        "source_ids": ["WIN_DESTINATIONS_2010_2019_PDF"],
    },
    {
        "period": "2020",
        "outcome_type": "final leaver destination distribution",
        "durham_pct": 12,
        "cambridge_pct": 10,
        "bristol_pct": 9,
        "oxford_pct": 8,
        "exeter_pct": 7,
        "ucl_pct": 7,
        "imperial_pct": 7,
        "edinburgh_pct": 6,
        "usa_pct": 5,
        "published_labels_total_pct": 95,
        "coverage_status": "selected named categories transcribed from the official rounded graphic",
        "confidence": "P",
        "note": "The source's complete printed labels total 95%. The published values are retained exactly and are not renormalised.",
        "source_ids": ["WIN_DESTINATIONS_2020_PDF"],
    },
    {
        "period": "2021",
        "outcome_type": "final leaver destination distribution",
        "oxbridge_pct": 12,
        "rest_uk_pct": 59,
        "us_canada_pct": 10,
        "post_application_or_reapplication_pct": 16,
        "other_pct": 3,
        "published_labels_total_pct": 100,
        "coverage_status": "complete overall category graphic",
        "confidence": "P/CONFLICT",
        "note": "A separate component graphic reports Oxford 12% and Cambridge 5% while this official overall graphic says 12% Oxbridge. The component split is internally inconsistent and is not merged.",
        "source_ids": ["WIN_DESTINATIONS_2021_IMAGE"],
    },
    {
        "period": "2022",
        "outcome_type": "final leaver destination distribution",
        "oxford": 11,
        "cambridge": 7,
        "oxbridge_pct": 11,
        "rest_uk_pct": 55,
        "international_pct": 12,
        "post_application_or_reapplication_pct": 16,
        "other_pct": 6,
        "published_labels_total_pct": 100,
        "coverage_status": "complete overall categories plus exact UK-chart Oxbridge counts",
        "confidence": "P",
        "source_ids": ["WIN_DESTINATIONS_2022_UK_IMAGE", "WIN_DESTINATIONS_2022_OVERALL_IMAGE"],
    },
]


WINCHESTER_CORRECTIONS = [
    {
        "id": "C18",
        "school": "Winchester College",
        "metric": "Pre-U annual primary series",
        "period": "2012–2020",
        "old": "partial companion-led rows",
        "new": "direct official annual tables and signed-account headlines",
        "status": "primary_archive_lock",
        "source_refs": [
            "WIN_PREU_2012_PDF",
            "WIN_PREU_2013_PDF",
            "WIN_PREU_2014_PDF",
            "WIN_PREU_2015_ORIGINAL_PDF",
            "WIN_PREU_2017_PDF",
            "WIN_ACCOUNTS_2018",
            "WIN_PREU_2019_PDF",
            "WIN_ACCOUNTS_2020",
        ],
        "reason": "Direct annual evidence fills D1 and D1–M3 gaps, restores primary D1–M1 values and corrects 2019 D1–M2 to 92.6%.",
    },
    {
        "id": "C19",
        "school": "Winchester College",
        "metric": "A-level A and A–B series",
        "period": "2003–2009",
        "old": "2003 only: 559 entries and 73.2% A",
        "new": "official school seven-year table; 2003 controls at 506 entries, 75.9% A and 93.3% A–B",
        "status": "primary_school_table_controls",
        "source_refs": ["WIN_ALEVEL_2003_2009_SCHOOL", "WIN_ALEVEL_2003_TIMES"],
        "reason": "The school table is a complete later official series; the contemporary 559-entry population remains an explicit denominator conflict.",
    },
    {
        "id": "C20",
        "school": "Winchester College",
        "metric": "2021 mixed A-level/Pre-U result",
        "period": 2021,
        "old": "absent or liable to be appended to pure Pre-U",
        "new": "separate mixed-qualification TAG ruler",
        "status": "population_basis_split",
        "source_refs": ["WIN_MIXED_RESULTS_2021_PDF"],
        "reason": "The official 450-entry distribution combines qualifications and cannot extend either pure trend.",
    },
    {
        "id": "C21",
        "school": "Winchester College",
        "metric": "2024/25 US university offers",
        "period": "2024/25",
        "old": 47,
        "new": 50,
        "status": "dedicated_results_page_controls",
        "source_refs": ["WIN_CURRENT_RESULTS_2025", "WIN_CURRENT_SIXTH_FORM_2025"],
        "reason": "The dedicated Exam Results & Futures page is the controlling surface; the Sixth Form page's 47 remains a labelled official variant.",
    },
    {
        "id": "C22",
        "school": "Winchester College",
        "metric": "2024/25 Oxbridge offer rate",
        "period": "2024/25",
        "old": "21%",
        "new": "official count 39 and cohort 156; 25.0% arithmetic ratio labelled as unvalidated",
        "status": "unsupported_rate_retired",
        "source_refs": ["WIN_CURRENT_RESULTS_2025"],
        "reason": "The official page publishes no offer rate and does not explicitly guarantee identical prior-leaver treatment in numerator and cohort.",
    },
    {
        "id": "C23",
        "school": "Winchester College",
        "metric": "Pre-U D1–M2",
        "period": 2019,
        "old": 92.7,
        "new": 92.6,
        "status": "integer_reconciliation",
        "source_refs": ["WIN_PREU_2019_PDF"],
        "reason": "The official integer grade counts round to 92.6%; 92.7% is impossible over 476 entries.",
    },
    {
        "id": "C24",
        "school": "Winchester College",
        "metric": "university offers, admissions, matriculations and destinations",
        "period": "2000–2025",
        "old": "single heterogeneous destination-labelled ledger",
        "new": "outcome-typed historic-access ledger plus separate final-destination distributions",
        "status": "population_basis_split",
        "source_refs": ["FB140", "WIN_DESTINATIONS_2010_2019_PDF", "WIN_DESTINATIONS_2020_PDF", "WIN_DESTINATIONS_2021_IMAGE", "WIN_DESTINATIONS_2022_OVERALL_IMAGE"],
        "reason": "Offers and admissions are leading/selection outcomes; final destinations remain separately typed and published rounding is never normalised.",
    },
    {
        "id": "C25",
        "school": "Winchester College",
        "metric": "2026 Oxbridge offers",
        "period": 2026,
        "old": "not represented",
        "new": "38 initial offers reported to date",
        "status": "provisional_current_year_addition",
        "source_refs": ["WIN_OXBRIDGE_2026_INITIAL"],
        "reason": "The March 2026 first-party newsletter supplies a current annual count, explicitly labelled initial and provisional rather than a final destination outcome.",
    },
]


WINCHESTER_CONFLICTS = [
    {
        "id": "WC01",
        "school": "Winchester College",
        "period": 2003,
        "metric": "A-level entries and A share",
        "values": [
            {"entries": 506, "grade_a": 75.9, "source": "WIN_ALEVEL_2003_2009_SCHOOL", "basis": "official school seven-year table"},
            {"entries": 559, "grade_a": 73.2, "source": "WIN_ALEVEL_2003_TIMES", "basis": "contemporary ISC/Times population"},
        ],
        "treatment": "Display the complete school series; preserve the 559-entry population as a comparator and never average.",
    },
    {
        "id": "WC02",
        "school": "Winchester College",
        "period": 2018,
        "metric": "Oxbridge offers",
        "values": [
            {"value": 37, "source": "WIN_ACCOUNTS_2018", "basis": "signed accounts"},
            {"value": 36, "source": "FB146", "basis": "strict application ledger"},
        ],
        "treatment": "Keep both source populations explicitly labelled; neither is a final destination count.",
    },
    {
        "id": "WC03",
        "school": "Winchester College",
        "period": "2024/25",
        "metric": "US university offers",
        "values": [
            {"value": 50, "source": "WIN_CURRENT_RESULTS_2025", "basis": "dedicated Exam Results & Futures page"},
            {"value": 47, "source": "WIN_CURRENT_SIXTH_FORM_2025", "basis": "Sixth Form achievements page"},
        ],
        "treatment": "Display 50 on the controlling dedicated page basis and retain 47 as an official companion-page variant.",
    },
    {
        "id": "WC04",
        "school": "Winchester College",
        "period": "2024/25",
        "metric": "Oxbridge offers divided by cohort",
        "values": [{"offers": 39, "cohort": 156, "arithmetic_ratio_pct": 25.0}],
        "treatment": "Show the count and cohort. Label 25.0% only as arithmetic because the page does not define an official same-population offer rate; retire 21%.",
    },
    {
        "id": "WC05",
        "school": "Winchester College",
        "period": 2025,
        "metric": "A-level A*, A*–A and A*–B shares",
        "values": [
            {"value": [44.0, 75.0, 92.0], "source": "WIN_CURRENT_RESULTS_2025", "basis": "dedicated current results page; controlling"},
            {"value": [42.0, 74.0, 91.0], "source": "WIN_ALEVEL_2025_INITIAL", "basis": "initial 27 August 2025 school newsletter"},
        ],
        "treatment": "Display the dedicated current-page values and retain the earlier official newsletter headline as an explicitly superseded source version.",
    },
]


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
        "role": "first-party full institution table for 182 leavers and the school-reported 2009–10 combined Oxbridge-offer headline",
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
        "role": "first-party full institution table: 181 university-bound plus three other leavers; recovered through the archive's HTTP replay when its HTTPS replay failed",
    },
    "SPS_DEST_2016_PDF": {
        "id": "st-pauls-destinations-2016-pdf",
        "title": "St Paul’s School · Destination of St Paul’s leavers 2016",
        "url": "https://web.archive.org/web/20191115012525id_/https://www.stpaulsschool.org.uk/assets/img/banners/SPS-PROS_2017-18_WEB2-35.pdf",
        "role": "first-party final leaver table, correct as at 1 September 2017; printed total 190 but the itemized university-side rows reconcile to 189",
    },
    "SPS_DEST_2016_ENTRY_PAGE": {
        "id": "st-pauls-destinations-entry-year-2016-page",
        "title": "St Paul’s School · university destinations · 2016 starters and January 2017 offer headline",
        "url": "https://www.stpaulsschool.org.uk/university-destinations/",
        "role": "first-party calendar-entry-year snapshot: 189 university-bound pupils, including deferred and post-A-level entrants; 53 Oxbridge and source-category America 34; also reports an un-denominated early-January headline of 85 Oxford/Cambridge offers",
    },
    "SPS_DEST_2017_GAP": {
        "id": "st-pauls-destinations-2017-gap",
        "title": "St Paul’s School · Pauline university destinations · 2017 publication promise",
        "url": "https://web.archive.org/web/20181123223247id_/https://www.stpaulsschool.org.uk/st-pauls/news/academic-news/pauline-university-destinations",
        "role": "archived first-party page still promising a future 2017 list after its stated publication date and linking only the explicit 2016 table; no 2017 table was recovered",
    },
    "SPS_OLD_PAULINE_NEWS_AUTUMN_2018": {
        "id": "st-pauls-old-pauline-news-autumn-2018",
        "title": "The Old Pauline News · Autumn 2018",
        "url": "https://drive.google.com/file/d/1hfDkbODbCArk4YPhDRyJxNIt3bxpzL87/view",
        "role": "contemporaneous first-party magazine corroboration for the 2016 total 190, Oxbridge 53, abroad 31 and US/Ivy-equivalent 28; image-only and not used as an additional institution ledger",
    },
    "SPS_DEST_2018_PDF": {
        "id": "st-pauls-destinations-2018-pdf",
        "title": "St Paul’s School · 2018 university destinations",
        "url": "https://www.stpaulsschool.org.uk/wp-content/uploads/2019/11/2018-Leavers-Destinations-Nov-2019-1.pdf",
        "role": "first-party full institution table: 162 UK or college destinations plus 42 abroad",
    },
    "SPS_DEST_2019_PDF": {
        "id": "st-pauls-destinations-2019-pdf",
        "title": "St Paul’s School · Destination of St Paul’s leavers 2019",
        "url": "https://web.archive.org/web/20211203162243id_/https://www.stpaulsschool.org.uk/wp-content/uploads/2021/09/2019-Leavers-Destinations-for-website.pdf",
        "role": "first-party final table, correct as at 22 September 2020: 190 leavers, including 23 abroad; extraction was verified from the rendered/archived original because the live text layer is unusable",
    },
    "SPS_DEST_2020_PDF": {
        "id": "st-pauls-destinations-entry-year-2020-pdf",
        "title": "St Paul’s School · leavers starting university in 2020 · updated 26 May 2021",
        "url": "https://www.stpaulsschool.org.uk/wp-content/uploads/2021/05/2020-Leavers-Destinations-for-website-updated-May-2021.pdf",
        "role": "first-party university-entry-year table: 175 main plus 27 abroad; the later May update controls because the earlier February file is blank",
    },
    "SPS_DEST_2021_PDF": {
        "id": "st-pauls-destinations-entry-year-2021-pdf",
        "title": "St Paul’s School · leavers starting university in 2021",
        "url": "https://www.stpaulsschool.org.uk/wp-content/uploads/2022/03/2021-destinations-for-website-page-Feb-2022.pdf",
        "role": "first-party university-entry-year table, as at 17 February 2022: 127 main plus 31 abroad",
    },
    "SPS_DEST_2022_PDF": {
        "id": "st-pauls-destinations-2022-pdf",
        "title": "St Paul’s School · Destination of St Paul’s leavers 2022",
        "url": "https://www.stpaulsschool.org.uk/wp-content/uploads/2022/11/2022-Destinations-as-at-18-Oct-2022.pdf",
        "role": "first-party final November table, as at 18 October 2022: 180 main plus 39 abroad; the similarly named October upload is incomplete",
    },
    "SPS_DEST_2023_PDF": {
        "id": "st-pauls-destinations-2023-pdf",
        "title": "St Paul’s School · Destinations of St Paul’s Leavers 2023",
        "url": "https://www.stpaulsschool.org.uk/wp-content/uploads/2023/09/UPDATED-2023-Destinations-as-at-14-Sep-2023.pdf",
        "role": "first-party updated final table, as at 14 September 2023: 186 main plus 42 abroad",
    },
    "SPS_DEST_2024_PDF": {
        "id": "st-pauls-destinations-2024-pdf",
        "title": "St Paul’s School · Destinations of St Paul’s Leavers 2024",
        "url": "https://www.stpaulsschool.org.uk/wp-content/uploads/2024/09/2024-Destinations-as-at-25-Sept-2024.pdf",
        "role": "first-party year-labelled final table, as at 25 September 2024: 143 UK plus 32 abroad",
    },
    "SPS_DEST_2024_PROSPECTUS": {
        "id": "st-pauls-destinations-2024-prospectus-corroboration",
        "title": "St Paul’s School · Senior Prospectus 2025 · destination table",
        "url": "https://drive.google.com/file/d/1-z_4-loUqMzwcxyoWbvQ1hoyZ9WQ2o_a/view",
        "role": "first-party 175-place corroboration for the official 2024 table; the year-labelled PDF controls and corrects the prospectus's École Polytechnique/Switzerland labelling to EPFL",
    },
    "SPS_DEST_2025_PDF": {
        "id": "st-pauls-destinations-2025-pdf",
        "title": "St Paul’s School · 2025 university destinations",
        "url": "https://www.stpaulsschool.org.uk/wp-content/uploads/2025/09/2025-Leavers-Destinations-5-September-2025.pdf",
        "role": "first-party full institution table: 143 UK destinations plus 42 abroad",
    },
    "SPS_FIGURES_BIBLE_V14_6": {
        "id": "st-pauls-figures-bible-v14-6-audit",
        "title": "The Figures Bible · v14.6 Wayback Destination-Lock Edition",
        "url": "https://drive.google.com/file/d/1fbqTfC7PXb8Iuu3JL6_7hEh6Z5Fjqrlm/view",
        "role": "latest user research synthesis audited as non-controlling where its St Paul’s table mixes strict UCAS outcomes, destination totals and entry-year denominators",
    },
    "SPS_OXFORD_APPLY_CENTRE_2006_2025": {
        "id": "st-pauls-oxford-apply-centre-2006-2025",
        "title": "University of Oxford · undergraduate admissions by UCAS apply centre · 2006–25",
        "url": "https://drive.google.com/file/d/1D-PVS0ojpR34XOMQMqKAIBskysLq0XYd/view",
        "role": "collated primary Oxford apply-centre tables carrying exact applications, offers and accepts",
    },
    "SPS_CAMBRIDGE_APPLY_CENTRE_2009_2024": {
        "id": "st-pauls-cambridge-apply-centre-2009-2024",
        "title": "University of Cambridge · undergraduate admissions by UCAS apply centre · 2009–24",
        "url": "https://drive.google.com/file/d/1WAcavIhtHoRx74fMermLyIlqqPVU7es9/view",
        "role": "collated primary Cambridge apply-centre tables carrying exact applications, offers and acceptances",
    },
    "SPS_CAMBRIDGE_WORKBOOK_2013_2024": {
        "id": "st-pauls-cambridge-apply-centre-workbook-2013-2024",
        "title": "University of Cambridge · apply-centre workbook 2013–24 · St Paul’s centre 11815",
        "url": "https://docs.google.com/spreadsheets/d/17iHacOOTr3cip51QBPRxiAMDw2GI_-47/edit",
        "role": "connected primary workbook locking the disputed 2020, 2023 and 2024 Cambridge application, offer and acceptance rows",
    },
    "SPS_PAULINE_2024_OFFERS_VARIANT": {
        "id": "st-pauls-pauline-2024-cambridge-offer-variant",
        "title": "2025 Cycle Apply Centre Audit Memo · The Pauline 2023–24 p.30 variant",
        "url": "https://drive.google.com/file/d/1hg94-njPhuzy4J0k2tcBfdDMKFLNLxOD/view",
        "role": "audit trail for the school-magazine headline of 19 Cambridge offers (47 combined), retained as a timing/counting variant against the official strict 18 (46 combined)",
    },
    "SPS_CAMBRIDGE_APPLY_CENTRE_2025": {
        "id": "st-pauls-cambridge-apply-centre-2025",
        "title": "University of Cambridge · applications, offers and acceptances by UCAS apply centre · 2025",
        "url": "https://www.undergraduate.study.cam.ac.uk/sites/default/files/2026-05/undergraduate_admissions_by_apply_centre_2025_cycle.pdf",
        "role": "official Cambridge 2025 apply-centre table; St Paul’s centre 11815 is 63 applications, 22 offers and 19 acceptances",
    },
    "SPS_CAMBRIDGE_APPLY_CENTRE_2012_MISSING": {
        "id": "st-pauls-cambridge-apply-centre-2012-missing",
        "title": "University of Cambridge · apply-centre statistics · 2012 cycle · known archive gap",
        "url": "http://www.study.cam.ac.uk/undergraduate/apply/statistics/archive/undergraduate_admissions_by_apply_centre_2012_cycle.pdf",
        "role": "the original official school-level PDF is contemporaneously indexed but no accessible capture or St Paul’s row was recovered; no values are inferred",
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


def _ratio(numerator: int | None, denominator: int | None) -> float | None:
    if numerator is None or denominator in (None, 0):
        return None
    return round(numerator / denominator, 6)


def _oxbridge_cycle_row(
    cycle: int,
    oxford: tuple[int | None, int | None, int | None],
    cambridge: tuple[int | None, int | None, int | None],
    *,
    combined: tuple[int | None, int | None, int | None] | None = None,
    confidence: str = "P",
    note: str | None = None,
    source_ids: list[str],
) -> dict[str, object]:
    if combined is None and all(value is not None for value in oxford + cambridge):
        combined = tuple(
            int(oxford[index]) + int(cambridge[index])
            for index in range(3)
        )
    applications, offers, acceptances = combined or (None, None, None)
    return {
        "cycle": cycle,
        "population_type": "UCAS apply-centre admissions cycle",
        "applications": applications,
        "offers": offers,
        "acceptances": acceptances,
        "offer_rate": _ratio(offers, applications),
        "acceptance_rate": _ratio(acceptances, applications),
        "oxford": {
            "applications": oxford[0],
            "offers": oxford[1],
            "acceptances": oxford[2],
        },
        "cambridge": {
            "applications": cambridge[0],
            "offers": cambridge[1],
            "acceptances": cambridge[2],
        },
        "confidence": confidence,
        "basis": "Applications, offers and source-labelled accepts/acceptances from the same named UCAS cycle.",
        "note": note,
        "source_ids": source_ids,
    }


ST_PAULS_OXBRIDGE_CYCLE_HISTORY = [
    _oxbridge_cycle_row(
        2006, (57, 32, 32), (None, None, None), confidence="P_PARTIAL",
        note="Oxford exact; no matching Cambridge apply-centre row recovered.",
        source_ids=["SPS_OXFORD_APPLY_CENTRE_2006_2025"],
    ),
    _oxbridge_cycle_row(
        2007, (80, 41, 39), (None, None, None), confidence="P_PARTIAL",
        note="Oxford exact; no matching Cambridge apply-centre row recovered.",
        source_ids=["SPS_OXFORD_APPLY_CENTRE_2006_2025"],
    ),
    _oxbridge_cycle_row(
        2008, (63, 30, 28), (None, None, None), confidence="P_PARTIAL",
        note="Oxford exact; no matching Cambridge apply-centre row recovered.",
        source_ids=["SPS_OXFORD_APPLY_CENTRE_2006_2025"],
    ),
    _oxbridge_cycle_row(
        2009, (85, 42, 41), (44, 21, 20),
        source_ids=["SPS_OXFORD_APPLY_CENTRE_2006_2025", "SPS_CAMBRIDGE_APPLY_CENTRE_2009_2024"],
    ),
    _oxbridge_cycle_row(
        2010, (94, 43, 43), (None, 31, None), combined=(None, 74, None), confidence="P/R",
        note="The school-reported combined offer total is 74. Cambridge offers 31 is the transparent residual 74 minus Oxford 43; combined applications and acceptances are unavailable, so no rates are calculated.",
        source_ids=["SPS_OXFORD_APPLY_CENTRE_2006_2025", "SPS_DEST_2009_BOOKLET"],
    ),
    _oxbridge_cycle_row(
        2011, (68, 29, 28), (69, 32, 29),
        source_ids=["SPS_OXFORD_APPLY_CENTRE_2006_2025", "SPS_CAMBRIDGE_APPLY_CENTRE_2009_2024"],
    ),
    _oxbridge_cycle_row(
        2012, (87, 35, 30), (None, None, None), confidence="P_PARTIAL",
        note="Oxford exact; incomplete Cambridge evidence means the former untyped combined figure 55 is not used.",
        source_ids=["SPS_OXFORD_APPLY_CENTRE_2006_2025", "SPS_CAMBRIDGE_APPLY_CENTRE_2012_MISSING"],
    ),
    _oxbridge_cycle_row(
        2013, (67, 21, 20), (71, 39, 37),
        source_ids=["SPS_OXFORD_APPLY_CENTRE_2006_2025", "SPS_CAMBRIDGE_APPLY_CENTRE_2009_2024"],
    ),
    _oxbridge_cycle_row(
        2014, (88, 32, 29), (59, 28, 24),
        source_ids=["SPS_OXFORD_APPLY_CENTRE_2006_2025", "SPS_CAMBRIDGE_APPLY_CENTRE_2009_2024"],
    ),
    _oxbridge_cycle_row(
        2015, (66, 22, 22), (63, 30, 23),
        source_ids=["SPS_OXFORD_APPLY_CENTRE_2006_2025", "SPS_CAMBRIDGE_APPLY_CENTRE_2009_2024"],
    ),
    _oxbridge_cycle_row(
        2016, (91, 30, 29), (52, 24, 22),
        source_ids=["SPS_OXFORD_APPLY_CENTRE_2006_2025", "SPS_CAMBRIDGE_APPLY_CENTRE_2009_2024"],
    ),
    _oxbridge_cycle_row(
        2017, (98, 40, 37), (53, 32, 29),
        note="The strict final cycle row is 151/72/66. A contemporaneous school webpage reported an early-January combined offer headline of 85 without a denominator or matching final-cycle method; it is retained as a timing/counting variant and does not overwrite the strict row.",
        source_ids=["SPS_OXFORD_APPLY_CENTRE_2006_2025", "SPS_CAMBRIDGE_APPLY_CENTRE_2009_2024", "SPS_DEST_2016_ENTRY_PAGE"],
    ),
    _oxbridge_cycle_row(
        2018, (88, 38, 32), (57, 23, 18),
        note="The strict cycle acceptance total is 50; the separate final-destination total is 53.",
        source_ids=["SPS_OXFORD_APPLY_CENTRE_2006_2025", "SPS_CAMBRIDGE_APPLY_CENTRE_2009_2024"],
    ),
    _oxbridge_cycle_row(
        2019, (87, 31, 30), (63, 28, 22),
        source_ids=["SPS_OXFORD_APPLY_CENTRE_2006_2025", "SPS_CAMBRIDGE_APPLY_CENTRE_2009_2024"],
    ),
    _oxbridge_cycle_row(
        2020, (75, 26, 26), (60, 18, 17),
        note="Exact lower-level records give 135 combined applications; the convenience table's 126 is rejected.",
        source_ids=["SPS_OXFORD_APPLY_CENTRE_2006_2025", "SPS_CAMBRIDGE_APPLY_CENTRE_2009_2024", "SPS_CAMBRIDGE_WORKBOOK_2013_2024"],
    ),
    _oxbridge_cycle_row(
        2021, (97, 23, 23), (57, 17, 14),
        source_ids=["SPS_OXFORD_APPLY_CENTRE_2006_2025", "SPS_CAMBRIDGE_APPLY_CENTRE_2009_2024"],
    ),
    _oxbridge_cycle_row(
        2022, (76, 20, 20), (69, 22, 21),
        source_ids=["SPS_OXFORD_APPLY_CENTRE_2006_2025", "SPS_CAMBRIDGE_APPLY_CENTRE_2009_2024"],
    ),
    _oxbridge_cycle_row(
        2023, (85, 30, 29), (76, 23, 20),
        note="Exact lower-level records give 161/53/49; the convenience table's 151/53/52 is rejected.",
        source_ids=["SPS_OXFORD_APPLY_CENTRE_2006_2025", "SPS_CAMBRIDGE_APPLY_CENTRE_2009_2024", "SPS_CAMBRIDGE_WORKBOOK_2013_2024"],
    ),
    _oxbridge_cycle_row(
        2024, (73, 28, 25), (54, 18, 18),
        confidence="P_CONFLICT",
        note="The official strict row is 127 applications, 46 offers and 43 accepted outcomes. The Pauline 2023–24 reports 19 Cambridge and 47 combined offers; that +1 school-layer timing/counting variant is retained but does not overwrite the official apply-centre row.",
        source_ids=["SPS_OXFORD_APPLY_CENTRE_2006_2025", "SPS_CAMBRIDGE_APPLY_CENTRE_2009_2024", "SPS_CAMBRIDGE_WORKBOOK_2013_2024", "SPS_PAULINE_2024_OFFERS_VARIANT"],
    ),
    _oxbridge_cycle_row(
        2025, (85, 29, 27), (63, 22, 19),
        source_ids=["SPS_OXFORD_APPLY_CENTRE_2006_2025", "SPS_CAMBRIDGE_APPLY_CENTRE_2025"],
    ),
    _oxbridge_cycle_row(
        2026, (None, 35, None), (None, 30, None), combined=(None, 65, None), confidence="S_CURRENT",
        note="Current-cycle offers to date only; no same-cycle application denominator or accepted outcomes are yet held.",
        source_ids=["FB146"],
    ),
]


_DESTINATION_NUMERIC_FIELDS = (
    "leavers",
    "university_bound",
    "destination_total",
    "oxford",
    "cambridge",
    "oxbridge",
    "oxbridge_destination_rate",
    "oxbridge_destination_rate_university_bound",
    "oxbridge_destination_reported_rate",
    "us_universities",
    "us_destination_rate",
    "us_destination_rate_university_bound",
    "canada",
    "us_canada",
    "north_america",
    "north_america_destination_rate",
    "north_america_destination_rate_university_bound",
    "uk_universities",
    "uk_or_college",
    "europe",
    "asia",
    "other_international",
    "abroad",
    "abroad_destination_rate",
    "other",
)


_DESTINATION_GAP_NOTES = {
    2012: "The former figure 55 is untyped and is not presented as a final destination count.",
    2017: "No 2017 table was recovered. The school promised a full list for September 2018, but its archived November 2018 page still contained only the promise and linked the explicit 2016 table.",
    2020: "The exact 202-place table is titled for leavers starting university in calendar 2020; it is kept in the separate entry-year series rather than recast as a 2020 leaver cohort.",
    2021: "The exact 158-place table is titled for leavers starting university in calendar 2021; it is kept in the separate entry-year series rather than recast as a 2021 leaver cohort.",
}


_DESTINATION_OVERRIDES: dict[int, dict[str, object]] = {
    2005: {
        "leavers": 168,
        "destination_total": 168,
        "oxford": 36,
        "cambridge": 23,
        "oxbridge": 59,
        "oxbridge_destination_rate": _ratio(59, 168),
        "us_universities": 15,
        "us_destination_rate": _ratio(15, 168),
        "confidence": "S/P",
        "coverage_status": "Provisional source-attached totals; institution table not independently reopened",
        "basis": "Final leaver destinations, provisional secondary/primary-source lead.",
        "note": "The 15 US figure remains provisional because its underlying booklet has not been independently reopened.",
        "source_ids": ["FB146"],
    },
    2009: {
        "leavers": 182,
        "destination_total": 182,
        "oxford": 42,
        "cambridge": 23,
        "oxbridge": 65,
        "oxbridge_destination_rate": _ratio(65, 182),
        "us_universities": 21,
        "us_destination_rate": _ratio(21, 182),
        "canada": 1,
        "us_canada": 22,
        "north_america": 22,
        "north_america_destination_rate": _ratio(22, 182),
        "uk_universities": 160,
        "confidence": "P",
        "coverage_status": "Complete first-party institution table",
        "basis": "Final destinations of 182 leavers.",
        "source_ids": ["SPS_DEST_2009_BOOKLET"],
    },
    2011: {
        "leavers": 175,
        "destination_total": 175,
        "oxford": 43,
        "cambridge": 30,
        "oxbridge": 73,
        "oxbridge_destination_rate": _ratio(73, 175),
        "us_universities": 13,
        "us_destination_rate": _ratio(13, 175),
        "canada": 2,
        "us_canada": 15,
        "north_america": 15,
        "north_america_destination_rate": _ratio(15, 175),
        "uk_universities": 160,
        "confidence": "P",
        "coverage_status": "Complete first-party institution table",
        "basis": "Final destinations of 175 leavers.",
        "source_ids": ["SPS_DEST_2011_BOOKLET"],
    },
    2013: {
        "leavers": 174,
        "destination_total": 174,
        "oxford": 18,
        "cambridge": 32,
        "oxbridge": 50,
        "oxbridge_destination_rate": _ratio(50, 174),
        "us_universities": 24,
        "us_destination_rate": _ratio(24, 174),
        "canada": 1,
        "us_canada": 25,
        "north_america": 25,
        "north_america_destination_rate": _ratio(25, 174),
        "uk_universities": 144,
        "europe": 2,
        "other": 3,
        "confidence": "P",
        "coverage_status": "Complete first-party table; five destinations are published only as regional/other buckets",
        "basis": "Final destinations of 174 leavers.",
        "source_ids": ["SPS_DEST_2013_BOOKLET"],
    },
    2014: {
        "oxbridge": 56,
        "oxbridge_destination_reported_rate": 0.30,
        "north_america": 24,
        "ucl_imperial": 34,
        "medicine": 15,
        "confidence": "P",
        "coverage_status": "First-party category totals; exact cohort and strict US split unavailable",
        "basis": "Final destination categories; the school reports a rounded 30% Oxbridge share.",
        "note": "Do not back-calculate an exact denominator from the rounded 30%, and do not relabel North America 24 as strict US. Medicine 15 overlaps university categories and is not additive.",
        "source_ids": ["SPS_DEST_2014_PAGE"],
    },
    2015: {
        "leavers": 184,
        "university_bound": 181,
        "destination_total": 184,
        "oxford": 20,
        "cambridge": 21,
        "oxbridge": 41,
        "oxbridge_destination_rate": _ratio(41, 184),
        "oxbridge_destination_rate_university_bound": _ratio(41, 181),
        "us_universities": 23,
        "us_destination_rate": _ratio(23, 184),
        "us_destination_rate_university_bound": _ratio(23, 181),
        "canada": 5,
        "us_canada": 28,
        "north_america": 28,
        "north_america_destination_rate": _ratio(28, 184),
        "north_america_destination_rate_university_bound": _ratio(28, 181),
        "uk_universities": 153,
        "other": 3,
        "confidence": "P",
        "coverage_status": "Complete first-party institution and other-destination table",
        "basis": "184 leavers: 181 university-bound plus three other destinations.",
        "source_ids": ["SPS_DEST_2015_PROSPECTUS", "SPS_DEST_2015_PAGE"],
    },
    2016: {
        "leavers": 190,
        "destination_total": 190,
        "oxford": 31,
        "cambridge": 22,
        "oxbridge": 53,
        "oxbridge_destination_rate": _ratio(53, 190),
        "us_universities": 28,
        "us_destination_rate": _ratio(28, 190),
        "canada": 1,
        "us_canada": 29,
        "uk_or_college": 159,
        "europe": 1,
        "other_international": 2,
        "abroad": 31,
        "abroad_destination_rate": _ratio(31, 190),
        "confidence": "P_CONFLICT",
        "coverage_status": "Complete first-party table with a one-place source-side reconciliation gap",
        "basis": "Final destinations of 2016 leavers; printed control total 190.",
        "note": "The university-side rows add to 189 although the PDF prints total 190 in both the destination and course controls. The missing one place is retained as an explicit reconciliation gap. A separate 189-student calendar-entry-year snapshot is also preserved and must not be merged into this row.",
        "source_ids": ["SPS_DEST_2016_PDF", "SPS_OLD_PAULINE_NEWS_AUTUMN_2018"],
    },
    2017: {
        "confidence": "P_NEGATIVE",
        "coverage_status": "Official publication promised, but no 2017 table recovered from the later archived page",
        "basis": "Explicit evidence gap; the linked table is the 2016 cohort and is not substituted.",
        "source_ids": ["SPS_DEST_2017_GAP", "SPS_DEST_2016_PDF"],
    },
    2018: {
        "leavers": 204,
        "destination_total": 204,
        "oxford": 35,
        "cambridge": 18,
        "oxbridge": 53,
        "oxbridge_destination_rate": _ratio(53, 204),
        "us_universities": 37,
        "us_destination_rate": _ratio(37, 204),
        "canada": 4,
        "north_america": 41,
        "north_america_destination_rate": _ratio(41, 204),
        "uk_or_college": 162,
        "other_international": 1,
        "abroad": 42,
        "abroad_destination_rate": _ratio(42, 204),
        "confidence": "P",
        "coverage_status": "Complete first-party institution table",
        "basis": "Final destinations: 162 UK or college destinations plus 42 abroad.",
        "note": "CAE Oxford Aviation Academy is a separate destination and is not counted as University of Oxford.",
        "source_ids": ["SPS_DEST_2018_PDF"],
    },
    2019: {
        "leavers": 190,
        "destination_total": 190,
        "oxford": 26,
        "cambridge": 26,
        "oxbridge": 52,
        "oxbridge_destination_rate": _ratio(52, 190),
        "us_universities": 22,
        "us_destination_rate": _ratio(22, 190),
        "uk_or_college": 163,
        "other_international": 1,
        "abroad": 23,
        "abroad_destination_rate": _ratio(23, 190),
        "other": 4,
        "confidence": "P",
        "coverage_status": "Complete first-party table; three 'Other' destinations are not further typed",
        "basis": "Final destinations of 190 leavers: 163 named UK/main institutions, 23 abroad, three Other and one direct-employment destination.",
        "note": "The final Oxbridge destination count is 52, not the former secondary 49. The PDF's live text layer is unusable; values were verified from the rendered official/archived document.",
        "source_ids": ["SPS_DEST_2019_PDF"],
    },
    2020: {
        "confidence": "P_DIFFERENT_POPULATION",
        "coverage_status": "Exact calendar-entry-year table recovered; no same-year final leaver table asserted",
        "basis": "See the separate 2020 university-entry-year dataset; admissions-cycle offers are also separate.",
        "source_ids": ["SPS_DEST_2020_PDF"],
    },
    2021: {
        "confidence": "P_DIFFERENT_POPULATION",
        "coverage_status": "Exact calendar-entry-year table recovered; no same-year final leaver table asserted",
        "basis": "See the separate 2021 university-entry-year dataset; admissions-cycle offers are also separate.",
        "source_ids": ["SPS_DEST_2021_PDF"],
    },
    2022: {
        "leavers": 219,
        "university_bound": 219,
        "destination_total": 219,
        "oxford": 21,
        "cambridge": 20,
        "oxbridge": 41,
        "oxbridge_destination_rate": _ratio(41, 219),
        "us_universities": 34,
        "us_destination_rate": _ratio(34, 219),
        "canada": 3,
        "us_canada": 37,
        "uk_or_college": 180,
        "europe": 2,
        "abroad": 39,
        "abroad_destination_rate": _ratio(39, 219),
        "confidence": "P",
        "coverage_status": "Complete first-party institution table",
        "basis": "Final destinations of 219 leavers: 180 UK/main plus 39 abroad.",
        "note": "The November final upload controls; the similarly named October upload is incomplete. The list gives 41 final Oxbridge destinations, not the unsupported 51.",
        "source_ids": ["SPS_DEST_2022_PDF"],
    },
    2023: {
        "leavers": 228,
        "university_bound": 228,
        "destination_total": 228,
        "oxford": 29,
        "cambridge": 21,
        "oxbridge": 50,
        "oxbridge_destination_rate": _ratio(50, 228),
        "us_universities": 35,
        "us_destination_rate": _ratio(35, 228),
        "canada": 1,
        "us_canada": 36,
        "uk_or_college": 186,
        "europe": 6,
        "abroad": 42,
        "abroad_destination_rate": _ratio(42, 228),
        "confidence": "P",
        "coverage_status": "Complete first-party institution table",
        "basis": "Final destinations of 228 leavers: 186 UK/main plus 42 abroad.",
        "note": "This source establishes 50 final Oxbridge destinations. It does not overwrite the separate 2023 admissions-cycle figures of 53 offers and 49 accepted outcomes.",
        "source_ids": ["SPS_DEST_2023_PDF"],
    },
    2024: {
        "population_type": "leaver-year final destinations",
        "leavers": 175,
        "university_bound": 175,
        "destination_total": 175,
        "oxford": 24,
        "cambridge": 16,
        "oxbridge": 40,
        "oxbridge_destination_rate": _ratio(40, 175),
        "us_universities": 22,
        "us_destination_rate": _ratio(22, 175),
        "uk_universities": 143,
        "europe": 9,
        "asia": 1,
        "other_international": 10,
        "abroad": 32,
        "abroad_destination_rate": _ratio(32, 175),
        "confidence": "P",
        "coverage_status": "Complete first-party year-labelled institution table",
        "basis": "Final destinations of 175 leavers: 143 UK plus 32 abroad.",
        "note": "The official year-labelled PDF supersedes the earlier prospectus-timing inference. Source labels are retained where they appear mistaken, with normalisation notes in the institution ledger.",
        "source_ids": ["SPS_DEST_2024_PDF", "SPS_DEST_2024_PROSPECTUS"],
    },
    2025: {
        "leavers": 185,
        "university_bound": 185,
        "destination_total": 185,
        "oxford": 21,
        "cambridge": 17,
        "oxbridge": 38,
        "oxbridge_destination_rate": _ratio(38, 185),
        "us_universities": 33,
        "us_destination_rate": _ratio(33, 185),
        "canada": 1,
        "north_america": 34,
        "north_america_destination_rate": _ratio(34, 185),
        "uk_universities": 143,
        "europe": 7,
        "asia": 1,
        "abroad": 42,
        "abroad_destination_rate": _ratio(42, 185),
        "confidence": "P_CONFLICT",
        "coverage_status": "Complete first-party institution table; narrative subset conflict retained",
        "basis": "Final destinations of 185 leavers: 143 UK plus 42 abroad.",
        "note": "The itemized USA institutions sum to 33. A current school narrative says 32 at 'top American universities', which is treated as a subset/headline rather than overwriting the complete list. The source course-column total 144 is also a typo; the institution column reconciles 143 + 42 = 185.",
        "source_ids": ["SPS_DEST_2025_PDF"],
    },
}


ST_PAULS_DESTINATION_HISTORY: list[dict[str, object]] = []
for _year in range(1990, 2026):
    _row: dict[str, object] = {
        "year": _year,
        "population_type": "leaver-year final destinations",
        **{field: None for field in _DESTINATION_NUMERIC_FIELDS},
        "confidence": "MISSING",
        "coverage_status": "No exact final-destination table recovered",
        "basis": "Final places taken up, where evidenced; never admissions-cycle offers.",
        "note": _DESTINATION_GAP_NOTES.get(_year),
        "source_ids": [],
    }
    _row.update(_DESTINATION_OVERRIDES.get(_year, {}))
    ST_PAULS_DESTINATION_HISTORY.append(_row)


ST_PAULS_UNIVERSITY_ENTRY_HISTORY = [
    {
        "year": 2016,
        "population_type": "university-entry year, including deferred and post-A-level entrants",
        "destination_total": 189,
        "oxbridge_entry_count": 53,
        "oxbridge_entry_rate": _ratio(53, 189),
        "america": 34,
        "america_entry_rate": _ratio(34, 189),
        "confidence": "P",
        "basis": "Students starting university in calendar 2016; not a same-year leaver cohort.",
        "note": "The source category is America, not strict USA, and is therefore not merged with the US-only destination series.",
        "source_ids": ["SPS_DEST_2016_ENTRY_PAGE", "FB146"],
    },
    {
        "year": 2020,
        "population_type": "university-entry year, potentially mixing school-leaver cohorts",
        "destination_total": 202,
        "uk_or_college": 175,
        "oxford_entry_count": 27,
        "cambridge_entry_count": 16,
        "oxbridge_entry_count": 43,
        "oxbridge_entry_rate": _ratio(43, 202),
        "us_universities": 24,
        "us_entry_rate": _ratio(24, 202),
        "europe": 3,
        "abroad": 27,
        "abroad_entry_rate": _ratio(27, 202),
        "confidence": "P",
        "basis": "St Paul’s leavers starting university in calendar 2020; not asserted to be the summer-2020 leaver cohort.",
        "note": "The exact 43 Oxbridge places happen to equal the strict admissions-cycle accepted-outcome total, but the population and measurement are different and remain separate.",
        "source_ids": ["SPS_DEST_2020_PDF"],
    },
    {
        "year": 2021,
        "population_type": "university-entry year, potentially mixing school-leaver cohorts",
        "destination_total": 158,
        "uk_or_college": 127,
        "oxford_entry_count": 18,
        "cambridge_entry_count": 12,
        "oxbridge_entry_count": 30,
        "oxbridge_entry_rate": _ratio(30, 158),
        "us_universities": 27,
        "us_entry_rate": _ratio(27, 158),
        "canada": 3,
        "europe": 1,
        "abroad": 31,
        "abroad_entry_rate": _ratio(31, 158),
        "confidence": "P",
        "basis": "St Paul’s leavers starting university in calendar 2021; not asserted to be the summer-2021 leaver cohort.",
        "note": "The 30 final entry-year Oxbridge places are not the 2021-cycle 40 offers or 37 accepted outcomes.",
        "source_ids": ["SPS_DEST_2021_PDF"],
    },
]


def _institution_rows(
    groups: list[tuple[str, str | None, list[tuple]]],
    source_id: str,
    total: int,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for region, country, destinations in groups:
        for item in destinations:
            destination, count = item[0], item[1]
            row_type = item[2] if len(item) > 2 else "institution"
            note = item[3] if len(item) > 3 else None
            additional_source_ids = item[4] if len(item) > 4 else []
            rows.append(
                {
                    "destination": destination,
                    "country": country,
                    "region": region,
                    "count": count,
                    "row_type": row_type,
                    "additive": True,
                    "note": note,
                    "source_ids": [source_id, *additional_source_ids],
                }
            )
    rows.append(
        {
            "destination": "TOTAL",
            "country": None,
            "region": "All destinations",
            "count": total,
            "row_type": "aggregate_total",
            "additive": False,
            "note": "Control total; excluded from additive reconciliation.",
            "source_ids": [source_id],
        }
    )
    return rows


def _destination_dataset(
    year: int,
    source_id: str,
    groups: list[tuple[str, str | None, list[tuple]]],
    total: int,
    *,
    basis: str,
    notes: str | None = None,
    suffix: str = "by_university",
    additional_source_ids: list[str] | None = None,
) -> dict[str, object]:
    source_ids = [source_id, *(additional_source_ids or [])]
    return {
        "dataset_id": f"st_pauls_destinations_{year}_{suffix}",
        "school": "St Paul's School",
        "domain": "university_destinations",
        "period": str(year),
        "basis": basis,
        "source_refs": source_ids,
        "notes": notes,
        "rows": _institution_rows(groups, source_id, total),
    }


ST_PAULS_DESTINATION_DETAIL_DATASETS = [
    _destination_dataset(
        2009,
        "SPS_DEST_2009_BOOKLET",
        [
            ("UK", "United Kingdom", [
                ("University of Oxford", 42), ("University of Cambridge", 23), ("Durham University", 15),
                ("University of Bristol", 13), ("Imperial College London", 9), ("University of Nottingham", 8),
                ("University of Edinburgh", 7), ("University of Warwick", 7), ("London School of Economics", 6),
                ("University of Manchester", 5), ("University of Leeds", 4), ("University College London", 3),
                ("King's College London", 3), ("University of Southampton", 3), ("University of Bath", 3),
                ("University of York", 1), ("SOAS University of London", 1), ("Newcastle University", 1),
                ("Other UK universities", 6, "unresolved_bucket"),
            ]),
            ("USA", "USA", [
                ("Columbia University", 1), ("Cornell University", 2), ("Georgetown University", 3),
                ("Harvard University", 3), ("Johns Hopkins University", 1), ("Kenyon College", 1),
                ("New York University", 1), ("Princeton University", 5), ("Tufts University", 2),
                ("University of California, Los Angeles", 1), ("Yale University", 1),
            ]),
            ("Canada", "Canada", [("McGill University", 1)]),
        ],
        182,
        basis="Complete final destination table for 182 leavers; strict USA 21 and Canada 1 remain separate.",
        suffix="complete_by_university",
    ),
    _destination_dataset(
        2011,
        "SPS_DEST_2011_BOOKLET",
        [
            ("UK", "United Kingdom", [
                ("University of Oxford", 43), ("University of Cambridge", 30), ("University of Bristol", 14),
                ("Durham University", 11), ("University College London", 10), ("University of Warwick", 6),
                ("University of Nottingham", 5), ("University of Edinburgh", 5), ("London School of Economics", 5),
                ("King's College London", 5), ("Imperial College London", 3), ("University of Leeds", 2),
                ("University of Southampton", 2), ("University of York", 2), ("University of Liverpool", 2),
                ("University of Exeter", 2), ("University of Birmingham", 2), ("Queen Mary University of London", 2),
                ("University of Sheffield", 2), ("University of St Andrews", 2), ("University of Manchester", 1),
                ("Newcastle University", 1), ("Bournemouth University", 1),
                ("Other UK universities", 2, "unresolved_bucket"),
            ]),
            ("USA", "USA", [
                ("Columbia University", 1), ("Georgetown University", 1), ("Harvard University", 1),
                ("Princeton University", 2), ("Brown University", 1), ("Duke University", 3),
                ("University of Pennsylvania", 2), ("Stanford University", 2),
            ]),
            ("Canada", "Canada", [("McGill University", 2)]),
        ],
        175,
        basis="Complete final destination table for 175 leavers; strict USA 13 and Canada 2 remain separate.",
    ),
    _destination_dataset(
        2013,
        "SPS_DEST_2013_BOOKLET",
        [
            ("UK", "United Kingdom", [
                ("University of Bath", 1), ("University of Birmingham", 1), ("Bournemouth University", 1),
                ("University of Bristol", 12), ("University of Cambridge", 32), ("City University London", 1),
                ("Durham University", 17), ("University of East Anglia", 1), ("University of Edinburgh", 7),
                ("University of Exeter", 4), ("University of Glasgow", 1), ("Hull York Medical School", 1),
                ("Imperial College London", 13), ("King's College London", 5), ("University of Leeds", 2),
                ("London School of Economics", 4), ("University of Manchester", 3), ("University of Nottingham", 3),
                ("University of Oxford", 18), ("University of Sheffield", 2), ("University of Southampton", 3),
                ("University of St Andrews", 1), ("St George's, University of London", 1),
                ("University College London", 4), ("University of Warwick", 4), ("University of York", 2),
            ]),
            ("USA", "USA", [
                ("Boston University", 1), ("Dartmouth College", 1), ("Emory University", 1), ("Duke University", 2),
                ("Georgetown University", 1), ("Harvard University", 2), ("University of Michigan", 1),
                ("New York University", 1), ("Princeton University", 1), ("Stanford University", 2),
                ("Swarthmore College", 1), ("Syracuse University", 1), ("Tufts University", 1),
                ("University of Chicago", 1), ("University of Pennsylvania", 3), ("University of Virginia", 2),
                ("Wheaton College", 1), ("Williams College", 1),
            ]),
            ("Canada", "Canada", [("McGill University", 1)]),
            ("Europe", None, [("Europe · institutions not published", 2, "unresolved_bucket")]),
            ("Other", None, [("Other destinations · not published", 3, "unresolved_bucket")]),
        ],
        174,
        basis="Complete 174-leaver reconciliation; five places are published only as Europe/Other buckets.",
    ),
    _destination_dataset(
        2015,
        "SPS_DEST_2015_PROSPECTUS",
        [
            ("UK", "United Kingdom", [
                ("University of Bath", 2), ("University of Bristol", 20), ("University of Cambridge", 21),
                ("Durham University", 9), ("University of Edinburgh", 7), ("University of Exeter", 5),
                ("Imperial College London", 7), ("King's College London", 4), ("University of Leicester", 1),
                ("London School of Economics", 6), ("University of Manchester", 5), ("University of Nottingham", 7),
                ("University of Oxford", 20),
                ("Queen Mary University of London", 3, "institution", "The prospectus prints two; the school webpage resolves one further place from its five-place Other bucket.", ["SPS_DEST_2015_PAGE"]),
                ("Queen's University Belfast", 1), ("Royal College of Music", 1),
                ("SOAS University of London", 1, "institution", "Resolved by the school webpage from the prospectus's five-place Other bucket.", ["SPS_DEST_2015_PAGE"]),
                ("University of St Andrews", 3), ("St George's, University of London", 3), ("University of Sussex", 1),
                ("Swansea University", 2), ("University College London", 6), ("University of Warwick", 12),
                ("University of York", 6),
            ]),
            ("USA", "USA", [
                ("Brown University", 2), ("Cornell University", 1), ("Georgetown University", 1),
                ("Harvard University", 2), ("New York University", 2), ("Northwestern University", 1),
                ("University of Notre Dame", 1), ("Stanford University", 1),
                ("University of California, Berkeley", 2), ("University of California, Los Angeles", 1),
                ("University of Chicago", 3), ("University of Michigan", 1), ("University of Pennsylvania", 1),
                ("University of Southern California", 1), ("Yale University", 3),
            ]),
            ("Canada", "Canada", [("McGill University", 5)]),
            ("Other", None, [
                ("Professional rugby · London Scottish 1st XV", 1, "other_destination"),
                ("Sports coach at St Paul's School", 1, "other_destination"),
                ("May apply for 2017 university entry", 1, "other_destination"),
            ]),
        ],
        184,
        basis="Complete table: 153 UK + 23 USA + 5 Canada + 3 other destinations = 184 leavers.",
        notes="USA-only 23 is derived transparently from the itemized list; the published North America headline is 28. The raw prospectus prints Queen Mary 2, no SOAS and Other 5; the separate school webpage resolves two of those places as Queen Mary +1 and SOAS 1, leaving the three named non-university destinations.",
        additional_source_ids=["SPS_DEST_2015_PAGE"],
    ),
    _destination_dataset(
        2016,
        "SPS_DEST_2016_PDF",
        [
            ("UK/main", "United Kingdom", [
                ("Brighton & Sussex Medical School", 1), ("University of Bristol", 21),
                ("University of Cambridge", 22), ("Cardiff University", 1), ("City University London", 1),
                ("Durham University", 20), ("University of Edinburgh", 6), ("University of Glasgow", 1),
                ("Imperial College London", 5), ("King's College London", 4), ("University of Leeds", 1),
                ("London School of Economics", 5), ("Loughborough University", 2),
                ("University of Manchester", 1), ("University of Oxford", 31),
                ("Queen Mary University of London", 1), ("Regent's University London", 1),
                ("SOAS University of London", 1), ("University of Southampton", 2),
                ("University of Sussex", 1), ("University College London", 20), ("University of Warwick", 6),
                ("Other · institution not published", 4, "unresolved_bucket"),
                ("Unresolved one-place source reconciliation gap", 1, "reconciliation_gap", "Derived transparently from the printed total 190 minus 189 itemized places; no institution is assigned."),
            ]),
            ("USA", "USA", [
                ("Brown University", 3), ("California Institute of Technology", 1),
                ("University of Chicago", 1), ("Colgate University", 1), ("Columbia University", 4),
                ("Cornell University", 1), ("Duke University", 1), ("Georgetown University", 1),
                ("Harvard University", 1), ("Johns Hopkins University", 1), ("Princeton University", 3),
                ("Stanford University", 1), ("Tufts University", 1),
                ("University of California, Los Angeles", 1), ("University of Pennsylvania", 4),
                ("Wesleyan University", 1), ("Yale University", 2),
            ]),
            ("Canada", "Canada", [("McGill University", 1)]),
            ("Europe", "France", [("École Supérieure des Arts et Techniques de la Mode", 1)]),
            ("Other international", "Mexico", [("Instituto Tecnológico Autónomo de México", 1)]),
        ],
        190,
        basis="Final destinations of 2016 leavers; the source prints total 190 but its itemized rows add to 189.",
        notes="The one-place reconciliation gap is shown as a derived unresolved row and is not assigned to a university. This table is separate from the 189-student calendar-entry-year snapshot.",
        additional_source_ids=["SPS_OLD_PAULINE_NEWS_AUTUMN_2018"],
    ),
    _destination_dataset(
        2018,
        "SPS_DEST_2018_PDF",
        [
            ("UK or college", "United Kingdom", [
                ("Anglia Ruskin University", 1), ("University of Bath", 1), ("University of Birmingham", 1),
                ("University of Brighton", 1), ("University of Bristol", 13), ("CAE Oxford Aviation Academy", 1),
                ("University of Cambridge", 18), ("Cardiff University", 1), ("Durham University", 9),
                ("University of East Anglia", 2), ("University of Edinburgh", 12), ("University of Exeter", 10),
                ("University of Gloucestershire", 1), ("Imperial College London", 11), ("King's College London", 3),
                ("University of Leeds", 1), ("London School of Economics", 4), ("University of Manchester", 4),
                ("Newcastle University", 2), ("University of Oxford", 35), ("Royal Holloway, University of London", 2),
                ("University of Southampton", 1), ("University of St Andrews", 1),
                ("St George's, University of London", 1), ("University College London", 14),
                ("University of the Arts London, Camberwell, then Newcastle", 1), ("University of Warwick", 7),
                ("University of York", 4),
            ]),
            ("USA", "USA", [
                ("Brown University", 2), ("Columbia University", 2), ("Cornell University", 1),
                ("Dartmouth College", 2), ("Davidson College", 1), ("Duke University", 2),
                ("Georgetown University", 1), ("Harvard University", 4), ("Johns Hopkins University", 1),
                ("New York University", 1), ("Northwestern University", 1), ("Princeton University", 2),
                ("Stanford University", 2), ("Tufts University", 1), ("University of California, Berkeley", 1),
                ("University of California, Los Angeles", 3), ("University of Chicago", 4),
                ("University of Pennsylvania", 2), ("University of Southern California", 1),
                ("Wesleyan University", 1), ("Yale University", 2),
            ]),
            ("Canada", "Canada", [("McGill University", 3), ("University of Toronto", 1)]),
            ("Other abroad", "Malta", [("Queen Mary University of London · Malta Campus", 1)]),
        ],
        204,
        basis="Complete final destination table: 162 UK or college destinations plus 42 abroad.",
        notes="CAE Oxford Aviation Academy is not University of Oxford and is excluded from the Oxbridge count.",
    ),
    _destination_dataset(
        2019,
        "SPS_DEST_2019_PDF",
        [
            ("UK/main", "United Kingdom", [
                ("University of Bath", 2), ("University of Bristol", 14), ("University of Cambridge", 26),
                ("City, University of London", 1), ("Durham University", 15), ("University of East Anglia", 2),
                ("University of Edinburgh", 13), ("University of Exeter", 6),
                ("Guildhall School of Music & Drama", 1), ("Imperial College London", 14),
                ("King's College London", 8), ("Kingston University", 1), ("University of Leeds", 1),
                ("University of Leicester", 1), ("University of Liverpool", 1),
                ("London School of Economics", 3), ("University of Manchester", 1),
                ("University of Nottingham", 2), ("University of Oxford", 26),
                ("Queen Mary University of London", 1),
                ("Royal Academy of Music, University of London · scholarship", 1),
                ("University of Sheffield", 1), ("University of St Andrews", 2),
                ("University College London", 13), ("University of Warwick", 5), ("University of York", 2),
            ]),
            ("Other", None, [
                ("Other · destination not published", 3, "unresolved_bucket"),
                ("Direct employment · theatre production", 1, "other_destination"),
            ]),
            ("USA", "USA", [
                ("Brown University", 2), ("Columbia University", 3), ("Duke University", 1),
                ("Harvard University", 2), ("University of Notre Dame", 1), ("Princeton University", 1),
                ("Rice University", 1), ("Stanford University", 1),
                ("University of California, Los Angeles", 1), ("University of Chicago", 3),
                ("New York University", 1, "institution", "The source prints 'University of New York (NYU)'; normalized here to the institution's name."),
                ("University of Pennsylvania", 1), ("University of Virginia", 1), ("Yale University", 3),
            ]),
            ("Other abroad", "Malta", [("Queen Mary University of London · Malta Campus", 1)]),
        ],
        190,
        basis="Complete final destination table: 163 named UK/main institutions, 23 abroad, three Other and one direct-employment destination.",
        notes="The itemized list establishes 52 Oxbridge and 22 strict-USA destinations. The rendered/archived original controls extraction because the live PDF has an unusable text layer.",
    ),
    _destination_dataset(
        2020,
        "SPS_DEST_2020_PDF",
        [
            ("UK/main", "United Kingdom", [
                ("University of Bristol", 15), ("University of Cambridge", 16), ("University of Dundee", 1),
                ("Durham University", 21), ("University of East Anglia", 1), ("University of Edinburgh", 14),
                ("University of Exeter", 3), ("Guildhall School of Music & Drama", 1),
                ("Imperial College London", 12), ("King's College London", 6), ("University of Leeds", 1),
                ("University of Leicester", 1), ("London School of Economics", 9),
                ("University of Manchester", 4), ("Newcastle University", 2),
                ("University of Nottingham", 2), ("University of Oxford", 27),
                ("Queen Mary University of London", 1), ("University of Sheffield", 1),
                ("University of St Andrews", 2), ("University College London", 25),
                ("University of Warwick", 7), ("University of York", 3),
            ]),
            ("USA", "USA", [
                ("Brown University", 1), ("Columbia University", 2), ("Georgetown University", 1),
                ("Harvard University", 1), ("Massachusetts Institute of Technology", 2),
                ("New York University", 1), ("Princeton University", 1), ("Stanford University", 2),
                ("University of California, Berkeley", 1), ("University of California, Los Angeles", 1),
                ("University of Chicago", 4), ("University of Pennsylvania", 2),
                ("University of Virginia", 1), ("Williams College", 3), ("Yale University", 1),
            ]),
            ("Europe", "France", [("Sciences Po, Paris", 1), ("Sciences Po, Reims", 1)]),
            ("Europe", "Italy", [("Bocconi University, Milan", 1)]),
        ],
        202,
        basis="University-entry-year population: 175 main plus 27 abroad; may include earlier school leavers after gap years or deferments.",
        notes="The May 2021 update controls because the earlier February PDF is blank. Do not merge these places with the 2020 admissions-cycle accepted outcomes.",
        suffix="entry_year_by_university",
    ),
    _destination_dataset(
        2021,
        "SPS_DEST_2021_PDF",
        [
            ("UK/main", "United Kingdom", [
                ("University of Bath", 3), ("University of Bristol", 10), ("University of Cambridge", 12),
                ("Cardiff University", 1), ("Durham University", 12), ("University of East Anglia", 1),
                ("University of Edinburgh", 16), ("University of Exeter", 6),
                ("Imperial College London", 11), ("King's College London", 1),
                ("London School of Economics", 8), ("Loughborough University", 1),
                ("University of Manchester", 2), ("Newcastle University", 1),
                ("University of Nottingham", 1), ("University of Oxford", 18),
                ("Queen Mary University of London", 2), ("University of Southampton", 1),
                ("University College London", 11), ("University of Warwick", 9),
            ]),
            ("USA", "USA", [
                ("Bates College", 1), ("Boston University", 1), ("Brown University", 1),
                ("Carnegie Mellon University", 1), ("University of Chicago", 4), ("Columbia University", 3),
                ("Duke University", 1), ("Harvard University", 3),
                ("Massachusetts Institute of Technology", 1), ("Middlebury College", 1),
                ("University of Pennsylvania", 3), ("University of Southern California", 1),
                ("Stanford University", 1), ("Tufts University", 1),
                ("University of California, Berkeley", 1), ("University of California, Los Angeles", 1),
                ("Yale University", 2),
            ]),
            ("Canada", "Canada", [("Queen's University", 1), ("University of Toronto", 2)]),
            ("Europe", "Italy", [("Bocconi University", 1)]),
        ],
        158,
        basis="University-entry-year population: 127 main plus 31 abroad; may include earlier school leavers after gap years or deferments.",
        notes="The exact 30 Oxbridge entry-year places are separate from the 2021 admissions-cycle 40 offers and 37 accepted outcomes.",
        suffix="entry_year_by_university",
    ),
    _destination_dataset(
        2022,
        "SPS_DEST_2022_PDF",
        [
            ("UK/main", "United Kingdom", [
                ("Aston University", 1), ("Central Saint Martins", 2), ("Durham University", 15),
                ("Glasgow School of Art", 1), ("Imperial College London", 22),
                ("King's College London", 5), ("London School of Economics", 14),
                ("Royal Veterinary College", 1), ("University College London", 10),
                ("University of Bath", 4), ("University of Birmingham", 2), ("University of Bristol", 14),
                ("University of Cambridge", 20), ("University of Edinburgh", 15), ("University of Exeter", 3),
                ("University of Leeds", 4), ("University of Leicester", 1),
                ("University of Manchester", 4), ("Newcastle University", 5),
                ("University of Nottingham", 2), ("University of Oxford", 21),
                ("University of Southampton", 2), ("University of St Andrews", 2),
                ("Swansea University", 1), ("University of Warwick", 6), ("University of York", 3),
            ]),
            ("USA", "USA", [
                ("Amherst College", 1), ("Babson College", 1), ("Berklee College of Music", 1),
                ("Brown University", 4), ("Dartmouth College", 1), ("Duke University", 2),
                ("Hamilton College", 1), ("Johns Hopkins University", 1),
                ("Northwestern University", 2), ("Stanford University", 4),
                ("University of California, Los Angeles", 2, "institution", "Combined from two differently worded UCLA rows in the source."),
                ("University of California, Santa Barbara", 1), ("University of California, Berkeley", 1),
                ("University of Chicago", 3), ("Columbia University", 2),
                ("University of Pennsylvania", 1), ("University of Southern California", 1),
                ("University of Notre Dame", 1), ("Yale University", 3), ("United States Naval Academy", 1),
            ]),
            ("Canada", "Canada", [
                ("McGill University", 1), ("Queen's University, Ontario", 1),
                ("University of British Columbia", 1),
            ]),
            ("Europe", "Italy", [("Bocconi University", 2)]),
        ],
        219,
        basis="Complete final destination table: 180 UK/main plus 39 abroad.",
        notes="The November final upload controls. The itemized list establishes 41 final Oxbridge and 34 strict-USA destinations.",
    ),
    _destination_dataset(
        2023,
        "SPS_DEST_2023_PDF",
        [
            ("UK/main", "United Kingdom", [
                ("City & Guilds of London Art School", 1), ("Durham University", 10),
                ("Glasgow School of Art", 1), ("Imperial College London", 23),
                ("King's College London", 4), ("London School of Economics", 12),
                ("Royal Veterinary College", 1), ("Queen Mary University of London", 2),
                ("St George's, University of London", 2), ("University College London", 21),
                ("University of Bath", 4), ("University of Bristol", 13), ("University of Cambridge", 21),
                ("Cardiff University", 1), ("University of Edinburgh", 17), ("University of Exeter", 3),
                ("University of Leeds", 3), ("University of Liverpool", 1),
                ("University of Manchester", 1), ("University of Nottingham", 1),
                ("University of Oxford", 29), ("University of Southampton", 2),
                ("University of St Andrews", 2), ("University of Surrey", 2),
                ("University of Warwick", 8), ("University of York", 1),
            ]),
            ("USA", "USA", [
                ("Brown University", 3), ("Columbia University", 5), ("Cornell University", 2),
                ("Dartmouth College", 1), ("Georgetown University", 3), ("Harvard University", 1),
                ("Princeton University", 2), ("Stanford University", 1),
                ("University of California, Berkeley", 3), ("University of California, Los Angeles", 1),
                ("University of Chicago", 3), ("University of Pennsylvania", 1),
                ("University of Southern California", 2), ("University of Notre Dame", 1),
                ("University of Virginia", 2), ("Yale University", 4),
            ]),
            ("Canada", "Canada", [("McGill University", 1)]),
            ("Europe", "France", [("École Polytechnique", 1)]),
            ("Europe", "Italy", [("Bocconi University", 4)]),
            ("Europe", "Ireland", [("Trinity College Dublin", 1)]),
        ],
        228,
        basis="Complete final destination table: 186 UK/main plus 42 abroad.",
        notes="The itemized list establishes 50 final Oxbridge and 35 strict-USA destinations; admissions-cycle offers and accepted outcomes remain in their separate dataset.",
    ),
    _destination_dataset(
        2024,
        "SPS_DEST_2024_PDF",
        [
            ("UK-wide", "United Kingdom", [
                ("University of Edinburgh", 12), ("University of Bristol", 11), ("Durham University", 10),
                ("University of Warwick", 9), ("University of Exeter", 5), ("Newcastle University", 2),
                ("Loughborough University", 1), ("University of Birmingham", 1), ("University of East Anglia", 1),
                ("University of Glasgow", 1), ("University of Leeds", 1), ("University of Liverpool", 1),
                ("University of Manchester", 1), ("University of Nottingham", 1), ("University of Southampton", 1),
                ("University of York", 1),
            ]),
            ("London", "United Kingdom", [
                ("Imperial College London", 20), ("University College London", 14), ("King's College London", 5),
                ("London School of Economics", 3), ("Queen Mary University of London", 2),
            ]),
            ("Oxbridge", "United Kingdom", [("University of Cambridge", 16), ("University of Oxford", 24)]),
            ("USA", "USA", [
                ("Brown University", 3), ("University of Chicago", 3), ("Stanford University", 3),
                ("University of Pennsylvania", 3), ("Yale University", 3),
                ("Boston University", 1, "institution", "The source prints 'University of Boston'; normalized to the institution's name."),
                ("Duke University", 1), ("Georgetown University", 1), ("Harvard University", 1),
                ("University of California, Berkeley", 1), ("University of Southern California", 1),
                ("Williams College", 1, "institution", "The source prints 'Williams University'; normalized to the institution's name."),
            ]),
            ("Non-US international", None, [
                ("Bocconi University, Milan", 4), ("Eindhoven University of Technology", 1),
                ("Sciences Po / Columbia University Dual BA", 1, "institution", "The school classifies this dual degree outside the USA category."),
                ("École Polytechnique Fédérale de Lausanne", 1),
                ("Trinity College Dublin", 1),
                ("Trinity College Dublin / Columbia University Dual BA", 1, "institution", "The school classifies this dual degree outside the USA category."),
                ("University of Hong Kong", 1),
            ]),
        ],
        175,
        basis="Complete final destination table: 143 UK plus 32 abroad = 175 leavers.",
        notes="The official year-labelled PDF supersedes the former prospectus inference. EPFL is retained as the actual institution rather than the different École Polytechnique.",
    ),
    _destination_dataset(
        2025,
        "SPS_DEST_2025_PDF",
        [
            ("UK", "United Kingdom", [
                ("City St George's, University of London", 1), ("Durham University", 14), ("Falmouth University", 1),
                ("Imperial College London", 19), ("King's College London", 7), ("London School of Economics", 8),
                ("Loughborough University", 1), ("Queen Mary University of London", 1),
                ("University College London", 12), ("University of Bath", 1), ("University of Bristol", 5),
                ("University of Cambridge", 17), ("University of Edinburgh", 14), ("University of Exeter", 2),
                ("University of Manchester", 1), ("University of Oxford", 21), ("University of Sheffield", 1),
                ("University of Southampton", 2), ("University of St Andrews", 3), ("University of Warwick", 12),
            ]),
            ("USA", "USA", [
                ("Brown University", 2), ("Carnegie Mellon University", 1), ("Cornell University", 1),
                ("Dartmouth College", 3), ("Duke University", 1), ("Georgetown University", 3),
                ("Harvard University", 3), ("Massachusetts Institute of Technology", 1), ("Princeton University", 1),
                ("Stanford University", 1), ("University of California, San Diego", 1),
                ("University of California, Los Angeles", 1), ("University of Chicago", 6), ("Columbia University", 1),
                ("University of Michigan", 1), ("University of Pennsylvania", 1),
                ("University of North Carolina", 1), ("University of Washington", 1), ("Yale University", 3),
            ]),
            ("Canada", "Canada", [("McGill University", 1)]),
            ("Europe", "Italy", [("Bocconi University, Milan", 6)]),
            ("Europe", "Ireland", [("Trinity College Dublin", 1)]),
            ("Asia", "South Korea", [("Korea Advanced Institute of Science and Technology", 1)]),
        ],
        185,
        basis="Complete final destination table: 143 UK plus 42 abroad = 185.",
        notes="The institution list gives 33 USA destinations. The current narrative's 32 'top American universities' is retained as a narrower headline conflict, not used to overwrite the list.",
    ),
]


ST_PAULS_DESTINATION_DATASET = {
    "dataset_id": "st_pauls_destinations",
    "school": "St Paul's School",
    "domain": "university_destinations",
    "basis": "1990–2025 final-destination coverage spine; blank years are explicit gaps and never filled with admissions-cycle offers",
    "source_refs": [
        "FB146",
        "SPS_DEST_2009_BOOKLET",
        "SPS_DEST_2011_BOOKLET",
        "SPS_DEST_2013_BOOKLET",
        "SPS_DEST_2014_PAGE",
        "SPS_DEST_2015_PROSPECTUS",
        "SPS_DEST_2015_PAGE",
        "SPS_DEST_2016_PDF",
        "SPS_OLD_PAULINE_NEWS_AUTUMN_2018",
        "SPS_DEST_2017_GAP",
        "SPS_DEST_2018_PDF",
        "SPS_DEST_2019_PDF",
        "SPS_DEST_2022_PDF",
        "SPS_DEST_2023_PDF",
        "SPS_DEST_2024_PDF",
        "SPS_DEST_2024_PROSPECTUS",
        "SPS_DEST_2025_PDF",
    ],
    "notes": "Percentages always retain their matching denominator. US, US & Canada, North America, America and abroad are separate fields.",
    "rows": ST_PAULS_DESTINATION_HISTORY,
}


ST_PAULS_ADDITIONAL_DESTINATION_DATASETS = [
    {
        "dataset_id": "st_pauls_oxbridge_cycle_overview",
        "school": "St Paul's School",
        "domain": "university_admissions",
        "basis": "same-cycle UCAS apply-centre applications, offers and accepted/admitted outcomes; distinct from final destinations",
        "source_refs": [
            "SPS_OXFORD_APPLY_CENTRE_2006_2025",
            "SPS_CAMBRIDGE_APPLY_CENTRE_2009_2024",
            "SPS_CAMBRIDGE_WORKBOOK_2013_2024",
            "SPS_CAMBRIDGE_APPLY_CENTRE_2025",
            "SPS_CAMBRIDGE_APPLY_CENTRE_2012_MISSING",
            "SPS_PAULINE_2024_OFFERS_VARIANT",
            "SPS_DEST_2016_ENTRY_PAGE",
            "SPS_DEST_2009_BOOKLET",
            "FB146",
        ],
        "notes": "Combined percentages are calculated only when both university application denominators are complete.",
        "rows": ST_PAULS_OXBRIDGE_CYCLE_HISTORY,
    },
    {
        "dataset_id": "st_pauls_university_entry_year_destinations",
        "school": "St Paul's School",
        "domain": "university_destinations",
        "basis": "university-entry year rather than leaver year; kept separate to prevent population mixing",
        "source_refs": ["SPS_DEST_2016_ENTRY_PAGE", "FB146", "SPS_DEST_2020_PDF", "SPS_DEST_2021_PDF"],
        "notes": "The 2016 snapshot retains the source category America. The 2020 and 2021 rows carry strict-USA counts from complete itemized tables. None is silently recast as a same-year summer-leaver cohort.",
        "rows": ST_PAULS_UNIVERSITY_ENTRY_HISTORY,
    },
    *ST_PAULS_DESTINATION_DETAIL_DATASETS,
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
        "population_type:{label:`Population basis`,kind:`text`},"
        "coverage_status:{label:`Coverage status`,kind:`text`},"
        "destination_total:{label:`Destination-list denominator`,kind:`count`},"
        "university_bound:{label:`University-bound leavers`,kind:`count`},"
        "uk_universities:{label:`UK universities`,kind:`count`},"
        "uk_or_college:{label:`UK university / college destinations`,kind:`count`},"
        "us_universities:{label:`US universities`,kind:`count`},"
        "canada:{label:`Canada`,kind:`count`},"
        "us_canada:{label:`US & Canada`,kind:`count`},"
        "north_america:{label:`North America`,kind:`count`},"
        "asia:{label:`Asia`,kind:`count`},"
        "other_international:{label:`Other international`,kind:`count`},"
        "america:{label:`America · source category`,kind:`count`},"
        "oxbridge_destination_rate:{label:`Oxbridge / matching destination cohort`,kind:`rate`},"
        "oxbridge_destination_rate_university_bound:{label:`Oxbridge / university-bound`,kind:`rate`},"
        "oxbridge_destination_reported_rate:{label:`Published Oxbridge share · rounded`,kind:`rate`},"
        "us_destination_rate:{label:`US / matching destination cohort`,kind:`rate`},"
        "us_destination_rate_university_bound:{label:`US / university-bound`,kind:`rate`},"
        "north_america_destination_rate:{label:`North America / matching destination cohort`,kind:`rate`},"
        "north_america_destination_rate_university_bound:{label:`North America / university-bound`,kind:`rate`},"
        "abroad_destination_rate:{label:`Abroad / matching destination cohort`,kind:`rate`},"
        "oxford_entry_count:{label:`Oxford / university-entry-year total`,kind:`count`},"
        "cambridge_entry_count:{label:`Cambridge / university-entry-year total`,kind:`count`},"
        "oxbridge_entry_count:{label:`Oxbridge entrants`,kind:`count`},"
        "oxbridge_entry_rate:{label:`Oxbridge / university-entry-year total`,kind:`rate`},"
        "america_entry_rate:{label:`America / university-entry-year total`,kind:`rate`},"
        "us_entry_rate:{label:`US / university-entry-year total`,kind:`rate`},"
        "abroad_entry_rate:{label:`Abroad / university-entry-year total`,kind:`rate`},"
        "row_type:{label:`Row type`,kind:`text`},"
        "additive:{label:`Included in total`,kind:`boolean`},"
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

    old_destination_dataset = (
        "{dataset_id:`st_pauls_destinations`,school:`St Paul's School`,domain:`university_destinations`,"
        "basis:`final leaver destination basis; never substitute for strict acceptances`,source_refs:[`FB13`,`FB146`],"
        "notes:null,rows:["
        "{year:2005,leavers:168,oxford:36,cambridge:23,oxbridge:59,basis:`P Annual Information`},"
        "{year:2009,leavers:182,oxford:42,cambridge:23,oxbridge:65,basis:`P Annual Information`},"
        "{year:2011,leavers:175,oxford:43,cambridge:30,oxbridge:73,basis:`P Annual Information`},"
        "{year:2012,leavers:null,oxford:null,cambridge:null,oxbridge:55,basis:`S external`},"
        "{year:2013,leavers:174,oxford:18,cambridge:32,oxbridge:50,basis:`P Annual Information`},"
        "{year:2014,leavers:null,oxford:null,cambridge:null,oxbridge:56,basis:`P school news`},"
        "{year:2015,leavers:null,oxford:null,cambridge:null,oxbridge:49,basis:`S external`},"
        "{year:2016,leavers:190,oxford:null,cambridge:null,oxbridge:53,basis:`P school news`},"
        "{year:2017,leavers:null,oxford:null,cambridge:null,oxbridge:51,basis:`S external`},"
        "{year:2018,leavers:204,oxford:35,cambridge:18,oxbridge:53,basis:`D PDF; 162 UK list +42 abroad`},"
        "{year:2019,leavers:null,oxford:null,cambridge:null,oxbridge:49,basis:`S external`},"
        "{year:2020,leavers:null,oxford:null,cambridge:null,oxbridge:44,basis:`S external`},"
        "{year:2021,leavers:null,oxford:null,cambridge:null,oxbridge:47,basis:`S external`},"
        "{year:2022,leavers:null,oxford:null,cambridge:null,oxbridge:51,basis:`S external`},"
        "{year:2023,leavers:null,oxford:null,cambridge:null,oxbridge:54,basis:`S external`},"
        "{year:2025,leavers:185,oxford:21,cambridge:17,oxbridge:38,basis:`D PDF; 20.5%`}]}"
    )
    destination_datasets = [
        ST_PAULS_DESTINATION_DATASET,
        *ST_PAULS_ADDITIONAL_DESTINATION_DATASETS,
    ]
    javascript = _replace_once(
        javascript,
        old_destination_dataset,
        ",".join(_compact_json(dataset) for dataset in destination_datasets),
        "St Paul’s source-faithful university destination datasets",
    )

    destination_label_anchor = "st_pauls_destinations:`Final leaver destinations`,kcs_offer_layer:"
    destination_labels = (
        "st_pauls_destinations:`Final destinations · 1990–2025 coverage spine`,"
        "st_pauls_oxbridge_cycle_overview:`Oxbridge applications, offers & acceptances · 2006–26`,"
        "st_pauls_university_entry_year_destinations:`University-entry-year destinations · 2016, 2020 & 2021`,"
        "st_pauls_destinations_2009_complete_by_university:`2009 destinations · all institutions in one ledger`,"
        "st_pauls_destinations_2011_by_university:`2011 destinations · all institutions`,"
        "st_pauls_destinations_2013_by_university:`2013 destinations · all published institutions and buckets`,"
        "st_pauls_destinations_2015_by_university:`2015 destinations · all institutions and other outcomes`,"
        "st_pauls_destinations_2016_by_university:`2016 destinations · all institutions plus source reconciliation gap`,"
        "st_pauls_destinations_2018_by_university:`2018 destinations · all institutions`,"
        "st_pauls_destinations_2019_by_university:`2019 destinations · all institutions and other outcomes`,"
        "st_pauls_destinations_2020_entry_year_by_university:`2020 university-entry-year destinations · all institutions`,"
        "st_pauls_destinations_2021_entry_year_by_university:`2021 university-entry-year destinations · all institutions`,"
        "st_pauls_destinations_2022_by_university:`2022 destinations · all institutions`,"
        "st_pauls_destinations_2023_by_university:`2023 destinations · all institutions`,"
        "st_pauls_destinations_2024_by_university:`2024 destinations · all institutions`,"
        "st_pauls_destinations_2025_by_university:`2025 destinations · all institutions`,"
        "kcs_offer_layer:"
    )
    javascript = _replace_once(
        javascript,
        destination_label_anchor,
        destination_labels,
        "St Paul’s destination dataset labels",
    )

    javascript = _replace_once(
        javascript,
        "{id:`C12`,school:`St Paul's Girls' School`,metric:`2025 A-level A*–A`,period:2025,old:null,new:88.7,status:`resolved_later_official_sheet`,source_refs:[`SPGS_2025_ALEVEL_SHEET`],reason:`The later official provisional subject-grade sheet supplies the previously uncaptured band.`}",
        "{id:`C12`,school:`St Paul's Girls' School`,metric:`2025 A-level A*–A`,period:2025,old:null,new:88.7,status:`resolved_later_official_sheet`,source_refs:[`SPGS_2025_ALEVEL_SHEET`],reason:`The later official provisional subject-grade sheet supplies the previously uncaptured band.`},{id:`C13`,school:`St Paul's School`,metric:`GCSE final primary ladder`,period:`2005–2009`,old:`missing or P/S`,new:`direct school five-year grid`,status:`primary_archive_lock`,source_refs:[`SPS_GCSE_2005_2009_WAYBACK`],reason:`The archived first-party rolling table supplies all three final cumulative bands.`},{id:`C14`,school:`St Paul's School`,metric:`2015 final Oxbridge destinations`,period:2015,old:49,new:41,status:`primary_prospectus_controls`,source_refs:[`SPS_DEST_2015_PROSPECTUS`,`SPS_DEST_2015_PAGE`],reason:`The full school table gives Oxford 20 plus Cambridge 21; 49 was secondary and is rejected.`},{id:`C15`,school:`St Paul's School`,metric:`Oxbridge offers, accepted outcomes and destinations`,period:`2009–2024`,old:`single mixed-population table in Figures Bible v14.6`,new:`strict UCAS-cycle and destination/entry-year datasets separated`,status:`population_basis_split`,source_refs:[`SPS_FIGURES_BIBLE_V14_6`,`SPS_OXFORD_APPLY_CENTRE_2006_2025`,`SPS_CAMBRIDGE_APPLY_CENTRE_2009_2024`,`SPS_DEST_2020_PDF`,`SPS_DEST_2021_PDF`,`SPS_DEST_2023_PDF`],reason:`The Bible still mixes strict UCAS outcomes with destination counts and calendar-entry-year denominators. Primary apply-centre rows control: 2020 is 135/44/43 and 2023 is 161/53/49; final destinations remain separately 43 and 50.`},{id:`C16`,school:`St Paul's School`,metric:`2024 final destinations`,period:2024,old:`175-place prospectus table marked inferred`,new:`official year-labelled 175-place PDF`,status:`primary_year_lock`,source_refs:[`SPS_DEST_2024_PDF`],reason:`The official PDF explicitly identifies the 2024 leavers and upgrades the row from D/R to P; it also identifies EPFL rather than École Polytechnique.`},{id:`C17`,school:`St Paul's School`,metric:`2016 final destination total`,period:2016,old:`189 itemized university-side places`,new:`printed control total 190 with one explicit unresolved gap`,status:`source_internal_conflict`,source_refs:[`SPS_DEST_2016_PDF`],reason:`Both printed total controls are 190, while the itemized destination rows add to 189. The missing place is shown as unresolved and is not assigned to an institution.`}",
        "St Paul’s correction ledger",
    )
    javascript = _replace_once(
        javascript,
        "{id:`WX06`,school:`Westminster School`,period:2004,metric:`A-level A`,values:[{value:83,source:`WEST_WAYBACK_RESULTS_1988_2009`,basis:`contemporaneous deep-spine capture`},{value:84,source:`WEST_WAYBACK_RESULTS_2010`,basis:`later redesigned school table`}],treatment:`Carry 83 from the contemporaneous school capture; retain 84 as a redesign-era conflict.`}",
        "{id:`WX06`,school:`Westminster School`,period:2004,metric:`A-level A`,values:[{value:83,source:`WEST_WAYBACK_RESULTS_1988_2009`,basis:`contemporaneous deep-spine capture`},{value:84,source:`WEST_WAYBACK_RESULTS_2010`,basis:`later redesigned school table`}],treatment:`Carry 83 from the contemporaneous school capture; retain 84 as a redesign-era conflict.`},{id:`SP01`,school:`St Paul's School`,period:2006,metric:`A-level A / A–B / A–C`,values:[{value:[85,97.7,98.6],source:`SPS_ALEVEL_2005_2009_WAYBACK`,basis:`school final rolling table`},{value:[82.31,97.2,98.6],source:`SPS_ALEVEL_2006_ISC`,basis:`ISC raw counts 470 A, 85 B and 8 C from 571 entries`}],treatment:`Display the school final grid in the headline series; retain the ISC population as an explicit denominator conflict and do not average.`}",
        "St Paul’s A-level 2006 conflict ledger",
    )

    historic_exam_row_delta = (len(ST_PAULS_GCSE_HISTORY) - 1) + (len(ST_PAULS_ALEVEL_HISTORY) - 1)
    destination_row_delta = len(ST_PAULS_DESTINATION_HISTORY) - 16
    added_dataset_rows = sum(
        len(dataset["rows"])
        for dataset in ST_PAULS_ADDITIONAL_DESTINATION_DATASETS
    )
    final_dataset_count = 45 + len(ST_PAULS_ADDITIONAL_DESTINATION_DATASETS)
    final_row_count = 555 + historic_exam_row_delta + destination_row_delta + added_dataset_rows
    javascript = _replace_once(
        javascript,
        "datasets:45,rows:555",
        f"datasets:{final_dataset_count},rows:{final_row_count}",
        "scope row count",
    )
    return javascript


def apply_winchester_history(javascript: str) -> str:
    javascript = _replace_once(
        javascript,
        "Evidence snapshot · 30 Aug 2026",
        "Evidence snapshot · 2 Sep 2026",
        "evidence snapshot date after Winchester audit",
    )
    javascript = _replace_once(
        javascript,
        "id:`winchester`,name:`Winchester College`,short:`Winchester`,applyCentreName:`Winchester College`,usName:`Winchester College`,accent:`#2563eb`,evidenceWindow:`2009–2026`",
        "id:`winchester`,name:`Winchester College`,short:`Winchester`,applyCentreName:`Winchester College`,usName:`Winchester College`,accent:`#2563eb`,evidenceWindow:`1994–2026`",
        "Winchester evidence window",
    )

    source_anchor = '"WIN_2026_RESULTS_HUB":'
    source_entries = _compact_json(WINCHESTER_SOURCES)[1:-1] + ","
    javascript = _replace_once(
        javascript,
        source_anchor,
        source_entries + source_anchor,
        "Winchester source catalogue",
    )

    javascript = _replace_once(
        javascript,
        "other_top_us_offers:{label:`Other named US offers`,kind:`count`},us_offers_min:",
        "other_top_us_offers:{label:`Other named US offers`,kind:`count`},"
        "ivy_league_plus_offers:{label:`Ivy League Plus offers`,kind:`count`},"
        "other_international_universities:{label:`Other international universities`,kind:`count`},"
        "us_offers_min:",
        "Winchester current-offer field catalogue",
    )
    javascript = _replace_once(
        javascript,
        "u_count:{label:`U count`,kind:`count`},x_count:",
        "u_count:{label:`U count`,kind:`count`},"
        "d1_count:{label:`D1 count · reconstructed`,kind:`count`},"
        "d2_count:{label:`D2 count · reconstructed`,kind:`count`},"
        "d3_count:{label:`D3 count · reconstructed`,kind:`count`},"
        "m1_m3_count:{label:`M1–M3 count · reconstructed`,kind:`count`},"
        "p1_p3_count:{label:`P1–P3 count · reconstructed`,kind:`count`},"
        "unclassified_residual:{label:`Unclassified residual`,kind:`count`},"
        "x_count:",
        "Winchester recovered-count field catalogue",
    )
    javascript = _replace_once(
        javascript,
        "rate_pct:{label:`Rate`,kind:`percent`},rate_approx_pct:",
        "rate_pct:{label:`Rate`,kind:`percent`},"
        "arithmetic_offer_cohort_ratio_pct:{label:`Arithmetic offers ÷ cohort · not an official rate`,kind:`percent`},"
        "published_labels_total_pct:{label:`Printed labels total`,kind:`percent`},"
        "oxford_pct:{label:`Oxford`,kind:`percent`},"
        "cambridge_pct:{label:`Cambridge`,kind:`percent`},"
        "oxbridge_pct:{label:`Oxbridge`,kind:`percent`},"
        "ucl_pct:{label:`UCL`,kind:`percent`},"
        "durham_pct:{label:`Durham`,kind:`percent`},"
        "bristol_pct:{label:`Bristol`,kind:`percent`},"
        "imperial_pct:{label:`Imperial`,kind:`percent`},"
        "edinburgh_pct:{label:`Edinburgh`,kind:`percent`},"
        "exeter_pct:{label:`Exeter`,kind:`percent`},"
        "north_america_pct:{label:`North America`,kind:`percent`},"
        "usa_pct:{label:`USA`,kind:`percent`},"
        "rest_uk_pct:{label:`Rest of UK`,kind:`percent`},"
        "us_canada_pct:{label:`USA / Canada`,kind:`percent`},"
        "international_pct:{label:`International`,kind:`percent`},"
        "post_application_or_reapplication_pct:{label:`Post-application / reapplication`,kind:`percent`},"
        "other_pct:{label:`Other`,kind:`percent`},"
        "rate_approx_pct:",
        "Winchester destination-distribution field catalogue",
    )
    javascript = _replace_once(
        javascript,
        "coverage_status:{label:`Coverage status`,kind:`text`},destination_total:",
        "coverage_status:{label:`Coverage status`,kind:`text`},"
        "outcome_type:{label:`Outcome type`,kind:`text`},"
        "denominator_basis:{label:`Denominator basis`,kind:`text`},"
        "narrative_d1:{label:`Official D1 wording`,kind:`text`},"
        "narrative_d2_grade_itself:{label:`Official D2-grade wording`,kind:`text`},"
        "narrative_d1_d3:{label:`Official D1–D3 wording`,kind:`text`},"
        "destination_total:",
        "Winchester basis and narrative field catalogue",
    )

    pre_u_datasets = [
        {
            "dataset_id": "winchester_pre_u_two_ruler_2011_2019",
            "school": "Winchester College",
            "domain": "exam_results",
            "basis": "pure Cambridge Pre-U principal-grade entry distributions; exact annual tables, signed-account headlines and a narrative-only 2010 row kept distinct",
            "source_refs": [
                "WIN_PREU_2010_PAGE",
                "WIN_PREU_2011_PDF",
                "WIN_PREU_2012_PDF",
                "WIN_PREU_2013_PDF",
                "WIN_PREU_2014_PDF",
                "WIN_PREU_2015_ORIGINAL_PDF",
                "WIN_ACCOUNTS_2015",
                "WIN_PREU_2016_PAGE",
                "WIN_PREU_2017_PDF",
                "WIN_ACCOUNTS_2018",
                "WIN_PREU_2019_PDF",
                "WIN_ACCOUNTS_2020",
            ],
            "notes": "D1–D3 and D1–M1 remain distinct rulers. The 2020 CAG row is quarantined. Competing 2015, 2017 and 2019 source variants remain in the conflict register and are never averaged.",
            "rows": WINCHESTER_PRE_U_HISTORY,
        },
        {
            "dataset_id": "winchester_mixed_alevel_pre_u_2021",
            "school": "Winchester College",
            "domain": "exam_results",
            "basis": "school-published combined A-level and Cambridge Pre-U equivalence ruler",
            "source_refs": ["WIN_MIXED_RESULTS_2021_PDF"],
            "notes": "Teacher-assessed pandemic result; kept separate from the pure A-level and pure Pre-U series.",
            "rows": WINCHESTER_MIXED_RESULTS_2021,
        },
    ]
    javascript = _replace_dataset_once(
        javascript,
        "winchester_pre_u_two_ruler_2011_2019",
        pre_u_datasets,
        "Winchester primary Pre-U and mixed-qualification datasets",
        expected_rows=9,
        expected_signatures=(
            "entries:326,d1:25.2",
            "d1_m2:92.7,d1_m3:96.6",
        ),
    )

    alevel_dataset = {
        "dataset_id": "winchester_alevel",
        "school": "Winchester College",
        "domain": "exam_results",
        "basis": "official annual A-level grade-entry shares; pre-2010 rows use A and A–B, while modern rows use A*, A*–A and A*–B",
        "source_refs": [
            "WIN_ALEVEL_2003_2009_SCHOOL",
            "WIN_ALEVEL_2003_TIMES",
            "WIN_ALEVEL_2006_ISC",
            "FB146",
            "WIN_CURRENT_RESULTS_2025",
            "WIN_ALEVEL_2025_INITIAL",
        ],
        "notes": "The school 2003–09 series controls. Conflicting 2003 and 2006 populations remain explicit and are not merged with the controlling denominators.",
        "rows": WINCHESTER_ALEVEL_HISTORY,
    }
    javascript = _replace_dataset_once(
        javascript,
        "winchester_alevel",
        [alevel_dataset],
        "Winchester official A-level history",
        expected_rows=6,
        expected_signatures=(
            "entries:559,a_star:null,a_star_a:73.2",
            "publication_status:`Pending detailed publication — no exact 2026 A-level grade-entry bands",
        ),
    )

    destination_datasets = [
        {
            "dataset_id": "winchester_destination_and_historic_access",
            "school": "Winchester College",
            "domain": "university_destinations",
            "basis": "outcome-typed historic access, applications/admissions, offers, places and matriculations; not one continuous destination series",
            "source_refs": [
                "FB140",
                "FB146",
                "WIN_OXBRIDGE_GUARDIAN_2001_2006",
                "WIN_OXBRIDGE_SUTTON_2002_2008",
                "WIN_ANNUAL_REPORT_2008",
                "WIN_DESTINATIONS_2010_PAGE",
                "WIN_DESTINATIONS_2011_PAGE",
                "WIN_DESTINATIONS_2012_PAGE",
                "WIN_ACCOUNTS_2015",
                "WIN_ACCOUNTS_2018",
                "WIN_ACCOUNTS_2020",
                "WIN_CURRENT_RESULTS_2025",
                "WIN_CURRENT_SIXTH_FORM_2025",
                "WIN_OXBRIDGE_2026_INITIAL",
            ],
            "notes": "Every row states its outcome type. Forecasts, rolling aggregates, offers, admissions and final matriculations must not be compared as if they shared one population.",
            "rows": WINCHESTER_ACCESS_HISTORY,
        },
        {
            "dataset_id": "winchester_final_destination_distributions_2010_2022",
            "school": "Winchester College",
            "domain": "university_destinations",
            "basis": "official final-leaver destination distributions; rounded source labels retained without renormalisation",
            "source_refs": [
                "WIN_DESTINATIONS_2010_2019_PDF",
                "WIN_DESTINATIONS_2020_PDF",
                "WIN_DESTINATIONS_2021_IMAGE",
                "WIN_DESTINATIONS_2022_UK_IMAGE",
                "WIN_DESTINATIONS_2022_OVERALL_IMAGE",
            ],
            "notes": "2010–19 and 2020 rows transcribe the named categories recovered into the ledger and state their source-wide printed totals; 2021–22 overall category rows are complete. No row is renormalised.",
            "rows": WINCHESTER_DESTINATION_DISTRIBUTIONS,
        },
    ]
    javascript = _replace_dataset_once(
        javascript,
        "winchester_destination_and_historic_access",
        destination_datasets,
        "Winchester outcome-typed access and destination datasets",
        expected_rows=17,
        expected_signatures=(
            "period:`1836`,metric:`percent_of_leavers_to_oxbridge`",
            "period:`2025`,metric:`us_offers`,value:47",
        ),
    )

    javascript = _replace_once(
        javascript,
        "dataset_id:`winchester_gcse`,school:`Winchester College`,domain:`exam_results`,basis:`old scale and reformed 9–1 kept typed; top_equivalent=A* or 9–8; astar_a_equivalent=A*/A or 9–7; wider band only when grade 6/A*–B is held`,source_refs:[`FB139`,`FB139A`,`FB141`,`FB146`],notes:null",
        "dataset_id:`winchester_gcse`,school:`Winchester College`,domain:`exam_results`,basis:`annual grade-entry shares; legacy A*–G rows use A*, A*/A and A*–B, while reformed rows retain their published 9–1 crosswalk; missing cells remain null and the 2011–12 suppressed results use documented upper bounds rounded to one decimal`,source_refs:[`FB139`,`FB139A`,`FB141`,`FB146`,`WIN_GCSE_HMC_1997`,`WIN_GCSE_2006_ISC`,`WIN_GCSE_2011_DFE_GCSE`,`WIN_GCSE_2011_DFE_IGCSE`,`WIN_GCSE_2012_DFE`],notes:`A* was introduced at GCSE in 1994, which is the start of the historical ledger. Pupil-level five-grade thresholds and incomplete government subsets are never substituted for entry-grade bands.`",
        "Winchester GCSE dataset metadata",
    )

    old_gcse_start = "rows:[{year:2013,scale:`A*-G`,entries:null,grade_9:null,top_equivalent:61.1"
    new_gcse_start = (
        "rows:["
        + _compact_json(WINCHESTER_GCSE_HISTORY)[1:-1]
        + ",{year:2013,scale:`A*-G`,entries:null,grade_9:null,top_equivalent:61.1"
    )
    javascript = _replace_once(
        javascript,
        old_gcse_start,
        new_gcse_start,
        "Winchester GCSE history rows",
    )

    javascript = _replace_once(
        javascript,
        "e===`kcs_ib_hl`?o=`ib-hl`:e.includes(`pre_u`)||e===`westminster_pre_u`?o=`pre-u`:",
        "e===`kcs_ib_hl`?o=`ib-hl`:"
        "e===`winchester_mixed_alevel_pre_u_2021`?(o=`a-level-pre-u-crosswalk`,V(n,`a_star`,`a_star_equivalent`),V(n,`a_star_a`,`a_star_a_pre_u_equivalent`),V(n,`a_star_b`,`a_star_b_pre_u_equivalent`)):"
        "e.includes(`pre_u`)||e===`westminster_pre_u`?o=`pre-u`:",
        "Winchester 2021 mixed-qualification ruler",
    )

    javascript = _replace_once(
        javascript,
        "winchester_pre_u_two_ruler_2011_2019:`Pre-U grade distribution · two published rulers`,winchester_alevel:`A-level results`,winchester_gcse:",
        "winchester_pre_u_two_ruler_2011_2019:`Pre-U grade distribution · 2010–20 primary archive`,"
        "winchester_mixed_alevel_pre_u_2021:`Mixed A-level / Pre-U TAG ruler · 2021`,"
        "winchester_alevel:`A-level results · official 2003–09 and modern series`,"
        "winchester_gcse:",
        "Winchester examination dataset labels",
    )
    javascript = _replace_once(
        javascript,
        "winchester_destination_and_historic_access:`Destination and historic-access measures`,spgs_destinations:",
        "winchester_destination_and_historic_access:`Historic access, offers, places & matriculations · outcome typed`,"
        "winchester_final_destination_distributions_2010_2022:`Final destination distributions · published rounding retained`,"
        "spgs_destinations:",
        "Winchester university dataset labels",
    )

    javascript = _replace_once(
        javascript,
        "{id:`X03`,school:`Winchester College`,period:2015,metric:`Pre-U entries`,values:[{value:443,source:`FB139`},{value:444,source:`FB146`}],treatment:`Unresolved; show denominator conflict.`}",
        "{id:`X03`,school:`Winchester College`,period:2015,metric:`Pre-U entries and cumulative bands`,values:[{value:443,source:`WIN_PREU_2015_ORIGINAL_PDF`,basis:`complete original result table; controlling`},{value:444,source:`WIN_ACCOUNTS_2015`,basis:`later signed-accounts version; 99.4% pass is arithmetically impossible over this denominator`}],treatment:`Display the coherent 443-entry original table. Preserve the later 444-entry version as a conflict and never combine its rounded bands or pass claim with the original denominator.`}",
        "Winchester 2015 Pre-U conflict treatment",
    )

    correction_entries = _compact_json(WINCHESTER_CORRECTIONS)[1:-1]
    javascript = _replace_one_of_once(
        javascript,
        (
            (
                "}],Ss=[{id:`X01`",
                "}," + correction_entries + "],Ss=[{id:`X01`",
            ),
            (
                "}],xs=[{id:`X01`",
                "}," + correction_entries + "],xs=[{id:`X01`",
            ),
        ),
        "Winchester correction ledger additions",
    )
    conflict_entries = _compact_json(WINCHESTER_CONFLICTS)[1:-1]
    javascript = _replace_one_of_once(
        javascript,
        (
            (
                "}],Cs=[{phase:`legacy clean/standardised`",
                "}," + conflict_entries + "],Cs=[{phase:`legacy clean/standardised`",
            ),
            (
                "}],Ss=[{phase:`legacy clean/standardised`",
                "}," + conflict_entries + "],Ss=[{phase:`legacy clean/standardised`",
            ),
        ),
        "Winchester conflict ledger additions",
    )
    javascript = _replace_once(
        javascript,
        "`For Winchester 2017/2019 Pre-U D1–M1, primary raw-count variants and later league candidates must remain distinct.`",
        "`For Winchester 2015, keep the coherent 443-entry original Pre-U table separate from the later 444-entry accounts version. For 2017/2019 D1–M1, primary raw-count variants control and later league candidates remain distinct. Keep the 2021 mixed A-level/Pre-U TAG ruler out of both pure trends.`",
        "Winchester qualification-basis guardrail",
    )

    historic_exam_row_delta = (len(ST_PAULS_GCSE_HISTORY) - 1) + (len(ST_PAULS_ALEVEL_HISTORY) - 1)
    destination_row_delta = len(ST_PAULS_DESTINATION_HISTORY) - 16
    st_pauls_added_rows = sum(
        len(dataset["rows"])
        for dataset in ST_PAULS_ADDITIONAL_DESTINATION_DATASETS
    )
    st_pauls_dataset_count = 45 + len(ST_PAULS_ADDITIONAL_DESTINATION_DATASETS)
    st_pauls_row_count = 555 + historic_exam_row_delta + destination_row_delta + st_pauls_added_rows
    winchester_added_dataset_count = 2
    winchester_row_delta = (
        len(WINCHESTER_GCSE_HISTORY)
        + (len(WINCHESTER_PRE_U_HISTORY) - 9)
        + len(WINCHESTER_MIXED_RESULTS_2021)
        + (len(WINCHESTER_ALEVEL_HISTORY) - 6)
        + (len(WINCHESTER_ACCESS_HISTORY) - 17)
        + len(WINCHESTER_DESTINATION_DISTRIBUTIONS)
    )
    javascript = _replace_once(
        javascript,
        f"datasets:{st_pauls_dataset_count},rows:{st_pauls_row_count}",
        f"datasets:{st_pauls_dataset_count + winchester_added_dataset_count},rows:{st_pauls_row_count + winchester_row_delta}",
        "scope row and dataset counts after Winchester history",
    )
    return javascript
