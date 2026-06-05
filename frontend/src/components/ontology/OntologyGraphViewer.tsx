import React, { useMemo } from "react";
import { GraphViewer, GraphData } from "@/components/common/GraphViewer";
import { Issue } from "@/types";
import { ONTOLOGY_CONCEPT } from "./types";

interface OntologyGraphViewerProps {
  issues: Issue[];
}

export function OntologyGraphViewer({ issues }: OntologyGraphViewerProps) {
  const graphData: GraphData = useMemo(() => {
    if (!issues || issues.length === 0) return { nodes: [], edges: [] };
    const nodes = issues.slice(0, 10).map((issue, i) => ({
      id: `ticket-${i}`,
      label: issue.title.substring(0, 35),
      type: "concept",
      nodeType: ONTOLOGY_CONCEPT,
      properties: { status: issue.status },
    }));
    const edges = nodes.slice(1).map((node, i) => ({
      id: `edge-${i}`,
      source: nodes[0].id,
      target: node.id,
      label: "relates_to",
      type: "RELATES_TO",
    }));
    return { nodes, edges };
  }, [issues]);

  if (issues.length === 0) return null;

  return (
    <GraphViewer
      data={graphData}
      showLabels={true}
      enableZoom={true}
      enableDrag={true}
      className="w-full h-full"
    />
  );
}
