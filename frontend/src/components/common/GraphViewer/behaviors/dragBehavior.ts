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

        console.log("👻 Ghost node attributes:", {
          cx: tempNode.attr("cx"),
          cy: tempNode.attr("cy"),
          r: tempNode.attr("r"),
          fill: tempNode.attr("fill"),
          stroke: tempNode.attr("stroke"),
        });

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
        console.log("👻 Ghost node created (invisible):", tempNode.node(), "Radius:", ghostRadius);
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

          if (availableTypes.length === 1) {
            // Si une seule relation possible, créer directement sans afficher la popup
            console.log("✨ Single edge type available, creating directly:", availableTypes[0].edgeType);
            if (onCreateEdge) {
              onCreateEdge(d.id, targetNode.id, availableTypes[0].edgeType);
            }
            setEdgeDragState({ sourceNode: null, targetNode: null, isDrawing: false });
          } else if (availableTypes.length > 1) {
            // Si plusieurs relations possibles, afficher la popup de sélection
            console.log("📝 Multiple edge types available, showing selector");
            setShowEdgeTypeSelector(true);
          } else {
            // Aucune relation possible
            console.log("⚠️ No edge types available");
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
