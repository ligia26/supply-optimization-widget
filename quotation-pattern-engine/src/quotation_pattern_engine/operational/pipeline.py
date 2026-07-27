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
from .models import DailyLedgerRow, PurchaseDecision, TankState
from .simulator import simulate_strategy


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def build_comparison(ledgers: list[DailyLedgerRow], decisions: list[PurchaseDecision], tanks: list[TankState]) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    for tank in sorted(tanks, key=lambda row: (row.distributor_id, row.product)):
        metrics: dict[str, dict[str, float]] = {}
        for strategy in ("AS_IS", "WIDGET"):
            selected_decisions = [d for d in decisions if d.strategy == strategy and d.distributor_id == tank.distributor_id and d.product == tank.product]
            selected_ledgers = [l for l in ledgers if l.strategy == strategy and l.distributor_id == tank.distributor_id and l.product == tank.product]
            spend = sum(d.purchase_spend_eur for d in selected_decisions)
            litres = sum(d.purchase_litres for d in selected_decisions)
            metrics[strategy] = {
                "spend": spend,
                "litres": litres,
                "orders": sum(1 for d in selected_decisions if d.purchase_litres > 1e-9),
                "closing": selected_ledgers[-1].closing_inventory_litres if selected_ledgers else tank.opening_inventory_litres,
                "lost": sum(l.lost_sales_litres for l in selected_ledgers),
                "avg": spend / litres if litres else 0.0,
            }

        current, widget = metrics["AS_IS"], metrics["WIDGET"]
        if abs(current["closing"] - widget["closing"]) > 0.05:
            raise ValueError(f"Closing inventory mismatch for {tank.distributor_id}/{tank.product}")
        if abs(current["litres"] - widget["litres"]) > 0.05:
            raise ValueError(f"Purchased-volume mismatch for {tank.distributor_id}/{tank.product}")
        saving = current["spend"] - widget["spend"]
        result.append({
            "distributor_id": tank.distributor_id,
            "product": tank.product,
            "as_is_supplier_spend_eur": current["spend"],
            "cuebit_supplier_spend_eur": widget["spend"],
            "estimated_saving_eur": saving,
            "estimated_saving_percent": saving / current["spend"] * 100 if current["spend"] else 0.0,
            "as_is_litres_purchased": current["litres"],
            "cuebit_litres_purchased": widget["litres"],
            "as_is_average_purchase_price_eur_per_litre": current["avg"],
            "cuebit_average_purchase_price_eur_per_litre": widget["avg"],
            "as_is_orders": int(current["orders"]),
            "cuebit_orders": int(widget["orders"]),
            "as_is_closing_inventory_litres": current["closing"],
            "cuebit_closing_inventory_litres": widget["closing"],
            "as_is_lost_sales_litres": current["lost"],
            "cuebit_lost_sales_litres": widget["lost"],
        })
    return result


def _write_report(path: Path, rows: list[dict[str, object]]) -> None:
    current = sum(float(row["as_is_supplier_spend_eur"]) for row in rows)
    cuebit = sum(float(row["cuebit_supplier_spend_eur"]) for row in rows)
    saving = current - cuebit
    current_litres = sum(float(row["as_is_litres_purchased"]) for row in rows)
    cuebit_litres = sum(float(row["cuebit_litres_purchased"]) for row in rows)
    current_orders = sum(int(row["as_is_orders"]) for row in rows)
    cuebit_orders = sum(int(row["cuebit_orders"]) for row in rows)
    lines = [
        "# CUEBIT purchasing simulation — fact-based candidate optimisation",
        "",
        "> The strategies serve the same demand, buy the same total litres and finish with the same physical inventory. No terminal inventory credit is used.",
        "",
        "## Headline result",
        "",
        "| Metric | Current reference policy | CUEBIT | Difference |",
        "|---|---:|---:|---:|",
        f"| **Supplier spend** | **€{current:,.2f}** | **€{cuebit:,.2f}** | **€{saving:,.2f} ({saving/current*100 if current else 0:.2f}%)** |",
        f"| Litres purchased | {current_litres:,.0f} L | {cuebit_litres:,.0f} L | {current_litres-cuebit_litres:,.0f} L |",
        f"| Purchase orders | {current_orders} | {cuebit_orders} | {current_orders-cuebit_orders} |",
        "",
        "## Result by distributor and product",
        "",
        "| Distributor | Product | Current spend | CUEBIT spend | Saving | Saving % |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(f"| {row['distributor_id']} | {row['product']} | €{float(row['as_is_supplier_spend_eur']):,.2f} | €{float(row['cuebit_supplier_spend_eur']):,.2f} | €{float(row['estimated_saving_eur']):,.2f} | {float(row['estimated_saving_percent']):.2f}% |")
    lines += [
        "",
        "## How decisions are made",
        "",
        "CUEBIT evaluates multiple acquisition volumes on each real quotation date. Every candidate is compared over the same planning horizon using only information observable on that date: P01 regime, P02 streaks, P03 stable-premium evidence, P04 multi-day quotation status, P05 reversals/revisions, P06 regulatory updates, P07 spikes and causal price position, plus pattern confidence and operational tank/demand constraints. Unknown delivery fees and holding costs remain explicit zero-value inputs rather than invented facts.",
        "",
        "## Validation warning",
        "",
        "The result is a historical simulation against a transparent reference policy, not verified realised savings. Actual order history, delivery fees, lead times, payment terms and June–July 2026 realised sales were not supplied. Pattern confidence is used as detection evidence and is not represented as validated predictive probability.",
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
        strategy_ledgers, strategy_decisions = simulate_strategy(strategy, tanks, demand_profiles, quotations, events, summaries, config)
        ledgers.extend(strategy_ledgers)
        decisions.extend(strategy_decisions)

    comparison = build_comparison(ledgers, decisions, tanks)
    paths = {
        "economic_report": output / "cuebit_economic_result.md",
        "economic_comparison": output / "cuebit_vs_as_is.csv",
        "purchase_decisions": output / "purchase_decisions.csv",
        "daily_inventory_ledger": output / "daily_inventory_ledger.csv",
        "demand_profiles": output / "demand_profiles.csv",
        "tank_states": output / "tank_states.csv",
        "simulation_method": output / "simulation_method.json",
    }
    _write_csv(paths["economic_comparison"], comparison)
    _write_csv(paths["purchase_decisions"], [asdict(row) for row in decisions])
    _write_csv(paths["daily_inventory_ledger"], [asdict(row) for row in ledgers])
    _write_csv(paths["demand_profiles"], [asdict(row) | {"forecast_daily_litres": row.forecast_daily_litres} for row in demand_profiles])
    _write_csv(paths["tank_states"], [asdict(row) for row in tanks])
    _write_report(paths["economic_report"], comparison)
    paths["simulation_method"].write_text(json.dumps({
        "engine": "causal common-horizon candidate optimiser",
        "pattern_inputs": ["P01", "P02", "P03", "P04", "P05", "P06", "P07"],
        "pattern_summary_usage": "loaded for audit but excluded from causal decisions because whole-period summaries would leak future data",
        "same_total_litres": True,
        "same_closing_inventory": True,
        "terminal_inventory_credit": False,
        "fact_boundary": "No delivery fee, holding cost, minimum order or lead time is invented. Zero values mean unavailable client inputs, not known zero economic cost.",
        "validation_warning": "Historical simulation against a modelled reference policy; requires actual order history and unseen periods for validation.",
        "config": asdict(config),
        "pattern_event_rows_loaded": len(events),
        "pattern_summary_rows_loaded": len(summaries),
    }, indent=2), encoding="utf-8")
    return paths
