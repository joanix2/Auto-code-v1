"""
Repository listing commands
"""
import typer
import asyncio
from typing import Optional
from rich.table import Table
from rich.panel import Panel

from cli.utils import console, get_github_service

# Create sub-app for repos commands
repos_app = typer.Typer(help="Repository management commands")


@repos_app.command()
def list(
    limit: int = typer.Option(10, "--limit", "-l", help="Number of repositories to show"),
    sort: str = typer.Option("updated", "--sort", "-s", help="Sort by: updated, created, pushed, full_name"),
    visibility: Optional[str] = typer.Option(None, "--visibility", "-v", help="Filter by visibility: all, public, private"),
):
    """
    List your GitHub repositories
    
    Shows repositories you own or have access to.
    
    Examples:
        autocode repos list                           # Show 10 most recently updated
        autocode repos list --limit 20                # Show 20 repositories
        autocode repos list --sort created            # Sort by creation date
        autocode repos list --visibility private      # Only private repos
    """
    console.print(Panel.fit(
        "[bold blue]GitHub Repositories[/bold blue]",
        border_style="blue"
    ))
    
    try:
        github_service = get_github_service()
        
        with console.status("[bold cyan]Fetching repositories...[/bold cyan]"):
            repos = asyncio.run(github_service.list_user_repositories(
                sort=sort,
                visibility=visibility,
                per_page=limit
            ))
        
        if not repos:
            console.print("\n[yellow]No repositories found[/yellow]")
            return
        
        console.print(f"\n[green]Found {len(repos)} repositories:[/green]\n")
        
        # Create table
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Name", style="cyan", no_wrap=True)
        table.add_column("Description", style="white")
        table.add_column("Visibility", style="yellow", justify="center")
        table.add_column("Language", style="green", justify="center")
        table.add_column("Stars", justify="right", style="blue")
        table.add_column("Updated", style="dim")
        
        for repo in repos:
            # Format visibility
            visibility_icon = "🔒" if repo.get('private') else "🌐"
            visibility_text = f"{visibility_icon} {'Private' if repo.get('private') else 'Public'}"
            
            # Format description
            description = repo.get('description') or '[dim]No description[/dim]'
            if len(description) > 50:
                description = description[:47] + "..."
            
            # Format language
            language = repo.get('language') or '[dim]N/A[/dim]'
            
            # Format stars
            stars = str(repo.get('stargazers_count', 0))
            
            # Format updated date
            updated = repo.get('updated_at', '')
            if updated:
                # Extract just the date part
                updated = updated.split('T')[0]
            
            table.add_row(
                repo['name'],
                description,
                visibility_text,
                language,
                stars,
                updated
            )
        
        console.print(table)
        console.print()
        
    except FileNotFoundError:
        console.print("[red]❌ Not authenticated. Run 'autocode auth login' first.[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]❌ Failed to fetch repositories: {str(e)}[/red]")
        raise typer.Exit(1)
