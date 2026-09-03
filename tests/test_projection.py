"""The public projection is deterministic, whitelisted and free of private locations.

The static frontend is built only from ``web/src/generated``; these tests hold
that projection to the same rules as the application: every count and hash
matches the frozen dataset, no private pattern reaches it, building it never
touches ``data/``, and the chart fixture the TypeScript parity test relies on
is the canonical renderer's current output.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tsr import chart, comparison, components, corpora, dataset, evidence, projection, records  # noqa: E402

DATASET_PATH = ROOT / "data" / "dataset.json"
DATASET_SHA256 = "245f2d8176f8fca0d53f41689f096734dd13e9023af9a67931314334251b9f6f"
PRIVATE_PATTERNS = (
    re.compile(r"drive\.google\.com", re.I),
    re.compile(r"docs\.google\.com", re.I),
    re.compile(r"private-source-[0-9a-f]{16}"),
    re.compile(r"/d/[A-Za-z0-9_-]{25,}"),
    re.compile(r"[?&]id=[A-Za-z0-9_-]{25,}"),
    re.compile(r"/home/[a-z0-9_-]+/"),
)


def _documents() -> dict[str, str]:
    if not hasattr(_documents, "cache"):
        _documents.cache = {name: projection.serialise(doc) for name, doc in projection.build().items()}  # type: ignore[attr-defined]
    return _documents.cache  # type: ignore[attr-defined]


class ProjectionContractTests(unittest.TestCase):
    def test_building_the_projection_leaves_the_frozen_dataset_untouched(self) -> None:
        before = DATASET_PATH.read_bytes()
        _documents()
        self.assertEqual(DATASET_PATH.read_bytes(), before)
        self.assertEqual(hashlib.sha256(before).hexdigest(), DATASET_SHA256)

    def test_the_projection_is_deterministic(self) -> None:
        first = _documents()
        second = {name: projection.serialise(doc) for name, doc in projection.build().items()}
        self.assertEqual(first, second)

    def test_no_private_location_or_identifier_reaches_the_projection(self) -> None:
        for name, text in _documents().items():
            for pattern in PRIVATE_PATTERNS:
                self.assertIsNone(pattern.search(text), f"{name} carries {pattern.pattern}")
            projection.scan(text, name)

    def test_the_site_document_pins_the_frozen_counts(self) -> None:
        site = json.loads(_documents()["site"])
        self.assertEqual(site["snapshot"], "production-818c7c2-data-frozen-v1")
        self.assertEqual(site["baselineCommit"], "818c7c296fed184480d5de05cbd34ad3ba481a46")
        self.assertEqual(site["counts"], {"figures": 1274, "granular": 83, "oxbridge": 571, "us": 349, "total": 2277})
        self.assertEqual(site["redactions"], 286)
        self.assertEqual(len(site["schools"]), 7)
        self.assertEqual(site["corrections"], len(corpora.corrections()))
        self.assertEqual(site["conflicts"], len(corpora.conflicts()))

    def test_every_frozen_record_has_exactly_one_permanent_address(self) -> None:
        records = json.loads(_documents()["evidence-records"])
        self.assertEqual(len(records), 2277)
        slugs = [record["slug"] for record in records]
        self.assertEqual(len(set(slugs)), len(slugs))
        self.assertEqual({record["id"] for record in records}, {item.id for item in evidence.index()})
        search = json.loads(_documents()["evidence-search"])
        self.assertEqual([entry["id"] for entry in search], [record["id"] for record in records])

    def test_every_ledger_row_is_present_with_its_anchor_and_record(self) -> None:
        total_rows = 0
        for school in dataset.schools():
            doc = json.loads(_documents()[f"schools/{school['id']}"])
            for ledger in [*doc["exam"], *doc["university"]]:
                self.assertEqual(len(ledger["rows"]), ledger["rowCount"])
                self.assertEqual(len(ledger["fields"]), len(ledger["summaryFields"]) + len(ledger["hiddenFields"]))
                for row in ledger["rows"]:
                    self.assertTrue(row["anchor"].startswith(ledger["id"] + "-"))
                    self.assertIsNotNone(row["recordId"], (ledger["id"], row["period"]))
                    self.assertTrue(row["recordId"].startswith("fig:"))
                total_rows += len(ledger["rows"])
        # Every figures row appears at least once (shared ledgers appear under every school they name).
        self.assertGreaterEqual(total_rows, 1274)

    def test_row_anchors_are_unique_and_record_ids_are_the_rows_own(self) -> None:
        for school in dataset.schools():
            doc = json.loads(_documents()[f"schools/{school['id']}"])
            anchors: list[str] = []
            for ledger in [*doc["exam"], *doc["university"]]:
                entry = next(item for item in dataset.figures()["datasets"] if item["dataset_id"] == ledger["id"])
                for row in ledger["rows"]:
                    anchors.append(row["anchor"])
                    self.assertEqual(row["recordId"], f"fig:{ledger['id']}:{row['index']}")
                    self.assertEqual(records.period_label(entry["rows"][row["index"]]), row["period"])
                    self.assertTrue(row["anchor"].startswith(f"{ledger['id']}-"))
            self.assertEqual(len(anchors), len(set(anchors)), school["id"])
        eton = json.loads(_documents()["schools/eton"])
        gcse = next(item for item in eton["exam"] if item["id"] == "eton_gcse_primary")
        self.assertEqual(sorted(row["anchor"] for row in gcse["rows"] if row["period"] == "2018"), ["eton_gcse_primary-2018", "eton_gcse_primary-2018-r1"])
        self.assertEqual(components.row_anchor("winchester_gcse", {"year": 2016}), "winchester_gcse-2016")

    def test_gaps_and_corrections_are_stated_per_ledger_and_row(self) -> None:
        westminster = json.loads(_documents()["schools/westminster"])
        alevel = next(item for item in westminster["exam"] if item["family"].startswith("A level") or "alevel" in item["id"])
        self.assertTrue(set(alevel["missingYears"]) >= {2020, 2021}, alevel["missingYears"])
        for school in dataset.schools():
            doc = json.loads(_documents()[f"schools/{school['id']}"])
            for ledger in [*doc["exam"], *doc["university"]]:
                years = {row["year"] for row in ledger["rows"] if row["year"] is not None}
                self.assertFalse(set(ledger["missingYears"]) & years)
                for row in ledger["rows"]:
                    for correction_id in row["corrections"]:
                        item = next(c for c in corpora.corrections() if c["id"] == correction_id)
                        self.assertEqual(str(item["period"]), row["period"])
        corrections = json.loads(_documents()["corrections"])["corrections"]
        with_rows = [item for item in corrections if item["rows"]]
        self.assertGreater(len(with_rows), 10)
        for item in with_rows:
            for row in item["rows"]:
                self.assertRegex(row["href"], r"^/schools/[a-z-]+/(exam-results|university-destinations)/#")

    def test_csv_downloads_join_lists_and_keep_blanks(self) -> None:
        doc = json.loads(_documents()["schools/winchester"])
        gcse = next(item for item in doc["exam"] if item["id"] == "winchester_gcse")
        self.assertNotIn("['", gcse["csv"])
        self.assertIn("2016", gcse["csv"])
        header = gcse["csv"].splitlines()[0].split(",")
        self.assertTrue({field["key"] for field in gcse["fields"]} <= set(header))
        self.assertEqual(len(gcse["csv"].splitlines()), gcse["rowCount"] + 1)

    def test_search_entries_are_compact_pairs(self) -> None:
        entry = json.loads(_documents()["evidence-search"])[0]
        self.assertNotIn("s", entry)
        self.assertTrue(all(isinstance(pair, list) and len(pair) == 2 for pair in entry["v"]))

    def test_formatted_cells_match_the_application_formatting(self) -> None:
        doc = json.loads(_documents()["schools/winchester"])
        ledger = next(item for item in doc["exam"] if item["id"] == "winchester_pre_u_two_ruler_2011_2019")
        row = next(item for item in ledger["rows"] if item["period"] == "2010")
        self.assertEqual(row["cells"]["entries"], "339")
        self.assertEqual(row["cells"]["d1"], "18.9%")
        self.assertEqual(row["cells"]["d1_d2"], "52.2%")
        self.assertEqual(row["cells"]["d1_m2"], "95.0%")
        self.assertEqual(row["cells"]["d1_d3_honest_astar_a"], "79.1")
        gcse = next(item for item in doc["exam"] if item["id"] == "winchester_gcse")
        self.assertIn("winchester_gcse-2016", [item["anchor"] for item in gcse["rows"]])

    def test_the_projection_carries_only_public_source_descriptions(self) -> None:
        for name, text in _documents().items():
            doc = json.loads(text)
            self._walk_sources(doc, name)

    def _walk_sources(self, node, where: str) -> None:
        if isinstance(node, dict):
            if {"ref", "title", "withheld", "url"} <= set(node):
                if node["url"] is not None:
                    self.assertTrue(node["url"].startswith(("https://", "http://")), where)
                    self.assertNotRegex(node["url"], r"(drive|docs)\.google\.com", where)
                if node["withheld"]:
                    self.assertEqual(node["title"], "Source title withheld", where)
            for key, value in node.items():
                self.assertNotIn(key, {"source_url", "sourceUrl", "drive_id", "path", "local_path"}, where)
                self._walk_sources(value, where)
        elif isinstance(node, list):
            for item in node:
                self._walk_sources(item, where)

    def test_the_chart_fixture_is_the_canonical_renderers_current_output(self) -> None:
        fixture_path = ROOT / "web" / "tests" / "fixtures" / "comparison-charts.json"
        self.assertTrue(fixture_path.exists(), "run tools/build_chart_fixtures.py")
        fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
        metrics = {metric["id"]: metric for metric in comparison.metrics()}
        self.assertEqual(set(fixture["metrics"][i]["id"] for i in range(len(fixture["metrics"]))), set(metrics))
        names = {school["id"]: school["name"] for school in dataset.schools()}
        from tsr import trajectory
        for case in fixture["cases"][::73]:
            metric = metrics[case["metric"]]
            layout = chart.COMPARISON_MOBILE if case["layout"] == "mobile" else chart.COMPARISON_DESKTOP
            markers = (trajectory.EXCEPTIONAL_YEARS,) if metric["domain"] == "results" else ()
            svg = chart.comparison_panel(metric, case["first"], case["second"], case["yearFrom"], case["yearTo"], layout, names=names, markers=markers)
            self.assertEqual(hashlib.sha256(svg.encode("utf-8")).hexdigest(), case["sha256"], case)

    def test_the_command_line_tool_checks_and_writes_outside_data(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                [sys.executable, str(ROOT / "tools" / "build_public_projection.py"), "--output", tmp],
                capture_output=True, text=True, check=False, cwd=ROOT,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            written = sorted(path.relative_to(tmp).as_posix() for path in Path(tmp).rglob("*.json"))
            self.assertIn("manifest.json", written)
            self.assertIn("schools/winchester.json", written)
            manifest = json.loads((Path(tmp) / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["datasetSha256"], DATASET_SHA256)
            self.assertEqual(manifest["counts"]["total"], 2277)
            check = subprocess.run(
                [sys.executable, str(ROOT / "tools" / "build_public_projection.py"), "--check", "--output", tmp],
                capture_output=True, text=True, check=False, cwd=ROOT,
            )
            self.assertEqual(check.returncode, 0, check.stderr)
        self.assertEqual(hashlib.sha256(DATASET_PATH.read_bytes()).hexdigest(), DATASET_SHA256)


if __name__ == "__main__":
    unittest.main()
