"""Tests for BaseRepository CRUD and custom repository methods."""

from __future__ import annotations

import pytest

from src.repositories.base import BaseRepository, prepare_neo4j_properties
from src.repositories.repository.issue_repository import IssueRepository
from src.repositories.repository.repository_repository import RepositoryRepository
from tests.conftest import MockNeo4jDB, MockNeo4jResult


class _ConcreteRepo(BaseRepository):
    """Minimal concrete subclass for testing BaseRepository."""

    def __init__(self, db):
        super().__init__(db, dict, "TestLabel")


# ---------------------------------------------------------------------------
# prepare_neo4j_properties
# ---------------------------------------------------------------------------


class TestPrepareNeo4jProperties:
    def test_primitives_passthrough(self):
        data = {"name": "hello", "count": 3, "ratio": 1.5, "flag": True, "nothing": None}
        result = prepare_neo4j_properties(data)
        assert result == data

    def test_list_of_primitives(self):
        data = {"tags": ["a", "b", "c"], "scores": [1, 2, 3]}
        result = prepare_neo4j_properties(data)
        assert result == data

    def test_dict_serialized_to_json(self):
        data = {"meta": {"key": "val"}}
        result = prepare_neo4j_properties(data)
        assert result["meta"] == '{"key": "val"}'

    def test_list_of_dicts_serialized(self):
        data = {"items": [{"x": 1}, {"x": 2}]}
        result = prepare_neo4j_properties(data)
        assert result["items"] == '[{"x": 1}, {"x": 2}]'

    def test_unknown_type_stringified(self):
        data = {"obj": object()}
        result = prepare_neo4j_properties(data)
        assert isinstance(result["obj"], str)


# ---------------------------------------------------------------------------
# BaseRepository CRUD
# ---------------------------------------------------------------------------


class TestBaseRepositoryCreate:
    async def test_create_returns_model(self, mock_db: MockNeo4jDB):
        mock_db.add_result([{"n": {"id": "test-1", "name": "created"}}])
        repo = _ConcreteRepo(mock_db)

        result = await repo.create({"id": "test-1", "name": "created"})

        assert result["id"] == "test-1"
        assert result["name"] == "created"

    async def test_create_raises_on_empty_result(self, mock_db: MockNeo4jDB):
        mock_db.add_result([])
        repo = _ConcreteRepo(mock_db)

        with pytest.raises(ValueError, match="Failed to create"):
            await repo.create({"id": "fail"})


class TestBaseRepositoryGetById:
    async def test_get_by_id_found(self, mock_db: MockNeo4jDB):
        mock_db.add_result([{"n": {"id": "r1", "name": "found"}}])
        repo = _ConcreteRepo(mock_db)

        result = await repo.get_by_id("r1")
        assert result is not None
        assert result["id"] == "r1"

    async def test_get_by_id_not_found(self, mock_db: MockNeo4jDB):
        mock_db.add_result([])
        repo = _ConcreteRepo(mock_db)

        result = await repo.get_by_id("missing")
        assert result is None


class TestBaseRepositoryGetAll:
    async def test_get_all_returns_list(self, mock_db: MockNeo4jDB):
        mock_db.add_result([{"n": {"id": "a"}}, {"n": {"id": "b"}}])
        repo = _ConcreteRepo(mock_db)

        results = await repo.get_all()
        assert len(results) == 2

    async def test_get_all_empty(self, mock_db: MockNeo4jDB):
        mock_db.add_result([])
        repo = _ConcreteRepo(mock_db)

        results = await repo.get_all()
        assert results == []


class TestBaseRepositoryUpdate:
    async def test_update_found(self, mock_db: MockNeo4jDB):
        mock_db.add_result([{"n": {"id": "r1", "name": "updated", "extra": "val"}}])
        repo = _ConcreteRepo(mock_db)

        result = await repo.update("r1", {"name": "updated"})
        assert result is not None
        assert result["name"] == "updated"

    async def test_update_not_found(self, mock_db: MockNeo4jDB):
        mock_db.add_result([])
        repo = _ConcreteRepo(mock_db)

        result = await repo.update("missing", {"name": "noop"})
        assert result is None

    async def test_update_no_changes_falls_back_to_get(self, mock_db: MockNeo4jDB):
        mock_db.add_result([{"n": {"id": "r1", "name": "same"}}])
        repo = _ConcreteRepo(mock_db)

        result = await repo.update("r1", {})
        assert result is not None
        assert result["name"] == "same"


class TestBaseRepositoryDelete:
    async def test_delete_found(self, mock_db: MockNeo4jDB):
        mock_db.add_result([{"deleted": 1}])
        repo = _ConcreteRepo(mock_db)

        assert await repo.delete("r1") is True

    async def test_delete_not_found(self, mock_db: MockNeo4jDB):
        mock_db.add_result([{"deleted": 0}])
        repo = _ConcreteRepo(mock_db)

        assert await repo.delete("missing") is False

    async def test_delete_empty_result(self, mock_db: MockNeo4jDB):
        mock_db.add_result([])
        repo = _ConcreteRepo(mock_db)

        assert not await repo.delete("missing")


# ---------------------------------------------------------------------------
# RepositoryRepository
# ---------------------------------------------------------------------------


class TestRepositoryRepository:
    async def test_get_by_github_id_found(self, mock_db: MockNeo4jDB, sample_repo_row):
        mock_db.add_result([sample_repo_row])
        repo = RepositoryRepository(mock_db)

        result = await repo.get_by_github_id(1001)
        assert result is not None
        assert result.id == "repo-1"
        assert result.github_id == 1001

    async def test_get_by_github_id_not_found(self, mock_db: MockNeo4jDB):
        mock_db.add_result([])
        repo = RepositoryRepository(mock_db)

        result = await repo.get_by_github_id(9999)
        assert result is None

    async def test_get_by_full_name_found(self, mock_db: MockNeo4jDB, sample_repo_row):
        mock_db.add_result([sample_repo_row])
        repo = RepositoryRepository(mock_db)

        result = await repo.get_by_full_name("testuser/test-repo")
        assert result is not None
        assert result.full_name == "testuser/test-repo"

    async def test_get_by_owner(self, mock_db: MockNeo4jDB, sample_repo_row):
        mock_db.add_result([sample_repo_row])
        repo = RepositoryRepository(mock_db)

        results = await repo.get_by_owner("testuser")
        assert len(results) == 1
        assert results[0].owner_username == "testuser"


# ---------------------------------------------------------------------------
# IssueRepository
# ---------------------------------------------------------------------------


class TestIssueRepository:
    async def test_get_by_repository(self, mock_db: MockNeo4jDB, sample_issue_row):
        mock_db.add_result([sample_issue_row])
        repo = IssueRepository(mock_db)

        results = await repo.get_by_repository("repo-1")
        assert len(results) == 1
        assert results[0].repository_id == "repo-1"

    async def test_get_by_repository_with_status(self, mock_db: MockNeo4jDB, sample_issue_row):
        mock_db.add_result([sample_issue_row])
        repo = IssueRepository(mock_db)

        results = await repo.get_by_repository("repo-1", status="open")
        assert len(results) == 1

    async def test_get_by_github_id(self, mock_db: MockNeo4jDB, sample_issue_row):
        mock_db.add_result([sample_issue_row])
        repo = IssueRepository(mock_db)

        result = await repo.get_by_github_id(2001)
        assert result is not None
        assert result.github_issue_number == 42
        assert result.repository_id == "repo-1"

    async def test_get_by_github_issue_number(self, mock_db: MockNeo4jDB, sample_issue_row):
        mock_db.add_result([sample_issue_row])
        repo = IssueRepository(mock_db)

        result = await repo.get_by_github_issue_number("repo-1", 42)
        assert result is not None
        assert result.github_issue_number == 42

    async def test_assign_to_copilot(self, mock_db: MockNeo4jDB, sample_issue_row):
        updated_row = dict(sample_issue_row)
        updated_row["n"] = {**sample_issue_row["n"], "assigned_to_copilot": True}
        mock_db.add_result([updated_row])
        repo = IssueRepository(mock_db)

        result = await repo.assign_to_copilot("issue-1", assigned=True)
        assert result is not None
        assert result.assigned_to_copilot is True

    async def test_get_copilot_issues(self, mock_db: MockNeo4jDB, sample_issue_row):
        mock_db.add_result([sample_issue_row])
        repo = IssueRepository(mock_db)

        results = await repo.get_copilot_issues()
        assert len(results) == 1

    async def test_link_to_github(self, mock_db: MockNeo4jDB, sample_issue_row):
        mock_db.add_result([sample_issue_row])
        repo = IssueRepository(mock_db)

        result = await repo.link_to_github("issue-1", {"github_issue_number": 99})
        assert result is not None
