"""Enquiry and correction forms.

Submissions go through ``review_queue``; the confirmation the submitter sees
states exactly where the submission went and whether that store is durable,
and a failed write is shown as a failure together with a copy of the text so
nothing is lost.  Nothing here touches the record.
"""

from __future__ import annotations

import streamlit as st

from . import review_queue
from .ui import controls, esc, write

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


def receipt_markup(receipt: review_queue.Receipt, fields: dict[str, object], kind_label: str) -> str:
    copy = esc(review_queue.transcript(fields))
    if receipt.status == review_queue.FORWARDED:
        eyebrow, heading = f"{kind_label} received", "Thank you. Your submission has been received for review."
        tone = "form-success"
    elif receipt.status == review_queue.STORED:
        eyebrow, heading = f"{kind_label} recorded", "Thank you. Your submission has been written to this deployment's review file."
        tone = "form-success form-success-local"
    else:
        eyebrow, heading = f"{kind_label} not recorded", "Your submission could not be stored."
        tone = "form-error-block"
    durability = (
        ""
        if receipt.durable
        else "<p><strong>Please keep a copy.</strong> This deployment has no durable review store configured, so the entry below is your record of what was sent.</p>"
    )
    return f"""<div class="{tone}" role="status">
  <p class="eyebrow">{esc(eyebrow)}</p>
  <h2>{esc(heading)}</h2>
  <p>{esc(receipt.detail)} Reference <code>{esc(receipt.reference)}</code>.</p>
  <p>No payment has been taken and no automated email has been sent. A human review is the next step.</p>
  {durability}
  <details class="submission-copy"><summary>Copy of your submission</summary><pre>{copy}</pre></details>
</div>"""


def enquiry_form() -> None:
    sent = st.session_state.get("enquiry_receipt")
    if sent:
        write(f'<main class="narrow-shell section no-top-space">{receipt_markup(sent["receipt"], sent["fields"], "Enquiry")}</main>')
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
        fields = {
            "name": name, "email": email, "role": role, "organisation": organisation,
            "schools": schools, "deliverable": deliverable, "deadline": deadline,
            "budgetBand": budget, "intendedUse": intended_use,
        }
        receipt = review_queue.submit("professional-enquiry", fields)
        st.session_state["enquiry_receipt"] = {"receipt": receipt, "fields": fields}
        st.rerun()


def correction_form() -> None:
    sent = st.session_state.get("correction_receipt")
    if sent:
        write(receipt_markup(sent["receipt"], sent["fields"], "Report"))
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
        fields = {
            "name": name, "email": email, "school": school, "period": period,
            "dataset": dataset_or_page, "issue": issue,
            "evidenceReference": evidence_reference,
        }
        receipt = review_queue.submit("correction-report", fields)
        st.session_state["correction_receipt"] = {"receipt": receipt, "fields": fields}
        st.rerun()
