import * as d3 from "d3";
import { GraphEdge, SimulationEdge } from "../types";
import { EDGE_STROKE_WIDTH, EDGE_STROKE_OPACITY, EDGE_LABEL_FONT_SIZE, EDGE_LABEL_OFFSET, DEFAULT_EDGE_COLOR, GRAPH_BACKGROUND_COLOR, DEFAULT_NODE_RADIUS, EDGE_ARROW_OFFSET } from "./constants";

/**
 * Détecte les liens multiples entre les mêmes paires de nœuds
 * et calcule une courbure appropriée pour chaque lien
 */
const calculateEdgeCurvature = (edges: GraphEdge[]): Map<string, number> => {
  // Grouper les edges par paire de nœuds (bidirectionnel)
  const edgeGroups = new Map<string, GraphEdge[]>();

  edges.forEach((edge) => {
    const sourceId = typeof edge.source === "string" ? edge.source : edge.source.id;
    const targetId = typeof edge.target === "string" ? edge.target : edge.target.id;

    // Créer une clé qui représente la paire (normalisée pour les liens bidirectionnels)
    const pairKey = [sourceId, targetId].sort().join("-");

    if (!edgeGroups.has(pairKey)) {
      edgeGroups.set(pairKey, []);
    }
    edgeGroups.get(pairKey)!.push(edge);
  });

  // Assigner une courbure à chaque edge
  const curvatureMap = new Map<string, number>();

  edgeGroups.forEach((groupEdges, pairKey) => {
    if (groupEdges.length === 1) {
      // Un seul lien: pas de courbure
      curvatureMap.set(groupEdges[0].id, 0);
    } else {
      // Plusieurs liens: distribuer les courbures symétriquement
      const count = groupEdges.length;
      groupEdges.forEach((edge, index) => {
        // Distribuer de -maxCurve à +maxCurve
        const maxCurvature = 0.5; // Courbure maximale
        const step = (maxCurvature * 2) / (count - 1);
        const curvature = -maxCurvature + index * step;
        curvatureMap.set(edge.id, curvature);
      });
    }
  });

  return curvatureMap;
};

/**
 * Creates edge (link) elements with curved paths for multiple edges between same nodes
 */
export const createEdges = (g: d3.Selection<SVGGElement, unknown, null, undefined>, edges: GraphEdge[], edgeColorMap: Record<string, string>, onEdgeClick?: (edge: GraphEdge) => void) => {
  // Calculer les courbures pour chaque edge
  const curvatureMap = calculateEdgeCurvature(edges);

  return g
    .append("g")
    .attr("class", "links")
    .selectAll("path")
    .data(edges)
    .join("path")
    .attr("stroke", (d) => edgeColorMap[d.type || ""] || DEFAULT_EDGE_COLOR)
    .attr("stroke-width", EDGE_STROKE_WIDTH)
    .attr("stroke-opacity", EDGE_STROKE_OPACITY)
    .attr("fill", "none")
    .attr("marker-end", "url(#arrowhead)")
    .attr("data-curvature", (d) => curvatureMap.get(d.id) || 0)
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
  nodeRadius: number = DEFAULT_NODE_RADIUS,
) => {
  // Utiliser des paths courbes au lieu de lignes droites
  link.attr("d", function (d: SimulationEdge) {
    const curvature = parseFloat(d3.select(this).attr("data-curvature") || "0");

    const sourceX = d.source.x!;
    const sourceY = d.source.y!;
    const targetX = d.target.x!;
    const targetY = d.target.y!;

    if (curvature === 0) {
      // Ligne droite - raccourcir aux bords des nœuds
      const dx = targetX - sourceX;
      const dy = targetY - sourceY;
      const dist = Math.sqrt(dx * dx + dy * dy);

      if (dist === 0) return `M ${sourceX},${sourceY} L ${targetX},${targetY}`;

      // Normaliser le vecteur
      const nx = dx / dist;
      const ny = dy / dist;

      // Calculer les points de début et fin ajustés
      const startX = sourceX + nx * nodeRadius;
      const startY = sourceY + ny * nodeRadius;
      const endX = targetX - nx * (nodeRadius + EDGE_ARROW_OFFSET);
      const endY = targetY - ny * (nodeRadius + EDGE_ARROW_OFFSET);

      return `M ${startX},${startY} L ${endX},${endY}`;
    } else {
      // Courbe quadratique - raccourcir aux bords des nœuds
      const midX = (sourceX + targetX) / 2;
      const midY = (sourceY + targetY) / 2;

      const dx = targetX - sourceX;
      const dy = targetY - sourceY;
      const dist = Math.sqrt(dx * dx + dy * dy);

      if (dist === 0) return `M ${sourceX},${sourceY} L ${targetX},${targetY}`;

      // Calculer le vecteur perpendiculaire pour la courbure
      const offsetX = (-dy / dist) * curvature * dist;
      const offsetY = (dx / dist) * curvature * dist;

      // Point de contrôle pour la courbe
      const controlX = midX + offsetX;
      const controlY = midY + offsetY;

      // Pour une courbe quadratique Bézier, la tangente au début (t=0) est dans la direction source->control
      const dxStart = controlX - sourceX;
      const dyStart = controlY - sourceY;
      const distStart = Math.sqrt(dxStart * dxStart + dyStart * dyStart);

      if (distStart === 0) return `M ${sourceX},${sourceY} L ${targetX},${targetY}`;

      const nxStart = dxStart / distStart;
      const nyStart = dyStart / distStart;

      const startX = sourceX + nxStart * nodeRadius;
      const startY = sourceY + nyStart * nodeRadius;

      // Pour une courbe quadratique Bézier, la tangente à la fin (t=1) est dans la direction control->target
      const dxEnd = targetX - controlX;
      const dyEnd = targetY - controlY;
      const distEnd = Math.sqrt(dxEnd * dxEnd + dyEnd * dyEnd);

      if (distEnd === 0) return `M ${sourceX},${sourceY} L ${targetX},${targetY}`;

      const nxEnd = dxEnd / distEnd;
      const nyEnd = dyEnd / distEnd;

      const endX = targetX - nxEnd * (nodeRadius + EDGE_ARROW_OFFSET);
      const endY = targetY - nyEnd * (nodeRadius + EDGE_ARROW_OFFSET);

      return `M ${startX},${startY} Q ${controlX},${controlY} ${endX},${endY}`;
    }
  });

  if (edgeLabels) {
    edgeLabels.attr("transform", (d: SimulationEdge) => {
      // Pour les labels, utiliser la même logique de courbure
      const edgeElement = link.filter((e: GraphEdge) => e.id === d.id).node() as SVGPathElement;
      const curvature = parseFloat(d3.select(edgeElement).attr("data-curvature") || "0");

      const sourceX = d.source.x!;
      const sourceY = d.source.y!;
      const targetX = d.target.x!;
      const targetY = d.target.y!;

      // Position du label au milieu de la courbe
      let x, y;

      if (curvature === 0) {
        // Ligne droite: milieu simple
        x = (sourceX + targetX) / 2;
        y = (sourceY + targetY) / 2;
      } else {
        // Courbe: position sur la courbe quadratique au point t=0.5
        const midX = (sourceX + targetX) / 2;
        const midY = (sourceY + targetY) / 2;

        const dx = targetX - sourceX;
        const dy = targetY - sourceY;
        const dist = Math.sqrt(dx * dx + dy * dy);

        const offsetX = (-dy / dist) * curvature * dist;
        const offsetY = (dx / dist) * curvature * dist;

        const controlX = midX + offsetX;
        const controlY = midY + offsetY;

        // Point sur la courbe quadratique Bézier à t=0.5
        const t = 0.5;
        x = (1 - t) * (1 - t) * sourceX + 2 * (1 - t) * t * controlX + t * t * targetX;
        y = (1 - t) * (1 - t) * sourceY + 2 * (1 - t) * t * controlY + t * t * targetY;
      }

      // Calculer l'angle de l'edge
      const dx = targetX - sourceX;
      const dy = targetY - sourceY;
      const angle = Math.atan2(dy, dx) * (180 / Math.PI);

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
