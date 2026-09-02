"""Re-extract ``data/dataset.json`` from the published front-end bundle.

The bundle in ``bundle/latest.js.gz`` is the compiled build of the previously
hosted site (snapshot ``production-818c7c2-data-frozen-v1``).  Its immutable
data module is a plain object literal, so it is lifted out with brace matching
and evaluated by Node, then written out verbatim as JSON.

    python tools/extract_dataset.py --check            # verify the frozen snapshot
    python tools/extract_dataset.py --output snap.json # write the raw snapshot

The committed ``data/dataset.json`` is this snapshot plus the revisions in
``data/revisions.json``; rebuild or verify it with ``tools/apply_revisions.py``.
Requires Node. Nothing here is used at runtime; it exists so the provenance of
the frozen dataset stays reproducible.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "bundle" / "latest.js.gz"
TARGET = ROOT / "data" / "dataset.json"
MARKER = "\tcorpora: /* @__PURE__ */ JSON.parse("

# SHA-256 of the serialised frozen snapshot production-818c7c2-data-frozen-v1.
FROZEN_SNAPSHOT_SHA256 = "245f2d8176f8fca0d53f41689f096734dd13e9023af9a67931314334251b9f6f"


def _object_literal(source: str) -> str:
    lines = source.split("\n")
    marker_index = next(i for i, line in enumerate(lines) if line.startswith(MARKER))
    declaration = next(
        i
        for i in range(marker_index, -1, -1)
        if lines[i].startswith(("var ", "let ", "const "))
    )
    offset = sum(len(line) + 1 for line in lines[:declaration])
    start = source.index("{", offset)

    depth = 0
    quote: str | None = None
    escaped = False
    index = start
    while index < len(source):
        char = source[index]
        if quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
        elif char in "\"'`":
            quote = char
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return source[start : index + 1]
        index += 1
    raise ValueError("unterminated data object in bundle")


def extract() -> dict:
    with gzip.open(BUNDLE, "rt", encoding="utf-8") as handle:
        source = handle.read()
    literal = _object_literal(source)
    with tempfile.TemporaryDirectory() as work:
        module = Path(work) / "data.mjs"
        module.write_text(
            f"const data = {literal};\nprocess.stdout.write("
            "JSON.stringify(data));\n",
            encoding="utf-8",
        )
        result = subprocess.run(
            ["node", str(module)], capture_output=True, check=True, text=True
        )
    return json.loads(result.stdout)


def serialise(data: dict) -> str:
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="verify the bundle still yields the frozen snapshot")
    parser.add_argument("--output", type=Path, help="write the raw frozen snapshot to this path")
    args = parser.parse_args()
    payload = serialise(extract())
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    if args.check:
        if digest != FROZEN_SNAPSHOT_SHA256:
            print("the published bundle no longer yields the frozen snapshot", file=sys.stderr)
            return 1
        print("the published bundle yields the frozen snapshot production-818c7c2-data-frozen-v1")
        print("verify data/dataset.json with: python tools/apply_revisions.py --check")
        return 0
    if args.output is None:
        parser.error("give --output PATH to write the raw snapshot; data/dataset.json is rebuilt by tools/apply_revisions.py")
    if args.output.resolve() == TARGET.resolve():
        parser.error("refusing to overwrite data/dataset.json with the raw snapshot; use tools/apply_revisions.py")
    args.output.write_text(payload, encoding="utf-8")
    print(f"wrote {args.output} ({len(payload):,} bytes, sha256 {digest})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
