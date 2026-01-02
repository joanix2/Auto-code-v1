# 🚀 OpenCode Service - Quick Start Guide

## ✅ Ce qui est installé et opérationnel

### 1. **Service Docker OpenCode**

- ✅ Image Docker construite : `autocode-opencode-service`
- ✅ Conteneur actif : `autocode-opencode`
- ✅ OpenCode AI installé dans le conteneur
- ✅ GitHub CLI configuré
- ✅ SSH pour GitHub configuré
- ✅ Python 3 + Node.js installés

### 2. **Configuration**

- ✅ Token GitHub configuré (`GH_TOKEN`)
- ✅ Clé SSH montée depuis l'hôte
- ✅ Workspace isolé : `/home/ubuntu/workspace`

## 📋 Commandes disponibles

### Gestion du conteneur

```bash
cd opencode-service

# Statut du service
./manage-opencode.sh status

# Accéder au shell du conteneur
./manage-opencode.sh exec

# Voir les logs
./manage-opencode.sh logs

# Redémarrer
./manage-opencode.sh restart

# Arrêter
./manage-opencode.sh stop

# Reconstruire complètement
./manage-opencode.sh rebuild
```

## 🔧 Configuration OpenCode

⚠️ **Important** : OpenCode doit être authentifié pour fonctionner.

### Option 1 : Authentifier OpenCode localement (recommandé)

```bash
# Sur ta machine hôte
opencode auth login

# Sélectionne ton LLM préféré (GPT-4, Claude, etc.)
# Cela créera ~/.local/share/opencode/auth.json
# Ce fichier sera automatiquement monté dans le conteneur
```

### Option 2 : Authentifier dans le conteneur

```bash
# Entrer dans le conteneur
./manage-opencode.sh exec

# Authentifier OpenCode
/home/ubuntu/.opencode/bin/opencode auth login

# Sortir
exit
```

## 🧪 Test rapide

### 1. Tester OpenCode dans le conteneur

```bash
# Entrer dans le conteneur
./manage-opencode.sh exec

# Créer un projet test
cd /home/ubuntu/workspace
mkdir test-project
cd test-project
git init

# Tester OpenCode
echo "Create a hello world Python script" | /home/ubuntu/.opencode/bin/opencode .

# Sortir
exit
```

### 2. Tester le service Python

```bash
cd ../backend

python -c "
import asyncio
from src.services.opencode_service import OpenCodeService

async def test():
    service = OpenCodeService()

    # Vérifier le statut
    status = await service.get_container_status()
    print(f'Container running: {status[\"running\"]}')
    print(f'Container exists: {status[\"exists\"]}')

asyncio.run(test())
"
```

## 🔗 Intégration avec Auto-Code

### Ajouter un endpoint API

Éditer `backend/src/controllers/ticket_controller.py` :

```python
from src.services.opencode_service import OpenCodeService

opencode_service = OpenCodeService()

@router.post("/tickets/{ticket_id}/develop-with-opencode")
async def develop_ticket_with_opencode(
    ticket_id: str,
    background_tasks: BackgroundTasks,
    current_user: str = Depends(get_current_user)
):
    # Get ticket and repository
    ticket = await ticket_repo.get_ticket_by_id(ticket_id)
    repository = await repo_repo.get_repository_by_id(ticket.repository_id)

    # Get user's GitHub token
    user = await user_repo.get_user(current_user)

    # Develop with OpenCode
    result = await opencode_service.develop_ticket(
        ticket_title=ticket.title,
        ticket_description=ticket.description,
        ticket_type=ticket.ticket_type,
        priority=ticket.priority,
        repository_url=repository.url,
        github_token=user.github_token
    )

    if result["success"]:
        # Update ticket status
        await ticket_repo.update_ticket_status(
            ticket_id,
            TicketStatus.pending_validation
        )

    return result
```

### Ajouter un bouton dans le frontend

Éditer `frontend/src/components/ClaudeDevelopmentBanner.tsx` :

```tsx
<div className="flex gap-2">
  <button onClick={() => developWithClaude()}>Develop with Claude</button>
  <button onClick={() => developWithOpenCode()}>Develop with OpenCode</button>
</div>
```

## 📊 Comparaison d'utilisation

| Tâche                | Claude (Actuel) | OpenCode (Nouveau) |
| -------------------- | --------------- | ------------------ |
| Génération de code   | ✅ Rapide       | ✅ Rapide          |
| Commits Git          | ❌ Non          | ✅ Oui             |
| Création de branches | ❌ Non          | ✅ Oui             |
| Pull Requests        | ❌ Non          | ✅ Oui             |
| Exécution de code    | ❌ Non          | ✅ Oui             |
| Isolation            | ✅ API externe  | ✅ Docker          |
| Coût                 | 💰 Pay-per-use  | 🆓 Gratuit\*       |

\*Selon le LLM backend utilisé (GPT-4, Claude, Llama, etc.)

## 🛠️ Troubleshooting

### Container ne démarre pas

```bash
# Voir les logs détaillés
docker logs autocode-opencode

# Rebuild
./manage-opencode.sh rebuild
```

### OpenCode ne répond pas

```bash
# Vérifier l'authentification
./manage-opencode.sh exec
/home/ubuntu/.opencode/bin/opencode auth status
```

### Erreur Git/GitHub

```bash
# Vérifier le token
echo $GH_TOKEN

# Tester l'accès GitHub
./manage-opencode.sh exec
gh auth status
```

## 📝 Prochaines étapes

1. ✅ ~~Installer et démarrer le service~~
2. ⏳ Authentifier OpenCode avec ton LLM
3. ⏳ Ajouter l'endpoint API dans le backend
4. ⏳ Ajouter le bouton dans le frontend
5. ⏳ Tester avec un vrai ticket

## 🎯 Objectif final

Permettre aux utilisateurs de choisir entre :

- **Claude** : Rapide, simple, génération de code textuelle
- **OpenCode** : Complet, commits Git, PRs automatiques, exécution dans conteneur isolé

---

**Status actuel** : ✅ Infrastructure prête, en attente d'authentification OpenCode
