# WebSocket System - Real-time Ticket Processing

## 🎯 Objectif

Système de communication temps réel entre le backend et le frontend pour suivre la progression du traitement automatique des tickets.

## Architecture

```
┌─────────────┐         WebSocket         ┌──────────────┐
│   Frontend  │ ◄─────────────────────── │   Backend    │
│  (React)    │                           │   (FastAPI)  │
└─────────────┘                           └──────────────┘
       │                                          │
       │ 1. POST /api/tickets/processing/start   │
       ├────────────────────────────────────────►│
       │                                          │
       │ 2. Ticket set to PENDING                │
       │ ◄────────────────────────────────────────┤
       │                                          │
       │ 3. Background task launched             │
       │                                          ├─────┐
       │                                          │     │ Workflow
       │ 4. WebSocket updates                     │     │ Processing
       │ ◄────────────────────────────────────────┤◄────┘
       │    - Status updates                      │
       │    - Progress (0-100%)                   │
       │    - Step information                    │
       │    - Logs                                │
       │                                          │
       │ 5. Final status (COMPLETED/FAILED)      │
       │ ◄────────────────────────────────────────┤
       │                                          │
```

## Backend Implementation

### 1. WebSocket Connection Manager

**Fichier**: `backend/src/websocket/connection_manager.py`

Gère les connexions WebSocket et broadcast des messages.

```python
from src.websocket.connection_manager import manager

# Send status update
await manager.send_status_update(
    ticket_id="123",
    status="IN_PROGRESS",
    message="Préparation du repository...",
    step="prepare_repository",
    progress=30
)

# Send log
await manager.send_log(
    ticket_id="123",
    log_level="INFO",
    log_message="Clonage du repository..."
)
```

### 2. WebSocket Endpoints

**Fichier**: `backend/src/controllers/websocket_controller.py`

#### Endpoint 1: Specific Ticket

```
ws://localhost:8000/ws/tickets/{ticket_id}
```

Reçoit les mises à jour pour un ticket spécifique.

#### Endpoint 2: All Tickets

```
ws://localhost:8000/ws/tickets
```

Reçoit les mises à jour pour tous les tickets (admin/dashboard).

### 3. Background Processing

**Fichier**: `backend/src/controllers/ticket_processing_controller.py`

```python
@router.post("/start")
async def start_ticket_processing(
    request: ProcessTicketRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    # 1. Set ticket to PENDING immediately
    ticket.status = "PENDING"
    ticket_repo.update(ticket)

    # 2. Send WebSocket update
    await manager.send_status_update(
        ticket_id,
        "PENDING",
        "Traitement en cours de démarrage...",
        progress=0
    )

    # 3. Launch background task
    background_tasks.add_task(
        _process_ticket_background,
        ticket_id,
        github_token
    )

    # 4. Return immediately
    return {
        "success": True,
        "status": "PENDING",
        "websocket_url": f"/ws/tickets/{ticket_id}"
    }
```

### 4. Workflow Integration

**Fichier**: `backend/src/services/ticket_workflow.py`

Chaque node du workflow envoie des updates WebSocket :

```python
import asyncio
from ..websocket.connection_manager import manager

def _check_iterations(self, state: TicketProcessingState):
    # Send update
    asyncio.create_task(manager.send_status_update(
        state.ticket_id,
        "IN_PROGRESS",
        "Vérification du nombre d'itérations...",
        step="check_iterations",
        progress=5
    ))

    # ... workflow logic ...
```

## Frontend Implementation

### 1. Custom Hook: useTicketProcessing

**Fichier**: `frontend/src/hooks/useTicketProcessing.ts`

```typescript
import { useTicketProcessing } from "../hooks/useTicketProcessing";

function MyComponent() {
  const {
    status, // 'PENDING' | 'IN_PROGRESS' | 'COMPLETED' | 'FAILED'
    message, // Human-readable message
    step, // Current workflow step
    progress, // 0-100
    error, // Error message if failed
    logs, // Array of log entries
    isConnected, // WebSocket connection status
  } = useTicketProcessing(ticketId);

  return (
    <div>
      <p>Status: {status}</p>
      <p>Message: {message}</p>
      {progress && <ProgressBar value={progress} />}
    </div>
  );
}
```

### 2. Component: TicketProcessingStatus

**Fichier**: `frontend/src/components/TicketProcessingStatus.tsx`

Composant React complet avec :

- Barre de progression
- Status badge (avec icône)
- Logs en temps réel
- Gestion d'erreurs

```tsx
import { TicketProcessingStatus } from "../components/TicketProcessingStatus";

function TicketPage({ ticketId }) {
  return <TicketProcessingStatus ticketId={ticketId} onComplete={() => console.log("Processing completed!")} onError={(error) => console.error("Error:", error)} />;
}
```

### 3. Start Processing (Button Handler)

```typescript
async function handleStartProcessing(ticketId: string) {
  try {
    const response = await fetch("/api/tickets/processing/start", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ ticket_id: ticketId }),
    });

    const data = await response.json();

    if (data.success) {
      // WebSocket will automatically connect via useTicketProcessing hook
      console.log("Processing started:", data.websocket_url);

      // UI will update automatically via WebSocket
    }
  } catch (error) {
    console.error("Failed to start processing:", error);
  }
}
```

## Message Types

### 1. Status Update

```json
{
  "type": "status_update",
  "ticket_id": "abc123",
  "status": "IN_PROGRESS",
  "message": "Préparation du repository...",
  "step": "prepare_repository",
  "progress": 30,
  "timestamp": "2025-01-02T10:30:00Z"
}
```

### 2. Log Entry

```json
{
  "type": "log",
  "ticket_id": "abc123",
  "level": "INFO",
  "message": "Clonage du repository https://github.com/user/repo...",
  "timestamp": "2025-01-02T10:30:05Z"
}
```

### 3. Error

```json
{
  "type": "status_update",
  "ticket_id": "abc123",
  "status": "FAILED",
  "message": "Échec de la préparation du repository",
  "error": "Repository not found",
  "timestamp": "2025-01-02T10:30:10Z"
}
```

### 4. Connection Confirmation

```json
{
  "type": "connected",
  "ticket_id": "abc123"
}
```

### 5. Heartbeat

Client → Server:

```
ping
```

Server → Client:

```json
{
  "type": "pong"
}
```

## Status Flow

```
IDLE
  │
  ▼
PENDING (ticket set immediately)
  │
  ▼
IN_PROGRESS (workflow started)
  │
  ├─► progress: 5%  - check_iterations
  ├─► progress: 20% - prepare_repository
  ├─► progress: 30% - load_conversation
  ├─► progress: 50% - call_llm
  ├─► progress: 70% - commit_changes
  ├─► progress: 85% - run_ci
  ├─► progress: 95% - handle_ci_result
  │
  ▼
┌───────────────────┐
│  CI Result?       │
└─────┬─────────────┘
      │
      ├─► COMPLETED (100%) - CI passed, awaiting validation
      ├─► FAILED - CI failed after MAX_ITERATIONS
      └─► CANCELLED - MAX_ITERATIONS exceeded
```

## Workflow Steps with Progress

| Step                 | Progress | Description                            |
| -------------------- | -------- | -------------------------------------- |
| `check_iterations`   | 5%       | Vérification du nombre d'itérations    |
| `prepare_repository` | 20%      | Clone/pull du repository               |
| `load_conversation`  | 30%      | Chargement de la conversation LLM      |
| `call_llm`           | 50%      | Appel à Claude pour génération de code |
| `commit_changes`     | 70%      | Commit des modifications Git           |
| `run_ci`             | 85%      | Exécution des tests CI/CD              |
| `handle_ci_result`   | 95%      | Traitement du résultat CI              |
| `await_validation`   | 100%     | Attente de validation humaine          |

## Error Handling

### Backend

```python
try:
    # Workflow logic
    result = await workflow.execute(ticket_id)
except Exception as e:
    logger.error(f"Workflow failed: {e}")
    await manager.send_status_update(
        ticket_id,
        "FAILED",
        "Erreur lors du traitement",
        error=str(e)
    )
```

### Frontend

```typescript
const { status, error } = useTicketProcessing(ticketId);

useEffect(() => {
  if (status === "FAILED" && error) {
    toast.error(`Échec du traitement: ${error}`);
  }
}, [status, error]);
```

## Testing

### Backend WebSocket

```bash
# Install wscat
npm install -g wscat

# Connect to ticket WebSocket
wscat -c ws://localhost:8000/ws/tickets/abc123

# You should see:
# {"type": "connected", "ticket_id": "abc123"}

# Then start processing in another terminal
curl -X POST http://localhost:8000/api/tickets/processing/start \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"ticket_id": "abc123"}'

# WebSocket will receive real-time updates
```

### Frontend

```typescript
// Test component
import { TicketProcessingStatus } from "./TicketProcessingStatus";

function TestPage() {
  const [ticketId, setTicketId] = useState("test-123");

  const handleStart = async () => {
    // Call API to start processing
    const response = await fetch("/api/tickets/processing/start", {
      method: "POST",
      body: JSON.stringify({ ticket_id: ticketId }),
    });
  };

  return (
    <div>
      <button onClick={handleStart}>Start Processing</button>
      <TicketProcessingStatus ticketId={ticketId} />
    </div>
  );
}
```

## Configuration

### CORS for WebSocket

Already configured in `main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Heartbeat

Client sends `ping` every 30 seconds to keep connection alive.

Server responds with `{"type": "pong"}`.

## Dependencies

### Backend

```txt
fastapi==0.109.0
uvicorn[standard]==0.27.0
websockets==12.0
```

### Frontend

```json
{
  "dependencies": {
    "react": "^18.2.0"
  }
}
```

No additional dependencies needed! Uses native WebSocket API.

## Next Steps

- [ ] Add reconnection logic with exponential backoff
- [ ] Implement message queue for offline support
- [ ] Add authentication for WebSocket connections
- [ ] Create admin dashboard with global WebSocket
- [ ] Add metrics (latency, message rate)
- [ ] Implement WebSocket compression

## Example: Complete Flow

1. **User clicks "Développer automatiquement"**

   ```typescript
   await fetch("/api/tickets/processing/start", {
     method: "POST",
     body: JSON.stringify({ ticket_id }),
   });
   ```

2. **Backend responds immediately**

   ```json
   {
     "success": true,
     "status": "PENDING",
     "websocket_url": "/ws/tickets/abc123"
   }
   ```

3. **Frontend connects to WebSocket**

   ```typescript
   const ws = new WebSocket("ws://localhost:8000/ws/tickets/abc123");
   ```

4. **Backend processes in background, sends updates**

   ```
   [5%]  check_iterations
   [20%] prepare_repository - "Clonage du repository..."
   [30%] load_conversation
   [50%] call_llm - "Génération du code avec Claude..."
   [70%] commit_changes
   [85%] run_ci - "Exécution des tests..."
   [95%] handle_ci_result
   [100%] await_validation - "COMPLETED"
   ```

5. **Frontend updates UI in real-time**
   - Progress bar animates
   - Status badge changes color
   - Logs appear in console
   - Final state displayed

🎉 **Résultat**: Expérience utilisateur fluide et informative !
