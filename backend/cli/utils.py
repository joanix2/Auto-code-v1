"""
Shared utilities for CLI commands
"""
import os
import json
from pathlib import Path
from typing import Optional
from rich.console import Console

# Rich console (shared instance)
console = Console()

# Config paths
CONFIG_DIR = Path.home() / ".autocode"
CONFIG_FILE = CONFIG_DIR / "config.json"

# Get GitHub token from environment
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")


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


def get_github_service():
    """Get initialized GitHub service (returns None if no token)"""
    from src.services.github_service import GitHubService
    
    token = get_stored_token() or GITHUB_TOKEN
    if not token:
        return None
    
    return GitHubService(token)
