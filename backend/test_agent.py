#!/usr/bin/env python3
"""
Test script for SimpleClaudeAgent
Demonstrates the complete workflow with a real ticket
"""

import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from src.agent.simple_claude_agent import SimpleClaudeAgent
from src.models.ticket import Ticket, TicketType, TicketPriority, TicketStatus

def test_agent():
    """Test SimpleClaudeAgent with a real ticket"""
    
    # Create a ticket
    ticket = Ticket(
        id="test-001",
        title="Add multiply and divide functions to calculator",
        description="""
        Add two new functions to the calculator.py file:
        1. multiply(a, b) - multiplies two numbers
        2. divide(a, b) - divides a by b (handle division by zero)
        
        Also update the main section to demonstrate these new functions.
        """,
        type=TicketType.feature,
        priority=TicketPriority.medium,
        status=TicketStatus.open,
        repository_id="test-repo",
        created_by="test-user"
    )
    
    # Repository path
    repo_path = Path(__file__).parent.parent / "workspace" / "test-agent"
    
    print("=" * 80)
    print("🤖 Testing SimpleClaudeAgent")
    print("=" * 80)
    print(f"\n📋 Ticket: {ticket.title}")
    print(f"📁 Repository: {repo_path}")
    print(f"🔑 API Key: {'✅ Set' if os.getenv('ANTHROPIC_API_KEY') else '❌ Not set'}")
    print()
    
    # Initialize agent
    try:
        agent = SimpleClaudeAgent()
        print(f"✅ Agent initialized: {agent.get_agent_name()}")
        print(f"   Model: {agent.model}")
        print(f"   Capabilities: {', '.join(agent._get_capabilities())}")
        print()
    except Exception as e:
        print(f"❌ Failed to initialize agent: {e}")
        return
    
    # Process ticket
    print("🚀 Processing ticket...")
    print("-" * 80)
    
    try:
        result = agent.process_ticket(ticket, repo_path)
        
        print()
        print("=" * 80)
        print("📊 RESULTS")
        print("=" * 80)
        
        if result["success"]:
            print("✅ Processing successful!")
            print(f"\n📝 Files modified:")
            for file_path in result["files_modified"]:
                print(f"   • {file_path}")
            
            print(f"\n💬 Summary:")
            print(result["message"])
            
            if "details" in result:
                details = result["details"]
                
                if "validation" in details:
                    validation = details["validation"]
                    print(f"\n🔍 Validation:")
                    print(f"   Valid: {'✅ Yes' if validation.get('valid') else '❌ No'}")
                    print(f"   Files checked: {validation.get('files_checked', 0)}")
                    
                    if validation.get("errors"):
                        print(f"\n   ❌ Errors:")
                        for error in validation["errors"]:
                            print(f"      • {error}")
                    
                    if validation.get("warnings"):
                        print(f"\n   ⚠️  Warnings:")
                        for warning in validation["warnings"]:
                            print(f"      • {warning}")
        else:
            print("❌ Processing failed!")
            print(f"\n💬 Error:")
            print(result["message"])
        
        print()
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ Error during processing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_agent()
