import * as d3 from "d3";
import { GraphNode, GraphData, EdgeTypeConstraint } from "../types";

interface CreateDragBehaviorParams {
  isEdgeModeActive: boolean;
  tempGroup: d3.Selection<SVGGElement, unknown, null, undefined>;
  simulation: d3.Simulation<GraphNode, undefined>;
  nodeRadius: number;
  data: GraphData;
  setEdgeDragState: (state: { sourceNode: GraphNode | null; targetNode: GraphNode | null; isDrawing: boolean }) => void;
  getAvailableEdgeTypes: (source: GraphNode | null, target: GraphNode | null) => EdgeTypeConstraint[];
  setShowEdgeTypeSelector: (show: boolean) => void;
}

export function createDragBehavior({ isEdgeModeActive, tempGroup, simulation, nodeRadius, data, setEdgeDragState, getAvailableEdgeTypes, setShowEdgeTypeSelector }: CreateDragBehaviorParams) {
  return d3.drag<SVGCircleElement, GraphNode>().on("start", function (event, d) {
    console.log("🎯 [DRAG START] Mode lien:", isEdgeModeActive, "Node:", d.id);

    if (isEdgeModeActive) {
      // MODE LIEN: Créer une ligne temporaire
      setEdgeDragState({ sourceNode: d, targetNode: null, isDrawing: true });

      console.log("📍 Source position:", { x: d.x, y: d.y });
      console.log("🖱️ Mouse position:", { x: event.x, y: event.y });

      // Dessiner la ligne temporaire
      const line = tempGroup
        .append("line")
        .attr("class", "temp-edge")
        .attr("x1", d.x!)
        .attr("y1", d.y!)
        .attr("x2", event.x)
        .attr("y2", event.y)
        .attr("stroke", "red") // ROUGE pour debug
        .attr("stroke-width", 10) // LARGE pour debug
        .attr("stroke-dasharray", "5,5")
        .attr("marker-end", "url(#arrow-default)")
        .style("pointer-events", "none")
        .attr("opacity", 1); // Explicite

      console.log("📏 Line element created:", line.node());
      console.log("🎨 TempGroup children count:", tempGroup.node()?.childNodes.length);

      // Utiliser event.on() pour les closures (pattern D3 natif)
      const dragged = (dragEvent: d3.D3DragEvent<SVGCircleElement, GraphNode, GraphNode>) => {
        console.log("🔄 [DRAGGING] Position:", { x: dragEvent.x, y: dragEvent.y });
        line.attr("x2", dragEvent.x).attr("y2", dragEvent.y);
      };

      const ended = (endEvent: d3.D3DragEvent<SVGCircleElement, GraphNode, GraphNode>) => {
        console.log("🏁 [DRAG END] Final position:", { x: endEvent.x, y: endEvent.y });
        line.remove();
        console.log("🗑️ Line removed, children count:", tempGroup.node()?.childNodes.length);

        const targetNode = data.nodes.find((n) => {
          const dx = n.x! - endEvent.x;
          const dy = n.y! - endEvent.y;
          return Math.sqrt(dx * dx + dy * dy) < nodeRadius && n.id !== d.id;
        });

        console.log("🎯 Target node found:", targetNode?.id || "none");

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
      };

      event.on("drag", dragged).on("end", ended);
    } else {
      // MODE NORMAL: Déplacer le nœud
      if (!event.active) simulation.alphaTarget(0.3).restart();
      d.fx = d.x;
      d.fy = d.y;

      const dragged = (dragEvent: d3.D3DragEvent<SVGCircleElement, GraphNode, GraphNode>) => {
        d.fx = dragEvent.x;
        d.fy = dragEvent.y;
      };

      const ended = () => {
        if (!event.active) simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
      };

      event.on("drag", dragged).on("end", ended);
    }
    event.sourceEvent?.stopPropagation();
  });
}
