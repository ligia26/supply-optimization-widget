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


def demand_for_lead_time(lookup, dist, prod, day, lead_days):
    if lead_days <= 0:
        return 0.0
    return demand_between(
        lookup,
        dist,
        prod,
        day,
        day + timedelta(days=lead_days),
    )


def reorder_point_litres(lookup, dist, prod, day, config: OperationalConfig) -> float:
    """Inventory level that should trigger a normal replenishment order.

    The 700 L floor is a hard physical constraint. The reorder point sits above
    it by the demand expected during the assumed delivery lead time.
    """
    return config.hard_min_stock_litres + demand_for_lead_time(
        lookup,
        dist,
        prod,
        day,
        config.delivery_lead_time_days,
    )


def _round_order_up(litres: float, increment: float) -> float:
    if litres <= 0:
        return 0.0
    return math.ceil((litres - 1e-9) / increment) * increment


def normalize_order_litres(
    litres: float,
    physical_headroom: float,
    config: OperationalConfig,
) -> float:
    """Apply minimum order and tanker-style rounding without exceeding headroom."""
    if litres <= 1e-9 or physical_headroom <= 1e-9:
        return 0.0

    target = max(litres, config.minimum_order_litres)
    target = _round_order_up(target, config.order_rounding_litres)

    # If the remaining headroom is smaller than the configured minimum order,
    # filling the remaining safe headroom is preferable to breaching capacity.
    return min(target, physical_headroom)


def operational_required_buy(
    *,
    lookup,
    tank: TankState,
    inventory: float,
    day: date,
    required_end: date,
    config: OperationalConfig,
) -> float:
    """Minimum feasible order that preserves the hard stock floor.

    The requirement covers demand through the next decision opportunity and
    leaves the confirmed hard minimum stock in the tank.
    """
    usable_capacity = tank.capacity_litres * config.max_fill_ratio
    physical_headroom = max(0.0, usable_capacity - inventory)
    demand_need = demand_between(
        lookup,
        tank.distributor_id,
        tank.product,
        day,
        required_end,
    )
    raw = max(0.0, config.hard_min_stock_litres + demand_need - inventory)
    return normalize_order_litres(raw, physical_headroom, config)


def baseline_replenishment_buy(
    *,
    lookup,
    tank: TankState,
    inventory: float,
    day: date,
    required_end: date,
    config: OperationalConfig,
) -> tuple[float, float]:
    """Reactive AS-IS policy: buy only the smallest standard chunk needed.

    The baseline has no price intelligence and does not deliberately exploit
    spare tank capacity. It triggers at the lead-time-aware reorder point or
    when the next decision opportunity would otherwise breach the 700 L floor.
    Once triggered, it buys the smallest feasible standard quantity: at least
    the configured 5,000 L MOQ, rounded upward to the configured increment.
    """
    usable_capacity = tank.capacity_litres * config.max_fill_ratio
    physical_headroom = max(0.0, usable_capacity - inventory)

    reorder_point = reorder_point_litres(
        lookup, tank.distributor_id, tank.product, day, config
    )
    demand_until_next = demand_between(
        lookup, tank.distributor_id, tank.product, day, required_end
    )
    floor_required = max(
        0.0,
        config.hard_min_stock_litres + demand_until_next - inventory,
    )
    must_order_for_floor = floor_required > 1e-9
    normal_reorder = inventory <= reorder_point + 1e-9

    if not (must_order_for_floor or normal_reorder):
        return 0.0, reorder_point

    # AS IS is intentionally reactive: it purchases only the smallest standard
    # delivery that protects operations, rather than refilling to a target %.
    raw = max(config.minimum_order_litres, floor_required)
    return normalize_order_litres(raw, physical_headroom, config), reorder_point


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
    usable_capacity = tank.capacity_litres * config.max_fill_ratio
    physical = max(0.0, usable_capacity - inventory)
    required = normalize_order_litres(required_buy, physical, config) if required_buy > 0 else 0.0
    candidates = {(round(required, 6), 0.0)}

    d = day
    cumulative = 0.0
    days = 0

    while d < planning_end:
        cumulative += demand_lookup.get(
            (tank.distributor_id, tank.product, d.weekday()),
            0.0,
        )
        days += 1
        raw_buy = max(
            0.0,
            config.hard_min_stock_litres + cumulative - inventory,
        )
        buy = normalize_order_litres(raw_buy, physical, config) if raw_buy > 0 else 0.0
        if buy + 1e-9 >= required:
            candidates.add((round(buy, 6), float(days)))
        d += timedelta(days=1)

    # CUEBIT can deliberately exploit spare capacity. Demand-cover candidates
    # represent progressively larger strategic buys; maximum usable fill is
    # included as the upper-bound candidate.
    max_buy = normalize_order_litres(physical, physical, config) if physical > 0 else 0.0
    if max_buy + 1e-9 >= required:
        candidates.add((round(max_buy, 6), float((planning_end - day).days)))

    unique = {round(x[0], 6): x for x in candidates}
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
        # The 700 L reserve is not available to cover normal forecast demand.
        usable_inventory_for_demand = max(
            0.0,
            inventory + buy - config.hard_min_stock_litres,
        )
        future_need = max(0.0, total_demand - usable_inventory_for_demand)
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
