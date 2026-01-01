# 🚀 Quick Start - Développement Automatique avec Claude

## En 5 minutes, testez le système headless !

### Prérequis

- Clé API Anthropic (gratuit pour commencer : https://console.anthropic.com/)
- Auto-Code déjà installé et fonctionnel
- Un ticket "open" dans un repository

### Étape 1: Configurer la Clé API (30 secondes)

```bash
# Ajouter la clé dans le backend/.env
cd /home/joan/Documents/AutoCode/Auto-code-v1/backend
echo "ANTHROPIC_API_KEY=sk-ant-votre-cle-ici" >> .env

# Vérifier
grep ANTHROPIC_API_KEY .env
```

### Étape 2: Tester via l'Interface Web (2 minutes)

```bash
# Si le frontend et backend ne sont pas déjà lancés :
cd /home/joan/Documents/AutoCode/Auto-code-v1

# Terminal 1 - Backend
cd backend
python main.py

# Terminal 2 - Frontend
cd frontend
npm run dev
```

Ensuite :

1. Ouvrir http://localhost:5173
2. Se connecter
3. Aller sur un repository
4. Voir la liste des tickets
5. Cliquer sur **"🚀 Développer avec Claude"** sur le premier ticket ouvert

### Étape 3: Tester via CLI (1 minute)

```bash
cd /home/joan/Documents/AutoCode/Auto-code-v1/backend

# Voir le prochain ticket
python claude_cli.py next VOTRE_REPO_ID

# Développer le prochain ticket
python claude_cli.py develop-next VOTRE_REPO_ID
```

### Étape 4: Tester le Mode Headless (1 minute)

```bash
# Configurer
export ANTHROPIC_API_KEY=sk-ant-votre-cle
export AUTOCODE_REPO_ID=votre-repo-id
export AUTOCODE_USERNAME=admin
export AUTOCODE_PASSWORD=admin
export AUTOCODE_MAX_TICKETS=1  # Tester avec 1 seul ticket

# Lancer
./scripts/headless_dev.sh
```

## 🎯 Récupérer votre Repository ID

### Méthode 1: Via l'interface

1. Ouvrir la liste des repositories
2. Ouvrir les DevTools (F12)
3. Onglet Network
4. Cliquer sur un repository
5. Regarder l'URL : `/tickets/REPOSITORY_ID`

### Méthode 2: Via l'API

```bash
# S'authentifier
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}' \
  | jq -r '.access_token')

# Lister les repos
curl -s http://localhost:8000/api/repositories \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.[] | {id, name}'
```

## 🧪 Exemple Complet de Test

```bash
#!/bin/bash
# test_claude.sh

# Configuration
export ANTHROPIC_API_KEY="sk-ant-votre-cle"
REPO_ID="votre-repo-id"

# 1. Créer un ticket de test
echo "📝 Création d'un ticket de test..."
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}' \
  | jq -r '.access_token')

TICKET_ID=$(curl -s -X POST http://localhost:8000/api/tickets \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"title\": \"Test Claude - Ajouter une fonction Hello World\",
    \"description\": \"Créer une fonction qui retourne 'Hello World' en Python\",
    \"repository_id\": \"$REPO_ID\",
    \"priority\": \"medium\",
    \"ticket_type\": \"feature\"
  }" \
  | jq -r '.id')

echo "✅ Ticket créé : $TICKET_ID"

# 2. Développer avec Claude
echo "🤖 Développement avec Claude..."
RESPONSE=$(curl -s -X POST http://localhost:8000/api/tickets/$TICKET_ID/develop-with-claude \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "ticket_id": "'"$TICKET_ID"'",
    "auto_update_status": true
  }')

# 3. Afficher le résultat
echo "📊 Résultat :"
echo "$RESPONSE" | jq '{
  ticket_title,
  model,
  usage,
  status_updated
}'

# 4. Sauvegarder la réponse
echo "$RESPONSE" | jq -r '.claude_response' > claude_test_output.md
echo "💾 Réponse complète sauvegardée dans claude_test_output.md"
```

## 📊 Exemple de Sortie Attendue

```json
{
  "ticket_id": "abc-123",
  "ticket_title": "Test Claude - Ajouter une fonction Hello World",
  "repository": "mon-repo",
  "claude_response": "# Implémentation\n\nVoici la fonction demandée...",
  "usage": {
    "input_tokens": 1234,
    "output_tokens": 5678
  },
  "model": "claude-3-5-sonnet-20241022",
  "status_updated": true
}
```

## ⚠️ Troubleshooting Rapide

### Erreur: "Claude API key not configured"

```bash
# Vérifier que la clé est dans .env
cd backend
cat .env | grep ANTHROPIC_API_KEY

# Si vide, ajouter :
echo "ANTHROPIC_API_KEY=sk-ant-votre-cle" >> .env

# Redémarrer le backend
```

### Erreur: "No open tickets in queue"

```bash
# Créer un ticket via l'interface ou :
curl -X POST http://localhost:8000/api/tickets \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test ticket",
    "description": "Pour tester Claude",
    "repository_id": "REPO_ID",
    "priority": "medium",
    "ticket_type": "feature"
  }'
```

### Erreur: "Authentication failed"

```bash
# Vérifier les credentials
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}'
```

## 🎓 Prochaines Étapes

Une fois le test réussi :

1. ✅ Créer de vrais tickets pour votre projet
2. ✅ Ajuster les prompts dans `claude_service.py` si nécessaire
3. ✅ Configurer le service systemd pour production
4. ✅ Surveiller les coûts via la console Anthropic
5. ✅ Intégrer dans votre workflow CI/CD

## 💡 Conseils

**Pour de meilleurs résultats :**

- Rédigez des descriptions de tickets claires et détaillées
- Ajoutez du contexte (architecture, patterns utilisés)
- Spécifiez les contraintes (tests, style de code)
- Vérifiez toujours le code généré avant merge

**Optimisation des coûts :**

- Utilisez `additional_context` seulement si nécessaire
- Limitez le nombre de tickets traités par jour
- Surveillez l'usage dans la console Anthropic

## 📚 Documentation Complète

- **Setup initial** : `CLAUDE_SETUP.md`
- **Mode headless** : `CLAUDE_HEADLESS.md`
- **Production** : `PRODUCTION_INSTALL.md`
- **Résumé complet** : `IMPLEMENTATION_SUMMARY.md`

---

**Besoin d'aide ?**
Consultez les logs : `tail -f backend/*.log` ou les journalctl si en production.
