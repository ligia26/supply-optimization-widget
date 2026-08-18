from datetime import date

from quotation_pattern_engine.operational.config import OperationalConfig
from quotation_pattern_engine.operational.models import DemandProfile, QuotationPoint, TankState
from quotation_pattern_engine.operational.simulator import simulate_strategy


def test_as_is_never_drops_below_client_floor():
    config = OperationalConfig(
        simulation_start="2026-06-16",
        simulation_end="2026-06-18",
        minimum_inventory_litres=700.0,
    )
    tank = TankState("X", "Diesel", 10000.0, 1700.0, 1.50, None)
    profiles = [
        DemandProfile("X", "Diesel", weekday, 1000.0, 1.0)
        for weekday in range(7)
    ]
    quotations = [
        QuotationPoint(date(2026, 6, 16), "Diesel", "Gasolio Synergy", 1.50, "stable", "", None),
        QuotationPoint(date(2026, 6, 18), "Diesel", "Gasolio Synergy", 1.50, "stable", "", None),
    ]

    ledger, _ = simulate_strategy(
        "AS_IS", tank and [tank], profiles, quotations, [], [], config
    )

    assert min(row.closing_inventory_litres for row in ledger) >= 700.0 - 1e-9
    assert sum(row.lost_sales_litres for row in ledger) == 0.0
