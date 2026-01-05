"""
Git clone and pull commands
"""
import typer
import asyncio
from pathlib import Path
from typing import Optional
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from cli.utils import console, get_github_service, GITHUB_TOKEN
from src.services.git_service import GitService

# Create sub-app for pull/clone commands
pull_app = typer.Typer(help="Clone and pull repository commands")


@pull_app.command()
def clone(
    repo: str = typer.Argument(..., help="Repository name (owner/repo or just repo)"),
    directory: Optional[str] = typer.Option(None, "--dir", "-d", help="Directory to clone into"),
    branch: Optional[str] = typer.Option(None, "--branch", "-b", help="Specific branch to clone"),
):
    """
    Clone a GitHub repository
    
    Clones a repository using your authenticated token.
    If you only provide the repo name, it will use your username.
    
    Examples:
        autocode pull clone my-repo                    # Clone your own repo
        autocode pull clone octocat/Hello-World        # Clone someone else's repo
        autocode pull clone my-repo --dir ~/projects   # Clone to specific directory
        autocode pull clone my-repo --branch develop   # Clone specific branch
    """
    console.print(Panel.fit(
        "[bold blue]Clone Repository[/bold blue]",
        border_style="blue"
    ))
    
    try:
        # Get GitHub service to fetch user info if needed
        github_service = get_github_service()
        
        # If repo doesn't contain '/', add user's username
        if '/' not in repo:
            with console.status("[bold cyan]Fetching user info...[/bold cyan]"):
                user_info = asyncio.run(github_service.get_authenticated_user())
                username = user_info['login']
                repo = f"{username}/{repo}"
        
        # Set default directory to workspace if not provided
        if not directory:
            workspace_dir = Path(__file__).parent.parent.parent.parent / "workspace"
            workspace_dir.mkdir(exist_ok=True)
            directory = str(workspace_dir)
        
        console.print(f"\n[cyan]Repository:[/cyan] {repo}")
        console.print(f"[cyan]Directory:[/cyan] {directory}")
        if branch:
            console.print(f"[cyan]Branch:[/cyan] {branch}")
        console.print()
        
        # Create git service
        git_service = GitService(GITHUB_TOKEN)
        
        # Clone repository
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("[cyan]Cloning repository...", total=None)
            
            result = asyncio.run(git_service.clone_repository(
                repo_name=repo,
                target_dir=directory,
                branch=branch
            ))
            
            progress.update(task, completed=True)
        
        if result:
            console.print(f"\n[green]✅ Successfully cloned {repo}[/green]")
            console.print(f"[dim]Location: {result}[/dim]\n")
        else:
            console.print(f"\n[red]❌ Failed to clone {repo}[/red]")
            raise typer.Exit(1)
            
    except FileNotFoundError:
        console.print("[red]❌ Not authenticated. Run 'autocode auth login' first.[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"\n[red]❌ Clone failed: {str(e)}[/red]")
        raise typer.Exit(1)


@pull_app.command()
def update(
    path: str = typer.Argument(..., help="Path to local repository"),
    branch: Optional[str] = typer.Option(None, "--branch", "-b", help="Branch to pull"),
):
    """
    Pull latest changes from remote
    
    Updates a local repository with the latest changes from GitHub.
    
    Examples:
        autocode pull update ./workspace/my-repo        # Pull default branch
        autocode pull update ~/projects/app --branch develop  # Pull specific branch
    """
    console.print(Panel.fit(
        "[bold blue]Update Repository[/bold blue]",
        border_style="blue"
    ))
    
    try:
        repo_path = Path(path).expanduser().resolve()
        
        if not repo_path.exists():
            console.print(f"[red]❌ Repository not found: {repo_path}[/red]")
            raise typer.Exit(1)
        
        if not (repo_path / ".git").exists():
            console.print(f"[red]❌ Not a git repository: {repo_path}[/red]")
            raise typer.Exit(1)
        
        console.print(f"\n[cyan]Repository:[/cyan] {repo_path}")
        if branch:
            console.print(f"[cyan]Branch:[/cyan] {branch}")
        console.print()
        
        # Create git service
        git_service = GitService(GITHUB_TOKEN)
        
        # Pull changes
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("[cyan]Pulling latest changes...", total=None)
            
            result = asyncio.run(git_service.pull_repository(
                repo_path=str(repo_path),
                branch=branch
            ))
            
            progress.update(task, completed=True)
        
        if result:
            console.print(f"\n[green]✅ Successfully updated repository[/green]")
            console.print(f"[dim]{result}[/dim]\n")
        else:
            console.print(f"\n[yellow]⚠️  Repository already up to date[/yellow]\n")
            
    except FileNotFoundError:
        console.print("[red]❌ Not authenticated. Run 'autocode auth login' first.[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"\n[red]❌ Pull failed: {str(e)}[/red]")
        raise typer.Exit(1)
