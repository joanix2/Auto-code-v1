import { useCallback } from "react";
import { GraphNode, GraphEdge } from "../types";
import { M3EdgeType, getAllowedEdgeTypes } from "@/types/dsl-config";
import type { GraphMode } from "./useGraphState";

interface UseEdgeModeParams {
  mode: GraphMode;
  setMode: (m: GraphMode) => void;
  edgeDragState: {
    sourceNode: GraphNode | null;
    targetNode: GraphNode | null;
    isDrawing: boolean;
  };
  setEdgeDragState: (state: { sourceNode: GraphNode | null; targetNode: GraphNode | null; isDrawing: boolean }) => void;
  edgeTypes: M3EdgeType[];
  existingEdges: GraphEdge[];
}

export function useEdgeMode({ mode, setMode, edgeDragState, setEdgeDragState, edgeTypes, existingEdges }: UseEdgeModeParams) {
  const isEdgeModeActive = mode === "edge";

  const getAvailableEdgeTypes = useCallback(
    (sourceNode: GraphNode | null, targetNode: GraphNode | null) => {
      if (!sourceNode || !targetNode || !edgeTypes.length) return [];
      const sourceType = sourceNode.type || "";
      const targetType = targetNode.type || "";
      const allowedTypes = getAllowedEdgeTypes(edgeTypes, sourceType, targetType);
      const availableTypes = allowedTypes.filter((edgeType) => {
        const edgeTypeName = edgeType.name.toUpperCase();
        return !existingEdges.some(
          (edge) => edge.source === sourceNode.id && edge.target === targetNode.id && edge.type?.toUpperCase() === edgeTypeName
        );
      });
      return availableTypes.map((edgeType) => ({ ...edgeType, edgeType: edgeType.name.toUpperCase() }));
    },
    [edgeTypes, existingEdges],
  );

  const setEdgeMode = useCallback(() => {
    setMode(mode === "edge" ? "move" : "edge");
    setEdgeDragState({ sourceNode: null, targetNode: null, isDrawing: false });
  }, [mode, setMode, setEdgeDragState]);

  const handleEdgeTypeSelected = useCallback(
    (edgeType: string, onCreateEdge?: (source: string, target: string, type: string) => void) => {
      if (edgeDragState.sourceNode && edgeDragState.targetNode && onCreateEdge) {
        onCreateEdge(edgeDragState.sourceNode.id, edgeDragState.targetNode.id, edgeType);
      }
      setEdgeDragState({ sourceNode: null, targetNode: null, isDrawing: false });
    },
    [edgeDragState, setEdgeDragState],
  );

  return {
    getAvailableEdgeTypes,
    setEdgeMode,
    handleEdgeTypeSelected,
    isEdgeModeActive,
  };
}
