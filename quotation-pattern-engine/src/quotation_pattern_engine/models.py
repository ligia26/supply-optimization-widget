from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import date
from typing import Any


@dataclass(frozen=True)
class Quotation:
    date: date
    product: str
    price: float
    supplier: str = "Unknown"
    valid_from: date | None = None
    valid_to: date | None = None
    event_type: str = "Normal quotation"
    source: str = ""
    priority: float = 0.0
    input_order: int = 0

    @property
    def series_key(self) -> tuple[str, str]:
        return self.supplier, self.product

    @property
    def canonical_key(self) -> tuple[date, str, str]:
        return self.date, self.supplier, self.product


@dataclass
class DailyAnalysis:
    date: date
    supplier: str
    product: str
    price: float
    previous_price: float | None
    change: float | None
    change_per_unit_divisor: float | None
    percentage_change: float | None
    direction: str
    moving_average: float
    rolling_volatility: float
    regime: str
    event_type: str
    source: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PatternEvent:
    pattern_id: str
    supplier: str
    product: str
    pattern_type: str
    start_date: date
    end_date: date
    observation_count: int
    magnitude: float
    confidence: str
    evidence: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
