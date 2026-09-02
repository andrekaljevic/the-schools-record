"""Access to the frozen production dataset.

``data/dataset.json`` is a verbatim extraction of the immutable data module that
ships inside the published front-end bundle (``bundle/latest.js.gz``, snapshot
``production-818c7c2-data-frozen-v1``).  Nothing in this package alters,
recalculates, normalises, rounds or replaces a stored figure: values are read as
they are and only formatted for display.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATASET_PATH = ROOT / "data" / "dataset.json"


@lru_cache(maxsize=1)
def load() -> dict[str, Any]:
    with DATASET_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


def data() -> dict[str, Any]:
    return load()


def schools() -> list[dict[str, Any]]:
    return load()["schools"]


def figures() -> dict[str, Any]:
    return load()["corpora"]["figures"]


def presentation() -> dict[str, Any]:
    return load()["presentation"]


def metadata() -> dict[str, Any]:
    return load()["metadata"]


def admissions_process() -> list[dict[str, Any]]:
    return load()["admissions_process"]
