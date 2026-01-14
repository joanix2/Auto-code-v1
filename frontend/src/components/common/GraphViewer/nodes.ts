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
    .style("touch-action", "manipulation") // Allow clicks but prevent double-tap zoom
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
  let dragStartTime = 0;
  let dragStartX = 0;
  let dragStartY = 0;
  let hasMoved = false;

  const drag = d3
    .drag<SVGCircleElement, GraphNode>()
    .subject((event, d) => {
      // Ensure proper subject for touch events
      return { x: d.x!, y: d.y! };
    })
    .on("start", (event, d) => {
      dragStartTime = Date.now();
      dragStartX = event.x;
      dragStartY = event.y;
      hasMoved = false;

      if (!event.active) simulation.alphaTarget(0.3).restart();
      d.fx = d.x;
      d.fy = d.y;

      // Prevent zoom behavior from interfering
      if (event.sourceEvent) {
        event.sourceEvent.stopPropagation();

        // Only preventDefault on touch if we're sure it's a drag, not on start
        // This allows click events to fire on mobile
      }
    })
    .on("drag", (event, d) => {
      const dx = Math.abs(event.x - dragStartX);
      const dy = Math.abs(event.y - dragStartY);

      // Consider it a drag if moved more than 5 pixels
      if (dx > 5 || dy > 5) {
        hasMoved = true;

        // Now we can safely preventDefault to avoid scrolling
        if (event.sourceEvent && event.sourceEvent.type.startsWith("touch")) {
          event.sourceEvent.preventDefault();
        }
      }

      d.fx = event.x;
      d.fy = event.y;

      // Prevent zoom behavior from interfering
      if (event.sourceEvent) {
        event.sourceEvent.stopPropagation();
      }
    })
    .on("end", (event, d) => {
      if (!event.active) simulation.alphaTarget(0);

      // If it was a tap/click (not a drag), restore position
      const duration = Date.now() - dragStartTime;
      if (!hasMoved && duration < 200) {
        // It's a tap/click, not a drag - don't fix position
        d.fx = null;
        d.fy = null;
      } else {
        // It was a drag - keep position fixed briefly then release
        d.fx = null;
        d.fy = null;
      }
    });

  node.call(drag);
};
