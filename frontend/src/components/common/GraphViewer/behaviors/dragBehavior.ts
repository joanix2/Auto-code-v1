import * as d3 from "d3";
import { GraphNode, GraphData, EdgeTypeConstraint } from "../types";

interface CreateDragBehaviorParams {
  isEdgeModeActive: boolean;
  tempGroup: d3.Selection<SVGGElement, unknown, null, undefined>;
  simulation: d3.Simulation<GraphNode, undefined>;
  nodeRadius: number;
  data: GraphData;
  nodeColorMap: Record<string, string>;
  svgElement: SVGSVGElement; // Ajout pour obtenir les coordonnées transformées
  setEdgeDragState: (state: { sourceNode: GraphNode | null; targetNode: GraphNode | null; isDrawing: boolean }) => void;
  getAvailableEdgeTypes: (source: GraphNode | null, target: GraphNode | null) => EdgeTypeConstraint[];
  setShowEdgeTypeSelector: (show: boolean) => void;
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
}: CreateDragBehaviorParams) {
  // Variables pour stocker les éléments temporaires en closure
  let tempLine: d3.Selection<SVGLineElement, unknown, null, undefined> | null = null;
  let tempNode: d3.Selection<SVGCircleElement, unknown, null, undefined> | null = null;

  return d3
    .drag<SVGCircleElement, GraphNode>()
    .on("start", function (event, d) {
      console.log("🎯 [DRAG START] Mode lien:", isEdgeModeActive, "Node:", d.id);

      if (isEdgeModeActive) {
        // MODE LIEN: Créer une ligne temporaire et un nœud fantôme
        setEdgeDragState({ sourceNode: d, targetNode: null, isDrawing: true });

        console.log("📍 Source position:", { x: d.x, y: d.y });
        console.log("🖱️ Event subject:", { x: event.subject.x, y: event.subject.y });
        console.log("🎨 TempGroup exists:", !tempGroup.empty(), "Node:", tempGroup.node());

        // Nettoyer tous les éléments temporaires existants
        tempGroup.selectAll("line.temp-edge").remove();
        tempGroup.selectAll("circle.temp-node").remove();
        tempGroup.selectAll("text.temp-label").remove();

        // Déterminer les types de nœuds cibles possibles
        const availableEdgeTypes = getAvailableEdgeTypes(d, null);
        console.log(
          "🔍 Available edge types from source:",
          availableEdgeTypes.map((et) => `${et.edgeType} -> ${et.targetNodeType}`),
        );

        // Prendre le premier type cible disponible ou un type par défaut
        const targetNodeType = availableEdgeTypes.length > 0 ? availableEdgeTypes[0].targetNodeType : d.type || "";
        const nodeColor = nodeColorMap[targetNodeType] || nodeColorMap[d.type || ""] || "#64748b";

        console.log("👻 Creating ghost node with type:", targetNodeType, "color:", nodeColor);

        // Créer le nœud fantôme avec le style du type cible
        const ghostRadius = nodeRadius * 0.7; // 70% de la taille normale
        tempNode = tempGroup
          .append("circle")
          .attr("class", "temp-node")
          .attr("cx", d.x!)
          .attr("cy", d.y!)
          .attr("r", ghostRadius)
          .attr("fill", nodeColor) // Couleur du type cible
          .attr("fill-opacity", 0.6) // Semi-transparent pour montrer que c'est temporaire
          .attr("stroke", "#fff")
          .attr("stroke-width", 2)
          .attr("stroke-dasharray", "4,2") // Pointillés pour indiquer que c'est temporaire
          .style("pointer-events", "none")
          .style("filter", "drop-shadow(0 0 4px rgba(0, 0, 0, 0.3))")
          .raise(); // Au-dessus de tout

        console.log("👻 Ghost node attributes:", {
          cx: tempNode.attr("cx"),
          cy: tempNode.attr("cy"),
          r: tempNode.attr("r"),
          fill: tempNode.attr("fill"),
          stroke: tempNode.attr("stroke"),
        });

        // Ajouter un label temporaire
        const tempLabel = tempGroup
          .append("text")
          .attr("class", "temp-label")
          .attr("x", d.x!)
          .attr("y", d.y! + ghostRadius + 12)
          .attr("text-anchor", "middle")
          .attr("font-size", 10)
          .attr("fill", "#666")
          .attr("opacity", 0.7)
          .text(`→ ${targetNodeType || "?"}`)
          .style("pointer-events", "none");

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

        console.log("📏 Line attributes:", {
          x1: tempLine.attr("x1"),
          y1: tempLine.attr("y1"),
          x2: tempLine.attr("x2"),
          y2: tempLine.attr("y2"),
          stroke: tempLine.attr("stroke"),
        });

        console.log("📏 Line attributes:", {
          x1: tempLine.attr("x1"),
          y1: tempLine.attr("y1"),
          x2: tempLine.attr("x2"),
          y2: tempLine.attr("y2"),
          stroke: tempLine.attr("stroke"),
        });
        console.log("👻 Ghost node created:", tempNode.node(), "Radius:", ghostRadius);
        console.log("🏷️ Label created:", tempLabel.node());
        console.log("🎨 TempGroup children:", tempGroup.node()?.childNodes.length);

        // CRITIQUE: Élever le groupe ENTIER au-dessus de tous les autres éléments
        tempGroup.raise();
        console.log("⬆️ TempGroup raised to top");

        console.log("✅ START: tempLine exists?", !!tempLine, "tempNode exists?", !!tempNode);
      } else {
        // MODE NORMAL: Déplacer le nœud
        if (!event.active) simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
      }
      event.sourceEvent?.stopPropagation();
    })
    .on("drag", function (event, d) {
      console.log("🔄 DRAG event fired! Mode:", isEdgeModeActive, "tempLine:", !!tempLine, "tempNode:", !!tempNode);
      if (isEdgeModeActive && tempLine && tempNode) {
        // MODE LIEN: Mettre à jour la ligne, le nœud fantôme et le label

        // Obtenir les coordonnées de la souris dans le SVG
        const point = d3.pointer(event.sourceEvent, svgElement);

        // Obtenir la transformation actuelle du tempGroup
        const transform = d3.zoomTransform(svgElement);

        // Appliquer la transformation inverse pour obtenir les coordonnées dans l'espace du graphe
        const graphX = (point[0] - transform.x) / transform.k;
        const graphY = (point[1] - transform.y) / transform.k;

        console.log("🔄 [DRAGGING] Mouse:", point, "Graph:", { x: graphX, y: graphY }, "Transform:", { k: transform.k, x: transform.x, y: transform.y });

        tempLine.attr("x2", graphX).attr("y2", graphY);
        tempNode.attr("cx", graphX).attr("cy", graphY);

        // Mettre à jour le label aussi
        const ghostRadius = nodeRadius * 0.7;
        tempGroup
          .select("text.temp-label")
          .attr("x", graphX)
          .attr("y", graphY + ghostRadius + 12);
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

        console.log("🏁 [DRAG END] At graph coords:", { x: graphX, y: graphY });

        // Trouver le nœud cible avec les coordonnées transformées
        const targetNode = data.nodes.find((n) => {
          const dx = n.x! - graphX;
          const dy = n.y! - graphY;
          return Math.sqrt(dx * dx + dy * dy) < nodeRadius && n.id !== d.id;
        });

        console.log("🎯 Target node:", targetNode?.id || "none");

        // Retirer la ligne, le nœud fantôme et le label
        tempLine.remove();
        tempNode.remove();
        tempGroup.selectAll("text.temp-label").remove();
        tempLine = null;
        tempNode = null;
        console.log("🗑️ Line, ghost node and label removed");

        if (targetNode) {
          setEdgeDragState({ sourceNode: d, targetNode, isDrawing: false });
          const availableTypes = getAvailableEdgeTypes(d, targetNode);
          console.log("📋 Available edge types:", availableTypes.length);
          if (availableTypes.length > 0) {
            setShowEdgeTypeSelector(true);
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
