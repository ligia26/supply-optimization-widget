from __future__ import annotations
from dataclasses import dataclass
from datetime import date, datetime

@dataclass(frozen=True)
class LocalDailySignal:
    date: date
    fuel: str
    avg_price: float
    min_price: float
    max_price: float
    competitors: int

@dataclass(frozen=True)
class CompetitorPrice:
    snapshot_date: date
    station_id: str
    fuel: str
    price: float
    is_self: bool
    communicated_at: datetime | None
