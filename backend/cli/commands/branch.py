"""
Branch management commands
"""
import typer
import asyncio
from typing import Optional
from rich.table import Table
from rich.panel import Panel
from rich import box

from cli.utils import console
from src.database import db
from src.services.git.branch_service import BranchService
from src.repositories.ticket_repository import TicketRepository
from src.repositories.repository_repository import RepositoryRepository

# Create sub-app for branch commands
branch_app = typer.Typer(help="Branch management commands")


def _get_branch_service():
    """Get branch service instance"""
    db.connect()
    return BranchService()


def _get_ticket_repo():
    """Get ticket repository instance"""
    db.connect()
    return TicketRepository(db)


def _get_repo_repo():
    """Get repository repository instance"""
    db.connect()
    return RepositoryRepository(db)


@branch_app.command()
def ensure(
    ticket_id: str = typer.Argument(..., help="Ticket ID"),
    base_branch: str = typer.Option("main", "--base", "-b", help="Base branch to create from"),
):
    """
    Ensure a branch exists for a ticket and checkout to it
    
    Creates the branch if it doesn't exist, otherwise checks it out.
    
    Examples:
        autocode branch ensure ticket-123
        autocode branch ensure ticket-123 --base develop
    """
    console.print(Panel.fit(
        "[bold blue]Ensure Ticket Branch[/bold blue]",
        border_style="blue"
    ))
    
    try:
        ticket_repo = _get_ticket_repo()
        repo_repo = _get_repo_repo()
        branch_service = _get_branch_service()
        
        with console.status("[bold cyan]Ensuring branch...[/bold cyan]"):
            # Get ticket
            ticket = asyncio.run(ticket_repo.get_ticket_by_id(ticket_id))
            
            if not ticket:
                console.print(f"\n[red]❌ Ticket not found: {ticket_id}[/red]")
                raise typer.Exit(1)
            
            # Get repository
            repository = asyncio.run(repo_repo.get_repository_by_id(ticket.repository_id))
            
            if not repository:
                console.print(f"\n[red]❌ Repository not found: {ticket.repository_id}[/red]")
                raise typer.Exit(1)
            
            # Ensure branch
            branch_name, was_created = branch_service.ensure_branch_for_ticket(
                ticket,
                repository.url,
                base_branch=base_branch
            )
            
            current_branch = branch_service.get_current_branch(repository.url)
        
        console.print()
        
        # Display result
        action = "Created" if was_created else "Checked out"
        action_color = "green" if was_created else "cyan"
        
        info_table = Table(show_header=False, box=box.SIMPLE, padding=(0, 2))
        info_table.add_column("Field", style="cyan bold", width=15)
        info_table.add_column("Value", style="white")
        
        info_table.add_row("Action", f"[{action_color}]{action}[/{action_color}]")
        info_table.add_row("Branch", f"[bold]{branch_name}[/bold]")
        info_table.add_row("Ticket ID", ticket_id)
        info_table.add_row("Ticket Title", ticket.title)
        info_table.add_row("Repository", repository.name)
        info_table.add_row("Current Branch", f"[yellow]{current_branch}[/yellow]")
        
        console.print(Panel(
            info_table,
            title=f"[bold {action_color}]Branch {action}[/bold {action_color}]",
            border_style=action_color
        ))
        
        console.print()
        
    except Exception as e:
        console.print(f"[red]❌ Failed to ensure branch: {str(e)}[/red]")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")
        raise typer.Exit(1)


@branch_app.command()
def create(
    ticket_id: str = typer.Argument(..., help="Ticket ID"),
    base_branch: str = typer.Option("main", "--base", "-b", help="Base branch to create from"),
    force: bool = typer.Option(False, "--force", "-f", help="Force creation even if exists"),
):
    """
    Create a branch for a ticket
    
    Examples:
        autocode branch create ticket-123
        autocode branch create ticket-123 --base develop
        autocode branch create ticket-123 --force
    """
    console.print(Panel.fit(
        "[bold blue]Create Ticket Branch[/bold blue]",
        border_style="blue"
    ))
    
    try:
        ticket_repo = _get_ticket_repo()
        repo_repo = _get_repo_repo()
        branch_service = _get_branch_service()
        
        with console.status("[bold cyan]Creating branch...[/bold cyan]"):
            # Get ticket
            ticket = asyncio.run(ticket_repo.get_ticket_by_id(ticket_id))
            
            if not ticket:
                console.print(f"\n[red]❌ Ticket not found: {ticket_id}[/red]")
                raise typer.Exit(1)
            
            # Get repository
            repository = asyncio.run(repo_repo.get_repository_by_id(ticket.repository_id))
            
            if not repository:
                console.print(f"\n[red]❌ Repository not found: {ticket.repository_id}[/red]")
                raise typer.Exit(1)
            
            # Create branch
            branch_name = branch_service.create_ticket_branch(
                ticket,
                repository.url,
                base_branch=base_branch,
                force=force
            )
            
            current_branch = branch_service.get_current_branch(repository.url)
        
        console.print()
        console.print(f"[green]✓ Created branch: {branch_name}[/green]")
        console.print(f"[dim]Current branch: {current_branch}[/dim]")
        console.print()
        
    except RuntimeError as e:
        console.print(f"\n[red]❌ {str(e)}[/red]")
        console.print(f"[dim]Use --force to recreate the branch[/dim]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]❌ Failed to create branch: {str(e)}[/red]")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")
        raise typer.Exit(1)


@branch_app.command()
def checkout(
    ticket_id: str = typer.Argument(..., help="Ticket ID"),
):
    """
    Checkout the branch for a ticket
    
    Examples:
        autocode branch checkout ticket-123
    """
    console.print(Panel.fit(
        "[bold blue]Checkout Ticket Branch[/bold blue]",
        border_style="blue"
    ))
    
    try:
        ticket_repo = _get_ticket_repo()
        repo_repo = _get_repo_repo()
        branch_service = _get_branch_service()
        
        with console.status("[bold cyan]Checking out branch...[/bold cyan]"):
            # Get ticket
            ticket = asyncio.run(ticket_repo.get_ticket_by_id(ticket_id))
            
            if not ticket:
                console.print(f"\n[red]❌ Ticket not found: {ticket_id}[/red]")
                raise typer.Exit(1)
            
            # Get repository
            repository = asyncio.run(repo_repo.get_repository_by_id(ticket.repository_id))
            
            if not repository:
                console.print(f"\n[red]❌ Repository not found: {ticket.repository_id}[/red]")
                raise typer.Exit(1)
            
            # Checkout branch
            branch_name = branch_service.checkout_ticket_branch(ticket, repository.url)
            current_branch = branch_service.get_current_branch(repository.url)
        
        console.print()
        console.print(f"[green]✓ Checked out branch: {branch_name}[/green]")
        console.print(f"[dim]Current branch: {current_branch}[/dim]")
        console.print()
        
    except RuntimeError as e:
        console.print(f"\n[red]❌ {str(e)}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]❌ Failed to checkout branch: {str(e)}[/red]")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")
        raise typer.Exit(1)


@branch_app.command()
def list(
    repository_id: str = typer.Argument(..., help="Repository ID"),
):
    """
    List all ticket branches for a repository
    
    Examples:
        autocode branch list repo-123
    """
    console.print(Panel.fit(
        "[bold blue]Ticket Branches[/bold blue]",
        border_style="blue"
    ))
    
    try:
        repo_repo = _get_repo_repo()
        branch_service = _get_branch_service()
        
        with console.status("[bold cyan]Listing branches...[/bold cyan]"):
            # Get repository
            repository = asyncio.run(repo_repo.get_repository_by_id(repository_id))
            
            if not repository:
                console.print(f"\n[red]❌ Repository not found: {repository_id}[/red]")
                raise typer.Exit(1)
            
            # List branches
            branches = branch_service.list_ticket_branches(repository.url)
            current_branch = branch_service.get_current_branch(repository.url)
        
        if not branches:
            console.print(f"\n[yellow]No ticket branches found for repository {repository.name}[/yellow]")
            return
        
        console.print(f"\n[green]Found {len(branches)} ticket branch{'es' if len(branches) != 1 else ''}:[/green]\n")
        
        # Create table
        table = Table(show_header=True, header_style="bold magenta", box=box.ROUNDED)
        table.add_column("Branch", style="cyan", no_wrap=False)
        table.add_column("Current", justify="center", width=10)
        
        for branch in branches:
            is_current = branch == current_branch
            current_marker = "[green]✓[/green]" if is_current else ""
            
            table.add_row(
                f"[bold]{branch}[/bold]" if is_current else branch,
                current_marker
            )
        
        console.print(table)
        console.print()
        console.print(f"[dim]Current branch: {current_branch}[/dim]")
        console.print()
        
    except Exception as e:
        console.print(f"[red]❌ Failed to list branches: {str(e)}[/red]")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")
        raise typer.Exit(1)


@branch_app.command()
def current(
    repository_id: str = typer.Argument(..., help="Repository ID"),
):
    """
    Show the current branch for a repository
    
    Examples:
        autocode branch current repo-123
    """
    try:
        repo_repo = _get_repo_repo()
        branch_service = _get_branch_service()
        
        with console.status("[bold cyan]Getting current branch...[/bold cyan]"):
            # Get repository
            repository = asyncio.run(repo_repo.get_repository_by_id(repository_id))
            
            if not repository:
                console.print(f"\n[red]❌ Repository not found: {repository_id}[/red]")
                raise typer.Exit(1)
            
            # Get current branch
            current_branch = branch_service.get_current_branch(repository.url)
        
        console.print()
        console.print(f"[green]Current branch:[/green] [bold]{current_branch}[/bold]")
        console.print(f"[dim]Repository: {repository.name}[/dim]")
        console.print()
        
    except Exception as e:
        console.print(f"[red]❌ Failed to get current branch: {str(e)}[/red]")
        raise typer.Exit(1)


@branch_app.command()
def info(
    branch_name: str = typer.Argument(..., help="Branch name"),
    repository_id: str = typer.Argument(..., help="Repository ID"),
):
    """
    Get information about a branch
    
    Examples:
        autocode branch info ticket/abc123-fix-bug repo-123
    """
    console.print(Panel.fit(
        "[bold blue]Branch Information[/bold blue]",
        border_style="blue"
    ))
    
    try:
        repo_repo = _get_repo_repo()
        branch_service = _get_branch_service()
        
        with console.status("[bold cyan]Getting branch info...[/bold cyan]"):
            # Get repository
            repository = asyncio.run(repo_repo.get_repository_by_id(repository_id))
            
            if not repository:
                console.print(f"\n[red]❌ Repository not found: {repository_id}[/red]")
                raise typer.Exit(1)
            
            # Get branch info
            info = branch_service.get_branch_info(repository.url, branch_name)
        
        console.print()
        
        if not info.get("exists"):
            console.print(f"[yellow]Branch does not exist: {branch_name}[/yellow]")
            return
        
        # Display info
        info_table = Table(show_header=False, box=box.SIMPLE, padding=(0, 2))
        info_table.add_column("Field", style="cyan bold", width=20)
        info_table.add_column("Value", style="white")
        
        info_table.add_row("Branch", f"[bold]{branch_name}[/bold]")
        info_table.add_row("Repository", repository.name)
        
        if info.get("last_commit"):
            commit = info["last_commit"]
            info_table.add_row("Last Commit", commit["hash"][:8])
            info_table.add_row("Author", commit["author_name"])
            info_table.add_row("Message", commit["message"])
            
            from datetime import datetime
            timestamp = datetime.fromtimestamp(commit["timestamp"])
            info_table.add_row("Date", timestamp.strftime('%Y-%m-%d %H:%M'))
        
        console.print(Panel(
            info_table,
            title="[bold green]Branch Info[/bold green]",
            border_style="green"
        ))
        
        console.print()
        
    except Exception as e:
        console.print(f"[red]❌ Failed to get branch info: {str(e)}[/red]")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")
        raise typer.Exit(1)
