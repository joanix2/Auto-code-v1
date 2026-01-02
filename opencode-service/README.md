# OpenCode AI Service for Auto-Code

Service conteneurisé pour exécuter OpenCode AI dans un environnement Docker isolé, appelable via l'API Auto-Code.

## 📋 Prérequis

- Docker Desktop installé et en cours d'exécution
- Token GitHub (pour l'accès aux repositories privés)
- Clé SSH configurée (`~/.ssh/id_ed25519` ou `~/.ssh/id_rsa`)
- OpenCode AI authentifié localement (`opencode auth login`)

## 🏗️ Architecture

```
opencode-service/
├── Dockerfile              # Image Docker Ubuntu + OpenCode
├── manage-opencode.sh      # Script de gestion du conteneur
└── README.md              # Cette documentation

backend/src/services/
└── opencode_service.py    # Service Python pour l'intégration API
```

## 🚀 Installation

### 1. Configurer les variables d'environnement

```bash
# Token GitHub
export GH_TOKEN=ghp_your_github_token_here

# Optionnel: chemins personnalisés
export OPENCODE_SSH_KEY=~/.ssh/id_ed25519
```

### 2. Authentifier OpenCode localement

```bash
# Installer OpenCode si pas déjà fait
curl -fsSL https://opencode.ai/install | bash

# S'authentifier avec votre LLM préféré
opencode auth login
```

Cela créera `~/.local/share/opencode/auth.json` qui sera monté dans le conteneur.

### 3. Construire l'image Docker

```bash
cd opencode-service
./manage-opencode.sh build
```

## 📖 Utilisation

### Via le script de gestion

```bash
# Démarrer le conteneur
./manage-opencode.sh start

# Vérifier le statut
./manage-opencode.sh status

# Exécuter un shell dans le conteneur
./manage-opencode.sh exec

# Voir les logs
./manage-opencode.sh logs

# Arrêter le conteneur
./manage-opencode.sh stop

# Reconstruire complètement
./manage-opencode.sh rebuild
```

### Via l'API Python

```python
from src.services.opencode_service import OpenCodeService

# Initialiser le service
service = OpenCodeService()

# Développer un ticket
result = await service.develop_ticket(
    ticket_title="Add user authentication",
    ticket_description="Implement JWT-based authentication",
    ticket_type="feature",
    priority="high",
    repository_url="https://github.com/user/repo.git",
    github_token=os.getenv("GH_TOKEN")
)

print(result["output"])
```

### Intégration avec Auto-Code backend

Le service est déjà intégré dans le backend. Pour l'utiliser:

```python
# Dans ticket_controller.py
from src.services.opencode_service import OpenCodeService

opencode_service = OpenCodeService()

# Remplacer ou compléter ClaudeService
result = await opencode_service.develop_ticket(
    ticket_title=ticket.title,
    ticket_description=ticket.description,
    ticket_type=ticket.ticket_type,
    priority=ticket.priority,
    repository_url=repository.url,
    github_token=user.github_token
)
```

## 🔧 Configuration

### Volumes montés

Le conteneur monte automatiquement:

- `~/.ssh/id_ed25519` ou `~/.ssh/id_rsa` → Clé SSH (lecture seule)
- `~/.config/opencode` → Configuration OpenCode (agents, plugins)
- `~/.local/share/opencode/auth.json` → Authentification LLM

### Workspace

Les repositories sont clonés dans `/home/ubuntu/workspace/` dans le conteneur.

## 🎯 Avantages

### Sécurité

- ✅ Exécution isolée dans Docker
- ✅ Pas de risque pour le système hôte
- ✅ Container jetable et reproductible

### Flexibilité

- ✅ Support multi-repos
- ✅ Clone/pull automatique
- ✅ Authentification GitHub intégrée

### Scalabilité

- ✅ Multiples containers possibles
- ✅ Parallélisation des tâches
- ✅ Gestion des ressources Docker

## 🔄 Workflow typique

1. **API reçoit une demande** de développement de ticket
2. **Service démarre** le conteneur OpenCode (si nécessaire)
3. **Repository est cloné** ou mis à jour dans le conteneur
4. **OpenCode analyse** et implémente le ticket
5. **Commits sont créés** dans le repository
6. **Résultats sont retournés** à l'API
7. **PR peut être créée** automatiquement

## 📊 Comparaison Claude vs OpenCode

| Critère            | Claude (Haiku)            | OpenCode                        |
| ------------------ | ------------------------- | ------------------------------- |
| **Exécution**      | API externe               | Conteneur local                 |
| **Sécurité**       | Limité à génération texte | Isolation Docker complète       |
| **Actions Git**    | ❌ Non                    | ✅ Oui (commits, branches, PRs) |
| **Accès fichiers** | ❌ Non                    | ✅ Oui (lecture/écriture)       |
| **Coût**           | Pay-per-token             | Gratuit (selon LLM backend)     |
| **Vitesse**        | Rapide                    | Moyenne (overhead Docker)       |
| **Complexité**     | Simple                    | Avancée                         |

## 🐛 Dépannage

### Container ne démarre pas

```bash
# Vérifier Docker
docker info

# Voir les logs
./manage-opencode.sh logs

# Rebuild complet
./manage-opencode.sh rebuild
```

### Erreur d'authentification GitHub

```bash
# Vérifier le token
echo $GH_TOKEN

# Tester manuellement
docker exec -it autocode-opencode gh auth status
```

### OpenCode non trouvé

```bash
# Vérifier l'installation dans le container
docker exec -it autocode-opencode /home/ubuntu/.opencode/bin/opencode --version
```

## 📝 TODO

- [ ] Ajouter endpoint API FastAPI pour OpenCode
- [ ] Implémenter création automatique de PR
- [ ] Support de multiples containers en parallèle
- [ ] Métriques et monitoring
- [ ] Webhooks pour notifications
- [ ] Interface UI pour visualiser l'exécution

## 🔗 Liens utiles

- [Documentation OpenCode](https://opencode.ai/docs/)
- [Docker Documentation](https://docs.docker.com/)
- [GitHub CLI](https://cli.github.com/)

## 📄 Licence

Même licence que le projet Auto-Code principal.
