from __future__ import annotations

import argparse
from pathlib import Path

# Import directly from the modules so this runner does not depend on
# quotation_pattern_engine/operational/__init__.py exporting these names.
from quotation_pattern_engine.operational.config import OperationalConfig
from quotation_pattern_engine.operational.pipeline import run_operational_simulation


def _find_project_root(start: Path) -> Path:
    candidates = [start.resolve(), *start.resolve().parents]
    for candidate in candidates:
        if (candidate / "data" / "operational").is_dir():
            return candidate

    raise FileNotFoundError(
        "Could not find the project root containing data/operational. "
        "Run from inside the project or pass --project-root."
    )


def _first_existing(label: str, *paths: Path) -> Path:
    for path in paths:
        if path.exists():
            return path

    checked = "\n".join(f"  - {path}" for path in paths)
    raise FileNotFoundError(f"Could not find {label}. Checked:\n{checked}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the CUEBIT pattern-aware operational simulation."
    )
    parser.add_argument("--project-root", type=Path, default=None)
    args = parser.parse_args()

    root = (
        args.project_root.resolve()
        if args.project_root
        else _find_project_root(Path.cwd())
    )

    operational_data = root / "data" / "operational"

    engine_root = _first_existing(
        "quotation-pattern-engine directory",
        root / "quotation-pattern-engine",
        root,
    )

    quotation_output_candidates = [
        root / "outputs" / "quotation_analysis",
        engine_root / "examples" / "output",
        engine_root / "examples" / "outputs",
    ]

    serbatoi = _first_existing(
        "Serbatoi workbook",
        operational_data / "Serbatoi.xlsx",
        operational_data / "Serbatoi(2).xlsx",
    )

    daily_sales = _first_existing(
        "daily sales workbook",
        operational_data / "Litres.xlsx",
    )

    monthly_sales = _first_existing(
        "monthly sales workbook",
        operational_data / "Litri Venduti.xlsx",
        operational_data / "Litri Venduti (1)(1).xlsx",
    )

    daily_analysis = _first_existing(
        "daily_analysis.csv",
        *(path / "daily_analysis.csv" for path in quotation_output_candidates),
    )

    pattern_events = _first_existing(
        "pattern_events.csv",
        *(path / "pattern_events.csv" for path in quotation_output_candidates),
    )

    pattern_summary = _first_existing(
        "pattern_summary.csv",
        *(path / "pattern_summary.csv" for path in quotation_output_candidates),
    )

    config_path = root / "config" / "operational.json"
    config = (
        OperationalConfig.from_json(config_path)
        if config_path.exists()
        else OperationalConfig()
    )

    output_paths = run_operational_simulation(
        serbatoi_path=serbatoi,
        daily_sales_path=daily_sales,
        monthly_sales_path=monthly_sales,
        daily_analysis_csv=daily_analysis,
        pattern_events_csv=pattern_events,
        pattern_summary_csv=pattern_summary,
        output_dir=root / "outputs" / "operational",
        config=config,
    )

    print("CUEBIT operational simulation completed.")
    for name, path in output_paths.items():
        print(f"{name}: {Path(path).resolve()}")


if __name__ == "__main__":
    main()
