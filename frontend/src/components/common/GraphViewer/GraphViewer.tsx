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
  edgeTypes = [],
  onCreateEdge,
  onAddNode,
  onCreateNode,
}) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const dimensions = useDimensions(containerRef, width, height);
  const clickThreshold = 5;
  const untitledCounter = useRef(0);

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
    mode,
    setMode,
    edgeDragState,
    setEdgeDragState,
    showEdgeTypeSelector,
    setShowEdgeTypeSelector,
    prompt,
    setPrompt,
    messages,
    setMessages,
    setTransform,
  } = state;

  const edgeModeRef = useRef(mode === "edge");
  edgeModeRef.current = mode === "edge";
  const modeRef = useRef(mode);
  modeRef.current = mode;

  // Hook pour la gestion du mode lien
  const {
    getAvailableEdgeTypes,
    handleEdgeTypeSelected: baseHandleEdgeTypeSelected,
  } = useEdgeMode({
    mode,
    setMode,
    edgeDragState,
    setEdgeDragState,
    edgeTypes,
    existingEdges: data.edges,
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
    setMessages([...messages, { role: "user", text: prompt }]);
    setPrompt("");
    // TODO: appeler l'API LLM et ajouter la réponse
    setTimeout(() => {
      setMessages(prev => [...prev, { role: "assistant", text: "✅ Graphe modifié" }]);
    }, 500);
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

    const svg = d3.select(svgRef.current);
    svg.selectAll(".graph-container").remove();
    svg.selectAll("defs").remove();

    // Create container group for zoom/pan (MUST be created first)
    const g = svg.append("g").attr("class", "graph-container");

    // Déduploquer les nœuds par id pour éviter les doublons
    const hasNodes = data.nodes.length > 0;
    const dedupedNodes = hasNodes
      ? data.nodes.filter((node, index, self) => index === self.findIndex((n) => n.id === node.id))
      : [];

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

      const tempGroup = svg.select<SVGGElement>("g.temp-edge-group");
      if (!tempGroup.empty()) {
        tempGroup.attr("transform", newTransform.toString());
      }
    }, modeRef);
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

    // Background click handler (deselect in move, create node in node mode)
    background
      .on("pointerdown", (event) => {
        dragStartPosRef.current = { x: event.clientX, y: event.clientY };
      })
      .on("pointerup", (event) => {
      if (!dragStartPosRef.current) return;
      const dx = Math.abs(event.clientX - dragStartPosRef.current.x);
      const dy = Math.abs(event.clientY - dragStartPosRef.current.y);
      if (dx < clickThreshold && dy < clickThreshold) {
        if (modeRef.current === "node" && onCreateNode) {
          const svgEl = svgRef.current;
          if (svgEl) {
            const pt = svgEl.createSVGPoint();
            pt.x = event.clientX;
            pt.y = event.clientY;
            const ctm = svgEl.getScreenCTM()?.inverse();
            if (ctm) {
              const p = pt.matrixTransform(ctm);
              untitledCounter.current += 1;
              onCreateNode({
                id: `node-${Date.now()}`,
                label: `untitled-${untitledCounter.current}`,
                type: "Sort",
                properties: {},
                x: p.x,
                y: p.y,
              });
            }
          }
        } else {
          setSelectedNodeData(null);
          setShowNodePanel(false);
          onBackgroundClick?.();
        }
      }
      dragStartPosRef.current = null;
    });

    // Create arrow markers
    createArrowMarkers(svg, nodeRadius);

    // Node click handler (declare BEFORE usage in createNodes)
    const handleInternalNodeClick = createNodeClickHandler({
      modeRef, edgeDragState, setEdgeDragState, setShowEdgeTypeSelector,
      setSelectedNodeData, setShowNodePanel, getAvailableEdgeTypes,
      onCreateEdge, onNodeClick, onDeleteNode,
    });

    let simulation: d3.Simulation<GraphNode, undefined> | null = null;
    let link: d3.Selection<d3.BaseType | SVGGElement, GraphEdge, SVGGElement, unknown> | null = null;
    let edgeLabels: d3.Selection<SVGTextElement, GraphEdge, SVGGElement, unknown> | null = null;
    let node: d3.Selection<SVGCircleElement, GraphNode, SVGGElement, unknown> | null = null;
    let nodeLabels: d3.Selection<SVGTextElement, GraphNode, SVGGElement, unknown> | null = null;

    if (hasNodes) {
      simulation = createSimulation(dedupedNodes, data.edges, dimensions.width, dimensions.height, nodeRadius);
      simulationRef.current = simulation;

      link = createEdges(g, data.edges, edgeColorMap, onEdgeClick);
      edgeLabels = createEdgeLabels(g, data.edges, showLabels);

      node = createNodes(g, dedupedNodes, nodeRadius, selectedNodeId, nodeColorMap, handleInternalNodeClick, onNodeDoubleClick);
      nodeLabels = createNodeLabels(g, dedupedNodes, nodeRadius, selectedNodeId, showLabels, nodeColorMap);
    }

    // Créer un groupe pour le nœud fantôme et la ligne temporaire en mode lien
    let tempGroup = svg.select<SVGGElement>("g.temp-edge-group");
    if (tempGroup.empty()) {
      tempGroup = svg.append("g").attr("class", "temp-edge-group");
    }
    const currentTransform = transformRef.current;
    tempGroup.attr("transform", currentTransform.toString());

    if (hasNodes && node) {
      // Add drag behavior with edge mode support
      if (enableDrag && simulation) {
        const drag = createDragBehavior({
          edgeModeRef, tempGroup, simulation, nodeRadius, data, nodeColorMap,
          svgElement: svgRef.current, setEdgeDragState,
          getAvailableEdgeTypes, setShowEdgeTypeSelector, onCreateEdge,
        });
        node.call(drag);
      }

      // Update positions on simulation tick
      simulation!.on("tick", () => {
        if (link && edgeLabels) updateEdgePositions(link, edgeLabels, nodeRadius);
        if (node && nodeLabels) updateNodePositions(node, nodeLabels);
      });
    }

    // Apply initial transform
    svg.call(zoom.transform, transformRef.current);

    return () => {
      if (simulation) simulation.stop();
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
        {enableZoom && <ZoomControls onZoomIn={handleZoomIn} onZoomOut={handleZoomOut} onFitToScreen={handleFitToScreen} onReset={handleReset} mode={mode} onModeChange={setMode} />}

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
          <div className="absolute inset-0 flex items-center justify-center text-gray-400 pointer-events-none">
            <p>Cliquez sur "Ajouter" ou sur l'arrière-plan pour créer un nœud</p>
          </div>
        )}

        {/* Graph Toolbar - Barre de prompt LLM en bas */}
        <GraphToolbar prompt={prompt} onPromptChange={setPrompt} onSendPrompt={handleSendPrompt} messages={messages} />
      </div>
    </div>
  );
};

export default GraphViewer;
