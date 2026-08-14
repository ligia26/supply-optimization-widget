from __future__ import annotations

import argparse
from pathlib import Path

from quotation_pattern_engine.combined.config import CombinedConfig
from quotation_pattern_engine.combined.pipeline import run_combined_simulation
from quotation_pattern_engine.external.config import ExternalConfig
from quotation_pattern_engine.operational.config import OperationalConfig


def _first(label: str, *paths: Path) -> Path:
    for path in paths:
        if path.exists():
            return path
    raise FileNotFoundError(f"Could not find {label}. Checked: " + ", ".join(str(x) for x in paths))


def main() -> None:
    parser = argparse.ArgumentParser(description="Run CUEBIT external-aware simulation without replacing current operational outputs")
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="Root supply-optimization-widget directory",
    )

    args = parser.parse_args()
    root = args.project_root.resolve()
    op = root / "data" / "operational"
    ext = root / "data" / "external"
    quotation_outputs = [root / "outputs" / "quotation_analysis", root / "quotation-pattern-engine" / "examples" / "output"]
    operational_config = OperationalConfig.from_json(root / "config" / "operational.json") if (root / "config" / "operational.json").exists() else OperationalConfig()
    external_config = ExternalConfig.from_json(root / "config" / "external.json") if (root / "config" / "external.json").exists() else ExternalConfig()
    combined_config = CombinedConfig.from_json(root / "config" / "combined.json") if (root / "config" / "combined.json").exists() else CombinedConfig()
    paths = run_combined_simulation(
        serbatoi_path=_first("Serbatoi", op / "Serbatoi.xlsx", op / "Serbatoi(2).xlsx"),
        daily_sales_path=_first("Litres", op / "Litres.xlsx"),
        monthly_sales_path=_first("Litri Venduti", op / "Litri Venduti.xlsx", op / "Litri Venduti (1)(1).xlsx"),
        daily_analysis_csv=_first("daily_analysis.csv", *(x / "daily_analysis.csv" for x in quotation_outputs)),
        pattern_events_csv=_first("pattern_events.csv", *(x / "pattern_events.csv" for x in quotation_outputs)),
        pattern_summary_csv=_first("pattern_summary.csv", *(x / "pattern_summary.csv" for x in quotation_outputs)),
        external_market_csv=ext / "external_market_daily.csv",
        external_news_csv=ext / "external_news_events.csv",
        output_dir=root / "outputs" / "combined_external",
        operational_config=operational_config,
        external_config=external_config,
        combined_config=combined_config,
    )
    for name, path in paths.items():
        print(f"{name}: {path.resolve()}")


if __name__ == "__main__":
    main()
