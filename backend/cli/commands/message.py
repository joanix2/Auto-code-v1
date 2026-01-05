"""
Message management commands
"""
import typer
from typing import Optional
from rich.table import Table
from rich.panel import Panel
from rich import box

from cli.utils import console
from src.database import db
from src.services.message_service import MessageService

# Create sub-app for message commands
message_app = typer.Typer(help="Message management commands")


def _get_message_service():
    """Get message service instance"""
    db.connect()  # Ensure database is connected
    return MessageService()


@message_app.command()
def count(
    ticket_id: str = typer.Argument(..., help="Ticket ID to count messages for"),
):
    """
    Get the number of messages for a ticket
    
    Examples:
        autocode message count ticket-123
    """
    console.print(Panel.fit(
        "[bold blue]Message Count[/bold blue]",
        border_style="blue"
    ))
    
    try:
        service = _get_message_service()
        
        with console.status("[bold cyan]Counting messages...[/bold cyan]"):
            count = service.get_message_count(ticket_id)
        
        console.print()
        console.print(f"[green]Ticket {ticket_id} has {count} message{'s' if count != 1 else ''}[/green]")
        console.print()
        
    except Exception as e:
        console.print(f"[red]❌ Failed to count messages: {str(e)}[/red]")
        raise typer.Exit(1)


@message_app.command()
def check_limit(
    ticket_id: str = typer.Argument(..., help="Ticket ID to check"),
    limit: int = typer.Argument(..., help="Message limit to check against"),
):
    """
    Check if message count exceeds a limit
    
    Examples:
        autocode message check-limit ticket-123 50
    """
    console.print(Panel.fit(
        "[bold blue]Message Limit Check[/bold blue]",
        border_style="blue"
    ))
    
    try:
        service = _get_message_service()
        
        with console.status("[bold cyan]Checking limit...[/bold cyan]"):
            result = service.check_limit_and_get_stats(ticket_id, limit)
        
        console.print()
        
        # Create info table
        info_table = Table(show_header=False, box=box.SIMPLE, padding=(0, 2))
        info_table.add_column("Field", style="cyan bold", width=15)
        info_table.add_column("Value", style="white")
        
        info_table.add_row("Ticket ID", ticket_id)
        info_table.add_row("Message Count", str(result['count']))
        info_table.add_row("Limit", str(result['limit']))
        info_table.add_row("Remaining", str(result['remaining']))
        
        # Status with color
        if result['over_limit']:
            status_text = f"[red]OVER LIMIT ⚠️[/red]"
            border_color = "red"
        else:
            status_text = f"[green]Within Limit ✓[/green]"
            border_color = "green"
        
        info_table.add_row("Status", status_text)
        
        console.print(Panel(
            info_table,
            title=f"[bold]Limit Check[/bold]",
            border_style=border_color
        ))
        
        # Show last message if available
        if result.get('last_message'):
            last_msg = result['last_message']
            console.print()
            console.print(Panel(
                f"[bold]{last_msg.role}:[/bold] {last_msg.content[:100]}{'...' if len(last_msg.content) > 100 else ''}",
                title="[bold dim]Last Message[/bold dim]",
                border_style="dim"
            ))
        
        console.print()
        
        if result['over_limit']:
            raise typer.Exit(1)
        
    except Exception as e:
        console.print(f"[red]❌ Failed to check limit: {str(e)}[/red]")
        raise typer.Exit(1)


@message_app.command()
def last(
    ticket_id: str = typer.Argument(..., help="Ticket ID to get last message from"),
    show_metadata: bool = typer.Option(False, "--metadata", "-m", help="Show message metadata"),
):
    """
    Get the last message for a ticket
    
    Examples:
        autocode message last ticket-123
        autocode message last ticket-123 --metadata
    """
    console.print(Panel.fit(
        "[bold blue]Last Message[/bold blue]",
        border_style="blue"
    ))
    
    try:
        service = _get_message_service()
        
        with console.status("[bold cyan]Fetching last message...[/bold cyan]"):
            message = service.get_last_message(ticket_id)
        
        if not message:
            console.print(f"\n[yellow]No messages found for ticket {ticket_id}[/yellow]")
            return
        
        console.print()
        
        # Role colors
        role_colors = {
            'user': 'blue',
            'assistant': 'magenta',
            'system': 'dim'
        }
        role_color = role_colors.get(message.role, 'white')
        
        # Create message display
        info_table = Table(show_header=False, box=box.SIMPLE, padding=(0, 2))
        info_table.add_column("Field", style="cyan bold", width=15)
        info_table.add_column("Value", style="white")
        
        info_table.add_row("Role", f"[{role_color}]{message.role}[/{role_color}]")
        info_table.add_row("Timestamp", message.timestamp.strftime('%Y-%m-%d %H:%M:%S'))
        
        if message.model:
            info_table.add_row("Model", message.model)
        
        if message.tokens_used:
            info_table.add_row("Tokens Used", str(message.tokens_used))
        
        if message.step:
            info_table.add_row("Step", message.step)
        
        console.print(Panel(
            info_table,
            title=f"[bold]Message Info[/bold]",
            border_style=role_color
        ))
        
        console.print()
        console.print(Panel(
            message.content,
            title="[bold]Content[/bold]",
            border_style="white"
        ))
        
        if show_metadata and message.metadata:
            console.print()
            import json
            console.print(Panel(
                json.dumps(message.metadata, indent=2),
                title="[bold]Metadata[/bold]",
                border_style="dim"
            ))
        
        console.print()
        
    except Exception as e:
        console.print(f"[red]❌ Failed to get last message: {str(e)}[/red]")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")
        raise typer.Exit(1)


@message_app.command()
def stats(
    ticket_id: str = typer.Argument(..., help="Ticket ID to get stats for"),
):
    """
    Get message statistics for a ticket
    
    Examples:
        autocode message stats ticket-123
    """
    console.print(Panel.fit(
        "[bold blue]Message Statistics[/bold blue]",
        border_style="blue"
    ))
    
    try:
        service = _get_message_service()
        
        with console.status("[bold cyan]Calculating statistics...[/bold cyan]"):
            stats = service.get_message_stats(ticket_id)
        
        console.print()
        
        if stats['total'] == 0:
            console.print(f"[yellow]No messages found for ticket {ticket_id}[/yellow]")
            return
        
        # Create stats table
        stats_table = Table(show_header=False, box=box.ROUNDED, padding=(0, 2))
        stats_table.add_column("Metric", style="cyan bold", width=20)
        stats_table.add_column("Value", style="white", justify="right")
        
        stats_table.add_row("Total Messages", str(stats['total']))
        stats_table.add_row("User Messages", f"[blue]{stats['user_messages']}[/blue]")
        stats_table.add_row("Assistant Messages", f"[magenta]{stats['assistant_messages']}[/magenta]")
        stats_table.add_row("System Messages", f"[dim]{stats['system_messages']}[/dim]")
        stats_table.add_row("Total Tokens", f"[yellow]{stats['total_tokens']:,}[/yellow]")
        
        if stats.get('first_message_at'):
            stats_table.add_row("First Message", stats['first_message_at'].strftime('%Y-%m-%d %H:%M'))
        
        if stats.get('last_message_at'):
            stats_table.add_row("Last Message", stats['last_message_at'].strftime('%Y-%m-%d %H:%M'))
        
        console.print(Panel(
            stats_table,
            title=f"[bold green]Statistics for {ticket_id}[/bold green]",
            border_style="green"
        ))
        
        console.print()
        
    except Exception as e:
        console.print(f"[red]❌ Failed to get statistics: {str(e)}[/red]")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")
        raise typer.Exit(1)


@message_app.command()
def list(
    ticket_id: str = typer.Argument(..., help="Ticket ID to list messages from"),
    limit: Optional[int] = typer.Option(None, "--limit", "-l", help="Limit number of messages"),
):
    """
    List all messages for a ticket
    
    Examples:
        autocode message list ticket-123
        autocode message list ticket-123 --limit 10
    """
    console.print(Panel.fit(
        "[bold blue]Messages[/bold blue]",
        border_style="blue"
    ))
    
    try:
        service = _get_message_service()
        
        with console.status("[bold cyan]Fetching messages...[/bold cyan]"):
            messages = service.get_messages(ticket_id, limit=limit)
        
        if not messages:
            console.print(f"\n[yellow]No messages found for ticket {ticket_id}[/yellow]")
            return
        
        console.print(f"\n[green]Found {len(messages)} message{'s' if len(messages) != 1 else ''}:[/green]\n")
        
        # Role colors
        role_colors = {
            'user': 'blue',
            'assistant': 'magenta',
            'system': 'dim'
        }
        
        # Display messages
        for i, msg in enumerate(messages, 1):
            role_color = role_colors.get(msg.role, 'white')
            timestamp = msg.timestamp.strftime('%Y-%m-%d %H:%M')
            
            # Truncate content for list view
            content = msg.content[:150] + "..." if len(msg.content) > 150 else msg.content
            
            console.print(Panel(
                f"[{role_color}]{msg.role.upper()}[/{role_color}] • {timestamp}\n\n{content}",
                title=f"[dim]Message {i}/{len(messages)}[/dim]",
                border_style=role_color
            ))
            console.print()
        
    except Exception as e:
        console.print(f"[red]❌ Failed to list messages: {str(e)}[/red]")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")
        raise typer.Exit(1)
