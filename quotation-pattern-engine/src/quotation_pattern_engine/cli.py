from __future__ import annotations

import argparse
from pathlib import Path

from .config import EngineConfig
from .pipeline import run_pipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="quotation-patterns",
        description="Analyze historical quotation patterns.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze = subparsers.add_parser("analyze")
    analyze.add_argument("--input", required=True, help="Input quotation CSV.")
    analyze.add_argument("--output", required=True, help="Output directory.")
    analyze.add_argument(
        "--config",
        help="Optional JSON configuration. Defaults are used when omitted.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()

    if args.command == "analyze":
        config = (
            EngineConfig.from_json(args.config)
            if args.config
            else EngineConfig()
        )
        paths = run_pipeline(args.input, args.output, config)
        print("Analysis completed.")
        for name, path in paths.items():
            print(f"{name}: {Path(path).resolve()}")


if __name__ == "__main__":
    main()
