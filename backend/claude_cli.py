#!/usr/bin/env python3
"""
CLI tool for Auto-Code Claude integration
Usage:
    python claude_cli.py develop <ticket_id>
    python claude_cli.py develop-next <repository_id>
    python claude_cli.py next <repository_id>
"""
import sys
import os
import asyncio
import json
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from src.services.claude_service import ClaudeService
from src.repositories.ticket_repository import TicketRepository
from src.repositories.repository_repository import RepositoryRepository
from src.database import Neo4jConnection


async def develop_ticket(ticket_id: str):
    """Develop a specific ticket with Claude"""
    db = Neo4jConnection()
    ticket_repo = TicketRepository(db)
    repo_repo = RepositoryRepository(db)
    
    # Get ticket
    ticket = await ticket_repo.get_ticket_by_id(ticket_id)
    if not ticket:
        print(f"❌ Ticket {ticket_id} not found")
        return 1
    
    # Get repository
    repository = await repo_repo.get_repository_by_id(ticket.repository_id)
    if not repository:
        print(f"❌ Repository {ticket.repository_id} not found")
        return 1
    
    print(f"\n🎯 Developing ticket: {ticket.title}")
    print(f"📦 Repository: {repository.name}")
    print(f"⏳ Calling Claude API...\n")
    
    try:
        claude = ClaudeService()
        result = await claude.develop_ticket(
            ticket_title=ticket.title,
            ticket_description=ticket.description,
            ticket_type=ticket.ticket_type,
            priority=ticket.priority,
            repository_name=repository.name,
            repository_path=repository.url
        )
        
        print(f"✅ Claude Response:")
        print(f"=" * 80)
        print(result['content'])
        print(f"=" * 80)
        print(f"\n📊 Usage:")
        print(f"   Input tokens:  {result['usage'].get('input_tokens', 'N/A')}")
        print(f"   Output tokens: {result['usage'].get('output_tokens', 'N/A')}")
        print(f"   Model: {result['model']}")
        
        # Save to file
        output_file = f"claude_response_{ticket_id}.md"
        with open(output_file, 'w') as f:
            f.write(result['content'])
        print(f"\n💾 Response saved to: {output_file}")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


async def develop_next_ticket(repository_id: str):
    """Develop the next ticket in queue"""
    db = Neo4jConnection()
    ticket_repo = TicketRepository(db)
    
    # Get all open tickets
    all_tickets = await ticket_repo.get_tickets_by_repository(repository_id)
    open_tickets = [t for t in all_tickets if t.status == "open"]
    open_tickets.sort(key=lambda t: t.order)
    
    if not open_tickets:
        print(f"❌ No open tickets found for repository {repository_id}")
        return 1
    
    next_ticket = open_tickets[0]
    print(f"🎯 Next ticket in queue: {next_ticket.title} (#{next_ticket.id})")
    print(f"📋 Queue position: 1/{len(open_tickets)}\n")
    
    return await develop_ticket(next_ticket.id)


async def show_next_ticket(repository_id: str):
    """Show the next ticket in queue without developing"""
    db = Neo4jConnection()
    ticket_repo = TicketRepository(db)
    repo_repo = RepositoryRepository(db)
    
    # Get repository
    repository = await repo_repo.get_repository_by_id(repository_id)
    if not repository:
        print(f"❌ Repository {repository_id} not found")
        return 1
    
    # Get all open tickets
    all_tickets = await ticket_repo.get_tickets_by_repository(repository_id)
    open_tickets = [t for t in all_tickets if t.status == "open"]
    open_tickets.sort(key=lambda t: t.order)
    
    print(f"\n📦 Repository: {repository.name}")
    print(f"📊 Total open tickets: {len(open_tickets)}")
    
    if not open_tickets:
        print("✅ No tickets in queue!")
        return 0
    
    next_ticket = open_tickets[0]
    print(f"\n🎯 Next ticket to develop:")
    print(f"   ID: {next_ticket.id}")
    print(f"   Title: {next_ticket.title}")
    print(f"   Type: {next_ticket.ticket_type}")
    print(f"   Priority: {next_ticket.priority}")
    print(f"   Description: {next_ticket.description or 'N/A'}")
    print(f"\n📋 Remaining in queue: {len(open_tickets) - 1}")
    
    return 0


def print_usage():
    """Print usage information"""
    print("""
Auto-Code Claude CLI

Usage:
    python claude_cli.py develop <ticket_id>           # Develop a specific ticket
    python claude_cli.py develop-next <repository_id>  # Develop next ticket in queue
    python claude_cli.py next <repository_id>          # Show next ticket in queue

Environment:
    ANTHROPIC_API_KEY must be set

Examples:
    export ANTHROPIC_API_KEY=sk-ant-...
    python claude_cli.py next my-repo-id
    python claude_cli.py develop-next my-repo-id
    """)


def main():
    """Main CLI entry point"""
    if len(sys.argv) < 2:
        print_usage()
        return 1
    
    # Check API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("❌ ANTHROPIC_API_KEY environment variable not set")
        print("   Get your key from: https://console.anthropic.com/")
        return 1
    
    command = sys.argv[1]
    
    if command == "develop" and len(sys.argv) == 3:
        ticket_id = sys.argv[2]
        return asyncio.run(develop_ticket(ticket_id))
    
    elif command == "develop-next" and len(sys.argv) == 3:
        repository_id = sys.argv[2]
        return asyncio.run(develop_next_ticket(repository_id))
    
    elif command == "next" and len(sys.argv) == 3:
        repository_id = sys.argv[2]
        return asyncio.run(show_next_ticket(repository_id))
    
    else:
        print_usage()
        return 1


if __name__ == "__main__":
    sys.exit(main())
