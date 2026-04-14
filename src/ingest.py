from __future__ import annotations

import re
from datetime import datetime
from typing import Optional

import pandas as pd
from dateutil import parser as date_parser

from .types import Review


def _norm_col(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(s).strip().lower()).strip()


def guess_columns(df: pd.DataFrame) -> dict[str, Optional[str]]:
    cols = list(df.columns)
    norm = {c: _norm_col(c) for c in cols}

    def pick(candidates: list[str]) -> Optional[str]:
        for c in cols:
            n = norm[c]
            for cand in candidates:
                if cand in n:
                    return c
        return None

    text_col = pick(["review", "comment", "text", "feedback", "content", "body"])
    rating_col = pick(["rating", "stars", "star"])
    date_col = pick(["date", "time", "created", "timestamp"])
    author_col = pick(["author", "reviewer", "name", "user", "customer"])

    return {"text": text_col, "rating": rating_col, "date": date_col, "author": author_col}


def _to_float(v) -> Optional[float]:
    try:
        if pd.isna(v):
            return None
        return float(v)
    except Exception:
        return None


def _to_dt(v) -> Optional[datetime]:
    try:
        if pd.isna(v):
            return None
        if isinstance(v, datetime):
            return v
        return date_parser.parse(str(v))
    except Exception:
        return None


def clean_text(s: str) -> str:
    s = str(s or "")
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    s = re.sub(r"[ \t]+", " ", s).strip()
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s


def reviews_from_dataframe(
    df: pd.DataFrame,
    *,
    text_col: str,
    rating_col: Optional[str] = None,
    date_col: Optional[str] = None,
    author_col: Optional[str] = None,
) -> list[Review]:
    out: list[Review] = []
    for i, row in df.iterrows():
        text_raw = row.get(text_col, "")
        text = clean_text(text_raw)
        if not text:
            continue

        rating = _to_float(row.get(rating_col)) if rating_col else None
        created_at = _to_dt(row.get(date_col)) if date_col else None
        author = None
        if author_col:
            a = row.get(author_col)
            author = None if pd.isna(a) else str(a).strip() or None

        out.append(
            Review(
                text=text,
                rating=rating,
                created_at=created_at,
                author=author,
                source_row=int(i) if isinstance(i, (int,)) else None,
            )
        )
    return out


def reviews_from_paste(text_block: str) -> list[Review]:
    # Accept either one review per line OR paragraphs separated by blank lines.
    raw = (text_block or "").strip()
    if not raw:
        return []
    chunks = re.split(r"\n\s*\n+", raw)
    if len(chunks) == 1:
        chunks = [c.strip() for c in raw.splitlines() if c.strip()]
    return [Review(text=clean_text(c)) for c in chunks if clean_text(c)]

