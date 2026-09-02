#!/usr/bin/env python3
"""Render comparison charts with the canonical Python renderer for the TypeScript parity test.

Every metric, every ordered pair of schools and a sample of year windows: the
frontend's port must reproduce each SVG byte for byte, which the test checks by
SHA-256 (a few full renderings are kept so a mismatch can be read).  Writes
web/tests/fixtures/comparison-charts.json (outside data/).
"""

from __future__ import annotations

import hashlib
import json
import sys
from itertools import permutations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tsr import chart, comparison, dataset  # noqa: E402

OUTPUT = ROOT / "web" / "tests" / "fixtures" / "comparison-charts.json"


def main() -> int:
    metrics = comparison.metrics()
    ids = [school["id"] for school in dataset.schools()]
    names = {school["id"]: school["name"] for school in dataset.schools()}
    all_years = [point["year"] for metric in metrics for point in metric["points"]]
    year_min, year_max = min(all_years), max(all_years)
    cases = []
    for metric in metrics:
        years = sorted({point["year"] for point in metric["points"]})
        windows = {(year_min, year_max), (years[0], years[-1]), (2015, 2019), (2010, 2026), (years[0], years[0]), (2020, 2021)}
        for first, second in permutations(ids, 2):
            for year_from, year_to in sorted(windows):
                svg = chart.comparison_chart(metric, first, second, year_from, year_to)
                case = {
                    "metric": metric["id"],
                    "first": first,
                    "second": second,
                    "yearFrom": year_from,
                    "yearTo": year_to,
                    "sha256": hashlib.sha256(svg.encode("utf-8")).hexdigest(),
                }
                # A few full renderings make a mismatch diagnosable; the rest are pinned by hash.
                if len(cases) % 250 == 0:
                    case["svg"] = svg
                cases.append(case)
    payload = {
        "schools": [{"id": sid, "name": names[sid]} for sid in ids],
        "metrics": [
            {"id": m["id"], "label": m["label"], "unit": m["unit"], "points": [{"schoolId": p["schoolId"], "schoolName": p["schoolName"], "year": p["year"], "value": p["value"], "status": p["status"]} for p in m["points"]]}
            for m in metrics
        ],
        "cases": cases,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"wrote {len(cases)} chart cases to {OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
