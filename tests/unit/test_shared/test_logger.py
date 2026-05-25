"""Tests for debate.shared.logger — StructuredLogger."""

import json

from debate.shared.logger import StructuredLogger


class TestStructuredLogger:
    """Tests for StructuredLogger with JSONL and FIFO rotation."""

    def test_log_entry_is_valid_jsonl(self, tmp_path):
        logger = StructuredLogger(str(tmp_path / "logs"), max_lines=100, max_files=5)
        logger.info("test_agent", "test_event", {"key": "value"})
        logger.close()

        log_files = list((tmp_path / "logs").glob("*.jsonl"))
        assert len(log_files) == 1
        with open(log_files[0]) as f:
            line = f.readline()
            entry = json.loads(line)
            assert entry["level"] == "INFO"
            assert entry["agent"] == "test_agent"
            assert entry["event"] == "test_event"
            assert entry["data"] == {"key": "value"}
            assert "timestamp" in entry

    def test_fifo_rotation_at_max_lines(self, tmp_path):
        logger = StructuredLogger(str(tmp_path / "logs"), max_lines=5, max_files=20)
        for i in range(12):
            logger.info("agent", f"event_{i}")
        logger.close()

        log_files = list((tmp_path / "logs").glob("*.jsonl"))
        assert len(log_files) >= 2  # Should have rotated at least once

    def test_max_files_enforced(self, tmp_path):
        logger = StructuredLogger(str(tmp_path / "logs"), max_lines=2, max_files=3)
        for i in range(20):
            logger.info("agent", f"event_{i}")
        logger.close()

        log_files = list((tmp_path / "logs").glob("*.jsonl"))
        assert len(log_files) <= 3

    def test_log_levels(self, tmp_path):
        logger = StructuredLogger(str(tmp_path / "logs"), max_lines=100, max_files=5)
        logger.debug("a", "d")
        logger.info("a", "i")
        logger.warning("a", "w")
        logger.error("a", "e")
        logger.close()

        log_file = list((tmp_path / "logs").glob("*.jsonl"))[0]
        with open(log_file) as f:
            lines = f.readlines()
        levels = [json.loads(line)["level"] for line in lines]
        assert levels == ["DEBUG", "INFO", "WARNING", "ERROR"]

    def test_creates_log_directory(self, tmp_path):
        log_dir = tmp_path / "nested" / "logs"
        assert not log_dir.exists()
        logger = StructuredLogger(str(log_dir), max_lines=100, max_files=5)
        logger.info("agent", "test")
        logger.close()
        assert log_dir.exists()

    def test_get_current_file(self, tmp_path):
        logger = StructuredLogger(str(tmp_path / "logs"), max_lines=100, max_files=5)
        current = logger.get_current_file()
        assert current is not None
        assert current.suffix == ".jsonl"
        logger.close()
