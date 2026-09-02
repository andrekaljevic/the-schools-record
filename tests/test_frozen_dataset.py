"""The dataset must equal the published bundle plus the recorded revisions.

``data/dataset.json`` is the immutable data module of the published front-end
bundle with every statistical change since then applied from
``data/revisions.json``.  These tests fail if a figure, a record count or the
snapshot identity drifts from that reproducible state, and — where Node is
available — rebuild the file from the bundle and the recorded revisions and
compare byte for byte.
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

# Published snapshot production-818c7c2-data-frozen-v1 plus revision v2.
DATASET_SHA256 = "23e1f1e3376385322c0e60b6011da5ba87d7f483f0f8217e51610fa591144279"
FROZEN_SNAPSHOT_SHA256 = "245f2d8176f8fca0d53f41689f096734dd13e9023af9a67931314334251b9f6f"
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
        self.assertEqual(metadata["snapshot_version"], "production-818c7c2-data-revised-v2")
        self.assertEqual([item["id"] for item in metadata["revisions"]], ["v2"])
        self.assertEqual(
            metadata["revisions"][0]["entries"],
            ["R-C01", "R-C02", "R-C03", "R-C05", "R-C06"],
        )
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

    def test_revision_v2_reverses_only_locked_examination_corrections(self) -> None:
        """Post-remark results control: the reversed entries are exactly these."""
        ledger = {item["id"]: item for item in self.data["corpora"]["figures"]["corrections"]}
        reversed_ids = ["C01", "C02", "C03", "C05", "C06"]
        for correction_id in reversed_ids:
            self.assertEqual(ledger[correction_id]["status"], "superseded", correction_id)
            reversal = ledger[f"R-{correction_id}"]
            self.assertEqual(reversal["reverses"], correction_id)
            self.assertEqual(reversal["status"], "locked")
            self.assertEqual(reversal["revision"], "v2")
        for correction_id in ("C04", "C07", "C08", "C09"):
            self.assertEqual(ledger[correction_id]["status"], "locked", correction_id)
            self.assertNotIn(f"R-{correction_id}", ledger)
        self.assertEqual(len(ledger), 34)

    def test_revised_rows_carry_the_post_remark_values(self) -> None:
        row = next(row for row in self._dataset("winchester_gcse")["rows"] if row.get("year") == 2016)
        self.assertEqual((row["top_equivalent"], row["astar_a_equivalent"]), (69.1, 94.1))
        row = next(row for row in self._dataset("winchester_gcse")["rows"] if row.get("year") == 2019)
        self.assertEqual(
            (row["grade_9"], row["top_equivalent"], row["astar_a_equivalent"], row["astar_b_or_9_6"]),
            (44.4, 72.4, 87.5, 95.3),
        )
        row = next(row for row in self._dataset("winchester_pre_u_two_ruler_2011_2019")["rows"] if row.get("year") == 2012)
        self.assertEqual(row["d1_d3_honest_astar_a"], 79)
        row = next(row for row in self._dataset("st_pauls_gcse")["rows"] if row.get("year") == 2012)
        self.assertEqual(row["top_3"], 98.8)
        row = next(row for row in self._dataset("st_pauls_alevel")["rows"] if row.get("year") == 2014)
        self.assertEqual(row["a_star"], 47.8)
        self.assertIn("revision v2", row["note"])

    def test_unrevised_locked_corrections_are_untouched(self) -> None:
        row = next(row for row in self._dataset("cambridge_and_combined_westminster_school")["rows"] if row.get("cycle") == 2025)
        self.assertEqual(
            (row["strict_oxbridge"]["applications"], row["strict_oxbridge"]["offers"], row["strict_oxbridge"]["acceptances"]),
            (166, 80, 73),
        )

    def test_every_recorded_revision_matches_a_frozen_value(self) -> None:
        """A revision must name the exact value it replaced, so it cannot drift."""
        spec = json.loads((ROOT / "data" / "revisions.json").read_text(encoding="utf-8"))
        for revision in spec["revisions"]:
            for change in revision["changes"]:
                entry = self._dataset(change["dataset_id"])
                row = next(row for row in entry["rows"] if all(row.get(k) == v for k, v in change["row"].items()))
                for item in change["fields"]:
                    self.assertEqual(row[item["field"]], item["to"], (change["reversal"], item["field"]))
                self.assertEqual(row["note"], change["note_to"], change["reversal"])

    @unittest.skipIf(shutil.which("node") is None, "Node is required to re-extract")
    def test_equals_the_published_bundle_plus_recorded_revisions(self) -> None:
        result = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "apply_revisions.py"), "--check"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    @unittest.skipIf(shutil.which("node") is None, "Node is required to re-extract")
    def test_the_frozen_snapshot_itself_is_still_reproducible(self) -> None:
        from tools.extract_dataset import extract, serialise

        digest = hashlib.sha256(serialise(extract()).encode("utf-8")).hexdigest()
        self.assertEqual(digest, FROZEN_SNAPSHOT_SHA256)


if __name__ == "__main__":
    unittest.main()
