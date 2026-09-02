from __future__ import annotations

import base64
import gzip
import json
import re
import unittest
from pathlib import Path

from site_patches import (
    WINCHESTER_ACCESS_HISTORY,
    WINCHESTER_ALEVEL_HISTORY,
    WINCHESTER_CONFLICTS,
    WINCHESTER_CORRECTIONS,
    WINCHESTER_DESTINATION_DISTRIBUTIONS,
    WINCHESTER_GCSE_HISTORY,
    WINCHESTER_MIXED_RESULTS_2021,
    WINCHESTER_PRE_U_HISTORY,
    WINCHESTER_SOURCES,
    apply_st_pauls_history,
    apply_winchester_history,
)


ROOT = Path(__file__).resolve().parents[1]


def load_connector_bundle() -> str:
    parts = sorted((ROOT / "bundle" / "connector" / "js").glob("part-*"))
    encoded = "".join(part.read_text(encoding="ascii") for part in parts)
    return gzip.decompress(base64.b64decode(encoded)).decode("utf-8")


def load_patched_bundle() -> str:
    return apply_winchester_history(apply_st_pauls_history(load_connector_bundle()))


def load_fallback_bundle() -> str:
    with gzip.open(ROOT / "bundle" / "app.js.gz", "rt", encoding="utf-8") as handle:
        return handle.read()


def interval_bounds(value: object) -> tuple[float, float] | None:
    if isinstance(value, (int, float)):
        number = float(value)
        return number, number
    if isinstance(value, str) and "–" in value:
        lower, upper = value.split("–", 1)
        return float(lower), float(upper)
    return None


class WinchesterHistoryPatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.javascript = load_patched_bundle()

    def test_complete_a_star_era_ledger_is_ordered(self) -> None:
        self.assertEqual(
            [row["year"] for row in WINCHESTER_GCSE_HISTORY],
            list(range(1994, 2013)),
        )

    def test_recovered_bands_and_selected_upper_bounds_are_present(self) -> None:
        for fragment in (
            '"year":1996,"scale":"A*-G","top_equivalent":null,"astar_a_equivalent":86.0,"astar_b_or_9_6":97.7',
            '"year":1997,"scale":"A*-G","entries":849,"top_equivalent":null,"astar_a_equivalent":85.0,"astar_b_or_9_6":97.4',
            '"year":2004,"scale":"A*-G","top_equivalent":null,"astar_a_equivalent":87.0,"astar_b_or_9_6":null',
            '"year":2005,"scale":"A*-G","candidates":132,"top_equivalent":50.9,"astar_a_equivalent":90.9,"astar_b_or_9_6":null',
            '"year":2006,"scale":"A*-G","entries":1069,"top_equivalent":47.0,"astar_a_equivalent":87.1,"astar_b_or_9_6":97.3',
            '"year":2011,"scale":"A*-G","top_equivalent":null,"astar_a_equivalent":90.7,"astar_b_or_9_6":null',
            '"year":2012,"scale":"A*-G","entries":1191,"top_equivalent":69.0,"astar_a_equivalent":93.5,"astar_b_or_9_6":99.0',
        ):
            self.assertIn(fragment, self.javascript)

    def test_requested_bands_are_monotonic_when_comparable(self) -> None:
        for row in WINCHESTER_GCSE_HISTORY:
            bands = [
                interval_bounds(row.get("top_equivalent")),
                interval_bounds(row.get("astar_a_equivalent")),
                interval_bounds(row.get("astar_b_or_9_6")),
            ]
            present = [band for band in bands if band is not None]
            self.assertTrue(
                all(0 <= lower <= upper <= 100 for lower, upper in present),
                row["year"],
            )
            for earlier, later in zip(present, present[1:]):
                self.assertLessEqual(earlier[1], later[0], row["year"])

    def test_2006_exact_count_recomputation(self) -> None:
        self.assertAlmostEqual(502 / 1069 * 100, 47.0, places=1)
        self.assertAlmostEqual((502 + 429) / 1069 * 100, 87.1, places=1)
        self.assertAlmostEqual((502 + 429 + 109) / 1069 * 100, 97.3, places=1)

    def test_2012_upper_bounds_follow_six_suppressed_entries(self) -> None:
        self.assertAlmostEqual(816 / 1191 * 100, 68.51, places=2)
        self.assertAlmostEqual((816 + 6) / 1191 * 100, 69.02, places=2)
        self.assertAlmostEqual((816 + 292) / 1191 * 100, 93.03, places=2)
        self.assertAlmostEqual((816 + 292 + 6) / 1191 * 100, 93.53, places=2)
        self.assertAlmostEqual((816 + 292 + 65) / 1191 * 100, 98.49, places=2)
        self.assertAlmostEqual((816 + 292 + 65 + 6) / 1191 * 100, 98.99, places=2)
        row = next(row for row in WINCHESTER_GCSE_HISTORY if row["year"] == 2012)
        self.assertEqual(row["top_equivalent"], 69.0)
        self.assertEqual(row["astar_a_equivalent"], 93.5)
        self.assertEqual(row["astar_b_or_9_6"], 99.0)

    def test_no_pupil_threshold_is_substituted(self) -> None:
        prohibited = {"five_plus_a_star_c", "five_plus_including_english_maths"}
        for row in WINCHESTER_GCSE_HISTORY:
            self.assertFalse(prohibited & set(row), row["year"])

    def test_row_source_references_resolve(self) -> None:
        known_sources = set(WINCHESTER_SOURCES) | {"FB146"}
        for row in WINCHESTER_GCSE_HISTORY:
            self.assertTrue(row["source_ids"], row["year"])
            self.assertFalse(set(row["source_ids"]) - known_sources, row["year"])

    def test_source_catalogue_and_metadata_are_present(self) -> None:
        for source_key, source_record in WINCHESTER_SOURCES.items():
            fragment = f'{json.dumps(source_key)}:{json.dumps(source_record, ensure_ascii=False, separators=(",", ":"))}'
            self.assertIn(fragment, self.javascript)
        self.assertIn("evidenceWindow:`1994–2026`", self.javascript)
        self.assertIn("Pupil-level five-grade thresholds", self.javascript)
        self.assertIn("Evidence snapshot · 2 Sep 2026", self.javascript)
        self.assertNotIn("Evidence snapshot · 30 Aug 2026", self.javascript)

    def test_fallback_source_catalogue_remains_valid_json(self) -> None:
        patched = apply_winchester_history(apply_st_pauls_history(load_fallback_bundle()))
        match = re.search(r"_s=JSON\.parse\(`(.*?)`\),vs=", patched)
        self.assertIsNotNone(match)
        catalogue = json.loads(match.group(1))
        for source_key in WINCHESTER_SOURCES:
            self.assertIn(source_key, catalogue)

    def test_scope_count_includes_both_historical_extensions(self) -> None:
        winchester_row_delta = (
            len(WINCHESTER_GCSE_HISTORY)
            + (len(WINCHESTER_PRE_U_HISTORY) - 9)
            + len(WINCHESTER_MIXED_RESULTS_2021)
            + (len(WINCHESTER_ALEVEL_HISTORY) - 6)
            + (len(WINCHESTER_ACCESS_HISTORY) - 17)
            + len(WINCHESTER_DESTINATION_DISTRIBUTIONS)
        )
        self.assertIn(f"datasets:62,rows:{1192 + winchester_row_delta}", self.javascript)

    def test_pre_u_primary_archive_is_complete_and_ordered(self) -> None:
        self.assertEqual(
            [row["year"] for row in WINCHESTER_PRE_U_HISTORY],
            list(range(2010, 2021)),
        )
        expected = {
            2012: (341, 20.5, 50.1, 80.1, 97.9),
            2013: (426, 20.2, 50.5, 79.1, 98.1),
            2014: (468, 21.2, 51.1, 79.5, 97.2),
            2015: (443, 21.0, 47.4, 75.2, 97.3),
            2017: (470, 19.4, 47.9, 71.3, 96.6),
            2019: (476, 20.2, 42.4, 67.4, 96.6),
            2020: (469, 24.9, 56.1, 81.0, 99.1),
        }
        for year, values in expected.items():
            row = next(row for row in WINCHESTER_PRE_U_HISTORY if row["year"] == year)
            self.assertEqual(
                (
                    row["entries"],
                    row["d1"],
                    row["d1_d2"],
                    row["d1_d3_honest_astar_a"],
                    row["d1_m3"],
                ),
                values,
            )

    def test_pre_u_cumulative_bands_are_monotonic(self) -> None:
        keys = (
            "d1",
            "d1_d2",
            "d1_d3_honest_astar_a",
            "d1_m1_published",
            "d1_m2",
            "d1_m3",
            "pre_u_pass",
        )
        for row in WINCHESTER_PRE_U_HISTORY:
            values = [float(row[key]) for key in keys if row.get(key) is not None]
            self.assertTrue(all(0 <= value <= 100 for value in values), row["year"])
            self.assertEqual(values, sorted(values), row["year"])

    def test_2015_pre_u_never_mixes_source_versions(self) -> None:
        row = next(row for row in WINCHESTER_PRE_U_HISTORY if row["year"] == 2015)
        self.assertEqual(row["entries"], 443)
        self.assertEqual(
            (row["d1"], row["d1_d2"], row["d1_d3_honest_astar_a"]),
            (21.0, 47.4, 75.2),
        )
        self.assertNotIn("pre_u_pass", row)
        self.assertIn("444", row["note"])
        self.assertIn("arithmetically impossible", row["note"])

    def test_2019_pre_u_integer_reconciliation(self) -> None:
        row = next(row for row in WINCHESTER_PRE_U_HISTORY if row["year"] == 2019)
        self.assertEqual(row["d1_m1_published"], 81.5)
        self.assertEqual(row["d1_m2"], 92.6)
        self.assertAlmostEqual(388 / 476 * 100, 81.5, places=1)
        self.assertAlmostEqual(441 / 476 * 100, 92.6, places=1)

    def test_2020_pre_u_reconstruction_and_quarantine(self) -> None:
        row = next(row for row in WINCHESTER_PRE_U_HISTORY if row["year"] == 2020)
        counts = [
            row["d1_count"],
            row["d2_count"],
            row["d3_count"],
            row["m1_m3_count"],
            row["p1_p3_count"],
            row["u_count"],
        ]
        self.assertEqual(sum(counts), 469)
        self.assertAlmostEqual(row["d1_count"] / 469 * 100, 24.9, places=1)
        self.assertAlmostEqual(sum(counts[:2]) / 469 * 100, 56.1, places=1)
        self.assertAlmostEqual(sum(counts[:3]) / 469 * 100, 81.0, places=1)
        self.assertAlmostEqual(sum(counts[:4]) / 469 * 100, 99.1, places=1)
        self.assertAlmostEqual(sum(counts[:-1]) / 469 * 100, 99.8, places=1)
        self.assertIn("centre-assessed", row["note"])

    def test_2021_mixed_result_has_its_own_ruler(self) -> None:
        self.assertEqual(len(WINCHESTER_MIXED_RESULTS_2021), 1)
        row = WINCHESTER_MIXED_RESULTS_2021[0]
        self.assertEqual(row["entries"], 450)
        self.assertEqual(
            (row["a_star"], row["a_star_a"], row["a_star_b"], row["published_pass_rate"]),
            (52.4, 80.2, 92.2, 98.9),
        )
        self.assertIn('"dataset_id":"winchester_mixed_alevel_pre_u_2021"', self.javascript)
        self.assertIn("a-level-pre-u-crosswalk", self.javascript)

    def test_official_2003_2009_alevel_series_reconciles(self) -> None:
        self.assertEqual(
            [row["year"] for row in WINCHESTER_ALEVEL_HISTORY],
            [2003, 2004, 2005, 2006, 2007, 2008, 2009, 2022, 2023, 2024, 2025, 2026],
        )
        for row in WINCHESTER_ALEVEL_HISTORY[:7]:
            counted = sum(row[key] for key in ("a_count", "b_count", "c_count", "d_count", "e_count"))
            self.assertEqual(counted + row["unclassified_residual"], row["entries"], row["year"])
            self.assertAlmostEqual(row["a_count"] / row["entries"] * 100, row["grade_a"], places=1)
            self.assertAlmostEqual(
                (row["a_count"] + row["b_count"]) / row["entries"] * 100,
                row["grade_a_b"],
                places=1,
            )
        controlling = WINCHESTER_ALEVEL_HISTORY[0]
        self.assertEqual(
            (controlling["entries"], controlling["grade_a"], controlling["grade_a_b"]),
            (506, 75.9, 93.3),
        )
        self.assertIn("559", controlling["note"])
        current = next(row for row in WINCHESTER_ALEVEL_HISTORY if row["year"] == 2025)
        self.assertEqual(
            (current["a_star"], current["a_star_a"], current["a_star_b"]),
            (44.0, 75.0, 92.0),
        )
        self.assertEqual(current["confidence"], "P/CONFLICT")
        self.assertIn("42%, 74% and 91%", current["note"])
        pending = next(row for row in WINCHESTER_ALEVEL_HISTORY if row["year"] == 2026)
        self.assertIn("2 September 2026", pending["publication_status"])

    def test_university_rows_keep_outcome_types_separate(self) -> None:
        for row in WINCHESTER_ACCESS_HISTORY:
            self.assertTrue(row.get("outcome_type"), row)
            if "offer" in str(row.get("metric", "")):
                self.assertNotEqual(row["outcome_type"], "final destination")
        final_rows = WINCHESTER_DESTINATION_DISTRIBUTIONS
        self.assertTrue(all(row["outcome_type"] == "final leaver destination distribution" for row in final_rows))

    def test_current_offers_use_controlling_page_and_preserve_conflict(self) -> None:
        oxbridge = next(
            row for row in WINCHESTER_ACCESS_HISTORY
            if row["period"] == "2024/25" and row["metric"] == "oxbridge_offers"
        )
        self.assertEqual((oxbridge["value"], oxbridge["cohort"]), (39, 156))
        self.assertNotIn("rate_pct", oxbridge)
        self.assertEqual(oxbridge["arithmetic_offer_cohort_ratio_pct"], 25.0)
        us_main = next(
            row for row in WINCHESTER_ACCESS_HISTORY
            if row["period"] == "2024/25" and row["metric"] == "us_offers"
        )
        us_variant = next(
            row for row in WINCHESTER_ACCESS_HISTORY
            if row["metric"] == "us_offers_companion_page_variant"
        )
        self.assertEqual(
            (us_main["value"], us_main["ivy_offers"], us_main["ivy_league_plus_offers"]),
            (50, 9, 17),
        )
        self.assertEqual(us_variant["value"], 47)
        provisional = next(
            row
            for row in WINCHESTER_ACCESS_HISTORY
            if row["period"] == "2026" and row["metric"] == "oxbridge_offers_initial"
        )
        self.assertEqual(provisional["value"], 38)
        self.assertEqual(provisional["outcome_type"], "initial offers reported to date")
        self.assertIn("later revisions remain possible", provisional["publication_status"])
        self.assertIn("gives no US total", provisional["note"])

    def test_destination_rounding_is_never_renormalised(self) -> None:
        rows = {row["period"]: row for row in WINCHESTER_DESTINATION_DISTRIBUTIONS}
        self.assertEqual(rows["2010-2019"]["published_labels_total_pct"], 99)
        self.assertEqual(rows["2020"]["published_labels_total_pct"], 95)
        self.assertEqual(rows["2021"]["published_labels_total_pct"], 100)
        self.assertEqual(rows["2022"]["published_labels_total_pct"], 100)
        self.assertEqual((rows["2022"]["oxford"], rows["2022"]["cambridge"]), (11, 7))

    def test_all_new_row_sources_resolve(self) -> None:
        known = set(WINCHESTER_SOURCES) | {"FB140", "FB146", "WIN_2026_RESULTS_HUB", "WIN_2026_ALEVEL_POST"}
        collections = (
            WINCHESTER_PRE_U_HISTORY,
            WINCHESTER_MIXED_RESULTS_2021,
            WINCHESTER_ALEVEL_HISTORY,
            WINCHESTER_ACCESS_HISTORY,
            WINCHESTER_DESTINATION_DISTRIBUTIONS,
        )
        for rows in collections:
            for row in rows:
                self.assertTrue(row.get("source_ids"), row)
                self.assertFalse(set(row["source_ids"]) - known, row)
        for item in (*WINCHESTER_CORRECTIONS, *WINCHESTER_CONFLICTS):
            refs = item.get("source_refs", [])
            for value in item.get("values", []):
                if isinstance(value, dict) and value.get("source"):
                    refs = [*refs, value["source"]]
            self.assertFalse(set(refs) - known, item["id"])

    def test_corrections_and_conflicts_are_published(self) -> None:
        for item in WINCHESTER_CORRECTIONS:
            self.assertIn(f'"id":"{item["id"]}"', self.javascript)
        for item in WINCHESTER_CONFLICTS:
            self.assertIn(f'"id":"{item["id"]}"', self.javascript)
        self.assertIn("coherent 443-entry original table", self.javascript)
        self.assertIn("dedicated Exam Results & Futures page", self.javascript)

    def test_patch_is_fail_closed(self) -> None:
        with self.assertRaises(RuntimeError):
            apply_winchester_history(self.javascript)

    def test_fallback_bundle_accepts_the_same_patch(self) -> None:
        patched = apply_winchester_history(apply_st_pauls_history(load_fallback_bundle()))
        self.assertIn('"year":2012,"scale":"A*-G","entries":1191', patched)
        self.assertIn('"dataset_id":"winchester_mixed_alevel_pre_u_2021"', patched)
        self.assertIn('"year":2003,"entries":506,"grade_a":75.9,"grade_a_b":93.3', patched)


if __name__ == "__main__":
    unittest.main()
