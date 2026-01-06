# Test GitHub Copilot Agent API

Script de test pour vérifier l'intégration avec l'API GitHub Copilot Agent.

## 🎯 Objectif

Ce script permet de tester directement l'API GitHub Copilot Agent sans passer par l'application AutoCode complète. Il effectue les opérations suivantes :

1. ✅ Vérifie si Copilot Agent est disponible pour votre repository
2. ✅ Crée une issue GitHub de test
3. ✅ Assigne l'issue à Copilot Agent
4. ✅ Affiche les détails de l'issue et son statut

## 📋 Prérequis

### 1. Abonnement GitHub Copilot

Vous devez avoir un **abonnement GitHub Copilot actif** :

- GitHub Copilot Individual ($10/mois)
- GitHub Copilot Business
- GitHub Copilot Enterprise

🔗 [Souscrire à GitHub Copilot](https://github.com/features/copilot)

### 2. Token GitHub Personnel

Créez un Personal Access Token avec les permissions suivantes :

1. Allez sur : https://github.com/settings/tokens
2. Cliquez sur "Generate new token (classic)"
3. Sélectionnez les scopes :
   - ✅ `repo` (Full control of private repositories)
   - ✅ `workflow` (Update GitHub Action workflows)
4. Générez le token et **copiez-le** (vous ne pourrez plus le voir après)

### 3. Configuration

Créez un fichier `.env` dans le dossier `backend/` :

```bash
# Copiez .env.example vers .env
cp .env.example .env

# Éditez .env et ajoutez votre token
nano .env
```

Ajoutez votre token dans `.env` :

```bash
GITHUB_TOKEN=ghp_votre_token_github_ici
```

## 🚀 Utilisation

### Exécuter le test

```bash
cd backend
python test_copilot_agent.py
```

### Sortie attendue

#### ✅ Si Copilot est activé :

```
============================================================
  Test GitHub Copilot Agent API
============================================================

✅ Token GitHub trouvé
   Repository: joanix2/Auto-code-v1

🔍 Vérification de la disponibilité de Copilot Agent...
✅ Copilot Agent est disponible pour joanix2/Auto-code-v1

📝 Création d'une issue de test...
✅ Issue #42 créée avec succès
   📎 URL: https://github.com/joanix2/Auto-code-v1/issues/42

🤖 Assignation de l'issue #42 à Copilot Agent...
📤 Envoi de la requête d'assignation...
✅ Issue #42 assignée à Copilot Agent avec succès !

🎉 Copilot va maintenant travailler sur cette issue
📬 Vous recevrez une notification GitHub quand la PR sera prête

👥 Assignees:
   - copilot-swe-agent[bot]

============================================================
✅ Test terminé avec succès !
============================================================

📝 Prochaines étapes:
1. Surveillez vos notifications GitHub
2. Copilot va créer une branche et travailler sur l'issue
3. Une PR sera créée automatiquement
4. Vous serez ajouté comme reviewer
```

#### ❌ Si Copilot n'est PAS activé :

```
============================================================
  Test GitHub Copilot Agent API
============================================================

✅ Token GitHub trouvé
   Repository: joanix2/Auto-code-v1

🔍 Vérification de la disponibilité de Copilot Agent...
❌ Copilot Agent n'est PAS disponible pour joanix2/Auto-code-v1
💡 Assurez-vous d'avoir un abonnement GitHub Copilot actif

============================================================
⚠️  Copilot Agent n'est pas disponible
============================================================

Pour activer Copilot Agent:
1. Visitez https://github.com/features/copilot
2. Souscrivez à GitHub Copilot (si pas déjà fait)
3. Activez la fonctionnalité Copilot Agent

💡 Le reste du test sera ignoré
```

## 🔍 Ce que fait le script

### 1. Vérification de Copilot (`check_copilot_availability`)

```python
GET https://api.github.com/repos/{owner}/{repo}/assignees/copilot-swe-agent[bot]

Response:
- 204 = Copilot disponible ✅
- 404 = Copilot non disponible ❌
```

### 2. Création d'une issue (`create_test_issue`)

```python
POST https://api.github.com/repos/{owner}/{repo}/issues

Body:
{
  "title": "🤖 Test GitHub Copilot Agent API",
  "body": "Description de la tâche...",
  "labels": ["test", "copilot-agent", "autocode"]
}

Response:
{
  "number": 42,
  "html_url": "https://github.com/owner/repo/issues/42",
  ...
}
```

### 3. Assignation à Copilot (`assign_issue_to_copilot`)

```python
POST https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}/assignees

Body:
{
  "assignees": ["copilot-swe-agent[bot]"],
  "agent_assignment": {
    "target_repo": "owner/repo",
    "base_branch": "main",
    "custom_instructions": "Instructions personnalisées..."
  }
}
```

## 📖 API Endpoints utilisés

| Endpoint                                          | Méthode | Description                            |
| ------------------------------------------------- | ------- | -------------------------------------- |
| `/repos/{owner}/{repo}/assignees/{assignee}`      | GET     | Vérifie si un assignee est disponible  |
| `/repos/{owner}/{repo}/issues`                    | POST    | Crée une nouvelle issue                |
| `/repos/{owner}/{repo}/issues/{number}/assignees` | POST    | Assigne une issue à un bot/utilisateur |
| `/repos/{owner}/{repo}/issues/{number}`           | GET     | Récupère les détails d'une issue       |

## 🐛 Dépannage

### Erreur : "GITHUB_TOKEN non défini"

**Solution** : Ajoutez votre token dans le fichier `.env`

```bash
GITHUB_TOKEN=ghp_votre_token_ici
```

### Erreur : "401 Unauthorized"

**Causes possibles** :

- Token invalide ou expiré
- Token sans les permissions nécessaires (`repo`, `workflow`)

**Solution** : Créez un nouveau token avec les bonnes permissions

### Erreur : "404 Not Found" sur l'assignee

**Cause** : Copilot Agent n'est pas activé

**Solution** : Activez votre abonnement GitHub Copilot

### Erreur : "422 Validation Failed"

**Cause** : Format du payload incorrect

**Solution** : Vérifiez que le repository existe et que vous avez les permissions

## 🎓 Personnalisation

### Modifier le repository cible

Éditez `test_copilot_agent.py` :

```python
OWNER = "votre_username"  # Votre username GitHub
REPO = "votre_repo"       # Nom du repository
```

### Modifier la tâche de test

Éditez la fonction `create_test_issue()` pour changer :

- Le titre de l'issue
- La description
- Les labels
- Les instructions pour Copilot

### Modifier les instructions Copilot

Dans `assign_issue_to_copilot()`, modifiez :

```python
"agent_assignment": {
    "target_repo": f"{owner}/{repo}",
    "base_branch": "main",  # Branche de base
    "custom_instructions": "Vos instructions ici..."  # Instructions personnalisées
}
```

## 📚 Ressources

- [GitHub Copilot Features](https://github.com/features/copilot)
- [GitHub REST API - Issues](https://docs.github.com/en/rest/issues)
- [GitHub REST API - Assignees](https://docs.github.com/en/rest/issues/assignees)
- [Creating a Personal Access Token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token)

## ✅ Prochaines étapes

Après avoir testé avec succès :

1. **Surveillez l'issue** : Copilot va commenter ses actions
2. **Attendez la PR** : Une Pull Request sera créée automatiquement
3. **Reviewez le code** : Vous serez notifié pour review
4. **Mergez** : Si le code est bon, mergez la PR

---

**Note** : Ce test crée une vraie issue sur votre repository GitHub. N'oubliez pas de la fermer après le test si vous ne voulez pas la garder.
