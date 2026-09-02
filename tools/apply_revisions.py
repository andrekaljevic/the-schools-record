"""Rebuild ``data/dataset.json`` as bundle extraction plus documented revisions.

The frozen snapshot is the immutable data module inside the published bundle.
Every statistical change made since is listed in ``data/revisions.json`` and
applied here, in order, on top of a fresh extraction, so the file on disk is
always reproducible as ``published bundle + recorded revisions``.  A change is
applied only when the value it replaces matches the recorded ``from`` value
exactly; any drift makes the tool refuse rather than guess.

    python tools/apply_revisions.py            # rebuild data/dataset.json
    python tools/apply_revisions.py --check    # verify the committed file

Requires Node for the extraction (see ``tools/extract_dataset.py``).
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.extract_dataset import extract, serialise  # noqa: E402

REVISIONS = ROOT / "data" / "revisions.json"
TARGET = ROOT / "data" / "dataset.json"


class RevisionError(RuntimeError):
    """A recorded revision does not fit the data it is applied to."""


def load_revisions() -> dict[str, Any]:
    with REVISIONS.open(encoding="utf-8") as handle:
        return json.load(handle)


def _dataset(data: dict[str, Any], dataset_id: str) -> dict[str, Any]:
    for entry in data["corpora"]["figures"]["datasets"]:
        if entry["dataset_id"] == dataset_id:
            return entry
    raise RevisionError(f"dataset {dataset_id!r} is not in the figures corpus")


def _row(entry: dict[str, Any], selector: dict[str, Any]) -> dict[str, Any]:
    matches = [
        row for row in entry["rows"]
        if all(row.get(key) == value for key, value in selector.items())
    ]
    if len(matches) != 1:
        raise RevisionError(f"{entry['dataset_id']} {selector} matches {len(matches)} rows, expected one")
    return matches[0]


def _correction(data: dict[str, Any], correction_id: str) -> dict[str, Any]:
    for item in data["corpora"]["figures"]["corrections"]:
        if item["id"] == correction_id:
            return item
    raise RevisionError(f"correction {correction_id!r} is not in the ledger")


def _shape(values: list[Any]) -> Any:
    return values[0] if len(values) == 1 else values


def apply_change(data: dict[str, Any], change: dict[str, Any], revision: dict[str, Any]) -> None:
    entry = _dataset(data, change["dataset_id"])
    row = _row(entry, change["row"])
    for item in change["fields"]:
        current = row.get(item["field"])
        if current != item["from"]:
            raise RevisionError(
                f"{change['dataset_id']} {change['row']} {item['field']} is {current!r}, "
                f"revision expects {item['from']!r}"
            )
        row[item["field"]] = item["to"]
    if row.get("note") != change["note_from"]:
        raise RevisionError(f"{change['dataset_id']} {change['row']} note does not match the recorded note")
    row["note"] = change["note_to"]

    original = _correction(data, change["reverses"])
    if original.get("status") != "locked":
        raise RevisionError(f"{change['reverses']} is not a locked correction")
    original["status"] = "superseded"
    original["superseded_by"] = change["reversal"]

    ledger = data["corpora"]["figures"]["corrections"]
    if any(item["id"] == change["reversal"] for item in ledger):
        raise RevisionError(f"{change['reversal']} already exists in the ledger")
    ledger.append({
        "id": change["reversal"],
        "metric": change["metric"],
        "new": _shape([item["to"] for item in change["fields"]]),
        "old": _shape([item["from"] for item in change["fields"]]),
        "period": change["period"],
        "reason": change["reason"],
        "school": change["school"],
        "source_refs": list(change["source_refs"]),
        "status": "locked",
        "reverses": change["reverses"],
        "revision": revision["id"],
    })


def apply_revisions(data: dict[str, Any], spec: dict[str, Any]) -> dict[str, Any]:
    """Return a new dataset with every recorded revision applied in order."""
    revised = copy.deepcopy(data)
    applied: list[dict[str, Any]] = []
    for revision in spec["revisions"]:
        for change in revision["changes"]:
            apply_change(revised, change, revision)
        revised["metadata"]["snapshot_version"] = revision["snapshot_version"]
        applied.append({
            "id": revision["id"],
            "applied": revision["applied"],
            "title": revision["title"],
            "basis": revision["basis"],
            "entries": [change["reversal"] for change in revision["changes"]],
        })
    if applied:
        revised["metadata"]["data_policy"] = (
            "Production data frozen at the published snapshot; every later statistical "
            "change is a recorded, versioned revision listed in metadata.revisions; "
            "source locations security-redacted"
        )
        revised["metadata"]["revisions"] = applied
    return revised


def build() -> str:
    return serialise(apply_revisions(extract(), load_revisions()))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    payload = build()
    if args.check:
        if TARGET.read_text(encoding="utf-8") != payload:
            print("data/dataset.json does not equal the published bundle plus recorded revisions", file=sys.stderr)
            return 1
        print("data/dataset.json equals the published bundle plus recorded revisions")
        return 0
    TARGET.write_text(payload, encoding="utf-8")
    print(f"wrote {TARGET} ({len(payload):,} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
