import React, { useEffect, useRef } from "react";
import * as d3 from "d3";
import { GraphViewerProps, GraphNode } from "./types";
import { useDimensions, useGraphState, useZoomControls, useEdgeMode } from "./hooks";
import { createNodeClickHandler, createBackgroundHandlers } from "./handlers";
import { createDragBehavior } from "./behaviors";
import { createZoomBehavior } from "./hooks/useZoomControls";
import { ZoomControls } from "./components/ZoomControls";
import { GraphNodePanel } from "./components/GraphNodePanel";
import { EdgeTypeSelector } from "./components/EdgeTypeSelector";
import { GraphToolbar } from "./components/GraphToolbar";
import { DEFAULT_NODE_RADIUS, createArrowMarkers, createSimulation, createEdges, createEdgeLabels, updateEdgePositions, createNodes, createNodeLabels, updateNodePositions } from "./utils";

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
  const clickThreshold = 5; // pixels

  // Utiliser les hooks personnalisés
  const state = useGraphState();
  const {
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
    setTransform,
  } = state;

  // Hook pour la gestion du mode lien
  const {
    getAvailableEdgeTypes,
    toggleEdgeMode,
    handleEdgeTypeSelected: baseHandleEdgeTypeSelected,
  } = useEdgeMode({
    isEdgeModeActive,
    setIsEdgeModeActive,
    edgeDragState,
    setEdgeDragState,
    edgeTypeConstraints,
  });

  // Hook pour les contrôles de zoom
  const { handleZoomIn, handleZoomOut, handleReset, handleFitToScreen } = useZoomControls({
    svgRef,
    zoomBehaviorRef,
    dimensions,
    nodes: data.nodes,
    nodeRadius,
    setTransform,
  });

  const handleSendPrompt = () => {
    if (!prompt.trim()) return;
    console.log("Prompt LLM:", prompt);
    setPrompt("");
  };

  const handleEdgeTypeSelected = (edgeType: string) => {
    baseHandleEdgeTypeSelected(edgeType, onCreateEdge);
  };

  // Synchroniser selectedNodeData avec les changements dans data.nodes
  useEffect(() => {
    if (selectedNodeData) {
      const updatedNode = data.nodes.find((node) => node.id === selectedNodeData.id);
      if (updatedNode) {
        setSelectedNodeData(updatedNode);
      }
    }
  }, [data.nodes, selectedNodeData, setSelectedNodeData]);

  // D3 Graph rendering
  useEffect(() => {
    if (!svgRef.current || dimensions.width === 0 || dimensions.height === 0) return;
    if (!data.nodes.length) return;

    const svg = d3.select(svgRef.current);

    // Instead of removing everything, selectively remove only graph elements
    // This preserves the temp-edge-group during drag operations
    svg.selectAll(".graph-container").remove();
    svg.selectAll("defs").remove();

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

      // Synchroniser le tempGroup avec la transformation
      const tempGroup = svg.select<SVGGElement>("g.temp-edge-group");
      if (!tempGroup.empty()) {
        tempGroup.attr("transform", newTransform.toString());
      }
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

    // Créer un groupe pour le nœud fantôme et la ligne temporaire en mode lien
    // IMPORTANT: Créer dans SVG (pas dans g) pour survivre aux re-renders
    // Mais appliquer la même transformation que g pour que les coordonnées correspondent
    let tempGroup = svg.select<SVGGElement>("g.temp-edge-group");
    if (tempGroup.empty()) {
      tempGroup = svg.append("g").attr("class", "temp-edge-group");
      console.log("🆕 Created new temp group in SVG");
    } else {
      console.log("♻️ Reusing existing temp group from SVG");
    }

    // Synchroniser la transformation du tempGroup avec celle de g
    const currentTransform = transformRef.current;
    tempGroup.attr("transform", currentTransform.toString());

    // Create nodes and node labels
    const handleInternalNodeClick = createNodeClickHandler({
      isEdgeModeActive,
      edgeDragState,
      setEdgeDragState,
      setShowEdgeTypeSelector,
      setSelectedNodeData,
      setShowNodePanel,
      getAvailableEdgeTypes,
      onCreateEdge,
      onNodeClick,
    });

    const node = createNodes(g, data.nodes, nodeRadius, selectedNodeId, nodeColorMap, handleInternalNodeClick, onNodeDoubleClick);
    const nodeLabels = createNodeLabels(g, data.nodes, nodeRadius, selectedNodeId, showLabels);

    // Add drag behavior with edge mode support
    if (enableDrag) {
      const drag = createDragBehavior({
        isEdgeModeActive,
        tempGroup,
        simulation,
        nodeRadius,
        data,
        nodeColorMap,
        svgElement: svgRef.current,
        setEdgeDragState,
        getAvailableEdgeTypes,
        setShowEdgeTypeSelector,
      });

      node.call(drag);
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
    edgeDragState,
    onCreateEdge,
    getAvailableEdgeTypes,
    setEdgeDragState,
    setShowEdgeTypeSelector,
    setSelectedNodeData,
    setShowNodePanel,
    setTransform,
    transformRef,
    simulationRef,
    zoomBehaviorRef,
    dragStartPosRef,
    clickThreshold,
  ]);

  return (
    <div className={`relative h-full w-full ${className}`}>
      <div ref={containerRef} className="relative w-full h-full">
        <svg ref={svgRef} width={dimensions.width} height={dimensions.height} className="bg-gray-50" style={{ touchAction: "none" }} />

        {/* Zoom Controls */}
        {enableZoom && <ZoomControls onZoomIn={handleZoomIn} onZoomOut={handleZoomOut} onFitToScreen={handleFitToScreen} onReset={handleReset} />}

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
