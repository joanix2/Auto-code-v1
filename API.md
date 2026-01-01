# API Documentation

## Endpoints

### Health Check

**GET** `/health`

Check the health status of the API and connected services.

**Response:**
```json
{
  "status": "healthy",
  "services": {
    "api": "healthy",
    "github": "healthy",
    "rabbitmq": "healthy"
  }
}
```

---

### Create Ticket

**POST** `/tickets`

Create a new development ticket. This will:
1. Create a GitHub issue
2. Queue the task in RabbitMQ
3. Trigger an AI agent to process the task

**Request Body:**
```json
{
  "title": "Add user authentication",
  "description": "Implement JWT-based authentication with login and logout endpoints",
  "labels": ["feature", "security"],
  "priority": "high"
}
```

**Response:**
```json
{
  "ticket_id": 123,
  "ticket_url": "https://github.com/owner/repo/issues/123",
  "title": "Add user authentication",
  "status": "queued",
  "message": "Ticket created and queued for processing"
}
```

**Status Codes:**
- `201` - Ticket created successfully
- `500` - Failed to create ticket or queue task

---

### Get Ticket

**GET** `/tickets/{ticket_id}`

Get information about a specific ticket.

**Response:**
```json
{
  "issue_number": 123,
  "title": "Add user authentication",
  "body": "Implement JWT-based authentication...",
  "state": "open",
  "labels": ["feature", "security", "auto-code"],
  "url": "https://github.com/owner/repo/issues/123"
}
```

**Status Codes:**
- `200` - Success
- `404` - Ticket not found
- `500` - Server error

---

## Error Responses

All error responses follow this format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

## Rate Limits

The API respects GitHub's rate limits. Check your current rate limit status:

```bash
curl https://api.github.com/rate_limit \
  -H "Authorization: token YOUR_GITHUB_TOKEN"
```

## Authentication

Currently, the API does not require authentication for creating tickets. In production, you should implement authentication mechanisms such as:

- API Keys
- OAuth 2.0
- JWT tokens

## Examples

### cURL

Create a ticket:
```bash
curl -X POST http://localhost:8000/tickets \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Fix login bug",
    "description": "Users cannot login with special characters in password",
    "priority": "high"
  }'
```

Get ticket status:
```bash
curl http://localhost:8000/tickets/123
```

### JavaScript (Axios)

```javascript
import axios from 'axios';

const API_URL = 'http://localhost:8000';

async function createTicket() {
  try {
    const response = await axios.post(`${API_URL}/tickets`, {
      title: 'Add dark mode',
      description: 'Implement dark mode toggle in settings',
      priority: 'medium',
      labels: ['enhancement', 'ui']
    });
    console.log('Ticket created:', response.data);
  } catch (error) {
    console.error('Error:', error.response.data);
  }
}
```

### Python

```python
import requests

API_URL = 'http://localhost:8000'

def create_ticket():
    payload = {
        'title': 'Optimize database queries',
        'description': 'Add indexes and optimize slow queries',
        'priority': 'high',
        'labels': ['performance']
    }
    
    response = requests.post(f'{API_URL}/tickets', json=payload)
    
    if response.status_code == 201:
        print('Ticket created:', response.json())
    else:
        print('Error:', response.json())
```

## Interactive Documentation

The API provides interactive Swagger documentation at:

**http://localhost:8000/docs**

You can test all endpoints directly from your browser using this interface.
