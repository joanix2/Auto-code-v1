import React, { useState } from "react";
import { GraphViewer, GraphData } from "@/components/common/GraphViewer";

interface ArchitectureGraphViewerProps {
  architectureName?: string;
}

export function ArchitectureGraphViewer({ architectureName }: ArchitectureGraphViewerProps) {
  const [graphData, setGraphData] = useState<GraphData>({ nodes: [], edges: [] });

  return (
    <GraphViewer
      data={graphData}
      showLabels={true}
      enableZoom={true}
      enableDrag={true}
      className="w-full h-full"
      onBackgroundClick={() => {
        const name = prompt("Nom du nœud :");
        if (!name) return;
        setGraphData((prev) => ({
          ...prev,
          nodes: [...prev.nodes, { id: `node-${Date.now()}`, label: name, type: "component" }],
        }));
      }}
      onAddNode={() => {
        const name = prompt("Nom du nœud :");
        if (!name) return;
        setGraphData((prev) => ({
          ...prev,
          nodes: [...prev.nodes, { id: `node-${Date.now()}`, label: name, type: "component" }],
        }));
      }}
    />
  );
}
