from __future__ import annotations

from datetime import date, timedelta
import math
import statistics

from quotation_pattern_engine.operational.config import OperationalConfig
from quotation_pattern_engine.operational.models import (
    CandidateEvaluation,
    PriceScenario,
    QuotationPoint,
    TankState,
)
from quotation_pattern_engine.operational.optimizer import (
    _candidate_volumes,
    demand_between,
)

from .config import CombinedConfig
from .models import CombinedSignal


def _quantile(values: list[float], q: float) -> float:
    if not values:
        return 0.0

    ordered = sorted(values)
    position = (len(ordered) - 1) * q
    lower = math.floor(position)
    upper = math.ceil(position)

    if lower == upper:
        return ordered[lower]

    return (
        ordered[lower] * (upper - position)
        + ordered[upper] * (position - lower)
    )


def build_combined_scenarios(
    history: list[QuotationPoint],
    signal: CombinedSignal,
    config: CombinedConfig,
) -> tuple[PriceScenario, ...]:
    """
    Build scenarios from both internal quotation behaviour and external
    market uncertainty.

    The scenario centre is the combined expected change. Historical internal
    residuals describe observed supplier-price variability. External
    uncertainty widens the scenario distribution.
    """
    changes = [
        point.change_per_litre
        for point in history
        if point.change_per_litre is not None
    ][-10:]

    if len(changes) < 3:
        return (
            PriceScenario(
                name="combined fact-limited central",
                probability=1.0,
                daily_change_eur_per_litre=(
                    signal.expected_change_per_litre_day
                ),
            ),
        )

    historical_center = statistics.median(changes)
    residuals = [
        change - historical_center
        for change in changes
    ]

    uncertainty_band = (
        signal.uncertainty_eur_per_litre_day
        * config.scenario_uncertainty_multiplier
    )

    quantiles = (0.10, 0.25, 0.50, 0.75, 0.90)
    probabilities = (0.10, 0.20, 0.40, 0.20, 0.10)
    uncertainty_multipliers = (-1.0, -0.5, 0.0, 0.5, 1.0)

    # Residual/uncertainty scenarios describe dispersion around the signal,
    # not an additional directional forecast. Re-centre the shocks so their
    # probability-weighted mean is zero. This guarantees that the expected
    # scenario change equals the combined causal forecast itself.
    raw_shocks = [
        _quantile(residuals, q) + m * uncertainty_band
        for q, m in zip(quantiles, uncertainty_multipliers)
    ]
    weighted_shock = sum(p * shock for p, shock in zip(probabilities, raw_shocks))
    centred_shocks = [shock - weighted_shock for shock in raw_shocks]

    return tuple(
        PriceScenario(
            name=f"combined empirical q{int(q * 100)}",
            probability=probability,
            daily_change_eur_per_litre=(
                signal.expected_change_per_litre_day + shock
            ),
        )
        for q, probability, shock in zip(
            quantiles, probabilities, centred_shocks
        )
    )


def evaluate_combined_candidates(
    *,
    day: date,
    end: date,
    tank: TankState,
    inventory: float,
    current_price: float,
    required_buy: float,
    demand_lookup,
    signal: CombinedSignal,
    history: list[QuotationPoint],
    operational_config: OperationalConfig,
    combined_config: CombinedConfig,
) -> list[CandidateEvaluation]:
    """
    Evaluate purchase candidates with combined internal/external logic.

    This intentionally differs from the operational-only optimiser:

    - price scenarios are centred on the combined signal;
    - historical supplier residuals remain part of the scenario distribution;
    - external uncertainty widens the tails;
    - expected waiting time depends on how much demand the purchase covers;
    - downside risk is adjusted by combined-signal confidence.
    """
    planning_end = min(
        end + timedelta(days=1),
        day + timedelta(
            days=operational_config.planning_horizon_days
        ),
    )

    total_demand = demand_between(
        demand_lookup,
        tank.distributor_id,
        tank.product,
        day,
        planning_end,
    )

    scenarios = build_combined_scenarios(
        history,
        signal,
        combined_config,
    )

    planning_days = max(
        1,
        (planning_end - day).days,
    )

    result: list[CandidateEvaluation] = []

    for buy, cover_days in _candidate_volumes(
        day=day,
        planning_end=planning_end,
        tank=tank,
        inventory=inventory,
        demand_lookup=demand_lookup,
        required_buy=required_buy,
        config=operational_config,
    ):
        usable_inventory_for_demand = max(
            0.0,
            inventory + buy - operational_config.hard_min_stock_litres,
        )
        raw_future_need = max(
            0.0,
            total_demand - usable_inventory_for_demand,
        )
        # Future procurement is not infinitely divisible: if a future shortfall
        # exists, the operator will have to place at least one standard order.
        # Costing only the raw shortfall (e.g. 11 L) massively understates the
        # value of buying a 5,000 L standard load earlier at a cheaper price.
        future_need = (
            max(raw_future_need, operational_config.minimum_order_litres)
            if raw_future_need > 1e-9
            else 0.0
        )
        if future_need > 0 and operational_config.order_rounding_litres > 0:
            future_need = (
                math.ceil(
                    (future_need - 1e-9)
                    / operational_config.order_rounding_litres
                )
                * operational_config.order_rounding_litres
            )

        covered_fraction = min(
            1.0,
            usable_inventory_for_demand / max(total_demand, 1e-9),
        )

        expected_wait_days = max(
            1.0,
            planning_days
            * (0.35 + 0.65 * covered_fraction),
        )

        holding_days = max(
            0.0,
            cover_days,
        ) / 2.0

        purchase_cost = buy * current_price

        holding_cost = (
            buy
            * operational_config.holding_cost_eur_per_litre_day
            * holding_days
        )

        capital_cost = (
            buy
            * current_price
            * operational_config.working_capital_cost_rate_daily
            * holding_days
        )

        order_cost = (
            (
                operational_config.order_cost_eur
                if buy > 1e-9
                else 0.0
            )
            + (
                operational_config.order_cost_eur
                if future_need > 1e-9
                else 0.0
            )
        )

        scenario_costs: list[float] = []
        expected_future_price = 0.0
        expected_future_cost = 0.0

        for scenario in scenarios:
            future_price = max(
                0.0,
                current_price
                + scenario.daily_change_eur_per_litre
                * expected_wait_days,
            )

            future_cost = future_need * future_price

            expected_future_price += (
                scenario.probability * future_price
            )

            expected_future_cost += (
                scenario.probability * future_cost
            )

            scenario_costs.append(
                purchase_cost
                + future_cost
                + holding_cost
                + capital_cost
                + order_cost
            )

        expected_cost = sum(
            scenario.probability * scenario_cost
            for scenario, scenario_cost in zip(
                scenarios,
                scenario_costs,
            )
        )

        downside_cost = (
            max(scenario_costs) - expected_cost
            if scenario_costs
            else 0.0
        )

        confidence_adjusted_risk = (
            operational_config.risk_aversion
            * (2.0 - signal.confidence)
        )

        robust_objective = (
            expected_cost
            + confidence_adjusted_risk
            * max(0.0, downside_cost)
        )

        result.append(
            CandidateEvaluation(
                purchase_litres=buy,
                target_cover_days=cover_days,
                purchase_cost_eur=purchase_cost,
                expected_future_cost_eur=expected_future_cost,
                expected_cost_eur=expected_cost,
                downside_cost_eur=max(
                    0.0,
                    downside_cost,
                ),
                holding_cost_eur=holding_cost,
                capital_cost_eur=capital_cost,
                order_cost_eur=order_cost,
                robust_objective_eur=robust_objective,
                expected_future_price_eur_per_litre=(
                    expected_future_price
                ),
                scenario_costs=tuple(scenario_costs),
            )
        )

    return result


def select_combined_candidate(
    candidates: list[CandidateEvaluation],
    required_buy: float,
    signal: CombinedSignal,
    config: CombinedConfig,
) -> tuple[CandidateEvaluation, CandidateEvaluation, str]:
    """Select a combined candidate with conservative, evidence-scaled anticipation.

    Operational litres are always allowed. Discretionary litres are only allowed
    when the combined forecast is bullish, sufficiently confident, economically
    meaningful, and the current price is not already expensive. The amount that
    may be brought forward is capped by confidence; disagreement between internal
    and external evidence is capped at one standard 5k tranche.
    """
    if not candidates:
        raise ValueError("No feasible candidates generated")

    required = min(
        candidates,
        key=lambda c: (abs(c.purchase_litres - required_buy), c.robust_objective_eur),
    )
    best_unconstrained = min(
        candidates,
        key=lambda c: (c.robust_objective_eur, c.purchase_litres),
    )

    if best_unconstrained.purchase_litres <= required.purchase_litres + 1e-9:
        return best_unconstrained, required, "Combined objective does not require discretionary litres"

    adjusted_signal = signal.score * signal.confidence
    if signal.expected_change_per_litre_day <= 0:
        return required, required, "Operational minimum: combined forecast is not bullish"
    if signal.price_percentile > config.max_price_percentile_for_discretionary_buy:
        return required, required, "Operational minimum: current quotation is too expensive for advance buying"
    if signal.confidence < config.min_combined_confidence_for_discretionary_buy:
        return required, required, "Operational minimum: combined confidence is insufficient for strategic inventory"
    if adjusted_signal < config.min_adjusted_signal_for_discretionary_buy:
        return required, required, "Operational minimum: confidence-adjusted signal is too weak"

    # Evidence-scaled strategic cap. Moderate evidence may advance one 5k tranche;
    # stronger evidence can advance more, but never jump directly to filling spare
    # capacity. This implements the V3 rule: weak/moderate signal -> stay close to
    # operational minimum; strong/high-confidence signal -> allow larger anticipation.
    if signal.confidence < 0.70:
        cap = config.max_discretionary_litres_moderate_confidence
    elif signal.confidence < 0.85:
        cap = config.max_discretionary_litres_high_confidence
    else:
        cap = config.max_discretionary_litres_very_high_confidence

    # If internal and external directional evidence disagree, do not let the
    # combined engine advance more than one standard tranche.
    if signal.internal_score * signal.external_score < 0:
        cap = min(cap, config.max_discretionary_litres_moderate_confidence)

    max_allowed = required.purchase_litres + cap
    eligible = [c for c in candidates if c.purchase_litres <= max_allowed + 1e-9]
    best = min(eligible, key=lambda c: (c.robust_objective_eur, c.purchase_litres))

    improvement = required.robust_objective_eur - best.robust_objective_eur
    improvement_ratio = improvement / max(required.robust_objective_eur, 1e-9)
    if (
        best.purchase_litres <= required.purchase_litres + 1e-9
        or improvement < config.min_objective_improvement_eur
        or improvement_ratio < config.min_objective_improvement_ratio
    ):
        return required, required, "Operational minimum: economic advantage is below action threshold"

    discretionary = best.purchase_litres - required.purchase_litres
    return (
        best,
        required,
        f"Combined evidence supports a capped strategic advance of {discretionary:.0f} L",
    )

