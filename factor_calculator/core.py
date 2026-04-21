"""
FactorCalculator - Main class for calculating factors using DMU and PEU units.

This module provides the FactorCalculator class that orchestrates factor calculation
by loading market data, creating units from specifications, and managing results.
"""

import datetime
import logging
import os
import time
from datetime import date
from typing import Any, Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)

import pandas as pd

from rbt.dmu import DecisionMakingUnit, PositionPnlDMU
from rbt.md import FuturesMdEngine
from rbt.peu import PnlEstimateUnit
from rbt.result_db.fs_result_db import FsResultDB
from rbt.strategy import Strategy

from .factory import create_unit, create_units


class FactorCalculator:
    """
    Main class for calculating factors using DMU and PEU units.
    
    This class integrates with the RBT framework to:
    - Load market data from configured sources
    - Create DMU (Decision Making Unit) and PEU (PnL Estimation Unit) instances
    - Run factor calculations with optional previous results
    - Save computed factors to a result database
    

    """
    
    def __init__(
        self,
        root_path: str = None,
        md_directory: Optional[str] = None,
        frequency: str = "tick",
        # Backward compatibility: db_directory -> root_path
        db_directory: str = None,
    ):
        """
        Initialize FactorCalculator.
        
        Args:
            root_path: Root path for FactorStore (formerly db_directory)
            md_directory: Directory containing market data files
            frequency: Data frequency (default: "tick")
            db_directory: (Deprecated) Use root_path instead
        """
        # Handle backward compatibility
        if root_path is None and db_directory is not None:
            root_path = db_directory
        
        self.root_path = root_path
        self.db_directory = root_path  # Backward compatibility alias
        self.md_directory = md_directory
        self.frequency = frequency
        
        # Initialize result database
        self.result_db = FsResultDB(self.root_path, self.frequency)
    
    def calculate(
        self,
        units: List[str],
        contract: str,
        trade_date: Optional[Union[str, date]] = None,
        frequency: str = "tick",
        recalculate: bool = False,
        bgm: Optional[Dict[str, Any]] = None,
        start_date: Optional[Union[str, date]] = None,
        end_date: Optional[Union[str, date]] = None,
        fail_fast: bool = False,
        show_progress: bool = True,
    ) -> pd.DataFrame:
        """
        Execute factor calculation.
        
        Supports two modes:
        - Single-day mode: provide ``trade_date`` only.
        - Multi-day mode: provide ``start_date`` and ``end_date``.
        The two modes are mutually exclusive.
        
        Args:
            units: List of unit specifications (e.g., ["KlineDMU(5)", "BiquotePEU(60)"])
            contract: Contract symbol (e.g., "IF2403")
            trade_date: Trade date as YYYY-MM-DD string or datetime.date.
                Used for single-day mode. Cannot be combined with
                start_date/end_date.
            frequency: Data frequency ("tick", "1min", "5min", etc.)
            recalculate: Whether to recalculate existing factors
            bgm: Background parameters dict injected into every tick's
                unit_results (e.g. constant config values).
            start_date: Start date (inclusive) for multi-day mode.
                Accepts YYYY-MM-DD string or datetime.date.
            end_date: End date (inclusive) for multi-day mode.
                Accepts YYYY-MM-DD string or datetime.date.
            fail_fast: If True, stop immediately on the first daily
                calculation failure. Defaults to False (skip failed
                dates and continue).
            show_progress: If True, show a progress bar for each day's
                tick-level calculation. Defaults to True.
            
        Returns:
            DataFrame containing calculated factor results.
            In multi-day mode the DataFrame includes a ``trade_date``
            column identifying each row's trading date.
            
        Raises:
            ValueError: If date parameters are invalid or conflicting.
        """
        # --- Parameter validation ---
        has_trade = trade_date is not None
        has_start = start_date is not None
        has_end = end_date is not None

        if has_trade and (has_start or has_end):
            raise ValueError(
                "Cannot use trade_date with start_date/end_date. Use one mode only."
            )

        if has_start != has_end:
            raise ValueError(
                "Both start_date and end_date must be provided for multi-day mode."
            )

        if not has_trade and not has_start and not has_end:
            raise ValueError(
                "Must provide either trade_date or start_date/end_date."
            )

        if has_start and has_end:
            start_date = self._normalize_date(start_date)
            end_date = self._normalize_date(end_date)
            if start_date > end_date:
                raise ValueError("start_date must not be later than end_date.")

        if has_trade:
            trade_date = self._normalize_date(trade_date)

        # Create unit instances from specifications
        dmus, peus = self._parse_units(units)

        # Multi-day mode
        if has_start and has_end:
            return self._run_strategy_multi_day(
                dmus=dmus,
                peus=peus,
                contract=contract,
                start_date=start_date,
                end_date=end_date,
                frequency=frequency,
                bgm=bgm,
                recalculate=recalculate,
                fail_fast=fail_fast,
                show_progress=show_progress,
            )

        # Single-day mode (existing behavior)
        return self._run_strategy(
            dmus=dmus,
            peus=peus,
            contract=contract,
            trade_date=trade_date,
            frequency=frequency,
            bgm=bgm,
            recalculate=recalculate,
            show_progress=show_progress,
        )
    
    def _parse_units(
        self, units: List[str]
    ) -> tuple:
        """
        Parse unit specifications into DMU and PEU instances.
        
        Args:
            units: List of unit specification strings
            
        Returns:
            Tuple of (dmus, peus) lists
        """
        dmus = []
        peus = []
        
        for spec in units:
            unit = create_unit(spec)
            
            # Determine if it's a DMU or PEU based on module
            if hasattr(unit, 'make_decision'):
                dmus.append(unit)
            elif hasattr(unit, 'estimate'):
                peus.append(unit)
            else:
                raise ValueError(f"Unknown unit type: {type(unit)}")
        
        return dmus, peus
    
    def _run_strategy(
        self,
        dmus: List[Any],
        peus: List[Any],
        contract: str,
        trade_date: date,
        frequency: str,
        bgm: Optional[Dict[str, Any]],
        recalculate: bool,
        show_progress: bool = False,
    ) -> pd.DataFrame:
        """
        Run the RBT Strategy to compute factors for a single date.

        Args:
            dmus: List of DMU instances
            peus: List of PEU instances
            contract: Contract symbol
            trade_date: Trade date
            frequency: Data frequency
            bgm: Background parameters or None
            recalculate: Whether to recalculate existing factors

        Returns:
            DataFrame containing calculated factors
        """
        strategy = self._build_strategy(dmus, peus, recalculate)
        strategy.run(sym=contract, dates=trade_date, show_progress=show_progress, bgm=bgm)
        return pd.DataFrame.from_dict(strategy.unit_results, orient="index")

    def _run_strategy_multi_day(
        self,
        dmus: List[Any],
        peus: List[Any],
        contract: str,
        start_date: date,
        end_date: date,
        frequency: str,
        bgm: Optional[Dict[str, Any]],
        recalculate: bool,
        fail_fast: bool,
        show_progress: bool = False,
    ) -> pd.DataFrame:
        """
        Run factor calculation over a date range.

        Delegates the multi-day loop to Strategy.run(sym, dates), which
        handles prepare_data, run, save, and on_end_of_day internally.
        FactorCalculator adds progress logging, error handling, and
        result merging on top.

        Args:
            dmus: List of DMU instances.
            peus: List of PEU instances.
            contract: Contract symbol.
            start_date: First date (inclusive).
            end_date: Last date (inclusive).
            frequency: Data frequency.
            bgm: Background parameters dict or None.
            recalculate: Whether to recalculate existing factors.
            fail_fast: If True, raise on first daily failure.

        Returns:
            Merged DataFrame with a ``trade_date`` column, or empty DataFrame
            if no dates succeeded.
        """
        dates = self._generate_date_range(start_date, end_date)
        total = len(dates)

        strategy = self._build_strategy(dmus, peus, recalculate)

        results_list: List[pd.DataFrame] = []
        failed_dates: List[Tuple[date, Exception]] = []
        success_count = 0
        t0 = time.time()

        for i, current_date in enumerate(dates, 1):
            logger.info(f"[{i}/{total}] 正在计算 {current_date}")
            try:
                strategy.run(sym=contract, dates=current_date, show_progress=show_progress, bgm=bgm)

                day_result = pd.DataFrame.from_dict(
                    strategy.unit_results, orient="index"
                )
                day_result["trade_date"] = str(current_date)
                results_list.append(day_result)
                success_count += 1
            except Exception as e:
                if fail_fast:
                    raise
                logger.error(f"计算 {current_date} 失败: {e}")
                failed_dates.append((current_date, e))

        elapsed = time.time() - t0
        logger.info(
            f"多天计算完成: {success_count}/{total} 天成功, 耗时 {elapsed:.1f}s"
        )

        if failed_dates:
            logger.warning(
                f"失败日期: {[str(d) for d, _ in failed_dates]}"
            )

        if results_list:
            return pd.concat(results_list, ignore_index=True)
        return pd.DataFrame()

    def _build_strategy(
        self,
        dmus: List[Any],
        peus: List[Any],
        recalculate: bool,
    ) -> Strategy:
        """
        Create and configure a Strategy instance with MdEngine, ResultDB,
        and all DMU/PEU units registered.
        """
        strategy = Strategy(position_pnl_dmu_class=PositionPnlDMU)
        md_engine = FuturesMdEngine(base_path=self.md_directory)
        strategy.register_md_engine(md_engine)
        strategy.register_result_db(self.result_db)
        for dmu in dmus:
            strategy.register_dmu(dmu, recalculate=recalculate)
        for peu in peus:
            strategy.register_peu(peu, recalculate=recalculate)
        return strategy

    @staticmethod
    def _normalize_date(d: Union[str, date]) -> date:
        """
        Normalize a date input to a datetime.date object.

        Args:
            d: Date as a string (YYYY-MM-DD) or datetime.date object.

        Returns:
            datetime.date object.

        Raises:
            ValueError: If the input is not a valid date string or date object.
        """
        if isinstance(d, date) and not isinstance(d, datetime.datetime):
            return d
        if isinstance(d, datetime.datetime):
            return d.date()
        if isinstance(d, str):
            try:
                return datetime.datetime.strptime(d, "%Y-%m-%d").date()
            except ValueError:
                raise ValueError(
                    f"Invalid date format: '{d}'. Expected YYYY-MM-DD."
                )
        raise ValueError(
            f"Unsupported date type: {type(d).__name__}. Expected str or datetime.date."
        )

    @staticmethod
    def _generate_date_range(start_date: date, end_date: date) -> List[date]:
        """
        Generate a list of all calendar dates from start_date to end_date (inclusive).

        Args:
            start_date: The first date in the range.
            end_date: The last date in the range (inclusive).

        Returns:
            List of datetime.date objects.
        """
        dates = []
        current = start_date
        while current <= end_date:
            dates.append(current)
            current += datetime.timedelta(days=1)
        return dates

    def get_existing_factors(
        self,
        contract: str,
        trade_date: str,
    ) -> List[str]:
        """
        Get list of existing factors in the database.
        
        Args:
            contract: Contract symbol
            trade_date: Trade date in YYYY-MM-DD format
            
        Returns:
            List of factor column names
        """
        return self.result_db.get_existing_factors(contract, trade_date)
    
    def save_factors(
        self,
        factors: pd.DataFrame,
        contract: str,
        trade_date: str,
    ) -> None:
        """
        Save calculated factors to the database.
        
        Args:
            factors: DataFrame containing factor data
            contract: Contract symbol
            trade_date: Trade date in YYYY-MM-DD format
        """
        self.result_db.save_data(contract, trade_date, factors)


