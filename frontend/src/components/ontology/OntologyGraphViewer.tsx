import React, { useState } from "react";
import { GraphViewer, GraphData } from "@/components/common/GraphViewer";
import { Issue } from "@/types";
import { ONTOLOGY_CONCEPT } from "./types";

interface OntologyGraphViewerProps {
  issues: Issue[];
}

export function OntologyGraphViewer({ issues }: OntologyGraphViewerProps) {
  const [graphData, setGraphData] = useState<GraphData>(() => {
    if (issues.length === 0) return { nodes: [], edges: [] };
    return {
      nodes: issues.slice(0, 10).map((issue, i) => ({
        id: `ticket-${i}`,
        label: issue.title.substring(0, 35),
        type: "concept",
        nodeType: ONTOLOGY_CONCEPT,
      })),
      edges: [],
    };
  });

  return (
    <div className="h-full">
      <GraphViewer
        data={graphData}
        showLabels={true}
        enableZoom={true}
        enableDrag={true}
        className="w-full h-full"
        onBackgroundClick={() => {
          const name = prompt("Nom du concept :");
          if (!name) return;
          setGraphData((prev) => ({
            ...prev,
            nodes: [...prev.nodes, { id: `node-${Date.now()}`, label: name, type: "concept", nodeType: ONTOLOGY_CONCEPT }],
          }));
        }}
        onAddNode={() => {
          const name = prompt("Nom du concept :");
          if (!name) return;
          setGraphData((prev) => ({
            ...prev,
            nodes: [...prev.nodes, { id: `node-${Date.now()}`, label: name, type: "concept", nodeType: ONTOLOGY_CONCEPT }],
          }));
        }}
      />
    </div>
  );
}
