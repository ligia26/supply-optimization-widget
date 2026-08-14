from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True)
class ExternalMarketObservation:
    observation_date: date
    available_at: datetime
    indicator: str
    product_scope: tuple[str, ...]
    market_scope: str
    driver: str
    value: float
    unit: str
    source: str
    source_reliability: float
    quality_status: str


@dataclass(frozen=True)
class ExternalNewsEvent:
    event_id: str
    theme_id: str
    published_at: datetime
    available_at: datetime
    event_start: date
    event_end: date
    expected_duration_days: int
    event_type: str
    driver: str
    market_scope: str
    headline: str
    supplier_relevance: float
    expected_pass_through_days: int
    diesel_direction: str
    diesel_effect_strength: float
    gasoline_direction: str
    gasoline_effect_strength: float
    source_reliability: float
    interpretation_confidence: float


@dataclass(frozen=True)
class ExternalSignalComponent:
    component_id: str
    theme_id: str
    component_type: str
    driver: str
    direction_score: float
    confidence: float
    expected_change_eur_per_litre_day: float
    uncertainty_eur_per_litre_day: float
    explanation: str


@dataclass(frozen=True)
class ExternalSignal:
    score: float
    confidence: float
    expected_change_eur_per_litre_day: float
    uncertainty_eur_per_litre_day: float
    components: tuple[ExternalSignalComponent, ...]
    themes_used: tuple[str, ...]
    caveats: tuple[str, ...]
