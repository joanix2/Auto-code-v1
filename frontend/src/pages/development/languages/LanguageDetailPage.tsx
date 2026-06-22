/**
 * Language Detail Page — visualize a language's M3 graph and manage its elements.
 */

import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
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
