"""Enquiry and correction forms.

The published site posts to server endpoints that a Streamlit deployment does
not provide, so submissions are appended to a local JSON Lines review file and
the submitter sees the same confirmation copy.  Nothing here touches the record.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st

from .ui import controls, write

REVIEW_DIR = Path(__file__).resolve().parents[1] / "review-queue"

ROLES = (
    "Parent or prospective parent",
    "Education consultant",
    "Researcher",
    "Journalist",
    "School leadership",
    "Communications team",
    "Other professional",
)
DELIVERABLES = (
    "Sourced comparison dossier",
    "Structured data",
    "Professional access",
    "Methodological support",
    "Not sure yet",
)
BUDGETS = (
    "Prefer not to say",
    "Under £1,000",
    "£1,000–£2,499",
    "£2,500–£4,999",
    "£5,000+",
    "Need scoping first",
)


def _record(kind: str, payload: dict[str, object]) -> None:
    try:
        REVIEW_DIR.mkdir(parents=True, exist_ok=True)
        line = json.dumps(
            {"kind": kind, "received": datetime.now(timezone.utc).isoformat(), **payload},
            ensure_ascii=False,
        )
        with REVIEW_DIR.joinpath(f"{kind}.jsonl").open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
    except OSError:
        # A read-only deployment must never lose the page over a log write.
        pass


def enquiry_form() -> None:
    if st.session_state.get("enquiry_sent"):
        write("""<main class="narrow-shell section no-top-space"><div class="form-success" role="status">
  <p class="eyebrow">Enquiry received</p>
  <h2>Thank you. Your request is in the review queue.</h2>
  <p>No payment has been taken and no automated email has been sent. A human review is the next step.</p>
</div></main>""")
        return

    with controls("tsr-enquiry-form"), st.form("professional-enquiry", clear_on_submit=False):
        left, right = st.columns(2)
        name = left.text_input("Name *", max_chars=120)
        email = right.text_input("Email *", max_chars=254)
        left, right = st.columns(2)
        role = left.selectbox("Role *", ("Select one", *ROLES))
        organisation = right.text_input("Organisation", max_chars=160)
        schools = st.text_input(
            "Schools of interest *", max_chars=500, placeholder="For example, Eton and Westminster"
        )
        left, right = st.columns(2)
        deliverable = left.selectbox("Preferred deliverable *", ("Select one", *DELIVERABLES))
        deadline = right.text_input("Deadline", max_chars=80, placeholder="A date or timeframe")
        budget = st.columns(2)[0].selectbox("Approximate budget band", BUDGETS)
        intended_use = st.text_area(
            "Intended use *",
            max_chars=2000,
            height=140,
            placeholder="What decision, article or research question should the work support?",
        )
        consent = st.checkbox(
            "I have read the privacy notice and agree that these details may be stored and used to respond to this enquiry."
        )
        submitted = st.form_submit_button("Request a sourced comparison")

    if submitted:
        missing = not all([
            name.strip(), email.strip(), role != "Select one", schools.strip(),
            deliverable != "Select one", intended_use.strip(), consent,
        ])
        if missing:
            st.error("Please complete every required field and confirm the privacy notice.")
            return
        _record("professional-enquiry", {
            "name": name, "email": email, "role": role, "organisation": organisation,
            "schools": schools, "deliverable": deliverable, "deadline": deadline,
            "budgetBand": budget, "intendedUse": intended_use,
        })
        st.session_state["enquiry_sent"] = True
        st.rerun()


def correction_form() -> None:
    if st.session_state.get("correction_sent"):
        write("""<div class="form-success" role="status">
  <p class="eyebrow">Report received</p>
  <h2>Thank you. Your correction report is in the review queue.</h2>
  <p>The existing record remains unchanged while the issue is assessed.</p>
</div>""")
        return

    with controls("tsr-correction-form"), st.form("correction-report", clear_on_submit=False):
        left, right = st.columns(2)
        name = left.text_input("Name *", max_chars=120)
        email = right.text_input("Email *", max_chars=254)
        left, right = st.columns(2)
        school = left.text_input("School *", max_chars=120)
        period = right.text_input("Year or period", max_chars=80)
        dataset_or_page = st.text_input("Dataset or page", max_chars=160)
        issue = st.text_area("What appears to be wrong? *", max_chars=4000, height=150)
        evidence_reference = st.text_area(
            "Supporting evidence reference",
            max_chars=1000,
            height=90,
            placeholder="Describe the publication and where it can be found. This is stored privately.",
        )
        consent = st.checkbox(
            "I have read the privacy notice and agree that these details may be stored to review this report."
        )
        submitted = st.form_submit_button("Submit correction report")

    if submitted:
        if not all([name.strip(), email.strip(), school.strip(), issue.strip(), consent]):
            st.error("Please complete every required field and confirm the privacy notice.")
            return
        _record("correction-report", {
            "name": name, "email": email, "school": school, "period": period,
            "dataset": dataset_or_page, "issue": issue,
            "evidenceReference": evidence_reference,
        })
        st.session_state["correction_sent"] = True
        st.rerun()
