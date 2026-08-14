from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from quotation_pattern_engine.operational.models import CandidateEvaluation


@dataclass(frozen=True)
class CombinedSignal:
    score: float
    confidence: float
    expected_change_per_litre_day: float
    uncertainty_eur_per_litre_day: float
    price_percentile: float
    internal_score: float
    internal_confidence: float
    internal_expected_change_per_litre_day: float
    external_score: float
    external_confidence: float
    external_expected_change_per_litre_day: float
    patterns: tuple[str, ...]
    external_drivers: tuple[str, ...]
    external_themes: tuple[str, ...]
    caveats: tuple[str, ...]


@dataclass(frozen=True)
class CombinedPurchaseDecision:
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
    internal_signal_score: float
    internal_signal_confidence: float
    internal_expected_change_eur_per_litre_day: float
    external_signal_score: float
    external_signal_confidence: float
    external_expected_change_eur_per_litre_day: float
    combined_signal_score: float
    combined_signal_confidence: float
    combined_expected_change_eur_per_litre_day: float
    combined_uncertainty_eur_per_litre_day: float
    candidates_evaluated: int
    selected_expected_cost_eur: float
    required_only_expected_cost_eur: float
    expected_advantage_eur: float
    downside_cost_eur: float
    patterns_used: str
    external_drivers: str
    external_themes: str
    caveats: str
    reason: str
    candidate_trace: tuple[CandidateEvaluation, ...]
