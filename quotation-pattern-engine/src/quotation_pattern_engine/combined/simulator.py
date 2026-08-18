from __future__ import annotations

from collections import defaultdict
from dataclasses import replace
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from quotation_pattern_engine.external.config import ExternalConfig
from quotation_pattern_engine.external.models import (
    ExternalMarketObservation,
    ExternalNewsEvent,
)
from quotation_pattern_engine.external.signal import (
    build_external_signal,
)
from quotation_pattern_engine.operational.config import OperationalConfig
from quotation_pattern_engine.operational.models import (
    CandidateEvaluation,
    DailyLedgerRow,
    DemandProfile,
    PatternEvent,
    PatternSummary,
    QuotationPoint,
    TankState,
)
from quotation_pattern_engine.operational.optimizer import operational_required_buy
from quotation_pattern_engine.operational.signal_model import build_signal

from .config import CombinedConfig
from .models import CombinedPurchaseDecision
from .optimizer import (
    evaluate_combined_candidates,
    select_combined_candidate,
)
from .signal import combine_signals


ROME = ZoneInfo("Europe/Rome")


def _mark_candidate_trace(
    candidates: list[CandidateEvaluation],
    chosen: CandidateEvaluation,
    required: CandidateEvaluation,
) -> tuple[CandidateEvaluation, ...]:
    trace: list[CandidateEvaluation] = []

    for candidate in candidates:
        selected = candidate is chosen

        if selected and chosen is required:
            reason = (
                "Selected because it is the operational minimum "
                "after combined-signal decision gates."
            )
        elif selected:
            reason = (
                "Selected because it has the lowest admissible "
                "combined robust objective."
            )
        elif candidate is required:
            reason = (
                "Operational-minimum benchmark; feasible but not selected."
            )
        else:
            reason = (
                "Feasible candidate rejected because its combined "
                "robust objective is higher or it failed a decision gate."
            )

        trace.append(
            replace(
                candidate,
                selected=selected,
                selection_reason=reason,
            )
        )

    return tuple(trace)


def simulate_combined_strategy(
    tanks: list[TankState],
    demand_profiles: list[DemandProfile],
    quotations: list[QuotationPoint],
    events: list[PatternEvent],
    summaries: list[PatternSummary],
    external_market_observations: list[ExternalMarketObservation],
    external_news_events: list[ExternalNewsEvent],
    operational_config: OperationalConfig,
    external_config: ExternalConfig,
    combined_config: CombinedConfig,
) -> tuple[
    list[DailyLedgerRow],
    list[CombinedPurchaseDecision],
]:
    lookup = {
        (
            profile.distributor_id,
            profile.product,
            profile.weekday,
        ): profile.forecast_daily_litres
        for profile in demand_profiles
    }

    by_product: dict[
        str,
        list[QuotationPoint],
    ] = defaultdict(list)

    for quotation in quotations:
        by_product[quotation.product].append(
            quotation
        )

    for rows in by_product.values():
        rows.sort(key=lambda row: row.date)

    start = (
        date.fromisoformat(
            operational_config.simulation_start
        )
        if operational_config.simulation_start
        else min(row.date for row in quotations)
    )

    end = (
        date.fromisoformat(
            operational_config.simulation_end
        )
        if operational_config.simulation_end
        else max(row.date for row in quotations)
    )

    inventory = {
        (tank.distributor_id, tank.product): tank.opening_inventory_litres
        for tank in tanks
    }
    implicit_cost = {
        (tank.distributor_id, tank.product): tank.opening_implicit_cost_per_litre
        for tank in tanks
    }

    quotation_lookup = {
        (
            quotation.product,
            quotation.date,
        ): quotation
        for quotation in quotations
    }

    ledgers: list[DailyLedgerRow] = []
    decisions: list[CombinedPurchaseDecision] = []

    for day_index in range(
        (end - start).days + 1
    ):
        day = start + timedelta(
            days=day_index
        )

        cutoff = datetime.combine(
            day,
            time(
                hour=(
                    combined_config
                    .decision_cutoff_hour_local
                )
            ),
            tzinfo=ROME,
        )

        for tank in sorted(
            tanks,
            key=lambda row: (
                row.distributor_id,
                row.product,
            ),
        ):
            key = (
                tank.distributor_id,
                tank.product,
            )

            opening = inventory[key]
            opening_implicit = implicit_cost[key]

            demand = lookup.get(
                (
                    tank.distributor_id,
                    tank.product,
                    day.weekday(),
                ),
                0.0,
            )

            point = quotation_lookup.get(
                (
                    tank.product,
                    day,
                )
            )

            purchase = 0.0
            decision: CombinedPurchaseDecision | None = None

            if point is not None:
                quotation_dates = [
                    row.date
                    for row in by_product[tank.product]
                ]

                next_quotation = next(
                    (
                        quotation_date
                        for quotation_date
                        in quotation_dates
                        if quotation_date > day
                    ),
                    end + timedelta(days=1),
                )

                history = [
                    row
                    for row in by_product[tank.product]
                    if row.date <= day
                ]

                internal_signal = build_signal(
                    history,
                    events,
                    day,
                    operational_config,
                )

                external_signal = build_external_signal(
                    external_market_observations,
                    external_news_events,
                    tank.product,
                    day,
                    cutoff,
                    external_config,
                )

                combined_signal = combine_signals(
                    internal_signal,
                    external_signal,
                    combined_config,
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
                    config=operational_config,
                )

                candidate_trace: tuple[
                    CandidateEvaluation,
                    ...
                ] = ()

                candidates = evaluate_combined_candidates(
                    day=day,
                    end=end,
                    tank=tank,
                    inventory=opening,
                    current_price=(
                        point.price_per_litre
                    ),
                    required_buy=required_buy,
                    demand_lookup=lookup,
                    signal=combined_signal,
                    history=history,
                    operational_config=(
                        operational_config
                    ),
                    combined_config=combined_config,
                )

                (
                    chosen,
                    required,
                    reason,
                ) = select_combined_candidate(
                    candidates,
                    required_buy,
                    combined_signal,
                    combined_config,
                )

                purchase = max(
                    required_buy,
                    chosen.purchase_litres,
                )

                selected_cover = (
                    chosen.target_cover_days
                )
                chosen_cost = (
                    chosen.robust_objective_eur
                )
                required_cost = (
                    required.robust_objective_eur
                )
                downside = (
                    chosen.downside_cost_eur
                )

                candidate_trace = (
                    _mark_candidate_trace(
                        candidates,
                        chosen,
                        required,
                    )
                )

                purchase = min(
                    purchase,
                    max(
                        0.0,
                        tank.capacity_litres
                        * operational_config.max_fill_ratio
                        - opening,
                    ),
                )

                decision = CombinedPurchaseDecision(
                    date=day,
                    strategy="WIDGET_EXTERNAL",
                    distributor_id=(
                        tank.distributor_id
                    ),
                    product=tank.product,
                    quotation_eur_per_litre=(
                        point.price_per_litre
                    ),
                    inventory_before_litres=opening,
                    purchase_litres=purchase,
                    purchase_spend_eur=(
                        purchase
                        * point.price_per_litre
                        + (
                            operational_config.order_cost_eur
                            if purchase > 0
                            else 0.0
                        )
                    ),
                    selected_cover_days=(
                        selected_cover
                    ),
                    operational_required_litres=(
                        required_buy
                    ),
                    discretionary_litres=max(
                        0.0,
                        purchase - required_buy,
                    ),
                    internal_signal_score=(
                        combined_signal.internal_score
                    ),
                    internal_signal_confidence=(
                        combined_signal
                        .internal_confidence
                    ),
                    internal_expected_change_eur_per_litre_day=(
                        combined_signal
                        .internal_expected_change_per_litre_day
                    ),
                    external_signal_score=(
                        combined_signal.external_score
                    ),
                    external_signal_confidence=(
                        combined_signal
                        .external_confidence
                    ),
                    external_expected_change_eur_per_litre_day=(
                        combined_signal
                        .external_expected_change_per_litre_day
                    ),
                    combined_signal_score=(
                        combined_signal.score
                    ),
                    combined_signal_confidence=(
                        combined_signal.confidence
                    ),
                    combined_expected_change_eur_per_litre_day=(
                        combined_signal
                        .expected_change_per_litre_day
                    ),
                    combined_uncertainty_eur_per_litre_day=(
                        combined_signal
                        .uncertainty_eur_per_litre_day
                    ),
                    candidates_evaluated=len(
                        candidate_trace
                    ),
                    selected_expected_cost_eur=(
                        chosen_cost
                    ),
                    required_only_expected_cost_eur=(
                        required_cost
                    ),
                    expected_advantage_eur=(
                        required_cost - chosen_cost
                    ),
                    downside_cost_eur=downside,
                    patterns_used=" | ".join(
                        combined_signal.patterns
                    ),
                    external_drivers=" | ".join(
                        combined_signal.external_drivers
                    ),
                    external_themes=" | ".join(
                        combined_signal.external_themes
                    ),
                    caveats=" | ".join(
                        combined_signal.caveats
                    ),
                    reason=reason,
                    candidate_trace=candidate_trace,
                )

                decisions.append(decision)

            purchase_price = point.price_per_litre if point is not None and purchase > 0 else 0.0
            if purchase > 0:
                post_purchase_inventory = opening + purchase
                closing_implicit = (
                    (opening * opening_implicit + purchase * purchase_price)
                    / post_purchase_inventory
                    if post_purchase_inventory > 1e-9 else opening_implicit
                )
            else:
                closing_implicit = opening_implicit

            sold = min(
                demand,
                opening + purchase,
            )
            lost = max(
                0.0,
                demand - sold,
            )
            closing = (
                opening + purchase - sold
            )
            if closing < operational_config.hard_min_stock_litres - 0.05:
                raise ValueError(
                    f"Hard minimum stock breached for combined strategy "
                    f"{tank.distributor_id}/{tank.product} on {day}: "
                    f"{closing:.2f} L < "
                    f"{operational_config.hard_min_stock_litres:.2f} L"
                )
            inventory[key] = closing
            implicit_cost[key] = closing_implicit

            ledgers.append(
                DailyLedgerRow(
                    date=day,
                    strategy="WIDGET_EXTERNAL",
                    distributor_id=(
                        tank.distributor_id
                    ),
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
                    regime=(
                        point.regime
                        if point
                        else "No new quotation"
                    ),
                )
            )

    return ledgers, decisions
