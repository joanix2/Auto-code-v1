import * as d3 from "d3";
import { GraphEdge, SimulationEdge } from "../types";
import { EDGE_STROKE_WIDTH, EDGE_STROKE_OPACITY, EDGE_LABEL_FONT_SIZE, EDGE_LABEL_OFFSET, DEFAULT_EDGE_COLOR, GRAPH_BACKGROUND_COLOR } from "./constants";

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
 * Creates edge labels with background to hide the line
 */
export const createEdgeLabels = (g: d3.Selection<SVGGElement, unknown, null, undefined>, edges: GraphEdge[], showLabels: boolean) => {
  if (!showLabels) return null;

  const labelGroup = g.append("g").attr("class", "edge-labels").selectAll("g").data(edges).join("g").attr("class", "edge-label-group");

  // Ajouter un rectangle en arrière-plan pour masquer le segment (même couleur que le fond du graphe)
  labelGroup.append("rect").attr("fill", GRAPH_BACKGROUND_COLOR).attr("stroke", "none").attr("rx", 2).attr("ry", 2);

  // Ajouter le texte par-dessus le rectangle
  labelGroup
    .append("text")
    .attr("font-size", EDGE_LABEL_FONT_SIZE)
    .attr("fill", "#666")
    .attr("text-anchor", "middle")
    .attr("dominant-baseline", "central")
    .text((d) => d.label || "");

  return labelGroup;
};

/**
 * Updates edge positions on simulation tick
 */
export const updateEdgePositions = (
  link: d3.Selection<d3.BaseType | SVGLineElement, GraphEdge, SVGGElement, unknown>,
  edgeLabels: d3.Selection<d3.BaseType | SVGGElement, GraphEdge, SVGGElement, unknown> | null,
) => {
  link
    .attr("x1", (d: SimulationEdge) => d.source.x!)
    .attr("y1", (d: SimulationEdge) => d.source.y!)
    .attr("x2", (d: SimulationEdge) => d.target.x!)
    .attr("y2", (d: SimulationEdge) => d.target.y!);

  if (edgeLabels) {
    edgeLabels.attr("transform", (d: SimulationEdge) => {
      // Calculer l'angle de l'edge
      const dx = d.target.x! - d.source.x!;
      const dy = d.target.y! - d.source.y!;
      const angle = Math.atan2(dy, dx) * (180 / Math.PI);

      // Position du centre de l'edge
      const x = (d.source.x! + d.target.x!) / 2;
      const y = (d.source.y! + d.target.y!) / 2;

      // Normaliser l'angle pour que le texte soit toujours lisible (pas à l'envers)
      const normalizedAngle = angle > 90 || angle < -90 ? angle + 180 : angle;

      return `translate(${x}, ${y}) rotate(${normalizedAngle})`;
    });

    // Mettre à jour la taille du rectangle en fonction du texte
    edgeLabels.each(function () {
      const group = d3.select(this);
      const text = group.select("text");
      const rect = group.select("rect");

      // Obtenir les dimensions du texte
      const bbox = (text.node() as SVGTextElement)?.getBBox();
      if (bbox) {
        const padding = 4;
        rect
          .attr("x", bbox.x - padding)
          .attr("y", bbox.y - padding / 2)
          .attr("width", bbox.width + padding * 2)
          .attr("height", bbox.height + padding);
      }
    });
  }
};
