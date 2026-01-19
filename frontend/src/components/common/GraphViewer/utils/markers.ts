import * as d3 from "d3";

/**
 * Creates arrow markers for directed edges
 */
export const createArrowMarkers = (svg: d3.Selection<SVGSVGElement, unknown, null, undefined>, nodeRadius: number) => {
  const defs = svg.append("defs");

  // Default arrow
  defs
    .append("marker")
    .attr("id", "arrowhead")
    .attr("viewBox", "0 -5 10 10")
    .attr("refX", 10) // Pointe exactement au bout du path
    .attr("refY", 0)
    .attr("markerWidth", 6)
    .attr("markerHeight", 6)
    .attr("orient", "auto")
    .append("path")
    .attr("d", "M0,-5L10,0L0,5")
    .attr("fill", "#999");

  // Selected arrow
  defs
    .append("marker")
    .attr("id", "arrowhead-selected")
    .attr("viewBox", "0 -5 10 10")
    .attr("refX", 10) // Pointe exactement au bout du path
    .attr("refY", 0)
    .attr("markerWidth", 6)
    .attr("markerHeight", 6)
    .attr("orient", "auto")
    .append("path")
    .attr("d", "M0,-5L10,0L0,5")
    .attr("fill", "#3b82f6");

  // Temporary edge arrow (inherits color from stroke)
  defs
    .append("marker")
    .attr("id", "arrowhead-temp")
    .attr("viewBox", "0 -5 10 10")
    .attr("refX", 10) // Pointe exactement à la position x2/y2 de la ligne
    .attr("refY", 0)
    .attr("markerWidth", 6)
    .attr("markerHeight", 6)
    .attr("orient", "auto")
    .append("path")
    .attr("d", "M0,-5L10,0L0,5")
    .attr("fill", "#999") // Gris comme les edges normaux
    .attr("stroke", "none");
};
