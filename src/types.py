from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class Review:
    text: str
    rating: Optional[float] = None
    created_at: Optional[datetime] = None
    author: Optional[str] = None
    source_row: Optional[int] = None


@dataclass(frozen=True)
class BrandVoice:
    business_name: str = "Your Business"
    signoff_name: str = "Team"
    tone: str = "Warm & professional"
    values: str = "Helpful, respectful, solution-oriented"
    do_not_say: str = "Do not mention refunds unless you intend to offer one"

