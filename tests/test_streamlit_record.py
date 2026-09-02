"""The Streamlit build must present the record exactly as the published site did.

These tests exercise the ported selection, formatting and comparison logic
against values read off the published build, so a regression in presentation is
caught without needing a browser.
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tsr import components, comparison, dataset, format as fmt, records, styles  # noqa: E402
from tsr.chart import comparison_chart  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def normalise(markup: str) -> str:
    return re.sub(r"\s+", " ", markup).replace("> <", "><").strip()


class RecordSelectionTests(unittest.TestCase):
    def test_dataset_counts_match_the_published_school_index(self) -> None:
        counts = {
            school["id"]: len(records.school_datasets(school["id"]))
            for school in dataset.schools()
        }
        self.assertEqual(
            counts,
            {
                "eton": 9,
                "kcs": 11,
                "spgs": 5,
                "st-pauls": 21,
                "westminster": 8,
                "winchester": 9,
                "wycombe": 5,
            },
        )

    def test_latest_verified_years_match_the_published_school_index(self) -> None:
        years = {
            school["id"]: records.latest_verified_year(school["id"])
            for school in dataset.schools()
        }
        self.assertEqual(
            years,
            {
                "eton": 2025,
                "kcs": 2026,
                "spgs": 2026,
                "st-pauls": 2026,
                "westminster": 2026,
                "winchester": 2026,
                "wycombe": 2026,
            },
        )

    def test_collection_span_and_record_total(self) -> None:
        self.assertEqual(records.collection_span(), {"min": 1836, "max": 2026})
        self.assertEqual(records.frozen_record_count(), 2277)

    def test_winchester_section_counts(self) -> None:
        self.assertEqual(len(records.school_datasets("winchester", ["exam_results"])), 4)
        self.assertEqual(
            len(
                records.school_datasets(
                    "winchester", ["university_admissions", "university_destinations"]
                )
            ),
            5,
        )
        self.assertEqual(
            len(records.school_datasets("winchester", ["university_admissions"])), 3
        )

    def test_rows_are_ordered_newest_first(self) -> None:
        entry = next(
            item
            for item in dataset.figures()["datasets"]
            if item["dataset_id"] == "winchester_gcse"
        )
        years = [records.row_year(row) for row in records.sorted_rows(entry)]
        dated = [year for year in years if year is not None]
        self.assertEqual(dated, sorted(dated, reverse=True))


class FormattingTests(unittest.TestCase):
    def test_to_fixed_follows_javascript_rounding(self) -> None:
        self.assertEqual(fmt.to_fixed(0.25), "0.3")
        self.assertEqual(fmt.to_fixed(46.85), "46.9")
        self.assertEqual(fmt.to_fixed(90), "90.0")
        self.assertEqual(fmt.to_fixed(2.675), "2.7")

    def test_blank_values_are_preserved_as_dashes(self) -> None:
        self.assertEqual(fmt.format_value("entries", None, {}), "—")
        self.assertEqual(fmt.format_value("entries", "", {}), "—")

    def test_percentages_keep_their_published_precision(self) -> None:
        row = {"a_star": 44.0}
        self.assertEqual(fmt.format_value("a_star", 44.0, row), "44.0%")

    def test_winchester_pre_u_columns_keep_every_published_figure(self) -> None:
        """The published build capped ledgers at nine columns; the native
        record shows every figure a row carries and keeps only annotations
        behind the expanded view."""
        entry = next(
            item
            for item in dataset.figures()["datasets"]
            if item["dataset_id"] == "winchester_pre_u_two_ruler_2011_2019"
        )
        summary = fmt.table_fields(entry["rows"])
        self.assertEqual(
            summary[:9],
            ["year", "scale", "entries", "d1", "d1_d2", "d1_m2", "d1_m3", "pre_u_pass", "d1_d3_honest_astar_a"],
        )
        for field in ("d1_m1_published", "fold_pp", "d1_count", "u_count"):
            self.assertIn(field, summary)
        self.assertEqual(summary[-2:], ["confidence", "publication_status"])
        hidden = [field for field in fmt.table_fields(entry["rows"], expanded=True) if field not in summary]
        self.assertEqual(hidden, ["estimate_basis", "estimate_range_summary", "estimate_status", "note", "source_ids"])

    def test_latest_record_matches_the_published_card(self) -> None:
        markup = components.latest_record(
            records.school_datasets("winchester", ["exam_results"])
        )
        self.assertIn("A-level results", markup)
        self.assertIn("2026", markup)
        self.assertIn("Evidence status: Primary.", markup)


class ComparisonTests(unittest.TestCase):
    def setUp(self) -> None:
        self.metrics = comparison.metrics()
        self.by_id = {metric["id"]: metric for metric in self.metrics}

    def test_published_metric_set(self) -> None:
        self.assertEqual(len(self.metrics), 11)
        self.assertIn("a_level_astar", self.by_id)
        self.assertIn("oxford_offer_rate", self.by_id)
        self.assertIn("public-source-b6f5e1ed22afa0a6", self.by_id)

    def test_metric_year_range_matches_the_published_defaults(self) -> None:
        years = [point["year"] for metric in self.metrics for point in metric["points"]]
        self.assertEqual((min(years), max(years)), (1994, 2026))

    def test_exceptional_years_are_excluded_from_exam_series(self) -> None:
        for metric_id in ("a_level_astar", "gcse_grade_9"):
            years = {point["year"] for point in self.by_id[metric_id]["points"]}
            self.assertNotIn(2020, years)
            self.assertNotIn(2021, years)

    def test_offer_rate_is_derived_and_labelled(self) -> None:
        points = self.by_id["oxford_offer_rate"]["points"]
        self.assertTrue(
            all(
                point["annotation"] == "Derived at display time from frozen offers and applications"
                for point in points
            )
        )
        eton_2006 = next(
            point
            for point in points
            if point["schoolId"] == "eton" and point["year"] == 2006
        )
        self.assertEqual(eton_2006["value"], 52.2)

    def test_default_chart_is_identical_to_the_published_svg(self) -> None:
        published = (FIXTURES / "published_comparison_chart.svg").read_text(
            encoding="utf-8"
        )
        rendered = comparison_chart(self.by_id["a_level_astar"], "eton", "kcs", 1994, 2026)
        rendered_svg = re.search(
            r"<svg class=\"comparison-chart\".*?</svg>", rendered, re.S
        ).group(0)
        self.assertEqual(normalise(rendered_svg), normalise(published))


class StylesheetTests(unittest.TestCase):
    def test_every_selector_is_scoped_to_the_record(self) -> None:
        css = styles.site_css()
        index = 0
        unscoped = []
        while True:
            brace = css.find("{", index)
            if brace == -1:
                break
            prelude = re.split(r"[{}]", css[index:brace])[-1].strip()
            if prelude and not prelude.startswith("@") and ".tsr" not in prelude:
                unscoped.append(prelude[:80])
            index = brace + 1
        self.assertEqual(unscoped, [])

    def test_the_published_stylesheet_is_reused_verbatim(self) -> None:
        source = styles.SITE_CSS.read_text(encoding="utf-8")
        self.assertIn("tailwindcss v4.2.1", source)
        self.assertIn(".school-artwork", source)


if __name__ == "__main__":
    unittest.main()
