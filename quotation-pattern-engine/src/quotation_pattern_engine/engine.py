from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict
from datetime import date
from statistics import mean, pstdev
from typing import Iterable, Any

from .config import EngineConfig
from .models import Quotation, DailyAnalysis, PatternEvent


class PatternEngine:
    def __init__(self, config: EngineConfig | None = None):
        self.config = config or EngineConfig()

    def analyze(
        self, quotations: Iterable[Quotation]
    ) -> tuple[list[DailyAnalysis], list[dict[str, Any]], list[PatternEvent]]:
        series = self._group_series(quotations)
        daily: list[DailyAnalysis] = []
        summaries: list[dict[str, Any]] = []
        events: list[PatternEvent] = []
        next_pattern_id = 1

        for (supplier, product), rows in sorted(series.items()):
            series_daily = self._daily_analysis(rows)
            daily.extend(series_daily)
            summaries.append(self._summary(rows, series_daily))

            series_events = self._events(
                rows=rows,
                start_pattern_number=next_pattern_id,
            )
            events.extend(series_events)
            next_pattern_id += len(series_events)

        return daily, summaries, events

    @staticmethod
    def _group_series(
        quotations: Iterable[Quotation],
    ) -> dict[tuple[str, str], list[Quotation]]:
        grouped: dict[tuple[str, str], list[Quotation]] = defaultdict(list)
        for quotation in quotations:
            grouped[quotation.series_key].append(quotation)
        for rows in grouped.values():
            rows.sort(key=lambda q: (q.date, q.input_order))
        return grouped

    def _sign(self, change: float) -> int:
        if change > self.config.movement_epsilon:
            return 1
        if change < -self.config.movement_epsilon:
            return -1
        return 0

    def _daily_analysis(self, rows: list[Quotation]) -> list[DailyAnalysis]:
        result: list[DailyAnalysis] = []

        for index, quotation in enumerate(rows):
            previous = rows[index - 1].price if index > 0 else None
            change = quotation.price - previous if previous is not None else None

            if change is None:
                direction = "Initial"
            else:
                sign = self._sign(change)
                direction = {1: "Increase", -1: "Decrease", 0: "Stable"}[sign]

            avg_start = max(0, index - self.config.moving_average_window + 1)
            moving_prices = [item.price for item in rows[avg_start:index + 1]]
            moving_average = mean(moving_prices)

            vol_start = max(1, index - self.config.volatility_window + 1)
            recent_changes = [
                rows[position].price - rows[position - 1].price
                for position in range(vol_start, index + 1)
            ]
            rolling_volatility = (
                pstdev(recent_changes) if len(recent_changes) >= 2 else 0.0
            )

            if index < self.config.regime_lookback:
                regime = "Insufficient history"
            else:
                regime_change = (
                    quotation.price
                    - rows[index - self.config.regime_lookback].price
                )
                if regime_change > self.config.regime_threshold:
                    regime = "Rising"
                elif regime_change < -self.config.regime_threshold:
                    regime = "Falling"
                else:
                    regime = "Stable"

            result.append(
                DailyAnalysis(
                    date=quotation.date,
                    supplier=quotation.supplier,
                    product=quotation.product,
                    price=quotation.price,
                    previous_price=previous,
                    change=change,
                    change_per_unit_divisor=(
                        change / self.config.price_to_display_unit_divisor
                        if change is not None
                        else None
                    ),
                    percentage_change=(
                        change / previous
                        if change is not None and previous not in (None, 0)
                        else None
                    ),
                    direction=direction,
                    moving_average=moving_average,
                    rolling_volatility=rolling_volatility,
                    regime=regime,
                    event_type=quotation.event_type,
                    source=quotation.source,
                )
            )

        return result

    def _volatility_label(self, value: float) -> str:
        if value < self.config.volatility_low_max:
            return "Low"
        if value < self.config.volatility_medium_max:
            return "Medium"
        return "High"

    def _summary(
        self,
        rows: list[Quotation],
        daily: list[DailyAnalysis],
    ) -> dict[str, Any]:
        prices = [row.price for row in rows]
        changes = [
            prices[index] - prices[index - 1]
            for index in range(1, len(prices))
        ]

        positive = [value for value in changes if self._sign(value) == 1]
        negative = [value for value in changes if self._sign(value) == -1]
        volatility = pstdev(changes) if len(changes) >= 2 else 0.0

        return {
            "supplier": rows[0].supplier,
            "product": rows[0].product,
            "period_start": rows[0].date,
            "period_end": rows[-1].date,
            "observations": len(rows),
            "start_price": prices[0],
            "end_price": prices[-1],
            "net_change": prices[-1] - prices[0],
            "display_unit_net_change": (
                (prices[-1] - prices[0])
                / self.config.price_to_display_unit_divisor
            ),
            "average_price": mean(prices),
            "minimum_price": min(prices),
            "maximum_price": max(prices),
            "price_range": max(prices) - min(prices),
            "average_change": mean(changes) if changes else 0.0,
            "volatility": volatility,
            "volatility_level": self._volatility_label(volatility),
            "maximum_increase": max(positive) if positive else 0.0,
            "maximum_decrease": min(negative) if negative else 0.0,
            "longest_increase_streak": self._max_streak(changes, 1),
            "longest_decrease_streak": self._max_streak(changes, -1),
            "reversals": self._reversal_count(changes),
            "current_regime": daily[-1].regime,
        }

    def _max_streak(self, changes: list[float], target_sign: int) -> int:
        best = 0
        current = 0
        for change in changes:
            if self._sign(change) == target_sign:
                current += 1
                best = max(best, current)
            else:
                current = 0
        return best

    def _reversal_count(self, changes: list[float]) -> int:
        reversals = 0
        previous_sign: int | None = None
        for change in changes:
            sign = self._sign(change)
            if sign == 0:
                continue
            if previous_sign is not None and sign != previous_sign:
                reversals += 1
            previous_sign = sign
        return reversals

    def _events(
        self,
        rows: list[Quotation],
        start_pattern_number: int,
    ) -> list[PatternEvent]:
        changes = [
            rows[index].price - rows[index - 1].price
            for index in range(1, len(rows))
        ]
        signs = [self._sign(value) for value in changes]
        events: list[PatternEvent] = []
        pattern_number = start_pattern_number

        def append_event(
            pattern_type: str,
            start_date: date,
            end_date: date,
            observation_count: int,
            magnitude: float,
            confidence: str,
            evidence: str,
        ) -> None:
            nonlocal pattern_number
            events.append(
                PatternEvent(
                    pattern_id=f"P{pattern_number:04d}",
                    supplier=rows[0].supplier,
                    product=rows[0].product,
                    pattern_type=pattern_type,
                    start_date=start_date,
                    end_date=end_date,
                    observation_count=observation_count,
                    magnitude=magnitude,
                    confidence=confidence,
                    evidence=evidence,
                )
            )
            pattern_number += 1

        # Consecutive increases and decreases.
        position = 0
        while position < len(signs):
            sign = signs[position]
            end = position
            while end + 1 < len(signs) and signs[end + 1] == sign:
                end += 1
            movement_count = end - position + 1

            if (
                sign != 0
                and movement_count >= self.config.minimum_streak_length
            ):
                start_row = position
                end_row = end + 1
                magnitude = rows[end_row].price - rows[start_row].price
                append_event(
                    pattern_type=(
                        "Consecutive increases"
                        if sign > 0
                        else "Consecutive decreases"
                    ),
                    start_date=rows[start_row].date,
                    end_date=rows[end_row].date,
                    observation_count=movement_count + 1,
                    magnitude=magnitude,
                    confidence="High",
                    evidence=(
                        f"{movement_count} consecutive movements; "
                        f"total change {magnitude:+.4f}"
                    ),
                )
            position = end + 1

        # Stable periods.
        position = 0
        while position < len(changes):
            stable = abs(changes[position]) <= self.config.stability_threshold
            end = position
            while (
                end + 1 < len(changes)
                and abs(changes[end + 1]) <= self.config.stability_threshold
            ):
                end += 1

            movement_count = end - position + 1
            if (
                stable
                and movement_count >= self.config.minimum_stable_length
            ):
                start_row = position
                end_row = end + 1
                magnitude = rows[end_row].price - rows[start_row].price
                append_event(
                    pattern_type="Stable period",
                    start_date=rows[start_row].date,
                    end_date=rows[end_row].date,
                    observation_count=movement_count + 1,
                    magnitude=magnitude,
                    confidence="High",
                    evidence=(
                        f"{movement_count} consecutive changes within "
                        f"±{self.config.stability_threshold}"
                    ),
                )
            position = end + 1

        # Regulatory adjustments and market spikes.
        absolute_changes = [abs(value) for value in changes]

        if absolute_changes:
            dispersion = (
                pstdev(absolute_changes)
                if len(absolute_changes) >= 2
                else 0.0
            )

            threshold = max(
                self.config.absolute_spike_floor,
                mean(absolute_changes)
                + self.config.spike_std_multiplier * dispersion,
            )

            for index, change in enumerate(changes, start=1):
                current_quotation = rows[index]

                is_regulatory_update = (
                    current_quotation.event_type.strip().lower()
                    == "regulatory update"
                )

                if is_regulatory_update:
                    append_event(
                        pattern_type="Regulatory adjustment",
                        start_date=rows[index - 1].date,
                        end_date=current_quotation.date,
                        observation_count=2,
                        magnitude=change,
                        confidence="High",
                        evidence=(
                            f"Quotation event type was "
                            f"{current_quotation.event_type!r}; "
                            f"price changed by {change:+.4f}"
                        ),
                    )

                elif abs(change) >= threshold:
                    append_event(
                        pattern_type=(
                            "Upward market spike"
                            if change > 0
                            else "Downward market spike"
                        ),
                        start_date=rows[index - 1].date,
                        end_date=current_quotation.date,
                        observation_count=2,
                        magnitude=change,
                        confidence="High",
                        evidence=(
                            f"Absolute change {abs(change):.4f} met or exceeded "
                            f"the calculated threshold {threshold:.4f}"
                        ),
                    )

        # Reversals.
        previous_nonzero: tuple[int, int] | None = None
        for index, sign in enumerate(signs, start=1):
            if sign == 0:
                continue
            if previous_nonzero is not None and sign != previous_nonzero[1]:
                change = rows[index].price - rows[index - 1].price
                append_event(
                    pattern_type="Trend reversal",
                    start_date=rows[index - 1].date,
                    end_date=rows[index].date,
                    observation_count=2,
                    magnitude=change,
                    confidence="Medium",
                    evidence=(
                        "Movement direction changed from "
                        f"{'increase' if previous_nonzero[1] > 0 else 'decrease'} "
                        f"to {'increase' if sign > 0 else 'decrease'}"
                    ),
                )
            previous_nonzero = (index, sign)

        return events
