from __future__ import annotations

import base64
import gzip
import unittest
from pathlib import Path

from premium_presentation import (
    PREMIUM_PRESENTATION_CSS,
    PREMIUM_PRESENTATION_MARKER,
    apply_premium_presentation,
)


ROOT = Path(__file__).resolve().parents[1]


def load_connector_css() -> str:
    parts = sorted((ROOT / "bundle" / "connector" / "css").glob("part-*"))
    encoded = "".join(part.read_text(encoding="ascii") for part in parts)
    return gzip.decompress(base64.b64decode(encoded)).decode("utf-8")


def load_fallback_css() -> str:
    with gzip.open(ROOT / "bundle" / "app.css.gz", "rt", encoding="utf-8") as handle:
        return handle.read()


class PremiumPresentationTests(unittest.TestCase):
    def test_patch_is_compatible_with_both_frontend_bundles(self) -> None:
        for original in (load_connector_css(), load_fallback_css()):
            patched = apply_premium_presentation(original)
            self.assertTrue(patched.startswith(original))
            self.assertEqual(patched.count(PREMIUM_PRESENTATION_MARKER), 1)

    def test_patch_is_idempotent(self) -> None:
        patched = apply_premium_presentation(load_connector_css())
        self.assertEqual(apply_premium_presentation(patched), patched)

    def test_patch_fails_closed_for_an_unrecognised_bundle(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "missing bundle selectors"):
            apply_premium_presentation("body { color: black; }")

    def test_presentation_system_covers_core_experiences(self) -> None:
        for selector in (
            ".briefing-inventory",
            ".release-table-shell",
            ".comparison-canvas",
            ".evidence-record",
            ".record-masthead",
            ".school-record-portrait",
            ".series-index",
            ".ledger-table-scroll",
            ".record-evidence-sheet",
            ".site-footer",
        ):
            self.assertIn(selector, PREMIUM_PRESENTATION_CSS)

    def test_accessibility_and_responsive_contracts_are_explicit(self) -> None:
        for contract in (
            ":focus-visible",
            "@media (hover: hover)",
            "@media (width <= 820px)",
            "@media (width <= 520px)",
            "@media (prefers-reduced-motion: reduce)",
            "min-height: 44px",
        ):
            self.assertIn(contract, PREMIUM_PRESENTATION_CSS)

    def test_stylesheet_is_self_contained(self) -> None:
        lowered = PREMIUM_PRESENTATION_CSS.lower()
        self.assertNotIn("@import", lowered)
        self.assertNotIn("url(http", lowered)
        self.assertEqual(PREMIUM_PRESENTATION_CSS.count("{"), PREMIUM_PRESENTATION_CSS.count("}"))


if __name__ == "__main__":
    unittest.main()
