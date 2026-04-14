from __future__ import annotations

import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Iterable, Optional

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from textblob import TextBlob

from .types import Review


@dataclass(frozen=True)
class ReviewSignal:
    polarity: float  # [-1, 1]
    subjectivity: float  # [0, 1]
    sentiment: str  # "negative" | "neutral" | "positive"


def sentiment_from_text(text: str) -> ReviewSignal:
    blob = TextBlob(text)
    pol = float(blob.sentiment.polarity)
    sub = float(blob.sentiment.subjectivity)

    # Calibrated to be conservative about "neutral"
    if pol <= -0.15:
        label = "negative"
    elif pol >= 0.20:
        label = "positive"
    else:
        label = "neutral"
    return ReviewSignal(polarity=pol, subjectivity=sub, sentiment=label)


RISK_PATTERNS: list[tuple[str, str]] = [
    ("legal_threat", r"\b(sue|lawsuit|attorney|lawyer|legal action|small claims)\b"),
    ("refund_chargeback", r"\b(chargeback|dispute the charge|refund|scam|fraud)\b"),
    ("safety_hygiene", r"\b(mold|roaches|rats|unsafe|hazard|poison|food poisoning)\b"),
    ("harassment_bias", r"\b(racist|sexist|harass|harassment|discriminat)\w*\b"),
    ("privacy", r"\b(dox|doxx|posted my|shared my)\b"),
]


def risk_flags(text: str) -> list[str]:
    t = (text or "").lower()
    flags: list[str] = []
    for name, pat in RISK_PATTERNS:
        if re.search(pat, t, re.IGNORECASE):
            flags.append(name)
    return flags


def bucket_from_rating(rating: Optional[float]) -> Optional[str]:
    if rating is None or (isinstance(rating, float) and math.isnan(rating)):
        return None
    if rating <= 2:
        return "negative"
    if rating == 3:
        return "neutral"
    if rating >= 4:
        return "positive"
    return None


def choose_sentiment(review: Review) -> ReviewSignal:
    # Prefer rating if available, else use text polarity.
    r_bucket = bucket_from_rating(review.rating)
    s = sentiment_from_text(review.text)
    if r_bucket:
        return ReviewSignal(polarity=s.polarity, subjectivity=s.subjectivity, sentiment=r_bucket)
    return s


def _top_keywords(texts: list[str], *, top_n: int = 12) -> list[tuple[str, float]]:
    if not texts:
        return []
    vec = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2),
        min_df=2 if len(texts) >= 12 else 1,
        max_features=2000,
    )
    X = vec.fit_transform(texts)
    scores = np.asarray(X.mean(axis=0)).ravel()
    idx = scores.argsort()[::-1][:top_n]
    feats = np.array(vec.get_feature_names_out())
    return [(str(feats[i]), float(scores[i])) for i in idx if scores[i] > 0]


def _representative_examples(texts: list[str], *, k: int = 3) -> list[int]:
    # Pick k diverse-ish examples by TF-IDF similarity to centroid.
    if not texts:
        return []
    vec = TfidfVectorizer(stop_words="english", max_features=1500)
    X = vec.fit_transform(texts)
    centroid = X.mean(axis=0)
    sims = cosine_similarity(X, centroid)
    order = np.argsort(-sims.ravel())
    picks: list[int] = []
    for i in order:
        if len(picks) >= k:
            break
        if i in picks:
            continue
        picks.append(int(i))
    return picks


@dataclass(frozen=True)
class Analysis:
    total: int
    counts: dict[str, int]
    avg_rating: Optional[float]
    top_positive_themes: list[str]
    top_negative_themes: list[str]
    highlights_positive: list[str]
    highlights_negative: list[str]
    risk_counts: dict[str, int]


def analyze_reviews(reviews: Iterable[Review]) -> Analysis:
    reviews = list(reviews)
    signals = [choose_sentiment(r) for r in reviews]
    by_bucket: dict[str, list[Review]] = defaultdict(list)
    for r, s in zip(reviews, signals):
        by_bucket[s.sentiment].append(r)

    counts = {k: len(v) for k, v in by_bucket.items()}
    total = len(reviews)

    ratings = [r.rating for r in reviews if r.rating is not None and not (isinstance(r.rating, float) and math.isnan(r.rating))]
    avg_rating = float(np.mean(ratings)) if ratings else None

    pos_texts = [r.text for r in by_bucket.get("positive", [])]
    neg_texts = [r.text for r in by_bucket.get("negative", [])]

    pos_kw = _top_keywords(pos_texts, top_n=10)
    neg_kw = _top_keywords(neg_texts, top_n=10)
    top_positive_themes = [k for k, _ in pos_kw]
    top_negative_themes = [k for k, _ in neg_kw]

    pos_idx = _representative_examples(pos_texts, k=3)
    neg_idx = _representative_examples(neg_texts, k=3)
    highlights_positive = [pos_texts[i] for i in pos_idx] if pos_texts else []
    highlights_negative = [neg_texts[i] for i in neg_idx] if neg_texts else []

    rc = Counter()
    for r in reviews:
        rc.update(risk_flags(r.text))

    return Analysis(
        total=total,
        counts={"negative": counts.get("negative", 0), "neutral": counts.get("neutral", 0), "positive": counts.get("positive", 0)},
        avg_rating=avg_rating,
        top_positive_themes=top_positive_themes,
        top_negative_themes=top_negative_themes,
        highlights_positive=highlights_positive,
        highlights_negative=highlights_negative,
        risk_counts=dict(sorted(rc.items(), key=lambda x: (-x[1], x[0]))),
    )

