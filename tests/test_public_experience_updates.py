from __future__ import annotations

import base64
import gzip
import unittest
from pathlib import Path

from kcs_entry_updates import apply_kcs_entry_updates
from premium_presentation import apply_premium_presentation
from public_experience_updates import (
    PUBLIC_EXPERIENCE_CSS,
    PUBLIC_EXPERIENCE_MARKER,
    _PRIVATE_DOCUMENT_ID,
    _PRIVATE_DOCUMENT_URL,
    apply_public_experience_updates,
)
from site_patches import apply_st_pauls_history, apply_winchester_history
from winchester_entry_updates import apply_winchester_gcse_entry_updates


ROOT = Path(__file__).resolve().parents[1]


def load_connector_asset(asset_type: str) -> str:
    parts = sorted((ROOT / "bundle" / "connector" / asset_type).glob("part-*"))
    encoded = "".join(part.read_text(encoding="ascii") for part in parts)
    return gzip.decompress(base64.b64decode(encoded)).decode("utf-8")


def load_fallback_asset(filename: str) -> str:
    with gzip.open(ROOT / "bundle" / filename, "rt", encoding="utf-8") as handle:
        return handle.read()


def apply_data_updates(javascript: str) -> str:
    javascript = apply_st_pauls_history(javascript)
    javascript = apply_winchester_history(javascript)
    javascript = apply_winchester_gcse_entry_updates(javascript)
    return apply_kcs_entry_updates(javascript)


def bundle_pairs() -> tuple[tuple[str, str], ...]:
    return (
        (load_connector_asset("css"), load_connector_asset("js")),
        (load_fallback_asset("app.css.gz"), load_fallback_asset("app.js.gz")),
    )


class PublicExperienceUpdateTests(unittest.TestCase):
    def patch(self, css: str, javascript: str) -> tuple[str, str]:
        return apply_public_experience_updates(
            apply_premium_presentation(css), apply_data_updates(javascript)
        )

    def test_patch_is_compatible_with_both_frontend_bundles(self) -> None:
        for css, javascript in bundle_pairs():
            patched_css, patched_js = self.patch(css, javascript)
            self.assertEqual(patched_css.count(PUBLIC_EXPERIENCE_MARKER), 1)
            self.assertEqual(patched_js.count(PUBLIC_EXPERIENCE_MARKER), 1)

    def test_patch_is_idempotent(self) -> None:
        css, javascript = bundle_pairs()[0]
        patched = self.patch(css, javascript)
        self.assertEqual(apply_public_experience_updates(*patched), patched)

    def test_homepage_explains_scope_method_and_future_coverage(self) -> None:
        for css, javascript in bundle_pairs():
            _, patched = self.patch(css, javascript)
            for copy in (
                "Independent school results,",
                "A clearer record of school results.",
                "examination results, university destinations and admissions figures",
                "Eton College, Westminster School, King’s College School Wimbledon",
                "A level, GCSE, IGCSE, IB and Pre-U results remain separate",
                "Further schools are added when there is enough reliable evidence",
                "interactive chart and the exact table",
            ):
                self.assertIn(copy, patched)

    def test_comparison_chart_is_obvious_and_open_by_default(self) -> None:
        for css, javascript in bundle_pairs():
            _, patched = self.patch(css, javascript)
            self.assertIn("See the schools on the same measure.", patched)
            self.assertIn("The chart and table update together", patched)
            self.assertIn(
                "className:`compare-trend-details`,open:!0,children:", patched
            )
            self.assertIn("children:`Interactive chart`", patched)
            self.assertIn("className:`comparison-section-label`", patched)
            self.assertIn("children:`Table`", patched)
            self.assertLess(
                patched.index("className:`compare-trend-details`"),
                patched.index("className:`comparison-section-label`"),
            )

    def test_audit_language_is_replaced_with_plain_english(self) -> None:
        for css, javascript in bundle_pairs():
            _, patched = self.patch(css, javascript)
            for expected in (
                "Method & notes",
                "How the figures are checked.",
                "What changed, and why.",
                "When published figures do not agree.",
                "How comparisons are made.",
                "Missing years stay blank",
            ):
                self.assertIn(expected, patched)
            for retired in (
                "The audit trail is a feature.",
                "The editorial contract",
                "Uncollapsed disagreements",
                "public lineage",
                "Precision before ranking.",
                "Controlling source families",
            ):
                self.assertNotIn(retired, patched)

    def test_bulk_download_controls_and_handlers_are_removed(self) -> None:
        for css, javascript in bundle_pairs():
            _, patched = self.patch(css, javascript)
            for retired in (
                "` CSV`",
                "Download index",
                "download-index",
                "schools-record-evidence-index.csv",
                "schools-record-${e}.csv",
                "new Blob",
                "URL.createObjectURL",
                ".download=",
            ):
                self.assertNotIn(retired, patched)
            self.assertIn("Copy view", patched)

    def test_private_documents_are_not_exposed_to_the_public_bundle(self) -> None:
        for css, javascript in bundle_pairs():
            updated = apply_data_updates(javascript)
            private_urls = _PRIVATE_DOCUMENT_URL.findall(updated)
            private_ids = {
                match.group(1)
                for url in private_urls
                if (match := _PRIVATE_DOCUMENT_ID.search(url))
            }
            self.assertGreater(len(private_urls), 390)
            self.assertGreater(len(private_ids), 70)

            _, patched = apply_public_experience_updates(
                apply_premium_presentation(css), updated
            )
            self.assertNotIn("drive.google.com", patched)
            self.assertNotIn("docs.google.com", patched)
            for identifier in private_ids:
                self.assertNotIn(identifier, patched)
            self.assertIn("sourceUrl:null", patched)
            self.assertIn("url:null", patched)

    def test_public_first_party_and_archive_links_remain(self) -> None:
        for css, javascript in bundle_pairs():
            _, patched = self.patch(css, javascript)
            self.assertIn(
                "https://www.winchestercollege.org/learning/exam-results-destinations/",
                patched,
            )
            self.assertIn("https://web.archive.org/", patched)
            self.assertIn(
                "https://www.compare-school-performance.service.gov.uk/download-data",
                patched,
            )

    def test_styles_cover_the_new_editorial_section_and_reflow(self) -> None:
        for contract in (
            ".briefing-about {",
            ".briefing-about-copy p:first-child",
            ".comparison-section-label",
            ".evidence-tools",
            "@media (width <= 820px)",
            "@media (width <= 520px)",
        ):
            self.assertIn(contract, PUBLIC_EXPERIENCE_CSS)
        self.assertEqual(
            PUBLIC_EXPERIENCE_CSS.count("{"), PUBLIC_EXPERIENCE_CSS.count("}")
        )

    def test_patch_fails_closed_for_an_unrecognised_bundle(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "missing bundle selectors"):
            apply_public_experience_updates("body{}", "console.log('test')")

    def test_partial_application_fails_closed(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "partially applied"):
            apply_public_experience_updates(
                f"{PUBLIC_EXPERIENCE_MARKER}.briefing-hero{{}}", "plain"
            )


if __name__ == "__main__":
    unittest.main()
