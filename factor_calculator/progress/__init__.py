"""
Progress tracking module for factor calculation.

This module provides functionality to track and persist calculation progress,
including task records, progress updates, and log entries.
"""

from factor_calculator.progress.models import (
    TASK_RECORD,
    LOG_ENTRY,
    generate_task_id,
    generate_log_id,
    utc_now,
    create_task_record,
    create_log_entry,
    validate_task_record,
    validate_log_entry,
)

# Import tracker if available (may not exist yet)
try:
    from factor_calculator.progress.tracker import ProgressTracker
    __all__ = [
        "TASK_RECORD",
        "LOG_ENTRY", 
        "generate_task_id",
        "generate_log_id",
        "utc_now",
        "create_task_record",
        "create_log_entry",
        "validate_task_record",
        "validate_log_entry",
        "ProgressTracker",
    ]
except ImportError:
    __all__ = [
        "TASK_RECORD",
        "LOG_ENTRY",
        "generate_task_id",
        "generate_log_id",
        "utc_now",
        "create_task_record",
        "create_log_entry",
        "validate_task_record",
        "validate_log_entry",
    ]