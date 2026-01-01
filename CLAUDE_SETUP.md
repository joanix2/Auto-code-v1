# Configuration Claude AI

## 🤖 Développement Automatique avec Claude

Ce projet intègre Claude AI d'Anthropic pour permettre le développement automatique de tickets.

## 📋 Prérequis

1. **Clé API Anthropic**
   - Créez un compte sur [console.anthropic.com](https://console.anthropic.com/)
   - Générez une clé API
   - La clé doit commencer par `sk-ant-`

## ⚙️ Configuration

### Backend

Ajoutez votre clé API dans le fichier `.env` du backend :

```bash
cd backend
echo "ANTHROPIC_API_KEY=sk-ant-votre-cle-ici" >> .env
```

Ou exportez-la comme variable d'environnement :

```bash
export ANTHROPIC_API_KEY=sk-ant-votre-cle-ici
```

### Vérification

Pour vérifier que la clé est bien configurée :

```bash
# Dans le backend
python3 -c "import os; print('✅ Clé configurée' if os.getenv('ANTHROPIC_API_KEY') else '❌ Clé manquante')"
```

## 🚀 Utilisation

### Via l'interface web

1. Accédez à la liste des tickets d'un repository
2. Le premier ticket avec le statut "Ouvert" affichera un bouton **🚀 Développer avec Claude**
3. Cliquez sur le bouton pour lancer le développement automatique
4. Claude analysera le ticket et générera une implémentation
5. Le statut du ticket passera automatiquement à "En cours"

### Via l'API REST

#### Développer un ticket spécifique

```bash
curl -X POST "http://localhost:8000/api/tickets/{ticket_id}/develop-with-claude" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "ticket_id": "ticket-uuid",
    "additional_context": "Utilise React et TypeScript",
    "auto_update_status": true
  }'
```

#### Développer le prochain ticket dans la queue

```bash
curl -X POST "http://localhost:8000/api/tickets/repository/{repository_id}/develop-next" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "additional_context": "Architecture hexagonale requise"
  }'
```

#### Récupérer le prochain ticket

```bash
curl -X GET "http://localhost:8000/api/tickets/repository/{repository_id}/next" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 📊 Modèles et Tarification

Le système utilise actuellement **Claude 3.5 Sonnet** :

- Modèle : `claude-3-5-sonnet-20241022`
- Tokens maximum : 8000 par requête
- Voir la [tarification Anthropic](https://www.anthropic.com/pricing) pour les coûts

## 🔒 Sécurité

⚠️ **Important** :

- Ne commitez JAMAIS votre clé API dans Git
- Le fichier `.env` est dans `.gitignore`
- Utilisez des variables d'environnement en production
- Renouvelez régulièrement vos clés API

## 🛠️ Workflow Automatisé

Pour automatiser complètement le développement :

```bash
# Script de développement continu
while true; do
  curl -X POST "http://localhost:8000/api/tickets/repository/REPO_ID/develop-next" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json"

  sleep 300  # Attendre 5 minutes entre chaque ticket
done
```

## 📝 Format de Réponse

Claude retourne une réponse structurée avec :

```json
{
  "ticket_id": "uuid",
  "ticket_title": "Implémenter X",
  "repository": "nom-du-repo",
  "claude_response": "# Implémentation\n\n...",
  "usage": {
    "input_tokens": 1234,
    "output_tokens": 5678
  },
  "model": "claude-3-5-sonnet-20241022",
  "status_updated": true
}
```

## 🐛 Dépannage

### Erreur: "Claude API key not configured"

- Vérifiez que `ANTHROPIC_API_KEY` est défini
- Redémarrez le backend après avoir ajouté la variable

### Erreur: "No open tickets in queue"

- Assurez-vous qu'il y a des tickets avec le statut "open"
- Vérifiez l'ordre des tickets

### Timeout

- Les requêtes ont un timeout de 5 minutes
- Pour des tickets complexes, augmentez `max_tokens` dans `claude_service.py`

## 📚 Ressources

- [Documentation Anthropic Claude](https://docs.anthropic.com/)
- [API Reference](https://docs.anthropic.com/claude/reference/getting-started-with-the-api)
- [Meilleures pratiques prompts](https://docs.anthropic.com/claude/docs/prompt-engineering)
