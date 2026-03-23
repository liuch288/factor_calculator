"""
FactorCalculator - Main class for calculating factors using DMU and PEU units.

This module provides the FactorCalculator class that orchestrates factor calculation
by loading market data, creating units from specifications, and managing results.
"""

import os
from typing import Any, Dict, List, Optional

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
    
    Example:
        >>> calculator = FactorCalculator(
        ...     root_path="/path/to/results",
        ...     frequency="tick",
        ...     md_directory="/path/to/market/data"
        ... )
        >>> units = ["KlineDMU(interval=5)", "BiquotePEU(watching_time=60)"]
        >>> load_factors = ["KlineDMU__open", "KlineDMU__close"]
        >>> result = calculator.calculate(
        ...     units=units,
        ...     load_factors=load_factors,
        ...     contract="IF2403",
        ...     trade_date="2024-03-15",
        ...     frequency="tick"
        ... )
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
        load_factors: List[str],
        contract: str,
        trade_date: str,
        frequency: str = "tick",
        recalculate: bool = False,
    ) -> pd.DataFrame:
        """
        Execute factor calculation.
        
        Args:
            units: List of unit specifications (e.g., ["KlineDMU(5)", "BiquotePEU(60)"])
            load_factors: List of factor names to load from previous results
            contract: Contract symbol (e.g., "IF2403")
            trade_date: Trade date in YYYY-MM-DD format
            frequency: Data frequency ("tick", "1min", "5min", etc.)
            recalculate: Whether to recalculate existing factors
            
        Returns:
            DataFrame containing calculated factor results
            
        Raises:
            ValueError: If required dependencies are missing
        """
        # Create unit instances from specifications
        dmus, peus = self._parse_units(units)
        
        # Load previous results if requested
        previous_results = self._load_previous_results(
            contract, trade_date, load_factors
        )
        
        # Run calculation using RBT Strategy
        return self._run_strategy(
            dmus=dmus,
            peus=peus,
            contract=contract,
            trade_date=trade_date,
            frequency=frequency,
            previous_results=previous_results,
            recalculate=recalculate,
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
    
    def _load_previous_results(
        self,
        contract: str,
        trade_date: str,
        load_factors: List[str],
    ) -> Dict[str, Any]:
        """
        Load previous factor results from the database.
        
        Args:
            contract: Contract symbol
            trade_date: Trade date
            load_factors: List of factor names to load
            
        Returns:
            Dictionary of previous results (factor_name -> value)
        """
        if not load_factors:
            return {}
        
        # Get data from result DB
        data = self.result_db.get_data(contract, trade_date)
        
        if data is None or data.empty:
            return {}
        
        # Extract requested factors
        previous_results = {}
        for factor in load_factors:
            if factor in data.columns:
                # Get the latest value
                previous_results[factor] = data[factor].iloc[-1]
        
        return previous_results
    
    def _run_strategy(
        self,
        dmus: List[Any],
        peus: List[Any],
        contract: str,
        trade_date: str,
        frequency: str,
        previous_results: Dict[str, Any],
        recalculate: bool,
    ) -> pd.DataFrame:
        """
        Run the RBT Strategy to compute factors.
        
        Args:
            dmus: List of DMU instances
            peus: List of PEU instances
            contract: Contract symbol
            trade_date: Trade date
            frequency: Data frequency
            previous_results: Previous factor results to inject
            recalculate: Whether to recalculate existing factors
            
        Returns:
            DataFrame containing calculated factors
        """
        # Import RBT Strategy
        
        # Initialize strategy
        strategy = Strategy(position_pnl_dmu_class=PositionPnlDMU)
        
        # Register units
        for dmu in dmus:
            strategy.register_dmu(dmu, recalculate=recalculate)
        
        for peu in peus:
            strategy.register_peu(peu, recalculate=recalculate)
        
        # Register result database
        strategy.register_result_db(self.result_db)
        
        # Register market data engine
        md_engine = FuturesMdEngine(base_path=self.md_directory)
        md_engine.prepare_data(sym=contract, date=trade_date)
        strategy.register_md_engine(md_engine)
        
        # Inject previous results as bgm
        bgm = previous_results if previous_results else None
        
        # Run strategy
        strategy.run(bgm=bgm)
        
        # Return results
        return pd.DataFrame.from_dict(
            strategy.unit_results, orient="index"
        )
    
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


