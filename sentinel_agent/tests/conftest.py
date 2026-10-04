"""Shared fixtures for Outbreak Sentinel tests."""

import os
from pathlib import Path
import tempfile
import pytest

from sentinel_agent.db import init_db
from sentinel_agent.notifier import ConsoleNotifier


@pytest.fixture
def temp_db(tmp_path: Path) -> str:
    """Provides a fresh isolated SQLite database for each test."""
    db_file = str(tmp_path / "test_sentinel.sqlite3")
    init_db(db_file)
    return db_file


@pytest.fixture
def memory_notifier() -> ConsoleNotifier:
    """Provides an in-memory console notifier for asserting alert dispatches."""
    notifier = ConsoleNotifier()
    notifier.clear()
    return notifier
