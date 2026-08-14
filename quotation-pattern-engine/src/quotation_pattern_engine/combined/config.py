from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CombinedConfig:
    internal_weight: float = 0.55
    external_weight: float = 0.45
    agreement_bonus: float = 0.10
    disagreement_penalty: float = 0.20
    scenario_uncertainty_multiplier: float = 1.25
    min_objective_improvement_eur: float = 5.0
    min_objective_improvement_ratio: float = 0.0005
    min_combined_confidence_for_discretionary_buy: float = 0.20
    decision_cutoff_hour_local: int = 8

    def __post_init__(self) -> None:
        if self.internal_weight < 0 or self.external_weight < 0:
            raise ValueError("signal weights cannot be negative")
        if self.internal_weight + self.external_weight <= 0:
            raise ValueError("at least one signal weight must be positive")
        if not 0 <= self.min_combined_confidence_for_discretionary_buy <= 1:
            raise ValueError("minimum confidence must be in [0, 1]")

    @classmethod
    def from_json(cls, path: str | Path) -> "CombinedConfig":
        return cls(**json.loads(Path(path).read_text(encoding="utf-8")))
