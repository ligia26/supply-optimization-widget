from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .config import EngineConfig
from .engine import PatternEngine
from .interpretation import (
    SYSTEM_PROMPT,
    build_payload,
    deterministic_interpretation,
)
from .io import read_quotations, canonicalize, write_csv


def _serialize_dict(row: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value.isoformat() if hasattr(value, "isoformat") else value
        for key, value in row.items()
    }


def run_pipeline(
    input_path: str | Path,
    output_dir: str | Path,
    config: EngineConfig,
) -> dict[str, Path]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    raw = read_quotations(input_path, config)
    canonical = canonicalize(raw)

    engine = PatternEngine(config)
    daily, summaries, events = engine.analyze(canonical)

    canonical_rows = [
        {
            "date": item.date,
            "supplier": item.supplier,
            "product": item.product,
            "price": item.price,
            "valid_from": item.valid_from,
            "valid_to": item.valid_to,
            "event_type": item.event_type,
            "source": item.source,
            "priority": item.priority,
        }
        for item in canonical
    ]
    daily_rows = [item.to_dict() for item in daily]
    event_rows = [item.to_dict() for item in events]

    paths = {
        "canonical": output / "canonical_quotations.csv",
        "daily": output / "daily_analysis.csv",
        "summary": output / "pattern_summary.csv",
        "events": output / "pattern_events.csv",
        "payload": output / "llm_payload.json",
        "prompt": output / "interpretation_prompt.txt",
        "interpretation": output / "deterministic_interpretation.md",
    }

    write_csv(paths["canonical"], canonical_rows)
    write_csv(paths["daily"], daily_rows)
    write_csv(paths["summary"], summaries)
    write_csv(paths["events"], event_rows)

    payload = build_payload(summaries, events, config.to_dict())
    paths["payload"].write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    paths["prompt"].write_text(SYSTEM_PROMPT, encoding="utf-8")
    paths["interpretation"].write_text(
        deterministic_interpretation(summaries, events),
        encoding="utf-8",
    )

    return paths
