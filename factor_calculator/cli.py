#!/usr/bin/env python
"""
Command-line interface for FactorCalculator.

This module provides a CLI tool for calculating factors using DMU and PEU units.
"""

import argparse
import sys
from typing import List, Optional

from .core import FactorCalculator
from .factory import get_available_classes, parse_unit_spec


def list_units(args):
    """List available DMU or PEU classes."""
    suffix = None
    if args.dmu:
        suffix = "DMU"
    elif args.peu:
        suffix = "PEU"
    
    classes = get_available_classes(suffix)
    print(f"Available {suffix or 'Unit'} classes:")
    for cls in classes:
        print(f"  - {cls}")


def calculate(args):
    """Run factor calculation."""
    has_date = args.date is not None
    has_start = args.start_date is not None
    has_end = args.end_date is not None

    # Validate mutual exclusivity
    if has_date and (has_start or has_end):
        print("Error: Cannot use --date with --start-date/--end-date. Use one mode only.")
        sys.exit(1)

    if has_start != has_end:
        print("Error: Both --start-date and --end-date must be provided for multi-day mode.")
        sys.exit(1)

    if not has_date and not has_start:
        print("Error: Must provide either --date or --start-date/--end-date.")
        sys.exit(1)

    # Initialize calculator
    calculator = FactorCalculator(
        db_directory=args.db_directory,
        md_directory=args.md_directory,
    )

    units = args.units.split(",") if args.units else []

    if has_start and has_end:
        # Multi-day mode
        result = calculator.calculate(
            units=units,
            contract=args.contract,
            start_date=args.start_date,
            end_date=args.end_date,
            frequency=args.frequency,
            recalculate=args.recalculate,
            fail_fast=args.fail_fast,
        )
    else:
        # Single-day mode
        result = calculator.calculate(
            units=units,
            contract=args.contract,
            trade_date=args.date,
            frequency=args.frequency,
            recalculate=args.recalculate,
        )

    # Output results
    if args.output:
        result.to_pickle(args.output)
        print(f"Results saved to {args.output}")
    else:
        print(result.head())


def show_factors(args):
    """Show existing factors in the database."""
    calculator = FactorCalculator(db_directory=args.db_directory)
    
    factors = calculator.get_existing_factors(
        contract=args.contract,
        trade_date=args.date,
    )
    
    print(f"Existing factors for {args.contract} on {args.date}:")
    for f in factors:
        print(f"  - {f}")


def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="FactorCalculator CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List available units")
    list_parser.add_argument(
        "--dmu", action="store_true", help="List only DMU classes"
    )
    list_parser.add_argument(
        "--peu", action="store_true", help="List only PEU classes"
    )
    
    # Calculate command
    calc_parser = subparsers.add_parser(
        "calculate", help="Calculate factors"
    )
    calc_parser.add_argument(
        "--db", dest="db_directory", required=True,
        help="Directory containing result database"
    )
    calc_parser.add_argument(
        "--md", dest="md_directory",
        help="Directory containing market data"
    )
    calc_parser.add_argument(
        "--units", required=True,
        help="Comma-separated list of unit specifications"
    )
    calc_parser.add_argument(
        "--contract", required=True,
        help="Contract symbol (e.g., IF2403)"
    )
    calc_parser.add_argument(
        "--date",
        help="Trade date (YYYY-MM-DD)"
    )
    calc_parser.add_argument(
        "--start-date",
        help="Start date for multi-day mode (YYYY-MM-DD)"
    )
    calc_parser.add_argument(
        "--end-date",
        help="End date for multi-day mode (YYYY-MM-DD)"
    )
    calc_parser.add_argument(
        "--fail-fast", action="store_true",
        help="Stop immediately on first daily calculation failure"
    )
    calc_parser.add_argument(
        "--frequency", default="tick",
        help="Data frequency (default: tick)"
    )
    calc_parser.add_argument(
        "--recalculate", action="store_true",
        help="Recalculate existing factors"
    )
    calc_parser.add_argument(
        "-o", "--output",
        help="Output file for results (pickle format)"
    )
    
    # Show factors command
    show_parser = subparsers.add_parser(
        "factors", help="Show existing factors"
    )
    show_parser.add_argument(
        "--db", dest="db_directory", required=True,
        help="Directory containing result database"
    )
    show_parser.add_argument(
        "--contract", required=True,
        help="Contract symbol"
    )
    show_parser.add_argument(
        "--date", required=True,
        help="Trade date (YYYY-MM-DD)"
    )
    
    return parser.parse_args(args)


def main(args: Optional[List[str]] = None) -> int:
    """Main entry point."""
    args = parse_args(args)
    
    if args.command == "list":
        list_units(args)
    elif args.command == "calculate":
        calculate(args)
    elif args.command == "factors":
        show_factors(args)
    else:
        print("Error: No command specified. Use -h for help.")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
