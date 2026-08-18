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
    @classmethod
    def setUpClass(cls) -> None:
        cls.engine_root = Path(__file__).resolve().parents[1]
        cls.project_root = cls.engine_root.parent
        cls.config = OperationalConfig.from_json(
            cls.project_root / "config" / "operational.json"
        )
        cls.data_dir = cls.project_root / "data" / "operational"
        cls.monthly_sales = next(
            path for path in (
                cls.data_dir / "Litri Venduti.xlsx",
                cls.data_dir / "Litri Venduti (1)(1).xlsx",
            )
            if path.exists()
        )

    def _inputs(self):
        states = load_tank_states(self.data_dir / "Serbatoi.xlsx", self.config)
        sales = load_daily_sales(self.data_dir / "Litres.xlsx", self.config)
        growth = load_growth_factors(self.monthly_sales, self.config)
        profiles = build_demand_profiles(sales, growth)
        quotes = load_quotation_points(
            self.engine_root / "examples" / "output" / "daily_analysis.csv",
            self.config,
        )
        return states, profiles, quotes

    def test_tank_loader_excludes_performance(self) -> None:
        states = load_tank_states(self.data_dir / "Serbatoi.xlsx", self.config)
        self.assertEqual(len(states), 10)
        self.assertNotIn("Performance", {state.product for state in states})

    def test_demand_profiles_cover_all_distributors_and_products(self) -> None:
        states, profiles, _ = self._inputs()
        pairs = {(p.distributor_id, p.product) for p in profiles}
        self.assertEqual(len(pairs), 10)
        self.assertEqual(
            pairs,
            {(s.distributor_id, s.product) for s in states},
        )

    def test_confirmed_and_assumed_operational_parameters(self) -> None:
        self.assertEqual(self.config.hard_min_stock_litres, 700.0)
        self.assertEqual(self.config.delivery_lead_time_days, 1)
        self.assertEqual(self.config.minimum_order_litres, 5000.0)
        self.assertEqual(self.config.order_rounding_litres, 1000.0)
        self.assertEqual(self.config.max_fill_ratio, 0.95)

    def test_both_strategies_respect_floor_and_capacity(self) -> None:
        states, profiles, quotes = self._inputs()
        capacities = {
            (s.distributor_id, s.product): s.capacity_litres * self.config.max_fill_ratio
            for s in states
        }
        for strategy in ("AS_IS", "WIDGET"):
            ledgers, decisions = simulate_strategy(
                strategy,
                states,
                profiles,
                quotes,
                [],
                [],
                self.config,
            )
            self.assertTrue(ledgers)
            self.assertTrue(decisions)
            for row in ledgers:
                self.assertGreaterEqual(
                    row.closing_inventory_litres + 0.05,
                    self.config.hard_min_stock_litres,
                )
                self.assertLessEqual(
                    row.closing_inventory_litres,
                    capacities[(row.distributor_id, row.product)] + 0.05,
                )
                self.assertEqual(row.lost_sales_litres, 0.0)

    def test_nonterminal_orders_obey_minimum_and_rounding(self) -> None:
        states, profiles, quotes = self._inputs()
        for strategy in ("AS_IS", "WIDGET"):
            _, decisions = simulate_strategy(
                strategy, states, profiles, quotes, [], [], self.config
            )
            for decision in decisions:
                if decision.purchase_litres <= 0.05:
                    continue
                if decision.reason == "Final quotation-date stock equalisation":
                    continue
                # An order may be smaller only if safe physical headroom is
                # itself smaller than the configured MOQ.
                headroom = next(
                    s.capacity_litres * self.config.max_fill_ratio
                    - decision.inventory_before_litres
                    for s in states
                    if s.distributor_id == decision.distributor_id
                    and s.product == decision.product
                )
                if headroom + 0.05 >= self.config.minimum_order_litres:
                    self.assertGreaterEqual(
                        decision.purchase_litres + 0.05,
                        self.config.minimum_order_litres,
                    )
                    multiple = decision.purchase_litres / self.config.order_rounding_litres
                    self.assertAlmostEqual(multiple, round(multiple), places=5)


if __name__ == "__main__":
    unittest.main()
