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
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a test pickle file with gzip
            test_data = pd.DataFrame({
                "KlineDMU__open": [100.0],
                "KlineDMU__close": [101.0],
            })
            test_path = os.path.join(tmpdir, "IF2403_2024-03-15.pkl")
            test_data.to_pickle(test_path, compression="gzip")
            
            calc = FactorCalculator(db_directory=tmpdir)
            
            factors = calc.get_existing_factors("IF2403", "2024-03-15")
            
            assert "KlineDMU__open" in factors
            assert "KlineDMU__close" in factors
    
    def test_load_previous_results(self):
        """Test loading previous results."""
        from factor_calculator.core import FactorCalculator
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test data
            mock_data = pd.DataFrame({
                "KlineDMU__open": [100.0, 101.0, 102.0],
                "KlineDMU__close": [100.5, 101.5, 102.5],
            }, index=pd.date_range("2024-03-15 09:30", periods=3, freq="1min"))
            
            test_path = os.path.join(tmpdir, "IF2403_2024-03-15.pkl")
            mock_data.to_pickle(test_path, compression="gzip")
            
            calc = FactorCalculator(db_directory=tmpdir)
            
            # Load factors
            previous = calc._load_previous_results(
                "IF2403",
                datetime.date(2024, 3, 15),
                ["KlineDMU__open", "KlineDMU__close"]
            )
            
            # Should return the latest values
            assert "KlineDMU__open" in previous
            assert "KlineDMU__close" in previous
    
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
        
        with tempfile.TemporaryDirectory() as tmpdir:
            calc = FactorCalculator(db_directory=tmpdir)
            
            factors = pd.DataFrame({
                "KlineDMU__open": [100.0],
            })
            
            calc.save_factors(factors, "IF2403", "2024-03-15")
            
            # Verify file was created
            test_path = os.path.join(tmpdir, "IF2403_2024-03-15.pkl")
            assert os.path.exists(test_path)


class TestSimpleFactorCalculator:
    """Tests for SimpleFactorCalculator class."""
    
    @pytest.fixture
    def sample_md_data(self):
        """Create sample market data."""
        return pd.DataFrame({
            "last_px": [100.0, 101.0, 102.0],
            "tot_sz": [100, 200, 300],
            "oi": [1000, 1100, 1200],
        }, index=pd.date_range("2024-03-15 09:30", periods=3, freq="1min"))
    
    def test_init(self):
        """Test SimpleFactorCalculator initialization."""
        from factor_calculator.core import SimpleFactorCalculator
        
        with tempfile.TemporaryDirectory() as tmpdir:
            calc = SimpleFactorCalculator(db_directory=tmpdir)
            
            assert calc.db_directory == tmpdir
    
    def test_calculate_dmu(self, sample_md_data):
        """Test calculating DMU on market data."""
        from factor_calculator.core import SimpleFactorCalculator
        
        # Add required columns for TrendDMU
        sample_md_data["bid_px1"] = sample_md_data["last_px"] - 0.1
        sample_md_data["ask_px1"] = sample_md_data["last_px"] + 0.1
        
        with tempfile.TemporaryDirectory() as tmpdir:
            calc = SimpleFactorCalculator(db_directory=tmpdir)
            
            # TrendDMU is a simple DMU
            result = calc.calculate_dmu(
                dmu_spec="TrendDMU",
                contract="IF2403",
                trade_date="2024-03-15",
                md_data=sample_md_data,
            )
            
            assert result is not None
