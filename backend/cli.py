#!/usr/bin/env python3
"""
AutoCode CLI - Command Line Interface for AutoCode operations
"""
import typer
import asyncio
from typing import Optional
from pathlib import Path
import os
import json
from dotenv import load_dotenv
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.panel import Panel
from src.services.github_service import GitHubService
from src.services.git_service import GitService
import subprocess
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading

# Load environment variables
load_dotenv()

# Initialize Typer app and Rich console
app = typer.Typer(
    name="autocode",
    help="AutoCode CLI - AI-Powered Development Automation",
    add_completion=False
)
console = Console()

# Config file path
CONFIG_DIR = Path.home() / ".autocode"
CONFIG_FILE = CONFIG_DIR / "config.json"

# Get GitHub token from environment
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")


def get_github_service() -> Optional[GitHubService]:
    """Get initialized GitHub service (returns None if no token)"""
    token = get_stored_token() or GITHUB_TOKEN
    if not token:
        return None
    
    return GitHubService(token)


def get_stored_token() -> Optional[str]:
    """Get stored GitHub token from config file"""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                return config.get('github_token')
        except Exception:
            return None
    return None


def save_token(token: str):
    """Save GitHub token to config file"""
    CONFIG_DIR.mkdir(exist_ok=True)
    config = {}
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
        except Exception:
            pass
    
    config['github_token'] = token
    
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)
    
    # Set secure permissions
    CONFIG_FILE.chmod(0o600)


@app.command()
def auth(
    token: Optional[str] = typer.Option(None, "--token", "-t", help="GitHub Personal Access Token"),
    oauth: bool = typer.Option(True, "--oauth/--no-oauth", help="Use OAuth2 flow (opens browser)"),
):
    """
    Authenticate with GitHub
    
    By default, uses OAuth2 flow (opens browser automatically).
    You can also provide a token directly.
    
    OAuth2 scopes: repo, user:email
    
    Examples:
        autocode auth                    # OAuth2 flow (recommended)
        autocode auth --token ghp_xxxxx  # Manual token
        autocode auth --no-oauth         # Prompt for token
    """
    console.print(Panel.fit(
        "[bold blue]GitHub Authentication[/bold blue]",
        border_style="blue"
    ))
    
    # If token provided directly, use it
    if token:
        oauth = False
    
    # OAuth2 flow
    if oauth and not token:
        console.print("\n[bold cyan]Starting OAuth2 authentication...[/bold cyan]")
        console.print("[yellow]Your browser will open automatically.[/yellow]\n")
        
        try:
            # Import OAuth service
            import sys
            sys.path.insert(0, str(Path(__file__).parent / "src"))
            from src.services.github_oauth_service import GitHubOAuthService
            
            # Create OAuth service with CLI redirect URI (use existing callback from .env)
            cli_redirect_uri = os.getenv("GITHUB_REDIRECT_URI", "http://localhost:8000/api/auth/github/callback")
            oauth_service = GitHubOAuthService(redirect_uri=cli_redirect_uri)
            
            # Extract port from redirect URI
            from urllib.parse import urlparse
            parsed_uri = urlparse(cli_redirect_uri)
            callback_port = parsed_uri.port or 8000
            callback_path = parsed_uri.path or "/callback"
            
            # Generate state for security
            import secrets
            state = secrets.token_urlsafe(32)
            
            # Create local server to receive callback
            callback_received = threading.Event()
            auth_code = {'code': None, 'error': None}
            
            class OAuthCallbackHandler(BaseHTTPRequestHandler):
                def do_GET(self):
                    # Parse query parameters
                    query = parse_qs(urlparse(self.path).query)
                    
                    if 'code' in query:
                        auth_code['code'] = query['code'][0]
                        # Send success response
                        self.send_response(200)
                        self.send_header('Content-type', 'text/html')
                        self.end_headers()
                        success_html = """
                        <html>
                        <head><title>Authentication Successful</title></head>
                        <body style="font-family: Arial; text-align: center; padding: 50px;">
                            <h1 style="color: green;">✅ Authentication Successful!</h1>
                            <p>You can close this window and return to the terminal.</p>
                        </body>
                        </html>
                        """
                        self.wfile.write(success_html.encode())
                    else:
                        auth_code['error'] = query.get('error', ['Unknown error'])[0]
                        self.send_response(400)
                        self.send_header('Content-type', 'text/html')
                        self.end_headers()
                        error_html = """
                        <html>
                        <head><title>Authentication Failed</title></head>
                        <body style="font-family: Arial; text-align: center; padding: 50px;">
                            <h1 style="color: red;">❌ Authentication Failed</h1>
                            <p>Please return to the terminal and try again.</p>
                        </body>
                        </html>
                        """
                        self.wfile.write(error_html.encode())
                    
                    callback_received.set()
                
                def log_message(self, format, *args):
                    pass  # Suppress server logs
            
            # Start local server on the port from redirect URI
            server = HTTPServer(('localhost', callback_port), OAuthCallbackHandler)
            server_thread = threading.Thread(target=server.handle_request, daemon=True)
            server_thread.start()
            
            # Generate authorization URL
            auth_url = oauth_service.get_authorization_url(state)
            
            console.print(f"[dim]Opening browser to:[/dim]")
            console.print(f"[cyan]{auth_url}[/cyan]\n")
            
            # Open browser
            webbrowser.open(auth_url)
            
            console.print("[yellow]Waiting for authentication...[/yellow]")
            console.print("[dim]If browser doesn't open, copy the URL above[/dim]\n")
            
            # Wait for callback (with timeout)
            if not callback_received.wait(timeout=120):
                console.print("[red]❌ Timeout waiting for authentication[/red]")
                raise typer.Exit(1)
            
            # Check for errors
            if auth_code['error']:
                console.print(f"[red]❌ Authentication error: {auth_code['error']}[/red]")
                raise typer.Exit(1)
            
            if not auth_code['code']:
                console.print("[red]❌ No authorization code received[/red]")
                raise typer.Exit(1)
            
            # Exchange code for token
            console.print("[green]✅ Authorization code received[/green]")
            console.print("[yellow]Exchanging code for access token...[/yellow]")
            
            token_data = asyncio.run(oauth_service.exchange_code_for_token(auth_code['code']))
            
            if 'access_token' not in token_data:
                console.print(f"[red]❌ Failed to get access token: {token_data}[/red]")
                raise typer.Exit(1)
            
            token = token_data['access_token']
            console.print("[green]✅ Access token received[/green]\n")
            
        except ImportError as e:
            console.print(f"[red]❌ OAuth service not available: {e}[/red]")
            console.print("[yellow]Falling back to manual token entry...[/yellow]\n")
            oauth = False
        except Exception as e:
            console.print(f"[red]❌ OAuth authentication failed: {str(e)}[/red]")
            console.print("[yellow]You can try manual token entry instead:[/yellow]")
            console.print("[cyan]autocode auth --no-oauth[/cyan]")
            raise typer.Exit(1)
    
    # Manual token entry
    if not token:
        console.print("\n[yellow]No token provided. You can create a Personal Access Token at:[/yellow]")
        console.print("[cyan]https://github.com/settings/tokens/new[/cyan]")
        console.print("\n[yellow]Required scopes: repo, user:email[/yellow]\n")
        
        token = typer.prompt("Enter your GitHub token", hide_input=True)
    
    # Test the token
    try:
        github_service = GitHubService(token)
        user_info = asyncio.run(github_service.get_authenticated_user())
        
        if not user_info:
            console.print("[red]❌ Invalid token or failed to authenticate[/red]")
            raise typer.Exit(1)
        
        # Save the token
        save_token(token)
        
        console.print(f"\n[green]✅ Successfully authenticated as [bold]{user_info['login']}[/bold][/green]")
        console.print(f"[dim]Token saved to: {CONFIG_FILE}[/dim]\n")
        
        # Display user info
        table = Table(show_header=False, border_style="green")
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="white")
        
        table.add_row("Username", user_info['login'])
        table.add_row("Name", user_info.get('name', 'N/A'))
        table.add_row("Email", user_info.get('email', 'N/A'))
        table.add_row("Public Repos", str(user_info.get('public_repos', 0)))
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]❌ Authentication failed: {str(e)}[/red]")
        raise typer.Exit(1)


@app.command()
def repos(
    username: Optional[str] = typer.Option(None, "--user", "-u", help="GitHub username (default: authenticated user)"),
    limit: int = typer.Option(20, "--limit", "-l", help="Number of repositories to show"),
    private: bool = typer.Option(False, "--private", "-p", help="Show only private repositories"),
):
    """
    List GitHub repositories
    
    Examples:
        autocode repos
        autocode repos --user octocat
        autocode repos --limit 10
        autocode repos --private
    """
    github_service = get_github_service()
    
    if not github_service:
        console.print("[red]❌ Not authenticated. Run 'autocode auth' first[/red]")
        raise typer.Exit(1)
    
    console.print(Panel.fit(
        f"[bold blue]GitHub Repositories[/bold blue]",
        border_style="blue"
    ))
    
    try:
        with console.status(f"[bold green]Fetching repositories..."):
            repos_data = asyncio.run(github_service.get_user_repositories(username=username, per_page=100))
        
        if not repos_data:
            console.print("[yellow]No repositories found[/yellow]")
            return
        
        # Filter private repos if requested
        if private:
            repos_data = [r for r in repos_data if r.get('private', False)]
        
        # Limit results
        repos_data = repos_data[:limit]
        
        # Create table
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Name", style="cyan")
        table.add_column("Description", style="white", max_width=50)
        table.add_column("Language", style="yellow")
        table.add_column("Stars", justify="right", style="green")
        table.add_column("Private", justify="center", style="red")
        
        for repo in repos_data:
            table.add_row(
                repo['full_name'],
                repo.get('description', 'N/A') or 'N/A',
                repo.get('language', 'N/A') or 'N/A',
                str(repo.get('stargazers_count', 0)),
                "🔒" if repo.get('private', False) else "🌍"
            )
        
        console.print(f"\n[bold]Showing {len(repos_data)} repositories[/bold]\n")
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]❌ Error fetching repositories: {str(e)}[/red]")
        raise typer.Exit(1)


@app.command()
def pull(
    repo: str = typer.Argument(..., help="Repository name (e.g., 'owner/repo' or just 'repo' for your repos)"),
    dest: Optional[Path] = typer.Option(
        None,
        "--dest", "-d",
        help="Destination directory (default: ./workspace/<repo-name>)"
    ),
    branch: Optional[str] = typer.Option(
        None,
        "--branch", "-b",
        help="Branch to clone (default: repository's default branch)"
    ),
    force: bool = typer.Option(
        False,
        "--force", "-f",
        help="Force clone even if directory exists"
    )
):
    """
    Pull (clone) a GitHub repository to local workspace
    
    Examples:
        autocode pull myrepo
        autocode pull owner/repo -d ./custom-path
        autocode pull repo -b develop
    """
    console.print(f"\n[bold blue]🔄 Pulling repository: {repo}[/bold blue]\n")
    
    try:
        # Initialize GitHub service (optional for public repos)
        github_service = get_github_service()
        
        # Determine full repository name
        if "/" not in repo:
            if not github_service:
                console.print("[yellow]⚠️  No GITHUB_TOKEN found. For user repos, please specify owner/repo[/yellow]")
                console.print("Example: autocode pull owner/repo")
                raise typer.Exit(1)
            
            # Get authenticated user to construct full repo name
            user_info = asyncio.run(github_service.get_authenticated_user())
            if not user_info:
                console.print("[red]❌ Failed to get authenticated user info[/red]")
                raise typer.Exit(1)
            
            repo_full_name = f"{user_info['login']}/{repo}"
        else:
            repo_full_name = repo
        
        # Determine destination directory
        if dest is None:
            workspace_dir = Path("./workspace")
            workspace_dir.mkdir(exist_ok=True)
            repo_name = repo_full_name.split("/")[1]
            dest = workspace_dir / repo_name
        
        dest = Path(dest).resolve()
        
        # Build clone URL
        clone_url = f"https://github.com/{repo_full_name}.git"
        
        # Get token for private repos
        token = get_stored_token() or GITHUB_TOKEN
        
        # Initialize Git Service (workspace_root not needed when using custom dest)
        git_service = GitService(workspace_root=str(dest.parent))
        
        # Clone or pull using GitService (business logic in service)
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            # Check if already cloned to show appropriate message
            is_already_cloned = dest.exists() and (dest / '.git').exists()
            
            if is_already_cloned and not force:
                task = progress.add_task("Pulling latest changes...", total=None)
                console.print(f"[yellow]⚠️  Repository already cloned at {dest}[/yellow]")
                console.print("[blue]ℹ️  Pulling latest changes instead...[/blue]")
            else:
                task = progress.add_task("Cloning repository...", total=None)
                console.print(f"[dim]Cloning from: {clone_url}[/dim]")
                console.print(f"[dim]Destination: {dest}[/dim]")
                if branch:
                    console.print(f"[dim]Branch: {branch}[/dim]")
            
            try:
                # Business logic handled by service - pass dest_path for custom location
                repo_path, is_new_clone = git_service.clone_or_pull(
                    clone_url, 
                    token=token, 
                    force=force,
                    dest_path=dest
                )
                progress.update(task, completed=True)
            except Exception as e:
                progress.stop()
                console.print(f"\n[red]❌ Failed: {str(e)}[/red]")
                raise typer.Exit(1)
        
        # Display success message
        if is_new_clone:
            console.print(f"\n[green]✅ Successfully cloned {repo_full_name}[/green]")
        else:
            console.print(f"\n[green]✅ Successfully updated {repo_full_name}[/green]")
        
        console.print(f"[green]📁 Location: {repo_path}[/green]\n")
        
        # Show repository info using GitHubService.get_repository
        if github_service:
            try:
                repo_info = github_service.get_repository(repo_full_name)
                
                if repo_info:
                    table = Table(show_header=False, border_style="blue", title="Repository Info")
                    table.add_column("Field", style="cyan")
                    table.add_column("Value", style="white")
                    
                    table.add_row("Full Name", repo_info['full_name'])
                    table.add_row("Description", repo_info.get('description', 'N/A') or 'N/A')
                    table.add_row("Language", repo_info.get('language', 'N/A') or 'N/A')
                    table.add_row("Stars", f"⭐ {repo_info.get('stargazers_count', 0)}")
                    table.add_row("Forks", f"🍴 {repo_info.get('forks_count', 0)}")
                    table.add_row("Default Branch", repo_info.get('default_branch', 'N/A'))
                    table.add_row("Private", "🔒 Yes" if repo_info.get('private', False) else "🌍 Public")
                    table.add_row("Clone URL", repo_info.get('clone_url', 'N/A'))
                    
                    console.print(table)
            except Exception as e:
                console.print(f"[dim]Could not fetch repository info: {e}[/dim]")
        
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def quickstart(
    workspace_dir: Path = typer.Option(
        "./workspace",
        "--workspace", "-w",
        help="Workspace directory for cloning repositories"
    ),
):
    """
    Quickstart: authenticate, list repos, and clone the first one
    
    This is a demo command that shows the full workflow:
    1. Check authentication
    2. List your repositories
    3. Clone the first repository to workspace
    
    Example:
        autocode quickstart
        autocode quickstart --workspace ./my-repos
    """
    console.print(Panel.fit(
        "[bold blue]🚀 AutoCode Quickstart[/bold blue]",
        border_style="blue"
    ))
    
    # Step 1: Check authentication
    console.print("\n[bold cyan]Step 1: Checking authentication...[/bold cyan]")
    github_service = get_github_service()
    
    if not github_service:
        console.print("[red]❌ Not authenticated. Please run 'autocode auth' first[/red]")
        console.print("\n[yellow]Quick setup:[/yellow]")
        console.print("1. Go to: [cyan]https://github.com/settings/tokens/new[/cyan]")
        console.print("2. Create a token with scopes: [cyan]repo, user:email[/cyan]")
        console.print("3. Run: [cyan]autocode auth --token YOUR_TOKEN[/cyan]")
        raise typer.Exit(1)
    
    try:
        user_info = asyncio.run(github_service.get_authenticated_user())
        if not user_info:
            console.print("[red]❌ Failed to authenticate[/red]")
            raise typer.Exit(1)
        
        console.print(f"[green]✅ Authenticated as [bold]{user_info['login']}[/bold][/green]")
        
        # Step 2: List repositories
        console.print(f"\n[bold cyan]Step 2: Fetching your repositories...[/bold cyan]")
        
        with console.status("[bold green]Loading repositories..."):
            repos_data = asyncio.run(github_service.get_user_repositories(per_page=10))
        
        if not repos_data:
            console.print("[yellow]⚠️  No repositories found[/yellow]")
            raise typer.Exit(0)
        
        console.print(f"[green]✅ Found {len(repos_data)} repositories[/green]\n")
        
        # Display repositories table
        table = Table(show_header=True, header_style="bold cyan", title="Your Repositories")
        table.add_column("#", style="dim", width=3)
        table.add_column("Name", style="cyan")
        table.add_column("Description", style="white", max_width=40)
        table.add_column("Language", style="yellow")
        table.add_column("Updated", style="green")
        
        for idx, repo in enumerate(repos_data[:5], 1):
            from datetime import datetime
            updated = repo.get('updated_at', '')
            if updated:
                updated_date = datetime.fromisoformat(updated.replace('Z', '+00:00'))
                updated = updated_date.strftime('%Y-%m-%d')
            
            table.add_row(
                str(idx),
                repo['name'],
                (repo.get('description', 'N/A') or 'N/A')[:40],
                repo.get('language', 'N/A') or 'N/A',
                updated
            )
        
        console.print(table)
        
        # Step 3: Clone first repository
        first_repo = repos_data[0]
        repo_full_name = first_repo['full_name']
        
        console.print(f"\n[bold cyan]Step 3: Cloning first repository: {repo_full_name}...[/bold cyan]")
        
        # Prepare workspace
        workspace_path = Path(workspace_dir).resolve()
        workspace_path.mkdir(parents=True, exist_ok=True)
        
        repo_name = first_repo['name']
        dest = workspace_path / repo_name
        
        # Build clone URL
        clone_url = first_repo['clone_url']
        token = get_stored_token() or GITHUB_TOKEN
        
        # Initialize Git Service
        git_service = GitService(workspace_root=str(workspace_path))
        
        # Clone or pull
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            is_already_cloned = dest.exists() and (dest / '.git').exists()
            
            if is_already_cloned:
                task = progress.add_task("Updating repository...", total=None)
            else:
                task = progress.add_task("Cloning repository...", total=None)
            
            try:
                repo_path, is_new_clone = git_service.clone_or_pull(
                    clone_url,
                    token=token,
                    dest_path=dest
                )
                progress.update(task, completed=True)
            except Exception as e:
                progress.stop()
                console.print(f"\n[red]❌ Failed: {str(e)}[/red]")
                raise typer.Exit(1)
        
        if is_new_clone:
            console.print(f"\n[green]✅ Successfully cloned {repo_full_name}![/green]")
        else:
            console.print(f"\n[green]✅ Successfully updated {repo_full_name}![/green]")
        
        console.print(f"[green]📁 Location: {repo_path}[/green]\n")
        
        # Display repository info
        repo_info = github_service.get_repository(repo_full_name)
        if repo_info:
            info_table = Table(show_header=False, border_style="blue", title="Repository Info")
            info_table.add_column("Field", style="cyan")
            info_table.add_column("Value", style="white")
            
            info_table.add_row("Full Name", repo_info['full_name'])
            info_table.add_row("Description", repo_info.get('description', 'N/A') or 'N/A')
            info_table.add_row("Language", repo_info.get('language', 'N/A') or 'N/A')
            info_table.add_row("Stars", f"⭐ {repo_info.get('stargazers_count', 0)}")
            info_table.add_row("Forks", f"🍴 {repo_info.get('forks_count', 0)}")
            info_table.add_row("Default Branch", repo_info.get('default_branch', 'N/A'))
            info_table.add_row("Private", "🔒 Yes" if repo_info.get('private', False) else "🌍 Public")
            
            console.print(info_table)
        
        console.print(f"\n[bold green]🎉 Quickstart complete![/bold green]")
        console.print(f"[dim]You can now work with your repository at: {repo_path}[/dim]\n")
        
    except Exception as e:
        console.print(f"[red]❌ Error: {str(e)}[/red]")
        raise typer.Exit(1)


@app.command()
def version():
    """Show AutoCode CLI version"""
    console.print("[bold blue]AutoCode CLI[/bold blue] v1.0.0")
    console.print("AI-Powered Development Automation")


if __name__ == "__main__":
    app()
