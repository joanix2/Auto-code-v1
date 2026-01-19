/**
 * Classe abstraite représentant un type de nœud
 */
export abstract class NodeType {
  /** Identifiant unique du type */
  abstract readonly id: string;
  /** Label au singulier */
  abstract readonly label: string;
  /** Label au pluriel */
  abstract readonly labelPlural: string;
  /** Genre grammatical ('m' pour masculin, 'f' pour féminin) */
  abstract readonly gender: "m" | "f";
  /** Article défini ('le', 'la', 'l'') */
  abstract readonly article: string;

  /**
   * Retourne l'article avec majuscule
   */
  getArticleMaj(): string {
    return this.article.charAt(0).toUpperCase() + this.article.slice(1);
  }
}

/**
 * Type de lien possible entre deux types de nœuds
 */
export interface EdgeType {
  edgeType: string;
  sourceNodeType: string;
  targetNodeType: string;
  label: string;
  description?: string;
}

export interface GraphNode {
  id: string;
  label: string;
  nodeType?: NodeType;
  type?: string; // Pour rétrocompatibilité - contient nodeType.id
  properties?: Record<string, unknown>;
  x?: number;
  y?: number;
  fx?: number | null;
  fy?: number | null;
}

export interface GraphEdge {
  id: string;
  source: string | GraphNode;
  target: string | GraphNode;
  label?: string;
  type?: string;
  properties?: Record<string, unknown>;
}

export interface SimulationEdge extends GraphEdge {
  source: GraphNode;
  target: GraphNode;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface GraphViewerProps {
  data: GraphData;
  width?: number;
  height?: number;
  nodeRadius?: number;
  onNodeClick?: (node: GraphNode) => void;
  onNodeDoubleClick?: (node: GraphNode) => void;
  onEdgeClick?: (edge: GraphEdge) => void;
  onBackgroundClick?: () => void;
  selectedNodeId?: string | null;
  nodeColorMap?: Record<string, string>;
  edgeColorMap?: Record<string, string>;
  showLabels?: boolean;
  enableZoom?: boolean;
  enableDrag?: boolean;
  className?: string;
  onEditNode?: (node: GraphNode) => void;
  onDeleteNode?: (node: GraphNode) => void;
  /**
   * Map de formulaires par type de nœud
   * Clé: type du nœud (ex: "concept", "attribute")
   * Valeur: fonction qui retourne le formulaire React pour ce type
   */
  forms?: Record<string, (node: GraphNode, isEditing: boolean, onCancelEdit: () => void, onTypeChange?: (newType: string) => void) => React.ReactNode>;
  /**
   * Types de liens possibles avec contraintes
   */
  edgeTypes?: EdgeType[];
  /**
   * Callback appelé quand un lien est créé
   */
  onCreateEdge?: (sourceNodeId: string, targetNodeId: string, edgeType: string) => void;
  /**
   * Callback appelé quand l'utilisateur veut ajouter un nœud
   */
  onAddNode?: () => void;
}
