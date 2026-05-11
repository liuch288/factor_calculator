"""
Data models for progress tracking.

Defines the structures for task records and log entries.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any


def generate_task_id() -> str:
    """Generate a unique task ID using UUID.
    
    Returns:
        A UUID string for task identification.
    """
    return str(uuid.uuid4())


def generate_log_id() -> str:
    """Generate a unique log ID using UUID.
    
    Returns:
        A UUID string for log entry identification.
    """
    return str(uuid.uuid4())


def utc_now() -> str:
    """Get current local time in ISO format.
    
    Returns:
        ISO format timestamp string.
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def create_task_record(
    contract: str,
    units: str,
    date_range_start: str,
    date_range_end: str,
    frequency: str,
    total_days: int = 1,
) -> Dict[str, Any]:
    """Create a new task record with all required fields.
    
    Args:
        contract: Contract code (e.g., "IF2403")
        units: JSON-serialized unit specifications
        date_range_start: Start date in YYYY-MM-DD format
        date_range_end: End date in YYYY-MM-DD format
        frequency: Data frequency (e.g., "tick", "1min")
        total_days: Total number of days for multi-day mode
    
    Returns:
        TASK_RECORD dict with all fields initialized.
    """
    now = utc_now()
    return {
        "task_id": generate_task_id(),
        "created_at": now,
        "updated_at": now,
        "status": "running",
        "contract": contract,
        "units": units,
        "date_range_start": date_range_start,
        "date_range_end": date_range_end,
        "frequency": frequency,
        "total_days": total_days,
        "completed_days": 0,
        "day_progress": 0,
        "total_progress": 0,
        "started_at": now,
        "completed_at": "",
        "error_message": "",
        "result_summary": "",
    }


def create_log_entry(
    task_id: str,
    level: str,
    message: str,
    context: str = "{}",
) -> Dict[str, Any]:
    """Create a new log entry.
    
    Args:
        task_id: Associated task ID
        level: Log level (INFO/WARNING/ERROR/DEBUG)
        message: Log message content
        context: JSON-serialized context information
    
    Returns:
        LOG_ENTRY dict with all fields.
    """
    return {
        "log_id": generate_log_id(),
        "task_id": task_id,
        "timestamp": utc_now(),
        "level": level,
        "message": message,
        "context": context,
    }


# Type definitions for clarity
TASK_RECORD: Dict[str, Any] = {}

LOG_ENTRY: Dict[str, Any] = {}


def validate_task_record(record: Dict[str, Any]) -> bool:
    """Validate that a task record has all required fields.
    
    Args:
        record: Task record dict to validate
    
    Returns:
        True if valid, False otherwise.
    """
    required_fields = [
        "task_id",
        "created_at",
        "updated_at",
        "status",
        "contract",
        "units",
        "date_range_start",
        "date_range_end",
        "frequency",
        "total_days",
        "completed_days",
        "day_progress",
        "total_progress",
        "started_at",
        "completed_at",
        "error_message",
        "result_summary",
    ]
    return all(field in record for field in required_fields)


def validate_log_entry(entry: Dict[str, Any]) -> bool:
    """Validate that a log entry has all required fields.
    
    Args:
        entry: Log entry dict to validate
    
    Returns:
        True if valid, False otherwise.
    """
    required_fields = [
        "log_id",
        "task_id",
        "timestamp",
        "level",
        "message",
        "context",
    ]
    return all(field in entry for field in required_fields)