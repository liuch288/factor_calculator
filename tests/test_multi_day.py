"""
Tests for multi-day factor calculation functionality.
"""

import datetime
import logging
from datetime import date
from unittest.mock import MagicMock, patch, PropertyMock

import pandas as pd
import pytest

from factor_calculator.core import FactorCalculator


class TestNormalizeDate:
    """Tests for FactorCalculator._normalize_date()."""

    def test_date_object_passthrough(self):
        d = date(2024, 3, 15)
        assert FactorCalculator._normalize_date(d) == d

    def test_string_yyyy_mm_dd(self):
        result = FactorCalculator._normalize_date("2024-03-15")
        assert result == date(2024, 3, 15)

    def test_datetime_object_extracts_date(self):
        dt = datetime.datetime(2024, 3, 15, 10, 30, 0)
        assert FactorCalculator._normalize_date(dt) == date(2024, 3, 15)

    def test_invalid_string_raises_valueerror(self):
        with pytest.raises(ValueError, match="Invalid date format"):
            FactorCalculator._normalize_date("15-03-2024")

    def test_non_date_string_raises_valueerror(self):
        with pytest.raises(ValueError, match="Invalid date format"):
            FactorCalculator._normalize_date("not-a-date")

    def test_unsupported_type_raises_valueerror(self):
        with pytest.raises(ValueError, match="Unsupported date type"):
            FactorCalculator._normalize_date(12345)

    def test_empty_string_raises_valueerror(self):
        with pytest.raises(ValueError, match="Invalid date format"):
            FactorCalculator._normalize_date("")


class TestGenerateDateRange:
    """Tests for FactorCalculator._generate_date_range()."""

    def test_single_day_range(self):
        d = date(2024, 3, 15)
        result = FactorCalculator._generate_date_range(d, d)
        assert result == [d]

    def test_multi_day_range(self):
        start = date(2024, 3, 1)
        end = date(2024, 3, 5)
        result = FactorCalculator._generate_date_range(start, end)
        assert result == [
            date(2024, 3, 1),
            date(2024, 3, 2),
            date(2024, 3, 3),
            date(2024, 3, 4),
            date(2024, 3, 5),
        ]

    def test_includes_start_and_end(self):
        start = date(2024, 1, 30)
        end = date(2024, 2, 2)
        result = FactorCalculator._generate_date_range(start, end)
        assert result[0] == start
        assert result[-1] == end


class TestCalculateParameterValidation:
    """Tests for calculate() date parameter validation (task 2.2)."""

    def _make_calculator(self):
        """Create a FactorCalculator with mocked dependencies."""
        from unittest.mock import MagicMock

        calc = object.__new__(FactorCalculator)
        calc.root_path = "/tmp/fake"
        calc.md_directory = "/tmp/fake_md"
        calc.frequency = "tick"
        calc.result_db = MagicMock()
        return calc

    def test_trade_date_with_start_date_raises(self):
        calc = self._make_calculator()
        with pytest.raises(
            ValueError,
            match="Cannot use trade_date with start_date/end_date. Use one mode only.",
        ):
            calc.calculate(
                units=["KlineDMU(5)"],
                contract="IF2403",
                trade_date="2024-03-15",
                start_date="2024-03-01",
            )

    def test_trade_date_with_end_date_raises(self):
        calc = self._make_calculator()
        with pytest.raises(
            ValueError,
            match="Cannot use trade_date with start_date/end_date. Use one mode only.",
        ):
            calc.calculate(
                units=["KlineDMU(5)"],
                contract="IF2403",
                trade_date="2024-03-15",
                end_date="2024-03-20",
            )

    def test_only_start_date_raises(self):
        calc = self._make_calculator()
        with pytest.raises(
            ValueError,
            match="Both start_date and end_date must be provided for multi-day mode.",
        ):
            calc.calculate(
                units=["KlineDMU(5)"],
                contract="IF2403",
                start_date="2024-03-01",
            )

    def test_only_end_date_raises(self):
        calc = self._make_calculator()
        with pytest.raises(
            ValueError,
            match="Both start_date and end_date must be provided for multi-day mode.",
        ):
            calc.calculate(
                units=["KlineDMU(5)"],
                contract="IF2403",
                end_date="2024-03-20",
            )

    def test_no_dates_raises(self):
        calc = self._make_calculator()
        with pytest.raises(
            ValueError,
            match="Must provide either trade_date or start_date/end_date.",
        ):
            calc.calculate(
                units=["KlineDMU(5)"],
                contract="IF2403",
            )

    def test_start_after_end_raises(self):
        calc = self._make_calculator()
        with pytest.raises(
            ValueError,
            match="start_date must not be later than end_date.",
        ):
            calc.calculate(
                units=["KlineDMU(5)"],
                contract="IF2403",
                start_date="2024-03-20",
                end_date="2024-03-01",
            )


class TestMultiDayErrorHandling:
    """Tests for error isolation and fail_fast behavior in multi-day mode."""

    def _make_calculator(self):
        """Create a FactorCalculator with mocked dependencies (bypass __init__)."""
        calc = object.__new__(FactorCalculator)
        calc.root_path = "/tmp/fake"
        calc.md_directory = "/tmp/fake_md"
        calc.frequency = "tick"
        calc.result_db = MagicMock()
        return calc

    def _make_mock_strategy(self, fail_on_dates=None):
        """
        Build a mock Strategy whose ``run()`` raises on specific call indices.

        Args:
            fail_on_dates: set of 0-based call indices where run() should raise.
        """
        fail_on_dates = fail_on_dates or set()
        mock_strategy = MagicMock()
        mock_strategy.dmus = []
        mock_strategy.peus = []

        call_count = {"n": 0}

        def _run_side_effect(**kwargs):
            idx = call_count["n"]
            call_count["n"] += 1
            if idx in fail_on_dates:
                raise RuntimeError(f"Simulated failure on call {idx}")

        mock_strategy.run.side_effect = _run_side_effect
        # unit_results returns a simple dict simulating tick-level results
        type(mock_strategy).unit_results = PropertyMock(
            return_value={0: {"col1": 1.0}, 1: {"col1": 2.0}}
        )
        return mock_strategy

    @patch("factor_calculator.core.FuturesMdEngine")
    @patch("factor_calculator.core.Strategy")
    def test_error_isolation_continues_on_failure(
        self, MockStrategy, MockMdEngine
    ):
        """When one day fails and fail_fast=False, other days still succeed."""
        mock_strategy = self._make_mock_strategy(fail_on_dates={1})
        MockStrategy.return_value = mock_strategy
        MockMdEngine.return_value = MagicMock()

        calc = self._make_calculator()
        result = calc._run_strategy_multi_day(
            dmus=[],
            peus=[],
            contract="IF2403",
            start_date=date(2024, 3, 1),
            end_date=date(2024, 3, 3),
            frequency="tick",
            bgm=None,
            recalculate=False,
            fail_fast=False,
        )

        # Days 1 and 3 succeed, day 2 fails → 2 save_data calls
        assert calc.result_db.save_data.call_count == 2
        assert isinstance(result, pd.DataFrame)
        assert not result.empty
        # Result should contain trade_date values for the 2 successful days
        assert set(result["trade_date"]) == {"2024-03-01", "2024-03-03"}

    @patch("factor_calculator.core.FuturesMdEngine")
    @patch("factor_calculator.core.Strategy")
    def test_fail_fast_stops_on_first_error(self, MockStrategy, MockMdEngine):
        """When fail_fast=True, the exception propagates immediately."""
        mock_strategy = self._make_mock_strategy(fail_on_dates={1})
        MockStrategy.return_value = mock_strategy
        MockMdEngine.return_value = MagicMock()

        calc = self._make_calculator()
        with pytest.raises(RuntimeError, match="Simulated failure on call 1"):
            calc._run_strategy_multi_day(
                dmus=[],
                peus=[],
                contract="IF2403",
                start_date=date(2024, 3, 1),
                end_date=date(2024, 3, 3),
                frequency="tick",
                bgm=None,
                recalculate=False,
                fail_fast=True,
            )

        # Only the first day ran successfully before the second day failed
        assert calc.result_db.save_data.call_count == 1

    @patch("factor_calculator.core.FuturesMdEngine")
    @patch("factor_calculator.core.Strategy")
    def test_all_dates_fail_returns_empty_dataframe(
        self, MockStrategy, MockMdEngine
    ):
        """When every day fails, an empty DataFrame is returned."""
        mock_strategy = self._make_mock_strategy(fail_on_dates={0, 1, 2})
        MockStrategy.return_value = mock_strategy
        MockMdEngine.return_value = MagicMock()

        calc = self._make_calculator()
        result = calc._run_strategy_multi_day(
            dmus=[],
            peus=[],
            contract="IF2403",
            start_date=date(2024, 3, 1),
            end_date=date(2024, 3, 3),
            frequency="tick",
            bgm=None,
            recalculate=False,
            fail_fast=False,
        )

        assert isinstance(result, pd.DataFrame)
        assert result.empty
        assert calc.result_db.save_data.call_count == 0

    @patch("factor_calculator.core.FuturesMdEngine")
    @patch("factor_calculator.core.Strategy")
    def test_failed_dates_logged(self, MockStrategy, MockMdEngine, caplog):
        """Failed dates appear in the warning log summary."""
        mock_strategy = self._make_mock_strategy(fail_on_dates={0, 2})
        MockStrategy.return_value = mock_strategy
        MockMdEngine.return_value = MagicMock()

        calc = self._make_calculator()
        with caplog.at_level(logging.WARNING, logger="factor_calculator.core"):
            calc._run_strategy_multi_day(
                dmus=[],
                peus=[],
                contract="IF2403",
                start_date=date(2024, 3, 1),
                end_date=date(2024, 3, 3),
                frequency="tick",
                bgm=None,
                recalculate=False,
                fail_fast=False,
            )

        # The warning log should mention both failed dates
        warning_messages = [
            r.message for r in caplog.records if r.levelno == logging.WARNING
        ]
        combined = " ".join(warning_messages)
        assert "2024-03-01" in combined
        assert "2024-03-03" in combined
