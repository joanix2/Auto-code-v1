"""
Test GitHub client functionality
"""
import pytest
from github_client import GitHubClient


def test_github_client_initialization():
    """Test that GitHub client can be initialized"""
    client = GitHubClient()
    assert client is not None


def test_github_client_has_methods():
    """Test that GitHub client has required methods"""
    client = GitHubClient()
    assert hasattr(client, 'create_issue')
    assert hasattr(client, 'get_issue')
    assert hasattr(client, 'create_pull_request')
    assert hasattr(client, 'update_issue')
