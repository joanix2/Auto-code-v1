import * as d3 from "d3";
import { GraphNode } from "./types";
import { NODE_LABEL_FONT_SIZE, NODE_LABEL_OFFSET, NODE_LABEL_MAX_LENGTH, DEFAULT_NODE_COLOR, SELECTED_STROKE_WIDTH, DEFAULT_STROKE_WIDTH } from "./constants";

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
  onNodeDoubleClick?: (node: GraphNode) => void,
) => {
  return g
    .append("g")
    .attr("class", "nodes")
    .selectAll("circle")
    .data(nodes)
    .join("circle")
    .attr("r", nodeRadius)
    .attr("fill", (d) => {
      // Conserver la couleur du type, même si sélectionné
      return nodeColorMap[d.type || ""] || DEFAULT_NODE_COLOR;
    })
    .attr("fill-opacity", (d) => (d.id === selectedNodeId ? 1 : 0.9))
    .attr("stroke", (d) => {
      // Toujours utiliser une version plus foncée de la couleur du nœud comme contour
      const nodeColor = nodeColorMap[d.type || ""] || DEFAULT_NODE_COLOR;
      const darkerColor = d3.color(nodeColor)?.darker(0.5).toString() || nodeColor;
      return darkerColor;
    })
    .attr("stroke-width", (d) => (d.id === selectedNodeId ? SELECTED_STROKE_WIDTH : DEFAULT_STROKE_WIDTH))
    .style("cursor", "pointer")
    .style("touch-action", "manipulation") // Allow clicks but prevent double-tap zoom
    .style("user-select", "none") // Prevent text selection during drag
    .style("-webkit-user-select", "none")
    .style("-webkit-tap-highlight-color", "transparent") // Remove tap highlight on mobile
    .style("filter", (d) => (d.id === selectedNodeId ? "drop-shadow(0 0 8px rgba(0, 0, 0, 0.3))" : "none"))
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
 * Détermine si le texte doit être blanc ou noir en fonction de la luminosité de la couleur de fond
 * Utilise la formule de luminosité relative WCAG
 */
const getContrastColor = (backgroundColor: string): string => {
  const color = d3.color(backgroundColor);
  if (!color) return "#000000";

  const rgb = color.rgb();
  // Formule de luminosité relative (WCAG)
  const luminance = (0.299 * rgb.r + 0.587 * rgb.g + 0.114 * rgb.b) / 255;

  // Si la couleur est claire (luminance > 0.5), utiliser du texte noir, sinon blanc
  return luminance > 0.5 ? "#000000" : "#ffffff";
};

/**
 * Creates node label elements (centered on nodes)
 */
export const createNodeLabels = (
  g: d3.Selection<SVGGElement, unknown, null, undefined>,
  nodes: GraphNode[],
  nodeRadius: number,
  selectedNodeId: string | null,
  showLabels: boolean,
  nodeColorMap: Record<string, string>,
) => {
  if (!showLabels) return null;

  return g
    .append("g")
    .attr("class", "node-labels")
    .selectAll("text")
    .data(nodes)
    .join("text")
    .attr("font-size", NODE_LABEL_FONT_SIZE)
    .attr("font-weight", (d) => (d.id === selectedNodeId ? "bold" : "normal"))
    .attr("fill", (d) => {
      // Déterminer la couleur du texte en fonction de la couleur de fond du nœud
      const nodeColor = nodeColorMap[d.type || ""] || DEFAULT_NODE_COLOR;
      return getContrastColor(nodeColor);
    })
    .attr("text-anchor", "middle")
    .attr("dominant-baseline", "central") // Centre verticalement le texte
    .text((d) => {
      // Tronquer le texte si plus de NODE_LABEL_MAX_LENGTH caractères
      const label = d.label || "";
      return label.length > NODE_LABEL_MAX_LENGTH ? label.substring(0, NODE_LABEL_MAX_LENGTH) + "..." : label;
    })
    .style("pointer-events", "none")
    .style("user-select", "none");
};

/**
 * Updates node positions on simulation tick
 */
export const updateNodePositions = (
  node: d3.Selection<d3.BaseType | SVGCircleElement, GraphNode, SVGGElement, unknown>,
  nodeLabels: d3.Selection<d3.BaseType | SVGTextElement, GraphNode, SVGGElement, unknown> | null,
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
