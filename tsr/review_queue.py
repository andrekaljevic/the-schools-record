"""Where enquiry and correction submissions go, and what the submitter is told.

The published site posted its forms to server endpoints that a Streamlit
deployment does not provide.  This module makes the replacement honest: a
submission is forwarded to a durable endpoint when the deployment configures
one, otherwise appended to a local review file; the receipt returned to the
page says exactly which happened, and a failed write is reported as a failure
rather than a success.  No credential or destination is invented: without
configuration the local file is the only backend, and the page says that it
may not persist on ephemeral hosting.

Configuration (environment variables or Streamlit secrets):

``TSR_REVIEW_WEBHOOK_URL``    HTTPS endpoint that receives each submission as a
                              JSON POST and answers 2xx when it has stored it.
``TSR_REVIEW_WEBHOOK_TOKEN``  optional bearer token sent with the POST.
``TSR_REVIEW_QUEUE_DIR``      directory for the local JSON Lines review files
                              (default: ``review-queue/`` beside the app).
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_QUEUE_DIR = ROOT / "review-queue"

STORED = "stored"
FORWARDED = "forwarded"
FAILED = "failed"


@dataclass(frozen=True)
class Receipt:
    status: str  # stored | forwarded | failed
    reference: str
    detail: str
    durable: bool

    @property
    def accepted(self) -> bool:
        return self.status in (STORED, FORWARDED)


def _setting(name: str) -> str | None:
    value = os.environ.get(name)
    if value:
        return value.strip() or None
    try:  # Streamlit secrets are optional and may not exist at all.
        import streamlit as st

        secret = st.secrets.get(name)  # type: ignore[union-attr]
        return str(secret).strip() if secret else None
    except Exception:
        return None


def queue_dir() -> Path:
    configured = _setting("TSR_REVIEW_QUEUE_DIR")
    return Path(configured) if configured else DEFAULT_QUEUE_DIR


def webhook() -> tuple[str | None, str | None]:
    return _setting("TSR_REVIEW_WEBHOOK_URL"), _setting("TSR_REVIEW_WEBHOOK_TOKEN")


def _reference(kind: str, received: datetime) -> str:
    return f"{kind[:3].upper()}-{received.strftime('%Y%m%d-%H%M%S')}"


def _post(url: str, token: str | None, payload: dict[str, Any], opener: Callable = urllib.request.urlopen) -> None:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(url, data=body, method="POST")
    request.add_header("Content-Type", "application/json; charset=utf-8")
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    with opener(request, timeout=10) as response:  # noqa: S310 - configured HTTPS endpoint
        status = getattr(response, "status", 200)
        if not 200 <= int(status) < 300:
            raise urllib.error.HTTPError(url, status, "unexpected status", None, None)


def _append(kind: str, payload: dict[str, Any], directory: Path) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / f"{kind}.jsonl"
    with target.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
    return target


def submit(kind: str, fields: dict[str, Any], *, opener: Callable = urllib.request.urlopen) -> Receipt:
    """Record a submission and say truthfully what happened to it."""
    received = datetime.now(timezone.utc)
    reference = _reference(kind, received)
    payload = {
        "kind": kind,
        "reference": reference,
        "received": received.isoformat(),
        **fields,
    }
    url, token = webhook()
    if url:
        if not url.lower().startswith("https://"):
            return Receipt(FAILED, reference, "The configured review endpoint is not an HTTPS address, so the submission was not sent.", False)
        try:
            _post(url, token, payload, opener=opener)
            return Receipt(FORWARDED, reference, "Forwarded to the configured review endpoint, which confirmed receipt.", True)
        except (urllib.error.URLError, OSError, ValueError) as error:
            return Receipt(FAILED, reference, f"The review endpoint did not confirm receipt ({error.__class__.__name__}).", False)
    try:
        target = _append(kind, payload, queue_dir())
    except OSError as error:
        return Receipt(FAILED, reference, f"The local review file could not be written ({error.__class__.__name__}).", False)
    configured = _setting("TSR_REVIEW_QUEUE_DIR") is not None
    return Receipt(
        STORED,
        reference,
        f"Written to the deployment's local review file ({target.name})."
        + ("" if configured else " No durable review store is configured for this deployment, so on ephemeral hosting the file may not survive a restart."),
        configured,
    )


def transcript(fields: dict[str, Any]) -> str:
    """A plain-text copy of a submission for the submitter to keep."""
    lines = []
    for key, value in fields.items():
        if value in (None, ""):
            continue
        lines.append(f"{key}: {value}")
    return "\n".join(lines)
