from __future__ import annotations

import base64
import gzip
import json
import re
import unittest
from pathlib import Path

from site_patches import (
    ST_PAULS_ADDITIONAL_DESTINATION_DATASETS,
    ST_PAULS_ALEVEL_HISTORY,
    ST_PAULS_DESTINATION_DETAIL_DATASETS,
    ST_PAULS_DESTINATION_HISTORY,
    ST_PAULS_GCSE_HISTORY,
    ST_PAULS_OXBRIDGE_CYCLE_HISTORY,
    ST_PAULS_SOURCES,
    ST_PAULS_UNIVERSITY_ENTRY_HISTORY,
    apply_st_pauls_history,
)


ROOT = Path(__file__).resolve().parents[1]


def load_connector_bundle() -> str:
    parts = sorted((ROOT / "bundle" / "connector" / "js").glob("part-*"))
    encoded = "".join(part.read_text(encoding="ascii") for part in parts)
    return gzip.decompress(base64.b64decode(encoded)).decode("utf-8")


def load_patched_bundle() -> str:
    return apply_st_pauls_history(load_connector_bundle())


def load_fallback_bundle() -> str:
    with gzip.open(ROOT / "bundle" / "app.js.gz", "rt", encoding="utf-8") as handle:
        return handle.read()


class StPaulsHistoryPatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.javascript = load_patched_bundle()

    def test_primary_gcse_run_is_present(self) -> None:
        for fragment in (
            '"year":2005,"scale":"A*-G","top":74.3,"top_2":94.8,"top_3":99.9',
            '"year":2006,"scale":"A*-G","top":70.9,"top_2":93.4,"top_3":99.2',
            '"year":2007,"scale":"A*-G","top":79.3,"top_2":96.6,"top_3":100.0',
            '"year":2008,"scale":"A*-G","top":83.4,"top_2":98.4,"top_3":99.8',
            '"year":2009,"scale":"A*-G","top":80.2,"top_2":97.5,"top_3":99.8',
        ):
            self.assertIn(fragment, self.javascript)

    def test_primary_pre_a_star_alevel_run_is_present(self) -> None:
        for fragment in (
            '"year":2005,"a_star":null,"a_star_a":78.5,"a_star_b":96.2,"grade_a_c":99.6',
            '"year":2006,"a_star":null,"a_star_a":85.0,"a_star_b":97.7,"grade_a_c":98.6',
            '"year":2007,"a_star":null,"a_star_a":86.5,"a_star_b":97.8,"grade_a_c":99.6',
            '"year":2008,"a_star":null,"a_star_a":83.3,"a_star_b":96.0,"grade_a_c":99.2',
            '"year":2009,"a_star":null,"a_star_a":90.6,"a_star_b":98.2,"grade_a_c":99.5',
        ):
            self.assertIn(fragment, self.javascript)

    def test_historic_years_are_unique_and_ordered(self) -> None:
        self.assertEqual(
            [row["year"] for row in ST_PAULS_GCSE_HISTORY],
            list(range(1999, 2010)),
        )
        self.assertEqual(
            [row["year"] for row in ST_PAULS_ALEVEL_HISTORY],
            [
                1992,
                1993,
                1994,
                1996,
                1997,
                1998,
                1999,
                2000,
                2002,
                2003,
                2004,
                2005,
                2006,
                2007,
                2008,
                2009,
            ],
        )

    def test_primary_percentage_ladders_are_monotonic(self) -> None:
        for row in ST_PAULS_GCSE_HISTORY:
            ladder = [row.get("top"), row.get("top_2"), row.get("top_3")]
            values = [value for value in ladder if value is not None]
            self.assertEqual(values, sorted(values), row["year"])
            self.assertTrue(all(0 <= value <= 100 for value in values), row["year"])

        for row in ST_PAULS_ALEVEL_HISTORY:
            ladder = [row.get("a_star_a"), row.get("a_star_b"), row.get("grade_a_c")]
            values = [value for value in ladder if value is not None]
            self.assertEqual(values, sorted(values), row["year"])
            self.assertTrue(all(0 <= value <= 100 for value in values), row["year"])

    def test_new_row_source_references_resolve(self) -> None:
        known_existing_sources = {"FB146"}
        known_sources = set(ST_PAULS_SOURCES) | known_existing_sources
        for row in ST_PAULS_GCSE_HISTORY + ST_PAULS_ALEVEL_HISTORY:
            self.assertTrue(row["source_ids"], row["year"])
            self.assertFalse(set(row["source_ids"]) - known_sources, row["year"])

    def test_legacy_metrics_remain_typed(self) -> None:
        self.assertIn('"year":1992,"a_star":null', self.javascript)
        self.assertIn('"legacy_points_per_candidate":28.3', self.javascript)
        self.assertIn('"five_plus_a_star_c":99', self.javascript)
        self.assertIn('"year":2002,"scale":"A*-G","top":null,"top_2":92.5', self.javascript)

    def test_historic_fields_have_display_units(self) -> None:
        for fragment in (
            'five_plus_a_star_c:{label:`% pupils with ≥5 A*–C`,kind:`percent`}',
            'legacy_points_per_candidate:{label:`Legacy points per candidate`,kind:`decimal`}',
            'as_grade_a_c:{label:`% AS grades A–C`,kind:`percent`}',
            'us_canada:{label:`US & Canada`,kind:`count`}',
        ):
            self.assertIn(fragment, self.javascript)

    def test_destination_coverage_spine_is_annual_1990_2025(self) -> None:
        self.assertEqual(
            [row["year"] for row in ST_PAULS_DESTINATION_HISTORY],
            list(range(1990, 2026)),
        )
        self.assertEqual(len({row["year"] for row in ST_PAULS_DESTINATION_HISTORY}), 36)

    def test_2015_destination_correction_and_denominators(self) -> None:
        row = next(row for row in ST_PAULS_DESTINATION_HISTORY if row["year"] == 2015)
        self.assertEqual((row["oxford"], row["cambridge"], row["oxbridge"]), (20, 21, 41))
        self.assertEqual((row["uk_universities"], row["us_universities"], row["canada"]), (153, 23, 5))
        self.assertEqual(row["north_america"], 28)
        self.assertEqual(row["university_bound"], 181)
        self.assertEqual(row["leavers"], 184)
        self.assertAlmostEqual(row["oxbridge_destination_rate"], 41 / 184, places=6)
        self.assertAlmostEqual(row["oxbridge_destination_rate_university_bound"], 41 / 181, places=6)
        self.assertAlmostEqual(row["us_destination_rate"], 23 / 184, places=6)
        self.assertNotIn(
            "{year:2015,leavers:null,oxford:null,cambridge:null,oxbridge:49,basis:`S external`}",
            self.javascript,
        )

    def test_oxbridge_cycle_spine_and_exact_reconciliations(self) -> None:
        self.assertEqual(
            [row["cycle"] for row in ST_PAULS_OXBRIDGE_CYCLE_HISTORY],
            list(range(2006, 2027)),
        )
        for row in ST_PAULS_OXBRIDGE_CYCLE_HISTORY:
            if row["applications"] is None:
                self.assertIsNone(row["offer_rate"])
                self.assertIsNone(row["acceptance_rate"])
                continue
            self.assertEqual(
                row["applications"],
                row["oxford"]["applications"] + row["cambridge"]["applications"],
            )
            self.assertEqual(row["offers"], row["oxford"]["offers"] + row["cambridge"]["offers"])
            self.assertEqual(
                row["acceptances"],
                row["oxford"]["acceptances"] + row["cambridge"]["acceptances"],
            )
            self.assertAlmostEqual(row["offer_rate"], row["offers"] / row["applications"], places=6)
            self.assertAlmostEqual(
                row["acceptance_rate"],
                row["acceptances"] / row["applications"],
                places=6,
            )

    def test_known_cycle_conflicts_use_lower_level_exact_rows(self) -> None:
        rows = {row["cycle"]: row for row in ST_PAULS_OXBRIDGE_CYCLE_HISTORY}
        self.assertEqual((rows[2020]["applications"], rows[2020]["offers"], rows[2020]["acceptances"]), (135, 44, 43))
        self.assertEqual((rows[2023]["applications"], rows[2023]["offers"], rows[2023]["acceptances"]), (161, 53, 49))
        self.assertEqual((rows[2025]["applications"], rows[2025]["offers"], rows[2025]["acceptances"]), (148, 51, 46))
        self.assertEqual((rows[2010]["offers"], rows[2010]["applications"], rows[2010]["acceptances"]), (74, None, None))
        self.assertEqual(rows[2026]["offers"], 65)

    def test_complete_destination_ledgers_reconcile(self) -> None:
        expected_totals = {
            2009: 182,
            2011: 175,
            2013: 174,
            2015: 184,
            2016: 190,
            2018: 204,
            2019: 190,
            2020: 202,
            2021: 158,
            2022: 219,
            2023: 228,
            2024: 175,
            2025: 185,
        }
        for dataset in ST_PAULS_DESTINATION_DETAIL_DATASETS:
            year = int(dataset["period"])
            rows = dataset["rows"]
            additive_total = sum(row["count"] for row in rows if row["additive"])
            control_rows = [row for row in rows if row["row_type"] == "aggregate_total"]
            self.assertEqual(len(control_rows), 1, dataset["dataset_id"])
            self.assertEqual(additive_total, expected_totals[year], dataset["dataset_id"])
            self.assertEqual(control_rows[0]["count"], expected_totals[year], dataset["dataset_id"])

    def test_strict_us_institution_totals_remain_separate(self) -> None:
        expected_us = {
            2009: 21,
            2011: 13,
            2013: 24,
            2015: 23,
            2016: 28,
            2018: 37,
            2019: 22,
            2020: 24,
            2021: 27,
            2022: 34,
            2023: 35,
            2024: 22,
            2025: 33,
        }
        for dataset in ST_PAULS_DESTINATION_DETAIL_DATASETS:
            year = int(dataset["period"])
            strict_us = sum(
                row["count"]
                for row in dataset["rows"]
                if row["additive"] and row["country"] == "USA"
            )
            self.assertEqual(strict_us, expected_us[year], dataset["dataset_id"])

    def test_entry_year_populations_are_separate(self) -> None:
        rows = {row["year"]: row for row in ST_PAULS_UNIVERSITY_ENTRY_HISTORY}
        row = rows[2016]
        self.assertEqual(row["destination_total"], 189)
        self.assertEqual(row["oxbridge_entry_count"], 53)
        self.assertAlmostEqual(row["oxbridge_entry_rate"], 53 / 189, places=6)
        self.assertEqual(row["america"], 34)
        self.assertIn("SPS_DEST_2016_ENTRY_PAGE", row["source_ids"])

        self.assertEqual((rows[2020]["destination_total"], rows[2020]["oxbridge_entry_count"]), (202, 43))
        self.assertEqual(rows[2020]["us_universities"], 24)
        self.assertAlmostEqual(rows[2020]["us_entry_rate"], 24 / 202, places=6)
        self.assertEqual((rows[2021]["destination_total"], rows[2021]["oxbridge_entry_count"]), (158, 30))
        self.assertEqual(rows[2021]["us_universities"], 27)
        self.assertAlmostEqual(rows[2021]["us_entry_rate"], 27 / 158, places=6)

        destination_2016 = next(row for row in ST_PAULS_DESTINATION_HISTORY if row["year"] == 2016)
        self.assertEqual((destination_2016["destination_total"], destination_2016["oxbridge"]), (190, 53))
        self.assertIn("one-place", destination_2016["coverage_status"])
        destination_2005 = next(row for row in ST_PAULS_DESTINATION_HISTORY if row["year"] == 2005)
        self.assertEqual(destination_2005["source_ids"], ["FB146"])

    def test_newly_recovered_final_destination_rows(self) -> None:
        rows = {row["year"]: row for row in ST_PAULS_DESTINATION_HISTORY}
        expected = {
            2016: (190, 31, 22, 53, 28),
            2019: (190, 26, 26, 52, 22),
            2022: (219, 21, 20, 41, 34),
            2023: (228, 29, 21, 50, 35),
            2024: (175, 24, 16, 40, 22),
        }
        for year, values in expected.items():
            row = rows[year]
            self.assertEqual(
                (row["destination_total"], row["oxford"], row["cambridge"], row["oxbridge"], row["us_universities"]),
                values,
            )
            self.assertAlmostEqual(row["oxbridge_destination_rate"], row["oxbridge"] / row["destination_total"], places=6)
            self.assertAlmostEqual(row["us_destination_rate"], row["us_universities"] / row["destination_total"], places=6)

        self.assertEqual(rows[2024]["confidence"], "P")
        self.assertEqual(rows[2017]["confidence"], "P_NEGATIVE")
        self.assertIn("promised", rows[2017]["note"])

    def test_2014_overlap_and_2018_college_basis_remain_explicit(self) -> None:
        rows = {row["year"]: row for row in ST_PAULS_DESTINATION_HISTORY}
        self.assertEqual(rows[2014]["oxbridge"], 56)
        self.assertEqual(rows[2014]["north_america"], 24)
        self.assertEqual(rows[2014]["ucl_imperial"], 34)
        self.assertEqual(rows[2014]["medicine"], 15)
        self.assertIsNone(rows[2018]["university_bound"])
        self.assertIsNone(rows[2018]["uk_universities"])
        self.assertEqual(rows[2018]["uk_or_college"], 162)

    def test_unsafe_legacy_destination_rows_are_removed(self) -> None:
        for fragment in (
            "{year:2012,leavers:null,oxford:null,cambridge:null,oxbridge:55,basis:`S external`}",
            "{year:2017,leavers:null,oxford:null,cambridge:null,oxbridge:51,basis:`S external`}",
            "{year:2020,leavers:null,oxford:null,cambridge:null,oxbridge:44,basis:`S external`}",
            "{year:2023,leavers:null,oxford:null,cambridge:null,oxbridge:54,basis:`S external`}",
        ):
            self.assertNotIn(fragment, self.javascript)

    def test_destination_sources_resolve(self) -> None:
        known_sources = set(ST_PAULS_SOURCES) | {"FB146"}
        for row in ST_PAULS_DESTINATION_HISTORY + ST_PAULS_OXBRIDGE_CYCLE_HISTORY + ST_PAULS_UNIVERSITY_ENTRY_HISTORY:
            self.assertFalse(set(row["source_ids"]) - known_sources, row.get("year", row.get("cycle")))
        for dataset in ST_PAULS_DESTINATION_DETAIL_DATASETS:
            self.assertFalse(set(dataset["source_refs"]) - known_sources, dataset["dataset_id"])
            for row in dataset["rows"]:
                self.assertFalse(set(row["source_ids"]) - known_sources, dataset["dataset_id"])

    def test_new_destination_series_and_units_are_in_both_bundles(self) -> None:
        fragments = (
            '"dataset_id":"st_pauls_oxbridge_cycle_overview"',
            '"dataset_id":"st_pauls_university_entry_year_destinations"',
            '"dataset_id":"st_pauls_destinations_2015_by_university"',
            '"dataset_id":"st_pauls_destinations_2019_by_university"',
            '"dataset_id":"st_pauls_destinations_2020_entry_year_by_university"',
            '"dataset_id":"st_pauls_destinations_2023_by_university"',
            '"dataset_id":"st_pauls_destinations_2025_by_university"',
            "oxbridge_destination_rate:{label:`Oxbridge / matching destination cohort`,kind:`rate`}",
            "us_destination_rate:{label:`US / matching destination cohort`,kind:`rate`}",
            "st_pauls_destinations_2024_by_university:`2024 destinations · all institutions`",
            '"destination":"École Polytechnique Fédérale de Lausanne"',
        )
        for patched in (self.javascript, apply_st_pauls_history(load_fallback_bundle())):
            for fragment in fragments:
                self.assertIn(fragment, patched)

    def test_dataset_ids_and_inventory_are_consistent(self) -> None:
        identifiers = [
            left or right
            for left, right in re.findall(
                r'(?:dataset_id:`([^`]+)`|"dataset_id":"([^"]+)")',
                self.javascript,
            )
        ]
        self.assertEqual(len(identifiers), len(set(identifiers)))
        self.assertIn("datasets:60,rows:1192", self.javascript)
        self.assertEqual(len(ST_PAULS_ADDITIONAL_DESTINATION_DATASETS), 15)

    def test_added_source_catalogue_is_present_in_connector(self) -> None:
        for source_key, source_record in ST_PAULS_SOURCES.items():
            fragment = f'{json.dumps(source_key)}:{json.dumps(source_record, ensure_ascii=False, separators=(",", ":"))}'
            self.assertIn(fragment, self.javascript)

    def test_fallback_source_catalogue_remains_valid_json(self) -> None:
        patched = apply_st_pauls_history(load_fallback_bundle())
        match = re.search(r"_s=JSON\.parse\(`(.*?)`\),vs=", patched)
        self.assertIsNotNone(match)
        catalogue = json.loads(match.group(1))
        for source_key in ST_PAULS_SOURCES:
            self.assertIn(source_key, catalogue)

    def test_patch_is_fail_closed(self) -> None:
        with self.assertRaises(RuntimeError):
            apply_st_pauls_history(self.javascript)

    def test_fallback_bundle_accepts_the_same_patch(self) -> None:
        patched = apply_st_pauls_history(load_fallback_bundle())
        self.assertIn('"year":2009,"scale":"A*-G","top":80.2', patched)


if __name__ == "__main__":
    unittest.main()
