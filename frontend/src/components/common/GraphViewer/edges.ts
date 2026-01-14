import * as d3 from "d3";
import { GraphEdge, SimulationEdge } from "./types";
import { EDGE_STROKE_WIDTH, EDGE_STROKE_OPACITY, EDGE_LABEL_FONT_SIZE, EDGE_LABEL_OFFSET, DEFAULT_EDGE_COLOR } from "./constants";

/**
 * Creates edge (link) elements
 */
export const createEdges = (g: d3.Selection<SVGGElement, unknown, null, undefined>, edges: GraphEdge[], edgeColorMap: Record<string, string>, onEdgeClick?: (edge: GraphEdge) => void) => {
  return g
    .append("g")
    .attr("class", "links")
    .selectAll("line")
    .data(edges)
    .join("line")
    .attr("stroke", (d) => edgeColorMap[d.type || ""] || DEFAULT_EDGE_COLOR)
    .attr("stroke-width", EDGE_STROKE_WIDTH)
    .attr("stroke-opacity", EDGE_STROKE_OPACITY)
    .attr("marker-end", "url(#arrowhead)")
    .style("cursor", onEdgeClick ? "pointer" : "default")
    .on("click", (event, d) => {
      if (onEdgeClick) {
        event.stopPropagation();
        onEdgeClick(d);
      }
    });
};

/**
 * Creates edge label elements
 */
export const createEdgeLabels = (g: d3.Selection<SVGGElement, unknown, null, undefined>, edges: GraphEdge[], showLabels: boolean) => {
  if (!showLabels) return null;

  return g
    .append("g")
    .attr("class", "edge-labels")
    .selectAll("text")
    .data(edges)
    .join("text")
    .attr("font-size", EDGE_LABEL_FONT_SIZE)
    .attr("fill", "#666")
    .attr("text-anchor", "middle")
    .attr("dy", EDGE_LABEL_OFFSET)
    .text((d) => d.label || "");
};

/**
 * Updates edge positions on simulation tick
 */
export const updateEdgePositions = (
  link: d3.Selection<d3.BaseType | SVGLineElement, GraphEdge, SVGGElement, unknown>,
  edgeLabels: d3.Selection<d3.BaseType | SVGTextElement, GraphEdge, SVGGElement, unknown> | null
) => {
  link
    .attr("x1", (d: SimulationEdge) => d.source.x!)
    .attr("y1", (d: SimulationEdge) => d.source.y!)
    .attr("x2", (d: SimulationEdge) => d.target.x!)
    .attr("y2", (d: SimulationEdge) => d.target.y!);

  if (edgeLabels) {
    edgeLabels.attr("x", (d: SimulationEdge) => (d.source.x! + d.target.x!) / 2).attr("y", (d: SimulationEdge) => (d.source.y! + d.target.y!) / 2);
  }
};
