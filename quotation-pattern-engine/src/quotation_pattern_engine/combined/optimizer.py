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

    return tuple(
        PriceScenario(
            name=f"combined empirical q{int(q * 100)}",
            probability=probability,
            daily_change_eur_per_litre=(
                signal.expected_change_per_litre_day
                + _quantile(residuals, q)
                + uncertainty_multiplier * uncertainty_band
            ),
        )
        for q, probability, uncertainty_multiplier in zip(
            quantiles,
            probabilities,
            uncertainty_multipliers,
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
        future_need = max(
            0.0,
            total_demand - (inventory + buy),
        )

        covered_fraction = min(
            1.0,
            (inventory + buy) / max(total_demand, 1e-9),
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
) -> tuple[
    CandidateEvaluation,
    CandidateEvaluation,
    str,
]:
    """
    Select the best combined candidate while keeping the operational minimum
    as the hard feasibility floor.
    """
    if not candidates:
        raise ValueError(
            "No feasible candidates generated"
        )

    required = min(
        candidates,
        key=lambda candidate: (
            abs(
                candidate.purchase_litres
                - required_buy
            ),
            candidate.robust_objective_eur,
        ),
    )

    best = min(
        candidates,
        key=lambda candidate: (
            candidate.robust_objective_eur,
            candidate.purchase_litres,
        ),
    )

    improvement = (
        required.robust_objective_eur
        - best.robust_objective_eur
    )

    improvement_ratio = (
        improvement
        / max(
            required.robust_objective_eur,
            1e-9,
        )
    )

    if (
        signal.expected_change_per_litre_day <= 0
        and best.purchase_litres
        > required.purchase_litres
    ):
        return (
            required,
            required,
            "Operational minimum: combined evidence does not support advance buying",
        )

    if (
        signal.confidence
        < config.min_combined_confidence_for_discretionary_buy
        and best.purchase_litres
        > required.purchase_litres
    ):
        return (
            required,
            required,
            "Operational minimum: combined confidence is insufficient",
        )

    if (
        improvement
        < config.min_objective_improvement_eur
        or improvement_ratio
        < config.min_objective_improvement_ratio
    ):
        return (
            required,
            required,
            "Operational minimum: objective improvement is below action threshold",
        )

    return (
        best,
        required,
        "Combined internal/external robust objective supports advance purchase",
    )
