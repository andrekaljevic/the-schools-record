"""Public source references and the approved public links behind them.

The frozen dataset identifies evidence by stable reference keys (``FB146``,
``WIN_GCSE_HMC_1997``, ``public-source-…``) and, by design, carries no document
locations at all.  The final reviewed public build did, however, keep links to
first-party school pages, public-body releases and Internet Archive captures
while redacting every private working document.  ``data/public_sources.json``
is that approved set, regenerated from the retained reference build by
``tools/build_public_sources.py`` under the same redaction rules; this module
joins it onto the frozen catalogue and refuses to serve anything that looks
like a private location.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from . import corpora

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_SOURCES_PATH = ROOT / "data" / "public_sources.json"

PRIVATE_URL = re.compile(r"https?://(?:[a-z0-9-]+\.)*(?:drive|docs)\.google\.com/", re.I)
PRIVATE_ID = re.compile(r"private-source-[0-9a-f]{16}")
PUBLIC_SCHEMES = ("https://", "http://")


class PrivateSourceError(RuntimeError):
    """Raised when a location that must stay private reaches the public layer."""


def is_public_url(url: Any) -> bool:
    return (
        isinstance(url, str)
        and url.startswith(PUBLIC_SCHEMES)
        and not PRIVATE_URL.search(url)
        and not PRIVATE_ID.search(url)
    )


@lru_cache(maxsize=1)
def public_sources() -> dict[str, dict[str, Any]]:
    """Reference key → approved public link, verified on load."""
    if not PUBLIC_SOURCES_PATH.exists():
        return {}
    with PUBLIC_SOURCES_PATH.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    entries: dict[str, dict[str, Any]] = {}
    for key, entry in payload.get("sources", {}).items():
        url = entry.get("url")
        if not is_public_url(url):
            raise PrivateSourceError(f"public source register carries a non-public location for {key}")
        entries[key] = {
            "key": key,
            "id": entry.get("id"),
            "title": entry.get("title") or key,
            "url": url,
            "role": entry.get("role"),
        }
    return entries


def public_link(ref: str) -> dict[str, Any] | None:
    """The approved public link for a reference key or id, if one exists."""
    register = public_sources()
    if ref in register:
        return register[ref]
    for entry in register.values():
        if entry["id"] == ref:
            return entry
    return None


def catalog_entry(ref: str) -> dict[str, Any] | None:
    catalog = corpora.source_catalog()
    if ref in catalog:
        return {"key": ref, **catalog[ref]}
    for key, entry in catalog.items():
        if entry.get("id") == ref:
            return {"key": key, **entry}
    return None


def describe(ref: str) -> dict[str, Any]:
    """Everything the public layer may say about one reference."""
    entry = catalog_entry(ref) or {}
    link = public_link(ref)
    title = entry.get("title") if entry else None
    if not title or title == "Source title withheld":
        title = link["title"] if link else None
    withheld = not title
    return {
        "ref": ref,
        "key": entry.get("key", ref),
        "id": entry.get("id"),
        "title": title or "Source title withheld",
        "withheld": withheld,
        "role": entry.get("role"),
        "url": link["url"] if link else None,
    }


def linked_sources(refs: list[str]) -> list[dict[str, Any]]:
    seen: dict[str, dict[str, Any]] = {}
    for ref in refs:
        if ref not in seen:
            seen[ref] = describe(ref)
    return list(seen.values())
