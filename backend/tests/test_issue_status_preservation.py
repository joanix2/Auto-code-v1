"""
Test for issue status preservation during GitHub sync
"""
import sys
import os
import asyncio
from unittest.mock import Mock

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from src.services.issue_service import IssueService
from src.models.issue import Issue


async def test_status_preservation_review():
    """Test that 'review' status is preserved when syncing from GitHub"""
    print("\n🧪 Test: Preserve 'review' status during GitHub sync...")
    
    # Create mock issue repository
    issue_repo = Mock()
    
    # Create service
    service = IssueService(issue_repo)
    
    # Simulate existing issue in 'review' status
    existing_issue = Issue(
        id="issue-123",
        github_id=123,
        github_issue_number=1,
        title="Test Issue",
        description="Test description",
        repository_id="repo-1",
        author_username="test_user",
        status="review",
        priority="medium",
        issue_type="feature"
    )
    
    # Simulate GitHub data with 'open' state
    github_data = {
        "id": 123,
        "number": 1,
        "title": "Test Issue Updated",
        "body": "Updated description",
        "state": "open",  # GitHub only knows 'open' or 'closed'
        "html_url": "https://github.com/test/test/issues/1",
        "labels": [],
        "user": {"login": "test_user"},
        "_context": {
            "existing_issue": existing_issue
        }
    }
    
    # Map GitHub data to DB format
    db_data = await service.map_github_to_db(github_data)
    
    # Verify status is preserved
    assert db_data["status"] == "review", f"❌ Expected 'review' but got '{db_data['status']}'"
    print(f"  ✅ Status preserved: {db_data['status']}")
    
    return True


async def test_status_preservation_in_progress():
    """Test that 'in_progress' status is preserved when syncing from GitHub"""
    print("\n🧪 Test: Preserve 'in_progress' status during GitHub sync...")
    
    # Create mock issue repository
    issue_repo = Mock()
    
    # Create service
    service = IssueService(issue_repo)
    
    # Simulate existing issue in 'in_progress' status
    existing_issue = Issue(
        id="issue-124",
        github_id=124,
        github_issue_number=2,
        title="Test Issue In Progress",
        description="Test description",
        repository_id="repo-1",
        author_username="test_user",
        status="in_progress",
        priority="high",
        issue_type="bug"
    )
    
    # Simulate GitHub data with 'open' state
    github_data = {
        "id": 124,
        "number": 2,
        "title": "Test Issue In Progress",
        "body": "Test description",
        "state": "open",
        "html_url": "https://github.com/test/test/issues/2",
        "labels": [],
        "user": {"login": "test_user"},
        "_context": {
            "existing_issue": existing_issue
        }
    }
    
    # Map GitHub data to DB format
    db_data = await service.map_github_to_db(github_data)
    
    # Verify status is preserved
    assert db_data["status"] == "in_progress", f"❌ Expected 'in_progress' but got '{db_data['status']}'"
    print(f"  ✅ Status preserved: {db_data['status']}")
    
    return True


async def test_status_update_to_closed():
    """Test that status is updated to 'closed' when GitHub issue is closed"""
    print("\n🧪 Test: Update status to 'closed' when GitHub issue is closed...")
    
    # Create mock issue repository
    issue_repo = Mock()
    
    # Create service
    service = IssueService(issue_repo)
    
    # Simulate existing issue in 'review' status
    existing_issue = Issue(
        id="issue-125",
        github_id=125,
        github_issue_number=3,
        title="Test Issue",
        description="Test description",
        repository_id="repo-1",
        author_username="test_user",
        status="review",
        priority="medium",
        issue_type="feature"
    )
    
    # Simulate GitHub data with 'closed' state
    github_data = {
        "id": 125,
        "number": 3,
        "title": "Test Issue",
        "body": "Test description",
        "state": "closed",  # GitHub issue is closed
        "html_url": "https://github.com/test/test/issues/3",
        "labels": [],
        "user": {"login": "test_user"},
        "_context": {
            "existing_issue": existing_issue
        }
    }
    
    # Map GitHub data to DB format
    db_data = await service.map_github_to_db(github_data)
    
    # Verify status is updated to closed
    assert db_data["status"] == "closed", f"❌ Expected 'closed' but got '{db_data['status']}'"
    print(f"  ✅ Status updated to: {db_data['status']}")
    
    return True


async def test_new_issue_default_status():
    """Test that new issues get 'open' status by default"""
    print("\n🧪 Test: New issue gets 'open' status by default...")
    
    # Create mock issue repository
    issue_repo = Mock()
    
    # Create service
    service = IssueService(issue_repo)
    
    # Simulate GitHub data for new issue (no existing issue in context)
    github_data = {
        "id": 126,
        "number": 4,
        "title": "New Test Issue",
        "body": "New test description",
        "state": "open",
        "html_url": "https://github.com/test/test/issues/4",
        "labels": [],
        "user": {"login": "test_user"}
        # No _context with existing_issue
    }
    
    # Map GitHub data to DB format
    db_data = await service.map_github_to_db(github_data)
    
    # Verify status is set to open
    assert db_data["status"] == "open", f"❌ Expected 'open' but got '{db_data['status']}'"
    print(f"  ✅ New issue status: {db_data['status']}")
    
    return True


async def main():
    """Run all tests"""
    print("=" * 60)
    print("TEST ISSUE STATUS PRESERVATION")
    print("=" * 60)
    
    tests = [
        ("Preserve 'review' status", test_status_preservation_review),
        ("Preserve 'in_progress' status", test_status_preservation_in_progress),
        ("Update to 'closed' when GitHub is closed", test_status_update_to_closed),
        ("New issue gets 'open' status", test_new_issue_default_status),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = await test_func()
            results.append(result)
        except Exception as e:
            print(f"\n❌ Error in test '{name}': {e}")
            import traceback
            traceback.print_exc()
            results.append(False)
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"✅ Tests passed: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 All tests passed successfully!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
