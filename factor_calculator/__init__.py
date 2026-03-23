"""
FactorCalculator - A tool for calculating trading factors using DMU and PEU units.

This package provides utilities for:
- Parsing unit specifications like "KlineDMU(45)" or "BiquotePEU(watching_time=60)"
- Dynamically creating DMU and PEU instances
- Running factor calculations with previous result injection
- Managing factor results in a database
"""

from .core import FactorCalculator
from .factory import (
    create_unit,
    create_units,
    get_available_classes,
    parse_unit_spec,
    parse_parameters,
    parse_value,
)

__version__ = "0.1.0"

__all__ = [
    "FactorCalculator",
    "create_unit",
    "create_units",
    "get_available_classes",
    "parse_unit_spec",
    "parse_parameters",
    "parse_value",
]
