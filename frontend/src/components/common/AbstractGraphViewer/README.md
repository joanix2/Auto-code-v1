# GraphViewer - Architecture

Composant de visualisation de graphes avec D3.js et React.

## 📁 Structure

```
GraphViewer/
├── GraphViewer.tsx          # Composant principal (orchestration)
├── index.ts                 # Exports publics
├── types.ts                 # Types TypeScript
│
├── behaviors/               # Comportements D3 (drag, etc.)
│   ├── dragBehavior.ts      # Drag avec mode lien
│   └── index.ts
│
├── components/              # Composants UI React
│   ├── CreateNodeModal.tsx  # Modal création nœud
│   ├── EdgeTypeSelector.tsx # Sélecteur type de lien
│   ├── GraphNodePanel.tsx   # Panneau propriétés nœud
│   ├── GraphToolbar.tsx     # Barre d'outils (prompt LLM)
│   └── ZoomControls.tsx     # Boutons zoom
│
├── handlers/                # Gestionnaires d'événements
│   ├── backgroundHandlers.ts # Clicks sur fond
│   ├── nodeHandlers.ts       # Clicks sur nœuds
│   └── index.ts
│
├── hooks/                   # Hooks React personnalisés
│   ├── useDimensions.ts     # Dimensions responsives
│   ├── useEdgeMode.ts       # Mode création lien
│   ├── useGraphState.ts     # État global du graphe
│   ├── useZoomControls.ts   # Contrôles zoom
│   └── index.ts
│
└── utils/                   # Utilitaires D3 purs
    ├── constants.ts         # Constantes (couleurs, forces, etc.)
    ├── edges.ts             # Création/update liens
    ├── markers.ts           # Flèches SVG
    ├── nodes.ts             # Création/update nœuds
    ├── simulation.ts        # Configuration force simulation
    └── index.ts
```

## 🎯 Principes d'organisation

### **behaviors/** - Comportements D3

Modules qui créent des comportements D3 (drag, zoom, etc.) réutilisables.

- Retournent des behaviors D3 configurés
- Utilisent `event.on()` pour les closures

### **components/** - Composants UI

Composants React purs pour l'interface utilisateur.

- Composants contrôlés (props + callbacks)
- Pas de logique D3

### **handlers/** - Gestionnaires d'événements

Fonctions factory qui créent des handlers d'événements.

- Fonctions pures
- Retournent des handlers configurés

### **hooks/** - Hooks React

Custom hooks pour la gestion d'état et effets.

- `useGraphState`: État centralisé (refs, state)
- `useZoomControls`: Logique zoom + behavior
- `useEdgeMode`: Logique mode lien
- `useDimensions`: Calcul dimensions responsive

### **utils/** - Utilitaires D3

Fonctions utilitaires pures pour manipuler D3.

- `constants`: Toutes les constantes du projet
- `edges`: Création et mise à jour des liens
- `markers`: Création des marqueurs SVG (flèches)
- `nodes`: Création et mise à jour des nœuds
- `simulation`: Configuration de la force simulation

## 🔄 Flux de données

```
GraphViewer.tsx (orchestration)
    ↓
hooks/ (état + logique)
    ↓
behaviors/ + handlers/ (événements)
    ↓
utils/ (rendu D3)
    ↓
components/ (UI React)
```

## 📦 Imports recommandés

```typescript
// Depuis l'extérieur
import { GraphViewer, type GraphViewerProps } from "@/components/common/GraphViewer";

// Dans GraphViewer.tsx
import { useGraphState, useZoomControls } from "./hooks";
import { createDragBehavior } from "./behaviors";
import { createNodeClickHandler } from "./handlers";
import { createNodes, createEdges, DEFAULT_NODE_RADIUS } from "./utils";
```

## 🎨 Avantages de cette structure

✅ **Séparation des responsabilités** - Chaque dossier a un rôle clair
✅ **Réutilisabilité** - Modules indépendants et testables
✅ **Maintenabilité** - Facile de trouver et modifier le code
✅ **Scalabilité** - Facile d'ajouter de nouvelles features
✅ **Lisibilité** - Import propres depuis `./utils`, `./hooks`, etc.

## 🐛 Debug

Le mode lien (edge creation) a des logs de debug dans `behaviors/dragBehavior.ts` :

- 🎯 Start/End drag
- 📍 Source node
- 🖱️ Mouse position
- 📏 Line created
- 🔄 Dragging
- 🗑️ Cleanup

Pour tester : Activer "Mode Lien" → Drag un nœud → Vérifier console F12
