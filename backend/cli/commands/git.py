"""
Git CLI Commands
Provides CLI commands for Git operations: commit, merge, and PR creation
"""

import os
import uuid
import asyncio
import typer
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from typing import Optional
from pathlib import Path

from src.services.git import GitService, PullRequestService
from src.services.messaging import MessageService
from src.repositories.ticket_repository import TicketRepository
from src.models.message import Message
from src.database import db as database

app = typer.Typer(help="Git operations: commit, merge, pull request")
console = Console()
console = Console()


def _get_ticket_repo():
    """Get ticket repository instance"""
    database.connect()
    return TicketRepository(database)


@app.command(name="commit")
def commit(
    ticket_id: str = typer.Argument(..., help="Ticket ID"),
    message: Optional[str] = typer.Option(None, "--message", "-m", help="Commit message (uses ticket title if not provided)"),
    push: bool = typer.Option(True, "--push/--no-push", help="Push after commit"),
    files: Optional[str] = typer.Option(None, "--files", "-f", help="Specific files to commit (comma-separated)")
):
    """
    Commit changes for a ticket (automatically adds, commits and pushes)
    """
    try:
        # Get ticket
        ticket_repo = _get_ticket_repo()
        ticket = asyncio.run(ticket_repo.get_ticket_by_id(ticket_id))
        
        if not ticket:
            console.print(f"[red]❌ Ticket {ticket_id} not found[/red]")
            raise typer.Exit(1)
        
        # Determine commit message
        commit_message = message or f"feat: {ticket.title}"
        
        # Get workspace root
        workspace_root = os.getenv("WORKSPACE_ROOT", "/workspace")
        repo_path = Path(workspace_root) / ticket.repository_name
        
        if not repo_path.exists():
            console.print(f"[red]❌ Repository not found at {repo_path}[/red]")
            raise typer.Exit(1)
        
        # Initialize Git service
        git_service = GitService(str(workspace_root))
        
        # Check for changes
        if not git_service.has_uncommitted_changes(ticket.repository_url):
            console.print("[yellow]⚠️  No uncommitted changes found[/yellow]")
            return
        
        # Parse files list if provided
        file_list = None
        if files:
            file_list = [f.strip() for f in files.split(",")]
            console.print(f"[dim]Files to commit: {', '.join(file_list)}[/dim]")
        
        # Determine branch name
        branch_name = f"ticket-{ticket.ticket_id}" if push else None
        
        # Get GitHub token
        github_token = os.getenv("GITHUB_TOKEN")
        
        # Perform add, commit, and push in one operation
        console.print(f"[cyan]🚀 Adding, committing and pushing changes...[/cyan]")
        console.print(f"[dim]Message: {commit_message}[/dim]")
        
        result = git_service.add_commit_and_push(
            repo_url=ticket.repository_url,
            commit_message=commit_message,
            branch_name=branch_name,
            files=file_list,
            token=github_token
        )
        
        if not result.get("success"):
            console.print(f"[red]❌ Operation failed: {result.get('message')}[/red]")
            raise typer.Exit(1)
        
        # Success!
        commit_hash = result.get("commit_hash", "")[:7]
        branch = result.get("branch")
        
        panel = Panel.fit(
            f"[green]✅ Successfully committed and pushed![/green]\n\n"
            f"[cyan]Commit:[/cyan] {commit_hash}\n"
            f"[cyan]Branch:[/cyan] {branch}\n"
            f"[dim]{commit_message}[/dim]",
            border_style="green"
        )
        console.print(panel)
        
        # Add message to ticket
        message_service = MessageService()
        commit_msg = Message(
            id=str(uuid.uuid4()),
            ticket_id=ticket.ticket_id,
            role="system",
            content=f"Changes committed and pushed: {commit_hash}\n{commit_message}",
            timestamp=datetime.now(),
            metadata={
                "commit_hash": result.get("commit_hash"),
                "branch": branch,
                "source": "auto_generated"
            }
        )
        message_service.create_message(commit_msg)
        
    except Exception as e:
        console.print(f"[red]❌ Error: {str(e)}[/red]")
        raise typer.Exit(1)


@app.command(name="merge")
def merge(
    ticket_id: str = typer.Argument(..., help="Ticket ID"),
    target_branch: str = typer.Option("main", "--target", "-t", help="Target branch to merge into"),
    fast_forward: bool = typer.Option(False, "--ff/--no-ff", help="Use fast-forward merge"),
    abort_on_conflict: bool = typer.Option(True, "--abort-on-conflict/--keep-conflict", help="Abort on merge conflict")
):
    """
    Merge ticket branch into target branch
    """
    try:
        # Get ticket
        ticket_repo = _get_ticket_repo()
        ticket = asyncio.run(ticket_repo.get_ticket_by_id(ticket_id))
        
        if not ticket:
            console.print(f"[red]❌ Ticket {ticket_id} not found[/red]")
            raise typer.Exit(1)
        
        source_branch = f"ticket-{ticket.ticket_id}"
        workspace_root = os.getenv("WORKSPACE_ROOT", "/workspace")
        
        # Initialize Git service
        git_service = GitService(workspace_root)
        
        console.print(f"[cyan]🔀 Merging {source_branch} into {target_branch}...[/cyan]")
        
        # Perform merge
        result = git_service.merge_branch(
            ticket.repository_url,
            source_branch,
            target_branch,
            fast_forward
        )
        
        if not result.get("success"):
            console.print(f"[red]❌ Merge failed: {result.get('message')}[/red]")
            
            # Check for conflicts
            conflicts = result.get("conflicts", [])
            if conflicts:
                console.print("\n[yellow]⚠️  Conflicts detected in:[/yellow]")
                for conflict in conflicts:
                    console.print(f"  • {conflict}")
                
                if abort_on_conflict:
                    console.print("\n[cyan]🔄 Aborting merge...[/cyan]")
                    git_service.abort_merge(ticket.repository_url)
                    console.print("[yellow]✅ Merge aborted[/yellow]")
                else:
                    console.print("\n[yellow]ℹ️  Resolve conflicts manually and commit[/yellow]")
            
            raise typer.Exit(1)
        
        console.print(f"[green]✅ Successfully merged {source_branch} into {target_branch}[/green]")
        
    except Exception as e:
        console.print(f"[red]❌ Error: {str(e)}[/red]")
        raise typer.Exit(1)


@app.command(name="pr")
def create_pr(
    ticket_id: str = typer.Argument(..., help="Ticket ID"),
    title: Optional[str] = typer.Option(None, "--title", "-t", help="PR title (uses ticket title if not provided)"),
    base_branch: str = typer.Option("main", "--base", "-b", help="Base branch for PR"),
    draft: bool = typer.Option(False, "--draft", help="Create as draft PR"),
    body: Optional[str] = typer.Option(None, "--body", help="PR description")
):
    """
    Create a Pull Request for a ticket
    """
    try:
        # Get ticket
        ticket_repo = _get_ticket_repo()
        ticket = asyncio.run(ticket_repo.get_ticket_by_id(ticket_id))
        
        if not ticket:
            console.print(f"[red]❌ Ticket {ticket_id} not found[/red]")
            raise typer.Exit(1)
        
        # Get GitHub token
        github_token = os.getenv("GITHUB_TOKEN")
        if not github_token:
            console.print("[red]❌ GITHUB_TOKEN environment variable not set[/red]")
            raise typer.Exit(1)
        
        # Prepare PR details
        pr_title = title or f"feat: {ticket.title}"
        head_branch = f"ticket-{ticket.ticket_id}"
        
        # Build PR body
        if not body:
            body = f"""## {ticket.title}

**Type:** {ticket.type}
**Priority:** {ticket.priority}

### Description
{ticket.description or 'No description provided'}

---
Closes #{ticket.ticket_id}
"""
        
        # Extract owner/repo from repository_name
        repo_full_name = ticket.repository_name
        
        # Initialize PR service
        pr_service = PullRequestService(github_token)
        
        console.print(f"[cyan]🚀 Creating Pull Request...[/cyan]")
        console.print(f"[dim]  Repository: {repo_full_name}[/dim]")
        console.print(f"[dim]  Branch: {head_branch} → {base_branch}[/dim]")
        console.print(f"[dim]  Title: {pr_title}[/dim]")
        
        # Create PR
        result = pr_service.create_pull_request(
            repo_full_name=repo_full_name,
            title=pr_title,
            body=body,
            head_branch=head_branch,
            base_branch=base_branch,
            draft=draft
        )
        
        if not result.get("success"):
            console.print(f"[red]❌ Failed to create PR: {result.get('message')}[/red]")
            raise typer.Exit(1)
        
        # Success!
        pr_url = result.get("pr_url")
        pr_number = result.get("pr_number")
        
        panel = Panel.fit(
            f"[green]✅ Pull Request Created![/green]\n\n"
            f"[cyan]PR #{pr_number}[/cyan]\n"
            f"[dim]{pr_url}[/dim]",
            border_style="green"
        )
        console.print(panel)
        
        # Add message to ticket
        message_service = MessageService()
        pr_msg = Message(
            id=str(uuid.uuid4()),
            ticket_id=ticket.ticket_id,
            role="system",
            content=f"Pull Request created: #{pr_number}\n{pr_url}",
            timestamp=datetime.now(),
            metadata={
                "pr_number": pr_number,
                "pr_url": pr_url,
                "source": "auto_generated"
            }
        )
        message_service.create_message(pr_msg)
        
    except Exception as e:
        console.print(f"[red]❌ Error: {str(e)}[/red]")
        raise typer.Exit(1)


@app.command(name="list-pr")
def list_prs(
    repo_name: str = typer.Argument(..., help="Repository name (owner/repo)"),
    state: str = typer.Option("open", "--state", "-s", help="PR state: open, closed, all"),
    base_branch: Optional[str] = typer.Option(None, "--base", "-b", help="Filter by base branch"),
    head_branch: Optional[str] = typer.Option(None, "--head", "-h", help="Filter by head branch")
):
    """
    List Pull Requests for a repository
    """
    try:
        # Get GitHub token
        github_token = os.getenv("GITHUB_TOKEN")
        if not github_token:
            console.print("[red]❌ GITHUB_TOKEN environment variable not set[/red]")
            raise typer.Exit(1)
        
        # Initialize PR service
        pr_service = PullRequestService(github_token)
        
        console.print(f"[cyan]📋 Fetching Pull Requests for {repo_name}...[/cyan]")
        
        # List PRs
        prs = pr_service.list_pull_requests(
            repo_full_name=repo_name,
            state=state,
            base_branch=base_branch,
            head_branch=head_branch
        )
        
        if not prs:
            console.print(f"[yellow]No {state} Pull Requests found[/yellow]")
            return
        
        # Create table
        table = Table(title=f"{repo_name} Pull Requests ({state})")
        table.add_column("#", style="cyan")
        table.add_column("Title", style="white")
        table.add_column("Branch", style="yellow")
        table.add_column("State", style="green")
        table.add_column("Draft", style="dim")
        
        for pr in prs:
            state_emoji = "✅" if pr["merged"] else ("🟢" if pr["state"] == "open" else "🔴")
            draft_text = "📝" if pr["draft"] else ""
            
            table.add_row(
                str(pr["number"]),
                pr["title"],
                f"{pr['head_branch']} → {pr['base_branch']}",
                f"{state_emoji} {pr['state']}",
                draft_text
            )
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]❌ Error: {str(e)}[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
