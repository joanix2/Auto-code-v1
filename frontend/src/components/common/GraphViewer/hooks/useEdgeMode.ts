import { useCallback } from "react";
import { GraphNode, GraphEdge } from "../types";
import { M3EdgeType, getAllowedEdgeTypes } from "@/types/m3";

interface UseEdgeModeParams {
  isEdgeModeActive: boolean;
  setIsEdgeModeActive: (active: boolean) => void;
  edgeDragState: {
    sourceNode: GraphNode | null;
    targetNode: GraphNode | null;
    isDrawing: boolean;
  };
  setEdgeDragState: (state: { sourceNode: GraphNode | null; targetNode: GraphNode | null; isDrawing: boolean }) => void;
  edgeTypes: M3EdgeType[];
  existingEdges: GraphEdge[];
}

export function useEdgeMode({ isEdgeModeActive, setIsEdgeModeActive, edgeDragState, setEdgeDragState, edgeTypes, existingEdges }: UseEdgeModeParams) {
  const getAvailableEdgeTypes = useCallback(
    (sourceNode: GraphNode | null, targetNode: GraphNode | null) => {
      if (!sourceNode || !targetNode || !edgeTypes.length) return [];

      const sourceType = sourceNode.type || "";
      const targetType = targetNode.type || "";

      // Filter edge types that allow this connection
      const allowedTypes = getAllowedEdgeTypes(edgeTypes, sourceType, targetType);

      // Filter out edge types that already exist between these nodes
      const availableTypes = allowedTypes.filter((edgeType) => {
        const edgeTypeName = edgeType.name.toUpperCase();
        return !existingEdges.some((edge) => edge.source === sourceNode.id && edge.target === targetNode.id && edge.type?.toUpperCase() === edgeTypeName);
      });

      // Return in the format expected by the UI (with edgeType name)
      return availableTypes.map((edgeType) => ({
        ...edgeType,
        edgeType: edgeType.name.toUpperCase(), // For display in UI
      }));
    },
    [edgeTypes, existingEdges],
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
