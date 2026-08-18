from __future__ import annotations

from collections import defaultdict
from dataclasses import replace
from datetime import date, timedelta

from .config import OperationalConfig
from .models import *
from .optimizer import (
    baseline_replenishment_buy,
    evaluate_candidates,
    operational_required_buy,
    reorder_point_litres,
)
from .signal_model import build_signal


def _mark_candidate_trace(
    candidates: list[CandidateEvaluation],
    chosen: CandidateEvaluation,
    required: CandidateEvaluation,
) -> tuple[CandidateEvaluation, ...]:
    trace = []

    for candidate in candidates:
        selected = candidate is chosen

        if selected and chosen is required:
            reason = "Selected because it is the operational minimum."
        elif selected:
            reason = "Selected because it has the lowest robust objective."
        elif candidate is required:
            reason = "Operational-minimum benchmark; feasible but not selected."
        else:
            reason = "Feasible candidate rejected because its robust objective is higher."

        trace.append(
            replace(
                candidate,
                selected=selected,
                selection_reason=reason,
            )
        )

    return tuple(trace)


def simulate_strategy(
    strategy: str,
    tanks: list[TankState],
    demand_profiles: list[DemandProfile],
    quotations: list[QuotationPoint],
    events: list[PatternEvent],
    summaries: list[PatternSummary],
    config: OperationalConfig,
):
    if strategy not in {"AS_IS", "WIDGET"}:
        raise ValueError(strategy)

    lookup = {
        (x.distributor_id, x.product, x.weekday): x.forecast_daily_litres
        for x in demand_profiles
    }

    byp = defaultdict(list)
    for q in quotations:
        byp[q.product].append(q)
    for values in byp.values():
        values.sort(key=lambda x: x.date)

    start = (
        date.fromisoformat(config.simulation_start)
        if config.simulation_start
        else min(x.date for x in quotations)
    )
    end = (
        date.fromisoformat(config.simulation_end)
        if config.simulation_end
        else max(x.date for x in quotations)
    )

    inv = {
        (t.distributor_id, t.product): t.opening_inventory_litres
        for t in tanks
    }
    implicit_cost = {
        (t.distributor_id, t.product): t.opening_implicit_cost_per_litre
        for t in tanks
    }

    ledger: list[DailyLedgerRow] = []
    decisions: list[PurchaseDecision] = []
    qlookup = {(q.product, q.date): q for q in quotations}

    for day_i in range((end - start).days + 1):
        day = start + timedelta(days=day_i)

        for tank in sorted(
            tanks,
            key=lambda x: (x.distributor_id, x.product),
        ):
            key = (tank.distributor_id, tank.product)
            opening = inv[key]
            opening_implicit = implicit_cost[key]
            today = lookup.get(
                (tank.distributor_id, tank.product, day.weekday()),
                0.0,
            )

            point = qlookup.get((tank.product, day))
            purchase = 0.0
            decision = None

            if point is not None:
                quotation_dates = [x.date for x in byp[tank.product]]
                next_quotation = next(
                    (d for d in quotation_dates if d > day),
                    end + timedelta(days=1),
                )

                history = [
                    x for x in byp[tank.product]
                    if x.date <= day
                ]
                signal = build_signal(
                    history,
                    events,
                    day,
                    config,
                )

                required_end = min(
                    next_quotation,
                    end + timedelta(days=1),
                )
                required_buy = operational_required_buy(
                    lookup=lookup,
                    tank=tank,
                    inventory=opening,
                    day=day,
                    required_end=required_end,
                    config=config,
                )

                candidates: list[CandidateEvaluation] = []
                candidate_trace: tuple[CandidateEvaluation, ...] = ()
                required = None
                chosen = None

                if strategy == "AS_IS":
                    purchase, reorder_point = baseline_replenishment_buy(
                        lookup=lookup,
                        tank=tank,
                        inventory=opening,
                        day=day,
                        required_end=required_end,
                        config=config,
                    )
                    selected_cover_days = float((required_end - day).days)
                    reason = (
                        "Baseline replenishment: lead-time-aware reorder point "
                        f"{reorder_point:,.0f} L; smallest feasible standard order"
                        if purchase > 0
                        else "Baseline hold: inventory above reorder point and 700 L floor remains protected"
                    )
                    downside = 0.0

                else:
                    candidates = evaluate_candidates(
                        day=day,
                        end=end,
                        tank=tank,
                        inventory=opening,
                        current_price=point.price_per_litre,
                        required_buy=required_buy,
                        demand_lookup=lookup,
                        signal=signal,
                        history=history,
                        config=config,
                    )
                    required = min(
                        candidates,
                        key=lambda candidate: (
                            abs(candidate.purchase_litres - required_buy),
                            candidate.robust_objective_eur,
                        ),
                    )
                    chosen = min(
                        candidates,
                        key=lambda candidate: (
                            candidate.robust_objective_eur,
                            candidate.purchase_litres,
                        ),
                    )

                    adjusted_signal = signal.score * signal.confidence
                    discretionary_supported = (
                        signal.expected_change_per_litre_day > 0
                        and adjusted_signal >= config.discretionary_min_adjusted_signal
                        and signal.price_percentile <= config.discretionary_max_price_percentile
                    )
                    if (
                        chosen.purchase_litres > required.purchase_litres
                        and not discretionary_supported
                    ):
                        chosen = required

                    purchase = max(required_buy, chosen.purchase_litres)
                    selected_cover_days = chosen.target_cover_days
                    reason = (
                        "Operational minimum selected: discretionary evidence below threshold"
                        if chosen is required
                        else "Strategic advance purchase: strong low-price/rising-price evidence"
                    )
                    downside = chosen.downside_cost_eur
                    candidate_trace = _mark_candidate_trace(candidates, chosen, required)

                purchase = min(
                    purchase,
                    max(
                        0.0,
                        tank.capacity_litres
                        * config.max_fill_ratio
                        - opening,
                    ),
                )

                if strategy == "WIDGET":
                    chosen_cost = chosen.robust_objective_eur
                    required_cost = required.robust_objective_eur
                else:
                    chosen_cost = (
                        purchase * point.price_per_litre
                    )
                    required_cost = chosen_cost

                decision = PurchaseDecision(
                    date=day,
                    strategy=strategy,
                    distributor_id=tank.distributor_id,
                    product=tank.product,
                    quotation_eur_per_litre=point.price_per_litre,
                    inventory_before_litres=opening,
                    purchase_litres=purchase,
                    purchase_spend_eur=(
                        purchase * point.price_per_litre
                        + (
                            config.order_cost_eur
                            if purchase > 0
                            else 0.0
                        )
                    ),
                    selected_cover_days=selected_cover_days,
                    operational_required_litres=required_buy,
                    discretionary_litres=max(
                        0.0,
                        purchase - required_buy,
                    ),
                    signal_score=signal.score,
                    signal_confidence=signal.confidence,
                    expected_change_eur_per_litre_day=(
                        signal.expected_change_per_litre_day
                    ),
                    observed_price_percentile=(
                        signal.price_percentile
                    ),
                    candidates_evaluated=len(candidates),
                    selected_expected_cost_eur=chosen_cost,
                    required_only_expected_cost_eur=required_cost,
                    expected_advantage_eur=(
                        required_cost - chosen_cost
                    ),
                    downside_cost_eur=downside,
                    patterns_used=" | ".join(signal.patterns),
                    caveats=" | ".join(signal.caveats),
                    reason=reason,
                    candidate_trace=candidate_trace,
                )
                decisions.append(decision)

            purchase_price = point.price_per_litre if point is not None and purchase > 0 else 0.0
            if purchase > 0:
                inventory_value_before = opening * opening_implicit
                purchased_value = purchase * purchase_price
                post_purchase_inventory = opening + purchase
                closing_implicit = (
                    (inventory_value_before + purchased_value) / post_purchase_inventory
                    if post_purchase_inventory > 1e-9 else opening_implicit
                )
            else:
                closing_implicit = opening_implicit

            sold = min(today, opening + purchase)
            lost = max(0.0, today - sold)
            closing = opening + purchase - sold
            if closing < config.hard_min_stock_litres - 0.05:
                raise ValueError(
                    f"Hard minimum stock breached for {strategy} "
                    f"{tank.distributor_id}/{tank.product} on {day}: "
                    f"{closing:.2f} L < {config.hard_min_stock_litres:.2f} L"
                )
            inv[key] = closing
            implicit_cost[key] = closing_implicit

            regime = (
                point.regime
                if point
                else "No new quotation"
            )

            ledger.append(
                DailyLedgerRow(
                    date=day,
                    strategy=strategy,
                    distributor_id=tank.distributor_id,
                    product=tank.product,
                    opening_inventory_litres=opening,
                    opening_implicit_cost_per_litre=opening_implicit,
                    purchase_litres=purchase,
                    purchase_price_eur_per_litre=purchase_price,
                    purchase_total_eur=(
                        decision.purchase_spend_eur
                        if decision
                        else 0.0
                    ),
                    sales_litres=sold,
                    lost_sales_litres=lost,
                    closing_inventory_litres=closing,
                    closing_implicit_cost_per_litre=closing_implicit,
                    regime=regime,
                )
            )

    return ledger, decisions
