"""Structured logger with JSONL format and FIFO rotation.

Each log entry is a single JSON object written on one line.
When the current file reaches max_lines, a new file is opened.
When max_files is reached, the oldest file is deleted (FIFO).
"""

from __future__ import annotations

import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path


class StructuredLogger:
    """Thread-safe JSONL logger with file rotation.

    Args:
        log_dir: Directory path for log files.
        max_lines: Max lines per log file before rotation.
        max_files: Max number of log files before oldest is deleted.
    """

    def __init__(
        self,
        log_dir: str = "results/logs",
        max_lines: int = 500,
        max_files: int = 20,
    ) -> None:
        self._log_dir = Path(log_dir)
        self._max_lines = max_lines
        self._max_files = max_files
        self._current_lines = 0
        self._lock = threading.Lock()
        self._current_file: Path | None = None
        self._file_handle = None
        self._log_dir.mkdir(parents=True, exist_ok=True)
        self._open_new_file()

    def _open_new_file(self) -> None:
        """Open a new log file and enforce FIFO rotation."""
        if self._file_handle is not None:
            self._file_handle.close()

        self._enforce_max_files()
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        counter = self._get_next_counter(timestamp)
        filename = f"debate_{timestamp}_{counter:03d}.jsonl"
        self._current_file = self._log_dir / filename
        self._file_handle = open(self._current_file, "a", encoding="utf-8")  # noqa: SIM115
        self._current_lines = 0

    def _get_next_counter(self, timestamp: str) -> int:
        """Get the next counter for the given timestamp prefix."""
        existing = sorted(self._log_dir.glob(f"debate_{timestamp}_*.jsonl"))
        if not existing:
            return 1
        last = existing[-1].stem
        last_counter = int(last.split("_")[-1])
        return last_counter + 1

    def _enforce_max_files(self) -> None:
        """Delete oldest log files if we exceed the max count."""
        log_files = sorted(self._log_dir.glob("debate_*.jsonl"))
        while len(log_files) >= self._max_files:
            oldest = log_files.pop(0)
            os.remove(oldest)

    def _write_entry(self, level: str, agent: str, event: str, data: dict | None) -> None:
        """Write a single JSONL log entry."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level,
            "agent": agent,
            "event": event,
            "data": data or {},
        }
        with self._lock:
            if self._current_lines >= self._max_lines:
                self._open_new_file()
            line = json.dumps(entry, ensure_ascii=False)
            self._file_handle.write(line + "\n")
            self._file_handle.flush()
            self._current_lines += 1

    def debug(self, agent: str, event: str, data: dict | None = None) -> None:
        """Log a DEBUG-level entry."""
        self._write_entry("DEBUG", agent, event, data)

    def info(self, agent: str, event: str, data: dict | None = None) -> None:
        """Log an INFO-level entry."""
        self._write_entry("INFO", agent, event, data)

    def warning(self, agent: str, event: str, data: dict | None = None) -> None:
        """Log a WARNING-level entry."""
        self._write_entry("WARNING", agent, event, data)

    def error(self, agent: str, event: str, data: dict | None = None) -> None:
        """Log an ERROR-level entry."""
        self._write_entry("ERROR", agent, event, data)

    def get_current_file(self) -> Path | None:
        """Return the path to the current log file."""
        return self._current_file

    def close(self) -> None:
        """Close the current log file handle."""
        if self._file_handle is not None:
            self._file_handle.close()
            self._file_handle = None
