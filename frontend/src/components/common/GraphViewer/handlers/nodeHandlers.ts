import { GraphNode, EdgeTypeConstraint } from "../types";

interface NodeClickHandlerParams {
  isEdgeModeActive: boolean;
  edgeDragState: {
    sourceNode: GraphNode | null;
    targetNode: GraphNode | null;
    isDrawing: boolean;
  };
  setEdgeDragState: (state: { sourceNode: GraphNode | null; targetNode: GraphNode | null; isDrawing: boolean }) => void;
  setShowEdgeTypeSelector: (show: boolean) => void;
  setSelectedNodeData: (node: GraphNode | null) => void;
  setShowNodePanel: (show: boolean) => void;
  getAvailableEdgeTypes: (source: GraphNode | null, target: GraphNode | null) => EdgeTypeConstraint[];
  onCreateEdge?: (source: string, target: string, type: string) => void;
  onNodeClick?: (node: GraphNode) => void;
}

export function createNodeClickHandler({
  isEdgeModeActive,
  edgeDragState,
  setEdgeDragState,
  setShowEdgeTypeSelector,
  setSelectedNodeData,
  setShowNodePanel,
  getAvailableEdgeTypes,
  onCreateEdge,
  onNodeClick,
}: NodeClickHandlerParams) {
  return (node: GraphNode) => {
    if (isEdgeModeActive) {
      if (!edgeDragState.sourceNode) {
        // Premier clic : définir le nœud source
        setEdgeDragState({
          sourceNode: node,
          targetNode: null,
          isDrawing: false,
        });
      } else if (edgeDragState.sourceNode.id !== node.id) {
        // Deuxième clic : définir le nœud cible
        const availableTypes = getAvailableEdgeTypes(edgeDragState.sourceNode, node);

        if (availableTypes.length === 0) {
          console.warn(`Aucun type de lien disponible entre ${edgeDragState.sourceNode.type} et ${node.type}`);
          setEdgeDragState({
            sourceNode: null,
            targetNode: null,
            isDrawing: false,
          });
        } else if (availableTypes.length === 1) {
          // Un seul type : créer directement
          if (onCreateEdge) {
            onCreateEdge(edgeDragState.sourceNode.id, node.id, availableTypes[0].edgeType);
          }
          setEdgeDragState({
            sourceNode: null,
            targetNode: null,
            isDrawing: false,
          });
        } else {
          // Plusieurs types : ouvrir le sélecteur
          setEdgeDragState({
            sourceNode: edgeDragState.sourceNode,
            targetNode: node,
            isDrawing: false,
          });
          setShowEdgeTypeSelector(true);
        }
      } else {
        // Clic sur le même nœud : annuler
        setEdgeDragState({
          sourceNode: null,
          targetNode: null,
          isDrawing: false,
        });
      }
    } else {
      // Mode normal : afficher le panel
      setSelectedNodeData(node);
      setShowNodePanel(true);
      if (onNodeClick) onNodeClick(node);
    }
  };
}
