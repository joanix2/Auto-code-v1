/**
 * Language Detail Page — visualize a language's M3 graph and manage its elements.
 */

import { useEffect, useState, useCallback } from "react";
import { useParams, Link } from "react-router-dom";
import { ArrowLeft, Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { GraphViewer } from "@/components/common/GraphViewer";
import type { GraphData, GraphNode, GraphEdge } from "@/components/common/GraphViewer";
import { languageService, type Language, type LanguageGraph } from "@/services/languageService";

const NODE_COLORS: Record<string, string> = {
  Sort: "#4CAF50",
  Op: "#2196F3",
  Equation: "#FF9800",
  Rule: "#F44336",
  ConditionalRule: "#E91E63",
  Strategy: "#9C27B0",
  Invariant: "#607D8B",
};

const ALL_TYPES = ["Sort", "Op", "Equation", "Rule", "ConditionalRule", "Strategy", "Invariant"];
const DEFAULT_SORTS = ["string", "int", "bool"];

export function LanguageDetailPage() {
  const { langId } = useParams<{ langId: string }>();
  const [language, setLanguage] = useState<Language | null>(null);
  const [graphData, setGraphData] = useState<GraphData>({ nodes: [], edges: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function loadGraph() {
    if (!langId) return;
    try {
      setLoading(true);
      const data: LanguageGraph = await languageService.getGraph(langId);
      setLanguage(data.language);

      const nodes: GraphNode[] = data.nodes.map((n) => ({
        id: n.id,
        label: n.name,
        type: n.label,
        properties: { description: n.description || "", ...n },
      }));

      const nodeIds = new Set(nodes.map((n) => n.id));
      const edges: GraphEdge[] = data.edges
        .filter((e) => nodeIds.has(e.source) && nodeIds.has(e.target))
        .map((e) => ({ id: e.id, source: e.source, target: e.target, label: e.type, type: e.type }));

      setGraphData({ nodes, edges });
      setError(null);
    } catch (err) {
      setError("Failed to load language graph");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { loadGraph(); }, [langId]);

  const handleCreateNode = useCallback(async (type: string, name: string) => {
    if (!langId) return;
    try {
      if (type === "Sort") {
        await languageService.createSort(langId, { name });
      } else if (type === "Op") {
        await languageService.createOp(langId, { name, result_sort: "string" });
      } else if (type === "Equation") {
        await languageService.createEquation(langId, { name, lhs: name, rhs: "" });
      } else if (type === "Rule") {
        await languageService.createRule(langId, { name, lhs: name, rhs: "" });
      } else if (type === "Invariant") {
        await languageService.createInvariant(langId, { name, condition: "" });
      }
      loadGraph();
    } catch (err) {
      console.error(`Failed to create ${type}`, err);
    }
  }, [langId]);

  if (loading) return <div className="p-6">Chargement...</div>;
  if (error) return <div className="p-6 text-red-500">{error}</div>;
  if (!language) return <div className="p-6">Language not found</div>;

  return (
    <div className="absolute inset-0 flex flex-col">
      {/* Header */}
      <div className="flex items-center gap-3 px-4 py-2 bg-white border-b z-10">
        <Link to="/development/languages">
          <Button variant="ghost" size="sm"><ArrowLeft className="w-4 h-4" /></Button>
        </Link>
        <h1 className="font-bold">{language.name}</h1>
        <span className="text-sm text-gray-400">
          {language.node_count} nodes · {language.edge_count} edges
        </span>
      </div>

      {/* Legend + quick-add */}
      <div className="flex flex-wrap items-center gap-3 px-4 py-2 bg-white border-b z-10">
        {ALL_TYPES.map((type) => (
          <div key={type} className="flex items-center gap-1 text-sm">
            <span className="inline-block w-3 h-3 rounded-full" style={{ backgroundColor: NODE_COLORS[type] }} />
            <span>{type}</span>
            <button
              className="ml-1 text-gray-400 hover:text-gray-600"
              onClick={() => {
                const name = prompt(`${type} name:`);
                if (name) handleCreateNode(type, name);
              }}
            >
              <Plus className="w-3 h-3" />
            </button>
          </div>
        ))}
      </div>

      {/* Graph */}
      <div className="flex-1 relative">
        <GraphViewer
          data={graphData}
          nodeColorMap={NODE_COLORS}
          showLabels={true}
          enableZoom={true}
          enableDrag={true}
        />
      </div>
    </div>
  );
}
