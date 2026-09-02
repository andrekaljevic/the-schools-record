#!/usr/bin/env python3
"""Write the public projection the static frontend is built from.

The frozen dataset under ``data/`` is read-only source material.  This tool
runs the tested Python interpretation layer (``tsr.projection``) and writes a
deterministic, whitelisted set of JSON documents to ``web/src/generated/``,
together with a manifest that pins the dataset hash, snapshot and record
counts the frontend must display.  Every document is scanned for private
patterns before it is written; a leak aborts the build with nothing written.

    python3 tools/build_public_projection.py            # write
    python3 tools/build_public_projection.py --check    # verify without writing
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tsr import corpora, dataset, projection  # noqa: E402

DATASET_PATH = ROOT / "data" / "dataset.json"
OUTPUT = ROOT / "web" / "src" / "generated"


def manifest(documents: dict[str, str]) -> dict[str, object]:
    metadata = dataset.metadata()
    return {
        "datasetSha256": hashlib.sha256(DATASET_PATH.read_bytes()).hexdigest(),
        "snapshot": metadata["snapshot_version"],
        "baselineCommit": metadata["baseline_commit"],
        "redactions": metadata["source_location_redactions"],
        "counts": corpora.corpus_counts(),
        "schools": len(dataset.schools()),
        "documents": {
            name: hashlib.sha256(text.encode("utf-8")).hexdigest() for name, text in sorted(documents.items())
        },
    }


def render() -> dict[str, str]:
    documents = {name: projection.serialise(doc) for name, doc in projection.build().items()}
    for name, text in documents.items():
        projection.scan(text, f"projection document {name}")
    documents["manifest"] = projection.serialise(manifest(documents))
    return documents


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--check", action="store_true", help="verify the projection matches what is on disk")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args(argv)

    before = hashlib.sha256(DATASET_PATH.read_bytes()).hexdigest()
    documents = render()
    after = hashlib.sha256(DATASET_PATH.read_bytes()).hexdigest()
    if before != after:  # pragma: no cover - defensive: the projection must never write data/
        print("refusing to continue: data/dataset.json changed during the build", file=sys.stderr)
        return 2

    if args.check:
        stale = []
        for name, text in documents.items():
            target = args.output / f"{name}.json"
            if not target.exists() or target.read_text(encoding="utf-8") != text:
                stale.append(name)
        if stale:
            print("projection is stale for: " + ", ".join(sorted(stale)), file=sys.stderr)
            return 1
        print(f"projection up to date ({len(documents)} documents)")
        return 0

    for name, text in documents.items():
        target = args.output / f"{name}.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
    total = sum(len(text.encode("utf-8")) for text in documents.values())
    where = args.output.relative_to(ROOT) if args.output.resolve().is_relative_to(ROOT) else args.output
    print(f"wrote {len(documents)} documents ({total / 1024 / 1024:.1f} MB) to {where}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
