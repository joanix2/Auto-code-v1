import React, { useEffect, useState, useCallback } from "react";
import { useParams } from "react-router-dom";
import { Metamodel } from "@/types/metamodel";
import { metamodelService } from "@/services/metamodelService";
import { conceptService, ConceptCreate } from "@/services/conceptService";
import { Database, Plus } from "lucide-react";
import { useToast } from "@/components/ui/use-toast";
import { GraphViewer, CreateNodeModal } from "@/components/common/GraphViewer";
import type { GraphData, GraphNode, GraphEdge, NodeTypeConfig } from "@/components/common/GraphViewer";
import { Button } from "@/components/ui/button";
import { ConceptForm } from "@/components/development/metamodels/ConceptForm";
import { AttributeForm } from "@/components/development/metamodels/AttributeForm";
import { RelationForm } from "@/components/development/metamodels/RelationForm";

export function MetamodelDetails() {
  const { id } = useParams<{ id: string }>();
  const { toast } = useToast();
  const [metamodel, setMetamodel] = useState<Metamodel | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const [isCreateNodeOpen, setIsCreateNodeOpen] = useState(false);

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

      // Charger les concepts réels depuis l'API
      const concepts = await conceptService.getByMetamodel(id);

      const nodes: GraphNode[] = concepts.map((concept) => ({
        id: concept.id,
        label: concept.name,
        type: "concept",
        properties: {
          description: concept.description || "",
          attributes: [],
        },
      }));

      // TODO: Charger les vraies relations entre concepts depuis l'API
      const edges: GraphEdge[] = [];

      setGraphData({ nodes, edges });
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
  };

  const handleDeleteNode = async (node: GraphNode) => {
    try {
      await conceptService.delete(node.id);

      // Retirer le nœud du graphe local
      setGraphData((prev: GraphData) => ({
        nodes: prev.nodes.filter((n) => n.id !== node.id),
        edges: prev.edges.filter((e) => e.source !== node.id && e.target !== node.id),
      }));

      toast({
        title: "Concept supprimé",
        description: `Le concept "${node.label}" a été supprimé`,
      });

      setSelectedNode(null);
    } catch (error) {
      console.error("Error deleting concept:", error);
      toast({
        title: "Erreur",
        description: "Impossible de supprimer le concept",
        variant: "destructive",
      });
    }
  };

  const handleUpdateConcept = async (conceptData: { name: string; description: string }, nodeId: string) => {
    try {
      // Mettre à jour le concept via l'API
      const updatedConcept = await conceptService.update(nodeId, {
        name: conceptData.name,
        description: conceptData.description,
      });

      console.log("📦 Concept retourné par le backend:", updatedConcept);

      // Mettre à jour le nœud dans le graphe local
      setGraphData((prev: GraphData) => ({
        nodes: prev.nodes.map((node) =>
          node.id === nodeId
            ? {
                ...node,
                label: updatedConcept.name,
                properties: {
                  ...node.properties,
                  description: updatedConcept.description || "",
                },
              }
            : node,
        ),
        edges: prev.edges,
      }));

      toast({
        title: "Concept mis à jour",
        description: `Le concept "${conceptData.name}" a été mis à jour`,
      });
    } catch (error) {
      console.error("Error updating concept:", error);
      toast({
        title: "Erreur",
        description: "Impossible de mettre à jour le concept",
        variant: "destructive",
      });
      throw error; // Re-throw pour que le formulaire puisse gérer l'erreur
    }
  };

  // Fonction de rendu du formulaire pour le GraphNodePanel
  const renderConceptForm = (node: GraphNode, isEditing: boolean, onCancelEdit: () => void) => {
    // Utiliser une key pour forcer React à recréer le composant quand les données changent
    const formKey = `${node.id}-${node.label}-${node.properties?.description || ""}`;

    return (
      <ConceptForm
        key={formKey}
        initialData={{
          name: node.label,
          description: (node.properties?.description as string) || "",
        }}
        edit={isEditing}
        onSubmit={async (data) => {
          await handleUpdateConcept(data, node.id);
          onCancelEdit(); // Sortir du mode édition après la sauvegarde
        }}
        onCancel={onCancelEdit}
      />
    );
  };

  // Fonction de rendu pour les attributs (Data Properties)
  const renderAttributeForm = (node: GraphNode, isEditing: boolean, onCancelEdit: () => void) => {
    const formKey = `${node.id}-${node.label}-${node.properties?.description || ""}-${node.properties?.dataType || ""}`;

    return (
      <AttributeForm
        key={formKey}
        initialData={{
          name: node.label,
          description: (node.properties?.description as string) || "",
          dataType: (node.properties?.dataType as string) || "",
        }}
        edit={isEditing}
        onSubmit={async (data) => {
          await handleUpdateConcept(data, node.id);
          onCancelEdit();
        }}
        onCancel={onCancelEdit}
      />
    );
  };

  // Fonction de rendu pour les relations (Object Properties)
  const renderRelationForm = (node: GraphNode, isEditing: boolean, onCancelEdit: () => void) => {
    const formKey = `${node.id}-${node.label}-${node.properties?.description || ""}-${node.properties?.sourceType || ""}-${node.properties?.targetType || ""}`;

    return (
      <RelationForm
        key={formKey}
        initialData={{
          name: node.label,
          description: (node.properties?.description as string) || "",
          sourceType: (node.properties?.sourceType as string) || "",
          targetType: (node.properties?.targetType as string) || "",
        }}
        edit={isEditing}
        onSubmit={async (data) => {
          await handleUpdateConcept(data, node.id);
          onCancelEdit();
        }}
        onCancel={onCancelEdit}
      />
    );
  };

  // Map des formulaires par type de nœud
  const nodeForms = {
    concept: renderConceptForm,
    attribute: renderAttributeForm,
    relation: renderRelationForm,
  };

  const handleCreateNode = async (nodeData: { name: string; description: string; type: "concept" | "attribute" | "relation" }) => {
    if (!id) return;

    try {
      // Appeler l'API pour créer le concept
      const createData: ConceptCreate = {
        name: nodeData.name,
        description: nodeData.description,
        graph_id: id,
        // Position aléatoire pour commencer (sera mise à jour par l'utilisateur)
        x_position: Math.random() * 400 + 100,
        y_position: Math.random() * 400 + 100,
      };

      const createdConcept = await conceptService.create(createData);

      // Ajouter le nouveau nœud au graphe local
      const newNode: GraphNode = {
        id: createdConcept.id,
        label: createdConcept.name,
        type: nodeData.type,
        properties: {
          description: createdConcept.description || "",
          attributes: [],
        },
      };

      setGraphData((prev) => ({
        nodes: [...prev.nodes, newNode],
        edges: prev.edges,
      }));

      toast({
        title: nodeData.type === "concept" ? "Concept créé" : nodeData.type === "attribute" ? "Attribut créé" : "Relation créée",
        description: `${nodeData.type === "concept" ? "Concept" : nodeData.type === "attribute" ? "Attribut" : "Relation"} "${nodeData.name}" créé avec succès`,
      });

      setIsCreateNodeOpen(false);
    } catch (error) {
      console.error("Error creating concept:", error);
      toast({
        title: "Erreur",
        description: "Impossible de créer le concept",
        variant: "destructive",
      });
    }
  };

  const nodeColorMap = {
    concept: "#3b82f6", // Bleu pour les concepts (classes)
    attribute: "#10b981", // Vert pour les attributs (data properties)
    relation: "#ec4899", // Rose pour les relations (object properties)
    entity: "#f59e0b", // Orange pour les entités
  };

  const edgeColorMap = {
    association: "#6366f1",
    inheritance: "#ec4899",
    composition: "#8b5cf6",
  };

  // Configuration des types de nœuds pour le modal
  const nodeTypeConfigs: NodeTypeConfig[] = [
    {
      value: "concept",
      label: "Concept",
      color: nodeColorMap.concept,
      placeholder: "Ex: Vehicle, Person, Product...",
      descriptionPlaceholder: "Décrivez ce concept...",
    },
    {
      value: "attribute",
      label: "Attribut",
      color: nodeColorMap.attribute,
      placeholder: "Ex: name, age, price...",
      descriptionPlaceholder: "Décrivez cet attribut...",
    },
    {
      value: "relation",
      label: "Relation",
      color: nodeColorMap.relation,
      placeholder: "Ex: possède, appartientÀ, contient...",
      descriptionPlaceholder: "Décrivez cette relation...",
    },
  ];

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
    <div className="flex h-full w-full relative overflow-hidden">
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
          onDeleteNode={handleDeleteNode}
          forms={nodeForms}
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

      {/* Bouton flottant pour créer un nœud */}
      <Button onClick={() => setIsCreateNodeOpen(true)} className="fixed bottom-6 right-6 h-14 w-14 rounded-full shadow-lg hover:shadow-xl transition-shadow z-50" size="icon">
        <Plus className="h-6 w-6" />
      </Button>

      {/* Modale de création de nœud */}
      <CreateNodeModal
        open={isCreateNodeOpen}
        onOpenChange={setIsCreateNodeOpen}
        onCreateNode={handleCreateNode}
        nodeTypes={nodeTypeConfigs}
        title="Créer un nouveau nœud"
        description="Ajoutez un concept, un attribut ou une relation à votre métamodèle."
      />
    </div>
  );
}
