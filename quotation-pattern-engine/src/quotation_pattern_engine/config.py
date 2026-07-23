from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any


@dataclass
class ColumnMap:
    date: str = "date"
    product: str = "product"
    price: str = "price"
    supplier: str | None = "supplier"
    valid_from: str | None = "valid_from"
    valid_to: str | None = "valid_to"
    event_type: str | None = "event_type"
    source: str | None = "source"
    priority: str | None = "priority"


@dataclass
class EngineConfig:
    columns: ColumnMap = field(default_factory=ColumnMap)
    date_formats: list[str] = field(default_factory=lambda: [
        "%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"
    ])
    regulatory_event_types: list[str] = field(
    default_factory=lambda: [
        "regulatory update",
        "regulatory adjustment",
        "excise update",
        "tax adjustment",
    ]
)
    movement_epsilon: float = 0.0
    moving_average_window: int = 3
    volatility_window: int = 3
    regime_lookback: int = 2
    regime_threshold: float = 5.0
    minimum_streak_length: int = 2
    minimum_stable_length: int = 2
    stability_threshold: float = 0.5
    absolute_spike_floor: float = 15.0
    spike_std_multiplier: float = 1.0
    price_to_display_unit_divisor: float = 10.0
    volatility_low_max: float = 10.0
    volatility_medium_max: float = 25.0

    @classmethod
    def from_json(cls, path: str | Path) -> "EngineConfig":
        raw: dict[str, Any] = json.loads(Path(path).read_text(encoding="utf-8"))
        column_values = raw.pop("columns", {})
        return cls(columns=ColumnMap(**column_values), **raw)

    def to_dict(self) -> dict[str, Any]:
        result = self.__dict__.copy()
        result["columns"] = self.columns.__dict__.copy()
        return result

