# 🤖 Assignation d'Issues à GitHub Copilot

## Vue d'ensemble

Ce système permet d'assigner automatiquement des issues à GitHub Copilot Coding Agent, qui créera une Pull Request pour résoudre l'issue.

## Architecture

### Backend

#### Service: `GitHubCopilotAgentService`

**Fichier**: `backend/src/services/copilot_agent_service.py`

**Responsabilités**:

- Vérifier la disponibilité de Copilot via GraphQL
- Assigner des issues via l'API REST GitHub
- Créer des issues et les assigner directement
- Récupérer les PRs créées par Copilot

**Méthodes principales**:

```python
async def check_copilot_agent_status(owner: str, repo: str) -> Dict[str, Any]
async def assign_issue_to_copilot(owner: str, repo: str, issue_number: int, ...) -> Dict[str, Any]
async def create_issue_and_assign_to_copilot(owner: str, repo: str, title: str, ...) -> Dict[str, Any]
async def get_pull_request_from_issue(owner: str, repo: str, issue_number: int) -> Optional[Dict[str, Any]]
```

**Note**: Le service nécessite un token GitHub lors de l'instanciation: `GitHubCopilotAgentService(github_token)`

#### Controller: `CopilotAssignmentController`

**Fichier**: `backend/src/controllers/copilot_assignment_controller.py`

**Responsabilités**:

- Valider les requêtes HTTP
- Récupérer les données depuis les repositories
- Orchestrer l'assignation avec le service
- Mettre à jour la base de données

**Endpoints exposés**:

- `GET /api/copilot/availability/{repository_id}` - Vérifier disponibilité
- `POST /api/copilot/assign/{issue_id}` - Assigner à Copilot
- `DELETE /api/copilot/assign/{issue_id}` - Désassigner de Copilot

### Frontend

#### Service: `CopilotService`

**Fichier**: `frontend/src/services/copilot.service.ts`

**Méthodes**:

```typescript
async checkAvailability(repositoryId: string): Promise<CopilotAvailabilityResponse>
async assignIssue(issueId: string, options?: AssignToCopilotRequest)
async unassignIssue(issueId: string)
```

#### Composant: `AssignToCopilotDialog`

**Fichier**: `frontend/src/components/common/AssignToCopilotDialog.tsx`

**Fonctionnalités**:

- Formulaire pour instructions personnalisées
- Information sur le processus d'assignation
- Confirmation et gestion du loading

#### Intégration dans IssueCard

**Fichier**: `frontend/src/components/common/Card/IssueCard.tsx`

Bouton "Copilot Dev" qui:

- S'affiche uniquement si l'issue est `open` et non assignée à Copilot
- Ouvre le dialogue d'assignation
- Affiche le badge Copilot si l'issue est assignée

## Flux d'Assignation

### 1. Utilisateur clique sur "Copilot Dev"

```
IssueCard (bouton) → Opens AssignToCopilotDialog
```

### 2. Dialogue ouvert

```
AssignToCopilotDialog
├── Affiche nom de l'issue
├── Champ instructions personnalisées (optionnel)
└── Bouton "Assigner à Copilot"
```

### 3. Confirmation

```
Issues.tsx (handleConfirmAssign)
└── useIssues.assignToCopilot(issueId, options)
    └── issueService.assignToCopilot(id, options)
        └── copilotService.assignIssue(id, options)
            └── POST /api/copilot/assign/{id}
```

### 4. Backend traite la requête

```
copilot_assignment_routes.assign_issue_to_copilot
└── CopilotAssignmentController.assign_to_copilot
    ├── Récupère issue et repository
    ├── Récupère token GitHub user
    ├── Vérifie github_issue_number exists
    ├── CopilotAssignmentService.assign_issue_to_copilot
    │   └── POST GitHub API /repos/{owner}/{repo}/issues/{number}/assignees
    │       payload: {
    │         assignees: ["copilot-swe-agent[bot]"],
    │         agent_assignment: { ... }
    │       }
    └── IssueRepository.assign_to_copilot(issue_id, True)
        └── Met à jour assigned_to_copilot dans Neo4j
```

### 5. Résultat

```
GitHub Copilot:
├── Analyse l'issue
├── Crée une branche
├── Génère le code
├── Ouvre une Pull Request
└── Envoie notification à l'utilisateur
```

## Modèles de Données

### Request Models

```typescript
// Frontend
interface AssignToCopilotRequest {
  base_branch?: string;
  custom_instructions?: string;
}
```

```python
# Backend
class AssignToCopilotRequest(BaseModel):
    base_branch: Optional[str] = None
    custom_instructions: Optional[str] = ""
```

### Response Models

```typescript
// Frontend
interface AssignToCopilotResponse {
  success: boolean;
  message: string;
  issue_id: string;
  assigned_to_copilot: boolean;
  github_issue_number?: number;
}

interface CopilotAvailabilityResponse {
  available: boolean;
  message: string;
  bot_id?: string;
}
```

## Prérequis

### GitHub

1. **Copilot activé** sur l'organisation/repository
2. **Token avec les permissions**:
   - `repo` (full control of private repositories)
   - `workflow` (update GitHub Action workflows)
3. **Issue synchronisée avec GitHub** (`github_issue_number` doit exister)

### Application

1. User authentifié avec `github_access_token`
2. Issue liée à un repository
3. Repository avec `full_name` valide (owner/repo)

## Test Manual

1. Créer une issue synchronisée avec GitHub
2. Cliquer sur "Copilot Dev" sur la card
3. (Optionnel) Ajouter des instructions personnalisées
4. Cliquer "Assigner à Copilot"
5. Vérifier:
   - Badge "Copilot" apparaît sur la card
   - Bouton "Copilot Dev" disparaît
   - Sur GitHub: issue assignée à `copilot-swe-agent[bot]`
   - Notification GitHub reçue
   - PR créée automatiquement

## Script de Test

```bash
# Test service backend
python backend/tests/test_copilot_assignment_service.py

# Test complet (requiert issue existante)
python backend/tests/test_copilot_agent.py
```

## Gestion des Erreurs

### Erreurs Communes

| Erreur           | Cause                        | Solution                             |
| ---------------- | ---------------------------- | ------------------------------------ |
| 401 Unauthorized | Token manquant/invalide      | Vérifier github_access_token user    |
| 404 Not Found    | Issue/Repository introuvable | Vérifier IDs                         |
| 400 Bad Request  | github_issue_number manquant | Synchroniser l'issue avec GitHub     |
| 500 Server Error | Copilot non disponible       | Vérifier activation Copilot org/repo |

### Logs

```python
# Backend
logger.info(f"Assigning issue #{issue_number} to Copilot")
logger.error(f"Error assigning issue: {e}")

# Frontend
console.log(`Issue #${issue.github_issue_number} n'a pas de github_issue_url`)
```

## Améliorations Futures

- [ ] Toast notifications au lieu d'alerts
- [ ] Vérification disponibilité Copilot avant d'afficher le bouton
- [ ] Badge de statut PR (ouvert/merged)
- [ ] Lien direct vers la PR créée
- [ ] Historique des assignations Copilot
- [ ] Annulation d'assignation depuis l'UI
