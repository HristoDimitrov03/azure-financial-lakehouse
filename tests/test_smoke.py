"""Smoke tests — prove the repo imports cleanly (Sprint 0)."""

from src.utils.logging_config import get_logger


def test_get_logger_returns_logger():
    logger = get_logger("test")
    assert logger.name == "test"
