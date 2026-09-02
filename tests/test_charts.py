"""The record's small-multiple charts are deterministic and draw frozen values only.

The index panels and the school "results by year" panels are built from the
comparison tool's own series.  These tests pin their markup, check that a line
never joins non-consecutive years, that every plotted value is a frozen value
shown at the record's display precision, and that drawing every chart leaves the
frozen dataset untouched.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tsr import chart, comparison, dataset, records, trajectory  # noqa: E402
from tsr.format import to_fixed  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures"
DATASET_PATH = ROOT / "data" / "dataset.json"
DATASET_SHA256 = "245f2d8176f8fca0d53f41689f096734dd13e9023af9a67931314334251b9f6f"


def normalise(markup: str) -> str:
    return re.sub(r"\s+", " ", markup).replace("> <", "><").strip()


def _point(year: int, value: float, status: str = "Primary") -> dict:
    return {
        "schoolId": "test",
        "schoolName": "Test School",
        "year": year,
        "value": value,
        "status": status,
        "datasetId": "test_dataset",
        "annotation": None,
    }


class PanelGeometryTests(unittest.TestCase):
    def test_runs_break_at_every_missing_year(self) -> None:
        points = [_point(y, 1) for y in (2015, 2016, 2017, 2019, 2022, 2023)]
        self.assertEqual(
            [[p["year"] for p in run] for run in chart.runs(points)],
            [[2015, 2016, 2017], [2019], [2022, 2023]],
        )

    def test_percent_rulers_always_run_to_100(self) -> None:
        self.assertEqual(chart.ceiling_for([12.5, 61.2], "percent"), 100)
        self.assertEqual(chart.ceiling_for([99.9], "percent"), 100)

    def test_count_rulers_round_up_to_a_grid_value(self) -> None:
        self.assertEqual(chart.ceiling_for([17, 90], "count"), 90)
        self.assertEqual(chart.ceiling_for([91], "count"), 100)
        self.assertEqual(chart.ceiling_for([], "count"), 10)

    def test_a_lone_year_is_padded_so_the_point_is_not_on_the_frame(self) -> None:
        self.assertEqual(chart.display_range(2026, 2026), (2025, 2027))
        self.assertEqual(chart.display_range(2010, 2026), (2010, 2026))

    def test_year_ticks_keep_both_ends(self) -> None:
        ticks = chart.year_ticks(1994, 2026, 8)
        self.assertEqual(ticks[0], 1994)
        self.assertEqual(ticks[-1], 2026)
        self.assertEqual(ticks, sorted(set(ticks)))

    def test_lines_join_consecutive_years_only(self) -> None:
        series = (chart.Series("A*", tuple(_point(y, 40 + y % 5) for y in (2015, 2016, 2019, 2022, 2023)), "#125c58"),)
        svg = chart.panel_svg(
            series, 2015, 2023, "percent", chart.TRAJECTORY_DESKTOP,
            uid="t", title="t", description="t",
        )
        paths = re.findall(r'<path d="([^"]+)"', svg)
        self.assertEqual(len(paths), 2, "one path per run of consecutive years")
        self.assertEqual([p.count(" L ") + 1 for p in paths], [2, 2])
        self.assertEqual(svg.count("<circle"), 5)

    def test_markers_are_drawn_only_inside_the_year_range(self) -> None:
        series = (chart.Series("A*", (_point(2011, 40), _point(2012, 41)), "#125c58"),)
        inside = chart.panel_svg(
            series, 2005, 2015, "percent", chart.TRAJECTORY_DESKTOP,
            uid="t", title="t", description="t", markers=(trajectory.A_STAR_INTRODUCED,),
        )
        outside = chart.panel_svg(
            series, 2010, 2015, "percent", chart.TRAJECTORY_DESKTOP,
            uid="t", title="t", description="t", markers=(trajectory.A_STAR_INTRODUCED,),
        )
        self.assertIn("A* introduced 2010", inside)
        self.assertNotIn("panel-rule", outside)


class IndexPanelTests(unittest.TestCase):
    def setUp(self) -> None:
        self.metrics = comparison.metrics()
        self.metric = comparison.metric_by_id(self.metrics, "a_level_astar")
        self.frame = trajectory.index_frame(self.metric)

    def test_default_series_is_available_for_every_school(self) -> None:
        self.assertIn(trajectory.INDEX_DEFAULT_METRIC, trajectory.index_metric_ids(self.metrics))
        for school in dataset.schools():
            markup = trajectory.index_panel(self.metric, school, self.frame)
            self.assertNotIn("index-panel-empty", markup, school["id"])

    def test_every_school_shares_one_ruler(self) -> None:
        self.assertEqual(self.frame, {"year_from": 2010, "year_to": 2026, "ceiling": 100})
        for school in dataset.schools():
            markup = trajectory.index_panel(self.metric, school, self.frame)
            self.assertIn('>2010</text>', markup)
            self.assertIn('>2026</text>', markup)
            self.assertIn('>100%</text>', markup)

    def test_every_plotted_value_is_a_frozen_value_at_display_precision(self) -> None:
        for school in dataset.schools():
            points = comparison.school_points(self.metric, school["id"])
            markup = trajectory.index_panel(self.metric, school, self.frame)
            self.assertEqual(markup.count("<circle"), len(points), school["id"])
            for point in points:
                self.assertIn(f"{point['year']}: {to_fixed(point['value'])}%", markup)
                self.assertIn(f"<th scope=\"row\">{point['year']}</th><td>{to_fixed(point['value'])}%</td>", markup)

    def test_a_missing_series_is_stated_not_drawn(self) -> None:
        metric = comparison.metric_by_id(self.metrics, "gcse_grade_9")
        markup = trajectory.index_panel(metric, records.find_school("eton"), trajectory.index_frame(metric))
        self.assertIn("index-panel-empty", markup)
        self.assertNotIn("<svg", markup)

    def test_index_panel_matches_the_pinned_markup(self) -> None:
        published = (FIXTURES / "index_panel_eton_a_level_astar.html").read_text(encoding="utf-8")
        rendered = trajectory.index_panel(self.metric, records.find_school("eton"), self.frame)
        self.assertEqual(normalise(rendered), normalise(published))


class SchoolTrajectoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.metrics = comparison.metrics()

    def test_each_school_gets_one_panel_per_ruler_it_publishes(self) -> None:
        counts = {
            school["id"]: [panel["key"] for panel in trajectory.school_ruler_panels(school, self.metrics)]
            for school in dataset.schools()
        }
        self.assertEqual(
            counts,
            {
                "eton": ["a-level"],
                "kcs": ["a-level", "gcse-9-1", "gcse-legacy"],
                "spgs": ["a-level", "gcse-9-1"],
                "st-pauls": ["a-level", "gcse-9-1", "gcse-legacy"],
                "westminster": ["a-level", "gcse-9-1", "gcse-legacy"],
                "winchester": ["a-level", "gcse-9-1", "gcse-legacy"],
                "wycombe": ["a-level", "gcse-9-1"],
            },
        )

    def test_rulers_the_comparison_tool_does_not_define_are_listed_not_drawn(self) -> None:
        markup = trajectory.school_trajectory(records.find_school("winchester"), self.metrics)
        self.assertIn("Cambridge Pre-U results · 2010–2020", markup)
        self.assertIn("Mixed A-level and Pre-U result · 2021", markup)
        self.assertNotIn("d1_d2", markup)

    def test_qualification_breaks_stay_visible(self) -> None:
        winchester = trajectory.school_trajectory(records.find_school("winchester"), self.metrics)
        self.assertIn("A* introduced 2010", winchester)
        self.assertIn("pre-A* thresholds A and A–B", winchester)
        self.assertIn("2020–21 not drawn (CAG/TAG)", winchester)
        eton = trajectory.school_trajectory(records.find_school("eton"), self.metrics)
        self.assertNotIn("A* introduced 2010", eton)

    def test_the_exceptional_band_is_drawn_only_where_a_series_reaches_it(self) -> None:
        panels = {
            panel["key"]: panel
            for panel in trajectory.school_ruler_panels(records.find_school("westminster"), self.metrics)
        }
        self.assertIn(trajectory.EXCEPTIONAL_YEARS, panels["a-level"]["markers"])
        self.assertNotIn(trajectory.EXCEPTIONAL_YEARS, panels["gcse-legacy"]["markers"])

    def test_exceptional_years_are_never_plotted(self) -> None:
        for school in dataset.schools():
            for panel in trajectory.school_ruler_panels(school, self.metrics):
                for item in panel["series"]:
                    years = {point["year"] for point in item.points}
                    self.assertFalse(years & {2020, 2021}, (school["id"], panel["key"], item.label))

    def test_winchester_trajectory_matches_the_pinned_markup(self) -> None:
        published = (FIXTURES / "trajectory_winchester.html").read_text(encoding="utf-8")
        rendered = trajectory.school_trajectory(records.find_school("winchester"), self.metrics)
        self.assertEqual(normalise(rendered), normalise(published))


class DeterminismAndFrozenDataTests(unittest.TestCase):
    def test_rendering_twice_gives_identical_markup(self) -> None:
        metrics = comparison.metrics()
        first = [
            trajectory.school_trajectory(school, metrics) for school in dataset.schools()
        ]
        second = [
            trajectory.school_trajectory(school, comparison.metrics()) for school in dataset.schools()
        ]
        self.assertEqual(first, second)

    def test_drawing_every_chart_leaves_the_frozen_dataset_untouched(self) -> None:
        before = copy.deepcopy(dataset.load())
        metrics = comparison.metrics()
        for metric in metrics:
            frame = trajectory.index_frame(metric)
            for school in dataset.schools():
                trajectory.index_panel(metric, school, frame)
        for school in dataset.schools():
            trajectory.school_trajectory(school, metrics)
        self.assertEqual(dataset.load(), before)
        with DATASET_PATH.open(encoding="utf-8") as handle:
            self.assertEqual(json.load(handle), before)
        self.assertEqual(hashlib.sha256(DATASET_PATH.read_bytes()).hexdigest(), DATASET_SHA256)


class RouteTests(unittest.TestCase):
    """Drive the application headlessly and check what each route draws."""

    @classmethod
    def setUpClass(cls) -> None:
        from streamlit.testing.v1 import AppTest

        cls.AppTest = AppTest

    def _render(self, route: str, **params: str) -> str:
        app = self.AppTest.from_file(str(ROOT / "streamlit_app.py"), default_timeout=120)
        app.query_params["p"] = route
        for key, value in params.items():
            app.query_params[key] = value
        app.run()
        self.assertEqual(len(app.exception), 0, [item.value for item in app.exception])
        return "".join(item.value for item in app.markdown)

    def test_the_index_draws_one_panel_per_school_on_the_default_series(self) -> None:
        markup = self._render("/schools")
        self.assertEqual(markup.count('class="index-panel"'), 7)
        self.assertEqual(markup.count('class="index-panel index-panel-empty"'), 0)
        self.assertIn("Share of published A-level entries awarded A*", markup)
        self.assertIn("?p=/compare&amp;metric=a_level_astar", markup)

    def test_the_index_series_follows_the_url(self) -> None:
        markup = self._render("/schools", series="oxford_offer_rate")
        self.assertIn("Oxford offers divided by applications", markup)
        self.assertIn("Calculated rates are generated at display time", markup)

    def test_a_school_record_draws_its_rulers(self) -> None:
        markup = self._render("/schools/westminster")
        self.assertEqual(markup.count('class="trajectory-panel"'), 3)
        self.assertIn("Results by year", markup)
        self.assertIn("Open the examination ledgers", markup)

    def test_the_sample_dossier_carries_the_comparison_chart(self) -> None:
        markup = self._render("/sample-dossier")
        self.assertIn('<svg class="comparison-chart"', markup)
        self.assertIn("Two school series from 2015 to 2019", markup)


if __name__ == "__main__":
    unittest.main()
