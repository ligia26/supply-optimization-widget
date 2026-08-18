from __future__ import annotations

import csv
import json
from dataclasses import asdict
from pathlib import Path

from .config import OperationalConfig
from .loaders import (
    build_demand_profiles,
    load_daily_sales,
    load_growth_factors,
    load_pattern_events,
    load_pattern_summaries,
    load_quotation_points,
    load_tank_states,
)
from .models import CandidateEvaluation, DailyLedgerRow, PurchaseDecision, TankState
from .simulator import simulate_strategy
from quotation_pattern_engine.audit_workbook import write_simulation_audit_workbook


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return

    fieldnames: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row:
            if key not in seen:
                seen.add(key)
                fieldnames.append(key)

    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def build_comparison(
    ledgers: list[DailyLedgerRow],
    decisions: list[PurchaseDecision],
    tanks: list[TankState],
    quotations,
) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    terminal_price = {}
    for q in sorted(quotations, key=lambda row: row.date):
        terminal_price[q.product] = q.price_per_litre

    for tank in sorted(tanks, key=lambda row: (row.distributor_id, row.product)):
        metrics: dict[str, dict[str, float]] = {}

        for strategy in ("AS_IS", "WIDGET"):
            selected_decisions = [
                decision
                for decision in decisions
                if decision.strategy == strategy
                and decision.distributor_id == tank.distributor_id
                and decision.product == tank.product
            ]
            selected_ledgers = [
                row
                for row in ledgers
                if row.strategy == strategy
                and row.distributor_id == tank.distributor_id
                and row.product == tank.product
            ]

            spend = sum(decision.purchase_spend_eur for decision in selected_decisions)
            litres = sum(decision.purchase_litres for decision in selected_decisions)

            metrics[strategy] = {
                "spend": spend,
                "litres": litres,
                "orders": float(
                    sum(
                        1
                        for decision in selected_decisions
                        if decision.purchase_litres > 1e-9
                    )
                ),
                "closing": (
                    selected_ledgers[-1].closing_inventory_litres
                    if selected_ledgers
                    else tank.opening_inventory_litres
                ),
                "lost": sum(row.lost_sales_litres for row in selected_ledgers),
                "avg": spend / litres if litres else 0.0,
            }

        baseline = metrics["AS_IS"]
        widget = metrics["WIDGET"]

        valuation_price = terminal_price.get(tank.product, 0.0)
        baseline_inventory_value = baseline["closing"] * valuation_price
        widget_inventory_value = widget["closing"] * valuation_price
        baseline_economic_cost = baseline["spend"] - baseline_inventory_value
        widget_economic_cost = widget["spend"] - widget_inventory_value
        cash_saving = baseline["spend"] - widget["spend"]
        inventory_value_adjustment = baseline_inventory_value - widget_inventory_value
        saving = baseline_economic_cost - widget_economic_cost

        result.append(
            {
                "distributor_id": tank.distributor_id,
                "product": tank.product,
                "as_is_supplier_spend_eur": baseline["spend"],
                "cuebit_supplier_spend_eur": widget["spend"],
                "cash_saving_eur": cash_saving,
                "terminal_valuation_price_eur_per_litre": valuation_price,
                "as_is_ending_inventory_value_eur": baseline_inventory_value,
                "cuebit_ending_inventory_value_eur": widget_inventory_value,
                "ending_inventory_value_difference_eur": inventory_value_adjustment,
                "as_is_inventory_adjusted_economic_cost_eur": baseline_economic_cost,
                "cuebit_inventory_adjusted_economic_cost_eur": widget_economic_cost,
                "estimated_saving_eur": saving,
                "estimated_saving_percent": (
                    saving / baseline_economic_cost * 100
                    if baseline_economic_cost
                    else 0.0
                ),
                "as_is_litres_purchased": baseline["litres"],
                "cuebit_litres_purchased": widget["litres"],
                "as_is_average_purchase_price_eur_per_litre": baseline["avg"],
                "cuebit_average_purchase_price_eur_per_litre": widget["avg"],
                "as_is_orders": int(baseline["orders"]),
                "cuebit_orders": int(widget["orders"]),
                "as_is_closing_inventory_litres": baseline["closing"],
                "cuebit_closing_inventory_litres": widget["closing"],
                "as_is_lost_sales_litres": baseline["lost"],
                "cuebit_lost_sales_litres": widget["lost"],
            }
        )

    return result


def _purchase_rows(
    decisions: list[PurchaseDecision],
    distributor_id: str,
    product: str,
    strategy: str,
) -> list[PurchaseDecision]:
    return sorted(
        [
            decision
            for decision in decisions
            if decision.distributor_id == distributor_id
            and decision.product == product
            and decision.strategy == strategy
            and decision.purchase_litres > 1e-9
        ],
        key=lambda row: row.date,
    )


def _all_decision_rows(
    decisions: list[PurchaseDecision],
    distributor_id: str,
    product: str,
    strategy: str,
) -> list[PurchaseDecision]:
    return sorted(
        [
            decision
            for decision in decisions
            if decision.distributor_id == distributor_id
            and decision.product == product
            and decision.strategy == strategy
        ],
        key=lambda row: row.date,
    )


def _fmt_patterns(value: str) -> str:
    if not value.strip():
        return "No directional pattern evidence"
    return value.replace(" | ", "; ")


def _fmt_eur(value: float) -> str:
    return f"€{value:,.2f}"


def _fmt_litres(value: float) -> str:
    return f"{value:,.0f} L"


def _candidate_rows_for_export(
    decisions: list[PurchaseDecision],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []

    for decision in decisions:
        for candidate in decision.candidate_trace:
            rows.append(
                {
                    "date": decision.date.isoformat(),
                    "strategy": decision.strategy,
                    "distributor_id": decision.distributor_id,
                    "product": decision.product,
                    "quotation_eur_per_litre": decision.quotation_eur_per_litre,
                    "inventory_before_litres": decision.inventory_before_litres,
                    "operational_required_litres": (
                        decision.operational_required_litres
                    ),
                    "signal_score": decision.signal_score,
                    "signal_confidence": decision.signal_confidence,
                    "adjusted_signal": (
                        decision.signal_score * decision.signal_confidence
                    ),
                    "observed_price_percentile": (
                        decision.observed_price_percentile
                    ),
                    "patterns_used": decision.patterns_used,
                    "candidate_purchase_litres": candidate.purchase_litres,
                    "target_cover_days": candidate.target_cover_days,
                    "purchase_cost_eur": candidate.purchase_cost_eur,
                    "expected_future_cost_eur": (
                        candidate.expected_future_cost_eur
                    ),
                    "holding_cost_eur": candidate.holding_cost_eur,
                    "capital_cost_eur": candidate.capital_cost_eur,
                    "order_cost_eur": candidate.order_cost_eur,
                    "expected_cost_eur": candidate.expected_cost_eur,
                    "downside_cost_eur": candidate.downside_cost_eur,
                    "robust_objective_eur": (
                        candidate.robust_objective_eur
                    ),
                    "expected_future_price_eur_per_litre": (
                        candidate.expected_future_price_eur_per_litre
                    ),
                    "selected": candidate.selected,
                    "selection_reason": candidate.selection_reason,
                    "scenario_costs_eur": json.dumps(
                        list(candidate.scenario_costs)
                    ),
                }
            )

    return rows


def _purchase_decision_rows_for_export(
    decisions: list[PurchaseDecision],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []

    for decision in decisions:
        row = asdict(decision)
        row.pop("candidate_trace", None)
        rows.append(row)

    return rows


def _baseline_replacement_map(
    decision: PurchaseDecision,
    baseline_purchases: list[PurchaseDecision],
) -> list[tuple[PurchaseDecision, float]]:
    """
    Approximate FIFO allocation of discretionary litres bought by CUEBIT
    against later baseline purchases for the same distributor/product.

    This is an explanatory allocation only; it is not an optimiser input.
    """
    remaining = max(0.0, decision.discretionary_litres)
    mapped: list[tuple[PurchaseDecision, float]] = []

    if remaining <= 0.05:
        return mapped

    for baseline in baseline_purchases:
        if baseline.date <= decision.date:
            continue
        if baseline.reason == "Terminal inventory adjustment":
            continue
        if remaining <= 0.05:
            break

        allocated = min(remaining, baseline.purchase_litres)
        if allocated > 0.05:
            mapped.append((baseline, allocated))
            remaining -= allocated

    return mapped


def _write_baseline_summary(
    lines: list[str],
    baseline_purchases: list[PurchaseDecision],
) -> None:
    lines += [
        "### Operational baseline",
        "",
        "The baseline uses a lead-time-aware reorder point (700 L hard floor "
        "+ expected lead-time demand). When triggered, it buys only the smallest "
        "standard quantity needed to remain operational: at least 5,000 L, "
        "rounded to 1,000 L, subject to the 95% usable-fill cap. It has no "
        "price intelligence and does not deliberately fill spare capacity.",
        "",
        "| Date | Inventory before | Demand cover required | Purchase | Quotation |",
        "|---|---:|---:|---:|---:|",
    ]

    if not baseline_purchases:
        lines.append("| — | — | — | — | — |")
    else:
        for decision in baseline_purchases:
            lines.append(
                f"| {decision.date.isoformat()} | "
                f"{_fmt_litres(decision.inventory_before_litres)} | "
                f"{_fmt_litres(decision.operational_required_litres)} | "
                f"**{_fmt_litres(decision.purchase_litres)}** | "
                f"€{decision.quotation_eur_per_litre:,.5f}/L |"
            )

    lines.append("")


def _write_candidate_table(
    lines: list[str],
    trace: tuple[CandidateEvaluation, ...],
) -> None:
    lines += [
        "#### Candidates evaluated",
        "",
        "| Buy today | Cover | Purchase cost | Expected future cost | Holding | Capital | Orders | Downside | Robust objective | Result |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]

    for candidate in trace:
        result = "✅ Selected" if candidate.selected else "Rejected"
        lines.append(
            f"| {_fmt_litres(candidate.purchase_litres)} | "
            f"{candidate.target_cover_days:.0f} days | "
            f"{_fmt_eur(candidate.purchase_cost_eur)} | "
            f"{_fmt_eur(candidate.expected_future_cost_eur)} | "
            f"{_fmt_eur(candidate.holding_cost_eur)} | "
            f"{_fmt_eur(candidate.capital_cost_eur)} | "
            f"{_fmt_eur(candidate.order_cost_eur)} | "
            f"{_fmt_eur(candidate.downside_cost_eur)} | "
            f"**{_fmt_eur(candidate.robust_objective_eur)}** | "
            f"{result} |"
        )

    lines.append("")


def _write_replacement_mapping(
    lines: list[str],
    decision: PurchaseDecision,
    baseline_purchases: list[PurchaseDecision],
) -> None:
    mapping = _baseline_replacement_map(decision, baseline_purchases)

    if not mapping:
        return

    lines += [
        "#### Baseline purchases approximately brought forward",
        "",
        "The following FIFO allocation explains which later baseline litres "
        "the discretionary purchase can be interpreted as replacing. "
        "It is an audit explanation, not an additional optimiser calculation.",
        "",
        "| Later baseline date | Baseline quotation | Litres allocated |",
        "|---|---:|---:|",
    ]

    for baseline, litres in mapping:
        lines.append(
            f"| {baseline.date.isoformat()} | "
            f"€{baseline.quotation_eur_per_litre:,.5f}/L | "
            f"{_fmt_litres(litres)} |"
        )

    lines.append("")


def _write_decision_story(
    lines: list[str],
    decision: PurchaseDecision,
    baseline_purchases: list[PurchaseDecision],
) -> None:
    lines += [
        f"### Decision — {decision.date.isoformat()}",
        "",
        "| Input | Value |",
        "|---|---:|",
        f"| Current quotation | €{decision.quotation_eur_per_litre:,.5f}/L |",
        f"| Inventory before purchase | {_fmt_litres(decision.inventory_before_litres)} |",
        f"| Operational minimum | {_fmt_litres(decision.operational_required_litres)} |",
        f"| Available discretionary purchase selected | {_fmt_litres(decision.discretionary_litres)} |",
        f"| Total purchase selected | **{_fmt_litres(decision.purchase_litres)}** |",
        f"| Selected cover | {decision.selected_cover_days:.0f} days |",
        "",
        "#### Market evidence",
        "",
        f"- Patterns: {_fmt_patterns(decision.patterns_used)}.",
        f"- Signal score: {decision.signal_score:+.3f}.",
        f"- Confidence: {decision.signal_confidence:.3f}.",
        f"- Adjusted signal: "
        f"{decision.signal_score * decision.signal_confidence:+.3f}.",
        f"- Expected daily quotation change: "
        f"{decision.expected_change_eur_per_litre_day:+.5f} €/L.",
        f"- Observed price percentile: "
        f"{decision.observed_price_percentile:.0%}.",
        "",
    ]

    if decision.candidate_trace:
        _write_candidate_table(lines, decision.candidate_trace)

        selected = next(
            (
                candidate
                for candidate in decision.candidate_trace
                if candidate.selected
            ),
            None,
        )

        if selected is not None:
            lines += [
                "#### Why this candidate won",
                "",
                f"The optimiser selected **{_fmt_litres(selected.purchase_litres)}** "
                f"because its robust objective of "
                f"**{_fmt_eur(selected.robust_objective_eur)}** was the lowest "
                "among the feasible candidates after expected procurement, "
                "holding, working-capital, ordering and downside costs were included.",
                "",
            ]

            rejected = [
                candidate
                for candidate in decision.candidate_trace
                if not candidate.selected
            ]
            if rejected:
                next_best = min(
                    rejected,
                    key=lambda candidate: candidate.robust_objective_eur,
                )
                gap = (
                    next_best.robust_objective_eur
                    - selected.robust_objective_eur
                )
                lines += [
                    f"The next-best rejected candidate was "
                    f"**{_fmt_litres(next_best.purchase_litres)}** with a robust "
                    f"objective of **{_fmt_eur(next_best.robust_objective_eur)}**, "
                    f"which was **{_fmt_eur(gap)}** higher.",
                    "",
                ]
    else:
        lines += [
            "#### Decision rule",
            "",
            f"{decision.reason}. No candidate trace exists for this terminal "
            "equalisation or baseline-only decision.",
            "",
        ]

    _write_replacement_mapping(lines, decision, baseline_purchases)

    lines += [
        "#### Decision-level economic result",
        "",
        f"- Expected advantage versus the operational-minimum candidate: "
        f"**{_fmt_eur(decision.expected_advantage_eur)}**.",
        f"- Selected downside cost: "
        f"{_fmt_eur(decision.downside_cost_eur)}.",
        f"- Immediate supplier spend on this order: "
        f"{_fmt_eur(decision.purchase_spend_eur)}.",
        "",
    ]

    if decision.caveats.strip():
        lines += [
            "#### Caveats",
            "",
            f"{decision.caveats.replace(' | ', '; ')}.",
            "",
        ]


def _write_report(
    path: Path,
    rows: list[dict[str, object]],
    decisions: list[PurchaseDecision],
) -> None:
    baseline_spend = sum(
        float(row["as_is_supplier_spend_eur"])
        for row in rows
    )
    cuebit_spend = sum(
        float(row["cuebit_supplier_spend_eur"])
        for row in rows
    )
    saving = baseline_spend - cuebit_spend

    baseline_litres = sum(
        float(row["as_is_litres_purchased"])
        for row in rows
    )
    cuebit_litres = sum(
        float(row["cuebit_litres_purchased"])
        for row in rows
    )
    baseline_orders = sum(int(row["as_is_orders"]) for row in rows)
    cuebit_orders = sum(int(row["cuebit_orders"]) for row in rows)

    saving_percent = (
        saving / baseline_spend * 100
        if baseline_spend
        else 0.0
    )

    lines = [
        "# CUEBIT purchasing simulation — decision audit",
        "",
        "> Same demand and physical constraints; purchased litres and ending inventory may differ. "
        "The difference is when the fuel is purchased, how much is purchased "
        "on each quotation date and which quotation is paid.",
        "",
        "## Executive result",
        "",
        "| Metric | Operational baseline | CUEBIT | Difference |",
        "|---|---:|---:|---:|",
        f"| **Supplier spend** | **{_fmt_eur(baseline_spend)}** | "
        f"**{_fmt_eur(cuebit_spend)}** | "
        f"**{_fmt_eur(saving)} ({saving_percent:.2f}%)** |",
        f"| Litres purchased | {_fmt_litres(baseline_litres)} | "
        f"{_fmt_litres(cuebit_litres)} | "
        f"{_fmt_litres(baseline_litres - cuebit_litres)} |",
        f"| Purchase orders | {baseline_orders} | {cuebit_orders} | "
        f"{baseline_orders - cuebit_orders} |",
        "",
        "## How CUEBIT decides",
        "",
        "On every quotation date, CUEBIT first calculates the minimum volume "
        "required to remain operational. It then generates feasible purchase "
        "volumes between that minimum and the usable tank capacity.",
        "",
        "Each candidate is evaluated as:",
        "",
        "```text",
        "Immediate purchase cost",
        "+ expected future procurement cost",
        "+ holding cost",
        "+ working-capital cost",
        "+ order cost",
        "+ risk adjustment for downside scenarios",
        "= robust objective",
        "```",
        "",
        "The feasible candidate with the lowest robust objective is selected. "
        "The candidate tables below show the complete comparison used by the optimiser.",
        "",
        "## Result by distributor and product",
        "",
        "| Distributor | Product | Baseline spend | CUEBIT spend | Saving | Saving % | Baseline orders | CUEBIT orders |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]

    for row in rows:
        lines.append(
            f"| {row['distributor_id']} | {row['product']} | "
            f"{_fmt_eur(float(row['as_is_supplier_spend_eur']))} | "
            f"{_fmt_eur(float(row['cuebit_supplier_spend_eur']))} | "
            f"{_fmt_eur(float(row['estimated_saving_eur']))} | "
            f"{float(row['estimated_saving_percent']):.2f}% | "
            f"{int(row['as_is_orders'])} | "
            f"{int(row['cuebit_orders'])} |"
        )

    lines += ["", "## Decision audit by distributor and product", ""]

    for row in rows:
        distributor_id = str(row["distributor_id"])
        product = str(row["product"])

        baseline_purchases = _purchase_rows(
            decisions,
            distributor_id,
            product,
            "AS_IS",
        )
        widget_decisions = _all_decision_rows(
            decisions,
            distributor_id,
            product,
            "WIDGET",
        )
        widget_purchases = [
            decision
            for decision in widget_decisions
            if decision.purchase_litres > 1e-9
        ]

        lines += [
            f"# {distributor_id} — {product}",
            "",
            f"**Economic result:** "
            f"{_fmt_eur(float(row['estimated_saving_eur']))} saved "
            f"({float(row['estimated_saving_percent']):.2f}%).",
            "",
            f"**Average purchase price:** "
            f"€{float(row['as_is_average_purchase_price_eur_per_litre']):,.5f}/L "
            f"→ "
            f"€{float(row['cuebit_average_purchase_price_eur_per_litre']):,.5f}/L.",
            "",
            f"**Order count:** {int(row['as_is_orders'])} "
            f"→ {int(row['cuebit_orders'])}.",
            "",
        ]

        _write_baseline_summary(lines, baseline_purchases)

        lines += ["### CUEBIT decision stories", ""]

        non_terminal = [
            decision
            for decision in widget_purchases
            if decision.reason
            != "Terminal inventory adjustment"
        ]

        if non_terminal:
            for decision in non_terminal:
                _write_decision_story(
                    lines,
                    decision,
                    baseline_purchases,
                )
        else:
            lines += [
                "No non-terminal optimisation purchase was made for this "
                "distributor/product. The only purchase was the final "
                "stock-equalisation adjustment, so the simulation does not "
                "demonstrate a timing advantage for this case.",
                "",
            ]

        terminal = [
            decision
            for decision in widget_purchases
            if decision.reason
            == "Terminal inventory adjustment"
        ]
        if terminal:
            lines += [
                "<details>",
                "<summary>Final stock-equalisation adjustment</summary>",
                "",
            ]
            for decision in terminal:
                lines += [
                    f"- {decision.date.isoformat()}: "
                    f"{_fmt_litres(decision.purchase_litres)} at "
                    f"€{decision.quotation_eur_per_litre:,.5f}/L. "
                    "This technical adjustment makes both strategies finish "
                    "with the same inventory and is not treated as a normal "
                    "optimisation decision.",
                ]
            lines += ["", "</details>", ""]

    lines += [
        "## Validation boundary",
        "",
        "This is a historical simulation against a modelled operational "
        "baseline. Actual historical purchase orders, realised demand, "
        "delivery fees, lead times, minimum order rules, payment terms and "
        "other client-specific constraints are required before the estimated "
        "savings can be treated as realised client savings.",
        "",
        "The FIFO 'brought forward' mapping is explanatory only. The authoritative "
        "optimiser evidence is the candidate table and its robust-objective ranking.",
    ]

    path.write_text("\n".join(lines), encoding="utf-8")


def run_operational_simulation(
    serbatoi_path: str | Path,
    daily_sales_path: str | Path,
    monthly_sales_path: str | Path,
    daily_analysis_csv: str | Path,
    pattern_events_csv: str | Path,
    pattern_summary_csv: str | Path,
    output_dir: str | Path,
    config: OperationalConfig,
) -> dict[str, Path]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    tanks = load_tank_states(serbatoi_path, config)
    daily = load_daily_sales(daily_sales_path, config)
    growth = load_growth_factors(monthly_sales_path, config)
    demand_profiles = build_demand_profiles(daily, growth)
    quotations = load_quotation_points(daily_analysis_csv, config)
    events = load_pattern_events(pattern_events_csv, config)
    summaries = load_pattern_summaries(pattern_summary_csv, config)

    ledgers: list[DailyLedgerRow] = []
    decisions: list[PurchaseDecision] = []

    for strategy in ("AS_IS", "WIDGET"):
        strategy_ledgers, strategy_decisions = simulate_strategy(
            strategy,
            tanks,
            demand_profiles,
            quotations,
            events,
            summaries,
            config,
        )
        ledgers.extend(strategy_ledgers)
        decisions.extend(strategy_decisions)

    comparison = build_comparison(ledgers, decisions, tanks, quotations)

    paths = {
        "economic_report": output / "cuebit_economic_result.md",
        "economic_comparison": output / "cuebit_vs_as_is.csv",
        "purchase_decisions": output / "purchase_decisions.csv",
        "candidate_evaluations": output / "candidate_evaluations.csv",
        "daily_inventory_ledger": output / "daily_inventory_ledger.csv",
        "demand_profiles": output / "demand_profiles.csv",
        "tank_states": output / "tank_states.csv",
        "simulation_method": output / "simulation_method.json",
        "simulation_audit_workbook": output / "simulation_audit.xlsx",
    }

    _write_csv(paths["economic_comparison"], comparison)
    _write_csv(
        paths["purchase_decisions"],
        _purchase_decision_rows_for_export(decisions),
    )
    _write_csv(
        paths["candidate_evaluations"],
        _candidate_rows_for_export(decisions),
    )
    _write_csv(
        paths["daily_inventory_ledger"],
        [asdict(row) for row in ledgers],
    )
    _write_csv(
        paths["demand_profiles"],
        [
            asdict(row)
            | {"forecast_daily_litres": row.forecast_daily_litres}
            for row in demand_profiles
        ],
    )
    _write_csv(
        paths["tank_states"],
        [asdict(row) for row in tanks],
    )

    _write_report(
        paths["economic_report"],
        comparison,
        decisions,
    )

    write_simulation_audit_workbook(
        paths["simulation_audit_workbook"],
        ledgers=ledgers,
        decisions=decisions,
        comparison_rows=comparison,
        config=config,
        title="CUEBIT Operational — Simulation Audit",
    )

    paths["simulation_method"].write_text(
        json.dumps(
            {
                "engine": "causal common-horizon candidate optimiser",
                "pattern_inputs": [
                    "P01",
                    "P02",
                    "P03",
                    "P04",
                    "P05",
                    "P06",
                    "P07",
                ],
                "pattern_summary_usage": (
                    "Loaded for audit but excluded from causal decisions "
                    "because whole-period summaries would leak future data"
                ),
                "same_total_litres": False,
                "same_closing_inventory": False,
                "terminal_inventory_credit": True,
                "terminal_valuation_method": "last observed quotation by product",
                "decision_trace": (
                    "Every feasible WIDGET candidate is exported with its "
                    "purchase cost, expected future cost, holding cost, "
                    "working-capital cost, order cost, downside cost, robust "
                    "objective, selection status and rejection reason."
                ),
                "decision_report": (
                    "Decision-oriented audit with operational state, market "
                    "evidence, complete candidate rankings, selected volume, "
                    "next-best alternative, approximate later baseline "
                    "purchases brought forward and decision-level economics."
                ),
                "fact_boundary": (
                    "Costs use supplied configuration values. Zero values mean "
                    "the configured input is zero; they should not be interpreted "
                    "as proof that the real client cost is zero."
                ),
                "validation_warning": (
                    "Historical simulation against a modelled reference policy; "
                    "requires actual order history and unseen periods for validation."
                ),
                "config": asdict(config),
                "pattern_event_rows_loaded": len(events),
                "pattern_summary_rows_loaded": len(summaries),
                "candidate_evaluation_rows_exported": len(
                    _candidate_rows_for_export(decisions)
                ),
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    return paths
