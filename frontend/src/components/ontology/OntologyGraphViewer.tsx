import React, { useMemo } from "react";
import { GraphViewer, GraphData } from "@/components/common/GraphViewer";
import { Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Issue } from "@/types";
import { ONTOLOGY_CONCEPT } from "./types";

interface OntologyGraphViewerProps {
  issues: Issue[];
}

export function OntologyGraphViewer({ issues }: OntologyGraphViewerProps) {
  const [graphData, setGraphData] = React.useState<GraphData>(() =>
    issues.length > 0
      ? {
          nodes: issues.slice(0, 10).map((issue, i) => ({
            id: `ticket-${i}`,
            label: issue.title.substring(0, 35),
            type: "concept",
            nodeType: ONTOLOGY_CONCEPT,
            properties: { status: issue.status },
          })),
          edges: [],
        }
      : { nodes: [], edges: [] }
  );

  const addNode = () => {
    const name = prompt("Nom du concept :");
    if (!name) return;
    setGraphData((prev) => ({
      ...prev,
      nodes: [...prev.nodes, { id: `node-${Date.now()}`, label: name, type: "concept", nodeType: ONTOLOGY_CONCEPT }],
    }));
  };

  if (graphData.nodes.length === 0) {
    return (
      <div className="flex items-center justify-center h-full flex-col space-y-4 text-gray-400">
        <p className="text-lg font-medium">Graphe d'ontologie vide</p>
        <p className="text-sm">Ajoutez des concepts manuellement ou créez des tickets</p>
        <Button size="sm" onClick={addNode}>
          <Plus className="h-4 w-4 mr-1" /> Ajouter un concept
        </Button>
      </div>
    );
  }

  return (
    <GraphViewer
      data={graphData}
      showLabels={true}
      enableZoom={true}
      enableDrag={true}
      className="w-full h-full"
      onBackgroundClick={addNode}
    />
  );
}

