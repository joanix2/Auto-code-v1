# GraphViewer - Architecture modulaire

## 📁 Structure des fichiers

```
GraphViewer/
├── index.ts              # Exports publics
├── GraphViewer.tsx       # Composant principal
├── types.ts              # Types TypeScript
├── constants.ts          # Constantes de configuration
├── hooks.ts              # Custom React hooks
├── simulation.ts         # Configuration D3 force simulation
├── nodes.ts              # Logique des nœuds (création, update, drag)
├── edges.ts              # Logique des arêtes (création, update)
├── markers.ts            # Création des arrow markers SVG
├── zoom.ts               # Gestion du zoom/pan
└── ZoomControls.tsx      # Composant UI contrôles zoom
```

## 📦 Modules

### `types.ts`

Définit tous les types TypeScript :

- `GraphNode` : Structure d'un nœud
- `GraphEdge` : Structure d'une arête
- `SimulationEdge` : Edge après simulation D3
- `GraphData` : Données du graphe (nodes + edges)
- `GraphViewerProps` : Props du composant principal

### `constants.ts`

Centralise toutes les constantes :

- Tailles et distances (nodeRadius, linkDistance, etc.)
- Couleurs par défaut
- Facteurs de zoom
- Tailles de police

### `hooks.ts`

Custom hooks React :

- `useDimensions()` : Calcul responsive des dimensions du container

### `simulation.ts`

Configuration D3 force simulation :

- `createSimulation()` : Initialise la simulation avec toutes les forces

### `nodes.ts`

Gestion des nœuds :

- `createNodes()` : Crée les éléments SVG circle
- `createNodeLabels()` : Crée les labels des nœuds
- `updateNodePositions()` : Met à jour les positions (tick)
- `addDragBehavior()` : Ajoute le comportement drag & drop

### `edges.ts`

Gestion des arêtes :

- `createEdges()` : Crée les éléments SVG line
- `createEdgeLabels()` : Crée les labels des arêtes
- `updateEdgePositions()` : Met à jour les positions (tick)

### `markers.ts`

Création des markers SVG :

- `createArrowMarkers()` : Crée les flèches pour les arêtes orientées

### `zoom.ts`

Gestion du zoom/pan :

- `createZoomBehavior()` : Configure D3 zoom
- `handleZoomIn()` : Zoom avant
- `handleZoomOut()` : Zoom arrière
- `handleResetZoom()` : Reset zoom
- `handleFitToScreen()` : Ajuste le zoom pour afficher tout le graphe

### `ZoomControls.tsx`

Composant UI des contrôles de zoom :

- 4 boutons : Zoom In, Zoom Out, Fit to Screen, Reset

## 🎯 Utilisation

```tsx
import { GraphViewer } from "@/components/common/GraphViewer";
import type { GraphData, GraphNode, GraphEdge } from "@/components/common/GraphViewer";

const data: GraphData = {
  nodes: [
    { id: "1", label: "Node 1", type: "concept" },
    { id: "2", label: "Node 2", type: "concept" },
  ],
  edges: [{ id: "e1", source: "1", target: "2", label: "relation", type: "association" }],
};

<GraphViewer
  data={data}
  nodeRadius={30}
  onNodeClick={(node) => console.log("Clicked:", node)}
  nodeColorMap={{ concept: "#3b82f6" }}
  edgeColorMap={{ association: "#6366f1" }}
  enableZoom={true}
  enableDrag={true}
  showLabels={true}
/>;
```

## ✨ Avantages de la segmentation

1. **Maintenabilité** : Chaque module a une responsabilité unique
2. **Testabilité** : Fonctions pures facilement testables
3. **Réutilisabilité** : Modules utilisables indépendamment
4. **Lisibilité** : Code organisé et documenté
5. **Extensibilité** : Facile d'ajouter de nouvelles fonctionnalités
6. **Performance** : Imports sélectifs possibles

## 🔧 Personnalisation

### Modifier les constantes

Éditez `constants.ts` pour changer les valeurs par défaut :

```ts
export const DEFAULT_NODE_RADIUS = 25; // au lieu de 20
export const ZOOM_IN_FACTOR = 1.5; // au lieu de 1.3
```

### Ajouter une nouvelle force

Dans `simulation.ts` :

```ts
.force("x", d3.forceX().strength(0.1))
.force("y", d3.forceY().strength(0.1))
```

### Personnaliser les nœuds

Modifiez `createNodes()` dans `nodes.ts` pour changer le rendu.

## 📝 Types de nœuds/arêtes personnalisés

Les types sont définis dans `types.ts`. Vous pouvez étendre avec vos propres propriétés :

```ts
interface MyCustomNode extends GraphNode {
  customProperty: string;
  metadata: Record<string, unknown>;
}
```

## 🎨 Thèmes

Utilisez `nodeColorMap` et `edgeColorMap` pour appliquer des couleurs selon les types :

```tsx
nodeColorMap={{
  concept: "#3b82f6",    // Bleu
  attribute: "#10b981",  // Vert
  entity: "#f59e0b"      // Orange
}}
```
