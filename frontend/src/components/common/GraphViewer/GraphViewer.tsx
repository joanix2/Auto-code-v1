import React, { useEffect, useRef, useState, useCallback } from "react";
import * as d3 from "d3";
import { GraphViewerProps, GraphNode, GraphEdge } from "./types";
import { DEFAULT_NODE_RADIUS, ZOOM_IN_FACTOR, ZOOM_OUT_FACTOR, FIT_TO_SCREEN_PADDING } from "./constants";
import { useDimensions } from "./hooks";
import { createArrowMarkers } from "./markers";
import { createSimulation } from "./simulation";
import { createEdges, createEdgeLabels, updateEdgePositions } from "./edges";
import { createNodes, createNodeLabels, updateNodePositions, addDragBehavior } from "./nodes";
import { createZoomBehavior } from "./zoom";
import { ZoomControls } from "./ZoomControls";
import { GraphNodePanel } from "./GraphNodePanel";
import { EdgeTypeSelector } from "./EdgeTypeSelector";
import { GraphToolbar } from "./GraphToolbar";
import { Link } from "lucide-react";
import { Button } from "@/components/ui/button";

export const GraphViewer: React.FC<GraphViewerProps> = ({
  data,
  width,
  height,
  nodeRadius = DEFAULT_NODE_RADIUS,
  onNodeClick,
  onNodeDoubleClick,
  onEdgeClick,
  onBackgroundClick,
  selectedNodeId = null,
  nodeColorMap = {},
  edgeColorMap = {},
  showLabels = true,
  enableZoom = true,
  enableDrag = true,
  className = "",
  onEditNode,
  onDeleteNode,
  forms,
  edgeTypeConstraints = [],
  onCreateEdge,
  onAddNode,
}) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const dimensions = useDimensions(containerRef, width, height);
  const [transform, setTransform] = useState(d3.zoomIdentity);
  const transformRef = useRef(d3.zoomIdentity);
  const simulationRef = useRef<d3.Simulation<GraphNode, GraphEdge> | null>(null);
  const zoomBehaviorRef = useRef<d3.ZoomBehavior<SVGSVGElement, unknown> | null>(null);
  const dragStartPosRef = useRef<{ x: number; y: number } | null>(null);
  const clickThreshold = 5; // pixels

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

  const handleSendPrompt = () => {
    if (!prompt.trim()) return;

    // TODO: Envoyer le prompt au LLM pour modification du graphe
    console.log("Prompt LLM:", prompt);

    // Réinitialiser le prompt après envoi
    setPrompt("");
  };

  // Synchroniser selectedNodeData avec les changements dans data.nodes
  useEffect(() => {
    if (selectedNodeData) {
      // Trouver le nœud mis à jour dans les nouvelles données
      const updatedNode = data.nodes.find((node) => node.id === selectedNodeData.id);
      if (updatedNode) {
        setSelectedNodeData(updatedNode);
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data.nodes]); // Se déclenche quand data.nodes change

  // Obtenir les types de liens disponibles entre deux nœuds
  const getAvailableEdgeTypes = useCallback(
    (sourceNode: GraphNode | null, targetNode: GraphNode | null) => {
      if (!sourceNode || !targetNode || !edgeTypeConstraints.length) return [];

      return edgeTypeConstraints.filter((constraint) => constraint.sourceNodeType === sourceNode.type && constraint.targetNodeType === targetNode.type);
    },
    [edgeTypeConstraints],
  );

  // Handler pour la sélection d'un type de lien
  const handleEdgeTypeSelected = useCallback(
    (edgeType: string) => {
      if (edgeDragState.sourceNode && edgeDragState.targetNode && onCreateEdge) {
        onCreateEdge(edgeDragState.sourceNode.id, edgeDragState.targetNode.id, edgeType);
      }
      // Reset l'état
      setEdgeDragState({
        sourceNode: null,
        targetNode: null,
        isDrawing: false,
      });
    },
    [edgeDragState.sourceNode, edgeDragState.targetNode, onCreateEdge],
  );

  // Toggle le mode création de lien
  const toggleEdgeMode = useCallback(() => {
    setIsEdgeModeActive(!isEdgeModeActive);
    if (isEdgeModeActive) {
      // Réinitialiser l'état si on désactive le mode
      setEdgeDragState({
        sourceNode: null,
        targetNode: null,
        isDrawing: false,
      });
    }
  }, [isEdgeModeActive]);

  // Handlers de zoom qui utilisent la référence stockée
  const handleZoomInClick = () => {
    if (!svgRef.current || !zoomBehaviorRef.current) return;
    const svg = d3.select(svgRef.current);
    const currentTransform = d3.zoomTransform(svgRef.current);
    const centerX = dimensions.width / 2;
    const centerY = dimensions.height / 2;

    // Calculate new transform centered on the viewport center
    const point = [(centerX - currentTransform.x) / currentTransform.k, (centerY - currentTransform.y) / currentTransform.k];
    const newK = currentTransform.k * ZOOM_IN_FACTOR;
    const newTransform = d3.zoomIdentity.translate(centerX - point[0] * newK, centerY - point[1] * newK).scale(newK);

    svg.transition().duration(300).call(zoomBehaviorRef.current.transform, newTransform);
  };

  const handleZoomOutClick = () => {
    if (!svgRef.current || !zoomBehaviorRef.current) return;
    const svg = d3.select(svgRef.current);
    const currentTransform = d3.zoomTransform(svgRef.current);
    const centerX = dimensions.width / 2;
    const centerY = dimensions.height / 2;

    // Calculate new transform centered on the viewport center
    const point = [(centerX - currentTransform.x) / currentTransform.k, (centerY - currentTransform.y) / currentTransform.k];
    const newK = currentTransform.k * ZOOM_OUT_FACTOR;
    const newTransform = d3.zoomIdentity.translate(centerX - point[0] * newK, centerY - point[1] * newK).scale(newK);

    svg.transition().duration(300).call(zoomBehaviorRef.current.transform, newTransform);
  };

  const handleResetZoomClick = () => {
    if (!svgRef.current || !zoomBehaviorRef.current) return;
    const svg = d3.select(svgRef.current);
    svg.transition().duration(300).call(zoomBehaviorRef.current.transform, d3.zoomIdentity);
    setTransform(d3.zoomIdentity);
  };

  const handleFitToScreenClick = () => {
    if (!svgRef.current || !zoomBehaviorRef.current || !data.nodes.length) return;

    const svg = d3.select(svgRef.current);
    const bounds = {
      minX: Math.min(...data.nodes.map((n) => n.x || 0)),
      maxX: Math.max(...data.nodes.map((n) => n.x || 0)),
      minY: Math.min(...data.nodes.map((n) => n.y || 0)),
      maxY: Math.max(...data.nodes.map((n) => n.y || 0)),
    };

    const graphWidth = bounds.maxX - bounds.minX + nodeRadius * 4;
    const graphHeight = bounds.maxY - bounds.minY + nodeRadius * 4;
    const scale = Math.min(dimensions.width / graphWidth, dimensions.height / graphHeight, 1) * FIT_TO_SCREEN_PADDING;

    const translateX = (dimensions.width - (bounds.minX + bounds.maxX) * scale) / 2;
    const translateY = (dimensions.height - (bounds.minY + bounds.maxY) * scale) / 2;

    const newTransform = d3.zoomIdentity.translate(translateX, translateY).scale(scale);

    svg.transition().duration(300).call(zoomBehaviorRef.current.transform, newTransform);
    setTransform(newTransform);
  };

  // D3 Graph rendering
  useEffect(() => {
    if (!svgRef.current || dimensions.width === 0 || dimensions.height === 0) return;
    if (!data.nodes.length) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    // Create container group for zoom/pan (MUST be created first)
    const g = svg.append("g").attr("class", "graph-container");

    // Create background rectangle INSIDE the group for click detection
    const background = g
      .append("rect")
      .attr("class", "graph-background")
      .attr("x", -dimensions.width * 2)
      .attr("y", -dimensions.height * 2)
      .attr("width", dimensions.width * 5)
      .attr("height", dimensions.height * 5)
      .attr("fill", "transparent")
      .style("cursor", enableZoom ? "grab" : "default")
      .style("pointer-events", "all")
      .lower(); // Ensure it's behind everything else

    // Setup zoom behavior BEFORE adding click handlers
    const zoom = createZoomBehavior(svg, g, (newTransform) => {
      transformRef.current = newTransform;
      setTransform(newTransform);
    });
    zoomBehaviorRef.current = zoom;

    if (enableZoom) {
      svg.call(zoom);

      // Restore previous transform (preserve zoom and pan position)
      const currentTransform = transformRef.current;
      if (currentTransform.k !== 1 || currentTransform.x !== 0 || currentTransform.y !== 0) {
        svg.call(zoom.transform, currentTransform);
        g.attr("transform", currentTransform.toString());
      }

      // Change cursor during pan (on SVG)
      svg.on("pointerdown.cursor", function (event) {
        const target = event.target as HTMLElement;
        const tagName = target.tagName?.toUpperCase();

        // Only change cursor if not on interactive elements
        if (tagName !== "CIRCLE" && tagName !== "TEXT") {
          svg.style("cursor", "grabbing");
        }
      });
      svg.on("pointerup.cursor", function () {
        svg.style("cursor", "grab");
      });
      svg.on("pointerleave.cursor", function () {
        svg.style("cursor", "grab");
      });
    }

    // Background click handler (only fires on actual clicks, not drags)
    if (onBackgroundClick) {
      background
        .on("pointerdown", (event) => {
          dragStartPosRef.current = { x: event.clientX, y: event.clientY };
        })
        .on("pointerup", (event) => {
          if (dragStartPosRef.current) {
            const dx = Math.abs(event.clientX - dragStartPosRef.current.x);
            const dy = Math.abs(event.clientY - dragStartPosRef.current.y);

            // Only trigger click if movement is minimal (not a drag)
            if (dx < clickThreshold && dy < clickThreshold) {
              setSelectedNodeData(null);
              setShowNodePanel(false);
              if (onBackgroundClick) onBackgroundClick();
            }
          }
          dragStartPosRef.current = null;
        });
    }

    // Create arrow markers
    createArrowMarkers(svg, nodeRadius);

    // Create force simulation
    const simulation = createSimulation(data.nodes, data.edges, dimensions.width, dimensions.height, nodeRadius);
    simulationRef.current = simulation;

    // Create edges and edge labels
    const link = createEdges(g, data.edges, edgeColorMap, onEdgeClick);
    const edgeLabels = createEdgeLabels(g, data.edges, showLabels);

    // Create nodes and node labels
    const handleInternalNodeClick = (node: GraphNode) => {
      // Si le mode création de lien est actif
      if (isEdgeModeActive) {
        if (!edgeDragState.sourceNode) {
          // Premier clic : définir le nœud source
          setEdgeDragState({
            sourceNode: node,
            targetNode: null,
            isDrawing: false,
          });
        } else if (edgeDragState.sourceNode.id !== node.id) {
          // Deuxième clic : définir le nœud cible et ouvrir le sélecteur
          const availableTypes = getAvailableEdgeTypes(edgeDragState.sourceNode, node);

          if (availableTypes.length === 0) {
            // Aucun type de lien disponible
            console.warn(`Aucun type de lien disponible entre ${edgeDragState.sourceNode.type} et ${node.type}`);
            // Reset
            setEdgeDragState({
              sourceNode: null,
              targetNode: null,
              isDrawing: false,
            });
          } else if (availableTypes.length === 1) {
            // Un seul type disponible : créer directement
            if (onCreateEdge) {
              onCreateEdge(edgeDragState.sourceNode.id, node.id, availableTypes[0].edgeType);
            }
            // Reset
            setEdgeDragState({
              sourceNode: null,
              targetNode: null,
              isDrawing: false,
            });
          } else {
            // Plusieurs types disponibles : ouvrir le sélecteur
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

    const node = createNodes(g, data.nodes, nodeRadius, selectedNodeId, nodeColorMap, handleInternalNodeClick, onNodeDoubleClick);
    const nodeLabels = createNodeLabels(g, data.nodes, nodeRadius, selectedNodeId, showLabels);

    // Add drag behavior
    if (enableDrag) {
      addDragBehavior(node, simulation);
    }

    // Update positions on simulation tick
    simulation.on("tick", () => {
      updateEdgePositions(link, edgeLabels);
      updateNodePositions(node, nodeLabels);
    });

    // Apply initial transform
    svg.call(zoom.transform, transformRef.current);

    return () => {
      simulation.stop();
    };
  }, [
    data,
    dimensions,
    selectedNodeId,
    nodeColorMap,
    edgeColorMap,
    showLabels,
    enableZoom,
    enableDrag,
    nodeRadius,
    onNodeClick,
    onNodeDoubleClick,
    onEdgeClick,
    onBackgroundClick,
    isEdgeModeActive,
    edgeDragState.sourceNode,
    onCreateEdge,
    getAvailableEdgeTypes,
  ]);

  return (
    <div className={`relative h-full w-full ${className}`}>
      <div ref={containerRef} className="relative w-full h-full">
        <svg ref={svgRef} width={dimensions.width} height={dimensions.height} className="bg-gray-50" style={{ touchAction: "none" }} />

        {/* Zoom Controls */}
        {enableZoom && <ZoomControls onZoomIn={handleZoomInClick} onZoomOut={handleZoomOutClick} onFitToScreen={handleFitToScreenClick} onReset={handleResetZoomClick} />}

        {/* Node Properties Panel */}
        <GraphNodePanel
          node={selectedNodeData}
          isOpen={showNodePanel}
          onClose={() => {
            setShowNodePanel(false);
            setSelectedNodeData(null);
          }}
          onEdit={onEditNode}
          onDelete={onDeleteNode}
          renderForm={selectedNodeData && forms && selectedNodeData.type ? forms[selectedNodeData.type] : undefined}
        />

        {/* Edge Type Selector */}
        <EdgeTypeSelector
          open={showEdgeTypeSelector}
          onOpenChange={setShowEdgeTypeSelector}
          sourceNode={edgeDragState.sourceNode}
          targetNode={edgeDragState.targetNode}
          availableEdgeTypes={getAvailableEdgeTypes(edgeDragState.sourceNode, edgeDragState.targetNode)}
          onSelectEdgeType={handleEdgeTypeSelected}
        />

        {/* Empty state */}
        {data.nodes.length === 0 && (
          <div className="absolute inset-0 flex items-center justify-center text-gray-400">
            <p>No data to display</p>
          </div>
        )}

        {/* Graph Toolbar - Barre de prompt LLM en bas */}
        <GraphToolbar prompt={prompt} onPromptChange={setPrompt} onSendPrompt={handleSendPrompt} onAddNode={() => onAddNode?.()} isEdgeMode={isEdgeModeActive} onToggleEdgeMode={toggleEdgeMode} />
      </div>
    </div>
  );
};

export default GraphViewer;
