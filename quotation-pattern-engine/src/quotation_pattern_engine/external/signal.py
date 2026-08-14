from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta
import math
import statistics

from .config import ExternalConfig
from .models import (
    ExternalMarketObservation,
    ExternalNewsEvent,
    ExternalSignal,
    ExternalSignalComponent,
)

_DIRECTION = {"UP": 1.0, "DOWN": -1.0, "MIXED": 0.0, "NEUTRAL": 0.0}


def _clip(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _matches_product(scope: tuple[str, ...], product: str) -> bool:
    aliases = {
        "Diesel": {"Diesel", "Gasolio Synergy"},
        "Verde": {"Verde", "Benzina Synergy"},
    }
    return not scope or bool(set(scope) & aliases.get(product, {product}))


def _market_components(
    observations: list[ExternalMarketObservation],
    product: str,
    decision_date: date,
    cutoff: datetime,
    config: ExternalConfig,
) -> list[ExternalSignalComponent]:
    components: list[ExternalSignalComponent] = []
    weights = config.product_indicator_weights.get(product, {})
    for indicator, product_weight in weights.items():
        visible = [
            x for x in observations
            if x.indicator == indicator
            and x.available_at <= cutoff
            and _matches_product(x.product_scope, product)
            and 0 <= (decision_date - x.observation_date).days <= config.market_lookback_days
        ]
        by_date: dict[date, ExternalMarketObservation] = {}
        for row in visible:
            if row.observation_date not in by_date or row.available_at > by_date[row.observation_date].available_at:
                by_date[row.observation_date] = row
        series = sorted(by_date.values(), key=lambda x: x.observation_date)
        if len(series) < 2:
            continue
        returns = [math.log(series[i].value / series[i - 1].value) for i in range(1, len(series)) if series[i - 1].value > 0 and series[i].value > 0]
        if not returns:
            continue
        latest_return = returns[-1]
        trend_return = math.log(series[-1].value / series[max(0, len(series) - 4)].value)
        blended = 0.60 * latest_return + 0.40 * trend_return
        volatility = statistics.pstdev(returns) if len(returns) >= 2 else abs(latest_return)
        direction = _clip(blended / max(2.0 * volatility, 0.005), -1.0, 1.0)
        latest = series[-1]
        age = max(0, (decision_date - latest.observation_date).days)
        freshness = math.exp(-math.log(2.0) * age / 3.0)
        scope_weight = config.market_scope_weights.get(latest.market_scope, 0.50)
        confidence = _clip(product_weight * scope_weight * latest.source_reliability * freshness, 0.0, 1.0)
        coefficient = config.pass_through.get(indicator, 0.0)
        expected_change = direction * abs(coefficient) * 0.01 * confidence
        if coefficient < 0:
            expected_change *= -1.0
        components.append(ExternalSignalComponent(
            component_id=indicator,
            theme_id=indicator,
            component_type="MARKET",
            driver=latest.driver,
            direction_score=direction,
            confidence=confidence,
            expected_change_eur_per_litre_day=expected_change,
            uncertainty_eur_per_litre_day=volatility * abs(coefficient) * confidence,
            explanation=f"{indicator}: blended return {blended:+.4%}, score {direction:+.3f}, confidence {confidence:.3f}",
        ))
    return components


def _news_components(
    events: list[ExternalNewsEvent],
    product: str,
    decision_date: date,
    cutoff: datetime,
    config: ExternalConfig,
) -> list[ExternalSignalComponent]:
    grouped: dict[str, list[ExternalSignalComponent]] = defaultdict(list)
    for event in events:
        if event.available_at > cutoff:
            continue
        effective = event.event_start + timedelta(days=event.expected_pass_through_days)
        if decision_date < effective:
            continue
        age = (decision_date - effective).days
        if age > event.expected_duration_days:
            continue
        decay = max(0.0, 1.0 - age / max(1, event.expected_duration_days))
        if product == "Diesel":
            direction_name, strength = event.diesel_direction, event.diesel_effect_strength
        elif product == "Verde":
            direction_name, strength = event.gasoline_direction, event.gasoline_effect_strength
        else:
            continue
        direction = _DIRECTION.get(direction_name, 0.0)
        if direction == 0.0 or strength <= 0.0:
            continue
        scope = config.market_scope_weights.get(event.market_scope, 0.50)
        driver = config.news_driver_weights.get(event.driver, 0.50)
        confidence = _clip(
            event.source_reliability * event.interpretation_confidence
            * event.supplier_relevance * scope * driver * decay,
            0.0, 1.0,
        )
        expected_change = direction * strength * confidence * config.news_eur_per_litre_day_scale
        grouped[event.theme_id].append(ExternalSignalComponent(
            component_id=event.event_id,
            theme_id=event.theme_id,
            component_type="NEWS",
            driver=event.driver,
            direction_score=direction,
            confidence=confidence,
            expected_change_eur_per_litre_day=expected_change,
            uncertainty_eur_per_litre_day=abs(expected_change) * 0.50,
            explanation=f"{event.headline}; theme={event.theme_id}; confidence={confidence:.3f}",
        ))

    result: list[ExternalSignalComponent] = []
    for _, components in grouped.items():
        components.sort(key=lambda x: abs(x.direction_score * x.confidence), reverse=True)
        used = 0.0
        for component in components:
            raw = abs(component.direction_score * component.confidence)
            room = max(0.0, config.news_theme_cap - used)
            if room <= 0:
                break
            ratio = min(1.0, room / max(raw, 1e-12))
            result.append(ExternalSignalComponent(
                component_id=component.component_id,
                theme_id=component.theme_id,
                component_type=component.component_type,
                driver=component.driver,
                direction_score=component.direction_score,
                confidence=component.confidence * ratio,
                expected_change_eur_per_litre_day=component.expected_change_eur_per_litre_day * ratio,
                uncertainty_eur_per_litre_day=component.uncertainty_eur_per_litre_day * ratio,
                explanation=component.explanation + ("; theme-capped" if ratio < 1 else ""),
            ))
            used += raw * ratio
    return result


def build_external_signal(
    market_observations: list[ExternalMarketObservation],
    news_events: list[ExternalNewsEvent],
    product: str,
    decision_date: date,
    cutoff: datetime,
    config: ExternalConfig,
) -> ExternalSignal:
    components = _market_components(market_observations, product, decision_date, cutoff, config)
    components.extend(_news_components(news_events, product, decision_date, cutoff, config))
    usable = [x for x in components if x.confidence >= config.min_component_confidence]
    if not usable:
        return ExternalSignal(0.0, 0.0, 0.0, 0.0, (), (), ("No external component passed the confidence threshold",))
    denominator = sum(x.confidence for x in usable)
    score = sum(x.direction_score * x.confidence for x in usable) / denominator
    expected = sum(x.expected_change_eur_per_litre_day * x.confidence for x in usable) / denominator
    uncertainty = math.sqrt(sum(x.uncertainty_eur_per_litre_day ** 2 for x in usable))
    confidence = 1.0 - math.exp(-denominator)
    themes = tuple(sorted({x.theme_id for x in usable if x.component_type == "NEWS"}))
    return ExternalSignal(_clip(score, -1.0, 1.0), _clip(confidence, 0.0, 1.0), expected, uncertainty, tuple(usable), themes, ())
