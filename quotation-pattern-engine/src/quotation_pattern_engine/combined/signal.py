from __future__ import annotations

from quotation_pattern_engine.external.models import ExternalSignal
from quotation_pattern_engine.operational.models import SignalAssessment

from .config import CombinedConfig
from .models import CombinedSignal


def _clip(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def combine_signals(internal: SignalAssessment, external: ExternalSignal, config: CombinedConfig) -> CombinedSignal:
    wi = config.internal_weight * internal.confidence
    we = config.external_weight * external.confidence
    total = wi + we
    if total <= 1e-12:
        score = expected = 0.0
    else:
        score = (wi * internal.score + we * external.score) / total
        expected = (wi * internal.expected_change_per_litre_day + we * external.expected_change_eur_per_litre_day) / total
    base_confidence = (
        config.internal_weight * internal.confidence + config.external_weight * external.confidence
    ) / (config.internal_weight + config.external_weight)
    disagree = internal.score * external.score < 0
    if disagree:
        confidence = base_confidence - config.disagreement_penalty * min(abs(internal.score), abs(external.score))
        extra = ("Internal and external evidence disagree; discretionary volume is penalised.",)
    else:
        confidence = base_confidence + config.agreement_bonus * min(abs(internal.score), abs(external.score))
        extra = ()
    return CombinedSignal(
        score=_clip(score, -1.0, 1.0),
        confidence=_clip(confidence, 0.0, 1.0),
        expected_change_per_litre_day=expected,
        uncertainty_eur_per_litre_day=external.uncertainty_eur_per_litre_day,
        price_percentile=internal.price_percentile,
        internal_score=internal.score,
        internal_confidence=internal.confidence,
        internal_expected_change_per_litre_day=internal.expected_change_per_litre_day,
        external_score=external.score,
        external_confidence=external.confidence,
        external_expected_change_per_litre_day=external.expected_change_eur_per_litre_day,
        patterns=tuple(internal.patterns),
        external_drivers=tuple(sorted({x.driver for x in external.components})),
        external_themes=external.themes_used,
        caveats=tuple(internal.caveats) + external.caveats + extra,
    )
