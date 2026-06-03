"""Shared fixtures for all backend tests"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.models.oauth.user import User
from src.models.repository.issue import Issue
from src.models.repository.repository import Repository
from src.utils.auth import get_current_user


class MockNeo4jResult(list):
    """A list that can be awaited — supports both sync and async execute_query calls."""

    def __await__(self):
        async def _await():
            return self
        return _await().__await__()


class MockNeo4jDB:
    """Fake Neo4jConnection that returns controllable results."""

    def __init__(self):
        self.results: list[Any] = []
        self.executed_queries: list[tuple[str, dict | None]] = []

    def execute_query(self, query: str, params: dict | None = None) -> MockNeo4jResult:
        self.executed_queries.append((query, params))
        if self.results:
            return MockNeo4jResult(self.results.pop(0))
        return MockNeo4jResult([])

    def add_result(self, data: list[dict[str, Any]]):
        self.results.append(data)

    def connect(self):
        pass

    def close(self):
        pass

    def verify_connectivity(self):
        return True


@pytest.fixture
def mock_db():
    return MockNeo4jDB()


@pytest.fixture
def mock_user():
    return User(
        id="user-1",
        username="testuser",
        email="test@example.com",
        github_id=12345,
        github_token="gh_token_test",
        is_active=True,
    )


@pytest.fixture
def sample_repo_row():
    return {
        "n": {
            "id": "repo-1",
            "name": "test-repo",
            "full_name": "testuser/test-repo",
            "description": "A test repo",
            "owner_username": "testuser",
            "github_id": 1001,
            "default_branch": "main",
            "is_private": False,
            "github_created_at": "2024-01-01T00:00:00Z",
            "github_pushed_at": "2024-06-01T00:00:00Z",
            "open_issues_count": 0,
        }
    }


@pytest.fixture
def sample_repo(sample_repo_row):
    return Repository(**sample_repo_row["n"])


@pytest.fixture
def sample_issue_row():
    return {
        "n": {
            "id": "issue-1",
            "name": "Test Issue",
            "description": "A test issue",
            "repository_id": "repo-1",
            "author_username": "testuser",
            "github_id": 2001,
            "github_issue_number": 42,
            "github_issue_url": "https://github.com/testuser/test-repo/issues/42",
            "status": "open",
            "priority": "medium",
            "issue_type": "feature",
            "assigned_to_copilot": False,
        }
    }


@pytest.fixture
def sample_issue(sample_issue_row):
    return Issue(**sample_issue_row["n"])


@pytest.fixture
def mock_httpx_client():
    """Patch httpx.AsyncClient so all GitHub API calls return controlled data."""
    with patch("httpx.AsyncClient") as mock:
        client_instance = AsyncMock()
        mock.return_value.__aenter__.return_value = client_instance
        yield client_instance


_app_instance = None


@pytest.fixture(scope="session")
def _real_app():
    """Import the real FastAPI app once at session scope."""
    from main import app as _app

    return _app


@pytest.fixture
def app(_real_app, mock_db: MockNeo4jDB, mock_user: User):
    """FastAPI app with mocked Neo4j and authentication for testing."""
    from src.database import get_db

    _real_app.dependency_overrides.clear()
    _real_app.dependency_overrides[get_db] = lambda: mock_db
    _real_app.dependency_overrides[get_current_user] = lambda: mock_user
    yield _real_app
    _real_app.dependency_overrides.clear()


@pytest.fixture
def client(app):
    return TestClient(app, raise_server_exceptions=False)
