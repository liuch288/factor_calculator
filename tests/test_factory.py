"""
Tests for the factory module.
"""

import datetime
import pytest

from factor_calculator.factory import (
    create_unit,
    create_units,
    get_available_classes,
    parse_parameters,
    parse_unit_spec,
    parse_value,
)


class TestParseUnitSpec:
    """Tests for parse_unit_spec function."""
    
    def test_simple_class_no_params(self):
        """Test parsing a simple class with no parameters."""
        class_name, params = parse_unit_spec("KlineDMU")
        assert class_name == "KlineDMU"
        assert params == ""
    
    def test_class_with_single_int_param(self):
        """Test parsing a class with a single integer parameter."""
        class_name, params = parse_unit_spec("KlineDMU(45)")
        assert class_name == "KlineDMU"
        assert params == "45"
    
    def test_class_with_kwargs(self):
        """Test parsing a class with keyword arguments."""
        class_name, params = parse_unit_spec("KlineDMU(interval=5)")
        assert class_name == "KlineDMU"
        assert params == "interval=5"
    
    def test_class_with_multiple_kwargs(self):
        """Test parsing a class with multiple keyword arguments."""
        class_name, params = parse_unit_spec("BiquotePEU(watching_time=60, watching_mds=100)")
        assert class_name == "BiquotePEU"
        assert params == "watching_time=60, watching_mds=100"
    
    def test_class_with_time_param(self):
        """Test parsing a class with time parameter."""
        class_name, params = parse_unit_spec("KlineDMU(start_time=9:30)")
        assert class_name == "KlineDMU"
        assert params == "start_time=9:30"
    
    def test_whitespace_handling(self):
        """Test that whitespace is handled correctly."""
        class_name, params = parse_unit_spec("  KlineDMU(45)  ")
        assert class_name == "KlineDMU"
        assert params == "45"


class TestParseParameters:
    """Tests for parse_parameters function."""
    
    def test_empty_string(self):
        """Test parsing empty parameter string."""
        assert parse_parameters("") == ([], {})
    
    def test_single_int(self):
        """Test parsing a single integer."""
        result = parse_parameters("45")
        assert result == ([45], {})
    
    def test_single_float(self):
        """Test parsing a single float."""
        result = parse_parameters("3.14")
        assert result == ([3.14], {})
    
    def test_single_string(self):
        """Test parsing a single string."""
        result = parse_parameters("hello")
        assert result == (["hello"], {})
    
    def test_single_kwarg_int(self):
        """Test parsing a single keyword argument integer."""
        result = parse_parameters("interval=5")
        assert result == ([], {"interval": 5})
    
    def test_single_kwarg_float(self):
        """Test parsing a single keyword argument float."""
        result = parse_parameters("threshold=3.14")
        assert result == ([], {"threshold": 3.14})
    
    def test_multiple_kwargs(self):
        """Test parsing multiple keyword arguments."""
        result = parse_parameters("a=1, b=2, c=3")
        assert result == ([], {"a": 1, "b": 2, "c": 3})
    
    def test_mixed_positional_and_kwargs(self):
        """Test parsing positional args with keyword arguments."""
        result = parse_parameters("60, watching_mds=100")
        assert result == ([60], {"watching_mds": 100})


class TestParseValue:
    """Tests for parse_value function."""
    
    def test_parse_int(self):
        """Test parsing integer values."""
        assert parse_value("42") == 42
        assert parse_value("-10") == -10
    
    def test_parse_float(self):
        """Test parsing float values."""
        assert parse_value("3.14") == 3.14
        assert parse_value("-2.5") == -2.5
    
    def test_parse_bool(self):
        """Test parsing boolean values."""
        assert parse_value("True") is True
        assert parse_value("False") is False
    
    def test_parse_none(self):
        """Test parsing None."""
        assert parse_value("None") is None
    
    def test_parse_time(self):
        """Test parsing time values."""
        result = parse_value("9:30")
        assert isinstance(result, datetime.time)
        assert result.hour == 9
        assert result.minute == 30
        
        result = parse_value("14:30:00")
        assert result.hour == 14
        assert result.minute == 30
        assert result.second == 0
    
    def test_parse_string(self):
        """Test parsing string values."""
        assert parse_value("'hello'") == "hello"
        assert parse_value('"world"') == "world"
        assert parse_value("plain_string") == "plain_string"


class TestCreateUnit:
    """Tests for create_unit function."""
    
    def test_create_dmu(self):
        """Test creating a DMU instance."""
        unit = create_unit("PositionPnlDMU")
        assert unit is not None
        assert hasattr(unit, 'make_decision')
    
    def test_create_dmu_with_params(self):
        """Test creating a DMU with parameters."""
        unit = create_unit("TrendDMU()")
        assert unit is not None
    
    def test_create_peu(self):
        """Test creating a PEU instance."""
        unit = create_unit("BtsSimplePEU(watching_time=60, buy_shift=1, sell_shift=1)")
        assert unit is not None
        assert hasattr(unit, 'estimate')
    
    def test_create_kline_dmu(self):
        """Test creating KlineDMU which is in a submodule."""
        unit = create_unit("KlineDMU(interval=5)")
        assert unit is not None
        assert hasattr(unit, 'interval')
        assert unit.interval == 5
    
    def test_invalid_suffix(self):
        """Test that invalid suffix raises error."""
        with pytest.raises(ValueError, match="Unknown class suffix"):
            create_unit("InvalidUnit")
    
    def test_nonexistent_class(self):
        """Test that nonexistent class raises error."""
        with pytest.raises(ValueError, match="not found"):
            create_unit("NonExistentDMU")
    
    def test_invalid_params(self):
        """Test that invalid parameters raise error."""
        with pytest.raises(ValueError, match="Failed to instantiate"):
            create_unit("TrendDMU(invalid_param=999)")


class TestCreateUnits:
    """Tests for create_units function."""
    
    def test_create_multiple_units(self):
        """Test creating multiple units."""
        units = create_units([
            "PositionPnlDMU",
            "TrendDMU",
        ])
        assert len(units) == 2
        assert all(u is not None for u in units)


class TestGetAvailableClasses:
    """Tests for get_available_classes function."""
    
    def test_get_all_classes(self):
        """Test getting all available classes."""
        classes = get_available_classes()
        assert len(classes) > 0
        assert "KlineDMU" in classes
    
    def test_filter_dmu(self):
        """Test filtering for DMU classes only."""
        classes = get_available_classes("DMU")
        assert all(c.endswith("DMU") for c in classes)
    
    def test_filter_peu(self):
        """Test filtering for PEU classes only."""
        classes = get_available_classes("PEU")
        assert all(c.endswith("PEU") for c in classes)
