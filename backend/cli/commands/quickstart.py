"""
Quickstart workflow commands
"""
import typer
import asyncio
from pathlib import Path
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from cli.utils import console, get_github_service, get_stored_token
from src.services.git_service import GitService

# Create sub-app for quickstart commands
quickstart_app = typer.Typer(help="Quick workflow automation")


@quickstart_app.callback(invoke_without_command=True)
def quickstart(ctx: typer.Context):
    """
    Quick setup workflow
    
    Performs a complete setup:
    1. Checks authentication
    2. Lists your repositories
    3. Clones the first repository to workspace
    
    This is a convenience command for getting started quickly.
    
    Examples:
        autocode quickstart
    """
    if ctx.invoked_subcommand is not None:
        return
    
    console.print(Panel.fit(
        "[bold blue]Quickstart Workflow[/bold blue]",
        border_style="blue"
    ))
    
    try:
        # Step 1: Check authentication
        console.print("\n[bold cyan]Step 1/3:[/bold cyan] Checking authentication...")
        
        try:
            github_service = get_github_service()
            user_info = asyncio.run(github_service.get_authenticated_user())
            console.print(f"[green]✅ Authenticated as {user_info['login']}[/green]")
        except FileNotFoundError:
            console.print("[red]❌ Not authenticated[/red]")
            console.print("\n[yellow]Please authenticate first:[/yellow]")
            console.print("[cyan]autocode auth login[/cyan]\n")
            raise typer.Exit(1)
        
        # Step 2: List repositories
        console.print("\n[bold cyan]Step 2/3:[/bold cyan] Fetching your repositories...")
        
        with console.status("[bold cyan]Loading repositories...[/bold cyan]"):
            repos = asyncio.run(github_service.get_user_repositories(
                per_page=5
            ))
        
        if not repos:
            console.print("[yellow]⚠️  No repositories found[/yellow]")
            console.print("\n[dim]You can create a repository on GitHub and try again.[/dim]")
            raise typer.Exit(0)
        
        console.print(f"[green]✅ Found {len(repos)} repositories[/green]")
        
        # Show repository options
        console.print("\n[bold]Available repositories:[/bold]")
        for i, repo in enumerate(repos, 1):
            visibility = "🔒 Private" if repo.get('private') else "🌐 Public"
            console.print(f"  {i}. [cyan]{repo['name']}[/cyan] {visibility}")
            if repo.get('description'):
                desc = repo['description']
                if len(desc) > 60:
                    desc = desc[:57] + "..."
                console.print(f"     [dim]{desc}[/dim]")
        
        # Step 3: Clone first repository
        console.print(f"\n[bold cyan]Step 3/3:[/bold cyan] Cloning first repository...")
        
        first_repo = repos[0]
        repo_name = first_repo['full_name']
        
        # Set workspace directory
        workspace_dir = Path(__file__).parent.parent.parent.parent / "workspace"
        workspace_dir.mkdir(exist_ok=True)
        
        console.print(f"\n[cyan]Repository:[/cyan] {repo_name}")
        console.print(f"[cyan]Directory:[/cyan] {workspace_dir}\n")
        
        # Create git service with workspace directory
        git_service = GitService(workspace_root=str(workspace_dir))
        
        # Build GitHub URL
        repo_url = f"https://github.com/{repo_name}.git"
        
        # Get token
        try:
            token = get_stored_token()
        except:
            token = None
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("[cyan]Cloning repository...", total=None)
            
            try:
                result = git_service.clone(repo_url, token=token)
                progress.update(task, completed=True)
            except Exception as e:
                progress.update(task, completed=True)
                raise e
        
        if result:
            console.print(f"\n[green]✅ Successfully cloned {repo_name}[/green]")
            console.print(f"[dim]Location: {result}[/dim]\n")
            
            # Summary
            console.print(Panel(
                f"[bold green]Quickstart Complete! 🎉[/bold green]\n\n"
                f"[cyan]User:[/cyan] {user_info['login']}\n"
                f"[cyan]Repository:[/cyan] {repo_name}\n"
                f"[cyan]Location:[/cyan] {result}\n\n"
                f"[dim]You can now start working on your project![/dim]",
                title="[bold magenta]Summary[/bold magenta]",
                border_style="green"
            ))
        else:
            console.print(f"\n[red]❌ Failed to clone repository[/red]")
            raise typer.Exit(1)
        
    except typer.Exit:
        raise
    except Exception as e:
        console.print(f"\n[red]❌ Quickstart failed: {str(e)}[/red]")
        raise typer.Exit(1)
