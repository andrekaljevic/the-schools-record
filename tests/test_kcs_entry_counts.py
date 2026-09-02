from __future__ import annotations

import base64
import gzip
import json
import re
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from kcs_entry_updates import (  # noqa: E402
    KCS_ENTRY_CORRECTIONS,
    KCS_ENTRY_SOURCES,
    apply_kcs_entry_updates,
)
from site_patches import apply_st_pauls_history, apply_winchester_history  # noqa: E402
from winchester_entry_updates import apply_winchester_gcse_entry_updates  # noqa: E402


def load_connector_bundle() -> str:
    parts = sorted((ROOT / "bundle" / "connector" / "js").glob("part-*"))
    encoded = "".join(part.read_text(encoding="ascii") for part in parts)
    return gzip.decompress(base64.b64decode(encoded)).decode("utf-8")


def load_fallback_bundle() -> str:
    with gzip.open(ROOT / "bundle" / "app.js.gz", "rt", encoding="utf-8") as handle:
        return handle.read()


def apply_all_patches(javascript: str) -> str:
    return apply_kcs_entry_updates(
        apply_winchester_gcse_entry_updates(
            apply_winchester_history(apply_st_pauls_history(javascript))
        )
    )


class KCSEntryCountPatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.javascript = apply_all_patches(load_connector_bundle())

    def test_modern_combined_sixth_form_denominators(self) -> None:
        for fragment in (
            "{year:2018,candidates:193,alevel_pathway_pupils:114,alevel_takers:114,alevel_entries:379,ib_candidates:79,ib_hl_entries:239,entries:618",
            "{year:2019,candidates:206,alevel_pathway_pupils:131,alevel_takers:131,alevel_entries:447,ib_candidates:75,ib_hl_entries:227,entries:674",
            "{year:2022,candidates:204,alevel_pathway_pupils:137,alevel_takers:137,alevel_entries:496,ib_candidates:67,ib_hl_entries:201,entries:697",
            "{year:2023,candidates:212,alevel_pathway_pupils:159,alevel_takers:159,alevel_entries:575,ib_candidates:53,ib_hl_entries:160,entries:735",
            "{year:2024,candidates:216,alevel_pathway_pupils:161,alevel_takers:162,alevel_entries:590,ib_candidates:55,ib_hl_entries:165,entries:755",
            "{year:2025,candidates:235,alevel_pathway_pupils:182,alevel_takers:183,alevel_entries:666,ib_candidates:53,ib_hl_entries:159,entries:825",
        ):
            self.assertIn(fragment, self.javascript)

    def test_route_and_actual_alevel_takers_remain_distinct(self) -> None:
        self.assertIn(
            "{year:2024,candidates:162,alevel_pathway_pupils:161,entries:590",
            self.javascript,
        )
        self.assertIn(
            "{year:2025,candidates:183,alevel_pathway_pupils:182,entries:666",
            self.javascript,
        )
        self.assertIn("included once in the 216-pupil cohort", self.javascript)
        self.assertIn("included once in the 235-pupil cohort", self.javascript)
        self.assertIn(
            "These are destination-list denominators, not examination candidate cohorts",
            self.javascript,
        )

    def test_modern_ib_denominators(self) -> None:
        for fragment in (
            "{year:2018,candidates:79,entries:239,grade_7:60.7",
            "{year:2019,candidates:75,entries:227,grade_7:56.4",
            "{year:2022,candidates:67,entries:201,grade_7:72.1",
            "{year:2023,candidates:53,entries:160,grade_7:63.75",
            "{year:2024,candidates:55,entries:165,grade_7:61.8",
            "{year:2025,candidates:53,entries:159,grade_7:69.8",
        ):
            self.assertIn(fragment, self.javascript)

    def test_modern_gcse_candidate_and_entry_denominators(self) -> None:
        for fragment in (
            "{year:2017,scale:`transition`,candidates:159",
            "{year:2018,scale:`transition`,candidates:147,entries:1555,numbered_entries:467,lettered_entries:1088,additional_maths_entries_excluded:88",
            "{year:2019,scale:`9-1`,candidates:153,entries:1698,numbered_entries:1438,lettered_entries:260",
            "{year:2022,scale:`9-1`,candidates:163,entries:1785",
            "{year:2023,scale:`9-1`,candidates:155,entries:1706",
            "{year:2024,scale:`9-1`,candidates:169,entries:1841",
            "{year:2025,scale:`9-1`,candidates:156,entries:1687",
        ):
            self.assertIn(fragment, self.javascript)

    def test_detailed_gcse_rows_have_full_context(self) -> None:
        self.assertIn(
            "{year:2018,candidates:147,entries:1555,numbered_entries:467,lettered_entries:1088,additional_maths_entries_excluded:88,grade_9:58.9",
            self.javascript,
        )
        self.assertIn(
            "{year:2019,candidates:153,entries:1698,numbered_entries:1438,lettered_entries:260,grade_9:57.1",
            self.javascript,
        )
        self.assertNotIn(
            "{year:2018,grade_9:58.9,grade_9_8:86.1,grade_9_7:95.9",
            self.javascript,
        )

    def test_historic_primary_counts_are_added_without_false_denominators(self) -> None:
        for fragment in (
            '"year":1990,"candidates":122,"entries":383',
            '"year":1991,"candidates":132,"entries":420',
            '"year":1997,"candidates":133,"entries":424',
            '"year":2003,"candidates":91,"entries":287',
            '"year":2004,"candidates":81,"entries":260',
            '"year":1990,"scale":"A–G","candidates":266,"upper_fifth_candidates":132,"lower_fifth_candidates":134,"entries":1331',
            '"year":1997,"scale":"A*–G","candidates":153,"entries":1584',
            '"year":2003,"scale":"A*–G","candidates":144,"entries":1353',
            '"year":2004,"scale":"A*–G","candidates":141,"entries":1333',
        ):
            self.assertIn(fragment, self.javascript)
        self.assertIn('"reported_a_c_entries":1296', self.javascript)
        self.assertNotIn('"year":1991,"scale":"A–G","candidates":266,"entries":1296', self.javascript)

    def test_secondary_and_lower_bound_counts_are_typed(self) -> None:
        self.assertIn('"year":2008,"ib_candidates_min":120,"confidence":"S"', self.javascript)
        self.assertIn('"year":2007,"candidates":155,"alevel_pathway_pupils":44', self.javascript)
        self.assertIn('"year":2011,"candidates":145,"entries":436', self.javascript)
        self.assertIn("one above the standard three-per-candidate expectation", self.javascript)

    def test_combined_series_has_one_row_per_year(self) -> None:
        match = re.search(
            r"\{dataset_id:`kcs_combined_alevel_ib`.*?\}\]\}(?=,\{dataset_id:)",
            self.javascript,
        )
        self.assertIsNotNone(match)
        combined = match.group(0)
        for year in (2011, 2014, 2016):
            self.assertEqual(combined.count(f"year:{year},"), 1)

    def test_count_fields_have_human_labels_and_are_visible(self) -> None:
        for fragment in (
            "alevel_pathway_pupils:{label:`A-level pathway pupils`,kind:`count`}",
            "alevel_takers:{label:`Actual A-level takers`,kind:`count`}",
            "ib_hl_entries:{label:`IB Higher-Level entries`,kind:`count`}",
            "additional_maths_entries_excluded:{label:`Additional Mathematics entries · excluded`,kind:`count`}",
            "reported_a_c_entries:{label:`Reported A–C entries · partial`,kind:`count`}",
        ):
            self.assertIn(fragment, self.javascript)
        self.assertIn(
            "`candidates`,`alevel_pathway_pupils`,`alevel_takers`,`alevel_entries`,`ib_candidates`",
            self.javascript,
        )

    def test_source_catalogue_and_corrections_are_auditable(self) -> None:
        for source_key, source in KCS_ENTRY_SOURCES.items():
            self.assertIn(f'"{source_key}":', self.javascript)
            self.assertNotIn("url", source)
        for correction in KCS_ENTRY_CORRECTIONS:
            self.assertIn(f'"id":"{correction["id"]}"', self.javascript)
        kcs_block = re.search(
            r"\{dataset_id:`kcs_combined_alevel_ib`.*?\{dataset_id:`spgs_exam_anchors`",
            self.javascript,
        ).group(0)
        arrays = re.findall(r"(?:source_ids|source_refs):\[([^\]]*)\]", kcs_block)
        source_ids = {
            source_id
            for array in arrays
            for source_id in re.findall(r"`([^`]+)`", array)
            if source_id.startswith("KCS_")
        }
        known_sources = set(KCS_ENTRY_SOURCES) | {
            "KCS_2026_ALEVEL_RELEASE",
            "KCS_2026_GCSE_RELEASE",
            "KCS_2026_IB_RELEASE",
        }
        self.assertTrue(source_ids)
        self.assertEqual(source_ids - known_sources, set())
        public_sources = json.dumps(KCS_ENTRY_SOURCES)
        self.assertNotIn("drive.google.com", public_sources)
        self.assertNotIn("docs.google.com", public_sources)

    def test_fallback_bundle_accepts_the_same_patch(self) -> None:
        patched = apply_all_patches(load_fallback_bundle())
        self.assertIn(
            "{year:2025,candidates:235,alevel_pathway_pupils:182,alevel_takers:183",
            patched,
        )
        match = re.search(r"_s=JSON\.parse\(`(.*?)`\),vs=", patched)
        self.assertIsNotNone(match)
        catalogue = json.loads(match.group(1))
        for source_key in KCS_ENTRY_SOURCES:
            self.assertIn(source_key, catalogue)

    def test_patch_is_fail_closed(self) -> None:
        with self.assertRaises(RuntimeError):
            apply_kcs_entry_updates(self.javascript)


if __name__ == "__main__":
    unittest.main()
