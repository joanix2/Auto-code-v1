import React, { useEffect, useState, useCallback } from "react";
import { useParams } from "react-router-dom";
import { Metamodel } from "@/types/metamodel";
import { metamodelService } from "@/services/metamodelService";
import { Database } from "lucide-react";
import { useToast } from "@/components/ui/use-toast";
import { GraphViewer } from "@/components/common/GraphViewer";
import type { GraphData, GraphNode, GraphEdge } from "@/components/common/GraphViewer";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { Edit, Trash2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";

export function MetamodelDetail() {
  const { id } = useParams<{ id: string }>();
  const { toast } = useToast();
  const [metamodel, setMetamodel] = useState<Metamodel | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const [selectedNodeData, setSelectedNodeData] = useState<GraphNode | null>(null);
  const [showNodePanel, setShowNodePanel] = useState(false);

  // Sample graph data - À remplacer par les vraies données du métamodèle
  const [graphData, setGraphData] = useState<GraphData>({
    nodes: [],
    edges: [],
  });

  const loadMetamodel = useCallback(async () => {
    if (!id) return;

    try {
      setLoading(true);
      const data = await metamodelService.getById(id);
      setMetamodel(data);

      // Générer des données de graphe exemple basées sur le métamodèle
      // TODO: Charger les vraies données du graphe depuis l'API
      const sampleNodes: GraphNode[] = [];
      const sampleEdges: GraphEdge[] = [];

      // Créer des nœuds exemples basés sur le nombre de concepts
      for (let i = 0; i < Math.min(data.concepts || 5, 10); i++) {
        sampleNodes.push({
          id: `concept-${i}`,
          label: `Concept ${i + 1}`,
          type: "concept",
          properties: {
            description: `Description du concept ${i + 1}`,
            attributes: [],
          },
        });
      }

      // Créer des relations exemples
      for (let i = 0; i < Math.min(data.relations || 3, sampleNodes.length - 1); i++) {
        sampleEdges.push({
          id: `relation-${i}`,
          source: sampleNodes[i].id,
          target: sampleNodes[i + 1].id,
          label: `relation_${i + 1}`,
          type: "association",
        });
      }

      setGraphData({ nodes: sampleNodes, edges: sampleEdges });
    } catch (error) {
      toast({
        title: "Erreur",
        description: "Impossible de charger le métamodèle.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  }, [id, toast]);

  useEffect(() => {
    loadMetamodel();
  }, [loadMetamodel]);

  const handleNodeClick = (node: GraphNode) => {
    setSelectedNode(node.id);
    setSelectedNodeData(node);
    setShowNodePanel(true);
  };

  const handleNodeDoubleClick = (node: GraphNode) => {
    // TODO: Ouvrir modal d'édition du nœud
    toast({
      title: "Édition du nœud",
      description: `Édition de ${node.label} - Fonctionnalité à venir`,
    });
  };

  const handleEdgeClick = (edge: GraphEdge) => {
    // TODO: Afficher les propriétés de la relation
    toast({
      title: "Relation sélectionnée",
      description: `${edge.label || "Relation"} - Fonctionnalité à venir`,
    });
  };

  const handleBackgroundClick = () => {
    setSelectedNode(null);
    setSelectedNodeData(null);
    setShowNodePanel(false);
  };

  const nodeColorMap = {
    concept: "#3b82f6",
    attribute: "#10b981",
    entity: "#f59e0b",
  };

  const edgeColorMap = {
    association: "#6366f1",
    inheritance: "#ec4899",
    composition: "#8b5cf6",
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="h-64 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  if (!metamodel) {
    return (
      <div className="p-6">
        <p>Métamodèle non trouvé</p>
      </div>
    );
  }

  return (
    <div className="flex h-full w-full">
      {/* Graphe en plein écran */}
      {graphData.nodes.length > 0 ? (
        <GraphViewer
          data={graphData}
          nodeRadius={30}
          onNodeClick={handleNodeClick}
          onNodeDoubleClick={handleNodeDoubleClick}
          onEdgeClick={handleEdgeClick}
          onBackgroundClick={handleBackgroundClick}
          selectedNodeId={selectedNode}
          nodeColorMap={nodeColorMap}
          edgeColorMap={edgeColorMap}
          showLabels={true}
          enableZoom={true}
          enableDrag={true}
          className="w-full h-full"
        />
      ) : (
        <div className="flex items-center justify-center h-full">
          <div className="text-center">
            <Database className="h-16 w-16 text-muted-foreground mx-auto mb-4" />
            <p className="text-muted-foreground mb-4">Aucun concept défini</p>
          </div>
        </div>
      )}

      {/* Node Properties Panel */}
      <Sheet open={showNodePanel} onOpenChange={setShowNodePanel}>
        <SheetContent>
          <SheetHeader>
            <SheetTitle>Propriétés du nœud</SheetTitle>
            <SheetDescription>{selectedNodeData?.label}</SheetDescription>
          </SheetHeader>

          {selectedNodeData && (
            <div className="mt-6 space-y-4">
              <div>
                <h3 className="font-semibold mb-2">Informations</h3>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-sm text-muted-foreground">ID:</span>
                    <span className="text-sm font-mono">{selectedNodeData.id}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-muted-foreground">Label:</span>
                    <span className="text-sm">{selectedNodeData.label}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-muted-foreground">Type:</span>
                    <Badge variant="secondary">{selectedNodeData.type}</Badge>
                  </div>
                </div>
              </div>

              <div>
                <h3 className="font-semibold mb-2">Propriétés</h3>
                {selectedNodeData.properties && Object.keys(selectedNodeData.properties).length > 0 ? (
                  <div className="space-y-2">
                    {Object.entries(selectedNodeData.properties).map(([key, value]) => (
                      <div key={key} className="flex justify-between">
                        <span className="text-sm text-muted-foreground">{key}:</span>
                        <span className="text-sm">{String(value)}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground">Aucune propriété</p>
                )}
              </div>

              <div className="pt-4 space-y-2">
                <Button variant="outline" className="w-full">
                  <Edit className="h-4 w-4 mr-2" />
                  Modifier
                </Button>
                <Button variant="destructive" className="w-full">
                  <Trash2 className="h-4 w-4 mr-2" />
                  Supprimer
                </Button>
              </div>
            </div>
          )}
        </SheetContent>
      </Sheet>
    </div>
  );
}
