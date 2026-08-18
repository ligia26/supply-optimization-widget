from datetime import date

from quotation_pattern_engine.operational.config import OperationalConfig
from quotation_pattern_engine.operational.models import QuotationPoint, SignalAssessment, TankState
from quotation_pattern_engine.operational.optimizer import (
    baseline_replenishment_buy,
    evaluate_candidates,
    reorder_point_litres,
)


def _history(changes):
    price = 1.40
    rows = []
    for i, change in enumerate(changes):
        price += change
        rows.append(
            QuotationPoint(
                date(2026, 1, 1 + i),
                "Diesel",
                "Diesel",
                price,
                "Rising" if change > 0 else "Falling",
                "Normal quotation",
                change,
            )
        )
    return rows


def test_reorder_point_includes_floor_and_lead_time_demand():
    cfg = OperationalConfig(delivery_lead_time_days=1, hard_min_stock_litres=700)
    lookup = {('1', 'Diesel', i): 3000 for i in range(7)}
    assert reorder_point_litres(lookup, '1', 'Diesel', date(2026, 1, 5), cfg) == 3700


def test_baseline_buys_smallest_standard_chunk_needed():
    cfg = OperationalConfig()
    tank = TankState('1', 'Diesel', 35000, 5000, 1.0, None)
    lookup = {('1', 'Diesel', i): 4000 for i in range(7)}
    buy, rp = baseline_replenishment_buy(
        lookup=lookup,
        tank=tank,
        inventory=4500,
        day=date(2026, 1, 5),
        required_end=date(2026, 1, 6),
        config=cfg,
    )
    assert rp == 4700
    assert buy == 5000  # Reactive AS IS: MOQ only when that safely covers the requirement.


def test_candidates_obey_minimum_rounding_and_capacity():
    cfg = OperationalConfig(planning_horizon_days=14)
    tank = TankState('1', 'Diesel', 20000, 2000, 1.0, None)
    lookup = {('1', 'Diesel', i): 900 for i in range(7)}
    sig = SignalAssessment(.2, .5, .001, .4, .01, (), ())
    rows = evaluate_candidates(
        day=date(2026, 1, 4),
        end=date(2026, 1, 20),
        tank=tank,
        inventory=2000,
        current_price=1.4,
        required_buy=5000,
        demand_lookup=lookup,
        signal=sig,
        history=_history([-.01, .00, .01, .01]),
        config=cfg,
    )
    assert len(rows) >= 3
    assert max(r.purchase_litres for r in rows) <= 17000  # 95% cap minus 2k stock
    for row in rows:
        if row.purchase_litres > 0:
            assert row.purchase_litres >= 5000
            assert abs(row.purchase_litres / 1000 - round(row.purchase_litres / 1000)) < 1e-6


def test_bullish_signal_can_favour_more_than_required():
    cfg = OperationalConfig(planning_horizon_days=7)
    tank = TankState('1', 'Diesel', 20000, 6000, 1.0, None)
    lookup = {('1', 'Diesel', i): 1000 for i in range(7)}
    sig = SignalAssessment(.8, .8, .02, .2, .01, ('P01 rising',), ())
    rows = evaluate_candidates(
        day=date(2026, 1, 4), end=date(2026, 1, 15), tank=tank,
        inventory=6000, current_price=1.4, required_buy=5000,
        demand_lookup=lookup, signal=sig,
        history=_history([-.01, .01, .02, .01]), config=cfg,
    )
    best = min(rows, key=lambda x: x.robust_objective_eur)
    assert best.purchase_litres >= 5000
