from __future__ import annotations
import json
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class LocalMarketConfig:
    lookback_days: int = 7
    macro_external_weight: float = 0.65
    local_market_weight: float = 0.35
    minimum_competitors: int = 2
    max_expected_change_eur_per_litre_day: float = 0.006
    retail_to_supplier_pass_through: float = 0.35
    disagreement_penalty: float = 0.10

    @classmethod
    def from_json(cls, path: str | Path) -> 'LocalMarketConfig':
        payload=json.loads(Path(path).read_text(encoding='utf-8'))
        return cls(**payload)
