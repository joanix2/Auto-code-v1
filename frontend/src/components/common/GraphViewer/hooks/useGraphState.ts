import { useState, useRef } from "react";
import * as d3 from "d3";
import { GraphNode, GraphEdge } from "../types";

export type GraphMode = "move" | "node" | "edge" | "delete";

export function useGraphState() {
  const [transform, setTransform] = useState(d3.zoomIdentity);
  const transformRef = useRef(d3.zoomIdentity);
  const simulationRef = useRef<d3.Simulation<GraphNode, GraphEdge> | null>(null);
  const zoomBehaviorRef = useRef<d3.ZoomBehavior<SVGSVGElement, unknown> | null>(null);
  const dragStartPosRef = useRef<{ x: number; y: number } | null>(null);

  const [selectedNodeData, setSelectedNodeData] = useState<GraphNode | null>(null);
  const [showNodePanel, setShowNodePanel] = useState(false);

  // Mode actif
  const [mode, setMode] = useState<GraphMode>("move");
  const [edgeDragState, setEdgeDragState] = useState<{
    sourceNode: GraphNode | null;
    targetNode: GraphNode | null;
    isDrawing: boolean;
  }>({
    sourceNode: null,
    targetNode: null,
    isDrawing: false,
  });
  const [showEdgeTypeSelector, setShowEdgeTypeSelector] = useState(false);

  // LLM prompt
  const [prompt, setPrompt] = useState("");

  return {
    transform, setTransform,
    transformRef, simulationRef, zoomBehaviorRef, dragStartPosRef,
    selectedNodeData, setSelectedNodeData,
    showNodePanel, setShowNodePanel,
    mode, setMode,
    edgeDragState, setEdgeDragState,
    showEdgeTypeSelector, setShowEdgeTypeSelector,
    prompt, setPrompt,
  };
}
