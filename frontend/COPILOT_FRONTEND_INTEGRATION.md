# Frontend - Intégration GitHub Copilot Development

## 🎯 Vue d'ensemble

Le frontend permet maintenant de lancer le développement automatique avec GitHub Copilot directement depuis la carte de ticket.

## 📁 Fichiers créés/modifiés

### Nouveaux fichiers

1. **`frontend/src/components/CopilotDevelopmentDialog.tsx`** (200+ lignes)
   - Modal pour configurer et lancer le développement Copilot
   - Formulaire avec instructions personnalisées et choix de branche
   - Gestion des états (loading, error, success)
   - Lien vers l'issue GitHub créée

### Fichiers modifiés

1. **`frontend/src/services/api.service.ts`**

   - Ajout méthode `startCopilotDevelopment()`
   - Ajout méthode `checkCopilotStatus()`
   - Nouveaux types TypeScript

2. **`frontend/src/components/TicketCard.tsx`**

   - Ajout bouton "Copilot Dev" (affiché uniquement si `status === "open"`)
   - Intégration du `CopilotDevelopmentDialog`
   - Prop `onDevelopmentStarted` pour callback

3. **`frontend/src/components/SortableTicketCard.tsx`**

   - Propagation de la prop `onDevelopmentStarted`

4. **`frontend/src/pages/TicketsList.tsx`**
   - Ajout callback pour rafraîchir les tickets après le démarrage

## 🎨 UI/UX

### Bouton "Copilot Dev"

**Emplacement** : Footer de la carte ticket, à gauche  
**Couleur** : Violet (purple-600)  
**Icône** : Sparkles/Étincelles  
**Condition d'affichage** : Ticket avec `status === "open"`

```tsx
<Button className="bg-purple-600 hover:bg-purple-700">
  <Sparkles /> Copilot Dev
</Button>
```

### Modal de développement

**Sections** :

1. **Header**

   - Titre : "Développement automatique avec GitHub Copilot"
   - Description : Explication courte

2. **Informations du ticket** (readonly)

   - Titre
   - Description (tronquée)
   - Type et priorité (badges)

3. **Configuration**

   - **Branche de base** : Input text (défaut: "main")
   - **Instructions personnalisées** : Textarea optionnel (4 lignes)

4. **Section informative**

   - Comment ça marche (4 étapes)
   - Style : fond bleu clair

5. **Footer**
   - Bouton "Annuler"
   - Bouton "Lancer le développement" (violet)

### États de la modal

#### Loading

```tsx
<Button disabled>
  <Loader2 className="animate-spin" />
  Démarrage en cours...
</Button>
```

#### Success

```tsx
<Alert variant="success">
  ✓ GitHub Copilot is now working on issue #42
  <Link to="https://github.com/...">Voir l'issue</Link>
</Alert>
```

#### Error

```tsx
<Alert variant="destructive">⚠️ {errorMessage}</Alert>
```

## 🔌 API Calls

### Service API

```typescript
// Types
interface CopilotDevelopmentRequest {
  ticket_id: string;
  custom_instructions?: string;
  base_branch?: string;
  model?: string;
}

interface CopilotDevelopmentResponse {
  success: boolean;
  ticket_id: string;
  issue_number?: number;
  issue_url?: string;
  message: string;
}
```

### Méthodes

```typescript
// Lancer le développement
await apiClient.startCopilotDevelopment({
  ticket_id: "uuid",
  custom_instructions: "Ajouter des tests...",
  base_branch: "main",
});

// Vérifier le statut Copilot
await apiClient.checkCopilotStatus(repositoryId);
```

## 🔄 Workflow utilisateur

### 1. Utilisateur clique sur "Copilot Dev"

```
TicketCard → setCopilotDialogOpen(true)
```

### 2. Modal s'ouvre

```
CopilotDevelopmentDialog rendu avec :
- ticket (props)
- Formulaire pré-rempli (branche: "main")
```

### 3. Utilisateur configure (optionnel)

```
- Change la branche de base
- Ajoute des instructions personnalisées
```

### 4. Utilisateur clique "Lancer"

```
handleStartDevelopment()
  → setLoading(true)
  → apiClient.startCopilotDevelopment()
  → Success: setSuccess() + setTimeout(close, 2000)
  → Error: setError()
```

### 5. Callback de succès

```
onSuccess() appelé
  → onDevelopmentStarted() dans TicketCard
  → fetchTickets() dans TicketsList
  → Modal se ferme après 2s
```

### 6. Tickets rafraîchis

```
- Liste mise à jour
- Ticket passe en status "in_progress"
- Badge GitHub visible (si issue créée)
```

## 📊 Flux de données

```
┌─────────────────────────────────────────────┐
│ User clicks "Copilot Dev"                  │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│ CopilotDevelopmentDialog opens             │
│ - Shows ticket info                        │
│ - Form: base_branch, custom_instructions   │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│ User fills form & clicks "Launch"          │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│ POST /api/copilot/start-development        │
│ {                                          │
│   ticket_id,                               │
│   custom_instructions,                     │
│   base_branch                              │
│ }                                          │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│ Backend processes request                  │
│ - Creates/assigns GitHub issue             │
│ - Updates ticket status → in_progress      │
│ - Returns issue URL & number               │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│ Success shown in modal                     │
│ - Green alert with issue link              │
│ - Auto-close after 2s                      │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│ Tickets list refreshed                     │
│ - Ticket status updated                    │
│ - GitHub badge visible                     │
└─────────────────────────────────────────────┘
```

## 🎨 Styling

### Bouton Copilot

```css
className="bg-purple-600 hover:bg-purple-700 text-white"
```

### Modal

- Max width: `max-w-2xl`
- Espacement: `space-y-4 py-4`

### Section info ticket

```css
className="rounded-lg border p-4 bg-slate-50 dark:bg-slate-900"
```

### Section "Comment ça marche"

```css
className="rounded-lg border p-4 bg-blue-50 dark:bg-blue-950 border-blue-200"
```

## 🚨 Gestion d'erreurs

### Erreurs affichées

| Erreur              | Message                                                                         |
| ------------------- | ------------------------------------------------------------------------------- |
| GitHub non connecté | "GitHub account not connected. Please connect your GitHub account in settings." |
| Copilot non activé  | "GitHub Copilot coding agent is not enabled for this repository"                |
| Repository invalide | "Invalid repository format. Expected 'owner/repo'"                              |
| Erreur réseau       | Message d'erreur générique                                                      |

### UX des erreurs

- Alert rouge en haut de la modal
- Icône `AlertCircle`
- Bouton "Lancer" reste cliquable (retry)
- Modal reste ouverte

## ✅ Validations

### Côté frontend

- ✅ `ticket_id` requis (toujours fourni via props)
- ✅ `base_branch` ne peut pas être vide (défaut: "main")
- ⚠️ `custom_instructions` optionnel (peut être vide)

### Côté backend

- ✅ Vérifie token GitHub
- ✅ Vérifie que le ticket existe
- ✅ Vérifie que le repository existe
- ✅ Vérifie que Copilot est activé

## 🎯 Améliorations futures

### Fonctionnalités

- [ ] Support du choix du modèle (Copilot Pro/Pro+)
- [ ] Support des agents personnalisés
- [ ] Preview du ticket avant envoi
- [ ] Historique des développements lancés
- [ ] Annulation d'un développement en cours

### UX

- [ ] Toast notification au lieu de modal auto-close
- [ ] Progress bar pendant le traitement
- [ ] Badge "Copilot en cours" sur le ticket
- [ ] Lien direct vers la PR (quand créée)
- [ ] Suivi temps réel via WebSocket

### Optimisations

- [ ] Cache du statut Copilot par repository
- [ ] Validation formulaire plus stricte
- [ ] Retry automatique en cas d'erreur réseau
- [ ] Offline detection

## 📖 Utilisation

### Pour l'utilisateur final

1. Ouvrir la liste des tickets
2. Trouver un ticket avec statut "open"
3. Cliquer sur le bouton violet "Copilot Dev"
4. (Optionnel) Ajouter des instructions personnalisées
5. (Optionnel) Changer la branche de base
6. Cliquer sur "Lancer le développement"
7. Attendre la confirmation (2 secondes)
8. Copilot travaille en arrière-plan
9. Notification GitHub quand la PR est prête

### Pour le développeur

```tsx
// Intégrer dans une nouvelle page
import { CopilotDevelopmentDialog } from "@/components/CopilotDevelopmentDialog";

<CopilotDevelopmentDialog
  open={dialogOpen}
  onOpenChange={setDialogOpen}
  ticket={selectedTicket}
  onSuccess={() => {
    // Rafraîchir les données
    refetchTickets();
  }}
/>;
```

---

**Status** : ✅ Intégration complète frontend-backend opérationnelle
