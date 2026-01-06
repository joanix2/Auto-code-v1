# WebSocket Error Handling - Documentation

## Vue d'ensemble

Le système affiche maintenant les erreurs de développement automatique en temps réel via WebSocket dans le frontend.

## Architecture

### Backend

#### 1. **Workflow (`simple_ticket_workflow.py`)**

Les erreurs sont capturées et envoyées via WebSocket à chaque étape critique :

```python
# Exemple d'envoi d'erreur
await safe_ws_update(
    ticket_id,
    "cancelled",  # Statut
    f"Erreur lors de la génération du code: {str(e)}",  # Message
    error=str(e),  # Détails de l'erreur
    progress=30  # Progression (0-100)
)
```

**Étapes qui envoient des erreurs :**

1. **Préparation du dépôt** (`_prepare_repository`)

   - Repository non trouvé
   - Échec du clone/pull
   - Erreur générale de préparation

2. **Génération de code** (`_call_llm`)

   - Agent non initialisé (ANTHROPIC_API_KEY manquante)
   - Échec de l'agent Claude
   - Erreur lors de l'appel à l'agent

3. **Commit des changements** (`_commit_changes`)

   - Échec du commit Git
   - Erreur lors du push

4. **Workflow global** (`execute`)
   - Toute exception non capturée

#### 2. **WebSocket Manager (`connection_manager.py`)**

```python
async def send_status_update(
    self,
    ticket_id: str,
    status: str,
    message: str,
    step: str = None,
    progress: int = None,
    error: str = None,  # ✅ Champ error
    data: dict = None
):
    """Envoie une mise à jour de statut via WebSocket"""
```

Le manager transmet le champ `error` dans le message JSON :

```json
{
  "type": "status_update",
  "ticket_id": "abc123",
  "status": "cancelled",
  "message": "Erreur lors de la génération du code: ...",
  "error": "Agent not initialized. Please set ANTHROPIC_API_KEY environment variable.",
  "progress": 30,
  "timestamp": "2026-01-06T12:34:56"
}
```

### Frontend

#### 1. **Hook WebSocket (`useTicketProcessing.ts`)**

Le hook expose le champ `error` :

```typescript
export function useTicketProcessing(ticketId: string | null) {
  const [status, setStatus] = useState<ProcessingStatus>({
    status: "idle",
    message: "En attente...",
  });

  // ...

  return {
    status: status.status,
    message: status.message,
    step: status.step,
    progress: status.progress,
    error: status.error, // ✅ Exposé
    data: status.data,
    logs,
    isConnected,
    connect,
    disconnect,
  };
}
```

#### 2. **Page des tickets (`TicketsList.tsx`)**

Récupère et affiche l'erreur :

```typescript
// Récupération de l'erreur WebSocket
const {
  status: wsStatus,
  message: wsMessage,
  progress: wsProgress,
  error: wsError, // ✅ Récupéré
  isConnected,
} = useTicketProcessing(processingTicketId);

// Affichage dans le state local
useEffect(() => {
  if (wsError) {
    console.error("[TicketsList] WebSocket error received:", wsError);
    setError(`Erreur de développement: ${wsError}`);
  }
}, [wsError]);
```

Affichage dans l'UI :

```tsx
{
  /* Error Alert */
}
{
  error && (
    <Alert variant="destructive" className="mb-6">
      <AlertDescription>{error}</AlertDescription>
    </Alert>
  );
}
```

#### 3. **Composant de progression (`TicketProcessingStatus.tsx`)**

Affiche également l'erreur de manière détaillée :

```tsx
{
  /* Error Message */
}
{
  error && (
    <div className="bg-red-50 border border-red-200 rounded-md p-3">
      <p className="text-sm text-red-800">
        <span className="font-semibold">Erreur:</span> {error}
      </p>
    </div>
  );
}
```

## Flux de données

```
1. Exception dans workflow
   ↓
2. Capture dans try/except
   ↓
3. await safe_ws_update(ticket_id, "cancelled", message, error=str(e))
   ↓
4. ConnectionManager.send_status_update(error=...)
   ↓
5. JSON envoyé via WebSocket
   ↓
6. useTicketProcessing reçoit le message
   ↓
7. setStatus({ ..., error: data.error })
   ↓
8. Hook expose error
   ↓
9. Composant affiche l'erreur (Alert rouge)
```

## Types d'erreurs affichées

### Erreurs d'infrastructure

- Repository non trouvé
- Échec du clone/pull Git
- Problèmes de connexion WebSocket

### Erreurs de l'agent

- `ANTHROPIC_API_KEY` manquante ou invalide
- Échec de l'analyse du ticket par Claude
- Erreur lors de la génération de code
- Timeout de l'agent

### Erreurs Git

- Échec du commit
- Échec du push
- Conflits de merge

### Erreurs CI/CD

- Tests échoués
- Build échoué
- Timeout des tests

## Tests

### Test manuel

1. Supprimer la variable `ANTHROPIC_API_KEY` :

   ```bash
   unset ANTHROPIC_API_KEY
   # ou dans .env : # ANTHROPIC_API_KEY=...
   ```

2. Lancer le développement automatique d'un ticket

3. Vérifier que l'erreur s'affiche :
   - Dans les logs backend
   - Via WebSocket dans la console browser
   - Dans l'Alert rouge en haut de la page
   - Dans le composant TicketProcessingStatus (si utilisé)

### Erreur attendue

```
Erreur de développement: Agent not initialized. Please set ANTHROPIC_API_KEY environment variable.
```

## Améliorations futures

- [ ] Catégoriser les erreurs (infrastructure, agent, git, ci)
- [ ] Ajouter des actions de récupération (retry, skip, cancel)
- [ ] Historique des erreurs par ticket
- [ ] Notifications push pour les erreurs critiques
- [ ] Logs détaillés téléchargeables
- [ ] Intégration avec un système de monitoring (Sentry, etc.)

## Références

- `backend/src/services/workflows/simple_ticket_workflow.py` - Workflow principal
- `backend/src/websocket/connection_manager.py` - Gestionnaire WebSocket
- `frontend/src/hooks/useTicketProcessing.ts` - Hook WebSocket
- `frontend/src/pages/TicketsList.tsx` - Page principale
- `frontend/src/components/TicketProcessingStatus.tsx` - Composant de progression
