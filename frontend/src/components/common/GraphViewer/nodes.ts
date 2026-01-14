import * as d3 from "d3";
import { GraphNode } from "./types";
import {
  NODE_LABEL_FONT_SIZE,
  NODE_LABEL_OFFSET,
  DEFAULT_NODE_COLOR,
  SELECTED_NODE_COLOR,
  SELECTED_NODE_STROKE_COLOR,
  DEFAULT_NODE_STROKE_COLOR,
  SELECTED_STROKE_WIDTH,
  DEFAULT_STROKE_WIDTH,
} from "./constants";

/**
 * Creates node (circle) elements
 */
export const createNodes = (
  g: d3.Selection<SVGGElement, unknown, null, undefined>,
  nodes: GraphNode[],
  nodeRadius: number,
  selectedNodeId: string | null,
  nodeColorMap: Record<string, string>,
  onNodeClick?: (node: GraphNode) => void,
  onNodeDoubleClick?: (node: GraphNode) => void
) => {
  return g
    .append("g")
    .attr("class", "nodes")
    .selectAll("circle")
    .data(nodes)
    .join("circle")
    .attr("r", nodeRadius)
    .attr("fill", (d) => {
      if (d.id === selectedNodeId) return SELECTED_NODE_COLOR;
      return nodeColorMap[d.type || ""] || DEFAULT_NODE_COLOR;
    })
    .attr("stroke", (d) => (d.id === selectedNodeId ? SELECTED_NODE_STROKE_COLOR : DEFAULT_NODE_STROKE_COLOR))
    .attr("stroke-width", (d) => (d.id === selectedNodeId ? SELECTED_STROKE_WIDTH : DEFAULT_STROKE_WIDTH))
    .style("cursor", "pointer")
    .style("touch-action", "none") // Prevent browser touch handling
    .style("user-select", "none") // Prevent text selection during drag
    .style("-webkit-user-select", "none")
    .style("-webkit-tap-highlight-color", "transparent") // Remove tap highlight on mobile
    .on("click", (event, d) => {
      event.stopPropagation();
      if (onNodeClick) onNodeClick(d);
    })
    .on("dblclick", (event, d) => {
      event.stopPropagation();
      if (onNodeDoubleClick) onNodeDoubleClick(d);
    });
};

/**
 * Creates node label elements
 */
export const createNodeLabels = (g: d3.Selection<SVGGElement, unknown, null, undefined>, nodes: GraphNode[], nodeRadius: number, selectedNodeId: string | null, showLabels: boolean) => {
  if (!showLabels) return null;

  return g
    .append("g")
    .attr("class", "node-labels")
    .selectAll("text")
    .data(nodes)
    .join("text")
    .attr("font-size", NODE_LABEL_FONT_SIZE)
    .attr("font-weight", (d) => (d.id === selectedNodeId ? "bold" : "normal"))
    .attr("fill", "#1f2937")
    .attr("text-anchor", "middle")
    .attr("dy", nodeRadius + NODE_LABEL_OFFSET)
    .text((d) => d.label)
    .style("pointer-events", "none")
    .style("user-select", "none");
};

/**
 * Updates node positions on simulation tick
 */
export const updateNodePositions = (
  node: d3.Selection<d3.BaseType | SVGCircleElement, GraphNode, SVGGElement, unknown>,
  nodeLabels: d3.Selection<d3.BaseType | SVGTextElement, GraphNode, SVGGElement, unknown> | null
) => {
  node.attr("cx", (d) => d.x!).attr("cy", (d) => d.y!);

  if (nodeLabels) {
    nodeLabels.attr("x", (d) => d.x!).attr("y", (d) => d.y!);
  }
};

/**
 * Adds drag behavior to nodes
 */
export const addDragBehavior = (node: d3.Selection<d3.BaseType | SVGCircleElement, GraphNode, SVGGElement, unknown>, simulation: d3.Simulation<GraphNode, undefined>) => {
  const drag = d3
    .drag<SVGCircleElement, GraphNode>()
    .subject((event, d) => {
      // Ensure proper subject for touch events
      console.log("[DRAG] Subject called", {
        eventType: event.type,
        sourceEventType: event.sourceEvent?.type,
        nodeId: d.id,
        position: { x: d.x, y: d.y },
      });
      return { x: d.x!, y: d.y! };
    })
    .on("start", (event, d) => {
      console.log("[DRAG] Start", {
        nodeId: d.id,
        eventType: event.type,
        sourceEventType: event.sourceEvent?.type,
        active: event.active,
        position: { x: d.x, y: d.y },
        eventPosition: { x: event.x, y: event.y },
      });

      if (!event.active) simulation.alphaTarget(0.3).restart();
      d.fx = d.x;
      d.fy = d.y;

      // Prevent zoom behavior from interfering
      if (event.sourceEvent) {
        console.log("[DRAG] Stopping propagation on", event.sourceEvent.type);
        event.sourceEvent.stopPropagation();

        // Prevent default touch behavior (scrolling, zooming)
        if (event.sourceEvent.type.startsWith("touch")) {
          console.log("[DRAG] Preventing default for touch event");
          event.sourceEvent.preventDefault();
        }
      }
    })
    .on("drag", (event, d) => {
      console.log("[DRAG] Dragging", {
        nodeId: d.id,
        eventType: event.type,
        sourceEventType: event.sourceEvent?.type,
        newPosition: { x: event.x, y: event.y },
        delta: {
          dx: event.x - (d.fx || d.x!),
          dy: event.y - (d.fy || d.y!),
        },
      });

      d.fx = event.x;
      d.fy = event.y;

      // Prevent zoom behavior from interfering
      if (event.sourceEvent) {
        event.sourceEvent.stopPropagation();
        if (event.sourceEvent.type.startsWith("touch")) {
          event.sourceEvent.preventDefault();
        }
      }
    })
    .on("end", (event, d) => {
      console.log("[DRAG] End", {
        nodeId: d.id,
        eventType: event.type,
        sourceEventType: event.sourceEvent?.type,
        active: event.active,
        finalPosition: { x: d.x, y: d.y },
      });

      if (!event.active) simulation.alphaTarget(0);
      d.fx = null;
      d.fy = null;
    });

  console.log("[DRAG] Drag behavior attached to", node.size(), "nodes");
  node.call(drag);
};
