from __future__ import annotations

import base64
import gzip
import json
import unittest
from pathlib import Path

from site_patches import (
    WINCHESTER_GCSE_HISTORY,
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

    def test_recovered_bands_and_suppression_ranges_are_present(self) -> None:
        for fragment in (
            '"year":1996,"scale":"A*-G","top_equivalent":null,"astar_a_equivalent":86.0,"astar_b_or_9_6":97.7',
            '"year":1997,"scale":"A*-G","entries":849,"top_equivalent":null,"astar_a_equivalent":85.0,"astar_b_or_9_6":97.4',
            '"year":2004,"scale":"A*-G","top_equivalent":null,"astar_a_equivalent":87.0,"astar_b_or_9_6":null',
            '"year":2005,"scale":"A*-G","candidates":132,"top_equivalent":50.9,"astar_a_equivalent":90.9,"astar_b_or_9_6":null',
            '"year":2006,"scale":"A*-G","entries":1069,"top_equivalent":47.0,"astar_a_equivalent":87.1,"astar_b_or_9_6":97.3',
            '"year":2011,"scale":"A*-G","top_equivalent":null,"astar_a_equivalent":"90.40–90.69","astar_b_or_9_6":null',
            '"year":2012,"scale":"A*-G","entries":1191,"top_equivalent":"68.51–69.02","astar_a_equivalent":"93.03–93.53","astar_b_or_9_6":"98.49–98.99"',
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

    def test_2012_bounds_follow_six_suppressed_entries(self) -> None:
        self.assertAlmostEqual(816 / 1191 * 100, 68.51, places=2)
        self.assertAlmostEqual((816 + 6) / 1191 * 100, 69.02, places=2)
        self.assertAlmostEqual((816 + 292) / 1191 * 100, 93.03, places=2)
        self.assertAlmostEqual((816 + 292 + 6) / 1191 * 100, 93.53, places=2)
        self.assertAlmostEqual((816 + 292 + 65) / 1191 * 100, 98.49, places=2)
        self.assertAlmostEqual((816 + 292 + 65 + 6) / 1191 * 100, 98.99, places=2)

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

    def test_scope_count_includes_both_historical_extensions(self) -> None:
        self.assertIn(
            f"datasets:45,rows:{580 + len(WINCHESTER_GCSE_HISTORY)}",
            self.javascript,
        )

    def test_patch_is_fail_closed(self) -> None:
        with self.assertRaises(RuntimeError):
            apply_winchester_history(self.javascript)

    def test_fallback_bundle_accepts_the_same_patch(self) -> None:
        patched = apply_winchester_history(apply_st_pauls_history(load_fallback_bundle()))
        self.assertIn('"year":2012,"scale":"A*-G","entries":1191', patched)


if __name__ == "__main__":
    unittest.main()
