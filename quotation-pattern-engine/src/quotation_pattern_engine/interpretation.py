from __future__ import annotations

import json
from typing import Any

from .models import PatternEvent


SYSTEM_PROMPT = """You are interpreting the output of a deterministic historical quotation pattern engine.

Rules:
1. Use only the supplied structured facts.
2. Do not recalculate metrics from raw quotations.
3. Do not invent external market causes.
4. Do not predict future prices.
5. Distinguish clearly between an observation and a possible operational implication.
6. Mention data limitations, especially short history, missing dates, revisions and sparse observations.
7. Preserve the price units supplied in the payload.

Return:
- Executive summary
- Product-by-product interpretation
- Important detected pattern events
- Possible procurement relevance
- Data limitations
"""


def build_payload(
    summaries: list[dict[str, Any]],
    events: list[PatternEvent],
    config: dict[str, Any],
) -> dict[str, Any]:
    return {
        "purpose": "Human interpretation of deterministic historical patterns",
        "guardrails": [
            "Metrics were calculated by code.",
            "The LLM must not discover patterns from raw prices.",
            "The LLM must not invent causes or forecasts.",
        ],
        "configuration": config,
        "series_summaries": [
            {
                key: value.isoformat() if hasattr(value, "isoformat") else value
                for key, value in summary.items()
            }
            for summary in summaries
        ],
        "important_pattern_events": [
            {
                key: value.isoformat() if hasattr(value, "isoformat") else value
                for key, value in event.to_dict().items()
            }
            for event in events
        ],
    }


def deterministic_interpretation(
    summaries: list[dict[str, Any]],
    events: list[PatternEvent],
) -> str:
    lines = ["# Historical Quotation Pattern Interpretation", ""]
    currency = "€"
    unit = "m³"

    for summary in summaries:
        net_change = summary["net_change"]
        start_price = summary["start_price"]
        end_price = summary["end_price"]
        if net_change > 0:
            direction = "increased"
        elif net_change < 0:
            direction = "decreased"
        else:
            direction = "did not change"

        percentage_change = (
        (net_change / start_price) * 100
        if start_price
        else 0.0
    )

        lines.extend([
            f"## {summary['supplier']} — {summary['product']}",
            "",
            (
                   f"Across {summary['observations']} canonical quotations from "
                f"{summary['period_start'].isoformat()} to "
                f"{summary['period_end'].isoformat()}, the quoted price "
                f"{direction} from "
                f"{currency}{start_price:,.2f}/{unit} to "
                f"{currency}{end_price:,.2f}/{unit}. "
                f"This represents a net change of "
                f"{net_change:+,.2f} {currency}/{unit} "
                f"({percentage_change:+.2f}%). "
                f"The observed volatility level was "
                f"{summary['volatility_level'].lower()}, with "
                f"{summary['reversals']} direction reversals."
            ),
            "",
            (
                f"The longest upward streak contained "
                f"{summary['longest_increase_streak']} consecutive increases, "
                f"while the longest downward streak contained "
                f"{summary['longest_decrease_streak']} consecutive decreases. "
                f"The latest detected regime was "
                f"{summary['current_regime'].lower()}."
            ),
            "",
        ])

        series_events = [
            event for event in events
            if event.supplier == summary["supplier"]
            and event.product == summary["product"]
        ]
        if series_events:
            lines.append("Detected events:")
            for event in series_events:
                lines.append(
                    f"- {event.pattern_type}, "
                    f"{event.start_date.isoformat()} to "
                    f"{event.end_date.isoformat()}: {event.evidence}."
                )
            lines.append("")

    lines.extend([
        "## Limitations",
        "",
        (
            "These results describe the supplied historical window only. "
            "They are not forecasts and do not incorporate inventory, sales, "
            "tank capacity, supplier lead times or external market events."
        ),
        "",
    ])
    return "\n".join(lines)
