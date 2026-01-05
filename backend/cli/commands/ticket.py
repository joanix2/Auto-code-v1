"""
Ticket management commands
"""
import typer
import asyncio
from typing import Optional
from datetime import datetime
from rich.table import Table
from rich.panel import Panel
from rich import box

from cli.utils import console
from src.database import db
from src.repositories.ticket_repository import TicketRepository
from src.repositories.message_repository import MessageRepository

# Create sub-app for ticket commands
ticket_app = typer.Typer(help="Ticket management commands")


def _get_ticket_repo():
    """Get ticket repository instance"""
    db.connect()  # Ensure database is connected
    return TicketRepository(db)


def _get_message_repo():
    """Get message repository instance"""
    db.connect()  # Ensure database is connected
    return MessageRepository(db)


@ticket_app.command()
def list(
    repository: Optional[str] = typer.Option(None, "--repo", "-r", help="Filter by repository ID"),
    limit: int = typer.Option(20, "--limit", "-l", help="Number of tickets to show"),
):
    """
    List all tickets
    
    Shows tickets from the database with their status and details.
    
    Examples:
        autocode ticket list                        # Show all recent tickets
        autocode ticket list --repo repo-id         # Tickets for specific repository
        autocode ticket list --limit 50             # Show 50 tickets
    """
    console.print(Panel.fit(
        "[bold blue]Tickets List[/bold blue]",
        border_style="blue"
    ))
    
    try:
        ticket_repo = _get_ticket_repo()
        
        with console.status("[bold cyan]Fetching tickets...[/bold cyan]"):
            if repository:
                tickets = asyncio.run(ticket_repo.get_tickets_by_repository(repository))
            else:
                # Get all tickets by querying all repositories
                # For now, just query Neo4j directly
                query = """
                MATCH (t:Ticket)<-[:CREATED]-(u:User)
                OPTIONAL MATCH (t)-[:FOR_REPO]->(r:Repository)
                RETURN t, u.username as created_by, r.name as repository_name
                ORDER BY t.created_at DESC
                LIMIT $limit
                """
                result = db.execute_query(query, {"limit": limit})
                
                from src.models.ticket import TicketStatus
                tickets = []
                for record in result:
                    ticket_node = record["t"]
                    from src.repositories.ticket_repository import neo4j_datetime_to_python
                    tickets.append(type('Ticket', (), {
                        'id': ticket_node["id"],
                        'title': ticket_node["title"],
                        'description': ticket_node.get("description"),
                        'repository_id': ticket_node.get("repository_id"),
                        'repository_name': record.get("repository_name"),
                        'status': ticket_node.get("status", "open"),
                        'created_at': neo4j_datetime_to_python(ticket_node.get("created_at")),
                        'created_by': record["created_by"]
                    }))
        
        if not tickets:
            console.print("\n[yellow]No tickets found[/yellow]")
            if repository:
                console.print(f"[dim]Try removing the --repo filter or check your database[/dim]")
            return
        
        console.print(f"\n[green]Found {len(tickets)} tickets:[/green]\n")
        
        # Create table
        table = Table(show_header=True, header_style="bold magenta", box=box.ROUNDED)
        table.add_column("ID", style="cyan", no_wrap=True, width=8)
        table.add_column("Title", style="white", max_width=40)
        table.add_column("Status", justify="center", width=12)
        table.add_column("Repo", style="blue", no_wrap=True, max_width=25)
        table.add_column("Created", style="dim", width=10)
        
        # Status colors
        status_colors = {
            'open': 'yellow',
            'pending': 'yellow',
            'in_progress': 'cyan',
            'completed': 'green',
            'error': 'red',
            'validated': 'bright_green',
            'rejected': 'bright_red',
            'closed': 'dim'
        }
        
        for ticket in tickets:
            # Format status with color
            ticket_status = ticket.status
            status_color = status_colors.get(ticket_status, 'white')
            status_text = f"[{status_color}]{ticket_status}[/{status_color}]"
            
            # Format title
            title = ticket.title if len(ticket.title) <= 40 else ticket.title[:37] + "..."
            
            # Format repo
            repo_name = ticket.repository_name if hasattr(ticket, 'repository_name') and ticket.repository_name else '[dim]N/A[/dim]'
            if repo_name and len(repo_name) > 25:
                repo_name = repo_name[:22] + "..."
            
            # Format date
            created = ticket.created_at.strftime('%Y-%m-%d') if hasattr(ticket, 'created_at') and ticket.created_at else '[dim]N/A[/dim]'
            
            # Format ID (shorten if too long)
            ticket_id = str(ticket.id)
            if len(ticket_id) > 8:
                ticket_id = ticket_id[:6] + ".."
            
            table.add_row(
                ticket_id,
                title,
                status_text,
                repo_name,
                created
            )
        
        console.print(table)
        console.print()
        
    except Exception as e:
        console.print(f"[red]❌ Failed to fetch tickets: {str(e)}[/red]")
        console.print(f"[dim]Make sure Neo4j is running and accessible[/dim]")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")
        raise typer.Exit(1)


@ticket_app.command()
def next(
    repository: str = typer.Argument(..., help="Repository ID or name to get next ticket from"),
):
    """
    Get the next ticket to work on
    
    Returns the next open ticket in the queue (first open ticket by order).
    
    Examples:
        autocode ticket next repo-id               # Get next ticket by repository ID
        autocode ticket next Auto-code-v1          # Get next ticket by repository name
    """
    console.print(Panel.fit(
        "[bold blue]Next Ticket in Queue[/bold blue]",
        border_style="blue"
    ))
    
    try:
        ticket_repo = _get_ticket_repo()
        
        with console.status("[bold cyan]Finding next ticket...[/bold cyan]"):
            # First, try to find repository by name if it's not a UUID
            repository_id = repository
            if not repository.startswith(('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'a', 'b', 'c', 'd', 'e', 'f')) or len(repository) < 32:
                # Likely a repository name, try to find the ID
                query = """
                MATCH (r:Repository {name: $repo_name})
                RETURN r.id as id
                """
                result = db.execute_query(query, {"repo_name": repository})
                if result and len(result) > 0:
                    repository_id = result[0]["id"]
                    console.print(f"[dim]Found repository ID: {repository_id}[/dim]")
                else:
                    console.print(f"\n[red]❌ Repository not found: {repository}[/red]")
                    console.print(f"[dim]Try using the repository ID or check the repository name[/dim]")
                    raise typer.Exit(1)
            
            # Get all tickets for the repository
            all_tickets = asyncio.run(ticket_repo.get_tickets_by_repository(repository_id))
            
            # Filter for open tickets
            from src.models.ticket import TicketStatus
            open_tickets = [t for t in all_tickets if t.status == TicketStatus.open]
            
            # Sort by order (already sorted from DB, but ensure it)
            open_tickets.sort(key=lambda t: t.order)
        
        if not open_tickets:
            console.print("\n[yellow]No open tickets found in queue[/yellow]")
            console.print(f"[dim]Repository: {repository}[/dim]")
            return
        
        next_ticket = open_tickets[0]
        total_open = len(open_tickets)
        
        console.print()
        console.print(f"[green]Found next ticket ({total_open} open ticket{'s' if total_open > 1 else ''} in queue):[/green]\n")
        
        # Display ticket details
        info_table = Table(show_header=False, box=box.SIMPLE, padding=(0, 2))
        info_table.add_column("Field", style="cyan bold", width=15)
        info_table.add_column("Value", style="white")
        
        info_table.add_row("ID", str(next_ticket.id))
        info_table.add_row("Title", next_ticket.title)
        info_table.add_row("Status", f"[yellow]{next_ticket.status.value}[/yellow]")
        info_table.add_row("Priority", next_ticket.priority.value)
        info_table.add_row("Type", next_ticket.ticket_type.value)
        info_table.add_row("Order", str(next_ticket.order))
        info_table.add_row("Created By", next_ticket.created_by)
        
        if next_ticket.created_at:
            info_table.add_row("Created", next_ticket.created_at.strftime('%Y-%m-%d %H:%M'))
        
        console.print(Panel(
            info_table,
            title=f"[bold green]Next Ticket[/bold green]",
            border_style="green"
        ))
        
        if next_ticket.description:
            console.print()
            console.print(Panel(
                next_ticket.description,
                title="[bold]Description[/bold]",
                border_style="dim"
            ))
        
        console.print()
        console.print(f"[dim]Queue position: 1/{total_open}[/dim]")
        console.print()
        
    except Exception as e:
        console.print(f"[red]❌ Failed to fetch next ticket: {str(e)}[/red]")
        console.print(f"[dim]Make sure Neo4j is running and the repository exists[/dim]")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")
        raise typer.Exit(1)


@ticket_app.command()
def get(
    ticket_id: str = typer.Argument(..., help="Ticket ID"),
    show_messages: bool = typer.Option(False, "--messages", "-m", help="Show conversation messages"),
):
    """
    Get detailed ticket information
    
    Shows full details of a specific ticket including description and optionally messages.
    
    Examples:
        autocode ticket get abc123                  # Show ticket details
        autocode ticket get abc123 --messages       # Include conversation messages
    """
    console.print(Panel.fit(
        "[bold blue]Ticket Details[/bold blue]",
        border_style="blue"
    ))
    
    try:
        ticket_repo = _get_ticket_repo()
        
        with console.status("[bold cyan]Fetching ticket...[/bold cyan]"):
            ticket = asyncio.run(ticket_repo.get_ticket_by_id(ticket_id))
        
        if not ticket:
            console.print(f"\n[red]❌ Ticket not found: {ticket_id}[/red]")
            raise typer.Exit(1)
        
        # Display ticket info
        console.print()
        
        # Status panel
        status_colors = {
            'pending': 'yellow',
            'in_progress': 'cyan',
            'completed': 'green',
            'error': 'red',
            'validated': 'bright_green',
            'rejected': 'bright_red'
        }
        status_color = status_colors.get(ticket.status, 'white')
        
        console.print(Panel(
            f"[bold]{ticket.title}[/bold]\n\n"
            f"[cyan]ID:[/cyan] {ticket.id}\n"
            f"[cyan]Status:[/cyan] [{status_color}]{ticket.status}[/{status_color}]\n"
            f"[cyan]Repository:[/cyan] {ticket.repository_name if hasattr(ticket, 'repository_name') else 'N/A'}\n"
            f"[cyan]Created:[/cyan] {ticket.created_at.strftime('%Y-%m-%d %H:%M:%S') if hasattr(ticket, 'created_at') and ticket.created_at else 'N/A'}",
            title="[bold magenta]Ticket Information[/bold magenta]",
            border_style="magenta"
        ))
        
        # Description panel
        if hasattr(ticket, 'description') and ticket.description:
            console.print()
            console.print(Panel(
                ticket.description,
                title="[bold blue]Description[/bold blue]",
                border_style="blue"
            ))
        
        # Show messages if requested
        if show_messages:
            message_repo = _get_message_repo()
            
            with console.status("[bold cyan]Fetching messages...[/bold cyan]"):
                messages = asyncio.run(message_repo.get_messages_by_ticket(ticket_id))
            
            if messages:
                console.print()
                console.print(Panel.fit(
                    f"[bold cyan]Conversation ({len(messages)} messages)[/bold cyan]",
                    border_style="cyan"
                ))
                console.print()
                
                for msg in messages:
                    role_color = "green" if msg.role == "user" else "blue"
                    role_icon = "👤" if msg.role == "user" else "🤖"
                    
                    console.print(Panel(
                        msg.content,
                        title=f"[{role_color}]{role_icon} {msg.role.upper()}[/{role_color}]",
                        border_style=role_color,
                        subtitle=f"[dim]{msg.created_at.strftime('%Y-%m-%d %H:%M:%S') if hasattr(msg, 'created_at') and msg.created_at else ''}[/dim]"
                    ))
                    console.print()
        
    except Exception as e:
        console.print(f"[red]❌ Failed to fetch ticket: {str(e)}[/red]")
        raise typer.Exit(1)


@ticket_app.command()
def status(
    ticket_id: str = typer.Argument(..., help="Ticket ID"),
    new_status: str = typer.Argument(..., help="New status (open, in_progress, completed, error, validated, rejected, closed)"),
):
    """
    Update ticket status
    
    Changes the status of a ticket.
    
    Valid statuses:
        - open: Newly created ticket
        - in_progress: Currently being worked on
        - completed: Processing finished
        - error: An error occurred
        - validated: Reviewed and approved
        - rejected: Reviewed and rejected
        - closed: Ticket is closed
    
    Examples:
        autocode ticket status abc123 in_progress
        autocode ticket status abc123 completed
        autocode ticket status abc123 validated
    """
    valid_statuses = ['open', 'in_progress', 'completed', 'error', 'validated', 'rejected', 'closed']
    
    if new_status not in valid_statuses:
        console.print(f"[red]❌ Invalid status: {new_status}[/red]")
        console.print(f"[yellow]Valid statuses: {', '.join(valid_statuses)}[/yellow]")
        raise typer.Exit(1)
    
    try:
        ticket_repo = _get_ticket_repo()
        
        # Check if ticket exists
        with console.status("[bold cyan]Checking ticket...[/bold cyan]"):
            ticket = asyncio.run(ticket_repo.get_ticket_by_id(ticket_id))
        
        if not ticket:
            console.print(f"\n[red]❌ Ticket not found: {ticket_id}[/red]")
            raise typer.Exit(1)
        
        old_status = ticket.status if hasattr(ticket.status, 'value') else ticket.status
        
        # Update status
        with console.status(f"[bold cyan]Updating status to {new_status}...[/bold cyan]"):
            asyncio.run(ticket_repo.update_ticket_status(ticket_id, new_status))
        
        console.print(f"\n[green]✅ Ticket status updated[/green]")
        console.print(f"[cyan]{old_status}[/cyan] → [green]{new_status}[/green]\n")
        
    except Exception as e:
        console.print(f"\n[red]❌ Failed to update status: {str(e)}[/red]")
        raise typer.Exit(1)


@ticket_app.command()
def validate(
    ticket_id: str = typer.Argument(..., help="Ticket ID to validate"),
):
    """
    Validate a completed ticket
    
    Marks a ticket as validated (reviewed and approved).
    The ticket should be in 'completed' status.
    
    Examples:
        autocode ticket validate abc123
    """
    try:
        ticket_repo = _get_ticket_repo()
        
        # Check ticket exists and status
        with console.status("[bold cyan]Checking ticket...[/bold cyan]"):
            ticket = asyncio.run(ticket_repo.get_ticket_by_id(ticket_id))
        
        if not ticket:
            console.print(f"\n[red]❌ Ticket not found: {ticket_id}[/red]")
            raise typer.Exit(1)
        
        current_status = ticket.status if hasattr(ticket.status, 'value') else ticket.status
        if current_status != 'completed':
            console.print(f"\n[yellow]⚠️  Warning: Ticket status is '{current_status}', not 'completed'[/yellow]")
            if not typer.confirm("Do you want to validate it anyway?"):
                console.print("[dim]Validation cancelled[/dim]")
                raise typer.Exit(0)
        
        # Update to validated
        with console.status("[bold cyan]Validating ticket...[/bold cyan]"):
            asyncio.run(ticket_repo.update_ticket_status(ticket_id, 'validated'))
        
        console.print(f"\n[green]✅ Ticket validated successfully[/green]")
        console.print(f"[dim]Ticket {ticket_id} is now marked as validated[/dim]\n")
        
    except Exception as e:
        console.print(f"\n[red]❌ Failed to validate ticket: {str(e)}[/red]")
        raise typer.Exit(1)


@ticket_app.command()
def reject(
    ticket_id: str = typer.Argument(..., help="Ticket ID to reject"),
    reason: Optional[str] = typer.Option(None, "--reason", "-r", help="Rejection reason"),
):
    """
    Reject a ticket
    
    Marks a ticket as rejected (reviewed but not approved).
    Optionally provide a reason for rejection.
    
    Examples:
        autocode ticket reject abc123
        autocode ticket reject abc123 --reason "Incorrect implementation"
    """
    try:
        ticket_repo = _get_ticket_repo()
        
        # Check ticket exists
        with console.status("[bold cyan]Checking ticket...[/bold cyan]"):
            ticket = asyncio.run(ticket_repo.get_ticket_by_id(ticket_id))
        
        if not ticket:
            console.print(f"\n[red]❌ Ticket not found: {ticket_id}[/red]")
            raise typer.Exit(1)
        
        # Ask for reason if not provided
        if not reason:
            reason = typer.prompt("Rejection reason (optional, press Enter to skip)", default="", show_default=False)
        
        # Update to rejected
        with console.status("[bold cyan]Rejecting ticket...[/bold cyan]"):
            asyncio.run(ticket_repo.update_ticket_status(ticket_id, 'rejected'))
            
            # TODO: If we want to store rejection reason, we could add a note/comment
            # For now, we just update the status
        
        console.print(f"\n[red]❌ Ticket rejected[/red]")
        if reason:
            console.print(f"[yellow]Reason:[/yellow] {reason}")
        console.print(f"[dim]Ticket {ticket_id} is now marked as rejected[/dim]\n")
        
    except Exception as e:
        console.print(f"\n[red]❌ Failed to reject ticket: {str(e)}[/red]")
        raise typer.Exit(1)
