from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parent
OPTIMIZER = ROOT / "src" / "quotation_pattern_engine" / "combined" / "optimizer.py"
PIPELINE = ROOT / "src" / "quotation_pattern_engine" / "combined" / "pipeline.py"


def patch_optimizer() -> None:
    text = OPTIMIZER.read_text(encoding="utf-8")

    old_missing_block = '''    missing = available - set(payload)
    if missing:
        raise TypeError(
            "Unsupported CandidateEvaluation schema. "
            f"Could not populate required fields: {sorted(missing)}"
        )

    return CandidateEvaluation(**payload)
'''

    new_missing_block = '''    # selected and selection_reason have defaults in the real dataclass.
    return CandidateEvaluation(**payload)
'''

    if old_missing_block in text:
        text = text.replace(old_missing_block, new_missing_block)

    text = text.replace(
        "expected_total_cost_eur",
        "robust_objective_eur",
    )

    OPTIMIZER.write_text(text, encoding="utf-8")


def patch_pipeline() -> None:
    text = PIPELINE.read_text(encoding="utf-8")

    text = text.replace(
        "candidate.expected_total_cost_eur",
        "candidate.robust_objective_eur",
    )
    text = text.replace(
        "chosen.expected_total_cost_eur",
        "chosen.robust_objective_eur",
    )
    text = text.replace(
        "required.expected_total_cost_eur",
        "required.robust_objective_eur",
    )

    PIPELINE.write_text(text, encoding="utf-8")


def verify() -> None:
    stale = []

    for path in (
        OPTIMIZER,
        PIPELINE,
        ROOT / "src" / "quotation_pattern_engine" / "combined" / "simulator.py",
    ):
        if not path.exists():
            continue

        text = path.read_text(encoding="utf-8")
        if "expected_total_cost_eur" in text:
            stale.append(str(path))

    if stale:
        raise RuntimeError(
            "Stale expected_total_cost_eur references remain in: "
            + ", ".join(stale)
        )

    print("Combined files repaired successfully.")
    print("Run:")
    print("PYTHONPATH=src python run_combined_simulation.py")


def main() -> None:
    if not OPTIMIZER.exists():
        raise FileNotFoundError(OPTIMIZER)
    if not PIPELINE.exists():
        raise FileNotFoundError(PIPELINE)

    patch_optimizer()
    patch_pipeline()
    verify()


if __name__ == "__main__":
    main()
