import unittest
from datetime import date

from quotation_pattern_engine.config import EngineConfig
from quotation_pattern_engine.engine import PatternEngine
from quotation_pattern_engine.io import canonicalize
from quotation_pattern_engine.models import Quotation


class PatternEngineTests(unittest.TestCase):
    def test_higher_priority_revision_becomes_canonical(self):
        rows = [
            Quotation(
                date=date(2026, 7, 4),
                supplier="A",
                product="Diesel",
                price=100,
                priority=0,
                input_order=0,
            ),
            Quotation(
                date=date(2026, 7, 4),
                supplier="A",
                product="Diesel",
                price=110,
                priority=10,
                input_order=1,
            ),
        ]
        selected = canonicalize(rows)
        self.assertEqual(len(selected), 1)
        self.assertEqual(selected[0].price, 110)

    def test_streak_and_reversal_detection(self):
        config = EngineConfig(
            movement_epsilon=0,
            minimum_streak_length=2,
            absolute_spike_floor=1000,
        )
        rows = [
            Quotation(date=date(2026, 1, day), supplier="A", product="D", price=price)
            for day, price in enumerate([100, 101, 102, 101], start=1)
        ]
        daily, summaries, events = PatternEngine(config).analyze(rows)

        event_types = [event.pattern_type for event in events]
        self.assertIn("Consecutive increases", event_types)
        self.assertIn("Trend reversal", event_types)
        self.assertEqual(summaries[0]["longest_increase_streak"], 2)
        self.assertEqual(summaries[0]["reversals"], 1)

    def test_series_are_analyzed_independently(self):
        rows = [
            Quotation(date=date(2026, 1, 1), supplier="A", product="D", price=100),
            Quotation(date=date(2026, 1, 2), supplier="A", product="D", price=101),
            Quotation(date=date(2026, 1, 1), supplier="B", product="D", price=200),
            Quotation(date=date(2026, 1, 2), supplier="B", product="D", price=199),
        ]
        _, summaries, _ = PatternEngine().analyze(rows)
        self.assertEqual(len(summaries), 2)


if __name__ == "__main__":
    unittest.main()
