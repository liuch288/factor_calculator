"""
ProgressTracker for managing calculation task progress.

Provides persistent storage and tracking of factor calculation tasks,
including progress updates, logging, and task lifecycle management.

Storage structure:
    {storage_path}/
        {task_id}/
            task.json    - Task record
            logs.jsonl   - Log entries
"""

import json
import logging
import os
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple

from factor_calculator.progress.models import (
    create_task_record,
    create_log_entry,
    get_time_str,
    validate_task_record,
)

logger = logging.getLogger(__name__)


class ProgressTracker:
    """Track and persist progress of factor calculation tasks.
    
    Each task gets its own directory to avoid multiprocessing conflicts:
        {storage_path}/{task_id}/
            task.json    - Task record
            logs.jsonl   - Log entries
    """

    def __init__(self, storage_path: str = None):
        """Initialize storage directory.
        
        Args:
            storage_path: Base path for storing progress data. 
                         Defaults to '~/.fc/progress'.
            Each task will create its own subdirectory: {storage_path}/{task_id}/
            This avoids multiprocess concurrent writing to the same file.
        """
        self.storage_path = None
        self._available = False
        
        try:
            default_path = Path.home() / ".fc" / "progress"
            self.storage_path = Path(storage_path) if storage_path else default_path
            self.storage_path.mkdir(parents=True, exist_ok=True)
            self._available = True
        except Exception as e:
            logger.warning(f"Progress tracker storage initialization failed: {e}")
            self._available = False
    
    def _get_task_dir(self, task_id: str) -> Path:
        """Get task directory path.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Path to the task directory
        """
        return self.storage_path / task_id
    
    def _get_task_file(self, task_id: str) -> Path:
        """Get task.json file path.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Path to task.json
        """
        return self._get_task_dir(task_id) / "task.json"
    
    def _get_logs_file(self, task_id: str) -> Path:
        """Get logs.jsonl file path.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Path to logs.jsonl
        """
        return self._get_task_dir(task_id) / "logs.jsonl"
    
    def _ensure_task_dir(self, task_id: str) -> None:
        """Ensure task directory exists.
        
        Args:
            task_id: Task identifier
        """
        if not self._available:
            raise IOError("Storage not available")
        self._get_task_dir(task_id).mkdir(parents=True, exist_ok=True)
    
    @property
    def is_available(self) -> bool:
        """Check if the tracker storage is available.
        
        Returns:
            True if storage is available, False otherwise.
        """
        return self._available

    def _read_json(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Read a single JSON record from a file.
        
        Args:
            file_path: Path to the JSON file
            
        Returns:
            Dictionary content or None if not found
        """
        if not self._available:
            return None
        
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None

    def _write_json(self, file_path: Path, data: Dict[str, Any]) -> None:
        """Write a JSON record to a file.
        
        Args:
            file_path: Path to the JSON file
            data: Dictionary to serialize
        """
        if not self._available:
            raise IOError("Storage not available")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _append_to_jsonl(self, file_path: Path, data: Dict[str, Any]) -> None:
        """Append a JSON record to a JSON Lines file.
        
        Args:
            file_path: Path to the JSON Lines file
            data: Dictionary to serialize and append
        """
        if not self._available:
            raise IOError("Storage not available")
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(data, ensure_ascii=False) + "\n")

    def _read_jsonl(self, file_path: Path) -> List[Dict[str, Any]]:
        """Read all records from a JSON Lines file.
        
        Args:
            file_path: Path to the JSON Lines file
            
        Returns:
            List of dictionaries, one per line
        """
        if not self._available:
            return []
        
        if not file_path.exists():
            return []
        
        records = []
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError:
                        # Skip invalid lines
                        continue
        return records

    def start_task(
        self,
        units: str,
        contract: str,
        date_range: Tuple[str, str],
        frequency: str,
        total_days: int = None,
        task_id: str = None,
    ) -> str:
        """Start tracking a new task.
        
        Creates a task record with running status and creates the task directory.
        
        Args:
            units: JSON-serialized unit specifications string
            contract: Contract code (e.g., "IF2403")
            date_range: Tuple of (start_date, end_date) in YYYY-MM-DD format
            frequency: Data frequency (e.g., "tick", "1min")
            total_days: Total number of days for multi-day mode
            task_id: Custom task ID (optional, will be auto-generated if not provided)
            
        Returns:
            The task_id (generated or provided)
        """
        # Generate task_id if not provided
        from factor_calculator.progress.models import generate_task_id
        if not task_id:
            task_id = generate_task_id()
        
        # Default total_days to 1 if not provided
        if total_days is None:
            total_days = 1
        
        # Create task directory
        try:
            self._ensure_task_dir(task_id)
        except Exception as e:
            logger.warning(f"Failed to create task directory: {e}")
        
        # Create task record
        units_json = json.dumps(units, ensure_ascii=False)
        record = create_task_record(
            contract=contract,
            units=units_json,
            date_range_start=date_range[0],
            date_range_end=date_range[1],
            frequency=frequency,
            total_days=total_days,
        )
        
        # Override the generated task_id with the provided one if specified
        if task_id:
            record["task_id"] = task_id
        
        # Persist to task.json
        try:
            task_file = self._get_task_file(task_id)
            self._write_json(task_file, record)
        except Exception as e:
            logger.warning(f"Failed to persist task record: {e}")
        
        return record["task_id"]

    def update_progress(
        self,
        task_id: str,
        current_day: int,
        total_days: int,
        day_progress: int = None,
        message: str = None,
    ) -> None:
        """Update task progress.
        
        Calculates total_progress using the formula:
        total_progress = (completed_days / total_days) * 100 + (day_progress / total_days)
        
        Args:
            task_id: The task ID to update
            current_day: Current day number (1-based)
            total_days: Total number of days
            day_progress: Progress percentage for current day (0-100)
            message: Optional progress message
        """
        # Default day_progress to 0 if not provided
        if day_progress is None:
            day_progress = 0
        
        # Calculate completed_days (all processed days, including current)
        completed_days = current_day
        
        # Calculate total_progress
        # Formula: (completed_days / total_days) * 100 + (day_progress / total_days)
        progress = (completed_days / total_days) * 100 + (day_progress / total_days)
        total_progress = round(progress, 2)
        
        # Clamp total_progress to 100
        total_progress = min(total_progress, 100)
        
        # Update the task record
        updates = {
            "current_day": current_day,
            "total_days": total_days,
            "completed_days": completed_days,
            "day_progress": day_progress,
            "total_progress": total_progress,
            "updated_at": get_time_str(),
        }
        
        if message:
            updates["progress_message"] = message
        
        try:
            task_file = self._get_task_file(task_id)
            task = self._read_json(task_file)
            if not task:
                logger.warning(f"Task not found for update: {task_id}")
                return
            
            task.update(updates)
            self._write_json(task_file, task)
        except Exception as e:
            logger.warning(f"Failed to update progress: {e}")

    def log(self, task_id: str, level: str, message: str) -> None:
        """Add a log entry.
        
        Args:
            task_id: Associated task ID
            level: Log level (INFO/WARNING/ERROR/DEBUG)
            message: Log message content
        """
        # Ensure task directory exists (task may have been created externally)
        try:
            task_dir = self._get_task_dir(task_id)
            if not task_dir.exists():
                logger.warning(f"Task directory not found for logging: {task_id}")
        except Exception as e:
            logger.warning(f"Failed to check task directory: {e}")
        
        # Create and persist log entry
        entry = create_log_entry(
            task_id=task_id,
            level=level.upper(),
            message=message,
        )
        
        try:
            logs_file = self._get_logs_file(task_id)
            self._append_to_jsonl(logs_file, entry)
        except Exception as e:
            logger.warning(f"Failed to persist log entry: {e}")

    def complete_task(
        self,
        task_id: str,
        status: str,
        result_summary: dict = None,
    ) -> None:
        """Mark a task as completed.
        
        Args:
            task_id: The task ID to complete
            status: Final status (success/failed/cancelled)
            result_summary: Optional summary of results
        """
        # Prepare updates
        updates = {
            "status": status,
            "completed_at": get_time_str(),
            "updated_at": get_time_str(),
        }
        
        if result_summary:
            updates["result_summary"] = json.dumps(result_summary, ensure_ascii=False)
        
        try:
            task_file = self._get_task_file(task_id)
            task = self._read_json(task_file)
            if not task:
                logger.warning(f"Task not found for completion: {task_id}")
                return
            
            task.update(updates)
            self._write_json(task_file, task)
        except Exception as e:
            logger.warning(f"Failed to complete task: {e}")

    def get_task(self, task_id: str) -> Optional[dict]:
        """Get task details by ID.
        
        Args:
            task_id: The task ID to retrieve
            
        Returns:
            Task record dictionary, or None if not found
        """
        try:
            task_file = self._get_task_file(task_id)
            return self._read_json(task_file)
        except Exception as e:
            logger.warning(f"Failed to get task: {e}")
            return None

    def list_tasks(
        self,
        contract: str = None,
        start_date: str = None,
        end_date: str = None,
        status: str = None,
        limit: int = 50,
    ) -> List[dict]:
        """Query tasks with optional filters.
        
        Scans all subdirectories in storage_path to find task records.
        
        Args:
            contract: Filter by contract code
            start_date: Filter by start date (YYYY-MM-DD)
            end_date: Filter by end date (YYYY-MM-DD)
            status: Filter by status (running/success/failed/cancelled)
            limit: Maximum number of results to return
            
        Returns:
            List of task records, sorted by created_at descending
        """
        if not self._available:
            return []
        
        tasks = []
        
        # Scan all subdirectories in storage_path
        try:
            for item in self.storage_path.iterdir():
                if item.is_dir():
                    task_file = item / "task.json"
                    if task_file.exists():
                        task = self._read_json(task_file)
                        if task:
                            tasks.append(task)
        except Exception as e:
            logger.warning(f"Failed to scan task directories: {e}")
            return []
        
        # Apply filters
        filtered = []
        for task in tasks:
            # Filter by contract
            if contract and task.get("contract") != contract:
                continue
            
            # Filter by status
            if status and task.get("status") != status:
                continue
            
            # Filter by date range
            if start_date and task.get("date_range_start", "") < start_date:
                continue
            if end_date and task.get("date_range_end", "") > end_date:
                continue
            
            filtered.append(task)
        
        # Sort by created_at descending (most recent first)
        filtered.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        # Apply limit
        return filtered[:limit]

    def get_logs(self, task_id: str) -> List[dict]:
        """Get all log entries for a task.
        
        Args:
            task_id: The task ID to get logs for
            
        Returns:
            List of log entries, sorted by timestamp ascending
        """
        try:
            logs_file = self._get_logs_file(task_id)
            all_logs = self._read_jsonl(logs_file)
            
            # Sort by timestamp ascending
            all_logs.sort(key=lambda x: x.get("timestamp", ""))
            
            return all_logs
        except Exception as e:
            logger.warning(f"Failed to get logs: {e}")
            return []