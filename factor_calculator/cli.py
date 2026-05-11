#!/usr/bin/env python
"""
Command-line interface for FactorCalculator.

This module provides a CLI tool for calculating factors using DMU and PEU units.
"""

import argparse
import json
import sys
from typing import List, Optional

from .core import FactorCalculator
from .factory import get_available_classes, parse_unit_spec
from .progress import ProgressTracker


def _split_units(raw: str) -> List[str]:
    """Split a comma-separated units string, respecting parentheses.

    E.g. "MoSplitDMU,BiquotePEU(600,1,1)" -> ["MoSplitDMU", "BiquotePEU(600,1,1)"]
    """
    units = []
    depth = 0
    current: List[str] = []
    for ch in raw:
        if ch == "(":
            depth += 1
            current.append(ch)
        elif ch == ")":
            depth -= 1
            current.append(ch)
        elif ch == "," and depth == 0:
            units.append("".join(current).strip())
            current = []
        else:
            current.append(ch)
    if current:
        units.append("".join(current).strip())
    return [u for u in units if u]


def list_units(args):
    """List available DMU or PEU classes."""
    if args.dmu:
        classes = get_available_classes("DMU")
        print("Available DMU classes:")
        for cls in classes:
            print(f"  - {cls}")
    elif args.peu:
        classes = get_available_classes("PEU")
        print("Available PEU classes:")
        for cls in classes:
            print(f"  - {cls}")
    else:
        dmu_classes = get_available_classes("DMU")
        peu_classes = get_available_classes("PEU")
        print("Available DMU classes:")
        for cls in dmu_classes:
            print(f"  - {cls}")
        print()
        print("Available PEU classes:")
        for cls in peu_classes:
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

    units = _split_units(args.units) if args.units else []

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
            show_progress=not args.no_progress,
        )
    else:
        # Single-day mode
        result = calculator.calculate(
            units=units,
            contract=args.contract,
            trade_date=args.date,
            frequency=args.frequency,
            recalculate=args.recalculate,
            show_progress=not args.no_progress,
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


def progress_list(args):
    """List calculation tasks with optional filters."""
    tracker = ProgressTracker(storage_path=args.storage)
    
    tasks = tracker.list_tasks(
        contract=args.contract,
        start_date=args.start_date,
        end_date=args.end_date,
        status=args.status,
        limit=args.limit,
    )
    
    if not tasks:
        print("No tasks found.")
        return
    
    # Output: task_id, contract, status, progress%, started_at
    print(f"{'TASK_ID':<40} {'CONTRACT':<12} {'STATUS':<10} {'PROGRESS':<10} {'STARTED_AT':<20}")
    print("-" * 95)
    
    for task in tasks:
        task_id = task.get("task_id", "")[:38]
        contract = task.get("contract", "")[:10]
        status = task.get("status", "")[:8]
        progress = f"{task.get('total_progress', 0):.1f}%"
        started_at = task.get("started_at", "")[:19]
        
        print(f"{task_id:<40} {contract:<12} {status:<10} {progress:<10} {started_at:<20}")


def progress_show(args):
    """Show detailed task information."""
    tracker = ProgressTracker(storage_path=args.storage)
    
    task = tracker.get_task(args.task_id)
    
    if not task:
        print(f"Task not found: {args.task_id}")
        sys.exit(1)
    
    print(f"Task ID: {task.get('task_id')}")
    print(f"Contract: {task.get('contract')}")
    print(f"Status: {task.get('status')}")
    print(f"Date Range: {task.get('date_range_start')} to {task.get('date_range_end')}")
    print(f"Frequency: {task.get('frequency')}")
    print(f"Units: {task.get('units')}")
    print(f"Progress: {task.get('total_progress', 0):.1f}%")
    print(f"  - Completed Days: {task.get('completed_days', 0)}/{task.get('total_days', 1)}")
    print(f"Created: {task.get('created_at')}")
    print(f"Started: {task.get('started_at')}")
    
    if task.get("completed_at"):
        print(f"Completed: {task.get('completed_at')}")
    
    if task.get("error_message"):
        print(f"Error: {task.get('error_message')}")
    
    # Show result_summary if available
    result_summary = task.get("result_summary")
    if result_summary and result_summary.strip():
        try:
            summary = json.loads(result_summary)
            print(f"Result Summary:")
            for key, value in summary.items():
                print(f"  - {key}: {value}")
        except (json.JSONDecodeError, AttributeError):
            print(f"Result Summary: {result_summary}")


def progress_logs(args):
    """Show all log entries for a task."""
    tracker = ProgressTracker(storage_path=args.storage)
    
    # First check if task exists
    task = tracker.get_task(args.task_id)
    if not task:
        print(f"Task not found: {args.task_id}")
        sys.exit(1)
    
    logs = tracker.get_logs(args.task_id)
    
    if not logs:
        print("No log entries found.")
        return
    
    # Output: timestamp, level, message
    print(f"{'TIMESTAMP':<24} {'LEVEL':<10} MESSAGE")
    print("-" * 80)
    
    for log in logs:
        timestamp = log.get("timestamp", "")[:22]
        level = log.get("level", "")[:8]
        message = log.get("message", "")
        
        print(f"{timestamp:<24} {level:<10} {message}")


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
        "--db", dest="db_directory", default=None,
        help="Directory containing result database (default: use framework default)"
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
    calc_parser.add_argument(
        "--no-progress", action="store_true",
        help="Disable tick-level progress bar"
    )
    
    # Show factors command
    show_parser = subparsers.add_parser(
        "factors", help="Show existing factors"
    )
    show_parser.add_argument(
        "--db", dest="db_directory", default=None,
        help="Directory containing result database (default: use framework default)"
    )
    show_parser.add_argument(
        "--contract", required=True,
        help="Contract symbol"
    )
    show_parser.add_argument(
        "--date", required=True,
        help="Trade date (YYYY-MM-DD)"
    )
    
    # Progress subcommand group
    progress_parser = subparsers.add_parser(
        "progress", help="Manage calculation progress"
    )
    progress_subparsers = progress_parser.add_subparsers(
        dest="progress_command", help="Progress commands"
    )
    
    # Progress list command
    list_parser = progress_subparsers.add_parser(
        "list", help="List calculation tasks"
    )
    list_parser.add_argument(
        "--storage", default=None,
        help="Storage path for progress data (default: .progress)"
    )
    list_parser.add_argument(
        "--contract",
        help="Filter by contract code (e.g., IF2403)"
    )
    list_parser.add_argument(
        "--status",
        help="Filter by status (running/success/failed/cancelled)"
    )
    list_parser.add_argument(
        "--start-date",
        help="Filter by start date (YYYY-MM-DD)"
    )
    list_parser.add_argument(
        "--end-date",
        help="Filter by end date (YYYY-MM-DD)"
    )
    list_parser.add_argument(
        "--limit", type=int, default=50,
        help="Maximum number of results (default: 50)"
    )
    
    # Progress show command
    show_progress_parser = progress_subparsers.add_parser(
        "show", help="Show task details"
    )
    show_progress_parser.add_argument(
        "--storage", default=None,
        help="Storage path for progress data (default: .progress)"
    )
    show_progress_parser.add_argument(
        "task_id",
        help="Task ID to display"
    )
    
    # Progress logs command
    logs_parser = progress_subparsers.add_parser(
        "logs", help="Show task logs"
    )
    logs_parser.add_argument(
        "--storage", default=None,
        help="Storage path for progress data (default: .progress)"
    )
    logs_parser.add_argument(
        "task_id",
        help="Task ID to show logs for"
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
    elif args.command == "progress":
        if args.progress_command == "list":
            progress_list(args)
        elif args.progress_command == "show":
            progress_show(args)
        elif args.progress_command == "logs":
            progress_logs(args)
        else:
            print("Error: No progress command specified. Use -h for help.")
            return 1
    else:
        print("Error: No command specified. Use -h for help.")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
