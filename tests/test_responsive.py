"""Representative pages stay usable at narrow widths.

Runs the application in a subprocess and inspects it with Playwright.  Skipped
when Playwright or a Chromium build is unavailable, so the rest of the suite
does not depend on a browser.
"""

from __future__ import annotations

import os
import shutil
import socket
import subprocess
import sys
import time
import unittest
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

try:  # pragma: no cover - availability check
    from playwright.sync_api import sync_playwright
except Exception:  # noqa: BLE001
    sync_playwright = None

CHROMIUM = next(
    (path for path in (
        os.environ.get("TSR_CHROMIUM"),
        "/opt/pw-browsers/chromium/chrome",
        "/opt/pw-browsers/chromium-1194/chrome-linux/chrome",
        shutil.which("chromium"),
        shutil.which("chromium-browser"),
        shutil.which("google-chrome"),
    ) if path and Path(path).exists()),
    None,
)

ROUTES = (
    "/schools",
    "/schools/kcs",
    "/schools/kcs/exam-results",
    "/schools/westminster/oxbridge",
    "/schools/st-pauls/us-universities",
    "/evidence",
    "/corrections",
)


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@unittest.skipIf(sync_playwright is None or CHROMIUM is None, "Playwright with Chromium is required")
class ResponsiveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.port = _free_port()
        cls.server = subprocess.Popen(
            [sys.executable, "-m", "streamlit", "run", str(ROOT / "streamlit_app.py"), "--server.port", str(cls.port),
             "--server.headless", "true", "--browser.gatherUsageStats", "false"],
            cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        deadline = time.time() + 60
        while time.time() < deadline:
            try:
                urllib.request.urlopen(f"http://127.0.0.1:{cls.port}/", timeout=2)
                break
            except Exception:  # noqa: BLE001
                time.sleep(1)
        else:
            raise RuntimeError("the application did not start")

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.terminate()
        cls.server.wait(timeout=20)

    def _inspect(self, route: str, width: int) -> dict:
        with sync_playwright() as play:
            browser = play.chromium.launch(executable_path=CHROMIUM)
            page = browser.new_page(viewport={"width": width, "height": 900})
            page.goto(f"http://127.0.0.1:{self.port}/?p={route}", wait_until="domcontentloaded")
            page.wait_for_selector(".tsr main", timeout=60000)
            page.wait_for_timeout(2500)
            info = page.evaluate(
                """() => {
                  const tables = [...document.querySelectorAll('.tsr .table-scroll')].map(el => {
                    const style = getComputedStyle(el);
                    return {overflow: style.overflowX, width: el.clientWidth, scrollWidth: el.scrollWidth, visible: el.getBoundingClientRect().height > 0};
                  });
                  const overflowing = [...document.querySelectorAll('.tsr main *')].filter(el => {
                    const rect = el.getBoundingClientRect();
                    return rect.right > window.innerWidth + 1 && !el.closest('.table-scroll') && !el.closest('.chart-wrap');
                  }).slice(0, 5).map(el => el.tagName + '.' + el.className);
                  return {
                    docWidth: document.documentElement.scrollWidth,
                    innerWidth: window.innerWidth,
                    tables,
                    overflowing,
                    exceptions: document.querySelectorAll('[data-testid=stException]').length,
                    cards: document.querySelectorAll('.tsr .dataset-card').length,
                    title: document.title,
                  };
                }"""
            )
            browser.close()
        return info

    def test_pages_do_not_overflow_horizontally_on_a_phone(self) -> None:
        for route in ROUTES:
            info = self._inspect(route, 390)
            self.assertEqual(info["exceptions"], 0, route)
            self.assertLessEqual(info["docWidth"], info["innerWidth"] + 1, f"{route} overflows the viewport")
            self.assertEqual(info["overflowing"], [], f"{route} has elements wider than the viewport: {info['overflowing']}")
            for table in info["tables"]:
                self.assertIn(table["overflow"], ("auto", "scroll"), route)

    def test_tables_render_and_are_titled_on_desktop(self) -> None:
        info = self._inspect("/schools/kcs/exam-results", 1366)
        self.assertEqual(info["exceptions"], 0)
        self.assertEqual(info["cards"], 5)
        self.assertIn("King’s College School, Wimbledon", info["title"])
        self.assertTrue(all(table["visible"] for table in info["tables"]))


if __name__ == "__main__":
    unittest.main()
