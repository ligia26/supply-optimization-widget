from __future__ import annotations

from datetime import date, timedelta
import math
import statistics

from .config import OperationalConfig
from .models import (
    CandidateEvaluation,
    PriceScenario,
    QuotationPoint,
    SignalAssessment,
    TankState,
)


def demand_between(lookup, dist, prod, start, end):
    total = 0.0
    d = start
    while d < end:
        total += lookup.get((dist, prod, d.weekday()), 0.0)
        d += timedelta(days=1)
    return total


def _weighted_quantile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    xs = sorted(values)
    idx = (len(xs) - 1) * q
    lo = int(math.floor(idx))
    hi = int(math.ceil(idx))
    if lo == hi:
        return xs[lo]
    return xs[lo] * (hi - idx) + xs[hi] * (idx - lo)


def build_price_scenarios(
    history: list[QuotationPoint],
    signal: SignalAssessment,
) -> tuple[PriceScenario, ...]:
    observed = [x.change_per_litre for x in history if x.change_per_litre is not None]
    residuals = observed[-10:]

    if len(residuals) < 3:
        return (
            PriceScenario(
                "fact-limited central",
                1.0,
                signal.expected_change_per_litre_day,
            ),
        )

    center = statistics.median(residuals)
    qs = (.10, .25, .50, .75, .90)
    probs = (.10, .20, .40, .20, .10)

    out = []
    for q, p in zip(qs, probs):
        empirical = _weighted_quantile(residuals, q) - center
        out.append(
            PriceScenario(
                f"empirical q{int(q * 100)}",
                p,
                signal.expected_change_per_litre_day + empirical,
            )
        )
    return tuple(out)


def _candidate_volumes(
    *,
    day: date,
    planning_end: date,
    tank: TankState,
    inventory: float,
    demand_lookup,
    required_buy: float,
    config: OperationalConfig,
) -> list[tuple[float, float]]:
    physical = max(
        0.0,
        tank.capacity_litres * config.max_fill_ratio - inventory,
    )
    candidates = {(round(min(required_buy, physical), 6), 0.0)}

    d = day
    cumulative = 0.0
    days = 0

    while d < planning_end:
        cumulative += demand_lookup.get(
            (tank.distributor_id, tank.product, d.weekday()),
            0.0,
        )
        days += 1
        buy = max(
            0.0,
            min(cumulative, tank.capacity_litres * config.max_fill_ratio)
            - inventory,
        )
        candidates.add((round(min(buy, physical), 6), float(days)))
        d += timedelta(days=1)

    candidates.add(
        (
            round(physical, 6),
            float((planning_end - day).days),
        )
    )

    cleaned = []
    for litres, cover in sorted(candidates):
        if 0 < litres < config.minimum_order_litres:
            litres = min(physical, config.minimum_order_litres)
        cleaned.append((litres, cover))

    unique = {round(x[0], 6): x for x in cleaned}
    return [unique[k] for k in sorted(unique)]


def evaluate_candidates(
    *,
    day: date,
    end: date,
    tank: TankState,
    inventory: float,
    current_price: float,
    required_buy: float,
    demand_lookup,
    signal: SignalAssessment,
    history: list[QuotationPoint],
    config: OperationalConfig,
) -> list[CandidateEvaluation]:
    planning_end = min(
        end + timedelta(days=1),
        day + timedelta(days=config.planning_horizon_days),
    )

    total_demand = demand_between(
        demand_lookup,
        tank.distributor_id,
        tank.product,
        day,
        planning_end,
    )

    scenarios = build_price_scenarios(history, signal)
    avg_wait_days = max(1.0, (planning_end - day).days / 2)
    out: list[CandidateEvaluation] = []

    for buy, cover_days in _candidate_volumes(
        day=day,
        planning_end=planning_end,
        tank=tank,
        inventory=inventory,
        demand_lookup=demand_lookup,
        required_buy=required_buy,
        config=config,
    ):
        future_need = max(0.0, total_demand - (inventory + buy))
        holding_days = max(0.0, cover_days) / 2

        purchase_cost = buy * current_price
        holding = (
            buy
            * config.holding_cost_eur_per_litre_day
            * holding_days
        )
        capital = (
            buy
            * current_price
            * config.working_capital_cost_rate_daily
            * holding_days
        )
        order = (
            (config.order_cost_eur if buy > 0 else 0.0)
            + (config.order_cost_eur if future_need > 0 else 0.0)
        )

        scenario_costs: list[float] = []
        expected_price = 0.0
        expected_future_cost = 0.0

        for scenario in scenarios:
            future_price = max(
                0.0,
                current_price
                + scenario.daily_change_eur_per_litre * avg_wait_days,
            )
            future_cost = future_need * future_price

            expected_price += scenario.probability * future_price
            expected_future_cost += scenario.probability * future_cost

            scenario_costs.append(
                purchase_cost
                + future_cost
                + holding
                + capital
                + order
            )

        expected_cost = sum(
            scenario.probability * scenario_cost
            for scenario, scenario_cost in zip(scenarios, scenario_costs)
        )

        downside = (
            max(scenario_costs) - expected_cost
            if scenario_costs
            else 0.0
        )
        robust_objective = (
            expected_cost
            + config.risk_aversion * downside
        )

        out.append(
            CandidateEvaluation(
                purchase_litres=buy,
                target_cover_days=cover_days,
                purchase_cost_eur=purchase_cost,
                expected_future_cost_eur=expected_future_cost,
                expected_cost_eur=expected_cost,
                downside_cost_eur=downside,
                holding_cost_eur=holding,
                capital_cost_eur=capital,
                order_cost_eur=order,
                robust_objective_eur=robust_objective,
                expected_future_price_eur_per_litre=expected_price,
                scenario_costs=tuple(scenario_costs),
            )
        )

    return out
