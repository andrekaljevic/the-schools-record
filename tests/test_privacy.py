"""Private source locations never reach public output.

The redaction logic of the final public build defined what is private: Google
Drive and Docs links and the document identifiers inside them.  These tests
render every public route, a sample of record permalinks and the public source
register, and fail if any such location appears; they also check that the
review-queue module never claims durable receipt it cannot prove.
"""

from __future__ import annotations

import json
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

sys.path.insert(0, str(Path(__file__).resolve().parent))

from support import page  # noqa: E402
from tsr import corpora, dataset, evidence, review_queue, sources  # noqa: E402

PRIVATE_PATTERNS = (
    re.compile(r"drive\.google\.com", re.I),
    re.compile(r"docs\.google\.com", re.I),
    re.compile(r"private-source-[0-9a-f]{16}"),
    re.compile(r"/d/[A-Za-z0-9_-]{25,}"),
    re.compile(r"[?&]id=[A-Za-z0-9_-]{25,}"),
)


def assert_no_private_location(test: unittest.TestCase, text: str, where: str) -> None:
    for pattern in PRIVATE_PATTERNS:
        test.assertIsNone(pattern.search(text), f"{where} exposes a private location: {pattern.pattern}")


class PublicOutputPrivacyTests(unittest.TestCase):
    ROUTES = [
        "/", "/schools", "/compare", "/methodology", "/evidence", "/oxbridge", "/us-universities", "/corrections",
        "/corrections/report", "/professional", "/sample-dossier", "/about", "/privacy", "/terms", "/changelog",
    ]

    def test_every_route_is_free_of_private_locations(self) -> None:
        routes = list(self.ROUTES)
        for school in dataset.schools():
            routes += [f"/schools/{school['id']}{suffix}" for suffix in ("", "/exam-results", "/university-destinations", "/oxbridge", "/us-universities", "/school-entry")]
        for route in routes:
            assert_no_private_location(self, page(route), route)
        for section in ("sources", "method"):
            assert_no_private_location(self, page("/evidence", section=section), f"/evidence?section={section}")

    def test_record_permalinks_and_search_pages_are_clean(self) -> None:
        index = evidence.index()
        samples = [index[i].id for i in range(0, len(index), 97)]
        for record_id in samples:
            assert_no_private_location(self, page("/evidence", record=record_id), record_id)
        for corpus in ("figures", "granular", "oxbridge", "us"):
            for number in ("1", "2"):
                assert_no_private_location(self, page("/evidence", corpus=corpus, page=number), f"{corpus} page {number}")

    def test_the_frozen_dataset_and_register_carry_no_private_location(self) -> None:
        assert_no_private_location(self, (ROOT / "data" / "dataset.json").read_text(encoding="utf-8"), "dataset.json")
        assert_no_private_location(self, (ROOT / "data" / "public_sources.json").read_text(encoding="utf-8"), "public_sources.json")

    def test_evidence_index_never_exposes_source_urls(self) -> None:
        for item in evidence.index():
            for label, value in evidence.detail_fields(item):
                self.assertNotIn("Source location", label, item.id)
                assert_no_private_location(self, value, item.id)

    def test_withheld_titles_are_not_reconstructed(self) -> None:
        catalog = corpora.source_catalog()
        withheld = [key for key, entry in catalog.items() if entry.get("title") == "Source title withheld"]
        self.assertGreater(len(withheld), 0)
        for key in withheld:
            self.assertEqual(sources.describe(key)["title"], "Source title withheld", key)
            self.assertIsNone(sources.describe(key)["url"], key)


class SourceRegisterGuardTests(unittest.TestCase):
    def test_private_urls_are_rejected(self) -> None:
        self.assertFalse(sources.is_public_url("https://drive.google.com/file/d/abc123456789012345678/view"))
        self.assertFalse(sources.is_public_url("https://docs.google.com/document/d/abc/edit"))
        self.assertFalse(sources.is_public_url("https://example.org/private-source-0123456789abcdef"))
        self.assertTrue(sources.is_public_url("https://web.archive.org/web/2004/http://www.wincoll.ac.uk/"))
        self.assertFalse(sources.is_public_url(None))

    def test_a_register_with_a_private_link_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "public_sources.json"
            path.write_text(json.dumps({"sources": {"X": {"id": "x", "title": "x", "url": "https://drive.google.com/file/d/abcdefghijklmnopqrstuvwxyz/view"}}}), encoding="utf-8")
            with mock.patch.object(sources, "PUBLIC_SOURCES_PATH", path):
                sources.public_sources.cache_clear()
                with self.assertRaises(sources.PrivateSourceError):
                    sources.public_sources()
        sources.public_sources.cache_clear()


class ReviewQueueHonestyTests(unittest.TestCase):
    def test_a_failed_local_write_is_reported_as_a_failure(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            blocked = Path(directory) / "file-not-dir"
            blocked.write_text("x", encoding="utf-8")
            with mock.patch.dict("os.environ", {"TSR_REVIEW_QUEUE_DIR": str(blocked / "queue"), "TSR_REVIEW_WEBHOOK_URL": ""}):
                receipt = review_queue.submit("correction-report", {"school": "Test"})
        self.assertEqual(receipt.status, review_queue.FAILED)
        self.assertFalse(receipt.accepted)
        self.assertFalse(receipt.durable)

    def test_a_local_write_is_not_described_as_durable_without_configuration(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with mock.patch.dict("os.environ", {"TSR_REVIEW_WEBHOOK_URL": ""}), mock.patch.object(review_queue, "DEFAULT_QUEUE_DIR", Path(directory)), mock.patch.object(review_queue, "_setting", lambda name: None):
                receipt = review_queue.submit("professional-enquiry", {"name": "Test"})
                self.assertEqual(receipt.status, review_queue.STORED)
                self.assertFalse(receipt.durable)
                self.assertIn("may not survive a restart", receipt.detail)
                self.assertTrue((Path(directory) / "professional-enquiry.jsonl").exists())

    def test_a_configured_endpoint_that_does_not_confirm_is_a_failure(self) -> None:
        def refuse(request, timeout):  # noqa: ARG001
            raise OSError("connection refused")

        with mock.patch.object(review_queue, "_setting", lambda name: "https://example.org/hook" if name == "TSR_REVIEW_WEBHOOK_URL" else None):
            receipt = review_queue.submit("correction-report", {"school": "Test"}, opener=refuse)
        self.assertEqual(receipt.status, review_queue.FAILED)

    def test_a_confirming_endpoint_is_reported_as_forwarded(self) -> None:
        class Response:
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

        with mock.patch.object(review_queue, "_setting", lambda name: "https://example.org/hook" if name == "TSR_REVIEW_WEBHOOK_URL" else None):
            receipt = review_queue.submit("correction-report", {"school": "Test"}, opener=lambda request, timeout: Response())
        self.assertEqual(receipt.status, review_queue.FORWARDED)
        self.assertTrue(receipt.durable)

    def test_the_report_page_never_claims_receipt_before_submission(self) -> None:
        markup = page("/corrections/report")
        self.assertNotIn("is in the review queue", markup)


if __name__ == "__main__":
    unittest.main()
