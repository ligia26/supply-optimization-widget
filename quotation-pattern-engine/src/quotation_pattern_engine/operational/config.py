from __future__ import annotations
import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class OperationalConfig:
    quotation_price_divisor: float = 1000.0
    simulation_start: str | None = None
    simulation_end: str | None = None
    ignored_products: tuple[str, ...] = ("Performance",)

    # Operational replenishment assumptions (MVP, pending client confirmation
    # except hard_min_stock_litres, which is confirmed).
    hard_min_stock_litres: float = 700.0
    delivery_lead_time_days: int = 1
    max_fill_ratio: float = 0.95
    minimum_order_litres: float = 5000.0
    order_rounding_litres: float = 1000.0

    planning_horizon_days: int = 14

    # Discretionary buying guardrails. A larger-than-operational-minimum order
    # is allowed only when the causal price evidence is sufficiently strong
    # and today's observed quotation is not expensive relative to history.
    discretionary_min_adjusted_signal: float = 0.10
    discretionary_max_price_percentile: float = 0.60

    order_cost_eur: float = 0.0
    holding_cost_eur_per_litre_day: float = 0.0
    working_capital_cost_rate_daily: float = 0.0
    risk_aversion: float = 0.0
    max_pattern_age_days: int = 7
    missing_pattern_confidence: float = 0.50
    confidence_labels: dict[str, float] = field(default_factory=lambda: {
        "very high": .95, "high": .85, "medium": .65, "low": .45, "very low": .25,
    })
    pattern_weights: dict[str, float] = field(default_factory=lambda: {
        "P01": 1.0, "P02": 1.0, "P03": .6, "P04": .4, "P05": .8, "P06": 1.2, "P07": .9,
    })
    product_mapping: dict[str, str] = field(default_factory=lambda: {"Verde":"Benzina Synergy","Diesel":"Gasolio Synergy"})
    distributor_mapping: dict[str, str] = field(default_factory=lambda: {
        "MG 368318":"368318","MG340 368319":"368319","Scoglio del Tonno 368320":"368320","Virgilio 368321":"368321","Dante":"368322",
    })
    monthly_name_mapping: dict[str, str] = field(default_factory=lambda: {
        "taras":"368318","lorenzo":"368319","scoglio":"368320","virgilio":"368321","dante":"368322",
    })

    def __post_init__(self) -> None:
        if self.planning_horizon_days < 1:
            raise ValueError("planning_horizon_days must be >= 1")
        if self.delivery_lead_time_days < 0:
            raise ValueError("delivery_lead_time_days must be >= 0")
        if self.hard_min_stock_litres < 0:
            raise ValueError("hard_min_stock_litres cannot be negative")
        if not 0 < self.max_fill_ratio <= 1:
            raise ValueError("max_fill_ratio must be in (0, 1]")
        if self.order_rounding_litres <= 0:
            raise ValueError("order_rounding_litres must be > 0")
        if not -1 <= self.discretionary_min_adjusted_signal <= 1:
            raise ValueError("discretionary_min_adjusted_signal must be in [-1, 1]")
        if not 0 <= self.discretionary_max_price_percentile <= 1:
            raise ValueError("discretionary_max_price_percentile must be in [0, 1]")
        for name in (
            "minimum_order_litres", "order_cost_eur",
            "holding_cost_eur_per_litre_day", "working_capital_cost_rate_daily",
            "risk_aversion",
        ):
            if getattr(self, name) < 0:
                raise ValueError(f"{name} cannot be negative")

    @classmethod
    def from_json(cls, path: str | Path) -> "OperationalConfig":
        payload = json.loads(Path(path).read_text())
        if "ignored_products" in payload:
            payload["ignored_products"] = tuple(payload["ignored_products"])
        # Backward compatibility with older config versions.
        payload.pop("candidate_cover_days", None)
        payload.pop("safety_days", None)
        return cls(**payload)
