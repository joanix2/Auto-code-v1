# GitHub Issues Integration

## Vue d'ensemble

Service pour synchroniser les tickets de l'application avec les issues GitHub. Permet de créer automatiquement des issues GitHub à partir de tickets et de maintenir la synchronisation bidirectionnelle.

## Architecture

### Modèle de données

**Ticket** (ajouts) :

- `github_issue_number`: Numéro de l'issue GitHub (optionnel)
- `github_issue_url`: URL de l'issue GitHub (optionnel)

### Services

#### `GitHubIssueService`

Service principal pour interagir avec l'API GitHub issues.

**Méthodes principales :**

1. **`create_issue_from_ticket(repo_full_name, ticket, branch_name)`**

   - Crée une issue GitHub à partir d'un ticket
   - Génère automatiquement le body avec les métadonnées
   - Ajoute des labels basés sur le type et la priorité
   - Retourne : `{issue_number, issue_url, title, state}`

2. **`update_issue_status(repo_full_name, issue_number, ticket_status, comment)`**

   - Met à jour le statut de l'issue en fonction du statut du ticket
   - Ajoute un commentaire optionnel
   - Ferme automatiquement l'issue si le ticket est closed/cancelled

3. **`add_comment_to_issue(repo_full_name, issue_number, comment)`**

   - Ajoute un commentaire à une issue

4. **`get_issue_info(repo_full_name, issue_number)`**

   - Récupère les informations d'une issue
   - Retourne : `{number, title, state, html_url, body, labels, created_at, etc.}`

5. **`link_pull_request_to_issue(repo_full_name, issue_number, pr_number)`**

   - Lie une PR à une issue via un commentaire

6. **`notify_development_started(repo_full_name, issue_number, branch_name)`**

   - Notifie sur l'issue que le développement a démarré

7. **`notify_ci_status(repo_full_name, issue_number, passed, details)`**
   - Notifie le résultat des tests CI sur l'issue

### API Endpoints

#### `POST /api/github-issues/create`

Crée une issue GitHub à partir d'un ticket.

**Request:**

```json
{
  "ticket_id": "uuid",
  "branch_name": "feature/ticket-123" // optionnel
}
```

**Response:**

```json
{
  "success": true,
  "ticket_id": "uuid",
  "issue_number": 42,
  "issue_url": "https://github.com/owner/repo/issues/42",
  "message": "GitHub issue #42 created successfully"
}
```

#### `POST /api/github-issues/update-status`

Met à jour le statut d'une issue GitHub.

**Request:**

```json
{
  "ticket_id": "uuid",
  "comment": "Tests passed, ready for review" // optionnel
}
```

**Response:**

```json
{
  "success": true,
  "ticket_id": "uuid",
  "issue_number": 42,
  "message": "GitHub issue updated successfully"
}
```

#### `POST /api/github-issues/link`

Lie une issue GitHub existante à un ticket.

**Request:**

```json
{
  "ticket_id": "uuid",
  "issue_number": 42,
  "issue_url": "https://github.com/owner/repo/issues/42"
}
```

**Response:**

```json
{
  "success": true,
  "ticket_id": "uuid",
  "issue_number": 42,
  "issue_url": "https://github.com/owner/repo/issues/42",
  "message": "GitHub issue linked successfully"
}
```

#### `GET /api/github-issues/{ticket_id}/issue-info`

Récupère les informations de l'issue GitHub liée à un ticket.

**Response:**

```json
{
  "success": true,
  "ticket_id": "uuid",
  "issue": {
    "number": 42,
    "title": "Add authentication feature",
    "state": "open",
    "html_url": "https://github.com/owner/repo/issues/42",
    "body": "...",
    "labels": ["enhancement", "priority: high", "autocode"],
    "created_at": "2026-01-06T12:00:00Z",
    "updated_at": "2026-01-06T13:00:00Z",
    "closed_at": null
  }
}
```

## Utilisation

### 1. Créer une issue automatiquement lors de la création d'un ticket

```python
from src.services.github.github_issue_service import GitHubIssueService

# Dans le workflow de développement
github_service = GitHubIssueService(github_token)
issue_result = github_service.create_issue_from_ticket(
    repo_full_name="owner/repo",
    ticket=ticket,
    branch_name="feature/ticket-123"
)

# Lier l'issue au ticket
await ticket_repo.link_github_issue(
    ticket_id=ticket.id,
    issue_number=issue_result["issue_number"],
    issue_url=issue_result["issue_url"]
)
```

### 2. Notifier le démarrage du développement

```python
github_service.notify_development_started(
    repo_full_name="owner/repo",
    issue_number=ticket.github_issue_number,
    branch_name=branch_name
)
```

### 3. Mettre à jour le statut après CI

```python
github_service.notify_ci_status(
    repo_full_name="owner/repo",
    issue_number=ticket.github_issue_number,
    passed=True,
    details="All tests passed ✅"
)
```

### 4. Lier une PR à l'issue

```python
github_service.link_pull_request_to_issue(
    repo_full_name="owner/repo",
    issue_number=ticket.github_issue_number,
    pr_number=pr.number
)
```

## Labels GitHub

Le service ajoute automatiquement des labels basés sur :

**Type de ticket :**

- `feature` → `enhancement`
- `bugfix` → `bug`
- `refactor` → `refactor`
- `documentation` → `documentation`

**Priorité :**

- `critical` → `priority: critical`
- `high` → `priority: high`
- `medium` → `priority: medium`
- `low` → `priority: low`

**Label automatique :**

- `autocode` - Indique que l'issue est gérée par AutoCode

## Format du body de l'issue

```markdown
[Description du ticket]

---

### 📋 Ticket Information

- **Type**: Feature
- **Priority**: High
- **Status**: In Progress
- **Branch**: `feature/ticket-123`

_Ticket ID: `uuid`_
_Created by AutoCode_
```

## Synchronisation du statut

| Statut Ticket        | Action sur l'issue GitHub                         |
| -------------------- | ------------------------------------------------- |
| `open`               | Ouvre l'issue si fermée                           |
| `in_progress`        | Pas de changement                                 |
| `pending_validation` | Pas de changement                                 |
| `closed`             | Ferme l'issue                                     |
| `cancelled`          | Ferme l'issue + commentaire "🚫 Ticket cancelled" |

## Sécurité

- Toutes les opérations nécessitent un token GitHub valide
- Le token est récupéré via `get_github_token_from_user(username)`
- L'utilisateur doit être authentifié (`get_current_user`)

## Erreurs courantes

### 401 Unauthorized

- Token GitHub manquant ou invalide
- L'utilisateur n'a pas connecté son compte GitHub

### 404 Not Found

- Ticket inexistant
- Repository inexistant
- Issue GitHub inexistante

### 400 Bad Request

- Ticket déjà lié à une issue
- Ticket non lié à une issue (pour update)

### 500 Internal Server Error

- Erreur API GitHub
- Problème de connexion réseau

## Intégration avec le workflow

Le service peut être intégré au workflow de développement automatique :

```python
# Dans simple_ticket_workflow.py

# Étape 1 : Créer l'issue au début
if not ticket.github_issue_number:
    issue_result = github_service.create_issue_from_ticket(...)
    await ticket_repo.link_github_issue(...)

# Étape 2 : Notifier le démarrage
github_service.notify_development_started(...)

# Étape 3 : Notifier les résultats CI
github_service.notify_ci_status(...)

# Étape 4 : Lier la PR
github_service.link_pull_request_to_issue(...)

# Étape 5 : Mettre à jour le statut
github_service.update_issue_status(...)
```

## Tests

Pour tester l'intégration :

1. Connecter un compte GitHub
2. Créer un ticket
3. Appeler l'endpoint `/api/github-issues/create`
4. Vérifier sur GitHub que l'issue est créée avec les bons labels
5. Mettre à jour le statut du ticket
6. Vérifier que l'issue GitHub est synchronisée

## Limitations

- Nécessite que le repository GitHub existe
- Nécessite des permissions d'écriture sur le repository
- Les labels doivent exister sur le repository (ou seront créés automatiquement)
