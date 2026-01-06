#!/usr/bin/env python3
"""
Test script GitHub Copilot Coding Agent (assign issue -> Copilot ouvre une PR)

- Vérifie la dispo via GraphQL `suggestedActors` (login: copilot-swe-agent)
- Crée une issue
- Assigne l'issue au bot `copilot-swe-agent[bot]` via REST + agent_assignment
"""
import asyncio
import os
from typing import Any, Dict, Optional, Tuple

import httpx
from dotenv import load_dotenv

load_dotenv()

# --- CONFIG ---
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
OWNER = "joanix2"
REPO = "Auto-code-v1"

API_VERSION = "2022-11-28"
REST_BASE = "https://api.github.com"
GQL_URL = "https://api.github.com/graphql"

# Terminal colors
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


def rest_headers(token: str) -> Dict[str, str]:
    return {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": API_VERSION,
    }


def gql_headers(token: str) -> Dict[str, str]:
    # D'après la doc, ce header est requis pour l'assign Copilot via API GraphQL
    # (et recommandé même si on ne fait "que" la vérif suggestedActors).
    return {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": API_VERSION,
        "GraphQL-Features": "issues_copilot_assignment_api_support,coding_agent_model_selection",
    }


async def graphql(client: httpx.AsyncClient, token: str, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    r = await client.post(GQL_URL, headers=gql_headers(token), json={"query": query, "variables": variables or {}}, timeout=30.0)
    r.raise_for_status()
    data = r.json()
    if "errors" in data:
        raise RuntimeError(f"GraphQL errors: {data['errors']}")
    return data["data"]


async def get_default_branch(client: httpx.AsyncClient, owner: str, repo: str, token: str) -> str:
    url = f"{REST_BASE}/repos/{owner}/{repo}"
    r = await client.get(url, headers=rest_headers(token), timeout=30.0)
    r.raise_for_status()
    return r.json().get("default_branch", "main")


async def check_copilot_enabled(client: httpx.AsyncClient, owner: str, repo: str, token: str) -> Tuple[bool, Optional[str]]:
    """
    Vérifie si le repo expose `copilot-swe-agent` dans suggestedActors(capabilities:[CAN_BE_ASSIGNED]).
    Retourne (True, bot_id) si dispo.
    """
    print(f"\n{BLUE}🔍 Vérification Copilot coding agent via GraphQL suggestedActors...{RESET}")

    q = """
    query($owner: String!, $name: String!) {
      repository(owner: $owner, name: $name) {
        suggestedActors(capabilities: [CAN_BE_ASSIGNED], first: 100) {
          nodes {
            login
            __typename
            ... on Bot { id }
            ... on User { id }
          }
        }
      }
    }
    """
    data = await graphql(client, token, q, {"owner": owner, "name": repo})
    nodes = (data.get("repository", {})
                .get("suggestedActors", {})
                .get("nodes", []))

    # La doc indique que si c'est activé, `copilot-swe-agent` apparait (souvent en premier).
    for n in nodes:
        if n.get("login") == "copilot-swe-agent" and n.get("__typename") == "Bot":
            bot_id = n.get("id")
            print(f"{GREEN}✅ Copilot coding agent détecté : login=copilot-swe-agent (Bot){RESET}")
            return True, bot_id

    # Debug utile si ça échoue
    logins = [n.get("login") for n in nodes if n.get("login")]
    print(f"{RED}❌ Copilot coding agent NON détecté dans suggestedActors{RESET}")
    print(f"{YELLOW}   suggestedActors logins (extrait): {logins[:15]}{RESET}")
    return False, None


async def create_test_issue(client: httpx.AsyncClient, owner: str, repo: str, token: str) -> Tuple[Optional[int], Optional[str]]:
    print(f"\n{BLUE}📝 Création d'une issue de test...{RESET}")
    url = f"{REST_BASE}/repos/{owner}/{repo}/issues"

    payload = {
        "title": "🤖 Test GitHub Copilot coding agent (API)",
        "body": """## Description
Issue de test pour vérifier l'intégration avec GitHub Copilot coding agent.

## Tâche
Ajouter un fichier `test_copilot.md` à la racine du projet avec le contenu suivant:

```markdown
# Test GitHub Copilot Agent

Ce fichier a été créé automatiquement par GitHub Copilot coding agent.

Date: 2026-01-06
Repository: Auto-code-v1
```

## Critères de succès
- ✅ Fichier créé à la racine
- ✅ Contenu correct
- ✅ PR créée automatiquement
""",
        "labels": ["test", "copilot-agent", "autocode"],
    }

    r = await client.post(url, headers=rest_headers(token), json=payload, timeout=30.0)
    if r.status_code >= 400:
        print(f"{RED}❌ Erreur HTTP {r.status_code}: {r.text}{RESET}")
        return None, None

    issue = r.json()
    print(f"{GREEN}✅ Issue #{issue['number']} créée{RESET}")
    print(f"   📎 {issue['html_url']}")
    return issue["number"], issue["html_url"]

async def assign_issue_to_copilot(
    client: httpx.AsyncClient,
    owner: str,
    repo: str,
    issue_number: int,
    token: str,
    base_branch: str,
    custom_instructions: str = "",
) -> bool:
    """
    Assigne l'issue à Copilot via REST.
    IMPORTANT: l'assignee attendu en REST est `copilot-swe-agent[bot]` (d'après la doc).
    """
    print(f"\n{BLUE}🤖 Assignation de l'issue #{issue_number} à Copilot...{RESET}")

    url = f"{REST_BASE}/repos/{owner}/{repo}/issues/{issue_number}/assignees"

    payload: Dict[str, Any] = {
        "assignees": ["copilot-swe-agent[bot]"],
        "agent_assignment": {
            "target_repo": f"{owner}/{repo}",
            "base_branch": base_branch,
            "custom_instructions": custom_instructions,
            "custom_agent": "",
            "model": "",
        },
    }

    r = await client.post(url, headers=rest_headers(token), json=payload, timeout=30.0)
    if r.status_code >= 400:
        print(f"{RED}❌ Erreur HTTP {r.status_code}: {r.text}{RESET}")
        return False

    data = r.json()
    assignees = [a.get("login") for a in data.get("assignees", [])]
    print(f"{GREEN}✅ Assignation OK{RESET}")
    print(f"{BLUE}👥 Assignees: {assignees}{RESET}")
    print(f"{YELLOW}📬 Surveille tes notifications : Copilot devrait ouvrir une PR.{RESET}")
    return True


async def main() -> None:
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}  Test GitHub Copilot coding agent (API){RESET}")
    print(f"{BLUE}{'='*60}{RESET}")

    if not GITHUB_TOKEN:
        print(f"\n{RED}❌ ERREUR: GITHUB_TOKEN non défini{RESET}")
        print(f"{YELLOW}💡 Ajoute dans .env: GITHUB_TOKEN=...{RESET}")
        return

    async with httpx.AsyncClient() as client:
        print(f"\n{GREEN}✅ Token GitHub détecté{RESET}")
        print(f"   Repo: {OWNER}/{REPO}")

        # 1) Vérif fiable via GraphQL
        enabled, _bot_id = await check_copilot_enabled(client, OWNER, REPO, GITHUB_TOKEN)
        if not enabled:
            print(f"\n{YELLOW}⚠️  Copilot coding agent n'est pas activé / pas dispo sur ce repo.{RESET}")
            print(f"{YELLOW}   (Vérifie plan Copilot + activation repo/org + droits write.){RESET}")
            return

        # 2) Default branch (pour agent_assignment)
        base_branch = await get_default_branch(client, OWNER, REPO, GITHUB_TOKEN)
        print(f"{BLUE}🌿 Base branch détectée: {base_branch}{RESET}")

        # 3) Crée issue
        issue_number, issue_url = await create_test_issue(client, OWNER, REPO, GITHUB_TOKEN)
        if not issue_number:
            return

        # 4) Assigne à Copilot
        ok = await assign_issue_to_copilot(
            client,
            OWNER,
            REPO,
            issue_number,
            GITHUB_TOKEN,
            base_branch=base_branch,
            custom_instructions="Merci de ne modifier que ce qui est nécessaire pour créer test_copilot.md.",
        )
        if not ok:
            return

        print(f"\n{GREEN}{'='*60}{RESET}")
        print(f"{GREEN}✅ Terminé. Issue: {issue_url}{RESET}")
        print(f"{GREEN}{'='*60}{RESET}")

if __name__ == "__main__":
    asyncio.run(main())