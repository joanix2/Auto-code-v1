"""
Quickstart workflow commands
"""
import typer
import asyncio
from pathlib import Path
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich import box

from cli.utils import console, get_github_service, get_stored_token
from src.services import GitService, BranchService, MessageService
from src.database import db
from src.repositories.ticket_repository import TicketRepository
from src.repositories.repository_repository import RepositoryRepository
from src.models.ticket import TicketStatus

# Create sub-app for quickstart commands
quickstart_app = typer.Typer(help="Quick workflow automation")


@quickstart_app.callback(invoke_without_command=True)
def quickstart(ctx: typer.Context):
    """
    Complete workflow automation
    
    Performs the complete development workflow:
    1. Checks authentication
    2. Clones Auto-code-v1 repository
    3. Gets the next open ticket
    4. Creates/checkouts a branch for the ticket
    5. Retrieves the last message from the ticket
    
    This command automates the entire setup and ticket workflow.
    
    Examples:
        autocode quickstart
    """
    if ctx.invoked_subcommand is not None:
        return
    
    console.print(Panel.fit(
        "[bold blue]AutoCode Workflow - Pipeline Complete[/bold blue]",
        border_style="blue"
    ))
    
    try:
        # Connect to database
        db.connect()
        ticket_repo = TicketRepository(db)
        repo_repo = RepositoryRepository(db)
        
        # Step 1: Check authentication
        console.print("\n[bold cyan]Step 1/5:[/bold cyan] Vérification de l'authentification...")
        
        try:
            github_service = get_github_service()
            if not github_service:
                raise FileNotFoundError("No token found")
            user_info = asyncio.run(github_service.get_authenticated_user())
            console.print(f"[green]✅ Authentifié en tant que {user_info['login']}[/green]")
        except (FileNotFoundError, Exception):
            console.print("[red]❌ Non authentifié[/red]")
            console.print("\n[yellow]Veuillez vous authentifier d'abord:[/yellow]")
            console.print("[cyan]autocode auth login[/cyan]\n")
            raise typer.Exit(1)
        
        # Step 2: Clone Auto-code-v1 repository
        console.print("\n[bold cyan]Step 2/5:[/bold cyan] Clonage du dépôt Auto-code-v1...")
        
        # Set workspace directory
        workspace_dir = Path(__file__).parent.parent.parent.parent / "workspace"
        workspace_dir.mkdir(exist_ok=True)
        
        # Create git service with workspace directory
        git_service = GitService(workspace_root=str(workspace_dir))
        
        # Build GitHub URL for Auto-code-v1
        repo_url = "https://github.com/joanix2/Auto-code-v1.git"
        repo_name = "joanix2/Auto-code-v1"
        
        # Get token
        token = get_stored_token()
        
        # Check if already cloned
        repo_path = workspace_dir / "joanix2" / "Auto-code-v1"
        
        if repo_path.exists():
            console.print(f"[yellow]⚠️  Dépôt déjà cloné[/yellow]")
            console.print(f"[dim]Location: {repo_path}[/dim]")
            
            # Pull latest changes
            with console.status("[cyan]Mise à jour du dépôt...[/cyan]"):
                try:
                    git_service.pull(repo_name)
                    console.print(f"[green]✅ Dépôt mis à jour[/green]")
                except Exception as e:
                    console.print(f"[yellow]⚠️  Impossible de mettre à jour: {str(e)}[/yellow]")
        else:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("[cyan]Clonage du dépôt...", total=None)
                
                try:
                    result = git_service.clone(repo_url, token=token)
                    progress.update(task, completed=True)
                    console.print(f"[green]✅ Dépôt cloné avec succès[/green]")
                    console.print(f"[dim]Location: {result}[/dim]")
                except Exception as e:
                    progress.update(task, completed=True)
                    console.print(f"[red]❌ Échec du clonage: {str(e)}[/red]")
                    raise typer.Exit(1)
        
        # Step 3: Get next ticket
        console.print("\n[bold cyan]Step 3/5:[/bold cyan] Récupération du prochain ticket...")
        
        with console.status("[bold cyan]Recherche du prochain ticket...[/bold cyan]"):
            # Find repository in database
            try:
                # Get all repositories and find Auto-code-v1
                all_repos = asyncio.run(repo_repo.get_repositories_by_owner("joanix2"))
                repository = next((r for r in all_repos if r.name == "Auto-code-v1" or r.full_name == "joanix2/Auto-code-v1"), None)
                
                if not repository:
                    console.print("[red]❌ Dépôt Auto-code-v1 non trouvé dans la base de données[/red]")
                    console.print("\n[yellow]Conseil: Synchronisez vos dépôts avec:[/yellow]")
                    console.print("[cyan]autocode repos sync[/cyan]\n")
                    raise typer.Exit(1)
                
                # Get open tickets for this repository
                tickets = asyncio.run(ticket_repo.get_tickets_by_repository(repository.id))
                open_tickets = [t for t in tickets if t.status == TicketStatus.open]
                
                if not open_tickets:
                    console.print("[yellow]⚠️  Aucun ticket ouvert trouvé[/yellow]")
                    console.print("\n[dim]Créez un ticket sur l'interface web ou avec la commande:[/dim]")
                    console.print("[cyan]autocode ticket create[/cyan]\n")
                    raise typer.Exit(0)
                
                # Sort by order
                open_tickets.sort(key=lambda t: t.order)
                next_ticket = open_tickets[0]
                
            except typer.Exit:
                raise
            except Exception as e:
                console.print(f"[red]❌ Erreur lors de la récupération du ticket: {str(e)}[/red]")
                raise typer.Exit(1)
        
        console.print(f"[green]✅ Prochain ticket trouvé ({len(open_tickets)} ticket{'s' if len(open_tickets) > 1 else ''} ouvert{'s' if len(open_tickets) > 1 else ''}):[/green]\n")
        
        # Display ticket info
        info_table = Table(box=box.ROUNDED, show_header=False, padding=(0, 1))
        info_table.add_column("Field", style="cyan bold", width=12)
        info_table.add_column("Value")
        
        info_table.add_row("ID", str(next_ticket.id))
        info_table.add_row("Titre", next_ticket.title)
        info_table.add_row("Statut", f"[yellow]{next_ticket.status.value}[/yellow]")
        info_table.add_row("Priorité", next_ticket.priority.value)
        info_table.add_row("Type", next_ticket.ticket_type.value)
        info_table.add_row("Ordre", str(next_ticket.order))
        
        console.print(info_table)
        
        if next_ticket.description:
            console.print(f"\n[bold]Description:[/bold]")
            console.print(Panel(next_ticket.description, border_style="dim", padding=(0, 1)))
        
        # Step 4: Create/checkout branch
        console.print(f"\n[bold cyan]Step 4/5:[/bold cyan] Gestion de la branche...")
        
        branch_service = BranchService(workspace_root=str(workspace_dir))
        
        with console.status("[cyan]Création/checkout de la branche...[/cyan]"):
            try:
                # Use full GitHub URL for proper path resolution
                full_repo_url = f"https://github.com/{repo_name}"
                branch_name, was_created = branch_service.ensure_branch_for_ticket(
                    ticket=next_ticket,
                    repo_url=full_repo_url,
                    base_branch="main"
                )
                if was_created:
                    console.print(f"[green]✅ Branche créée et active: {branch_name}[/green]")
                else:
                    console.print(f"[green]✅ Branche active: {branch_name}[/green]")
            except Exception as e:
                console.print(f"[red]❌ Erreur lors de la gestion de la branche: {str(e)}[/red]")
                console.print(f"[yellow]⚠️  Continuons avec la branche courante[/yellow]")
                branch_name = None
        
        # Step 5: Get last message
        console.print(f"\n[bold cyan]Step 5/5:[/bold cyan] Récupération du dernier message...")
        
        message_service = MessageService()
        
        with console.status("[cyan]Récupération des messages...[/cyan]"):
            try:
                last_message = message_service.get_last_message(next_ticket.id)
                
                if last_message:
                    console.print(f"[green]✅ Dernier message trouvé:[/green]\n")
                    
                    message_table = Table(box=box.ROUNDED, show_header=False, padding=(0, 1))
                    message_table.add_column("Field", style="cyan bold", width=12)
                    message_table.add_column("Value")
                    
                    # Get sender from metadata or use role
                    sender = last_message.metadata.get('sender', last_message.role) if last_message.metadata else last_message.role
                    message_table.add_row("De", sender)
                    message_table.add_row("Rôle", last_message.role)
                    if last_message.timestamp:
                        message_table.add_row("Date", last_message.timestamp.strftime('%Y-%m-%d %H:%M:%S'))
                    
                    console.print(message_table)
                    console.print(f"\n[bold]Contenu:[/bold]")
                    console.print(Panel(last_message.content, border_style="green", padding=(0, 1)))
                    
                    # Get message count
                    message_count = message_service.get_message_count(next_ticket.id)
                    console.print(f"\n[dim]Total: {message_count} message{'s' if message_count > 1 else ''}[/dim]")
                else:
                    console.print(f"[yellow]⚠️  Aucun message trouvé pour ce ticket[/yellow]")
                    
            except Exception as e:
                console.print(f"[red]❌ Erreur lors de la récupération du message: {str(e)}[/red]")
        
        # Summary
        console.print(f"\n")
        console.print(Panel(
            f"[bold green]Pipeline Complète! 🎉[/bold green]\n\n"
            f"[cyan]Utilisateur:[/cyan] {user_info['login']}\n"
            f"[cyan]Dépôt:[/cyan] {repo_name}\n"
            f"[cyan]Location:[/cyan] {repo_path}\n"
            f"[cyan]Ticket:[/cyan] {next_ticket.title}\n"
            f"[cyan]Branche:[/cyan] {branch_name or 'N/A'}\n\n"
            f"[dim]Vous pouvez maintenant travailler sur le ticket ![/dim]",
            title="[bold magenta]Résumé[/bold magenta]",
            border_style="green"
        ))
        
    except typer.Exit:
        raise
    except Exception as e:
        console.print(f"\n[red]❌ Quickstart échoué: {str(e)}[/red]")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")
        raise typer.Exit(1)

