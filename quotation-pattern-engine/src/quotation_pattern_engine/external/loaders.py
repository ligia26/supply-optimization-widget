from __future__ import annotations

import csv
from datetime import date, datetime
from pathlib import Path

from .models import ExternalMarketObservation, ExternalNewsEvent


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value.strip().replace("Z", "+00:00"))


def _products(value: str) -> tuple[str, ...]:
    return tuple(x.strip() for x in value.split(",") if x.strip())


def load_external_market_observations(path: str | Path) -> list[ExternalMarketObservation]:
    rows: list[ExternalMarketObservation] = []
    with Path(path).open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {
            "observation_date", "available_at", "indicator", "product_scope",
            "market_scope", "driver", "value", "unit", "source",
            "source_reliability", "quality_status",
        }
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Missing external market columns: {sorted(missing)}")
        for row in reader:
            rows.append(ExternalMarketObservation(
                observation_date=date.fromisoformat(row["observation_date"]),
                available_at=_dt(row["available_at"]),
                indicator=row["indicator"].strip(),
                product_scope=_products(row["product_scope"]),
                market_scope=row["market_scope"].strip(),
                driver=row["driver"].strip(),
                value=float(row["value"]),
                unit=row["unit"].strip(),
                source=row["source"].strip(),
                source_reliability=float(row["source_reliability"]),
                quality_status=row["quality_status"].strip(),
            ))
    return sorted(rows, key=lambda x: (x.available_at, x.indicator))


def load_external_news_events(path: str | Path) -> list[ExternalNewsEvent]:
    rows: list[ExternalNewsEvent] = []
    with Path(path).open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            rows.append(ExternalNewsEvent(
                event_id=row["event_id"].strip(),
                theme_id=row["theme_id"].strip(),
                published_at=_dt(row["published_at"]),
                available_at=_dt(row["available_at"]),
                event_start=date.fromisoformat(row["event_start"]),
                event_end=date.fromisoformat(row["event_end"]),
                expected_duration_days=int(row["expected_duration_days"]),
                event_type=row["event_type"].strip(),
                driver=row["driver"].strip(),
                market_scope=row["market_scope"].strip(),
                headline=row["headline"].strip(),
                supplier_relevance=float(row["supplier_relevance"]),
                expected_pass_through_days=int(row["expected_pass_through_days"]),
                diesel_direction=row["diesel_direction"].strip(),
                diesel_effect_strength=float(row["diesel_effect_strength"]),
                gasoline_direction=row["gasoline_direction"].strip(),
                gasoline_effect_strength=float(row["gasoline_effect_strength"]),
                source_reliability=float(row["source_reliability"]),
                interpretation_confidence=float(row["interpretation_confidence"]),
            ))
    return sorted(rows, key=lambda x: (x.available_at, x.event_id))
