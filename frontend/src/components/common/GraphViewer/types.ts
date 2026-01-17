export interface GraphNode {
  id: string;
  label: string;
  type?: string;
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
  forms?: Record<string, (node: GraphNode, isEditing: boolean, onCancelEdit: () => void) => React.ReactNode>;
}
