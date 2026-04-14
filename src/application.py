from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import pandas as pd

from .analyze import Analysis, analyze_reviews
from .ingest import guess_columns, reviews_from_dataframe, reviews_from_paste
from .respond import Draft, draft_response
from .types import BrandVoice, Review


@dataclass(frozen=True)
class CsvLoadOptions:
    text_col: str
    rating_col: Optional[str] = None
    date_col: Optional[str] = None
    author_col: Optional[str] = None


def preview_csv(file_bytes: bytes, *, max_rows: int = 50) -> pd.DataFrame:
    # Kept intentionally simple; callers can re-read if needed.
    df = pd.read_csv(pd.io.common.BytesIO(file_bytes))
    return df.head(max_rows)


def infer_csv_options(df: pd.DataFrame) -> dict[str, Optional[str]]:
    return guess_columns(df)


def load_reviews_from_csv(
    df: pd.DataFrame,
    *,
    options: CsvLoadOptions,
) -> list[Review]:
    return reviews_from_dataframe(
        df,
        text_col=options.text_col,
        rating_col=options.rating_col,
        date_col=options.date_col,
        author_col=options.author_col,
    )


def load_reviews_from_paste(text_block: str) -> list[Review]:
    return reviews_from_paste(text_block)


def get_insights(reviews: list[Review]) -> Analysis:
    return analyze_reviews(reviews)


def draft_replies(reviews: list[Review], *, voice: BrandVoice, limit: int = 15) -> list[Draft]:
    return [draft_response(r, voice) for r in reviews[: max(0, int(limit))]]

