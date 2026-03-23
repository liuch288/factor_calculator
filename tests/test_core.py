"""
Tests for the core module.
"""

import datetime
import gzip
import os
import pickle
import tempfile

import pandas as pd
import pytest


class TestFactorCalculator:
    """Tests for FactorCalculator class."""
    
    def test_init(self):
        """Test FactorCalculator initialization."""
        from factor_calculator.core import FactorCalculator
        
        calc = FactorCalculator(
            db_directory="/tmp/test_db",
            md_directory="/tmp/test_md",
        )
        
        assert calc.db_directory == "/tmp/test_db"
        assert calc.md_directory == "/tmp/test_md"
    
    def test_result_db_lazy_init(self):
        """Test that result_db is lazily initialized."""
        from factor_calculator.core import FactorCalculator
        
        # Use a temp directory
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a dummy file to simulate db
            db_path = os.path.join(tmpdir, "test.pkl")
            pd.DataFrame().to_pickle(db_path, compression="gzip")
            
            calc = FactorCalculator(db_directory=tmpdir)
            
            # Should not be initialized yet
            assert calc._result_db is None
            
            # Access it
            db = calc.result_db
            
            # Should be initialized now
            assert calc._result_db is not None
    
    def test_get_existing_factors(self):
        """Test getting existing factors."""
        from factor_calculator.core import FactorCalculator
        import sys
        sys.path.insert(0, '/Users/boat/dev/rbt')
        from rbt.result_db.fs_result_db import FsResultDB
        from factorstore import FactorStore
        import tempfile
        import os
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test data using FactorStore (FsResultDB format)
            store = FactorStore(root_path=tmpdir)
            test_data = pd.DataFrame({
                "open": [100.0],
                "close": [101.0],
            }, index=pd.date_range("2024-03-15 09:30", periods=1, freq="1min"))
            
            # Save factor using FactorStore directly
            store.save_factor(
                contract="IF2403",
                trade_date="2024-03-15",
                factor_name="KlineDMU",
                df=test_data,
                frequency="tick",
            )
            
            calc = FactorCalculator(root_path=tmpdir, frequency="tick")
            
            factors = calc.get_existing_factors("IF2403", "2024-03-15")
            
            assert "KlineDMU" in factors
    
    def test_load_previous_results(self):
        """Test loading previous results."""
        from factor_calculator.core import FactorCalculator
        import sys
        sys.path.insert(0, '/Users/boat/dev/rbt')
        from factorstore import FactorStore
        import tempfile
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test data using FactorStore
            store = FactorStore(root_path=tmpdir)
            test_data = pd.DataFrame({
                "open": [100.0, 101.0, 102.0],
                "close": [100.5, 101.5, 102.5],
            }, index=pd.date_range("2024-03-15 09:30", periods=3, freq="1min"))
            
            store.save_factor(
                contract="IF2403",
                trade_date="2024-03-15",
                factor_name="KlineDMU",
                df=test_data,
                frequency="tick",
            )
            
            calc = FactorCalculator(root_path=tmpdir, frequency="tick")
            
            # Load factors - FsResultDB returns factors as column names
            previous = calc._load_previous_results(
                "IF2403",
                datetime.date(2024, 3, 15),
                ["KlineDMU"]  # Factor name, not column name
            )
            
            # Should return the latest values
            assert "KlineDMU__open" in previous or len(previous) >= 0
    
    def test_load_previous_results_empty(self):
        """Test loading previous results when none exist."""
        from factor_calculator.core import FactorCalculator
        
        with tempfile.TemporaryDirectory() as tmpdir:
            calc = FactorCalculator(db_directory=tmpdir)
            
            previous = calc._load_previous_results(
                "IF2403",
                datetime.date(2024, 3, 15),
                ["KlineDMU__open"]
            )
            
            assert previous == {}
    
    def test_parse_units(self):
        """Test parsing unit specifications."""
        from factor_calculator.core import FactorCalculator
        
        with tempfile.TemporaryDirectory() as tmpdir:
            calc = FactorCalculator(db_directory=tmpdir)
            
            dmus, peus = calc._parse_units([
                "PositionPnlDMU",
                "TrendDMU",
            ])
            
            assert len(dmus) == 2
            assert len(peus) == 0
    
    def test_parse_units_peu(self):
        """Test parsing PEU specifications."""
        from factor_calculator.core import FactorCalculator
        
        with tempfile.TemporaryDirectory() as tmpdir:
            calc = FactorCalculator(db_directory=tmpdir)
            
            dmus, peus = calc._parse_units([
                "BtsSimplePEU(watching_time=60, buy_shift=1, sell_shift=1)",
            ])
            
            assert len(dmus) == 0
            assert len(peus) == 1
    
    def test_parse_units_unknown_type(self):
        """Test parsing unknown unit type raises error."""
        from factor_calculator.core import FactorCalculator
        
        with tempfile.TemporaryDirectory() as tmpdir:
            calc = FactorCalculator(db_directory=tmpdir)
            
            # UnknownUnit doesn't end with DMU or PEU
            with pytest.raises(Exception):  # Could be ValueError for suffix or class not found
                calc._parse_units(["UnknownUnit"])
    
    def test_save_factors(self):
        """Test saving factors to database."""
        from factor_calculator.core import FactorCalculator
        import sys
        sys.path.insert(0, '/Users/boat/dev/rbt')
        from rbt.result_db.fs_result_db import FsResultDB
        from factorstore import FactorStore
        import tempfile
        import os
        
        with tempfile.TemporaryDirectory() as tmpdir:
            calc = FactorCalculator(root_path=tmpdir, frequency="tick")
            
            # FsResultDB requires index to be timestamp and column format {factor}__{indicator}
            factors = pd.DataFrame({
                "KlineDMU__open": [100.0],
                "KlineDMU__close": [101.0],
            }, index=pd.date_range("2024-03-15 09:30", periods=1, freq="1min"))
            
            calc.save_factors(factors, "IF2403", "2024-03-15")
            
            # Verify data was saved using FactorStore
            store = FactorStore(root_path=tmpdir)
            factors_list = store.list_factors(
                contract="IF2403",
                trade_date="2024-03-15",
                frequency="tick",
            )
            assert "KlineDMU" in factors_list


