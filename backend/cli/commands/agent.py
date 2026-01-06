"""
Agent management commands
"""
import typer
import asyncio
from pathlib import Path
from rich.table import Table
from rich.panel import Panel
from rich import box
from rich.progress import Progress, SpinnerColumn, TextColumn

from cli.utils import console
from src.database import db
from src.repositories.ticket_repository import TicketRepository
from src.repositories.repository_repository import RepositoryRepository
from src.services import MessageService
from src.agent import DummyAgent

# Create sub-app for agent commands
agent_app = typer.Typer(help="Agent management and execution commands")


@agent_app.command()
def list():
    """
    List available agents
    
    Shows all available agent implementations and their capabilities.
    
    Examples:
        autocode agent list
    """
    console.print(Panel.fit(
        "[bold blue]Available Agents[/bold blue]",
        border_style="blue"
    ))
    
    # List of available agents
    agents = [
        {
            "name": "DummyAgent",
            "description": "Test agent that modifies a 'toto' file",
            "capabilities": ["create_files", "modify_files", "delete_files", "basic_validation"],
            "status": "✅ Available"
        },
        {
            "name": "ClaudeAgent",
            "description": "AI agent powered by Claude Opus 4",
            "capabilities": ["code_analysis", "code_generation", "planning", "reasoning"],
            "status": "⚠️  Disabled (langgraph issues)"
        }
    ]
    
    # Create table
    table = Table(box=box.ROUNDED, show_header=True, header_style="bold cyan")
    table.add_column("Agent", style="cyan bold")
    table.add_column("Description")
    table.add_column("Status")
    
    for agent in agents:
        table.add_row(
            agent["name"],
            agent["description"],
            agent["status"]
        )
    
    console.print(table)
    
    # Show capabilities
    console.print("\n[bold]Capabilities:[/bold]")
    for agent in agents:
        console.print(f"\n[cyan]{agent['name']}:[/cyan]")
        for cap in agent["capabilities"]:
            console.print(f"  • {cap}")


@agent_app.command()
def run(
    ticket_id: str = typer.Argument(..., help="Ticket ID to process"),
    agent_name: str = typer.Option("DummyAgent", "--agent", "-a", help="Agent to use"),
    workspace: str = typer.Option(
        None,
        "--workspace", "-w",
        help="Workspace directory (default: ../workspace)"
    )
):
    """
    Run an agent to process a ticket
    
    The agent will:
    1. Load the ticket from database
    2. Get or create initial message
    3. Process the ticket
    4. Make file modifications
    5. Validate changes
    
    Examples:
        autocode agent run ticket-123
        autocode agent run ticket-123 --agent DummyAgent
        autocode agent run ticket-123 -w /path/to/workspace
    """
    console.print(Panel.fit(
        f"[bold blue]Running Agent: {agent_name}[/bold blue]",
        border_style="blue"
    ))
    
    try:
        # Connect to database
        db.connect()
        
        # Get ticket
        console.print(f"\n[bold cyan]Step 1/5:[/bold cyan] Loading ticket...")
        
        ticket_repo = TicketRepository(db)
        ticket = asyncio.run(ticket_repo.get_ticket_by_id(ticket_id))
        
        if not ticket:
            console.print(f"[red]❌ Ticket not found: {ticket_id}[/red]")
            raise typer.Exit(1)
        
        console.print(f"[green]✅ Ticket loaded: {ticket.title}[/green]")
        
        # Show ticket info
        ticket_table = Table(box=box.ROUNDED, show_header=False, padding=(0, 1))
        ticket_table.add_column("Field", style="cyan bold", width=12)
        ticket_table.add_column("Value")
        
        ticket_table.add_row("ID", str(ticket.id))
        ticket_table.add_row("Title", ticket.title)
        ticket_table.add_row("Type", ticket.ticket_type.value if ticket.ticket_type else "N/A")
        ticket_table.add_row("Priority", ticket.priority.value if ticket.priority else "N/A")
        ticket_table.add_row("Status", ticket.status.value if ticket.status else "N/A")
        
        console.print(ticket_table)
        
        # Get repository
        console.print(f"\n[bold cyan]Step 2/5:[/bold cyan] Finding repository...")
        
        repo_repo = RepositoryRepository(db)
        
        if ticket.repository_id:
            repository = asyncio.run(repo_repo.get_repository_by_id(ticket.repository_id))
            if repository:
                console.print(f"[green]✅ Repository: {repository.full_name}[/green]")
                repo_name = repository.full_name
            else:
                console.print(f"[yellow]⚠️  Repository not found in DB[/yellow]")
                repo_name = "unknown"
        else:
            console.print(f"[yellow]⚠️  No repository linked to ticket[/yellow]")
            repo_name = "unknown"
        
        # Get or create initial message
        console.print(f"\n[bold cyan]Step 3/5:[/bold cyan] Getting initial message...")
        
        message_service = MessageService()
        initial_message = message_service.get_or_create_initial_message(ticket, repo_name)
        
        is_new = initial_message.metadata and initial_message.metadata.get('source') == 'auto_generated'
        console.print(f"[green]✅ Message: {'created' if is_new else 'found'}[/green]")
        
        # Determine workspace path
        if workspace is None:
            workspace = str(Path(__file__).parent.parent.parent.parent / "workspace")
        
        workspace_path = Path(workspace)
        
        # Determine repository path
        if repo_name and repo_name != "unknown":
            # Extract owner/repo from full_name
            parts = repo_name.split('/')
            if len(parts) == 2:
                repo_path = workspace_path / parts[0] / parts[1]
            else:
                repo_path = workspace_path / repo_name
        else:
            repo_path = workspace_path / "test-repo"
        
        if not repo_path.exists():
            console.print(f"[yellow]⚠️  Repository not found at {repo_path}[/yellow]")
            console.print(f"[yellow]Creating directory...[/yellow]")
            repo_path.mkdir(parents=True, exist_ok=True)
        
        console.print(f"[dim]Repository path: {repo_path}[/dim]")
        
        # Initialize agent
        console.print(f"\n[bold cyan]Step 4/5:[/bold cyan] Initializing agent...")
        
        if agent_name == "DummyAgent":
            agent = DummyAgent(workspace_root=str(workspace_path))
        else:
            console.print(f"[red]❌ Unknown agent: {agent_name}[/red]")
            console.print(f"[yellow]Available agents: DummyAgent[/yellow]")
            raise typer.Exit(1)
        
        console.print(f"[green]✅ Agent initialized: {agent.get_agent_name()}[/green]")
        console.print(f"[dim]Capabilities: {', '.join(agent._get_capabilities())}[/dim]")
        
        # Process ticket
        console.print(f"\n[bold cyan]Step 5/5:[/bold cyan] Processing ticket...")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("[cyan]Agent working...", total=None)
            
            try:
                result = agent.process_ticket(ticket, repo_path, initial_message)
                progress.update(task, completed=True)
            except Exception as e:
                progress.update(task, completed=True)
                raise e
        
        # Show results
        if result["success"]:
            console.print(f"\n[green]✅ Processing completed successfully![/green]")
            
            console.print(f"\n[bold]Files modified:[/bold]")
            for file_path in result["files_modified"]:
                console.print(f"  • {file_path}")
            
            console.print(f"\n[bold]Message:[/bold]")
            console.print(Panel(result["message"], border_style="green", padding=(0, 1)))
            
            # Show validation results if available
            if "details" in result and "validation" in result["details"]:
                validation = result["details"]["validation"]
                
                if validation.get("warnings"):
                    console.print(f"\n[yellow]Warnings:[/yellow]")
                    for warning in validation["warnings"]:
                        console.print(f"  ⚠️  {warning}")
        else:
            console.print(f"\n[red]❌ Processing failed![/red]")
            console.print(f"[red]{result['message']}[/red]")
            
            if "details" in result and "validation" in result["details"]:
                validation = result["details"]["validation"]
                
                if validation.get("errors"):
                    console.print(f"\n[red]Errors:[/red]")
                    for error in validation["errors"]:
                        console.print(f"  ❌ {error}")
            
            raise typer.Exit(1)
        
        # Summary
        console.print(f"\n")
        console.print(Panel(
            f"[bold green]Agent Processing Complete! 🤖[/bold green]\n\n"
            f"[cyan]Agent:[/cyan] {agent_name}\n"
            f"[cyan]Ticket:[/cyan] {ticket.title}\n"
            f"[cyan]Files Modified:[/cyan] {len(result['files_modified'])}\n"
            f"[cyan]Repository:[/cyan] {repo_path}\n\n"
            f"[dim]Check the modified files to see the agent's work![/dim]",
            title="[bold magenta]Summary[/bold magenta]",
            border_style="green"
        ))
        
    except typer.Exit:
        raise
    except Exception as e:
        console.print(f"\n[red]❌ Agent execution failed: {str(e)}[/red]")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")
        raise typer.Exit(1)


@agent_app.command()
def info(
    agent_name: str = typer.Argument(..., help="Agent name to get info about")
):
    """
    Get detailed information about an agent
    
    Examples:
        autocode agent info DummyAgent
    """
    console.print(Panel.fit(
        f"[bold blue]Agent Information: {agent_name}[/bold blue]",
        border_style="blue"
    ))
    
    try:
        if agent_name == "DummyAgent":
            agent = DummyAgent()
            info = agent.get_agent_info()
            
            console.print(f"\n[bold cyan]Name:[/bold cyan] {info['name']}")
            console.print(f"[bold cyan]Workspace:[/bold cyan] {info['workspace_root']}")
            
            console.print(f"\n[bold cyan]Capabilities:[/bold cyan]")
            for cap in info['capabilities']:
                console.print(f"  • {cap}")
            
            console.print(f"\n[bold cyan]Description:[/bold cyan]")
            console.print(Panel(
                "Test agent that creates/modifies a 'toto' file with ticket information.\n"
                "Used for testing the agent interface and workflow.",
                border_style="dim"
            ))
            
        else:
            console.print(f"[red]❌ Unknown agent: {agent_name}[/red]")
            console.print(f"\n[yellow]Available agents:[/yellow]")
            console.print("  • DummyAgent")
            raise typer.Exit(1)
    
    except typer.Exit:
        raise
    except Exception as e:
        console.print(f"[red]❌ Error: {str(e)}[/red]")
        raise typer.Exit(1)
