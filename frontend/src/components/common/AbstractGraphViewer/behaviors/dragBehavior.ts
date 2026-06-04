import * as d3 from "d3";
import { GraphNode, GraphData } from "../types";
import { M3EdgeType } from "@/types/dsl-config";

interface CreateDragBehaviorParams {
  isEdgeModeActive: boolean;
  tempGroup: d3.Selection<SVGGElement, unknown, null, undefined>;
  simulation: d3.Simulation<GraphNode, undefined>;
  nodeRadius: number;
  data: GraphData;
  nodeColorMap: Record<string, string>;
  svgElement: SVGSVGElement; // Ajout pour obtenir les coordonnées transformées
  setEdgeDragState: (state: { sourceNode: GraphNode | null; targetNode: GraphNode | null; isDrawing: boolean }) => void;
  getAvailableEdgeTypes: (source: GraphNode | null, target: GraphNode | null) => M3EdgeType[];
  setShowEdgeTypeSelector: (show: boolean) => void;
  onCreateEdge?: (source: string, target: string, type: string) => void;
}

export function createDragBehavior({
  isEdgeModeActive,
  tempGroup,
  simulation,
  nodeRadius,
  data,
  nodeColorMap,
  svgElement,
  setEdgeDragState,
  getAvailableEdgeTypes,
  setShowEdgeTypeSelector,
  onCreateEdge,
}: CreateDragBehaviorParams) {
  // Variables pour stocker les éléments temporaires en closure
  let tempLine: d3.Selection<SVGLineElement, unknown, null, undefined> | null = null;
  let tempNode: d3.Selection<SVGCircleElement, unknown, null, undefined> | null = null;

  return d3
    .drag<SVGCircleElement, GraphNode>()
    .subject((event, d) => ({ x: d.x!, y: d.y! }))
    .on("start", function (event, d) {
      if (isEdgeModeActive) {
        // MODE LIEN: Créer une ligne temporaire et un nœud fantôme
        setEdgeDragState({ sourceNode: d, targetNode: null, isDrawing: true });

        // Nettoyer tous les éléments temporaires existants
        tempGroup.selectAll("line.temp-edge").remove();
        tempGroup.selectAll("circle.temp-node").remove();
        tempGroup.selectAll("text.temp-label").remove();

        // Déterminer les types de nœuds cibles possibles
        const availableEdgeTypes = getAvailableEdgeTypes(d, null);

        // Prendre le premier type cible disponible ou un type par défaut
        const targetNodeType = availableEdgeTypes.length > 0 ? availableEdgeTypes[0].targetNodeTypes[0] : d.type || "";
        const nodeColor = nodeColorMap[targetNodeType] || nodeColorMap[d.type || ""] || "#64748b";

        // Créer le nœud fantôme avec le style du type cible (INVISIBLE)
        const ghostRadius = nodeRadius * 0.7; // 70% de la taille normale
        tempNode = tempGroup
          .append("circle")
          .attr("class", "temp-node")
          .attr("cx", d.x!)
          .attr("cy", d.y!)
          .attr("r", ghostRadius)
          .attr("fill", nodeColor)
          .attr("fill-opacity", 0) // INVISIBLE: opacité à 0
          .attr("stroke", "none") // Pas de bordure
          .style("pointer-events", "none")
          .raise(); // Au-dessus de tout

        // Note: Le label temporaire est supprimé pour une interface plus minimaliste
        // Seule la ligne avec la flèche est affichée

        // Dessiner la ligne temporaire DANS le groupe transformé
        tempLine = tempGroup
          .append("line")
          .attr("class", "temp-edge")
          .attr("x1", d.x!)
          .attr("y1", d.y!)
          .attr("x2", d.x!) // Commence au même point
          .attr("y2", d.y!)
          .attr("stroke", "#999") // Gris comme les edges normaux
          .attr("stroke-width", 2)
          .attr("stroke-dasharray", "5,3") // Pointillés pour montrer que c'est temporaire
          .attr("marker-end", "url(#arrowhead-temp)") // Flèche grise avec pointe à la souris
          .style("pointer-events", "none")
          .attr("opacity", 0.8)
          .raise(); // S'assurer qu'elle est au-dessus

        // CRITIQUE: Élever le groupe ENTIER au-dessus de tous les autres éléments
        tempGroup.raise();
      } else {
        // MODE NORMAL: Déplacer le nœud
        if (!event.active) simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
      }
      event.sourceEvent?.stopPropagation();
    })
    .on("drag", function (event, d) {
      if (isEdgeModeActive && tempLine && tempNode) {
        // MODE LIEN: Mettre à jour la ligne, le nœud fantôme et le label

        // Obtenir les coordonnées de la souris dans le SVG
        const point = d3.pointer(event.sourceEvent, svgElement);

        // Obtenir la transformation actuelle du tempGroup
        const transform = d3.zoomTransform(svgElement);

        // Appliquer la transformation inverse pour obtenir les coordonnées dans l'espace du graphe
        const graphX = (point[0] - transform.x) / transform.k;
        const graphY = (point[1] - transform.y) / transform.k;

        tempLine.attr("x2", graphX).attr("y2", graphY);
        tempNode.attr("cx", graphX).attr("cy", graphY);

        // Note: Le label n'est plus mis à jour car il a été supprimé
      } else if (!isEdgeModeActive) {
        // MODE NORMAL: Déplacer le nœud
        d.fx = event.x;
        d.fy = event.y;
      }
    })
    .on("end", function (event, d) {
      if (isEdgeModeActive && tempLine && tempNode) {
        // MODE LIEN: Finaliser

        // Obtenir les coordonnées de la souris dans le SVG
        const point = d3.pointer(event.sourceEvent, svgElement);

        // Obtenir la transformation actuelle
        const transform = d3.zoomTransform(svgElement);

        // Appliquer la transformation inverse pour obtenir les coordonnées dans l'espace du graphe
        const graphX = (point[0] - transform.x) / transform.k;
        const graphY = (point[1] - transform.y) / transform.k;

        // Trouver le nœud cible avec les coordonnées transformées
        const targetNode = data.nodes.find((n) => {
          const dx = n.x! - graphX;
          const dy = n.y! - graphY;
          return Math.sqrt(dx * dx + dy * dy) < nodeRadius && n.id !== d.id;
        });

        // Retirer la ligne, le nœud fantôme et le label
        tempLine.remove();
        tempNode.remove();
        tempGroup.selectAll("text.temp-label").remove();
        tempLine = null;
        tempNode = null;

        if (targetNode) {
          setEdgeDragState({ sourceNode: d, targetNode, isDrawing: false });
          const availableTypes = getAvailableEdgeTypes(d, targetNode);

          if (availableTypes.length === 1) {
            // Si une seule relation possible, créer directement sans afficher la popup
            if (onCreateEdge) {
              onCreateEdge(d.id, targetNode.id, availableTypes[0].name);
            }
            setEdgeDragState({ sourceNode: null, targetNode: null, isDrawing: false });
          } else if (availableTypes.length > 1) {
            // Si plusieurs relations possibles, afficher la popup de sélection
            setShowEdgeTypeSelector(true);
          } else {
            // Aucune relation possible
            setEdgeDragState({ sourceNode: null, targetNode: null, isDrawing: false });
          }
        } else {
          setEdgeDragState({ sourceNode: null, targetNode: null, isDrawing: false });
        }
      } else if (!isEdgeModeActive) {
        // MODE NORMAL: Libérer le nœud
        if (!event.active) simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
      }
    });
}
