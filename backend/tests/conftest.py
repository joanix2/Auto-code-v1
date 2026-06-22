"""Shared fixtures for backend tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def mock_db():
    from unittest.mock import MagicMock

    return MagicMock()


@pytest.fixture
def client():
    from main import app

    return TestClient(app, raise_server_exceptions=False)
