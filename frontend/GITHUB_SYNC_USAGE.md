# Guide d'utilisation - Synchronisation GitHub Issues

## 🎯 Fonctionnalité

L'intégration GitHub permet d'importer automatiquement vos issues GitHub comme tickets AutoCode, créant ainsi une synchronisation bidirectionnelle entre GitHub et votre application.

## 📍 Accès à la fonctionnalité

### Depuis la page des tickets

1. Naviguez vers la liste des tickets d'un repository
2. Cliquez sur le bouton **"Sync GitHub"** dans la barre de recherche
3. Une modal s'ouvre avec la liste des issues GitHub

## 🖥️ Interface utilisateur

### Modal de synchronisation

La modal affiche trois onglets :

#### 1. **À importer** (par défaut)

- Liste des issues GitHub **non encore importées**
- Compteur visible : `À importer (X)`
- Chaque issue affiche :
  - Numéro et titre de l'issue
  - Lien direct vers GitHub
  - Auteur et date de création
  - Labels (type, priorité, custom)
  - Description (preview)
  - Bouton **"Importer"**

#### 2. **Déjà importées**

- Liste des issues **déjà importées** comme tickets
- Badge vert **"Importée"** sur chaque issue
- Compteur : `Déjà importées (X)`

#### 3. **Toutes**

- Vue complète de toutes les issues (importées + non importées)
- Compteur total : `Toutes (X)`

## ✨ Fonctionnalités

### Import individuel

1. Dans l'onglet "À importer", trouvez l'issue souhaitée
2. Cliquez sur le bouton **"Importer"** à droite de l'issue
3. Le bouton affiche "Import..." pendant le traitement
4. Un message de succès s'affiche : _"Issue #X importée avec succès !"_
5. L'issue passe automatiquement dans l'onglet "Déjà importées"
6. La liste des tickets est rafraîchie automatiquement

### Import en masse

1. Dans le footer de la modal, un bouton **"Importer tout (X)"** est visible
2. X = nombre d'issues non importées
3. Cliquez pour importer toutes les issues ouvertes en une fois
4. Un résumé s'affiche :
   ```
   Import terminé: 7 importées, 2 ignorées, 1 erreurs
   ```
5. Toutes les issues sont créées comme tickets

### Mapping automatique

Les issues GitHub sont automatiquement converties en tickets avec :

#### Types (depuis les labels)

- `bug` → Ticket type **"bugfix"**
- `enhancement` ou `feature` → Ticket type **"feature"**
- `documentation` → Ticket type **"documentation"**
- `refactor` → Ticket type **"refactor"**
- Aucun label → **"feature"** par défaut

#### Priorités (depuis les labels)

- `priority: critical` ou `critical` → **Critical**
- `priority: high` ou `high` → **High**
- `priority: medium` ou `medium` → **Medium**
- `priority: low` ou `low` → **Low**
- Aucun label → **Medium** par défaut

#### Statuts

- Issue `open` → Ticket **"open"**
- Issue `closed` → Ticket **"closed"**

### Indicateur visuel sur les tickets

Les tickets importés depuis GitHub affichent un **badge GitHub** :

```
┌─────────────────────────────────────┐
│ Mon super ticket                    │
│ 🔗 Issue #42                        │  ← Lien cliquable vers GitHub
│ ...                                 │
└─────────────────────────────────────┘
```

- Icône GitHub visible
- Numéro de l'issue cliquable
- Ouvre l'issue GitHub dans un nouvel onglet

## 🔄 Workflow typique

### Scénario 1 : Importer des issues existantes

```
1. User crée des issues sur GitHub (manuellement ou via CLI)
   └─ Issues #1, #2, #3 créées

2. User ouvre AutoCode → Page Tickets
   └─ Clique "Sync GitHub"

3. Modal affiche les 3 issues dans "À importer"
   └─ User clique "Importer tout (3)"

4. AutoCode crée 3 tickets automatiquement
   └─ Mapping type/priorité depuis les labels
   └─ Liens GitHub issue ↔ Ticket

5. User peut maintenant lancer le développement
   └─ Les changements seront notifiés sur GitHub
```

### Scénario 2 : Synchronisation régulière

```
1. User a déjà importé 10 issues (onglet "Déjà importées")

2. Une nouvelle issue #11 est créée sur GitHub

3. User clique "Sync GitHub" pour vérifier
   └─ Onglet "À importer" affiche : (1)
   └─ Issue #11 visible

4. User importe juste cette issue
   └─ Reste synchronisé avec GitHub
```

## 🎨 UI Components

### Badges de priorité

Les priorités sont affichées avec des couleurs :

- 🔴 **Critical / High** : Rouge (destructive)
- 🟡 **Medium** : Gris (default)
- 🟢 **Low** : Gris clair (secondary)

### Badges de type

- `bug`, `enhancement`, `feature`, etc.
- Style outlined

### Labels personnalisés

Tous les autres labels GitHub sont affichés en gris (secondary)

## 🚨 Gestion d'erreurs

### Erreurs affichées dans la modal

- **Compte GitHub non connecté** : Message d'erreur rouge

  ```
  ⚠️ Vous devez connecter votre compte GitHub
  ```

- **Repository non trouvé** : Alert destructive

  ```
  ⚠️ Repository non trouvé
  ```

- **Issue déjà importée** : Ignore automatiquement

  - Dans l'import masse : compteur "skipped"

- **Erreur API** : Message d'erreur détaillé
  ```
  ⚠️ Erreur lors de l'import de l'issue #42
  ```

### Messages de succès

Alert verte avec icône ✓ :

```
✓ Issue #42 importée avec succès !
```

## 💡 Astuces

### Filtrage des issues

- Par défaut, seules les issues **ouvertes** sont affichées
- Les Pull Requests sont automatiquement **filtrées** (non affichées)

### Rafraîchissement automatique

- Après import, la liste des tickets est **automatiquement rafraîchie**
- Pas besoin de recharger la page

### Indicateur de chargement

- Spinner lors du chargement initial
- Bouton "Import..." pendant l'import
- Interface bloquée pendant l'import en masse

## 🔧 Paramètres techniques

### Endpoints utilisés

```typescript
// Liste des issues
GET /api/github-issues/sync/{repository_id}?state=all

// Import individuel
POST /api/github-issues/import/{repository_id}/{issue_number}

// Import masse
POST /api/github-issues/import-all/{repository_id}?state=open
```

### Types TypeScript

```typescript
interface GitHubIssue {
  number: number;
  title: string;
  body: string;
  state: "open" | "closed";
  html_url: string;
  labels: string[];
  created_at: string;
  updated_at: string;
  user: { login: string; avatar_url: string };
}

interface GitHubIssueWithImportStatus {
  issue: GitHubIssue;
  is_imported: boolean;
  ticket_id: string | null;
}
```

## 📊 Statistiques

Le footer de la modal affiche :

- **Total d'issues** dans le repository
- **Nombre d'issues importées**
- **Nombre d'issues à importer**

Exemple :

```
┌────────────────────────────────────────┐
│                                        │
│  Footer:  "5 issues à importer"       │
│  [Fermer]  [Importer tout (5)]        │
└────────────────────────────────────────┘
```

## 🎯 Prochaines améliorations

- [ ] Synchronisation automatique périodique (webhook)
- [ ] Import des commentaires GitHub
- [ ] Export de tickets vers GitHub
- [ ] Filtrage par labels GitHub
- [ ] Preview du ticket avant import
- [ ] Synchronisation bidirectionnelle des commentaires

---

**Note** : Assurez-vous d'avoir connecté votre compte GitHub dans les paramètres de profil avant d'utiliser cette fonctionnalité.
