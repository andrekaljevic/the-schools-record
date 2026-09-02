"""Shared helpers for the headless application tests."""

from __future__ import annotations

import sys
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

APP = ROOT / "streamlit_app.py"


@lru_cache(maxsize=None)
def render(route: str, params: tuple[tuple[str, str], ...] = ()) -> str:
    """Render one route headlessly and return its markup."""
    from streamlit.testing.v1 import AppTest

    app = AppTest.from_file(str(APP), default_timeout=180)
    app.query_params["p"] = route
    for key, value in params:
        app.query_params[key] = value
    app.run()
    if len(app.exception):
        raise AssertionError(f"{route} {dict(params)} raised: {[item.value for item in app.exception]}")
    return "".join(item.value for item in app.markdown)


def page(route: str, **params: str) -> str:
    return render(route, tuple(sorted(params.items())))
