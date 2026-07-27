from __future__ import annotations

import unittest
from pathlib import Path

from quotation_pattern_engine.operational.config import OperationalConfig
from quotation_pattern_engine.operational.loaders import (
    build_demand_profiles,
    load_daily_sales,
    load_growth_factors,
    load_quotation_points,
    load_tank_states,
)
from quotation_pattern_engine.operational.simulator import simulate_strategy


class OperationalSimulationTests(unittest.TestCase):
    """Integration tests for the client workbooks and quotation output.

    Expected project layout:

        supply-optimization-widget/
            data/operational/*.xlsx
            config/operational.json
            quotation-pattern-engine/
                examples/output/daily_analysis.csv
                tests/test_operational.py
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.engine_root = Path(__file__).resolve().parents[1]
        cls.project_root = cls.engine_root.parent
        cls.config = OperationalConfig.from_json(
            cls.project_root / "config" / "operational.json"
        )
        cls.data_dir = cls.project_root / "data" / "operational"

    def test_tank_loader_excludes_performance(self) -> None:
        states = load_tank_states(self.data_dir / "Serbatoi.xlsx", self.config)
        self.assertEqual(len(states), 10)
        self.assertNotIn("Performance", {state.product for state in states})

    def test_demand_profiles_cover_all_distributors_and_products(self) -> None:
        sales = load_daily_sales(self.data_dir / "Litres.xlsx", self.config)
        growth = load_growth_factors(
            self.data_dir / "Litri Venduti.xlsx", self.config
        )
        profiles = build_demand_profiles(sales, growth)
        pairs = {(p.distributor_id, p.product) for p in profiles}
        self.assertEqual(len(pairs), 10)

    def test_simulation_respects_physical_capacity(self) -> None:
        states = load_tank_states(self.data_dir / "Serbatoi.xlsx", self.config)
        sales = load_daily_sales(self.data_dir / "Litres.xlsx", self.config)
        growth = load_growth_factors(
            self.data_dir / "Litri Venduti.xlsx", self.config
        )
        profiles = build_demand_profiles(sales, growth)
        quotes = load_quotation_points(
            self.engine_root / "examples" / "output" / "daily_analysis.csv",
            self.config,
        )
        ledgers, decisions = simulate_strategy(
            "WIDGET", states, profiles, quotes, self.config
        )
        capacities = {(s.distributor_id, s.product): s.capacity_litres for s in states}

        self.assertTrue(ledgers)
        self.assertTrue(decisions)
        for row in ledgers:
            self.assertGreaterEqual(row.closing_inventory_litres, 0.0)
            self.assertLessEqual(
                row.closing_inventory_litres,
                capacities[(row.distributor_id, row.product)],
            )

    def test_config_has_no_unconfirmed_order_parameters(self) -> None:
        forbidden = {
            "safety_stock_days",
            "baseline_target_days",
            "stable_target_days",
            "rising_target_days",
            "falling_target_days",
            "regulatory_target_days",
            "minimum_order_litres",
            "order_rounding_litres",
            "maximum_fill_ratio",
        }
        self.assertTrue(forbidden.isdisjoint(self.config.__dataclass_fields__))


if __name__ == "__main__":
    unittest.main()