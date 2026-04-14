from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

from .analyze import risk_flags, sentiment_from_text
from .types import BrandVoice, Review


@dataclass(frozen=True)
class Draft:
    sentiment: str
    risk_flags: list[str]
    response: str
    notes: list[str]


_PERSONAL_DATA = re.compile(r"\b(\d{3}[-.\s]?\d{3}[-.\s]?\d{4}|[\w\.-]+@[\w\.-]+\.\w{2,})\b")


def _redact_personal_data(s: str) -> str:
    return _PERSONAL_DATA.sub("[redacted]", s)


def _clamp_len(s: str, *, max_chars: int = 850) -> str:
    s = (s or "").strip()
    if len(s) <= max_chars:
        return s
    return s[: max_chars - 1].rstrip() + "…"


def _safe_language_filter(text: str) -> tuple[str, list[str]]:
    notes: list[str] = []
    t = text

    # Avoid admissions of wrongdoing / liability-like phrasing.
    bad_phrases = [
        (r"\bwe (?:failed|messed up|screwed up)\b", "Avoid admitting fault; use empathy + fix-forward instead."),
        (r"\bit(?:'| i)s our fault\b", "Avoid assigning blame; focus on making it right."),
        (r"\bwe broke\b", "Avoid liability phrasing; describe next step instead."),
    ]
    for pat, note in bad_phrases:
        if re.search(pat, t, re.IGNORECASE):
            notes.append(note)
            t = re.sub(pat, "we’re sorry to hear this", t, flags=re.IGNORECASE)

    return t, notes


def draft_response(review: Review, voice: BrandVoice) -> Draft:
    s = sentiment_from_text(review.text)
    flags = risk_flags(review.text)

    business = (voice.business_name or "Our business").strip()
    signoff = (voice.signoff_name or "Team").strip()
    tone = (voice.tone or "Warm & professional").strip()
    contact_line = (voice.contact_line or "").strip()

    # Keep replies short and professional; do not quote the whole review.
    if s.sentiment == "positive":
        body = (
            f"Thanks for the love - and for choosing {business}! "
            "We're happy you had a great visit."
        )
        cta = "Hope to see you again soon!"
    elif s.sentiment == "neutral":
        body = (
            f"Thanks for taking the time to leave a review and for choosing {business}. "
            "We're always working to get better."
        )
        cta = "If you share what we could do better next time, we'll take it seriously."
    else:
        body = (
            "Thanks for the feedback - we're sorry your visit wasn't great. "
            "We'd like to look into it and make it right."
        )
        cta = "Please reach out so we can help."

    # Risk-aware tweaks.
    risk_notes: list[str] = []
    if "privacy" in flags:
        risk_notes.append("Avoid discussing personal details publicly; invite offline.")
        cta = "Please reach out directly so we can help privately."
    if "legal_threat" in flags:
        risk_notes.append("Keep it calm and brief; invite offline; avoid debate.")
        body = (
            "Thanks for the note. We take concerns seriously and would like to look into this."
        )
        cta = "Please reach out directly so we can review the details."
    if "refund_chargeback" in flags:
        risk_notes.append("Don’t promise refunds publicly; direct to support channel.")
        cta = "Please reach out directly so we can review and help."

    if any(f in flags for f in ["food_safety_illness", "allergens", "foreign_object", "cleanliness", "safety_hygiene"]):
        risk_notes.append("Food safety / hygiene concern: acknowledge + route offline quickly.")
        body = (
            "Thanks for letting us know - we're sorry to hear this. "
            "We take food safety and cleanliness seriously and want to follow up right away."
        )
        cta = "Please reach out directly with the date/time of your visit so we can investigate."

    offline = f" {contact_line}" if contact_line else ""
    resp = f"{body} {cta}{offline}\n\n- {signoff}"

    # Apply safety filters.
    resp = _redact_personal_data(resp)
    resp, filter_notes = _safe_language_filter(resp)

    # Add voice hint as a subtle style constraint (kept out of the public reply).
    notes: list[str] = []
    notes.append(f"Tone target: {tone}.")
    if voice.values:
        notes.append(f"Values: {voice.values.strip()}.")
    if voice.do_not_say:
        notes.append(f"Do-not-say: {voice.do_not_say.strip()}.")
    notes.extend(risk_notes)
    notes.extend(filter_notes)

    return Draft(
        sentiment=s.sentiment,
        risk_flags=flags,
        response=_clamp_len(resp),
        notes=notes,
    )


def response_style_preview(voice: BrandVoice) -> str:
    return (
        f"Business: {voice.business_name}\n"
        f"Sign-off: {voice.signoff_name}\n"
        f"Tone: {voice.tone}\n"
        f"Values: {voice.values}\n"
        f"Do-not-say: {voice.do_not_say}\n"
        f"Contact line: {voice.contact_line}\n"
    )

