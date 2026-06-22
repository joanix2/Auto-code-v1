/**
 * M3 Page — visualize and interact with the rewriting-logic M3 graph.
 *
 * Displays the 7 Neo4j node types (:Sort, :Op, :Equation, :Rule,
 * :ConditionalRule, :Strategy, :Invariant) as a D3.js force graph.
 */

import { useEffect, useState } from "react";
import { GraphViewer } from "@/components/common/GraphViewer";
import type { GraphData, GraphNode, GraphEdge } from "@/components/common/GraphViewer";
import { m3Service, type M3GraphData } from "@/services/m3Service";

/** Distinct colors for each of the 7 M3 node labels */
const NODE_COLORS: Record<string, string> = {
  Sort: "#4CAF50",
  Op: "#2196F3",
  Equation: "#FF9800",
  Rule: "#F44336",
  ConditionalRule: "#E91E63",
  Strategy: "#9C27B0",
  Invariant: "#607D8B",
};

const M3_LABELS = ["Sort", "Op", "Equation", "Rule", "ConditionalRule", "Strategy", "Invariant"];

export function M3Page() {
  const [graphData, setGraphData] = useState<GraphData>({ nodes: [], edges: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        setLoading(true);
        const data: M3GraphData = await m3Service.getGraph();

        const nodes: GraphNode[] = data.nodes.map((n) => ({
          id: n.id,
          label: `${n.name}`,
          type: n.label,
          properties: {
            description: n.description || "",
            kind: n.label,
            ...Object.fromEntries(Object.entries(n).filter(([k]) => !["id", "label", "name", "description"].includes(k))),
          },
        }));

        const nodeIds = new Set(nodes.map((n) => n.id));
        const edges: GraphEdge[] = data.edges
          .filter((e) => nodeIds.has(e.source) && nodeIds.has(e.target))
          .map((e) => ({
            id: e.id,
            source: e.source,
            target: e.target,
            label: e.type,
            type: e.type,
          }));

        setGraphData({ nodes, edges });
        setError(null);
      } catch (err) {
        console.error("Failed to load M3 graph:", err);
        setError("Impossible de charger le graphe M3");
      } finally {
        setLoading(false);
      }
    }

    load();
  }, []);

  const handleNodeClick = (node: GraphNode) => {
    console.log("Node clicked:", node);
  };

  const handleBackgroundClick = () => {
    // deselect
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-lg">Chargement du graphe M3...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-red-500">{error}</div>
      </div>
    );
  }

  return (
    <div className="absolute inset-0 flex flex-col">
      {/* Legend */}
      <div className="flex flex-wrap gap-3 px-4 py-2 bg-white border-b z-10">
        {M3_LABELS.map((label) => (
          <div key={label} className="flex items-center gap-1.5 text-sm">
            <span
              className="inline-block w-3 h-3 rounded-full"
              style={{ backgroundColor: NODE_COLORS[label] }}
            />
            <span>{label}</span>
          </div>
        ))}
      </div>

      {/* Graph */}
      <div className="flex-1 relative">
        <GraphViewer
          data={graphData}
          onNodeClick={handleNodeClick}
          onBackgroundClick={handleBackgroundClick}
          nodeColorMap={NODE_COLORS}
          showLabels={true}
          enableZoom={true}
          enableDrag={true}
        />
      </div>
    </div>
  );
}
