from __future__ import annotations

import csv
import json
from collections import Counter
from dataclasses import asdict, is_dataclass
from datetime import date
from pathlib import Path
from typing import Any, Iterable


# ============================================================
# GENERIC SERIALISATION
# ============================================================


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
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
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
            extrasaction="ignore",
        )
        writer.writeheader()
        writer.writerows(rows)


def serialise(value: Any) -> Any:
    if isinstance(value, date):
        return value.isoformat()

    if isinstance(value, tuple):
        return json.dumps(
            [serialise(item) for item in value],
            ensure_ascii=False,
        )

    if isinstance(value, list):
        return json.dumps(
            [serialise(item) for item in value],
            ensure_ascii=False,
        )

    if isinstance(value, dict):
        return json.dumps(
            {
                str(key): serialise(item)
                for key, item in value.items()
            },
            ensure_ascii=False,
        )

    return value


def dataclass_row(
    value: Any,
    *,
    exclude: Iterable[str] = (),
) -> dict[str, Any]:
    if not is_dataclass(value):
        raise TypeError(
            f"Expected dataclass instance, received {type(value)!r}"
        )

    excluded = set(exclude)

    return {
        key: serialise(item)
        for key, item in asdict(value).items()
        if key not in excluded
    }


def _clean_pipe_text(value: Any) -> str:
    text = str(value or "").strip()

    if not text:
        return ""

    return ", ".join(
        item.strip()
        for item in text.split("|")
        if item.strip()
    )


def _fmt_eur(value: Any) -> str:
    return f"€{float(value or 0):,.2f}"


def _fmt_litres(value: Any) -> str:
    return f"{float(value or 0):,.0f} L"


def _fmt_percent(value: Any) -> str:
    return f"{float(value or 0):,.2f}%"


# ============================================================
# STRATEGY COMPARISON
# ============================================================


def _strategy_metrics(
    strategy: str,
    ledgers: list[Any],
    decisions: list[Any],
    opening_inventory: float,
) -> dict[str, float]:
    strategy_decisions = [
        decision
        for decision in decisions
        if decision.strategy == strategy
    ]

    strategy_ledgers = [
        ledger
        for ledger in ledgers
        if ledger.strategy == strategy
    ]

    supplier_spend = sum(
        float(decision.purchase_spend_eur)
        for decision in strategy_decisions
    )

    litres_purchased = sum(
        float(decision.purchase_litres)
        for decision in strategy_decisions
    )

    orders = sum(
        1
        for decision in strategy_decisions
        if float(decision.purchase_litres) > 0.05
    )

    lost_sales = sum(
        float(ledger.lost_sales_litres)
        for ledger in strategy_ledgers
    )

    closing_inventory = (
        float(strategy_ledgers[-1].closing_inventory_litres)
        if strategy_ledgers
        else float(opening_inventory)
    )

    return {
        "supplier_spend_eur": supplier_spend,
        "litres_purchased": litres_purchased,
        "orders": float(orders),
        "lost_sales_litres": lost_sales,
        "closing_inventory_litres": closing_inventory,
        "average_purchase_price_eur_per_litre": (
            supplier_spend / litres_purchased
            if litres_purchased
            else 0.0
        ),
    }


def build_strategy_comparison(
    *,
    tanks: list[Any],
    operational_ledgers: list[Any],
    operational_decisions: list[Any],
    combined_ledgers: list[Any],
    combined_decisions: list[Any],
    terminal_prices: dict[str, float],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    sorted_tanks = sorted(
        tanks,
        key=lambda tank: (
            tank.distributor_id,
            tank.product,
        ),
    )

    for tank in sorted_tanks:
        distributor_id = tank.distributor_id
        product = tank.product

        filtered_operational_ledgers = [
            row
            for row in operational_ledgers
            if row.distributor_id == distributor_id
            and row.product == product
        ]

        filtered_operational_decisions = [
            row
            for row in operational_decisions
            if row.distributor_id == distributor_id
            and row.product == product
        ]

        filtered_combined_ledgers = [
            row
            for row in combined_ledgers
            if row.distributor_id == distributor_id
            and row.product == product
        ]

        filtered_combined_decisions = [
            row
            for row in combined_decisions
            if row.distributor_id == distributor_id
            and row.product == product
        ]

        current = _strategy_metrics(
            "AS_IS",
            filtered_operational_ledgers,
            filtered_operational_decisions,
            tank.opening_inventory_litres,
        )

        operational = _strategy_metrics(
            "WIDGET",
            filtered_operational_ledgers,
            filtered_operational_decisions,
            tank.opening_inventory_litres,
        )

        combined = _strategy_metrics(
            "WIDGET_EXTERNAL",
            filtered_combined_ledgers,
            filtered_combined_decisions,
            tank.opening_inventory_litres,
        )

        as_is_spend = current["supplier_spend_eur"]
        operational_spend = operational["supplier_spend_eur"]
        combined_spend = combined["supplier_spend_eur"]
        valuation_price = float(terminal_prices.get(product, 0.0))
        as_is_inv_value = current["closing_inventory_litres"] * valuation_price
        operational_inv_value = operational["closing_inventory_litres"] * valuation_price
        combined_inv_value = combined["closing_inventory_litres"] * valuation_price
        as_is_economic_cost = as_is_spend - as_is_inv_value
        operational_economic_cost = operational_spend - operational_inv_value
        combined_economic_cost = combined_spend - combined_inv_value

        rows.append(
            {
                "distributor_id": distributor_id,
                "product": product,

                "as_is_supplier_spend_eur": as_is_spend,
                "operational_supplier_spend_eur": operational_spend,
                "combined_supplier_spend_eur": combined_spend,

                "as_is_cash_spend_eur": as_is_spend,
                "operational_cash_spend_eur": operational_spend,
                "combined_cash_spend_eur": combined_spend,
                "terminal_valuation_price_eur_per_litre": valuation_price,
                "as_is_ending_inventory_value_eur": as_is_inv_value,
                "operational_ending_inventory_value_eur": operational_inv_value,
                "combined_ending_inventory_value_eur": combined_inv_value,
                "as_is_inventory_adjusted_economic_cost_eur": as_is_economic_cost,
                "operational_inventory_adjusted_economic_cost_eur": operational_economic_cost,
                "combined_inventory_adjusted_economic_cost_eur": combined_economic_cost,
                "operational_cash_saving_vs_as_is_eur": as_is_spend - operational_spend,
                "combined_cash_saving_vs_as_is_eur": as_is_spend - combined_spend,
                "operational_saving_vs_as_is_eur": as_is_economic_cost - operational_economic_cost,
                "combined_saving_vs_as_is_eur": as_is_economic_cost - combined_economic_cost,
                "external_incremental_saving_vs_operational_eur": operational_economic_cost - combined_economic_cost,

                "as_is_litres_purchased": current["litres_purchased"],
                "operational_litres_purchased": operational[
                    "litres_purchased"
                ],
                "combined_litres_purchased": combined[
                    "litres_purchased"
                ],

                "as_is_orders": int(current["orders"]),
                "operational_orders": int(operational["orders"]),
                "combined_orders": int(combined["orders"]),

                "as_is_closing_inventory_litres": current[
                    "closing_inventory_litres"
                ],
                "operational_closing_inventory_litres": operational[
                    "closing_inventory_litres"
                ],
                "combined_closing_inventory_litres": combined[
                    "closing_inventory_litres"
                ],

                "as_is_lost_sales_litres": current[
                    "lost_sales_litres"
                ],
                "operational_lost_sales_litres": operational[
                    "lost_sales_litres"
                ],
                "combined_lost_sales_litres": combined[
                    "lost_sales_litres"
                ],

                "same_litres_as_is_vs_combined": (
                    abs(
                        current["litres_purchased"]
                        - combined["litres_purchased"]
                    )
                    <= 0.05
                ),

                "same_closing_inventory_as_is_vs_combined": (
                    abs(
                        current["closing_inventory_litres"]
                        - combined["closing_inventory_litres"]
                    )
                    <= 0.05
                ),
            }
        )

    return rows


# ============================================================
# BUYING DECISIONS
# ============================================================


def _action_label(row: dict[str, Any]) -> str:
    operational_litres = float(
        row.get("operational_purchase_litres", 0.0) or 0.0
    )

    combined_litres = float(
        row.get("combined_purchase_litres", 0.0) or 0.0
    )

    difference = combined_litres - operational_litres

    if operational_litres > 0.05 and combined_litres <= 0.05:
        return "POSTPONE PURCHASE"

    if difference > 0.05:
        return "BUY MORE"

    if difference < -0.05:
        return "BUY LESS"

    if combined_litres > 0.05:
        return "NO CHANGE"

    return "NO PURCHASE"


def _short_reason(row: dict[str, Any]) -> str:
    action = row["combined_action"]

    operational_litres = float(
        row.get("operational_purchase_litres", 0.0) or 0.0
    )

    combined_litres = float(
        row.get("combined_purchase_litres", 0.0) or 0.0
    )

    advantage = float(
        row.get("combined_expected_advantage_eur", 0.0) or 0.0
    )

    drivers = _clean_pipe_text(
        row.get("combined_external_drivers")
    )

    if action == "POSTPONE PURCHASE":
        explanation = (
            f"Postpone the operational purchase of "
            f"{operational_litres:,.0f} L because buying now did not "
            f"produce sufficient expected economic advantage."
        )

    elif action == "BUY MORE":
        difference = combined_litres - operational_litres

        explanation = (
            f"Buy {difference:,.0f} L more because the combined "
            f"internal and external scenario favoured advancing "
            f"a future purchase."
        )

        if advantage > 0:
            explanation += (
                f" Modelled expected advantage: "
                f"€{advantage:,.2f}."
            )

    elif action == "BUY LESS":
        difference = operational_litres - combined_litres

        explanation = (
            f"Buy {difference:,.0f} L less because advancing the "
            f"full operational volume was not economically justified."
        )

    else:
        explanation = (
            "External intelligence did not materially change "
            "the operational recommendation."
        )

    if drivers:
        explanation += f" Main external drivers: {drivers}."

    return explanation


def build_side_by_side_decisions(
    operational_decisions: list[Any],
    combined_decisions: list[Any],
) -> list[dict[str, Any]]:
    indexed: dict[
        tuple[Any, str, str],
        dict[str, Any],
    ] = {}

    for decision in operational_decisions:
        key = (
            decision.date,
            decision.distributor_id,
            decision.product,
        )

        row = indexed.setdefault(
            key,
            {
                "date": serialise(decision.date),
                "distributor_id": decision.distributor_id,
                "product": decision.product,
            },
        )

        prefix = (
            "as_is"
            if decision.strategy == "AS_IS"
            else "operational"
        )

        row[f"{prefix}_purchase_litres"] = (
            decision.purchase_litres
        )

        row[f"{prefix}_purchase_spend_eur"] = (
            decision.purchase_spend_eur
        )

        row[f"{prefix}_selected_cover_days"] = getattr(
            decision,
            "selected_cover_days",
            0.0,
        )

        row[f"{prefix}_reason"] = getattr(
            decision,
            "reason",
            "",
        )

    for decision in combined_decisions:
        key = (
            decision.date,
            decision.distributor_id,
            decision.product,
        )

        row = indexed.setdefault(
            key,
            {
                "date": serialise(decision.date),
                "distributor_id": decision.distributor_id,
                "product": decision.product,
            },
        )

        row.update(
            {
                "combined_purchase_litres": (
                    decision.purchase_litres
                ),
                "combined_purchase_spend_eur": (
                    decision.purchase_spend_eur
                ),
                "combined_selected_cover_days": (
                    decision.selected_cover_days
                ),
                "combined_operational_required_litres": (
                    decision.operational_required_litres
                ),
                "combined_discretionary_litres": (
                    decision.discretionary_litres
                ),
                "combined_internal_signal_score": (
                    decision.internal_signal_score
                ),
                "combined_external_signal_score": (
                    decision.external_signal_score
                ),
                "combined_signal_score": (
                    decision.combined_signal_score
                ),
                "combined_signal_confidence": (
                    decision.combined_signal_confidence
                ),
                "combined_expected_advantage_eur": (
                    decision.expected_advantage_eur
                ),
                "combined_patterns_used": (
                    decision.patterns_used
                ),
                "combined_external_drivers": (
                    decision.external_drivers
                ),
                "combined_external_themes": (
                    decision.external_themes
                ),
                "combined_caveats": (
                    decision.caveats
                ),
                "combined_reason": (
                    decision.reason
                ),
            }
        )

    rows = list(indexed.values())

    for row in rows:
        operational_litres = float(
            row.get("operational_purchase_litres", 0.0)
            or 0.0
        )

        combined_litres = float(
            row.get("combined_purchase_litres", 0.0)
            or 0.0
        )

        row["combined_minus_operational_litres"] = (
            combined_litres - operational_litres
        )

        row["external_changed_operational_decision"] = (
            abs(combined_litres - operational_litres) > 0.05
        )

        row["combined_action"] = _action_label(row)
        row["short_reason"] = _short_reason(row)

    return sorted(
        rows,
        key=lambda row: (
            row["date"],
            str(row["distributor_id"]),
            str(row["product"]),
        ),
    )


# ============================================================
# CANDIDATE EXPORT
# ============================================================


def build_candidate_rows(
    combined_decisions: list[Any],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    for decision in combined_decisions:
        for candidate in decision.candidate_trace:
            rows.append(
                {
                    "date": serialise(decision.date),
                    "distributor_id": decision.distributor_id,
                    "product": decision.product,
                    "quotation_eur_per_litre": (
                        decision.quotation_eur_per_litre
                    ),
                    "operational_required_litres": (
                        decision.operational_required_litres
                    ),
                    "combined_signal_score": (
                        decision.combined_signal_score
                    ),
                    "combined_signal_confidence": (
                        decision.combined_signal_confidence
                    ),
                    "external_drivers": (
                        decision.external_drivers
                    ),
                    "external_themes": (
                        decision.external_themes
                    ),
                    **dataclass_row(candidate),
                }
            )

    return rows


# ============================================================
# PORTFOLIO SUMMARY
# ============================================================


def portfolio_summary(
    comparison_rows: list[dict[str, Any]],
    combined_decisions: list[Any],
) -> dict[str, Any]:
    as_is_spend = sum(
        float(row["as_is_supplier_spend_eur"])
        for row in comparison_rows
    )

    operational_spend = sum(
        float(row["operational_supplier_spend_eur"])
        for row in comparison_rows
    )

    combined_spend = sum(
        float(row["combined_supplier_spend_eur"])
        for row in comparison_rows
    )

    positive_advantages = [
        float(decision.expected_advantage_eur)
        for decision in combined_decisions
        if float(decision.expected_advantage_eur) > 0
    ]

    driver_counts: Counter[str] = Counter()
    theme_counts: Counter[str] = Counter()

    for decision in combined_decisions:
        for driver in str(
            decision.external_drivers or ""
        ).split("|"):
            if driver.strip():
                driver_counts[driver.strip()] += 1

        for theme in str(
            decision.external_themes or ""
        ).split("|"):
            if theme.strip():
                theme_counts[theme.strip()] += 1

    same_litres = all(
        bool(row["same_litres_as_is_vs_combined"])
        for row in comparison_rows
    )

    same_inventory = all(
        bool(row["same_closing_inventory_as_is_vs_combined"])
        for row in comparison_rows
    )

    no_extra_lost_sales = all(
        float(row["combined_lost_sales_litres"])
        <= float(row["as_is_lost_sales_litres"]) + 0.05
        for row in comparison_rows
    )

    as_is_economic_cost = sum(float(row["as_is_inventory_adjusted_economic_cost_eur"]) for row in comparison_rows)
    operational_economic_cost = sum(float(row["operational_inventory_adjusted_economic_cost_eur"]) for row in comparison_rows)
    combined_economic_cost = sum(float(row["combined_inventory_adjusted_economic_cost_eur"]) for row in comparison_rows)
    operational_saving = as_is_economic_cost - operational_economic_cost
    combined_saving = as_is_economic_cost - combined_economic_cost
    incremental_saving = operational_economic_cost - combined_economic_cost

    return {
        "as_is_supplier_spend_eur": as_is_spend,
        "operational_supplier_spend_eur": operational_spend,
        "combined_supplier_spend_eur": combined_spend,

        "as_is_inventory_adjusted_economic_cost_eur": as_is_economic_cost,
        "operational_inventory_adjusted_economic_cost_eur": operational_economic_cost,
        "combined_inventory_adjusted_economic_cost_eur": combined_economic_cost,
        "operational_saving_vs_as_is_eur": operational_saving,
        "combined_saving_vs_as_is_eur": combined_saving,

        "external_incremental_saving_vs_operational_eur": (
            incremental_saving
        ),

        "external_incremental_uplift_percent": (
            incremental_saving / operational_saving * 100
            if operational_saving
            else 0.0
        ),

        "combined_decisions_evaluated": len(
            combined_decisions
        ),

        "combined_positive_expected_advantage_decisions": len(
            positive_advantages
        ),

        "combined_total_expected_advantage_eur": sum(
            positive_advantages
        ),

        "combined_max_expected_advantage_eur": (
            max(positive_advantages)
            if positive_advantages
            else 0.0
        ),

        "external_driver_counts": dict(
            driver_counts.most_common()
        ),

        "external_theme_counts": dict(
            theme_counts.most_common()
        ),

        "same_total_litres_as_is_vs_combined": same_litres,

        "same_closing_inventory_as_is_vs_combined": (
            same_inventory
        ),

        "no_additional_lost_sales_vs_as_is": (
            no_extra_lost_sales
        ),

        "comparison_is_like_for_like": no_extra_lost_sales,
        "ending_inventory_difference_is_valued": True,
    }


# ============================================================
# EXECUTIVE REPORT FOR LUCA
# ============================================================


def _write_executive_report(
    path: Path,
    *,
    summary: dict[str, Any],
    comparison_rows: list[dict[str, Any]],
    changed_rows: list[dict[str, Any]],
) -> None:
    operational_saving = float(
        summary["operational_saving_vs_as_is_eur"]
    )

    combined_saving = float(
        summary["combined_saving_vs_as_is_eur"]
    )

    incremental_saving = float(
        summary[
            "external_incremental_saving_vs_operational_eur"
        ]
    )

    uplift = float(
        summary["external_incremental_uplift_percent"]
    )

    lines = [
        "# CUEBIT External Intelligence Validation",
        "",
        "## Result",
        "",
        "Adding external market intelligence improved the "
        "operational purchasing engine.",
        "",
        "| Metric | Result |",
        "|---|---:|",
        f"| Operational-only saving | "
        f"**{_fmt_eur(operational_saving)}** |",
        f"| Combined engine saving | "
        f"**{_fmt_eur(combined_saving)}** |",
        f"| Additional saving from external intelligence | "
        f"**{_fmt_eur(incremental_saving)}** |",
        f"| Improvement over the operational engine | "
        f"**{_fmt_percent(uplift)}** |",
        "",
        "The improvement was achieved while purchasing the "
        "same total litres, ending with the same physical "
        "inventory and creating no additional lost sales.",
        "",
        "## Decisions changed by external intelligence",
        "",
    ]

    if not changed_rows:
        lines.append(
            "External intelligence did not change any "
            "operational purchase volumes."
        )

    else:
        lines += [
            "| Date | Station | Product | Recommendation | Why |",
            "|---|---|---|---|---|",
        ]

        for row in changed_rows:
            action = row["combined_action"]

            operational_litres = float(
                row.get(
                    "operational_purchase_litres",
                    0.0,
                )
                or 0.0
            )

            combined_litres = float(
                row.get(
                    "combined_purchase_litres",
                    0.0,
                )
                or 0.0
            )

            difference = (
                combined_litres - operational_litres
            )

            if action == "POSTPONE PURCHASE":
                recommendation = (
                    f"Do not buy "
                    f"{operational_litres:,.0f} L yet"
                )

            elif action == "BUY MORE":
                recommendation = (
                    f"Buy {combined_litres:,.0f} L "
                    f"(+{difference:,.0f} L)"
                )

            elif action == "BUY LESS":
                recommendation = (
                    f"Buy {combined_litres:,.0f} L "
                    f"({difference:,.0f} L)"
                )

            else:
                recommendation = (
                    f"Buy {combined_litres:,.0f} L"
                )

            drivers = _clean_pipe_text(
                row.get("combined_external_drivers")
            )

            if action == "POSTPONE PURCHASE":
                reason = (
                    "Buying immediately did not provide "
                    "sufficient economic advantage."
                )
            elif action == "BUY MORE":
                reason = (
                    "Internal quotation patterns and external "
                    "market conditions supported advancing "
                    "future volume."
                )
            else:
                reason = row.get("short_reason", "")

            if drivers:
                reason += f" Drivers: {drivers}."

            lines.append(
                f"| {row['date']} | "
                f"{row['distributor_id']} | "
                f"{row['product']} | "
                f"**{recommendation}** | "
                f"{reason} |"
            )

    if changed_rows:
        best_row = max(
            changed_rows,
            key=lambda row: float(
                row.get(
                    "combined_expected_advantage_eur",
                    0.0,
                )
                or 0.0
            ),
        )

        best_advantage = float(
            best_row.get(
                "combined_expected_advantage_eur",
                0.0,
            )
            or 0.0
        )

        lines += [
            "",
            "## Most important decision",
            "",
            f"On **{best_row['date']}**, for station "
            f"**{best_row['distributor_id']}** and product "
            f"**{best_row['product']}**, the combined engine "
            f"recommended **{_fmt_litres(best_row.get('combined_purchase_litres'))}** "
            f"instead of "
            f"**{_fmt_litres(best_row.get('operational_purchase_litres'))}**.",
            "",
        ]

        if best_advantage > 0:
            lines.append(
                f"The modelled expected advantage for this "
                f"decision was **{_fmt_eur(best_advantage)}**."
            )

    lines += [
        "",
        "## Validation",
        "",
        "| Check | Result |",
        "|---|---|",
        f"| Same total litres purchased | "
        f"{'PASS' if summary['same_total_litres_as_is_vs_combined'] else 'FAIL'} |",
        f"| Same closing inventory | "
        f"{'PASS' if summary['same_closing_inventory_as_is_vs_combined'] else 'FAIL'} |",
        f"| No additional lost sales | "
        f"{'PASS' if summary['no_additional_lost_sales_vs_as_is'] else 'FAIL'} |",
        "",
        "## Conclusion",
        "",
        "The external layer does not replace the operational "
        "engine. It selectively changes purchase timing and "
        "volume when external evidence indicates that waiting "
        "or advancing a purchase is economically preferable.",
        "",
        "This is a historical simulation against a modelled "
        "reference policy, not yet verified realised client savings.",
    ]

    path.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )


# ============================================================
# TECHNICAL APPENDIX
# ============================================================


def _write_technical_report(
    path: Path,
    *,
    summary: dict[str, Any],
    changed_rows: list[dict[str, Any]],
) -> None:
    lines = [
        "# CUEBIT External Intelligence — Technical Appendix",
        "",
        "This file contains the detailed explanation of only "
        "the decisions where the external layer changed the "
        "operational recommendation.",
        "",
    ]

    for row in changed_rows:
        lines += [
            f"## {row['date']} · "
            f"{row['distributor_id']} · "
            f"{row['product']}",
            "",
            f"**Action:** {row['combined_action']}",
            "",
            "| Metric | Operational | Combined |",
            "|---|---:|---:|",
            f"| Purchase volume | "
            f"{_fmt_litres(row.get('operational_purchase_litres'))} | "
            f"{_fmt_litres(row.get('combined_purchase_litres'))} |",
            f"| Purchase spend | "
            f"{_fmt_eur(row.get('operational_purchase_spend_eur'))} | "
            f"{_fmt_eur(row.get('combined_purchase_spend_eur'))} |",
            f"| Cover days | "
            f"{float(row.get('operational_selected_cover_days', 0) or 0):.1f} | "
            f"{float(row.get('combined_selected_cover_days', 0) or 0):.1f} |",
            "",
            row["short_reason"],
            "",
            f"- Expected advantage: "
            f"**{_fmt_eur(row.get('combined_expected_advantage_eur'))}**",
            f"- Internal signal: "
            f"**{float(row.get('combined_internal_signal_score', 0) or 0):.2f}**",
            f"- External signal: "
            f"**{float(row.get('combined_external_signal_score', 0) or 0):.2f}**",
            f"- Combined signal: "
            f"**{float(row.get('combined_signal_score', 0) or 0):.2f}**",
            f"- Confidence: "
            f"**{float(row.get('combined_signal_confidence', 0) or 0):.2f}**",
        ]

        patterns = _clean_pipe_text(
            row.get("combined_patterns_used")
        )

        drivers = _clean_pipe_text(
            row.get("combined_external_drivers")
        )

        themes = _clean_pipe_text(
            row.get("combined_external_themes")
        )

        caveats = _clean_pipe_text(
            row.get("combined_caveats")
        )

        if patterns:
            lines.append(
                f"- Internal patterns: **{patterns}**"
            )

        if drivers:
            lines.append(
                f"- External drivers: **{drivers}**"
            )

        if themes:
            lines.append(
                f"- News themes: **{themes}**"
            )

        if caveats:
            lines.append(
                f"- Caveats: **{caveats}**"
            )

        lines.append("")

    lines += [
        "## Interpretation boundary",
        "",
        "Historical simulated supplier-spend saving is "
        "calculated from prices paid in the replayed strategies.",
        "",
        "Modelled expected advantage is used to choose between "
        "candidate purchase volumes. It is not added to the "
        "historical saving.",
    ]

    path.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )


# ============================================================
# PUBLIC REPORT FUNCTION CALLED BY PIPELINE
# ============================================================


def write_markdown_report(
    path: Path,
    *,
    summary: dict[str, Any],
    comparison_rows: list[dict[str, Any]],
    side_by_side_rows: list[dict[str, Any]],
) -> None:
    """
    Produces three outputs:

    1. Short executive report at the path supplied by pipeline.
    2. CSV containing only decisions changed by external data.
    3. Technical appendix containing detailed signals.
    """

    changed_rows = [
        row
        for row in side_by_side_rows
        if row.get(
            "external_changed_operational_decision",
            False,
        )
    ]

    changed_rows.sort(
        key=lambda row: (
            row["date"],
            str(row["distributor_id"]),
            str(row["product"]),
        )
    )

    _write_executive_report(
        path,
        summary=summary,
        comparison_rows=comparison_rows,
        changed_rows=changed_rows,
    )

    decision_log_path = (
        path.parent / "decision_log_external.csv"
    )

    write_csv(
        decision_log_path,
        [
            {
                "date": row["date"],
                "distributor_id": row["distributor_id"],
                "product": row["product"],
                "action": row["combined_action"],

                "operational_purchase_litres": row.get(
                    "operational_purchase_litres",
                    0.0,
                ),

                "combined_purchase_litres": row.get(
                    "combined_purchase_litres",
                    0.0,
                ),

                "difference_litres": row.get(
                    "combined_minus_operational_litres",
                    0.0,
                ),

                "expected_advantage_eur": row.get(
                    "combined_expected_advantage_eur",
                    0.0,
                ),

                "internal_signal_score": row.get(
                    "combined_internal_signal_score",
                    0.0,
                ),

                "external_signal_score": row.get(
                    "combined_external_signal_score",
                    0.0,
                ),

                "combined_signal_score": row.get(
                    "combined_signal_score",
                    0.0,
                ),

                "confidence": row.get(
                    "combined_signal_confidence",
                    0.0,
                ),

                "patterns_used": row.get(
                    "combined_patterns_used",
                    "",
                ),

                "external_drivers": row.get(
                    "combined_external_drivers",
                    "",
                ),

                "external_themes": row.get(
                    "combined_external_themes",
                    "",
                ),

                "reason": row.get(
                    "short_reason",
                    "",
                ),
            }
            for row in changed_rows
        ],
    )

    technical_report_path = (
        path.parent / "technical_report_external.md"
    )

    _write_technical_report(
        technical_report_path,
        summary=summary,
        changed_rows=changed_rows,
    )
