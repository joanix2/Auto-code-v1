# Système de Traitement Automatique des Tickets

## 📋 Vue d'ensemble

Le système implémente un workflow complet de développement automatique avec LLM, incluant :

- Conversation contextuelle avec l'IA via des messages persistés
- Workflow itératif avec gestion d'erreurs et CI/CD
- Validation humaine avant merge
- Création automatique de Pull Requests

## 🏗️ Architecture

### Nouveaux composants

#### 1. **Message System** - Conversation avec LLM

- **Model** : `Message` avec role, content, step, tokens
- **Repository** : CRUD + méthodes spécialisées (get_latest, get_by_step, conversation_summary)
- **Controller** : API REST complète pour les messages
- **Neo4j** : Relation `Ticket -[:HAS_MESSAGE]-> Message`

#### 2. **Services de Workflow**

**GitService** - Gestion Git complète

```python
git_service.clone(repo_url)
git_service.create_branch(branch_name)
git_service.rebase_branch(branch, "main")
git_service.commit_changes(message)
git_service.push_branch(branch)
```

**CIService** - Exécution des tests

```python
ci_result = ci_service.run_ci(repo_path)
if ci_result.failed:
    error_msg = ci_service.create_ci_error_message(ci_result)
```

**TicketProcessingService** - Orchestration principale

```python
result = await service.process_ticket(ticket_id)
result = await service.handle_validation_result(ticket_id, approved=True)
```

#### 3. **API Endpoints**

**Messages**

- `POST /api/messages/` - Créer un message
- `GET /api/messages/ticket/{ticket_id}` - Tous les messages
- `GET /api/messages/ticket/{ticket_id}/latest` - Dernier message
- `GET /api/messages/ticket/{ticket_id}/summary` - Statistiques

**Traitement**

- `POST /api/tickets/processing/start` - Démarrer le traitement
- `POST /api/tickets/processing/validation` - Soumettre validation
- `GET /api/tickets/processing/status/{ticket_id}` - Statut actuel

## 🔄 Workflow Détaillé

### 1. Démarrage du traitement

```bash
POST /api/tickets/processing/start
{
  "ticket_id": "abc-123"
}
```

### 2. Phases automatiques

```
┌─────────────────────────────────────────────┐
│ 1. Vérification MAX_ITERATIONS             │
│    → Si dépassé: CANCELLED + bug ticket    │
└─────────────────┬───────────────────────────┘
                  │
┌─────────────────▼───────────────────────────┐
│ 2. Préparation Repository                  │
│    → Clone/Pull                             │
│    → Créer/Checkout branche                 │
│    → Rebase sur main                        │
└─────────────────┬───────────────────────────┘
                  │
┌─────────────────▼───────────────────────────┐
│ 3. Récupération Conversation                │
│    → Messages existants?                    │
│    → Sinon: créer message initial           │
└─────────────────┬───────────────────────────┘
                  │
┌─────────────────▼───────────────────────────┐
│ 4. BOUCLE PRINCIPALE                        │
│                                             │
│   while (iteration < MAX_ITERATIONS):       │
│     ┌────────────────────────┐              │
│     │ LLM Reasoning          │              │
│     │ (ClaudeAgent)          │              │
│     └──────────┬─────────────┘              │
│                │                             │
│     ┌──────────▼─────────────┐              │
│     │ Apply Code Mods        │              │
│     └──────────┬─────────────┘              │
│                │                             │
│     ┌──────────▼─────────────┐              │
│     │ Git Commit             │              │
│     └──────────┬─────────────┘              │
│                │                             │
│     ┌──────────▼─────────────┐              │
│     │ Run CI/CD              │              │
│     └──────────┬─────────────┘              │
│                │                             │
│     ┌──────────▼─────────────┐              │
│     │ CI Failed?             │              │
│     └──┬────────────────┬────┘              │
│        │ OUI            │ NON               │
│        │                │                   │
│   ┌────▼────┐      ┌────▼────┐             │
│   │ Add Msg │      │ PENDING_│             │
│   │ Retry   │      │ VALID   │             │
│   └────┬────┘      └────┬────┘             │
│        │                │                   │
│        └────────┬───────┘                   │
│                 │                           │
└─────────────────┴───────────────────────────┘
                  │
┌─────────────────▼───────────────────────────┐
│ 5. Attente Validation Humaine               │
│    Status: PENDING_VALIDATION               │
└─────────────────────────────────────────────┘
```

### 3. Validation humaine

```bash
POST /api/tickets/processing/validation
{
  "ticket_id": "abc-123",
  "approved": true,
  "feedback": "Looks good!"
}
```

**Si approuvé** :

- Création d'une Pull Request sur GitHub
- Ticket → CLOSED

**Si rejeté** :

- Message de rejet ajouté à la conversation
- Ticket → OPEN (pour retry)

## 📊 Modèle de données

### Message

```python
{
  "id": "msg_xyz",
  "ticket_id": "ticket_abc",
  "role": "assistant",  # user | assistant | system
  "content": "Here's my analysis...",
  "timestamp": "2026-01-02T10:30:00",
  "model": "claude-opus-4-20250514",
  "tokens_used": 1500,
  "step": "analysis",  # ticket_description | analysis | code_generation | review | ci_error | human_feedback
  "metadata": {}
}
```

### Ticket (mis à jour)

```python
{
  "id": "ticket_abc",
  "title": "Add authentication",
  "iteration_count": 3,  # NOUVEAU
  "status": "PENDING_VALIDATION",
  ...
}
```

## 🔧 Configuration

### Variables d'environnement

```env
# Claude API
ANTHROPIC_API_KEY=sk-ant-api03-...

# GitHub (pour PR)
GITHUB_TOKEN=ghp_...

# Workspace
WORKSPACE_ROOT=/tmp/autocode-workspace

# Limites
MAX_ITERATIONS=10  # Dans ticket_processing_service.py
```

### Neo4j Contraintes

Nouvelles contraintes à ajouter :

```cypher
CREATE CONSTRAINT message_id IF NOT EXISTS
FOR (m:Message) REQUIRE m.id IS UNIQUE;
```

## 📝 Exemples d'utilisation

### Frontend : Démarrer le traitement

```typescript
const startProcessing = async (ticketId: string) => {
  const res = await fetch("/api/tickets/processing/start", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ ticket_id: ticketId }),
  });

  const result = await res.json();

  if (result.status === "PENDING_VALIDATION") {
    showValidationUI(ticketId);
  }
};
```

### Frontend : Valider les changements

```typescript
const validateChanges = async (ticketId: string, approved: boolean, feedback?: string) => {
  const res = await fetch("/api/tickets/processing/validation", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      ticket_id: ticketId,
      approved,
      feedback,
    }),
  });

  const result = await res.json();

  if (result.status === "CLOSED") {
    showSuccess("PR créée avec succès!");
  }
};
```

### Backend : Accéder à la conversation

```python
from src.repositories.message_repository import MessageRepository

message_repo = MessageRepository()

# Tous les messages
messages = message_repo.get_by_ticket_id("ticket_abc")

# Dernier message
last_msg = message_repo.get_latest_by_ticket_id("ticket_abc")

# Messages d'une étape spécifique
code_msgs = message_repo.get_by_step("ticket_abc", "code_generation")

# Statistiques
summary = message_repo.get_conversation_summary("ticket_abc")
# {
#   "total_messages": 7,
#   "total_tokens": 15000,
#   "roles": ["user", "assistant", "system"],
#   "steps": ["analysis", "code_generation", "review"]
# }
```

## 🚀 Déploiement

### 1. Installer dépendances

```bash
cd backend
pip install -r requirements.txt
```

Nouvelles dépendances :

- `anthropic>=0.40.0`
- `langgraph>=0.2.54`
- `langchain-core>=0.3.26`
- `langchain-anthropic>=0.3.5`
- `PyGithub==2.1.1` (déjà présent)

### 2. Configurer environnement

```bash
# backend/.env
ANTHROPIC_API_KEY=sk-ant-...
GITHUB_TOKEN=ghp_...
WORKSPACE_ROOT=/tmp/autocode-workspace
```

### 3. Démarrer le serveur

```bash
cd backend
python main.py
```

## 🐛 Debugging

### Voir les messages d'un ticket

```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/messages/ticket/abc-123"
```

### Statut du traitement

```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/tickets/processing/status/abc-123"
```

### Logs détaillés

Le backend log toutes les étapes :

```
INFO - Starting ticket processing for abc-123
INFO - Repository prepared at /tmp/autocode-workspace/my-repo
INFO - Processing iteration 1 for ticket abc-123
INFO - CI result: CIResult(success=True, message='All tests passed')
INFO - Ticket abc-123 waiting for human validation
```

## 📚 Documentation

- **WORKFLOW.md** : Documentation complète du workflow
- **flow.mmd** : Diagramme Mermaid du workflow
- **backend/src/agent/README.md** : Documentation de l'agent LangGraph
- **backend/src/agent/QUICKSTART.md** : Guide de démarrage rapide

## ⚠️ Limitations actuelles

1. **Application du code** : `apply_code_modifications()` n'est pas encore implémenté

   - Le LLM génère le code mais ne l'applique pas automatiquement
   - À implémenter : parsing du JSON et écriture des fichiers

2. **Tests** : Pas de tests unitaires pour les nouveaux services

3. **Gestion des conflits** : Le rebase peut échouer en cas de conflits

4. **Frontend** : UI de validation pas encore créée

## 🔜 Prochaines étapes

### Court terme

- [ ] Implémenter `apply_code_modifications()` réel
- [ ] Interface de validation dans le frontend
- [ ] Tests unitaires pour services
- [ ] Meilleure gestion des erreurs de rebase

### Moyen terme

- [ ] Support multi-fichiers complexe
- [ ] Analyse de codebase existant
- [ ] Suggestions automatiques de tests
- [ ] Dashboard de monitoring

### Long terme

- [ ] Mode interactif temps réel
- [ ] Optimisation coûts LLM
- [ ] Métriques qualité de code
- [ ] Apprentissage des patterns

## 🤝 Contribuer

Pour étendre le système :

1. **Ajouter un step au workflow** : Modifier `TicketProcessingService._processing_loop()`
2. **Nouveau type de CI** : Ajouter une méthode dans `CIService`
3. **Personnaliser l'agent** : Créer un nouveau workflow dans `backend/src/agent/workflow.py`

## 📄 License

Voir LICENSE principal du projet.
