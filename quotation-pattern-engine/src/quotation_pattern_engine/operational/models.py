from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date


@dataclass(frozen=True)
class TankState:
    distributor_id: str
    product: str
    capacity_litres: float
    opening_inventory_litres: float
    opening_implicit_cost_per_litre: float
    selling_price_per_litre: float | None


@dataclass(frozen=True)
class DemandProfile:
    distributor_id: str
    product: str
    weekday: int
    average_daily_litres_2025: float
    growth_factor_2026: float

    @property
    def forecast_daily_litres(self) -> float:
        return self.average_daily_litres_2025 * self.growth_factor_2026


@dataclass(frozen=True)
class QuotationPoint:
    date: date
    product: str
    quotation_product: str
    price_per_litre: float
    regime: str
    event_type: str
    change_per_litre: float | None


@dataclass(frozen=True)
class PatternEvent:
    product: str
    pattern_id: str
    pattern_name: str
    start_date: date
    end_date: date
    direction: str = ""
    magnitude_per_litre: float | None = None
    threshold_per_litre: float | None = None
    duration_days: int | None = None
    event_type: str = ""
    confidence: float | None = None
    raw: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class PatternSummary:
    product: str
    metrics: dict[str, float | str]


@dataclass(frozen=True)
class SignalAssessment:
    score: float
    confidence: float
    expected_change_per_litre_day: float
    price_percentile: float
    empirical_change_scale: float
    patterns: tuple[str, ...]
    caveats: tuple[str, ...]


@dataclass(frozen=True)
class PriceScenario:
    name: str
    probability: float
    daily_change_eur_per_litre: float


@dataclass(frozen=True)
class CandidateEvaluation:
    purchase_litres: float
    target_cover_days: float

    purchase_cost_eur: float
    expected_future_cost_eur: float
    expected_cost_eur: float

    downside_cost_eur: float
    holding_cost_eur: float
    capital_cost_eur: float
    order_cost_eur: float
    robust_objective_eur: float

    expected_future_price_eur_per_litre: float
    scenario_costs: tuple[float, ...]

    selected: bool = False
    selection_reason: str = ""


@dataclass(frozen=True)
class PurchaseDecision:
    date: date
    strategy: str
    distributor_id: str
    product: str
    quotation_eur_per_litre: float
    inventory_before_litres: float
    purchase_litres: float
    purchase_spend_eur: float
    selected_cover_days: float
    operational_required_litres: float
    discretionary_litres: float
    signal_score: float
    signal_confidence: float
    expected_change_eur_per_litre_day: float
    observed_price_percentile: float
    candidates_evaluated: int
    selected_expected_cost_eur: float
    required_only_expected_cost_eur: float
    expected_advantage_eur: float
    downside_cost_eur: float
    patterns_used: str
    caveats: str
    reason: str

    # Full optimiser audit trail. Existing consumers can ignore this field.
    candidate_trace: tuple[CandidateEvaluation, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class DailyLedgerRow:
    date: date
    strategy: str
    distributor_id: str
    product: str
    opening_inventory_litres: float
    opening_implicit_cost_per_litre: float
    purchase_litres: float
    purchase_price_eur_per_litre: float
    purchase_total_eur: float
    sales_litres: float
    lost_sales_litres: float
    closing_inventory_litres: float
    closing_implicit_cost_per_litre: float
    regime: str
