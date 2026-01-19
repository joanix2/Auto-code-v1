import { useCallback } from "react";
import { GraphNode } from "../types";
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
}

export function useEdgeMode({ isEdgeModeActive, setIsEdgeModeActive, edgeDragState, setEdgeDragState, edgeTypes }: UseEdgeModeParams) {
  const getAvailableEdgeTypes = useCallback(
    (sourceNode: GraphNode | null, targetNode: GraphNode | null) => {
      if (!sourceNode || !targetNode || !edgeTypes.length) return [];

      const sourceType = sourceNode.type || "";
      const targetType = targetNode.type || "";

      // Filter edge types that allow this connection
      const allowedTypes = getAllowedEdgeTypes(edgeTypes, sourceType, targetType);

      // Return in the format expected by the UI (with edgeType name)
      return allowedTypes.map((edgeType) => ({
        ...edgeType,
        edgeType: edgeType.name.toUpperCase(), // For display in UI
      }));
    },
    [edgeTypes],
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
