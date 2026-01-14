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
    .attr("refX", nodeRadius + 8)
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
    .attr("refX", nodeRadius + 8)
    .attr("refY", 0)
    .attr("markerWidth", 6)
    .attr("markerHeight", 6)
    .attr("orient", "auto")
    .append("path")
    .attr("d", "M0,-5L10,0L0,5")
    .attr("fill", "#3b82f6");
};
