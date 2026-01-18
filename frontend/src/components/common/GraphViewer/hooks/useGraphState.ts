import { useState, useRef } from "react";
import * as d3 from "d3";
import { GraphNode, GraphEdge } from "../types";

export function useGraphState() {
  const [transform, setTransform] = useState(d3.zoomIdentity);
  const transformRef = useRef(d3.zoomIdentity);
  const simulationRef = useRef<d3.Simulation<GraphNode, GraphEdge> | null>(null);
  const zoomBehaviorRef = useRef<d3.ZoomBehavior<SVGSVGElement, unknown> | null>(null);
  const dragStartPosRef = useRef<{ x: number; y: number } | null>(null);

  // State pour le panel de propriétés du nœud
  const [selectedNodeData, setSelectedNodeData] = useState<GraphNode | null>(null);
  const [showNodePanel, setShowNodePanel] = useState(false);

  // State pour le mode création de lien
  const [isEdgeModeActive, setIsEdgeModeActive] = useState(false);
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

  // State pour la barre d'outils
  const [prompt, setPrompt] = useState("");

  return {
    transform,
    setTransform,
    transformRef,
    simulationRef,
    zoomBehaviorRef,
    dragStartPosRef,
    selectedNodeData,
    setSelectedNodeData,
    showNodePanel,
    setShowNodePanel,
    isEdgeModeActive,
    setIsEdgeModeActive,
    edgeDragState,
    setEdgeDragState,
    showEdgeTypeSelector,
    setShowEdgeTypeSelector,
    prompt,
    setPrompt,
  };
}
