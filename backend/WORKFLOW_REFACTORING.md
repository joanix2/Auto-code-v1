# Refactorisation du Workflow - Documentation

## 🎯 Objectif

Réduire la taille du fichier `ticket_workflow.py` (738+ lignes) et résoudre les problèmes de compatibilité avec LangGraph.

## 📁 Nouvelle Structure

```
backend/src/services/workflows/
├── __init__.py                       # Export TicketProcessingWorkflow
├── simple_ticket_workflow.py         # Workflow simplifié (~220 lignes)
├── workflow_state.py                 # État Pydantic (~45 lignes)
├── workflow_helpers.py               # Helpers WebSocket (~85 lignes)
└── workflow_conditions.py            # Fonctions conditionnelles (~75 lignes)
```

> **Note** : L'ancien `ticket_workflow.py` avec LangGraph a été supprimé car il causait des problèmes de compatibilité.

## 🔧 Changements Principaux

### 1. **workflow_state.py**

- Définition du modèle Pydantic `TicketProcessingState`
- Contient tous les champs nécessaires pour suivre l'état du workflow
- Séparé pour réutilisabilité

### 2. **workflow_helpers.py**

- `safe_ws_update()` : Envoi sécurisé de mises à jour WebSocket
- `safe_ws_log()` : Envoi sécurisé de logs WebSocket
- `log_workflow_step()` : Logging formaté des étapes
- `format_error_message()` : Formatage des erreurs
- `MAX_ITERATIONS = 10` : Configuration centralisée

### 3. **workflow_conditions.py**

- Fonctions de décision pour le workflow
- `should_continue_after_check()` : Continuer ou créer bug ticket
- `should_commit()` : Valider les changements LLM
- `should_continue_after_ci()` : Retry ou validation après CI
- Prêtes pour une future implémentation avec LangGraph

### 4. **simple_ticket_workflow.py** ⭐

Workflow simplifié sans dépendance à LangGraph :

#### Étapes du workflow :

1. **\_check_iterations** : Vérifier le nombre d'itérations
2. **\_prepare_repository** : Préparer le dépôt Git
3. **\_load_conversation** : Charger l'historique des messages
4. **\_call_llm** : Générer le code avec DummyAgent
5. **\_commit_changes** : Committer les modifications
6. **\_run_ci** : Exécuter les tests CI
7. **\_handle_ci_result** : Gérer les résultats
8. **\_handle_max_iterations** : Créer un bug ticket si limite atteinte

#### Intégrations :

- ✅ **DummyAgent** : Génération de code (remplace ClaudeAgent temporairement)
- ✅ **GitService** : Opérations Git
- ✅ **CIService** : Tests CI (skippé pour l'instant)
- ✅ **Repositories** : Neo4j (TicketRepository, MessageRepository, RepositoryRepository)
- ✅ **WebSocket** : Mises à jour en temps réel (avec fallback safe)

## 🐛 Problèmes Résolus

### 1. **Erreur LangGraph**

```
ImportError: cannot import name 'RemoveMessage' from 'langchain_core.messages'
```

**Solution** : Créé un workflow simplifié sans LangGraph

### 2. **Erreur Repository Init**

```
TypeError: TicketRepository.__init__() missing 1 required positional argument: 'db'
```

**Solution** : Ajouté `db = Neo4jConnection()` dans `__init__`

### 3. **Erreur MessageRepository**

```
TypeError: MessageRepository() takes no arguments
```

**Solution** : MessageRepository utilise des méthodes statiques, pas de `db` nécessaire

### 4. **Erreur Event Loop WebSocket**

```
RuntimeError: no running event loop
```

**Solution** : Créé `safe_ws_update()` et `safe_ws_log()` avec try/except

### 5. **Fichier trop volumineux**

**Solution** : Segmenté en 5 fichiers modulaires

## 🚀 Utilisation

```python
from src.services.workflows import TicketProcessingWorkflow

# Initialiser le workflow
workflow = TicketProcessingWorkflow(github_token="ghp_xxx")

# Exécuter pour un ticket
result = await workflow.execute(ticket_id="d09ca245-...")

# Résultat
{
    "success": True,
    "ticket_id": "d09ca245-...",
    "status": "PENDING_VALIDATION",
    "commit_hash": "abc123",
    "message": "Code generated and tests passed"
}
```

## 📊 Statistiques

| Fichier                     | Lignes   | Rôle                     |
| --------------------------- | -------- | ------------------------ |
| `simple_ticket_workflow.py` | ~220     | Orchestration principale |
| `workflow_state.py`         | ~45      | Modèle de données        |
| `workflow_helpers.py`       | ~85      | Utilitaires              |
| `workflow_conditions.py`    | ~75      | Logique de décision      |
| **TOTAL**                   | **~425** | vs 738+ lignes avant     |

## 🔄 Prochaines Étapes

1. ⏳ Implémenter les vraies opérations Git (clone, checkout, push)
2. ⏳ Activer les tests CI
3. ⏳ Créer les pull requests automatiquement
4. ⏳ Remplacer DummyAgent par ClaudeAgent (quand LangGraph sera fixé)
5. ⏳ Implémenter la création de bug tickets
6. ⏳ Ajouter la gestion des retries avec queue

## ✅ Tests Validés

```bash
✅ Workflow module loads!
✅ Workflow instantiates!
✅ Agent type: DummyAgent
✅ TicketProcessingService module loads!
✅ TicketProcessingService instantiates!
✅ Workflow type: TicketProcessingWorkflow
```

## 🎨 Architecture

```
Frontend (Button "Développer automatiquement")
    ↓ POST /api/tickets/processing/start
TicketProcessingController
    ↓ background_tasks.add_task()
TicketProcessingService.process_ticket()
    ↓ workflow.execute()
TicketProcessingWorkflow (simple_ticket_workflow.py)
    ↓ _check_iterations → _prepare_repository → _load_conversation
    ↓ _call_llm (DummyAgent) → _commit_changes → _run_ci
    ↓ _handle_ci_result
Result: PENDING_VALIDATION ou FAILED ou CANCELLED
```

## 🔧 Configuration

- **MAX_ITERATIONS** : 10 (dans `workflow_helpers.py`)
- **Workspace** : `/tmp/autocode-workspace`
- **Agent** : `DummyAgent` (temporaire)
- **WebSocket** : Updates en temps réel avec fallback safe

---

**Date** : 6 janvier 2026
**Statut** : ✅ Fonctionnel avec DummyAgent
