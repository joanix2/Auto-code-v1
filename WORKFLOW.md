# Workflow de Traitement Automatique des Tickets

Ce document décrit le workflow complet de traitement automatique des tickets avec le LLM.

## Vue d'ensemble

Le système implémente un processus itératif de développement automatique basé sur **LangGraph** (state machine).

### Workflow Principal

1. **Préparation** : Clone/pull du repo, gestion des branches
2. **Conversation** : Récupération ou création de messages avec le LLM
3. **Boucle principale** : Reasoning LLM → Code → Commit → CI
4. **Validation** : Attente de validation humaine
5. **Finalisation** : Création de PR ou retour en TODO

### Implementation

Le workflow est implémenté avec **LangGraph StateGraph** qui orchestre tous les états et transitions :

- **Fichier principal** : `backend/src/services/ticket_workflow.py`
- **State** : `TicketProcessingState` (Pydantic model)
- **Nodes** : 9 étapes du workflow
- **Edges** : Transitions conditionnelles entre états
- **Service Facade** : `TicketProcessingService` délègue à `TicketProcessingWorkflow`

## Architecture LangGraph

### State Machine

### State Machine

```
                            START
                              │
                              ▼
                    ┌─────────────────┐
                    │ check_iterations│ (Node 1)
                    │ Vérif MAX=5     │
                    └────────┬────────┘
                             │
                  ┌──────────┴──────────┐
                  │                     │
              EXCEEDED               CONTINUE
                  │                     │
                  ▼                     ▼
            ┌──────────┐      ┌──────────────────┐
            │create_bug│      │prepare_repository│ (Node 2)
            │_ticket   │      │Clone/Pull/Branch │
            └────┬─────┘      └────────┬─────────┘
                 │                     │
                 ▼                     ▼
               END          ┌─────────────────────┐
                            │load_conversation    │ (Node 3)
                            │Get/Create Messages  │
                            └──────────┬──────────┘
                                       │
                                       ▼
                            ┌─────────────────────┐
                            │    call_llm         │ (Node 4)
                            │ ClaudeAgent.run()   │
                            └──────────┬──────────┘
                                       │
                            ┌──────────┴──────────┐
                            │                     │
                        NO CHANGES            HAS CHANGES
                            │                     │
                            ▼                     ▼
                          END           ┌─────────────────┐
                                        │commit_changes   │ (Node 5)
                                        │Git commit       │
                                        └────────┬────────┘
                                                 │
                                                 ▼
                                        ┌─────────────────┐
                                        │    run_ci       │ (Node 6)
                                        │pytest/npm/make  │
                                        └────────┬────────┘
                                                 │
                                                 ▼
                                        ┌─────────────────┐
                                        │handle_ci_result │ (Node 7)
                                        │Check CI status  │
                                        └────────┬────────┘
                                                 │
                                  ┌──────────────┴──────────────┐
                                  │                             │
                              CI FAILED                     CI PASSED
                                  │                             │
                    ┌─────────────┴──────────┐                 │
                    │                        │                 │
            iterations < MAX        iterations >= MAX          │
                    │                        │                 │
                    ▼                        ▼                 ▼
            ┌──────────────┐      ┌──────────────┐   ┌────────────────┐
            │   call_llm   │      │create_bug    │   │await_validation│ (Node 8)
            │ (with error) │      │_ticket       │   │Set PENDING_VAL │
            └──────┬───────┘      └──────┬───────┘   └────────────────┘
                   │                     │                    │
                   └──────────┬──────────┘                    │
                              │                               │
                              ▼                               ▼
                            END                             END
```

### Nodes (Étapes du Workflow)

1. **check_iterations** : Vérifie si MAX_ITERATIONS (5) est dépassé
2. **prepare_repository** : Clone/pull repo, crée/checkout branche, rebase
3. **load_conversation** : Charge messages existants ou crée message initial
4. **call_llm** : Appelle ClaudeAgent pour analyse/génération de code
5. **commit_changes** : Commit les modifications Git
6. **run_ci** : Exécute tests CI/CD (pytest, npm test, make test, GitHub Actions)
7. **handle_ci_result** : Traite le résultat des tests
8. **await_validation** : Attend validation humaine (état final PENDING_VALIDATION)
9. **create_bug_ticket** : Crée ticket de bug si échec (état final CANCELLED)

### Conditional Edges (Décisions)

- **\_should_continue_after_check** : Continue ou crée bug ticket
- **\_should_commit** : Commit si changements détectés
- **\_should_retry_or_validate** : Retry (CI échec + iterations<MAX) ou Validate (CI OK) ou Bug ticket (CI échec + iterations≥MAX)

## Architecture Technique

### Structure des Fichiers

```
backend/src/
├── services/
│   ├── ticket_workflow.py          # LangGraph StateGraph (workflow complet)
│   ├── ticket_processing_service.py # Facade service (délègue au workflow)
│   ├── git_service.py               # Opérations Git
│   └── ci_service.py                # Tests CI/CD
├── models/
│   ├── ticket.py                    # Ticket model (avec iteration_count)
│   └── message.py                   # Message model (conversation LLM)
├── repositories/
│   ├── ticket_repository.py         # CRUD tickets
│   └── message_repository.py        # CRUD messages
└── controllers/
    ├── ticket_processing_controller.py # API endpoints
    └── message_controller.py           # API messages
```

### LangGraph Implementation

#### TicketProcessingState (Pydantic Model)

```python
class TicketProcessingState(BaseModel):
    # Ticket info
    ticket_id: str
    ticket: Optional[Ticket] = None
    repository: Optional[Any] = None

    # Paths
    repo_path: Optional[str] = None
    branch_name: Optional[str] = None

    # Conversation
    conversation: List[Message] = []
    last_message: Optional[Message] = None

    # Results
    llm_response: Optional[Dict[str, Any]] = None
    ci_result: Optional[CIResult] = None

    # State tracking
    iteration_count: int = 0
    has_uncommitted_changes: bool = False
    error: Optional[str] = None
    status: str = "OPEN"
```

#### TicketProcessingWorkflow (LangGraph)

```python
class TicketProcessingWorkflow:
    def __init__(self, github_token: Optional[str] = None):
        # Initialize services
        self.ticket_repo = TicketRepository()
        self.message_repo = MessageRepository()
        self.repository_repo = RepositoryRepository()
        self.git_service = GitService()
        self.ci_service = CIService()

        # Build StateGraph
        self.workflow = self._build_workflow()

    def _build_workflow(self) -> StateGraph:
        workflow = StateGraph(TicketProcessingState)

        # Add nodes
        workflow.add_node("check_iterations", self._check_iterations)
        workflow.add_node("prepare_repository", self._prepare_repository)
        workflow.add_node("load_conversation", self._load_conversation)
        workflow.add_node("call_llm", self._call_llm)
        workflow.add_node("commit_changes", self._commit_changes)
        workflow.add_node("run_ci", self._run_ci)
        workflow.add_node("handle_ci_result", self._handle_ci_result)
        workflow.add_node("await_validation", self._await_validation)
        workflow.add_node("create_bug_ticket", self._create_bug_ticket)

        # Set entry point
        workflow.set_entry_point("check_iterations")

        # Add conditional edges
        workflow.add_conditional_edges(
            "check_iterations",
            self._should_continue_after_check,
            {
                "continue": "prepare_repository",
                "create_bug": "create_bug_ticket"
            }
        )

        workflow.add_edge("prepare_repository", "load_conversation")
        workflow.add_edge("load_conversation", "call_llm")

        workflow.add_conditional_edges(
            "call_llm",
            self._should_commit,
            {
                "commit": "commit_changes",
                "end": END
            }
        )

        workflow.add_edge("commit_changes", "run_ci")
        workflow.add_edge("run_ci", "handle_ci_result")

        workflow.add_conditional_edges(
            "handle_ci_result",
            self._should_retry_or_validate,
            {
                "retry": "call_llm",
                "validate": "await_validation",
                "create_bug": "create_bug_ticket"
            }
        )

        workflow.add_edge("await_validation", END)
        workflow.add_edge("create_bug_ticket", END)

        return workflow.compile()

    async def execute(self, ticket_id: str) -> TicketProcessingState:
        """Execute workflow for a ticket"""
        initial_state = TicketProcessingState(ticket_id=ticket_id)
        result = await self.workflow.ainvoke(initial_state)
        return result
```

## Composants

### 1. Services

#### **TicketProcessingWorkflow** (`src/services/ticket_workflow.py`)

**State Machine LangGraph** - Orchestre tout le workflow :

- `execute()` : Point d'entrée, lance le StateGraph
- `_check_iterations()` : Node - Vérifie MAX_ITERATIONS
- `_prepare_repository()` : Node - Clone/pull/branch
- `_load_conversation()` : Node - Charge messages
- `_call_llm()` : Node - Appelle ClaudeAgent
- `_commit_changes()` : Node - Git commit
- `_run_ci()` : Node - Exécute tests
- `_handle_ci_result()` : Node - Traite résultat CI
- `_await_validation()` : Node - État final PENDING_VALIDATION
- `_create_bug_ticket()` : Node - État final CANCELLED
- `_should_continue_after_check()` : Decision - Continue ou bug
- `_should_commit()` : Decision - Commit si changements
- `_should_retry_or_validate()` : Decision - Retry/Validate/Bug

#### **TicketProcessingService** (`src/services/ticket_processing_service.py`)

**Facade Service** - Délègue au workflow LangGraph :

- `process_ticket()` : Appelle `workflow.execute(ticket_id)` et retourne le résultat
- `handle_validation_result()` : Gère la validation humaine (approuvé/rejeté)
- `_create_bug_ticket()` : Crée un ticket de bug quand MAX_ITERATIONS est dépassé

#### **GitService** (`src/services/git_service.py`)

Gère toutes les opérations Git :

- `is_cloned()` : Vérifie si le repo est cloné
- `clone()` : Clone un repository
- `get_repo_path()` : Retourne path local (structure `workspace/owner/repo`)
- `pull()` : Pull les dernières modifications
- `branch_exists()` : Vérifie l'existence d'une branche
- `create_branch()` : Crée une nouvelle branche
- `checkout_branch()` : Checkout une branche
- `rebase_branch()` : Rebase une branche
- `has_uncommitted_changes()` : Vérifie si des changements non commités existent
- `commit_changes()` : Commit les modifications
- `push_branch()` : Push vers remote

**Workspace Structure**: `/tmp/autocode-workspace/owner/repo`

- Parse owner et repo depuis URL (SSH ou HTTPS)
- Évite conflits entre repos avec même nom

#### **CIService** (`src/services/ci_service.py`)

Exécute les tests CI/CD :

- `run_ci()` : Lance les tests (pytest, npm test, make test)
- `_run_pytest()` : Tests Python
- `_run_npm_test()` : Tests Node.js
- `_run_make_test()` : Tests Make
- `_check_github_actions()` : Vérifie GitHub Actions
- `create_ci_error_message()` : Formate les erreurs pour le LLM

### 2. Modèles

#### **Ticket** (`src/models/ticket.py`)

```python
class Ticket:
    id: str
    title: str
    description: str
    type: str  # "feature", "bugfix", "refactor"
    priority: str  # "low", "medium", "high", "critical"
    status: str  # "OPEN", "PENDING", "PENDING_VALIDATION", "CLOSED", "CANCELLED"
    repository_id: str
    order: int
    iteration_count: int  # NEW: Compteur d'itérations
```

#### **Message** (`src/models/message.py`)

```python
class Message:
    id: str
    ticket_id: str
    role: str  # "user", "assistant", "system"
    content: str
    timestamp: datetime
    model: Optional[str]  # "claude-opus-4-20250514"
    tokens_used: Optional[int]
    step: Optional[str]  # "ticket_description", "analysis", "code_generation",
                         # "review", "ci_error", "human_feedback"
```

    model: Optional[str]  # e.g., "claude-opus-4-20250514"
    tokens_used: Optional[int]
    step: Optional[str]  # "analysis", "code_generation", etc.

````

#### **Ticket** (mis à jour)

Nouveau champ ajouté :

```python
iteration_count: int = 0  # Compteur d'itérations
````

### 3. Repository

#### **MessageRepository** (`src/repositories/message_repository.py`)

- `create()` : Créer un message
- `get_by_ticket_id()` : Récupérer tous les messages d'un ticket
- `get_latest_by_ticket_id()` : Dernier message
- `get_by_step()` : Messages par étape du workflow
- `get_conversation_summary()` : Statistiques de conversation

### 4. API Endpoints

#### **POST** `/api/tickets/processing/start`

Démarre le traitement automatique d'un ticket

**Request:**

```json
{
  "ticket_id": "abc-123"
}
```

**Response:**

```json
{
  "success": true,
  "status": "PENDING_VALIDATION",
  "iterations": 3,
  "message": "Code generated and CI passed, awaiting human validation"
}
```

#### **POST** `/api/tickets/processing/validation`

Soumet le résultat de validation humaine

**Request:**

```json
{
  "ticket_id": "abc-123",
  "approved": true,
  "feedback": "Looks good!"
}
```

**Response:**

```json
{
  "success": true,
  "status": "CLOSED",
  "message": "Changes approved and PR created"
}
```

#### **GET** `/api/tickets/processing/status/{ticket_id}`

Obtient le statut du traitement

**Response:**

```json
{
  "ticket_id": "abc-123",
  "status": "PENDING_VALIDATION",
  "iteration_count": 3,
  "conversation": {
    "total_messages": 7,
    "total_tokens": 15000,
    "roles": ["user", "assistant", "system"],
    "steps": ["ticket_description", "analysis", "code_generation", "review"]
  }
}
```

#### **GET** `/api/messages/ticket/{ticket_id}`

Récupère tous les messages d'un ticket

#### **GET** `/api/messages/ticket/{ticket_id}/latest`

Récupère le dernier message

## Configuration

### Variables d'environnement

```env
# Claude API
ANTHROPIC_API_KEY=sk-ant-...

# GitHub (pour PR et Actions)
GITHUB_TOKEN=ghp_...

# Workspace
WORKSPACE_ROOT=/tmp/autocode-workspace

# Limites
MAX_ITERATIONS=10
```

### Constantes

Dans `ticket_processing_service.py` :

```python
MAX_ITERATIONS = 10  # Nombre max d'itérations avant annulation
```

## Workflow détaillé

### Phase 1 : Initialisation

1. **Récupération du ticket** depuis Neo4j
2. **Vérification du compteur d'itérations**
   - Si `iteration_count >= MAX_ITERATIONS` : CANCELLED + bug ticket
3. **Changement de statut** : OPEN → PENDING

### Phase 2 : Préparation Repository

1. **Clone ou Pull**

   ```python
   if not git_service.is_cloned(repo_url):
       git_service.clone(repo_url)
   else:
       git_service.pull(repo_url)
   ```

2. **Gestion des branches**

   ```python
   branch_name = f"ticket-{ticket.id[:8]}"
   if not git_service.branch_exists(repo_url, branch_name):
       git_service.create_branch(repo_url, branch_name)
   else:
       git_service.checkout_branch(repo_url, branch_name)
   ```

3. **Rebase sur main**
   ```python
   git_service.rebase_branch(repo_url, branch_name, "main")
   ```

### Phase 3 : Conversation

1. **Récupération des messages existants**

   ```python
   conversation = message_repo.get_by_ticket_id(ticket_id)
   ```

2. **Si aucun message** : création du message initial
   ```python
   initial_message = create_message_from_ticket(ticket)
   ```

### Phase 4 : Boucle Principale

```python
while True:
    # Sécurité
    if ticket.iteration_count >= MAX_ITERATIONS:
        ticket.status = CANCELLED
        create_bug_ticket(ticket)
        return

    # LLM
    response = call_llm(agent, ticket, repository, last_message)

    # Apply code (à implémenter)
    apply_code_modifications(response)

    # Commit
    git_service.commit_changes(...)

    # CI
    ci_result = ci_service.run_ci(repo_path)

    # Increment
    ticket.iteration_count += 1

    # Check CI
    if ci_result.failed:
        error_message = create_ci_error_message(ci_result)
        message_repo.create(error_message)
        continue  # Retry

    # CI passed!
    ticket.status = PENDING_VALIDATION
    return  # Wait for human
```

### Phase 5 : Validation Humaine

Deux scénarios :

**Approuvé** :

```python
github_service.create_pull_request(...)
ticket.status = CLOSED
```

**Rejeté** :

```python
rejection_message = create_rejection_message(feedback)
message_repo.create(rejection_message)
ticket.status = OPEN
```

## Gestion des erreurs

### Dépassement du nombre d'itérations

Quand `iteration_count >= MAX_ITERATIONS` :

1. Ticket → CANCELLED
2. Création automatique d'un ticket de bug :
   ```
   Title: [BUG] Failed to process: {original_title}
   Type: bugfix
   Priority: high
   Status: OPEN
   ```

### Échec de préparation du repo

- Ticket → CANCELLED
- Retour d'erreur avec détails

### Échec du LLM

- Ticket → CANCELLED
- Log de l'erreur
- Notification à l'utilisateur

### Échec CI

- Message d'erreur ajouté à la conversation
- Retry automatique (nouvelle itération)
- Le LLM reçoit l'erreur et peut corriger

## Intégration avec le frontend

Le frontend peut déclencher le traitement via le bouton "Développer automatiquement" :

```typescript
const handleDevelop = async (ticketId: string) => {
  const response = await fetch("/api/tickets/processing/start", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ ticket_id: ticketId }),
  });

  const result = await response.json();

  if (result.status === "PENDING_VALIDATION") {
    // Afficher interface de validation
    showValidationUI(ticketId);
  }
};
```

## Prochaines étapes

### Court terme

- [ ] Implémenter `apply_code_modifications()` réel
- [ ] Intégration frontend pour validation
- [ ] Améliorer gestion des erreurs de rebase
- [ ] Ajouter logs détaillés

### Moyen terme

- [ ] Support multi-fichiers pour modifications
- [ ] Analyse de code existant avant modification
- [ ] Suggestions automatiques de tests
- [ ] Dashboard de monitoring des itérations

### Long terme

- [ ] Mode interactif avec feedback temps réel
- [ ] Optimisation des coûts LLM
- [ ] Métriques de qualité de code
- [ ] Apprentissage des patterns de réussite

## Debugging

### Voir les messages d'un ticket

```bash
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/messages/ticket/abc-123
```

### Voir le statut du traitement

```bash
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/tickets/processing/status/abc-123
```

### Logs

Les logs sont dans la console du backend :

```
INFO - Starting ticket processing for abc-123
INFO - Repository prepared at /tmp/autocode-workspace/my-repo
INFO - Processing iteration 1 for ticket abc-123
INFO - CI result: CIResult(success=True, message='All pytest tests passed')
INFO - Ticket abc-123 waiting for human validation
```
