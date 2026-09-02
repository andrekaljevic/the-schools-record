"""Derive ``data/public_sources.json`` from the retained reference build.

The final reviewed public build (``bundle/app.js.gz`` with the data and
public-experience patches applied) kept links to first-party school pages,
public-body releases and Internet Archive captures, and replaced every private
working document with ``url: null``.  This tool applies exactly that patch
pipeline, lifts the surviving links for the source references the frozen
dataset actually cites, and writes them out.  It never touches
``data/dataset.json``.

    python tools/build_public_sources.py           # rewrite the register
    python tools/build_public_sources.py --check   # verify the committed file
"""

from __future__ import annotations

import argparse
import gzip
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from kcs_entry_updates import apply_kcs_entry_updates  # noqa: E402
from premium_presentation import apply_premium_presentation  # noqa: E402
from public_experience_updates import apply_public_experience_updates  # noqa: E402
from site_patches import apply_st_pauls_history, apply_winchester_history  # noqa: E402
from winchester_entry_updates import apply_winchester_gcse_entry_updates  # noqa: E402

TARGET = ROOT / "data" / "public_sources.json"
DATASET = ROOT / "data" / "dataset.json"

_ENTRY = re.compile(
    r'"(?P<key>[A-Z][A-Z0-9_]{3,})":\{"id":"(?P<id>[^"]+)","title":"(?P<title>[^"]*)",'
    r'"url":"(?P<url>https?://[^"]+)"(?:,"role":"(?P<role>[^"]*)")?'
)
_PRIVATE = re.compile(r"https?://(?:[a-z0-9-]+\.)*(?:drive|docs)\.google\.com/", re.I)


def _unescape(literal: str) -> str:
    """Decode a JSON string body exactly as the bundle's own parser would."""
    return json.loads(f'"{literal}"')


def reference_build() -> str:
    with gzip.open(ROOT / "bundle" / "app.js.gz", "rt", encoding="utf-8") as handle:
        javascript = handle.read()
    with gzip.open(ROOT / "bundle" / "app.css.gz", "rt", encoding="utf-8") as handle:
        css = handle.read()
    javascript = apply_st_pauls_history(javascript)
    javascript = apply_winchester_history(javascript)
    javascript = apply_winchester_gcse_entry_updates(javascript)
    javascript = apply_kcs_entry_updates(javascript)
    _, javascript = apply_public_experience_updates(apply_premium_presentation(css), javascript)
    return javascript


def build() -> dict:
    javascript = reference_build()
    with DATASET.open(encoding="utf-8") as handle:
        catalog = json.load(handle)["corpora"]["figures"]["source_catalog"]
    sources: dict[str, dict] = {}
    for match in _ENTRY.finditer(javascript):
        key = match.group("key")
        url = _unescape(match.group("url"))
        if key not in catalog or _PRIVATE.search(url):
            continue
        sources[key] = {
            "id": match.group("id"),
            "title": _unescape(match.group("title")),
            "url": url,
            "role": _unescape(match.group("role")) if match.group("role") else None,
        }
    if not sources:
        raise RuntimeError("no public source links were recovered from the reference build")
    return {
        "derived_from": "bundle/app.js.gz with the retained data and public-experience patches applied",
        "policy": "Only links the reviewed public build kept after redacting private working documents; keys limited to references the frozen dataset cites.",
        "sources": dict(sorted(sources.items())),
    }


def serialise(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    payload = serialise(build())
    if args.check:
        if TARGET.read_text(encoding="utf-8") != payload:
            print("data/public_sources.json does not match the reference build", file=sys.stderr)
            return 1
        print("data/public_sources.json matches the reference build")
        return 0
    TARGET.write_text(payload, encoding="utf-8")
    print(f"wrote {TARGET} ({len(json.loads(payload)['sources'])} sources)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
