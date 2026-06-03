"""Tests for service-layer business logic with mocked repositories and httpx."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from src.services.repository.copilot_agent_service import GitHubCopilotAgentService
from src.services.repository.issue_service import IssueService
from src.services.repository.repository_service import RepositoryService
from src.services.repository.message_service import MessageService
from src.services.oauth.user_service import UserService


# ---------------------------------------------------------------------------
# Copilot Agent Service
# ---------------------------------------------------------------------------


class TestGitHubCopilotAgentService:
    @pytest.fixture
    def service(self):
        return GitHubCopilotAgentService(github_token="fake_token")

    @pytest.fixture
    def mock_async_client(self):
        with patch("httpx.AsyncClient") as m:
            client = AsyncMock()
            m.return_value.__aenter__.return_value = client
            yield client

    async def test_assign_issue_to_copilot_success(self, service, mock_async_client):
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "assignees": [{"login": "copilot-swe-agent[bot]"}],
        }
        mock_async_client.post.return_value = mock_response

        result = await service.assign_issue_to_copilot(
            owner="testuser",
            repo="test-repo",
            issue_number=42,
        )

        assert result["success"] is True
        assert result["issue_number"] == 42
        assert "copilot-swe-agent" in result["assignees"][0]["login"]

    async def test_assign_issue_to_copilot_http_error(self, service, mock_async_client):
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Bad request", request=MagicMock(), response=MagicMock()
        )
        mock_response.text = "Not Found"
        mock_async_client.post.return_value = mock_response

        with pytest.raises(Exception, match="Failed to assign issue"):
            await service.assign_issue_to_copilot(owner="u", repo="r", issue_number=1)

    async def test_create_issue_and_assign_success(self, service, mock_async_client):
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "number": 42,
            "html_url": "https://github.com/u/r/issues/42",
            "title": "Test",
            "assignees": [{"login": "copilot-swe-agent[bot]"}],
        }
        mock_async_client.post.return_value = mock_response

        result = await service.create_issue_and_assign_to_copilot(
            owner="u",
            repo="r",
            title="Test",
            body="desc",
        )

        assert result["success"] is True
        assert result["issue_number"] == 42

    async def test_check_copilot_agent_status_enabled(self, service, mock_async_client):
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "data": {
                "repository": {
                    "suggestedActors": {
                        "nodes": [
                            {"login": "copilot-swe-agent", "__typename": "Bot"},
                        ]
                    }
                }
            }
        }
        mock_async_client.post.return_value = mock_response

        result = await service.check_copilot_agent_status(owner="u", repo="r")

        assert result["enabled"] is True

    async def test_check_copilot_agent_status_disabled(self, service, mock_async_client):
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "data": {
                "repository": {
                    "suggestedActors": {
                        "nodes": [{"login": "some-other-bot", "__typename": "Bot"}],
                    }
                }
            }
        }
        mock_async_client.post.return_value = mock_response

        result = await service.check_copilot_agent_status(owner="u", repo="r")

        assert result["enabled"] is False

    async def test_check_copilot_agent_status_graphql_error(self, service, mock_async_client):
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "errors": [{"message": "Not found"}],
        }
        mock_async_client.post.return_value = mock_response

        result = await service.check_copilot_agent_status(owner="u", repo="r")

        assert result["enabled"] is False
        assert "Error" in result["message"]

    async def test_check_copilot_agent_status_404(self, service, mock_async_client):
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "404", request=MagicMock(), response=MagicMock(status_code=404)
        )
        mock_async_client.post.return_value = mock_response

        result = await service.check_copilot_agent_status(owner="u", repo="r")

        assert result["enabled"] is False
        assert "not available" in result["message"]

    async def test_get_pull_request_from_issue_found(self, service, mock_async_client):
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = [
            {
                "event": "cross-referenced",
                "source": {
                    "type": "issue",
                    "issue": {
                        "number": 100,
                        "html_url": "https://github.com/u/r/pull/100",
                        "title": "PR Title",
                        "state": "open",
                        "created_at": "2024-01-01T00:00:00Z",
                        "pull_request": {},
                    },
                },
            }
        ]
        mock_async_client.get.return_value = mock_response

        result = await service.get_pull_request_from_issue(owner="u", repo="r", issue_number=42)

        assert result is not None
        assert result["number"] == 100

    async def test_get_pull_request_from_issue_not_found(self, service, mock_async_client):
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = [
            {"event": "mentioned", "source": {"type": "issue", "issue": {}}}
        ]
        mock_async_client.get.return_value = mock_response

        result = await service.get_pull_request_from_issue(owner="u", repo="r", issue_number=42)

        assert result is None


# ---------------------------------------------------------------------------
# Repository Service
# ---------------------------------------------------------------------------


class TestRepositoryService:
    @pytest.fixture
    def mock_repo_repo(self):
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_repo_repo):
        return RepositoryService(mock_repo_repo)

    async def test_create_in_db_calls_repo(self, service, mock_repo_repo):
        mock_repo_repo.create.return_value = MagicMock(id="repo-1")
        result = await service._create_in_db({"name": "test"})
        assert result.id == "repo-1"
        mock_repo_repo.create.assert_called_once_with({"name": "test"})

    async def test_get_by_id(self, service, mock_repo_repo):
        mock_repo_repo.get_by_id.return_value = MagicMock(id="repo-1")
        result = await service.get_by_id("repo-1")
        assert result.id == "repo-1"

    async def test_sync_from_github(self, service, mock_repo_repo):
        mock_repo_repo.get_by_github_id.return_value = None
        mock_repo_repo.create.return_value = MagicMock(id="repo-1001", full_name="u/r")

        with patch("httpx.AsyncClient") as m:
            client = AsyncMock()
            m.return_value.__aenter__.return_value = client
            resp = MagicMock()
            resp.raise_for_status = MagicMock()
            resp.json.return_value = [
                {"id": 1001, "owner": {"login": "u"}, "name": "r", "full_name": "u/r", "private": False, "default_branch": "main", "created_at": "now", "pushed_at": "now", "description": None}
            ]
            client.get.return_value = resp

            results = await service.sync_from_github("token", username="u")
            assert len(results) == 1

    async def test_create_on_github_success(self, service, mock_repo_repo):
        with patch("httpx.AsyncClient") as m:
            client = AsyncMock()
            m.return_value.__aenter__.return_value = client
            resp = MagicMock()
            resp.raise_for_status = MagicMock()
            resp.json.return_value = {"id": 99, "name": "new-repo", "owner": {"login": "u"}, "full_name": "u/new-repo", "private": False, "default_branch": "main", "created_at": "now", "pushed_at": "now", "description": None}
            client.post.return_value = resp

            result = await service.create_on_github(access_token="tok", name="new-repo")
            assert result["id"] == 99


# ---------------------------------------------------------------------------
# Issue Service
# ---------------------------------------------------------------------------


class TestIssueService:
    @pytest.fixture
    def mock_issue_repo(self):
        return AsyncMock()

    @pytest.fixture
    def mock_repo_repo(self):
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_issue_repo, mock_repo_repo):
        return IssueService(mock_issue_repo, mock_repo_repo)

    async def test_create_issue_calls_github_then_db(self, service, mock_issue_repo):
        mock_issue_repo.create.return_value = MagicMock(id="issue-1")

        with patch("httpx.AsyncClient") as m:
            client = AsyncMock()
            m.return_value.__aenter__.return_value = client
            resp = MagicMock()
            resp.raise_for_status = MagicMock()
            resp.json.return_value = {
                "id": 2001,
                "number": 42,
                "title": "Test",
                "body": "desc",
                "state": "open",
                "html_url": "https://github.com/u/r/issues/42",
                "labels": [],
                "user": {"login": "u"},
            }
            client.post.return_value = resp

            result = await service.create({
                "access_token": "tok",
                "repository_full_name": "u/r",
                "title": "Test",
                "description": "desc",
                "repository_id": "repo-1",
                "author_username": "u",
            })
            assert result.id == "issue-1"

    async def test_get_by_repository(self, service, mock_issue_repo):
        mock_issue_repo.get_by_repository.return_value = [MagicMock(id="i1")]
        results = await service.get_by_repository("repo-1")
        assert len(results) == 1


# ---------------------------------------------------------------------------
# Message Service
# ---------------------------------------------------------------------------


class TestMessageService:
    @pytest.fixture
    def mock_msg_repo(self):
        return AsyncMock()

    @pytest.fixture
    def mock_issue_repo(self):
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_msg_repo, mock_issue_repo):
        return MessageService(mock_msg_repo, mock_issue_repo)

    async def test_create_message(self, service, mock_msg_repo):
        mock_msg_repo.create.return_value = MagicMock(id="msg-1")
        result = await service.create_message(
            issue_id="i1", content="Hello", author_username="u"
        )
        assert result.id == "msg-1"


# ---------------------------------------------------------------------------
# User Service
# ---------------------------------------------------------------------------


class TestUserService:
    @pytest.fixture
    def mock_user_repo(self):
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_user_repo):
        return UserService(mock_user_repo)

    async def test_get_or_create_from_github_new_user(self, service, mock_user_repo):
        mock_user_repo.get_by_github_id.return_value = None
        mock_user_repo.create.return_value = MagicMock(id="user-42", username="newuser")

        with patch("httpx.AsyncClient") as m:
            client = AsyncMock()
            m.return_value.__aenter__.return_value = client
            resp = MagicMock()
            resp.raise_for_status = MagicMock()
            resp.json.return_value = {
                "id": 42,
                "login": "newuser",
                "email": "new@example.com",
                "avatar_url": "https://avatars/42",
            }
            client.get.return_value = resp

            user = await service.get_or_create_from_github("token")
            assert user.username == "newuser"
            mock_user_repo.create.assert_called_once()

    async def test_get_or_create_from_github_existing_user(self, service, mock_user_repo):
        existing = MagicMock(id="user-42", username="existing")
        mock_user_repo.get_by_github_id.return_value = existing
        mock_user_repo.update.return_value = existing

        with patch("httpx.AsyncClient") as m:
            client = AsyncMock()
            m.return_value.__aenter__.return_value = client
            resp = MagicMock()
            resp.raise_for_status = MagicMock()
            resp.json.return_value = {
                "id": 42,
                "login": "existing",
                "email": "existing@example.com",
                "avatar_url": None,
            }
            client.get.return_value = resp

            user = await service.get_or_create_from_github("token")
            assert user.username == "existing"
            mock_user_repo.update.assert_called_once()
