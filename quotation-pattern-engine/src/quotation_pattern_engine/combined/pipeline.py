from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from quotation_pattern_engine.external.config import ExternalConfig
from quotation_pattern_engine.external.loaders import (
    load_external_market_observations,
    load_external_news_events,
)
from quotation_pattern_engine.operational.config import OperationalConfig
from quotation_pattern_engine.operational.loaders import (
    build_demand_profiles,
    load_daily_sales,
    load_growth_factors,
    load_pattern_events,
    load_pattern_summaries,
    load_quotation_points,
    load_tank_states,
)
from quotation_pattern_engine.operational.simulator import simulate_strategy

from .config import CombinedConfig
from .reporting import (
    build_candidate_rows,
    build_side_by_side_decisions,
    build_strategy_comparison,
    dataclass_row,
    portfolio_summary,
    write_csv,
    write_markdown_report,
)
from .simulator import simulate_combined_strategy


def run_combined_simulation(
    serbatoi_path: str | Path,
    daily_sales_path: str | Path,
    monthly_sales_path: str | Path,
    daily_analysis_csv: str | Path,
    pattern_events_csv: str | Path,
    pattern_summary_csv: str | Path,
    external_market_csv: str | Path,
    external_news_csv: str | Path,
    output_dir: str | Path,
    operational_config: OperationalConfig,
    external_config: ExternalConfig,
    combined_config: CombinedConfig,
) -> dict[str, Path]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    tanks = load_tank_states(serbatoi_path, operational_config)
    daily = load_daily_sales(daily_sales_path, operational_config)
    growth = load_growth_factors(monthly_sales_path, operational_config)
    demand_profiles = build_demand_profiles(daily, growth)
    quotations = load_quotation_points(daily_analysis_csv, operational_config)
    events = load_pattern_events(pattern_events_csv, operational_config)
    summaries = load_pattern_summaries(pattern_summary_csv, operational_config)
    market = load_external_market_observations(external_market_csv)
    news = load_external_news_events(external_news_csv)

    operational_ledgers = []
    operational_decisions = []
    for strategy in ("AS_IS", "WIDGET"):
        strategy_ledgers, strategy_decisions = simulate_strategy(
            strategy,
            tanks,
            demand_profiles,
            quotations,
            events,
            summaries,
            operational_config,
        )
        operational_ledgers.extend(strategy_ledgers)
        operational_decisions.extend(strategy_decisions)

    combined_ledgers, combined_decisions = simulate_combined_strategy(
        tanks,
        demand_profiles,
        quotations,
        events,
        summaries,
        market,
        news,
        operational_config,
        external_config,
        combined_config,
    )

    comparison_rows = build_strategy_comparison(
        tanks=tanks,
        operational_ledgers=operational_ledgers,
        operational_decisions=operational_decisions,
        combined_ledgers=combined_ledgers,
        combined_decisions=combined_decisions,
    )
    side_by_side_rows = build_side_by_side_decisions(
        operational_decisions,
        combined_decisions,
    )
    candidate_rows = build_candidate_rows(combined_decisions)
    summary = portfolio_summary(comparison_rows, combined_decisions)

    paths = {
        "economic_report": output / "cuebit_combined_economic_result.md",
        "strategy_comparison": output / "cuebit_combined_vs_as_is.csv",
        "portfolio_summary": output / "portfolio_summary_external.json",
        "buying_decisions": output / "buying_decisions_side_by_side.csv",
        "purchase_decisions_external": output / "purchase_decisions_external.csv",
        "candidate_evaluations_external": output / "candidate_evaluations_external.csv",
        "daily_inventory_external": output / "daily_inventory_external.csv",
        "simulation_method_external": output / "simulation_method_external.json",
    }

    write_csv(paths["strategy_comparison"], comparison_rows)
    write_csv(paths["buying_decisions"], side_by_side_rows)
    write_csv(
        paths["purchase_decisions_external"],
        [
            dataclass_row(decision, exclude=("candidate_trace",))
            for decision in combined_decisions
        ],
    )
    write_csv(paths["candidate_evaluations_external"], candidate_rows)
    write_csv(
        paths["daily_inventory_external"],
        [dataclass_row(row) for row in combined_ledgers],
    )

    write_markdown_report(
        paths["economic_report"],
        summary=summary,
        comparison_rows=comparison_rows,
        side_by_side_rows=side_by_side_rows,
    )

    paths["portfolio_summary"].write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    paths["simulation_method_external"].write_text(
        json.dumps({
            "strategy": "WIDGET_EXTERNAL",
            "comparison_strategies": ["AS_IS", "WIDGET", "WIDGET_EXTERNAL"],
            "formula": (
                "robust objective = immediate purchase + probability-weighted "
                "future purchase + holding + working capital + order costs + "
                "confidence-adjusted downside"
            ),
            "historical_saving_definition": (
                "supplier-spend difference between strategies; clean like-for-like "
                "only when equal litres, equal closing inventory and no additional "
                "lost sales checks pass"
            ),
            "expected_advantage_definition": (
                "ex-ante candidate objective improvement used for decision selection; "
                "not added to historical supplier-spend saving"
            ),
            "causal_rule": (
                "only internal and external observations available at or before "
                "the decision cutoff are used"
            ),
            "external_market_rows": len(market),
            "external_news_rows": len(news),
            "pattern_event_rows": len(events),
            "pattern_summary_rows": len(summaries),
            "comparison_validation": {
                "same_total_litres_as_is_vs_combined": summary[
                    "same_total_litres_as_is_vs_combined"
                ],
                "same_closing_inventory_as_is_vs_combined": summary[
                    "same_closing_inventory_as_is_vs_combined"
                ],
                "no_additional_lost_sales_vs_as_is": summary[
                    "no_additional_lost_sales_vs_as_is"
                ],
                "comparison_is_like_for_like": summary[
                    "comparison_is_like_for_like"
                ],
            },
            "warning": (
                "Historical simulation against a modelled reference policy. "
                "Pass-through coefficients, news annotations and candidate scenarios "
                "require calibration on more supplier quotation history and validation "
                "against actual orders."
            ),
            "operational_config": asdict(operational_config),
            "external_config": asdict(external_config),
            "combined_config": asdict(combined_config),
        }, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    return paths
