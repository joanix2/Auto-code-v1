import React, { useState } from "react";
import { GraphViewer, GraphData } from "@/components/common/GraphViewer";
import { Button } from "@/components/ui/button";
import { Plus } from "lucide-react";

interface ArchitectureGraphViewerProps {
  architectureName?: string;
}

export function ArchitectureGraphViewer({ architectureName }: ArchitectureGraphViewerProps) {
  const [graphData, setGraphData] = useState<GraphData>({ nodes: [], edges: [] });

  const addNode = () => {
    const name = prompt("Nom du nœud :");
    if (!name) return;
    const newNode = {
      id: `node-${Date.now()}`,
      label: name,
      type: "component",
    };
    setGraphData((prev) => ({ ...prev, nodes: [...prev.nodes, newNode] }));
  };

  if (graphData.nodes.length === 0) {
    return (
      <div className="flex items-center justify-center h-full flex-col space-y-4 text-gray-400">
        <p className="text-lg font-medium">Graphe vide</p>
        <p className="text-sm">Ajoutez des nœuds pour modéliser l'architecture</p>
        <Button size="sm" onClick={addNode}>
          <Plus className="h-4 w-4 mr-1" /> Ajouter un nœud
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
