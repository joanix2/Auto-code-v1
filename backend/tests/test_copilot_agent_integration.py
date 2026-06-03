"""Integration tests for GitHubCopilotAgentService with mocked httpx.

Replaces the original test_copilot_agent.py (which required live GitHub API).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from src.services.repository.copilot_agent_service import GitHubCopilotAgentService


@pytest.fixture
def service():
    return GitHubCopilotAgentService(github_token="gh_test_token_123")


@pytest.fixture
def mock_client():
    with patch("httpx.AsyncClient") as m:
        client = AsyncMock()
        m.return_value.__aenter__.return_value = client
        yield client


def _ok_response(data: dict):
    """Return a mock httpx.Response that works for sync .json() and .raise_for_status()."""
    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    resp.json.return_value = data
    return resp


class TestAssignIssueToCopilot:
    """Tests for the assign_issue_to_copilot method."""

    async def test_assigns_issue_successfully(self, service, mock_client):
        mock_client.post.return_value = _ok_response({
            "assignees": [{"login": "copilot-swe-agent[bot]"}],
        })
        result = await service.assign_issue_to_copilot(
            owner="testowner",
            repo="testrepo",
            issue_number=42,
            custom_instructions="Fix this bug",
            base_branch="main",
        )
        assert result["success"] is True
        assert result["issue_number"] == 42
        assert result["assignees"][0]["login"] == "copilot-swe-agent[bot]"

        # Verify payload sent to GitHub
        call_kwargs = mock_client.post.call_args.kwargs
        payload = call_kwargs["json"]
        assert payload["assignees"] == ["copilot-swe-agent[bot]"]
        assert payload["agent_assignment"]["base_branch"] == "main"
        assert payload["agent_assignment"]["custom_instructions"] == "Fix this bug"

    async def test_raises_on_http_error(self, service, mock_client):
        resp = MagicMock()
        resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            "403 Forbidden", request=MagicMock(), response=MagicMock(status_code=403)
        )
        resp.text = "Forbidden"
        mock_client.post.return_value = resp

        with pytest.raises(Exception, match="Failed to assign"):
            await service.assign_issue_to_copilot(owner="o", repo="r", issue_number=1)

    async def test_sends_correct_headers(self, service, mock_client):
        mock_client.post.return_value = _ok_response({"assignees": []})
        await service.assign_issue_to_copilot(owner="o", repo="r", issue_number=1)

        headers = mock_client.post.call_args.kwargs["headers"]
        assert headers["Authorization"] == "Bearer gh_test_token_123"
        assert headers["Accept"] == "application/vnd.github+json"
        assert headers["X-GitHub-Api-Version"] == "2022-11-28"

    async def test_correct_url(self, service, mock_client):
        mock_client.post.return_value = _ok_response({"assignees": []})
        await service.assign_issue_to_copilot(owner="myorg", repo="myrepo", issue_number=7)

        url = mock_client.post.call_args.args[0]
        assert url == "https://api.github.com/repos/myorg/myrepo/issues/7/assignees"


class TestCreateIssueAndAssignToCopilot:
    async def test_creates_and_assigns(self, service, mock_client):
        mock_client.post.return_value = _ok_response({
            "number": 100,
            "html_url": "https://github.com/o/r/issues/100",
            "title": "Auto task",
            "assignees": [{"login": "copilot-swe-agent[bot]"}],
        })

        result = await service.create_issue_and_assign_to_copilot(
            owner="o",
            repo="r",
            title="Auto task",
            body="Do something",
            labels=["bug"],
            base_branch="develop",
        )

        assert result["success"] is True
        assert result["issue_number"] == 100

        payload = mock_client.post.call_args.kwargs["json"]
        assert payload["title"] == "Auto task"
        assert payload["labels"] == ["bug"]
        assert payload["agent_assignment"]["base_branch"] == "develop"

    async def test_handles_labels_optionally(self, service, mock_client):
        mock_client.post.return_value = _ok_response({
            "number": 1, "html_url": "", "title": "", "assignees": [],
        })

        await service.create_issue_and_assign_to_copilot(owner="o", repo="r", title="T", body="B")

        payload = mock_client.post.call_args.kwargs["json"]
        assert "labels" not in payload


class TestCheckCopilotAgentStatus:
    async def test_enabled_when_actor_found(self, service, mock_client):
        mock_client.post.return_value = _ok_response({
            "data": {
                "repository": {
                    "suggestedActors": {
                        "nodes": [
                            {"login": "copilot-swe-agent", "__typename": "Bot"},
                        ],
                    },
                },
            },
        })

        status = await service.check_copilot_agent_status(owner="o", repo="r")
        assert status["enabled"] is True

    async def test_disabled_when_actor_not_found(self, service, mock_client):
        mock_client.post.return_value = _ok_response({
            "data": {
                "repository": {
                    "suggestedActors": {"nodes": []},
                },
            },
        })

        status = await service.check_copilot_agent_status(owner="o", repo="r")
        assert status["enabled"] is False

    async def test_disabled_on_graphql_errors(self, service, mock_client):
        mock_client.post.return_value = _ok_response({
            "errors": [{"message": "Something went wrong"}],
        })

        status = await service.check_copilot_agent_status(owner="o", repo="r")
        assert status["enabled"] is False

    async def test_disabled_on_404(self, service, mock_client):
        resp = MagicMock()
        resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            "404", request=MagicMock(), response=MagicMock(status_code=404)
        )
        mock_client.post.return_value = resp

        status = await service.check_copilot_agent_status(owner="o", repo="r")
        assert status["enabled"] is False
        assert "not available" in status["message"]

    async def test_sends_graphql_features_header(self, service, mock_client):
        mock_client.post.return_value = _ok_response({
            "data": {"repository": {"suggestedActors": {"nodes": []}}},
        })

        await service.check_copilot_agent_status(owner="o", repo="r")

        headers = mock_client.post.call_args.kwargs["headers"]
        assert "GraphQL-Features" in headers


class TestGetPullRequestFromIssue:
    async def test_returns_pr_when_cross_referenced(self, service, mock_client):
        mock_client.get.return_value = _ok_response([
            {
                "event": "cross-referenced",
                "source": {
                    "type": "issue",
                    "issue": {
                        "number": 200,
                        "html_url": "https://github.com/o/r/pull/200",
                        "title": "Fix bug",
                        "state": "open",
                        "created_at": "2024-06-01T12:00:00Z",
                        "pull_request": {},
                    },
                },
            },
        ])

        pr = await service.get_pull_request_from_issue(owner="o", repo="r", issue_number=42)
        assert pr is not None
        assert pr["number"] == 200
        assert pr["title"] == "Fix bug"

    async def test_returns_none_when_no_pr(self, service, mock_client):
        mock_client.get.return_value = _ok_response([
            {"event": "mentioned", "source": {"type": "issue", "issue": {}}},
        ])

        pr = await service.get_pull_request_from_issue(owner="o", repo="r", issue_number=42)
        assert pr is None

    async def test_returns_none_on_api_error(self, service, mock_client):
        mock_client.get.side_effect = httpx.HTTPStatusError(
            "500", request=MagicMock(), response=MagicMock(status_code=500)
        )
        pr = await service.get_pull_request_from_issue(owner="o", repo="r", issue_number=42)
        assert pr is None
