import { useCallback } from "react";
import { GraphNode, EdgeTypeConstraint } from "../types";

interface UseEdgeModeParams {
  isEdgeModeActive: boolean;
  setIsEdgeModeActive: (active: boolean) => void;
  edgeDragState: {
    sourceNode: GraphNode | null;
    targetNode: GraphNode | null;
    isDrawing: boolean;
  };
  setEdgeDragState: (state: { sourceNode: GraphNode | null; targetNode: GraphNode | null; isDrawing: boolean }) => void;
  edgeTypeConstraints: EdgeTypeConstraint[];
}

export function useEdgeMode({ isEdgeModeActive, setIsEdgeModeActive, edgeDragState, setEdgeDragState, edgeTypeConstraints }: UseEdgeModeParams) {
  const getAvailableEdgeTypes = useCallback(
    (sourceNode: GraphNode | null, targetNode: GraphNode | null) => {
      if (!sourceNode || !targetNode || !edgeTypeConstraints.length) return [];

      return edgeTypeConstraints.filter((constraint) => constraint.sourceNodeType === sourceNode.type && constraint.targetNodeType === targetNode.type);
    },
    [edgeTypeConstraints],
  );

  const toggleEdgeMode = useCallback(() => {
    setIsEdgeModeActive(!isEdgeModeActive);
    if (isEdgeModeActive) {
      setEdgeDragState({
        sourceNode: null,
        targetNode: null,
        isDrawing: false,
      });
    }
  }, [isEdgeModeActive, setIsEdgeModeActive, setEdgeDragState]);

  const handleEdgeTypeSelected = useCallback(
    (edgeType: string, onCreateEdge?: (source: string, target: string, type: string) => void) => {
      if (edgeDragState.sourceNode && edgeDragState.targetNode && onCreateEdge) {
        onCreateEdge(edgeDragState.sourceNode.id, edgeDragState.targetNode.id, edgeType);
      }
      setEdgeDragState({
        sourceNode: null,
        targetNode: null,
        isDrawing: false,
      });
    },
    [edgeDragState, setEdgeDragState],
  );

  return {
    getAvailableEdgeTypes,
    toggleEdgeMode,
    handleEdgeTypeSelected,
  };
}
