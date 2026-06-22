"""Tests for data models"""

from src.models.repository.issue import IssueCreate
from src.models.repository.repository import RepositoryCreate


def test_issue_create_schema():
    data = IssueCreate(title="Test issue", description="Test desc", repository_id="repo:1")
    assert data.title == "Test issue"
    assert data.repository_id == "repo:1"


def test_repository_create():
    data = RepositoryCreate(name="test-repo", description="A test repo", private=False)
    assert data.name == "test-repo"
    assert data.private is False
