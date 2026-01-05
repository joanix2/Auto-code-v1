# CLI Structure

This directory contains the modular CLI implementation for AutoCode.

## Structure

```
cli/
├── __init__.py              # Package initialization
├── utils.py                 # Shared utilities (console, token management)
└── commands/                # Command modules
    ├── __init__.py          # Commands package initialization
    ├── auth.py              # Authentication commands
    ├── repos.py             # Repository listing
    ├── pull.py              # Clone and pull operations
    ├── ticket.py            # Ticket management
    └── quickstart.py        # Quick setup workflow
```

## Entry Point

The main CLI entry point is `cli_main.py` in the parent directory, which:

- Creates the main Typer app
- Imports all command sub-apps
- Registers them with `app.add_typer()`

## Command Modules

### auth.py

**Commands:**

- `autocode auth login` - Authenticate with GitHub (OAuth2 or manual token)

**Features:**

- OAuth2 flow with automatic browser opening
- Local callback server for OAuth
- Manual token entry fallback
- Token validation and storage

### repos.py

**Commands:**

- `autocode repos list` - List GitHub repositories

**Options:**

- `--limit` - Number of repositories to show
- `--sort` - Sort by: updated, created, pushed, full_name
- `--visibility` - Filter by: all, public, private

### pull.py

**Commands:**

- `autocode pull clone <repo>` - Clone a repository
- `autocode pull update <path>` - Pull latest changes

**Features:**

- Automatic username resolution
- Custom directory support
- Branch selection
- Progress indicators

### ticket.py

**Commands:**

- `autocode ticket list` - List all tickets
- `autocode ticket get <id>` - Get ticket details
- `autocode ticket status <id> <status>` - Update ticket status
- `autocode ticket validate <id>` - Validate a completed ticket
- `autocode ticket reject <id>` - Reject a ticket

**Features:**

- Neo4j integration
- Status filtering
- Conversation message display
- Rich table formatting

### quickstart.py

**Commands:**

- `autocode quickstart` - Quick setup workflow

**Steps:**

1. Check authentication
2. List repositories
3. Clone first repository to workspace

## Shared Utilities (utils.py)

### Console

```python
from cli.utils import console
console.print("[green]Success![/green]")
```

### Token Management

```python
from cli.utils import get_stored_token, save_token, GITHUB_TOKEN

# Get token from config file
token = get_stored_token()

# Save new token
save_token(new_token)

# Use in commands
GITHUB_TOKEN  # Path to config file
```

### GitHub Service

```python
from cli.utils import get_github_service

# Get initialized GitHub service with stored token
github_service = get_github_service()
user = asyncio.run(github_service.get_authenticated_user())
```

## Adding New Commands

1. Create a new file in `cli/commands/`:

```python
# cli/commands/mycommand.py
import typer
from cli.utils import console

mycommand_app = typer.Typer(help="My command description")

@mycommand_app.command()
def action():
    """Action description"""
    console.print("[green]Action executed![/green]")
```

2. Export in `cli/commands/__init__.py`:

```python
from .mycommand import mycommand_app

__all__ = [..., 'mycommand_app']
```

3. Register in `cli_main.py`:

```python
from cli.commands import mycommand_app

app.add_typer(mycommand_app, name="mycommand")
```

## Running Commands

From the backend directory:

```bash
# Using the modular CLI
python cli_main.py auth login
python cli_main.py repos list
python cli_main.py ticket list --status pending

# Or using the legacy CLI (if still available)
python cli.py auth
```

## Dependencies

- **typer**: CLI framework
- **rich**: Terminal formatting and progress bars
- **asyncio**: Async operations
- **pathlib**: File path handling
- **Neo4j**: Database for tickets
- **GitHubService**: GitHub API integration
- **GitService**: Git operations

## Migration from Monolithic CLI

The original `cli.py` (700+ lines) has been refactored into:

- Smaller, focused modules (~100-300 lines each)
- Shared utilities extracted to `utils.py`
- Better separation of concerns
- Easier to test and maintain

## Testing

Each command module can be tested independently:

```python
from cli.commands.ticket import ticket_app
from typer.testing import CliRunner

runner = CliRunner()
result = runner.invoke(ticket_app, ["list"])
assert result.exit_code == 0
```
