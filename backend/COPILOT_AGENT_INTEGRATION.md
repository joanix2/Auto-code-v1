# GitHub Copilot Agent Integration

## 🤖 Vue d'ensemble

AutoCode utilise maintenant l'API **GitHub Copilot Coding Agent** pour le développement automatique, remplaçant le workflow Claude précédent. Cette intégration permet à Copilot de travailler directement sur vos tickets en créant des Pull Requests automatiquement.

## ⚠️ Prérequis

**IMPORTANT** : Pour utiliser cette fonctionnalité, vous devez :

1. ✅ Avoir un **abonnement GitHub Copilot actif** (Individual, Business, ou Enterprise)
2. ✅ Activer la fonctionnalité **GitHub Copilot Agent** dans vos paramètres GitHub
3. ✅ Avoir les permissions appropriées sur le repository

**Sans abonnement Copilot** : Vous recevrez une erreur 400 avec le message "GitHub Copilot Agent is not enabled for this repository".

**Liens utiles** :

- 🔗 [GitHub Copilot Features](https://github.com/features/copilot)
- 🔗 [GitHub Copilot Pricing](https://github.com/features/copilot#pricing)
- 🔗 [Copilot Documentation](https://docs.github.com/en/copilot)

## 🆕 Changement majeur

**Avant** : Workflow Claude personnalisé  
**Maintenant** : GitHub Copilot Coding Agent officiel

### Avantages

✅ **Intégration native GitHub** - Directement intégré dans GitHub  
✅ **Notifications automatiques** - Vous êtes notifié quand la PR est prête  
✅ **Révision intégrée** - Utilisez les outils de révision de code GitHub  
✅ **Suivi d'avancement** - Visible directement dans l'issue/PR GitHub  
✅ **Modèles multiples** - Support de différents modèles AI  
✅ **Agents personnalisés** - Possibilité d'utiliser des agents spécialisés

## 📋 Architecture

### Backend

#### Service: `GitHubCopilotAgentService`

**Fichier**: `backend/src/services/github/copilot_agent_service.py`

**Méthodes principales**:

```python
async def assign_issue_to_copilot(
    owner: str,
    repo: str,
    issue_number: int,
    custom_instructions: Optional[str] = None,
    base_branch: Optional[str] = "main",
    custom_agent: Optional[str] = None,
    model: Optional[str] = None
) -> Dict[str, Any]
```

```python
async def create_issue_and_assign_to_copilot(
    owner: str,
    repo: str,
    title: str,
    body: str,
    custom_instructions: Optional[str] = None,
    base_branch: Optional[str] = "main",
    labels: Optional[list] = None,
    custom_agent: Optional[str] = None,
    model: Optional[str] = None
) -> Dict[str, Any]
```

```python
async def check_copilot_agent_status(
    owner: str,
    repo: str
) -> Dict[str, Any]
```

#### Contrôleur: `copilot_development_controller`

**Fichier**: `backend/src/controllers/copilot_development_controller.py`

**Endpoints**:

| Méthode | Endpoint                                            | Description                           |
| ------- | --------------------------------------------------- | ------------------------------------- |
| `POST`  | `/api/copilot/start-development`                    | Démarre le développement avec Copilot |
| `GET`   | `/api/copilot/check-copilot-status/{repository_id}` | Vérifie si Copilot est activé         |

## 🔧 API Endpoints

### 1. Démarrer le développement automatique

**Endpoint**: `POST /api/copilot/start-development`

**Request Body**:

```json
{
  "ticket_id": "uuid-du-ticket",
  "custom_instructions": "Instructions supplémentaires (optionnel)",
  "base_branch": "main",
  "model": "gpt-4" // Optionnel, pour Copilot Pro/Pro+
}
```

**Response**:

```json
{
  "success": true,
  "ticket_id": "uuid-du-ticket",
  "issue_number": 42,
  "issue_url": "https://github.com/owner/repo/issues/42",
  "message": "GitHub Copilot is now working on issue #42. You will be notified when the PR is ready for review."
}
```

**Comportement**:

1. ✅ Récupère le ticket depuis la base de données
2. ✅ Récupère les détails du repository
3. ✅ Vérifie que Copilot est activé pour ce repository
4. ✅ Si le ticket a déjà une issue GitHub → Assigne l'issue existante à Copilot
5. ✅ Sinon → Crée une nouvelle issue et l'assigne à Copilot
6. ✅ Met à jour le statut du ticket à `in_progress`
7. ✅ Construit des instructions automatiques depuis le ticket
8. ✅ Ajoute des labels automatiques (bug, enhancement, priority, autocode)

### 2. Vérifier le statut Copilot

**Endpoint**: `GET /api/copilot/check-copilot-status/{repository_id}`

**Response**:

```json
{
  "enabled": true,
  "message": "Copilot coding agent is enabled for this repository"
}
```

## 🔄 Workflow complet

### 1. Utilisateur clique sur "Développement automatique"

Frontend → `POST /api/copilot/start-development`

### 2. Backend traite la requête

```
┌─────────────────────────────────────────┐
│ 1. Récupérer le ticket                 │
│ 2. Récupérer le repository             │
│ 3. Vérifier le token GitHub            │
│ 4. Vérifier que Copilot est activé     │
│ 5. Construire les instructions         │
│ 6. Créer/Assigner issue à Copilot      │
│ 7. Mettre à jour le statut du ticket   │
└─────────────────────────────────────────┘
```

### 3. GitHub Copilot Agent travaille

- 🤖 Copilot analyse le ticket/issue
- 📝 Crée une branche de travail
- 💻 Implémente les changements
- ✅ Exécute les tests (si configurés)
- 🔀 Crée une Pull Request
- 👤 Vous ajoute comme reviewer

### 4. Notification utilisateur

- 📧 Email GitHub (PR créée + review requested)
- 🔔 Notification GitHub
- 🌐 Notification dans AutoCode (via webhook - à implémenter)

## 📝 Instructions automatiques

Le système construit automatiquement des instructions pour Copilot :

```markdown
**Ticket Details:**

- Title: {ticket.title}
- Type: {ticket.ticket_type}
- Priority: {ticket.priority}

**Description:**
{ticket.description}

**Additional Instructions:** (si fournies)
{custom_instructions}
```

## 🏷️ Labels automatiques

Le système ajoute automatiquement des labels à l'issue :

| Condition                        | Label ajouté                  |
| -------------------------------- | ----------------------------- |
| `ticket_type == "bugfix"`        | `bug`                         |
| `ticket_type == "feature"`       | `enhancement`                 |
| `ticket_type == "documentation"` | `documentation`               |
| Toujours                         | `priority: {ticket.priority}` |
| Toujours                         | `autocode`                    |

## ⚙️ Configuration requise

### Repository GitHub

1. **Copilot doit être activé** pour le repository
2. **Compte Copilot** :
   - GitHub Copilot Pro (personnel)
   - GitHub Copilot Business (organisation)
   - GitHub Copilot Enterprise (entreprise)

### Token GitHub

L'utilisateur doit avoir un **Personal Access Token** avec les permissions :

- ✅ `repo` (accès complet aux repositories)
- ✅ `issues` (lire/écrire les issues)
- ✅ `pull_requests` (lire/écrire les PRs)

## 🚨 Gestion d'erreurs

### Copilot non activé

```json
{
  "detail": "GitHub Copilot coding agent is not enabled for this repository"
}
```

**Solution** : Activer Copilot dans les paramètres du repository

### Token GitHub manquant

```json
{
  "detail": "GitHub account not connected. Please connect your GitHub account in settings."
}
```

**Solution** : Connecter le compte GitHub dans le profil

### Repository invalide

```json
{
  "detail": "Invalid repository format. Expected 'owner/repo'"
}
```

**Solution** : Vérifier que `repository.full_name` est au format `owner/repo`

## 📊 Suivi de progression

### Via GitHub

1. Ouvrir l'issue assignée à Copilot
2. Voir les commentaires de Copilot sur sa progression
3. Recevoir une notification quand la PR est créée
4. Reviewer la PR directement sur GitHub

### Via AutoCode (futur)

- WebSocket pour suivre la progression en temps réel
- Webhook GitHub pour recevoir les événements
- Dashboard de suivi des sessions Copilot

## 🔗 Intégration avec GitHub Issues

Si le ticket a déjà une issue GitHub liée :

- ✅ Réutilise l'issue existante
- ✅ Assigne simplement Copilot à cette issue
- ✅ Préserve le numéro et l'URL de l'issue

Si le ticket n'a pas d'issue :

- ✅ Crée une nouvelle issue
- ✅ Lie automatiquement l'issue au ticket
- ✅ Sauvegarde `github_issue_number` et `github_issue_url`

## 🎯 Prochaines étapes

### Frontend à implémenter

1. **Bouton "Développement avec Copilot"** dans la carte ticket
2. **Modal de configuration** :
   - Instructions personnalisées
   - Choix de la branche de base
   - Sélection du modèle (Pro/Pro+ uniquement)
3. **Indicateur de statut** :
   - "Copilot travaille..." pendant le développement
   - Lien vers l'issue/PR GitHub
4. **Notifications** :
   - Toast quand Copilot démarre
   - Toast quand la PR est prête

### Webhook GitHub

Implémenter un webhook pour recevoir les événements :

- `pull_request.opened` - PR créée par Copilot
- `pull_request.review_requested` - Review demandée
- `pull_request.closed` - PR mergée/fermée
- `issue.comment` - Commentaires de Copilot

## � Dépannage

### Erreur : "GitHub Copilot Agent is not enabled"

**Problème** : L'API GitHub retourne 404 lors de la vérification de `copilot-swe-agent[bot]`

**Causes possibles** :

1. ❌ Vous n'avez pas d'abonnement GitHub Copilot actif
2. ❌ La fonctionnalité Copilot Agent n'est pas activée pour votre compte
3. ❌ Le repository n'a pas accès à Copilot (limitation organisation)

**Solutions** :

1. ✅ Vérifier votre abonnement Copilot : [github.com/settings/copilot](https://github.com/settings/copilot)
2. ✅ Activer Copilot Agent dans les paramètres
3. ✅ Pour les organisations : vérifier les permissions dans Organization Settings

### Erreur : "GitHub account not connected"

**Problème** : Aucun token GitHub trouvé pour l'utilisateur

**Solution** : Connecter votre compte GitHub dans les paramètres de l'application

### Erreur : "Repository full_name not set"

**Problème** : Le repository n'a pas de `full_name` ou `owner_username`

**Solution** :

```bash
# Vérifier les données du repository dans Neo4j
MATCH (r:Repository) RETURN r.name, r.full_name, r.owner_username
```

Assurer que le repository a soit `full_name` (format: `owner/repo`) soit `owner_username` + `name`

### Mode développement sans Copilot

Si vous voulez tester l'application **sans abonnement Copilot** :

1. **Option 1** : Commenter temporairement la vérification Copilot

```python
# Dans copilot_development_controller.py
# copilot_status = await copilot_service.check_copilot_agent_status(owner, repo_name)
# if not copilot_status["enabled"]:
#     raise HTTPException(...)
```

2. **Option 2** : Utiliser uniquement la création d'issues GitHub

```python
# Créer juste l'issue sans assigner à Copilot
# Modifier create_issue_and_assign_to_copilot pour skip l'assignation
```

3. **Option 3** : Revenir temporairement au workflow Claude (branche précédente)

## �📖 Références

- [GitHub Copilot Coding Agent Docs](https://docs.github.com/en/copilot/using-github-copilot/asking-github-copilot-questions-in-github)
- [GitHub REST API - Issues](https://docs.github.com/en/rest/issues)
- [GitHub GraphQL API](https://docs.github.com/en/graphql)

## ✅ Avantages vs Claude Workflow

| Aspect             | Claude Workflow     | Copilot Agent         |
| ------------------ | ------------------- | --------------------- |
| Intégration GitHub | ⚠️ Via API manuelle | ✅ Native             |
| Notifications      | ⚠️ WebSocket custom | ✅ GitHub natif       |
| Révision code      | ⚠️ Manuelle         | ✅ GitHub PR review   |
| Tests CI/CD        | ⚠️ Trigger manuel   | ✅ Automatique        |
| Suivi progression  | ⚠️ Logs custom      | ✅ Issue GitHub       |
| Coût               | 💰 API Claude       | 💰 Abonnement Copilot |
| Personnalisation   | ✅ Workflow custom  | ⚠️ Agents custom      |

---

**Status** : ✅ Backend implémenté, prêt pour intégration frontend
