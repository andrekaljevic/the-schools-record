from __future__ import annotations

import base64
import gzip
import json
import re
import unittest
from pathlib import Path

from site_patches import (
    ST_PAULS_ALEVEL_HISTORY,
    ST_PAULS_GCSE_HISTORY,
    ST_PAULS_SOURCES,
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

    def test_2015_destination_correction(self) -> None:
        self.assertIn(
            "{year:2015,leavers:184,university_bound:181,uk_universities:153,oxford:20,cambridge:21,oxbridge:41,us_canada:28,other:3",
            self.javascript,
        )
        self.assertEqual(20 + 21, 41)
        self.assertEqual(153 + 28, 181)
        self.assertEqual(181 + 3, 184)
        self.assertNotIn(
            "{year:2015,leavers:null,oxford:null,cambridge:null,oxbridge:49,basis:`S external`}",
            self.javascript,
        )

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
