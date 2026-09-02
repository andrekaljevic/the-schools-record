"""Render the sample dossier page to the downloadable PDF.

Run against a locally running instance:

    streamlit run streamlit_app.py --server.port 8502 &
    python tools/build_sample_pdf.py http://127.0.0.1:8502/

The PDF is a print of the live page, so it always reflects the frozen record.
"""

from __future__ import annotations

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

OUTPUT = Path(__file__).resolve().parents[1] / "static" / "the-schools-record-sample-dossier.pdf"


def main(base: str) -> None:
    with sync_playwright() as play:
        browser = play.chromium.launch()
        page = browser.new_page(viewport={"width": 900, "height": 1400})
        page.goto(f"{base}?p=/sample-dossier", wait_until="domcontentloaded")
        page.wait_for_selector(".tsr .dossier-page", timeout=30000)
        page.wait_for_timeout(1500)
        page.emulate_media(media="print")
        page.add_style_tag(content="""
          .tsr .breadcrumbs, .tsr .dossier-actions, .tsr .dossier-cta { display: none !important; }
          .tsr .shell { width: 100% !important; }
          .tsr .dossier-cover { padding-block: 0 0 1.5rem !important; }
          .tsr .dossier-section { padding-block: 1.6rem !important; break-inside: auto; }
          .tsr .dossier-page { padding-bottom: 0 !important; }
          .tsr h1 { font-size: 2.6rem !important; }
          .tsr h2 { font-size: 1.7rem !important; }
        """)
        page.wait_for_timeout(400)
        page.pdf(
            path=str(OUTPUT),
            format="A4",
            print_background=True,
            margin={"top": "18mm", "bottom": "18mm", "left": "16mm", "right": "16mm"},
        )
        browser.close()
    print(f"wrote {OUTPUT} ({OUTPUT.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8502/")
