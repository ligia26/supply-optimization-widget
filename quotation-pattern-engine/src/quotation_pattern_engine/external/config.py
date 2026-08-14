from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class ExternalConfig:
    """Configuration for external evidence only.

    Values are intentionally conservative until calibrated on more supplier
    quotation history. They are configuration, not hidden model constants.
    """

    min_component_confidence: float = 0.15
    max_data_age_days: int = 7
    market_lookback_days: int = 10
    news_theme_cap: float = 0.85
    news_eur_per_litre_day_scale: float = 0.004

    pass_through: dict[str, float] = field(default_factory=lambda: {
        "brent_spot_usd_per_barrel": 0.22,
        "eur_usd": -0.18,
        "ice_gasoil_continuous_usd_per_tonne": 0.55,
    })
    product_indicator_weights: dict[str, dict[str, float]] = field(default_factory=lambda: {
        "Diesel": {
            "brent_spot_usd_per_barrel": 0.55,
            "eur_usd": 0.35,
            "ice_gasoil_continuous_usd_per_tonne": 1.00,
        },
        "Verde": {
            "brent_spot_usd_per_barrel": 0.85,
            "eur_usd": 0.40,
            "ice_gasoil_continuous_usd_per_tonne": 0.10,
        },
    })
    market_scope_weights: dict[str, float] = field(default_factory=lambda: {
        "ITALY": 1.00,
        "MEDITERRANEAN": 0.95,
        "EUROPE": 0.90,
        "GLOBAL_EUROPE": 0.85,
        "GLOBAL": 0.75,
    })
    news_driver_weights: dict[str, float] = field(default_factory=lambda: {
        "Refining and supply": 1.00,
        "Refined product supply": 0.95,
        "Logistics": 0.90,
        "Supply": 0.85,
        "Geopolitics": 0.80,
        "Currency": 0.70,
        "Supply and demand": 0.65,
        "Market outlook": 0.40,
    })

    def __post_init__(self) -> None:
        if not 0 <= self.min_component_confidence <= 1:
            raise ValueError("min_component_confidence must be in [0, 1]")
        if self.max_data_age_days < 0 or self.market_lookback_days < 2:
            raise ValueError("invalid external lookback configuration")
        if self.news_eur_per_litre_day_scale < 0:
            raise ValueError("news_eur_per_litre_day_scale cannot be negative")

    @classmethod
    def from_json(cls, path: str | Path) -> "ExternalConfig":
        return cls(**json.loads(Path(path).read_text(encoding="utf-8")))
