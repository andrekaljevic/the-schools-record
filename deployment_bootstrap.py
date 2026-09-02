"""Materialise deterministic runtime assets on Streamlit Community Cloud.

The immutable source bundle and repository artwork are already versioned in the
repository. This deployment recreates the derived local files before importing
the native Streamlit views. The generated dataset, stylesheet and responsive
school images have been verified byte-for-byte against the completed rebuild.
"""

from __future__ import annotations

import gzip
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def _ensure_site_css() -> None:
    target = ROOT / "assets" / "site.css"
    if target.exists():
        return
    source = ROOT / "bundle" / "latest.css.gz"
    target.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(source, "rb") as handle:
        target.write_bytes(handle.read())


def _ensure_dataset() -> None:
    target = ROOT / "data" / "dataset.json"
    if target.exists():
        return
    from tools.extract_dataset import extract, serialise

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(serialise(extract()), encoding="utf-8")


def _ensure_school_artwork() -> None:
    target = ROOT / "static" / "schools" / "wycombe-1200.webp"
    if target.exists():
        return
    from tools.build_static_images import main as build_static_images

    build_static_images()


def ensure_runtime_assets() -> None:
    _ensure_site_css()
    _ensure_dataset()
    _ensure_school_artwork()
