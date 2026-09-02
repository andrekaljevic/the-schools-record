"""The frozen production dataset must never change.

``data/dataset.json`` is a verbatim extraction of the immutable data module in
the published front-end bundle.  These tests fail if a figure, a record count
or the snapshot identity is altered, and — where Node is available — re-extract
the bundle and compare byte for byte.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DATASET_PATH = ROOT / "data" / "dataset.json"

# Recorded from the published snapshot production-818c7c2-data-frozen-v1.
DATASET_SHA256 = "245f2d8176f8fca0d53f41689f096734dd13e9023af9a67931314334251b9f6f"
FIGURE_ROWS = 1274
GRANULAR_ROWS = 83
OXBRIDGE_RECORDS = 571
US_RECORDS = 349
TOTAL_RECORDS = 2277


def load() -> dict:
    with DATASET_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


class FrozenDatasetTests(unittest.TestCase):
    def setUp(self) -> None:
        self.data = load()

    def test_file_checksum_is_unchanged(self) -> None:
        digest = hashlib.sha256(DATASET_PATH.read_bytes()).hexdigest()
        self.assertEqual(digest, DATASET_SHA256)

    def test_snapshot_identity(self) -> None:
        metadata = self.data["metadata"]
        self.assertEqual(metadata["snapshot_version"], "production-818c7c2-data-frozen-v1")
        self.assertEqual(
            metadata["baseline_commit"], "818c7c296fed184480d5de05cbd34ad3ba481a46"
        )
        self.assertEqual(metadata["source_location_redactions"], 286)

    def test_record_counts(self) -> None:
        corpora = self.data["corpora"]
        self.assertEqual(
            sum(len(entry["rows"]) for entry in corpora["figures"]["datasets"]),
            FIGURE_ROWS,
        )
        self.assertEqual(
            sum(len(entry["rows"]) for entry in corpora["granular"]["datasets"]),
            GRANULAR_ROWS,
        )
        self.assertEqual(len(corpora["oxbridge"]["records"]), OXBRIDGE_RECORDS)
        self.assertEqual(corpora["oxbridge"]["record_count"], OXBRIDGE_RECORDS)
        self.assertEqual(len(corpora["us"]["records"]), US_RECORDS)
        self.assertEqual(
            FIGURE_ROWS + GRANULAR_ROWS + OXBRIDGE_RECORDS + US_RECORDS, TOTAL_RECORDS
        )

    def test_seven_schools_with_their_published_windows(self) -> None:
        windows = {
            school["id"]: school["evidenceWindow"] for school in self.data["schools"]
        }
        self.assertEqual(
            windows,
            {
                "eton": "2006–2026",
                "kcs": "2006–2026",
                "spgs": "2009–2026",
                "st-pauls": "1992–2026",
                "westminster": "1988–2026",
                "winchester": "1994–2026",
                "wycombe": "2009–2026",
            },
        )

    def _dataset(self, dataset_id: str) -> dict:
        return next(
            entry
            for entry in self.data["corpora"]["figures"]["datasets"]
            if entry["dataset_id"] == dataset_id
        )

    def test_winchester_modelled_2010_pre_u_row_is_intact(self) -> None:
        row = next(
            row
            for row in self._dataset("winchester_pre_u_two_ruler_2011_2019")["rows"]
            if row.get("year") == 2010
        )
        self.assertEqual(row["entries"], 339)
        self.assertEqual(row["d1"], 18.9)
        self.assertEqual(row["d1_d2"], 52.2)
        self.assertEqual(row["d1_d3_honest_astar_a"], 79.1)
        self.assertEqual(row["d1_m1_published"], 90)
        self.assertEqual(row["d1_m2"], 95)
        self.assertEqual(row["confidence"], "P/D/MODELLED")

    def test_st_pauls_2015_oxbridge_destinations_are_intact(self) -> None:
        row = next(
            row
            for row in self._dataset("st_pauls_destinations")["rows"]
            if row.get("year") == 2015
        )
        self.assertEqual(row["cambridge"], 21)
        self.assertEqual(row["oxbridge"], 41)
        self.assertEqual(row["leavers"], 184)

    def test_eton_first_oxford_cycle_is_intact(self) -> None:
        row = self._dataset("oxford_strict_eton_college")["rows"][0]
        self.assertEqual(row["cycle"], 2006)
        self.assertEqual(row["applications"], 134)
        self.assertEqual(row["offers"], 70)
        self.assertEqual(row["acceptances"], 65)

    @unittest.skipIf(shutil.which("node") is None, "Node is required to re-extract")
    def test_matches_a_fresh_extraction_from_the_published_bundle(self) -> None:
        result = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "extract_dataset.py"), "--check"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
