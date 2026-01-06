"""
Example script to test GitHub Issues integration
"""
import asyncio
import os
from src.database import Neo4jConnection
from src.repositories.ticket_repository import TicketRepository
from src.repositories.repository_repository import RepositoryRepository
from src.services.github.github_issue_service import GitHubIssueService
from src.models.ticket import TicketCreate, TicketType, TicketPriority


async def test_github_issues():
    """Test GitHub issues integration"""
    
    # Get GitHub token from environment
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        print("❌ GITHUB_TOKEN not found in environment")
        return
    
    # Initialize services
    db = Neo4jConnection()
    db.connect()
    
    ticket_repo = TicketRepository(db)
    repo_repository = RepositoryRepository(db)
    github_service = GitHubIssueService(github_token)
    
    print("=" * 80)
    print("🧪 Testing GitHub Issues Integration")
    print("=" * 80)
    
    try:
        # 1. Create a test ticket (or use existing one)
        print("\n📋 Step 1: Get or create a ticket...")
        
        # Get a repository
        repositories = await repo_repository.get_repositories_by_user("test_user")
        if not repositories:
            print("❌ No repositories found")
            return
        
        repo = repositories[0]
        print(f"   Repository: {repo.full_name}")
        
        # Create a test ticket
        ticket_data = TicketCreate(
            title="Test GitHub Issue Integration",
            description="This is a test ticket to verify GitHub issues integration works correctly.",
            repository_id=repo.id,
            priority=TicketPriority.high,
            ticket_type=TicketType.feature
        )
        
        ticket = await ticket_repo.create_ticket(ticket_data, "test_user")
        if not ticket:
            print("❌ Failed to create ticket")
            return
        
        print(f"   ✅ Ticket created: {ticket.id}")
        
        # 2. Create GitHub issue from ticket
        print("\n🔧 Step 2: Create GitHub issue...")
        
        issue_result = github_service.create_issue_from_ticket(
            repo_full_name=repo.full_name,
            ticket=ticket,
            branch_name="test/github-issues-integration"
        )
        
        if not issue_result:
            print("❌ Failed to create GitHub issue")
            return
        
        print(f"   ✅ Issue created: #{issue_result['issue_number']}")
        print(f"   📎 URL: {issue_result['issue_url']}")
        
        # 3. Link issue to ticket
        print("\n🔗 Step 3: Link issue to ticket...")
        
        success = await ticket_repo.link_github_issue(
            ticket_id=ticket.id,
            issue_number=issue_result["issue_number"],
            issue_url=issue_result["issue_url"]
        )
        
        if success:
            print(f"   ✅ Linked issue #{issue_result['issue_number']} to ticket {ticket.id}")
        else:
            print("❌ Failed to link issue to ticket")
            return
        
        # 4. Notify development started
        print("\n🚀 Step 4: Notify development started...")
        
        success = github_service.notify_development_started(
            repo_full_name=repo.full_name,
            issue_number=issue_result["issue_number"],
            branch_name="test/github-issues-integration"
        )
        
        if success:
            print(f"   ✅ Notification added to issue #{issue_result['issue_number']}")
        else:
            print("❌ Failed to notify development started")
        
        # 5. Add CI status comment
        print("\n✅ Step 5: Add CI status comment...")
        
        success = github_service.notify_ci_status(
            repo_full_name=repo.full_name,
            issue_number=issue_result["issue_number"],
            passed=True,
            details="All tests passed! ✅\n\n- Unit tests: 42 passed\n- Integration tests: 12 passed"
        )
        
        if success:
            print(f"   ✅ CI status added to issue #{issue_result['issue_number']}")
        else:
            print("❌ Failed to add CI status")
        
        # 6. Get issue info
        print("\n📊 Step 6: Get issue information...")
        
        issue_info = github_service.get_issue_info(
            repo_full_name=repo.full_name,
            issue_number=issue_result["issue_number"]
        )
        
        if issue_info:
            print(f"   ✅ Issue info retrieved:")
            print(f"      - Title: {issue_info['title']}")
            print(f"      - State: {issue_info['state']}")
            print(f"      - Labels: {', '.join(issue_info['labels'])}")
            print(f"      - URL: {issue_info['html_url']}")
        else:
            print("❌ Failed to get issue info")
        
        # 7. Update issue status (close it)
        print("\n🔒 Step 7: Close the issue...")
        
        from src.models.ticket import TicketStatus
        
        # First update ticket status
        await ticket_repo.update_ticket_status(ticket.id, "closed")
        
        # Reload ticket
        ticket = await ticket_repo.get_ticket_by_id(ticket.id)
        
        # Update GitHub issue
        success = github_service.update_issue_status(
            repo_full_name=repo.full_name,
            issue_number=issue_result["issue_number"],
            ticket_status=ticket.status,
            comment="✅ Feature completed and tested!"
        )
        
        if success:
            print(f"   ✅ Issue #{issue_result['issue_number']} closed")
        else:
            print("❌ Failed to close issue")
        
        print("\n" + "=" * 80)
        print("✅ ALL TESTS PASSED!")
        print("=" * 80)
        print(f"\n🔗 Check the issue on GitHub: {issue_result['issue_url']}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(test_github_issues())
