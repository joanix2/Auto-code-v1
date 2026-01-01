# 🤖 Système de Développement Automatique avec Claude

## Vue d'ensemble

Ce système permet de développer automatiquement des tickets en utilisant Claude AI d'Anthropic. Il fonctionne de manière **headless** (sans interface graphique) et peut être exécuté sur un serveur.

## Architecture

```
┌─────────────────┐
│   Frontend      │  → Interface web (optionnelle)
│   - Bouton UI   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Backend API   │  → FastAPI REST API
│   - Endpoints   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Claude Service  │  → Service d'intégration
│   - Prompts     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Claude API     │  → Anthropic API
│  (anthropic.com)│
└─────────────────┘
```

## Composants

### 1. Backend Service (`claude_service.py`)

**Responsabilités:**

- Génération de prompts structurés
- Communication avec l'API Claude
- Gestion des tokens et timeouts

**Méthodes principales:**

```python
# Générer un prompt pour un ticket
generate_ticket_prompt(title, description, type, priority, repo)

# Envoyer un message à Claude
send_message(prompt, system_message)

# Développer un ticket
develop_ticket(ticket_title, ticket_description, ...)
```

### 2. API Endpoints (`ticket_controller.py`)

**Endpoints disponibles:**

#### `GET /tickets/repository/{id}/next`

Récupère le prochain ticket dans la queue

```json
{
  "ticket": {...},
  "queue_position": 1,
  "total_open_tickets": 5
}
```

#### `POST /tickets/{id}/develop-with-claude`

Développe un ticket spécifique

```json
{
  "ticket_id": "uuid",
  "additional_context": "optional",
  "auto_update_status": true
}
```

#### `POST /tickets/repository/{id}/develop-next`

Développe automatiquement le prochain ticket

```json
{
  "additional_context": "optional"
}
```

### 3. Frontend Integration

**Composants modifiés:**

- `TicketCard.tsx` - Bouton "Développer avec Claude"
- `SortableTicketCard.tsx` - Props pour identification queue
- `TicketsList.tsx` - Gestion du développement

**Service frontend:**

```typescript
ClaudeService.developTicket(ticketId, context);
ClaudeService.developNextTicket(repositoryId, context);
ClaudeService.getNextTicket(repositoryId);
```

### 4. CLI Tool (`claude_cli.py`)

**Usage:**

```bash
# Afficher le prochain ticket
python backend/claude_cli.py next <repo_id>

# Développer le prochain ticket
python backend/claude_cli.py develop-next <repo_id>

# Développer un ticket spécifique
python backend/claude_cli.py develop <ticket_id>
```

## Utilisation Headless (Serveur)

### Setup initial

1. **Installer les dépendances:**

```bash
cd backend
pip install -r requirements.txt
```

2. **Configurer la clé API:**

```bash
export ANTHROPIC_API_KEY=sk-ant-your-key-here
```

3. **Démarrer le backend:**

```bash
cd backend
python main.py
# ou avec uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Scénarios d'utilisation

#### Scénario 1: Développement manuel via API

```bash
# 1. Authentification
TOKEN=$(curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}' \
  | jq -r '.access_token')

# 2. Voir le prochain ticket
curl -X GET "http://localhost:8000/api/tickets/repository/REPO_ID/next" \
  -H "Authorization: Bearer $TOKEN"

# 3. Développer le prochain ticket
curl -X POST "http://localhost:8000/api/tickets/repository/REPO_ID/develop-next" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  | jq '.claude_response'
```

#### Scénario 2: Développement automatisé (CI/CD)

```bash
#!/bin/bash
# continuous_development.sh

REPO_ID="your-repository-id"
TOKEN="your-auth-token"
API_URL="http://localhost:8000/api"

while true; do
  echo "🔍 Checking for next ticket..."

  RESPONSE=$(curl -s -X POST "$API_URL/tickets/repository/$REPO_ID/develop-next" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json")

  if [ $? -eq 0 ]; then
    echo "✅ Ticket developed successfully"
    echo "$RESPONSE" | jq '.claude_response' > "implementation_$(date +%s).md"
  else
    echo "⚠️ No tickets or error occurred"
    break
  fi

  # Attendre avant le prochain ticket
  sleep 300  # 5 minutes
done
```

#### Scénario 3: CLI direct

```bash
# Setup
export ANTHROPIC_API_KEY=sk-ant-...
cd backend

# Développement continu
while true; do
  python claude_cli.py develop-next YOUR_REPO_ID
  if [ $? -ne 0 ]; then
    echo "No more tickets or error"
    break
  fi
  sleep 60
done
```

#### Scénario 4: Cron job

```bash
# Ajouter au crontab
# Développer un ticket toutes les heures
0 * * * * cd /path/to/Auto-code-v1/backend && \
  export ANTHROPIC_API_KEY=sk-ant-... && \
  python claude_cli.py develop-next REPO_ID >> /var/log/autocode.log 2>&1
```

## Workflow Complet

1. **Création du ticket** (manuel ou automatique)

   - Frontend ou API POST `/tickets`
   - Ticket créé avec status "open"
   - Order calculé automatiquement

2. **File d'attente**

   - Tickets triés par `order` (ASC)
   - Premier ticket "open" = prochain à développer

3. **Développement automatique**

   - Appel API ou CLI
   - Génération du prompt structuré
   - Appel à Claude API
   - Status → "in_progress"

4. **Récupération de la réponse**

   - Code généré par Claude
   - Sauvegarde locale ou affichage
   - Tokens utilisés tracés

5. **Post-traitement** (manuel)
   - Review du code
   - Tests
   - Commit
   - Status → "closed"

## Configuration Avancée

### Variables d'environnement

```bash
# Requis
ANTHROPIC_API_KEY=sk-ant-...

# Optionnel (dans claude_service.py)
CLAUDE_MODEL=claude-3-5-sonnet-20241022
CLAUDE_MAX_TOKENS=8000
CLAUDE_TIMEOUT=300
```

### Personnalisation du prompt

Modifiez `backend/src/services/claude_service.py`:

```python
def generate_ticket_prompt(self, ...):
    prompt = f"""
    # Votre template personnalisé

    ## Context spécifique à votre projet
    - Architecture: Clean Architecture
    - Tests: Jest + React Testing Library
    - Style: Prettier + ESLint

    {ticket_title}
    {ticket_description}
    """
    return prompt
```

## Monitoring et Logs

### Backend logs

```bash
# Dans main.py, les logs sont automatiques
INFO:     Started server process
INFO:     Waiting for application startup.
```

### Tracking des tokens

```python
# Chaque réponse contient:
{
  "usage": {
    "input_tokens": 1234,
    "output_tokens": 5678
  }
}
```

### Métriques à surveiller

- Nombre de tickets développés/jour
- Tokens consommés
- Taux de succès
- Temps de réponse moyen

## Sécurité

### Best Practices

1. **Clé API**

   - Stockée en variable d'environnement
   - Jamais committée
   - Rotation régulière

2. **Authentication**

   - JWT tokens pour API
   - Expiration configurée
   - Refresh tokens

3. **Rate Limiting**

   - Implémenter dans FastAPI si nécessaire
   - Limiter les appels Claude

4. **Validation**
   - Valider les tickets avant envoi
   - Sanitize user input
   - Vérifier les permissions

## Coûts et Limites

### Claude 3.5 Sonnet Pricing (2024)

- Input: ~$3 / million tokens
- Output: ~$15 / million tokens

### Estimation

Un ticket moyen (2000 tokens input, 6000 tokens output):

- Coût: ~$0.096 par ticket
- 10 tickets/jour: ~$1/jour
- 300 tickets/mois: ~$30/mois

### Limites

- Rate limits Anthropic: vérifier console
- Timeout: 5 minutes par requête
- Max tokens: 8000 par réponse

## Troubleshooting

### Problème: "Claude API key not configured"

```bash
# Vérifier la variable
echo $ANTHROPIC_API_KEY

# Si vide, l'exporter
export ANTHROPIC_API_KEY=sk-ant-...

# Redémarrer le backend
```

### Problème: "No open tickets in queue"

```python
# Créer un ticket de test
curl -X POST "http://localhost:8000/api/tickets" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test ticket",
    "description": "For testing Claude",
    "repository_id": "REPO_ID",
    "priority": "medium",
    "ticket_type": "feature"
  }'
```

### Problème: Timeout

```python
# Augmenter le timeout dans claude_service.py
async with httpx.AsyncClient(timeout=600.0) as client:  # 10 min
```

## Roadmap

- [ ] Intégration GitHub Actions
- [ ] Support multi-modèles (GPT-4, Gemini)
- [ ] Validation automatique du code généré
- [ ] Tests automatiques post-génération
- [ ] Commit automatique
- [ ] Webhook sur completion
- [ ] Dashboard de monitoring
- [ ] Cache des prompts similaires

## Support

Pour toute question:

1. Lire `CLAUDE_SETUP.md`
2. Vérifier les logs backend
3. Consulter la [documentation Anthropic](https://docs.anthropic.com/)
