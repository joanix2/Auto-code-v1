#!/usr/bin/env python3
"""
AutoCode CLI - Main Entry Point
"""
import typer
from pathlib import Path
from rich.console import Console

# Import command modules
from cli.commands.auth import auth_app
from cli.commands.repos import repos_app
from cli.commands.pull import pull_app
from cli.commands.ticket import ticket_app
from cli.commands.message import message_app
from cli.commands.branch import branch_app
from cli.commands.agent import agent_app
from cli.commands.quickstart import quickstart_app

# Initialize main Typer app
app = typer.Typer(
    name="autocode",
    help="AutoCode CLI - AI-Powered Development Automation",
    add_completion=False
)

# Rich console
console = Console()

# Register command groups
app.add_typer(auth_app, name="auth")
app.add_typer(repos_app, name="repos")
app.add_typer(pull_app, name="pull")
app.add_typer(ticket_app, name="ticket")
app.add_typer(message_app, name="message")
app.add_typer(branch_app, name="branch")
app.add_typer(agent_app, name="agent")
app.add_typer(quickstart_app, name="quickstart")


@app.command()
def version():
    """Show AutoCode CLI version"""
    console.print("[bold blue]AutoCode CLI[/bold blue] v1.0.0")
    console.print("AI-Powered Development Automation")


if __name__ == "__main__":
    app()
