"""Product parity: the complete intended public record survives the migration.

These tests drive the native application headlessly and fail closed if a
dataset, a corpus, a capability or a navigation path disappears again.  They
check reachability (every frozen record has a public page), the feature matrix
of the final pre-native public product, representative high-complexity ledgers,
and exact frozen values as displayed.  Nothing here writes to the dataset.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

sys.path.insert(0, str(Path(__file__).resolve().parent))

from support import page, render  # noqa: E402
from tsr import components, corpora, dataset, evidence, format as fmt, records, sources  # noqa: E402

DATASET_PATH = ROOT / "data" / "dataset.json"
DATASET_SHA256 = "245f2d8176f8fca0d53f41689f096734dd13e9023af9a67931314334251b9f6f"
NOT_FOUND = "That page is not in the record"


def school_page(dataset_id: str) -> str:
    """The route on which a figures dataset is displayed."""
    entry = next(item for item in dataset.figures()["datasets"] if item["dataset_id"] == dataset_id)
    section = "exam-results" if entry["domain"] == "exam_results" else "university-destinations"
    school_id = corpora.school_id_for(entry["school"])
    return f"/schools/{school_id}/{section}" if school_id else f"/schools/eton/{section}"


class FrozenDataTests(unittest.TestCase):
    def test_dataset_file_is_unchanged(self) -> None:
        self.assertEqual(hashlib.sha256(DATASET_PATH.read_bytes()).hexdigest(), DATASET_SHA256)

    def test_corpus_accounting_matches_the_advertised_total(self) -> None:
        counts = corpora.corpus_counts()
        self.assertEqual(counts, {"figures": 1274, "granular": 83, "oxbridge": 571, "us": 349, "total": 2277})
        self.assertEqual(evidence.counts()["total"], 2277)
        self.assertEqual(records.frozen_record_count(), 2277)

    def test_every_record_has_one_stable_identifier(self) -> None:
        ids = [item.id for item in evidence.index()]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(sum(1 for item in ids if item.startswith("fig:")), 1274)
        self.assertEqual(sum(1 for item in ids if item.startswith("gran:")), 83)
        self.assertEqual(sum(1 for item in ids if item.startswith("ox:")), 571)
        self.assertEqual(sum(1 for item in ids if item.startswith("us:")), 349)


class DatasetReachabilityTests(unittest.TestCase):
    """Every figures dataset renders, with every row, on its school page."""

    def test_every_dataset_renders_every_row_on_its_public_route(self) -> None:
        for entry in dataset.figures()["datasets"]:
            dataset_id = entry["dataset_id"]
            if entry["school"] == "All seven schools":
                for school in dataset.schools():
                    rows = [row for row in entry["rows"] if corpora.school_id_for(row.get("school")) == school["id"]]
                    markup = page(f"/schools/{school['id']}/university-destinations")
                    self.assertIn(f'id="{dataset_id}"', markup, (dataset_id, school["id"]))
                    self.assertEqual(markup.count(f'<tr id="{dataset_id}-'), len(rows), (dataset_id, school["id"]))
                continue
            markup = page(school_page(dataset_id))
            self.assertIn(f'id="{dataset_id}"', markup, dataset_id)
            self.assertEqual(markup.count(f'<tr id="{dataset_id}-'), len(entry["rows"]), dataset_id)

    def test_every_gcse_ledger_is_reachable_and_labelled(self) -> None:
        gcse = [
            entry for entry in dataset.figures()["datasets"]
            if "gcse" in entry["dataset_id"] or entry["dataset_id"].endswith("exam_anchors")
        ]
        self.assertEqual(
            sorted(entry["dataset_id"] for entry in gcse),
            [
                "eton_gcse_primary",
                "kcs_gcse_detailed_9_1",
                "kcs_gcse_headline",
                "spgs_exam_anchors",
                "st_pauls_gcse",
                "westminster_gcse_old_scale",
                "westminster_gcse_reformed",
                "winchester_gcse",
                "wycombe_exam_anchors",
            ],
        )
        for entry in gcse:
            route = school_page(entry["dataset_id"])
            markup = page(route)
            self.assertIn(f'id="{entry["dataset_id"]}"', markup)
            self.assertEqual(markup.count(f'<tr id="{entry["dataset_id"]}-'), len(entry["rows"]))
            self.assertIn(records.dataset_family(entry), markup)
            self.assertIn(f'href="#{entry["dataset_id"]}"', markup, "the series index must link to the ledger")
            # The school landing page must name the ledger and its family too.
            landing = page(route.rsplit("/", 1)[0])
            self.assertIn(f"#{entry['dataset_id']}", landing)
            self.assertIn("GCSE / IGCSE", landing)

    def test_dataset_years_are_all_present(self) -> None:
        for entry in dataset.figures()["datasets"]:
            if entry["school"] == "All seven schools":
                continue
            markup = page(school_page(entry["dataset_id"]))
            for row in entry["rows"]:
                anchor = components.row_anchor(entry["dataset_id"], row)
                self.assertIn(f'<tr id="{anchor}"', markup, anchor)


class CorpusReachabilityTests(unittest.TestCase):
    def test_granular_rows_render_on_the_school_pages(self) -> None:
        for entry in corpora.granular_datasets():
            school_id = corpora.school_id_for(entry["school"])
            section = "exam-results" if entry["domain"] == "exam_results" else "university-destinations"
            markup = page(f"/schools/{school_id}/{section}")
            self.assertIn(f'id="{entry["dataset_id"]}"', markup)
            start = markup.index(f'id="{entry["dataset_id"]}"')
            block = markup[start:start + 200000]
            table = block[: block.index("</table>")]
            self.assertEqual(table.count("<tr") - 1, len(entry["rows"]), entry["dataset_id"])

    def test_every_oxbridge_record_is_traceable_on_a_public_page(self) -> None:
        by_school: dict[str | None, list[dict]] = {}
        for record in corpora.oxbridge_records():
            by_school.setdefault(corpora.oxbridge_school_id(record), []).append(record)
        for school_id, items in by_school.items():
            route = f"/schools/{school_id}/oxbridge" if school_id else "/oxbridge"
            markup = page(route)
            for record in items:
                self.assertIn(f"record=ox:{record['record_id']}", markup, (route, record["record_id"]))

    def test_every_us_record_is_traceable_on_its_school_page(self) -> None:
        for school in dataset.schools():
            markup = page(f"/schools/{school['id']}/us-universities")
            for record in corpora.us_records(school["id"]):
                self.assertIn(f"record=us:{record['record_id']}", markup, record["record_id"])
        self.assertEqual(sum(len(corpora.us_records(s["id"])) for s in dataset.schools()), 349)

    def test_record_permalinks_render_full_detail(self) -> None:
        samples = ["fig:kcs_gcse_detailed_9_1:1", "gran:st_pauls_subject_results_2010_alevel:0",
                   "ox:oxford-apply-centre-2006-10092", "ox:historical-top100-1", "us:USU-0001", "us:USU-0276"]
        for record_id in samples:
            item = evidence.record(record_id)
            self.assertIsNotNone(item, record_id)
            markup = page("/evidence", record=record_id)
            self.assertIn(f'id="{record_id}"', markup)
            self.assertIn("Permanent link to this record", markup)
            for label, value in evidence.detail_fields(item)[:6]:
                self.assertIn(value if len(value) < 60 else value[:40], markup, (record_id, label))

    def test_every_index_record_carries_a_public_route(self) -> None:
        for item in evidence.index():
            self.assertTrue(item.route.startswith("/"), item.id)
            self.assertNotEqual(item.route, "/evidence", item.id)

    def test_index_counts_by_school_account_for_every_school_record(self) -> None:
        for school in dataset.schools():
            expected = corpora.school_corpus_counts(school["id"])
            got = len(evidence.filter_records(evidence.index(), school_id=school["id"]))
            self.assertEqual(got, sum(expected.values()), school["id"])


FEATURE_MATRIX = (
    ("school index", "/schools", {}, ["School records", 'class="index-row']),
    ("school examination records", "/schools/westminster/exam-results", {}, ['id="westminster_gcse_old_scale"', 'id="westminster_alevel"', "Ledgers in this record"]),
    ("school university records", "/schools/st-pauls/university-destinations", {}, ['id="st_pauls_destinations"', 'id="oxford_strict_st_paul_s_school"']),
    ("comparison tool", "/compare", {}, ['class="comparison-chart"', "Exact values for"]),
    ("evidence search", "/evidence", {"q": "winchester 2019 gcse"}, ["Tracing" if False else "records", 'id="fig:winchester_gcse:']),
    ("evidence deep linking", "/evidence", {"school": "Winchester College", "dataset": "winchester_gcse", "period": "2019"}, ["Tracing a displayed figure", 'id="fig:winchester_gcse:']),
    ("record permalink", "/evidence", {"record": "ox:oxford-apply-centre-2006-10092"}, ["Permanent link to this record", "134"]),
    ("evidence sources register", "/evidence", {"section": "sources"}, ["source references", 'id="source-FB146"', 'id="source-WIN_GCSE_HMC_1997"']),
    ("how the figures are checked", "/evidence", {"section": "method"}, ["Evidence status codes", "Which compilation controls"]),
    ("corrections ledger", "/corrections", {}, ["What changed, and why", 'id="C01"', 'id="C29"']),
    ("published differences", "/corrections", {}, ["When published figures do not agree", 'id="X01"', 'id="WC05"']),
    ("correction report form", "/corrections/report", {}, ["Report a correction", "Correction policy"]),
    ("Oxbridge corpus home", "/oxbridge", {}, ["Oxford and Cambridge admissions records", "University-wide outcomes", "2007 five-year table"]),
    ("Oxbridge school records", "/schools/westminster/oxbridge", {}, ["Apply-centre outcomes by college", "record=ox:"]),
    ("US corpus home", "/us-universities", {}, ["Records by school", "Outcome types in this corpus"]),
    ("US school records", "/schools/kcs/us-universities", {}, ["University of Pennsylvania", "Aggregate", "record=us:USU-0001"]),
    ("school entry evidence", "/schools/st-pauls/school-entry", {}, ["Published process and known limits", "Evidence boundary"]),
    ("methodology", "/methodology", {}, ["Definitions before comparisons", "Grading systems"]),
    ("evidence status on every ledger row", "/schools/winchester/exam-results", {}, ["Evidence status", "Row sources"]),
    ("public source linking", "/schools/winchester/exam-results", {}, ["https://web.archive.org/", "WIN_GCSE_HMC_1997"]),
    ("school record inventory", "/schools/kcs", {}, ["Evidence by qualification and outcome", "School entry", "Oxford and Cambridge", "US and overseas universities"]),
    ("results by year charts", "/schools/kcs", {}, ["Results by year", 'class="trajectory-panel"']),
    ("home inventory", "/", {}, ["2,277 frozen records", "Oxford and Cambridge records", "US university records"]),
    ("professional enquiry", "/professional", {}, ["Request a sourced comparison"]),
    ("sample dossier", "/sample-dossier", {}, ['class="comparison-chart"']),
)


class FeatureParityTests(unittest.TestCase):
    def test_every_final_public_capability_has_a_native_equivalent(self) -> None:
        for capability, route, params, markers in FEATURE_MATRIX:
            markup = page(route, **params)
            for marker in markers:
                self.assertIn(marker, markup, f"{capability}: {route} {params} lacks {marker!r}")

    def test_navigation_exposes_every_corpus_from_every_school_record(self) -> None:
        for school in dataset.schools():
            markup = page(f"/schools/{school['id']}")
            for section in ("exam-results", "university-destinations", "oxbridge", "us-universities", "school-entry"):
                self.assertIn(f"?p=/schools/{school['id']}/{section}", markup, (school["id"], section))


class NavigationTests(unittest.TestCase):
    ENTRY_POINTS = ["/", "/schools", "/compare", "/methodology", "/evidence", "/oxbridge", "/us-universities", "/corrections",
                    "/corrections/report", "/professional", "/sample-dossier", "/about", "/privacy", "/terms", "/changelog"]

    @staticmethod
    def internal_links(markup: str) -> set[tuple[str, tuple[tuple[str, str], ...]]]:
        found: set[tuple[str, tuple[tuple[str, str], ...]]] = set()
        for href in re.findall(r'href="\?p=([^"#]+)', markup):
            href = href.replace("&amp;", "&")
            route, _, query = href.partition("&")
            params = tuple(sorted(tuple(part.split("=", 1)) for part in query.split("&") if "=" in part))
            found.add((route, params))
        return found

    def test_no_internal_link_ends_on_the_not_found_page(self) -> None:
        seen: set[tuple[str, tuple[tuple[str, str], ...]]] = set()
        queue = [(route, ()) for route in self.ENTRY_POINTS]
        queue += [(f"/schools/{s['id']}", ()) for s in dataset.schools()]
        visited = 0
        while queue:
            route, params = queue.pop()
            if (route, params) in seen:
                continue
            seen.add((route, params))
            markup = render(route, params)
            visited += 1
            self.assertNotIn(NOT_FOUND, markup, f"{route} {params} is not found")
            for link in self.internal_links(markup):
                target_route, target_params = link
                if any(key == "record" for key, _ in target_params):
                    continue  # permalinks are sampled separately
                if any(key == "page" for key, _ in target_params):
                    continue
                if link not in seen:
                    queue.append(link)
        self.assertGreater(visited, 60)

    def test_unknown_routes_still_render_the_record_chrome(self) -> None:
        markup = page("/does-not-exist")
        self.assertIn(NOT_FOUND, markup)
        self.assertIn("The Schools Record", markup)


class DisplayTests(unittest.TestCase):
    """Representative high-complexity datasets keep their denominators visible."""

    def _columns(self, dataset_id: str) -> list[str]:
        entry = next(item for item in dataset.figures()["datasets"] if item["dataset_id"] == dataset_id)
        return [fmt.field_label(field) for field in fmt.table_fields(entry["rows"])]

    def test_kcs_modern_gcse_keeps_every_denominator_by_default(self) -> None:
        columns = self._columns("kcs_gcse_detailed_9_1")
        for label in ("Entries", "Candidates", "Numbered-grade entries", "Letter-grade entries", "Additional Mathematics entries · excluded", "% grade 9", "% grades 9–8", "% grades 9–7"):
            self.assertIn(label, columns)

    def test_kcs_a_level_and_ib_denominators_are_visible(self) -> None:
        columns = self._columns("kcs_combined_alevel_ib")
        for label in ("Candidates", "A-level pathway pupils", "Actual A-level takers", "A-level entries", "IB candidates", "IB Higher-Level entries", "IB candidates · lower bound"):
            self.assertIn(label, columns)
        markup = page("/schools/kcs/exam-results")
        for label in ("Actual A-level takers", "IB Higher-Level entries"):
            self.assertIn(label, markup)

    def test_winchester_gcse_shows_scale_and_published_crosswalks(self) -> None:
        columns = self._columns("winchester_gcse")
        for label in ("Grade scale", "Entries", "% grade 9", "% A*–A · published crosswalk", "% A*–B or 9–6 · published crosswalk", "Top band · published crosswalk"):
            self.assertIn(label, columns)

    def test_winchester_pre_u_keeps_both_rulers_and_reconstructed_counts(self) -> None:
        columns = self._columns("winchester_pre_u_two_ruler_2011_2019")
        for label in ("% D1", "% D1–D3 · A*/A-equivalent", "% D1–M1 · published ruler", "D1 count · reconstructed", "Entries"):
            self.assertIn(label, columns)

    def test_winchester_university_outcomes_render_both_destination_ledgers(self) -> None:
        markup = page("/schools/winchester/university-destinations")
        for dataset_id in ("winchester_destination_and_historic_access", "winchester_final_destination_distributions_2010_2022", "oxford_strict_winchester_college", "cambridge_and_combined_winchester_college"):
            self.assertIn(f'id="{dataset_id}"', markup)
        self.assertIn("Arithmetic offers ÷ cohort · not an official rate", markup)

    def test_st_pauls_destinations_keep_denominators_and_rates_apart(self) -> None:
        columns = self._columns("st_pauls_destinations")
        for label in ("Leavers", "Oxford + Cambridge", "Destination-list denominator", "University-bound leavers", "Oxbridge / matching destination cohort", "US universities"):
            self.assertIn(label, columns)

    def test_no_column_cap_hides_a_published_figure(self) -> None:
        for entry in dataset.figures()["datasets"]:
            summary = set(fmt.table_fields(entry["rows"]))
            for field in fmt.table_fields(entry["rows"], expanded=True):
                if field.split(".")[-1] in fmt.DETAIL_ONLY_FIELDS:
                    continue
                values = [fmt.cell_value(row, field) for row in entry["rows"]]
                numeric = [v for v in values if isinstance(v, (int, float)) and not isinstance(v, bool)]
                if numeric:
                    self.assertIn(field, summary, (entry["dataset_id"], field))

    def test_latest_card_names_every_omitted_field(self) -> None:
        markup = components.latest_record(records.school_datasets("westminster", ["exam_results"]))
        self.assertIn("Open this ledger", markup)
        self.assertNotIn("[object Object]", markup)

    def test_oxbridge_record_detail(self) -> None:
        item = evidence.record("ox:oxford-apply-centre-2006-10092")
        detail = dict(evidence.detail_fields(item))
        self.assertEqual(detail["Applications"], "134")
        self.assertEqual(detail["Offers"], "70")
        self.assertEqual(detail["Accepted / admitted"], "65")
        self.assertEqual(detail["Offer rate"], "52.2%")
        self.assertEqual(detail["Entry cycle"], "2006")
        self.assertEqual(detail["Apply centre"], "Eton College")

    def test_rounded_oxbridge_intervals_stay_intervals(self) -> None:
        item = evidence.record("ox:oxford-westminster-foi-2022-2025-subject-ancient-and-modern-history")
        self.assertIn(("Applications", "0–4 (rounded down to multiple of 5)"), item.summary)

    def test_us_record_detail(self) -> None:
        item = evidence.record("us:USU-0001")
        detail = dict(evidence.detail_fields(item))
        self.assertEqual(detail["Institution"], "University of Pennsylvania")
        self.assertEqual(detail["Count"], "2")
        self.assertEqual(detail["Outcome type"], "Leaver destination")
        self.assertEqual(detail["Cohort denominator"], "—")
        self.assertIn("not printed", detail["Denominator basis"])
        alternative = evidence.record("us:USU-0276")
        self.assertEqual(dict(evidence.detail_fields(alternative))["Used for analysis"], "No")
        self.assertIn("westminster_2014_destination_versions", dict(evidence.detail_fields(alternative))["Published-difference group"])


class NumericalParityTests(unittest.TestCase):
    def test_winchester_modelled_pre_u_row_displays_as_stored(self) -> None:
        markup = page("/schools/winchester/exam-results")
        row_start = markup.index('<tr id="winchester_pre_u_two_ruler_2011_2019-2010"')
        row = markup[row_start: markup.index("</tr>", row_start)]
        # d1_d3_honest_astar_a and d1_m1_published carry no percent spec in the
        # frozen presentation, so they print as the published build printed them.
        for value in ("339", "18.9%", "52.2%", ">79.1<", ">90.0<", "95.0%"):
            self.assertIn(value, row)
        self.assertIn("Primary / Derived / MODELLED", row)

    def test_st_pauls_2015_destinations(self) -> None:
        markup = page("/schools/st-pauls/university-destinations")
        row_start = markup.index('<tr id="st_pauls_destinations-2015"')
        row = markup[row_start: markup.index("</tr>", row_start)]
        for value in (">21<", ">41<", ">184<"):
            self.assertIn(value, row)

    def test_kcs_2019_gcse_detail_row(self) -> None:
        markup = page("/schools/kcs/exam-results")
        row_start = markup.index('<tr id="kcs_gcse_detailed_9_1-2019"')
        row = markup[row_start: markup.index("</tr>", row_start)]
        for value in ("1,698", ">153<", "57.1%"):
            self.assertIn(value, row)

    def test_westminster_2025_strict_oxbridge_uses_the_corrected_values(self) -> None:
        markup = page("/schools/westminster/university-destinations")
        row_start = markup.index('<tr id="cambridge_and_combined_westminster_school-2025"')
        row = markup[row_start: markup.index("</tr>", row_start)]
        for value in (">166<", ">80<", ">73<"):
            self.assertIn(value, row)

    def test_blanks_bounds_and_ranges_are_preserved(self) -> None:
        markup = page("/schools/kcs/exam-results")
        self.assertIn('class="blank-value">—</td>', markup)
        self.assertIn("≥120", markup, "the typed IB lower bound keeps its bound")
        winchester = page("/schools/winchester/exam-results")
        self.assertIn("–", winchester)
        self.assertNotIn("[object Object]", markup)

    def test_corrections_ledger_shows_old_and_new_values(self) -> None:
        markup = page("/corrections")
        for old, new in (("79", "80.1"), ("98.8", "99.8"), ("179 / 96 / 91", "166 / 80 / 73")):
            self.assertIn(old, markup)
            self.assertIn(new, markup)
        self.assertEqual(markup.count('class="ledger-entry"'), 29 + 26)


class SourceTests(unittest.TestCase):
    def test_public_links_are_the_reviewed_set_and_nothing_private(self) -> None:
        register = sources.public_sources()
        self.assertEqual(len(register), 40)
        for entry in register.values():
            self.assertTrue(sources.is_public_url(entry["url"]), entry)
        self.assertIn("WIN_GCSE_HMC_1997", register)
        self.assertTrue(register["WIN_GCSE_HMC_1997"]["url"].startswith("https://web.archive.org/"))

    def test_withheld_sources_stay_withheld(self) -> None:
        described = sources.describe("FB146")
        self.assertTrue(described["withheld"])
        self.assertIsNone(described["url"])
        self.assertEqual(described["title"], "Source title withheld")

    def test_every_dataset_reference_is_described(self) -> None:
        for entry in dataset.figures()["datasets"]:
            for ref in entry.get("source_refs") or []:
                self.assertIsNotNone(sources.catalog_entry(ref), ref)


if __name__ == "__main__":
    unittest.main()
