# Services Organization

Les services ont été réorganisés dans des sous-dossiers thématiques pour une meilleure maintenabilité.

## Structure

```
services/
├── git/                    # Services Git et VCS
│   ├── git_service.py      # Opérations Git (clone, pull, commit, push)
│   ├── branch_service.py   # Gestion des branches pour les tickets
│   ├── github_service.py   # API GitHub
│   └── BRANCH_SERVICE.md   # Documentation du service de branches
│
├── ai/                     # Services IA
│   ├── claude_service.py               # Service Claude (Anthropic)
│   └── ticket_processing_service.py    # Traitement des tickets par IA
│
├── messaging/              # Services de messages
│   └── message_service.py  # Gestion des messages des tickets
│
├── utils/                  # Services utilitaires
│   ├── file_modification_service.py    # Modification de fichiers
│   ├── image_service.py                # Traitement d'images
│   └── levenshtein_service.py          # Distance de Levenshtein
│
├── auth/                   # Services d'authentification
│   └── github_oauth_service.py         # OAuth GitHub
│
├── ci/                     # Services CI/CD
│   └── ci_service.py       # Intégration continue
│
└── workflows/              # Workflows
    └── ticket_workflow.py  # Workflow de traitement des tickets (LangGraph)
```

## Imports

### Imports directs depuis le package services

```python
from src.services import (
    # Git
    GitService,
    BranchService,
    GitHubService,
    # Messaging
    MessageService,
    # Utils
    FileModificationService,
    ImageService,
    levenshtein_service,
    # Auth
    GitHubOAuthService,
    # CI
    CIService,
)
```

### Imports depuis les sous-packages

```python
from src.services.git import GitService, BranchService
from src.services.messaging import MessageService
from src.services.utils import FileModificationService
```

### Imports lazy (AI et Workflows)

Les services AI et Workflows utilisent des dépendances lourdes (langgraph, langchain) et sont chargés dynamiquement :

```python
# Import automatique via __getattr__
from src.services import ClaudeService  # Chargé à la demande

# Ou import direct
from src.services.ai import ClaudeService
from src.services.workflows import TicketWorkflow
```

## Catégories de services

### 🔀 Git Services (`services/git/`)

Services liés à Git et GitHub :
- **GitService** : Opérations Git de base (clone, pull, commit, push, rebase)
- **BranchService** : Gestion automatique des branches pour les tickets
- **GitHubService** : Interaction avec l'API GitHub

**Use case** : Cloner un repo, créer une branche pour un ticket, commit/push les modifications

### 🤖 AI Services (`services/ai/`)

Services d'intelligence artificielle :
- **ClaudeService** : Communication avec l'API Claude (Anthropic)
- **TicketProcessingService** : Orchestration du traitement des tickets par IA

**Use case** : Traiter un ticket avec l'agent IA

### 💬 Messaging Services (`services/messaging/`)

Gestion des conversations :
- **MessageService** : CRUD et statistiques sur les messages des tickets

**Use case** : Récupérer l'historique des messages, vérifier les limites

### 🛠️ Utils Services (`services/utils/`)

Services utilitaires :
- **FileModificationService** : Modification intelligente de fichiers
- **ImageService** : Traitement et manipulation d'images
- **levenshtein_service** : Calcul de distance de Levenshtein (fuzzy matching)

**Use case** : Modifier un fichier, calculer la similarité entre deux chaînes

### 🔐 Auth Services (`services/auth/`)

Services d'authentification :
- **GitHubOAuthService** : Authentification OAuth avec GitHub

**Use case** : Gérer l'authentification des utilisateurs

### 🚀 CI Services (`services/ci/`)

Services CI/CD :
- **CIService** : Interaction avec les systèmes de CI/CD

**Use case** : Récupérer le statut des workflows GitHub Actions

### 📋 Workflow Services (`services/workflows/`)

Workflows complexes :
- **TicketWorkflow** : Workflow de traitement des tickets avec LangGraph

**Use case** : Orchestrer le traitement complet d'un ticket

## Migration depuis l'ancienne structure

Si vous aviez du code utilisant les anciens imports :

```python
# Ancien (ne fonctionne plus)
from src.services.git_service import GitService
from src.services.message_service import MessageService

# Nouveau (à utiliser)
from src.services import GitService, MessageService
# ou
from src.services.git import GitService
from src.services.messaging import MessageService
```

## Ajouter un nouveau service

1. Choisissez le dossier approprié (ou créez-en un nouveau)
2. Créez votre fichier de service
3. Ajoutez-le dans le `__init__.py` du sous-package
4. Ajoutez l'export dans `services/__init__.py`

**Exemple** : Ajouter un `DockerService`

```python
# services/ci/docker_service.py
class DockerService:
    def build(self):
        pass

# services/ci/__init__.py
from .docker_service import DockerService
__all__ = [..., "DockerService"]

# services/__init__.py
from .ci import DockerService
__all__ = [..., "DockerService"]
```

## Tests

Les tests doivent importer depuis le package principal :

```python
# tests/test_git_service.py
from src.services import GitService

def test_clone():
    service = GitService()
    # ...
```

## Bénéfices de cette organisation

✅ **Clarté** : Facile de trouver un service par catégorie
✅ **Modularité** : Chaque sous-package peut évoluer indépendamment
✅ **Lazy loading** : Services lourds chargés à la demande
✅ **Scalabilité** : Facile d'ajouter de nouveaux services
✅ **Documentation** : Chaque dossier peut avoir son README
✅ **Tests** : Plus facile de tester par catégorie

## Notes techniques

- Les imports relatifs dans les services utilisent `...` (3 points) au lieu de `..` (2 points) à cause du niveau d'imbrication supplémentaire
- Les services AI et Workflows utilisent `__getattr__` pour le lazy loading afin d'éviter les erreurs d'import si langgraph n'est pas installé
- Le module `levenshtein_service` est un module de fonctions, pas une classe, donc importé directement
