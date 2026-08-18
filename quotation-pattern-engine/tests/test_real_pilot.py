from pathlib import Path
import pandas as pd


def _output_root() -> Path:
    return Path(__file__).resolve().parents[2] / "outputs" / "operational"


def test_verified_outputs_use_inventory_adjusted_economics():
    comp = pd.read_csv(_output_root() / "cuebit_vs_as_is.csv")
    ledger = pd.read_csv(_output_root() / "daily_inventory_ledger.csv")

    assert comp.cuebit_lost_sales_litres.sum() < 1e-6
    assert ledger.closing_inventory_litres.min() >= 699.95

    # V3 explicitly allows different purchased litres and ending inventories.
    # Fairness is achieved through terminal inventory valuation instead of a
    # fake final-day equalisation order.
    expected = (
        comp.as_is_inventory_adjusted_economic_cost_eur
        - comp.cuebit_inventory_adjusted_economic_cost_eur
    )
    assert (expected - comp.estimated_saving_eur).abs().max() < 1e-6
    assert "Final quotation-date stock equalisation" not in pd.read_csv(
        _output_root() / "purchase_decisions.csv"
    ).reason.fillna("").tolist()
