"""Tests for data models"""

from src.models.graph.node_type import NodeType
from src.models.graph.edge_type import EdgeType
from src.models.repository.issue import IssueCreate
from src.models.repository.repository import RepositoryCreate


def test_node_type_creation():
    nt = NodeType(
        name="Concept",
        label="Concept",
        labelPlural="Concepts",
        gender="m",
        article="le",
    )
    assert nt.name == "Concept"
    assert nt.label == "Concept"
    assert nt.article == "le"


def test_edge_type_creation():
    et = EdgeType(
        name="DOMAIN",
        description="Domain relationship",
        sourceNodeTypes=["concept"],
        targetNodeTypes=["concept"],
        directed=True,
    )
    assert et.name == "DOMAIN"
    assert et.directed is True
    assert "concept" in et.sourceNodeTypes


def test_issue_create_schema():
    data = IssueCreate(title="Test issue", description="Test desc", repository_id="repo:1")
    assert data.title == "Test issue"
    assert data.repository_id == "repo:1"


def test_repository_create():
    data = RepositoryCreate(name="test-repo", description="A test repo", private=False)
    assert data.name == "test-repo"
    assert data.private is False
