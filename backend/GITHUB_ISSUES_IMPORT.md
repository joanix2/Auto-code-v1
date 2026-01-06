# Import GitHub Issues - Guide d'utilisation

## Vue d'ensemble

Le système permet maintenant d'importer les issues GitHub existantes comme tickets dans l'application. Cela permet une synchronisation bidirectionnelle entre GitHub et AutoCode.

## Endpoints disponibles

### 1. Lister les issues GitHub avec statut d'import

```http
GET /api/github-issues/sync/{repository_id}?state=open
```

**Paramètres :**

- `repository_id` (path) : ID du repository
- `state` (query, optionnel) : État des issues (`open`, `closed`, `all`). Défaut: `open`

**Réponse :**

```json
{
  "success": true,
  "repository_id": "repo-uuid",
  "repository_name": "owner/repo",
  "issues": [
    {
      "issue": {
        "number": 42,
        "title": "Add authentication",
        "body": "We need to add user authentication...",
        "state": "open",
        "html_url": "https://github.com/owner/repo/issues/42",
        "labels": ["enhancement", "priority: high"],
        "created_at": "2026-01-06T10:00:00Z",
        "updated_at": "2026-01-06T12:00:00Z",
        "user": {
          "login": "username",
          "avatar_url": "https://..."
        }
      },
      "is_imported": false,
      "ticket_id": null
    },
    {
      "issue": {
        "number": 41,
        "title": "Fix login bug",
        "body": "Login fails with...",
        "state": "open",
        "html_url": "https://github.com/owner/repo/issues/41",
        "labels": ["bug", "priority: critical"],
        "created_at": "2026-01-05T15:00:00Z"
      },
      "is_imported": true,
      "ticket_id": "ticket-uuid"
    }
  ],
  "total": 2,
  "imported": 1,
  "not_imported": 1
}
```

### 2. Importer une issue spécifique

```http
POST /api/github-issues/import/{repository_id}/{issue_number}
```

**Paramètres :**

- `repository_id` (path) : ID du repository
- `issue_number` (path) : Numéro de l'issue GitHub

**Réponse :**

```json
{
  "success": true,
  "ticket_id": "new-ticket-uuid",
  "issue_number": 42,
  "issue_url": "https://github.com/owner/repo/issues/42",
  "message": "GitHub issue #42 imported successfully"
}
```

**Erreurs possibles :**

- `400` : Issue déjà importée
- `404` : Repository ou issue non trouvée
- `401` : Compte GitHub non connecté

### 3. Importer toutes les issues

```http
POST /api/github-issues/import-all/{repository_id}?state=open
```

**Paramètres :**

- `repository_id` (path) : ID du repository
- `state` (query, optionnel) : État des issues à importer. Défaut: `open`

**Réponse :**

```json
{
  "success": true,
  "repository_id": "repo-uuid",
  "repository_name": "owner/repo",
  "summary": {
    "total_issues": 10,
    "imported": 7,
    "skipped": 2,
    "errors": 1
  },
  "imported_tickets": [
    {
      "issue_number": 42,
      "ticket_id": "ticket-uuid-1",
      "title": "Add authentication"
    },
    {
      "issue_number": 43,
      "ticket_id": "ticket-uuid-2",
      "title": "Fix bug"
    }
  ],
  "skipped_issues": [
    {
      "issue_number": 41,
      "ticket_id": "existing-ticket-uuid",
      "reason": "Already imported"
    }
  ],
  "errors": [
    {
      "issue_number": 44,
      "error": "Invalid data"
    }
  ]
}
```

## Mapping GitHub → Ticket

### Type de ticket (depuis les labels)

| Label GitHub    | Type Ticket        |
| --------------- | ------------------ |
| `bug`           | `bugfix`           |
| `enhancement`   | `feature`          |
| `feature`       | `feature`          |
| `refactor`      | `refactor`         |
| `documentation` | `documentation`    |
| Aucun label     | `feature` (défaut) |

### Priorité (depuis les labels)

| Label GitHub                       | Priorité          |
| ---------------------------------- | ----------------- |
| `priority: critical` ou `critical` | `critical`        |
| `priority: high` ou `high`         | `high`            |
| `priority: medium` ou `medium`     | `medium`          |
| `priority: low` ou `low`           | `low`             |
| Aucun label                        | `medium` (défaut) |

### Statut

| État GitHub | Statut Ticket |
| ----------- | ------------- |
| `open`      | `open`        |
| `closed`    | `closed`      |

### Nettoyage de la description

Si l'issue a été créée par AutoCode, la section de métadonnées est automatiquement supprimée lors de l'import pour éviter la duplication.

## Utilisation depuis le frontend

### 1. Afficher un bouton "Importer des issues GitHub"

```typescript
// Dans la page de liste des tickets
const syncGitHubIssues = async () => {
  const response = await fetch(`/api/github-issues/sync/${repositoryId}?state=open`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  const data = await response.json();

  // Afficher une modal avec la liste des issues
  setIssues(data.issues);
};
```

### 2. Importer une issue sélectionnée

```typescript
const importIssue = async (issueNumber: number) => {
  const response = await fetch(`/api/github-issues/import/${repositoryId}/${issueNumber}`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (response.ok) {
    // Rafraîchir la liste des tickets
    fetchTickets();
  }
};
```

### 3. Importer toutes les issues non importées

```typescript
const importAllIssues = async () => {
  const response = await fetch(`/api/github-issues/import-all/${repositoryId}?state=open`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  const result = await response.json();
  console.log(`Imported ${result.summary.imported} issues`);

  // Rafraîchir la liste
  fetchTickets();
};
```

## Exemple de flux utilisateur

1. **Utilisateur crée une issue sur GitHub** (manuellement ou via CLI)

2. **Utilisateur ouvre AutoCode**

   - Voit ses tickets existants
   - Clique sur "Synchroniser avec GitHub"

3. **Application affiche une modal**

   - Liste toutes les issues GitHub
   - Indique lesquelles sont déjà importées
   - Permet de sélectionner les issues à importer

4. **Utilisateur sélectionne les issues** et clique "Importer"

5. **Application crée les tickets**

   - Mappe automatiquement les labels aux types/priorités
   - Lie chaque ticket à son issue GitHub
   - Rafraîchit la liste

6. **Utilisateur voit maintenant les issues GitHub comme tickets**
   - Peut lancer le développement automatique
   - Les changements sont synchronisés vers GitHub

## Suggestions d'implémentation UI

### Modal de synchronisation

```tsx
<Dialog>
  <DialogTitle>
    Synchroniser avec GitHub
    <Badge>{notImportedCount} nouvelles issues</Badge>
  </DialogTitle>

  <DialogContent>
    {issues.map((item) => (
      <Card key={item.issue.number}>
        <CardHeader>
          <h3>
            #{item.issue.number}: {item.issue.title}
          </h3>
          {item.is_imported ? <Badge variant="success">Déjà importé</Badge> : <Button onClick={() => importIssue(item.issue.number)}>Importer</Button>}
        </CardHeader>
        <CardContent>
          <p>{item.issue.body.substring(0, 200)}...</p>
          <div>
            {item.issue.labels.map((label) => (
              <Badge key={label}>{label}</Badge>
            ))}
          </div>
        </CardContent>
      </Card>
    ))}
  </DialogContent>

  <DialogFooter>
    <Button variant="secondary" onClick={onClose}>
      Fermer
    </Button>
    <Button onClick={importAllNotImported}>Importer tout ({notImportedCount})</Button>
  </DialogFooter>
</Dialog>
```

### Badge dans la liste des tickets

```tsx
{
  ticket.github_issue_number && (
    <a href={ticket.github_issue_url} target="_blank" className="flex items-center gap-1">
      <GitHubIcon />#{ticket.github_issue_number}
    </a>
  );
}
```

## Synchronisation continue

Pour une synchronisation automatique périodique :

```typescript
// Vérifier les nouvelles issues toutes les 5 minutes
useEffect(() => {
  const interval = setInterval(async () => {
    const response = await fetch(`/api/github-issues/sync/${repositoryId}?state=open`);
    const data = await response.json();

    if (data.not_imported > 0) {
      // Afficher une notification
      showNotification(`${data.not_imported} nouvelle(s) issue(s) GitHub disponible(s)`);
    }
  }, 5 * 60 * 1000); // 5 minutes

  return () => clearInterval(interval);
}, [repositoryId]);
```

## Limitations

- Les Pull Requests ne sont pas importées (elles sont filtrées automatiquement)
- Seuls les utilisateurs avec un token GitHub connecté peuvent importer
- L'import ne crée pas automatiquement les messages/commentaires de l'issue
- Les assignés GitHub ne sont pas mappés (tous les tickets sont créés par l'utilisateur qui importe)

## Améliorations futures

- [ ] Import des commentaires de l'issue comme messages
- [ ] Synchronisation automatique périodique (webhook GitHub)
- [ ] Import des Pull Requests comme tickets spéciaux
- [ ] Mapping des assignés GitHub vers les utilisateurs AutoCode
- [ ] Import des milestones GitHub
- [ ] Filtrage par labels lors de l'import
- [ ] Preview du ticket avant import
