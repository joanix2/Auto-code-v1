import React from "react";
import { GraphNode } from "../types";
import type { GraphMode } from "@/lib/graph-modes";
import { M3EdgeType } from "@/types/dsl-config";

interface NodeClickHandlerParams {
  modeRef: React.MutableRefObject<GraphMode>;
  edgeDragState: {
    sourceNode: GraphNode | null;
    targetNode: GraphNode | null;
    isDrawing: boolean;
  };
  setEdgeDragState: (state: { sourceNode: GraphNode | null; targetNode: GraphNode | null; isDrawing: boolean }) => void;
  setShowEdgeTypeSelector: (show: boolean) => void;
  setSelectedNodeData: (node: GraphNode | null) => void;
  setShowNodePanel: (show: boolean) => void;
  getAvailableEdgeTypes: (source: GraphNode | null, target: GraphNode | null) => M3EdgeType[];
  onCreateEdge?: (source: string, target: string, type: string) => void;
  onNodeClick?: (node: GraphNode) => void;
  onDeleteNode?: (node: GraphNode) => void;
}

export function createNodeClickHandler({
  modeRef,
  edgeDragState,
  setEdgeDragState,
  setShowEdgeTypeSelector,
  setSelectedNodeData,
  setShowNodePanel,
  getAvailableEdgeTypes,
  onCreateEdge,
  onNodeClick,
  onDeleteNode,
}: NodeClickHandlerParams) {
  return (node: GraphNode) => {
    if (modeRef.current === "edge") {
      if (!edgeDragState.sourceNode) {
        setEdgeDragState({ sourceNode: node, targetNode: null, isDrawing: false });
      } else if (edgeDragState.sourceNode.id !== node.id) {
        const availableTypes = getAvailableEdgeTypes(edgeDragState.sourceNode, node);
        if (availableTypes.length === 0) {
          setEdgeDragState({ sourceNode: null, targetNode: null, isDrawing: false });
        } else if (availableTypes.length === 1) {
          onCreateEdge?.(edgeDragState.sourceNode.id, node.id, availableTypes[0].name);
          setEdgeDragState({ sourceNode: null, targetNode: null, isDrawing: false });
        } else {
          setEdgeDragState({ sourceNode: edgeDragState.sourceNode, targetNode: node, isDrawing: false });
          setShowEdgeTypeSelector(true);
        }
      } else {
        setEdgeDragState({ sourceNode: null, targetNode: null, isDrawing: false });
      }
    } else if (modeRef.current === "delete") {
      onDeleteNode?.(node);
    } else {
      setSelectedNodeData(node);
      setShowNodePanel(true);
      onNodeClick?.(node);
    }
  };
}
