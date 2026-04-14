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

    # Keep replies short and professional; do not quote the whole review.
    if s.sentiment == "positive":
        body = (
            f"Thanks so much for the kind words and for choosing {business}. "
            "We’re really glad you had a great experience. "
            "If there’s anything we can do for you in the future, we’re here to help."
        )
        cta = "We’d love to see you again soon."
    elif s.sentiment == "neutral":
        body = (
            f"Thanks for taking the time to leave a review. "
            f"We appreciate you choosing {business}, and we’re always working to improve."
        )
        cta = "If you’re open to it, share what we could do better next time."
    else:
        body = (
            "Thanks for the feedback, and I’m sorry to hear your experience didn’t meet expectations. "
            "We’d like to understand what happened and make things right."
        )
        cta = "Please contact us directly so we can help."

    # Risk-aware tweaks.
    risk_notes: list[str] = []
    if "privacy" in flags:
        risk_notes.append("Avoid discussing personal details publicly; invite offline.")
        cta = "Please contact us directly so we can help privately."
    if "legal_threat" in flags:
        risk_notes.append("Keep it calm and brief; invite offline; avoid debate.")
        body = (
            "Thanks for the note. We take concerns seriously and would like to look into this."
        )
        cta = "Please contact us directly so we can review the details."
    if "refund_chargeback" in flags:
        risk_notes.append("Don’t promise refunds publicly; direct to support channel.")
        cta = "Please contact us directly so we can review your order and help."
    if "safety_hygiene" in flags:
        risk_notes.append("Acknowledge concern; invite offline; avoid defensiveness.")
        cta = "Please contact us directly so we can follow up right away."

    resp = f"{body} {cta}\n\n— {signoff}"

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
    )

