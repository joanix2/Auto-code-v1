"""
Quickstart workflow commands
"""
import os
import uuid
import typer
import asyncio
from pathlib import Path
from datetime import datetime
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich import box

from cli.utils import console, get_github_service, get_stored_token
from src.services import GitService, BranchService, MessageService
from src.services.git import PullRequestService
from src.database import db
from src.repositories.ticket_repository import TicketRepository
from src.repositories.repository_repository import RepositoryRepository
from src.models.ticket import TicketStatus
from src.models.message import Message
from src.agent.dummy_agent import DummyAgent

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
    6. Executes DummyAgent to modify code
    7. Commits and pushes changes
    8. Creates a Pull Request
    
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
        console.print("\n[bold cyan]Step 1/8:[/bold cyan] Vérification de l'authentification...")
        
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
        console.print("\n[bold cyan]Step 2/8:[/bold cyan] Clonage du dépôt Auto-code-v1...")
        
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
        console.print("\n[bold cyan]Step 3/8:[/bold cyan] Récupération du prochain ticket...")
        
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
        console.print(f"\n[bold cyan]Step 4/8:[/bold cyan] Gestion de la branche...")
        
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
        
        # Step 5: Get or create initial message
        console.print(f"\n[bold cyan]Step 5/8:[/bold cyan] Récupération du message initial...")
        
        message_service = MessageService()
        
        with console.status("[cyan]Récupération ou création du message initial...[/cyan]"):
            try:
                # Use new method to get existing or create initial message
                message = message_service.get_or_create_initial_message(
                    ticket=next_ticket,
                    repository_name=repository.name if repository else None
                )
                
                is_new = message.metadata and message.metadata.get('source') == 'auto_generated'
                
                if is_new:
                    console.print(f"[green]✅ Message initial créé automatiquement:[/green]\n")
                else:
                    console.print(f"[green]✅ Message existant récupéré:[/green]\n")
                
                message_table = Table(box=box.ROUNDED, show_header=False, padding=(0, 1))
                message_table.add_column("Field", style="cyan bold", width=12)
                message_table.add_column("Value")
                
                # Get sender from metadata or use role
                sender = message.metadata.get('sender', message.role) if message.metadata else message.role
                message_table.add_row("De", sender)
                message_table.add_row("Rôle", message.role)
                if message.timestamp:
                    message_table.add_row("Date", message.timestamp.strftime('%Y-%m-%d %H:%M:%S'))
                if is_new:
                    message_table.add_row("Type", "Auto-généré")
                
                console.print(message_table)
                console.print(f"\n[bold]Contenu:[/bold]")
                console.print(Panel(message.content, border_style="green", padding=(0, 1)))
                
                # Get message count
                message_count = message_service.get_message_count(next_ticket.id)
                console.print(f"\n[dim]Total: {message_count} message{'s' if message_count > 1 else ''}[/dim]")
                    
            except Exception as e:
                console.print(f"[red]❌ Erreur lors de la gestion du message: {str(e)}[/red]")
                import traceback
                console.print(f"[dim]{traceback.format_exc()}[/dim]")
        
        # Step 6: Execute DummyAgent to modify code
        console.print(f"\n[bold cyan]Step 6/8:[/bold cyan] Exécution du DummyAgent pour modifier le code...")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("[cyan]DummyAgent en cours d'exécution...", total=None)
            
            try:
                # Initialize DummyAgent
                agent = DummyAgent(workspace_root=str(workspace_dir))
                
                # Execute agent workflow - pass the actual repo path
                result = agent.process_ticket(next_ticket, repo_path)
                
                progress.update(task, completed=True)
                
                if result.get("success"):
                    console.print(f"[green]✅ DummyAgent a modifié le code avec succès[/green]")
                    
                    # Show modifications
                    files_modified = result.get("files_modified", [])
                    if files_modified:
                        mod_table = Table(title="Fichiers modifiés", box=box.ROUNDED)
                        mod_table.add_column("Fichier", style="cyan")
                        mod_table.add_column("Chemin", style="dim")
                        
                        for file_path in files_modified:
                            # Extract just the filename
                            file_name = Path(file_path).name
                            mod_table.add_row(file_name, str(file_path))
                        
                        console.print(mod_table)
                else:
                    console.print(f"[yellow]⚠️  DummyAgent a rencontré un problème: {result.get('message')}[/yellow]")
                    
            except Exception as e:
                progress.update(task, completed=True)
                console.print(f"[red]❌ Erreur lors de l'exécution du DummyAgent: {str(e)}[/red]")
                console.print(f"[yellow]⚠️  Continuons quand même...[/yellow]")
        
        # Step 7: Add, Commit and Push changes
        console.print(f"\n[bold cyan]Step 7/8:[/bold cyan] Commit et push des changements...")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("[cyan]Add, commit et push en cours...", total=None)
            
            try:
                # Check if there are changes to commit
                full_repo_url = f"https://github.com/{repo_name}"
                
                if git_service.has_uncommitted_changes(full_repo_url):
                    # Commit message based on ticket
                    commit_message = f"feat: {next_ticket.title}"
                    
                    # Perform add, commit and push
                    commit_result = git_service.add_commit_and_push(
                        repo_url=full_repo_url,
                        commit_message=commit_message,
                        branch_name=branch_name,
                        token=token
                    )
                    
                    progress.update(task, completed=True)
                    
                    if commit_result.get("success"):
                        commit_hash = commit_result.get("commit_hash", "")[:7]
                        console.print(f"[green]✅ Changements committés et pushés: {commit_hash}[/green]")
                        console.print(f"[dim]{commit_message}[/dim]")
                        
                        # Add message to ticket
                        commit_msg = Message(
                            id=str(uuid.uuid4()),
                            ticket_id=next_ticket.id,
                            role="system",
                            content=f"Changements committés et pushés: {commit_hash}\n{commit_message}",
                            timestamp=datetime.now(),
                            metadata={
                                "commit_hash": commit_result.get("commit_hash"),
                                "branch": branch_name,
                                "source": "quickstart"
                            }
                        )
                        message_service.create_message(commit_msg)
                    else:
                        console.print(f"[yellow]⚠️  Échec du commit/push: {commit_result.get('message')}[/yellow]")
                        console.print(f"[yellow]⚠️  Impossible de créer la PR sans commit[/yellow]")
                        raise Exception("Commit failed")
                else:
                    progress.update(task, completed=True)
                    console.print(f"[yellow]⚠️  Aucun changement à committer[/yellow]")
                    console.print(f"[yellow]⚠️  Impossible de créer la PR sans changements[/yellow]")
                    raise Exception("No changes to commit")
                    
            except Exception as e:
                progress.update(task, completed=True)
                if "Commit failed" not in str(e) and "No changes" not in str(e):
                    console.print(f"[red]❌ Erreur lors du commit/push: {str(e)}[/red]")
                # Skip PR creation if commit failed
                raise
        
        # Step 8: Create Pull Request
        console.print(f"\n[bold cyan]Step 8/8:[/bold cyan] Création de la Pull Request...")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("[cyan]Création de la PR...", total=None)
            
            try:
                # Get GitHub token
                github_token = os.getenv("GITHUB_TOKEN") or get_stored_token()
                if not github_token:
                    raise Exception("GITHUB_TOKEN not found")
                
                # Initialize PR service
                pr_service = PullRequestService(github_token)
                
                # Prepare PR details
                pr_title = f"feat: {next_ticket.title}"
                pr_body = f"""## {next_ticket.title}

**Type:** {next_ticket.ticket_type.value}
**Priority:** {next_ticket.priority.value}

### Description
{next_ticket.description or 'No description provided'}

### Changes
- Code modifications by DummyAgent
- Automated workflow via quickstart

---
Closes #{next_ticket.id}
"""
                
                # Create PR
                pr_result = pr_service.create_pull_request(
                    repo_full_name=repo_name,
                    title=pr_title,
                    body=pr_body,
                    head_branch=branch_name,
                    base_branch="main",
                    draft=False
                )
                
                progress.update(task, completed=True)
                
                if pr_result.get("success"):
                    pr_number = pr_result.get("pr_number")
                    pr_url = pr_result.get("pr_url")
                    
                    console.print(f"[green]✅ Pull Request créée: #{pr_number}[/green]")
                    console.print(f"[cyan]{pr_url}[/cyan]")
                    
                    # Add message to ticket
                    pr_msg = Message(
                        id=str(uuid.uuid4()),
                        ticket_id=next_ticket.id,
                        role="system",
                        content=f"Pull Request créée: #{pr_number}\n{pr_url}",
                        timestamp=datetime.now(),
                        metadata={
                            "pr_number": pr_number,
                            "pr_url": pr_url,
                            "source": "quickstart"
                        }
                    )
                    message_service.create_message(pr_msg)
                else:
                    console.print(f"[yellow]⚠️  Échec de la création de PR: {pr_result.get('message')}[/yellow]")
                    
            except Exception as e:
                progress.update(task, completed=True)
                console.print(f"[red]❌ Erreur lors de la création de la PR: {str(e)}[/red]")
                console.print(f"[yellow]⚠️  Vous pouvez créer la PR manuellement avec:[/yellow]")
                console.print(f"[cyan]autocode git pr {next_ticket.id}[/cyan]")
        
        # Summary
        console.print(f"\n")
        
        # Try to get PR info if available
        pr_info = ""
        try:
            # Get last message to check for PR
            messages = message_service.get_messages_by_ticket(next_ticket.id)
            pr_messages = [m for m in messages if m.metadata and m.metadata.get("pr_number")]
            if pr_messages:
                last_pr = pr_messages[-1]
                pr_number = last_pr.metadata.get("pr_number")
                pr_url = last_pr.metadata.get("pr_url")
                pr_info = f"[cyan]Pull Request:[/cyan] #{pr_number}\n[cyan]URL:[/cyan] {pr_url}\n"
        except:
            pass
        
        console.print(Panel(
            f"[bold green]Pipeline Complète! 🎉[/bold green]\n\n"
            f"[cyan]Utilisateur:[/cyan] {user_info['login']}\n"
            f"[cyan]Dépôt:[/cyan] {repo_name}\n"
            f"[cyan]Location:[/cyan] {repo_path}\n"
            f"[cyan]Ticket:[/cyan] {next_ticket.title}\n"
            f"[cyan]Branche:[/cyan] {branch_name or 'N/A'}\n"
            f"{pr_info}\n"
            f"[dim]Le workflow complet a été exécuté:[/dim]\n"
            f"[green]✓[/green] Authentification\n"
            f"[green]✓[/green] Clone/Pull du dépôt\n"
            f"[green]✓[/green] Ticket récupéré\n"
            f"[green]✓[/green] Branche créée\n"
            f"[green]✓[/green] Message initial\n"
            f"[green]✓[/green] Code modifié (DummyAgent)\n"
            f"[green]✓[/green] Commit & Push\n"
            f"[green]✓[/green] Pull Request créée",
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

