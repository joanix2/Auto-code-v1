"""
Authentication commands
"""
import typer
import asyncio
import secrets
import webbrowser
import threading
from typing import Optional
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from rich.table import Table
from rich.panel import Panel

from cli.utils import console, save_token, GITHUB_TOKEN
from src.services.git.github_service import GitHubService

# Create sub-app for auth commands
auth_app = typer.Typer(help="Authentication commands")


@auth_app.command()
def login(
    token: Optional[str] = typer.Option(None, "--token", "-t", help="GitHub Personal Access Token"),
    oauth: bool = typer.Option(True, "--oauth/--no-oauth", help="Use OAuth2 flow (opens browser)"),
):
    """
    Authenticate with GitHub
    
    By default, uses OAuth2 flow (opens browser automatically).
    You can also provide a token directly.
    
    OAuth2 scopes: repo, user:email
    
    Examples:
        autocode auth login                    # OAuth2 flow (recommended)
        autocode auth login --token ghp_xxxxx  # Manual token
        autocode auth login --no-oauth         # Prompt for token
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
            sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
            from backend.src.services.github_oauth_service import GitHubOAuthService
            import os
            
            # Create OAuth service with CLI redirect URI (use existing callback from .env)
            cli_redirect_uri = os.getenv("GITHUB_REDIRECT_URI", "http://localhost:8000/api/auth/github/callback")
            oauth_service = GitHubOAuthService(redirect_uri=cli_redirect_uri)
            
            # Extract port from redirect URI
            from urllib.parse import urlparse
            parsed_uri = urlparse(cli_redirect_uri)
            callback_port = parsed_uri.port or 8000
            callback_path = parsed_uri.path or "/callback"
            
            # Generate state for security
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
            console.print("[cyan]autocode auth login --no-oauth[/cyan]")
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
        from cli.utils import CONFIG_FILE
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


# Alias for backward compatibility
@auth_app.callback(invoke_without_command=True)
def auth_callback(ctx: typer.Context):
    """Authentication with GitHub (alias for 'auth login')"""
    if ctx.invoked_subcommand is None:
        # If no subcommand, default to login
        ctx.invoke(login)
