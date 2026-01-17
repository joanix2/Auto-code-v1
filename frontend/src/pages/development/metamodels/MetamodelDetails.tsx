import React, { useEffect, useState, useCallback } from "react";
import { useParams } from "react-router-dom";
import { Metamodel } from "@/types/metamodel";
import { metamodelService } from "@/services/metamodelService";
import { conceptService, ConceptCreate, type Concept } from "@/services/conceptService";
import { attributeService, type AttributeCreate as AttributeCreateType, type Attribute } from "@/services/attributeService";
import { relationshipService, type Relationship, type RelationshipCreate } from "@/services/relationshipService";
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

      // Charger les attributs du métamodèle
      const attributes = await attributeService.getByMetamodel(id);

      // Charger les relations du métamodèle
      const relationships = await relationshipService.getByMetamodel(id, true);

      const conceptNodes: GraphNode[] = concepts.map((concept) => ({
        id: concept.id,
        label: concept.name,
        type: "concept",
        properties: {
          description: concept.description || "",
          attributes: [],
        },
      }));

      // Créer les nœuds pour les attributs standalone (sans concept_id)
      const attributeNodes: GraphNode[] = attributes
        .filter((attr) => !attr.concept_id)
        .map((attr) => ({
          id: attr.id,
          label: attr.name,
          type: "attribute",
          properties: {
            description: attr.description || "",
            dataType: attr.type || "string",
            isRequired: attr.is_required || false,
            isUnique: attr.is_unique || false,
          },
        }));

      // Créer les arêtes pour visualiser les relations
      const edges: GraphEdge[] = relationships.map((rel) => ({
        id: `edge-${rel.id}`,
        source: rel.source_concept_id,
        target: rel.target_concept_id,
        label: rel.name, // Utiliser le nom de la relation
        type: "relation",
      }));

      const nodes: GraphNode[] = [...conceptNodes, ...attributeNodes];

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
      // Appeler le bon service en fonction du type de nœud
      if (node.type === "concept") {
        await conceptService.delete(node.id);
      } else if (node.type === "attribute") {
        await attributeService.delete(node.id);
      } else if (node.type === "relation") {
        await relationshipService.delete(node.id);
      } else {
        throw new Error(`Delete not implemented for node type: ${node.type}`);
      }

      // Retirer le nœud du graphe local
      setGraphData((prev: GraphData) => ({
        nodes: prev.nodes.filter((n) => n.id !== node.id),
        edges: prev.edges.filter((e) => e.source !== node.id && e.target !== node.id),
      }));

      const nodeTypeLabel = node.type === "concept" ? "Concept" : node.type === "attribute" ? "Attribut" : node.type === "relation" ? "Relation" : "Élément";

      toast({
        title: `${nodeTypeLabel} supprimé`,
        description: `Le ${nodeTypeLabel.toLowerCase()} "${node.label}" a été supprimé`,
      });

      setSelectedNode(null);
    } catch (error) {
      console.error(`Error deleting ${node.type}:`, error);
      toast({
        title: "Erreur",
        description: `Impossible de supprimer le ${node.type === "concept" ? "concept" : node.type === "attribute" ? "attribut" : "élément"}`,
        variant: "destructive",
      });
    }
  };

  const handleUpdateNode = async (nodeData: { name: string; description?: string; [key: string]: unknown }, nodeId: string, nodeType: string) => {
    try {
      let updatedNode: Concept | Attribute | Relationship;

      if (nodeType === "concept") {
        // Mettre à jour le concept via l'API
        updatedNode = await conceptService.update(nodeId, {
          name: nodeData.name,
          description: nodeData.description || "",
        });
      } else if (nodeType === "attribute") {
        // Mettre à jour l'attribut via l'API
        const attributeData = nodeData as {
          name: string;
          description?: string;
          dataType?: string;
          isRequired?: boolean;
          isUnique?: boolean;
        };
        updatedNode = await attributeService.update(nodeId, {
          name: attributeData.name,
          description: attributeData.description || "",
          type: attributeData.dataType || "string",
          is_required: attributeData.isRequired || false,
          is_unique: attributeData.isUnique || false,
        });
      } else if (nodeType === "relation") {
        // Mettre à jour la relation via l'API
        const relationData = nodeData as {
          name: string;
          description?: string;
          relationType?: string;
        };
        updatedNode = await relationshipService.update(nodeId, {
          type: relationData.relationType as "is_a" | "has_part" | "has_subclass" | "part_of" | "other",
          description: relationData.description || "",
        });
      } else {
        throw new Error(`Update not implemented for node type: ${nodeType}`);
      }

      console.log(`📦 ${nodeType} retourné par le backend:`, updatedNode);

      // Mettre à jour le nœud dans le graphe local
      setGraphData((prev: GraphData) => ({
        nodes: prev.nodes.map((node) =>
          node.id === nodeId
            ? {
                ...node,
                label: nodeType === "relation" ? node.label : (updatedNode as Concept | Attribute).name,
                properties: {
                  ...node.properties,
                  description: updatedNode.description || "",
                  ...(nodeType === "attribute" && {
                    dataType: (updatedNode as Attribute).type || "string",
                    isRequired: (updatedNode as Attribute).is_required || false,
                    isUnique: (updatedNode as Attribute).is_unique || false,
                  }),
                  ...(nodeType === "relation" && {
                    relationType: (updatedNode as Relationship).type || "other",
                    sourceConceptId: (updatedNode as Relationship).source_concept_id,
                    targetConceptId: (updatedNode as Relationship).target_concept_id,
                  }),
                },
              }
            : node,
        ),
        edges: prev.edges,
      }));

      toast({
        title: `${nodeType === "concept" ? "Concept" : nodeType === "attribute" ? "Attribut" : "Relation"} mis à jour`,
        description: `${nodeType === "concept" ? "Le concept" : nodeType === "attribute" ? "L'attribut" : "La relation"} "${nodeData.name || "sans nom"}" a été mis à jour`,
      });
    } catch (error) {
      console.error(`Error updating ${nodeType}:`, error);
      toast({
        title: "Erreur",
        description: `Impossible de mettre à jour ${nodeType === "concept" ? "le concept" : nodeType === "attribute" ? "l'attribut" : "la relation"}`,
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
        nodeType={node.type}
        initialData={{
          name: node.label,
          description: (node.properties?.description as string) || "",
        }}
        edit={isEditing}
        onSubmit={async (data) => {
          await handleUpdateNode(data, node.id, node.type);
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
        nodeType={node.type}
        initialData={{
          name: node.label,
          description: (node.properties?.description as string) || "",
          dataType: (node.properties?.dataType as string) || "",
          isRequired: (node.properties?.isRequired as boolean) || false,
          isUnique: (node.properties?.isUnique as boolean) || false,
        }}
        edit={isEditing}
        onSubmit={async (data) => {
          await handleUpdateNode(data, node.id, node.type);
          onCancelEdit();
        }}
        onCancel={onCancelEdit}
      />
    );
  };

  // Fonction de rendu pour les relations (Object Properties)
  const renderRelationForm = (node: GraphNode, isEditing: boolean, onCancelEdit: () => void) => {
    const formKey = `${node.id}-${node.label}-${node.properties?.description || ""}-${node.properties?.relationType || ""}-${node.properties?.sourceConceptId || ""}-${node.properties?.targetConceptId || ""}`;

    // Récupérer la liste des concepts pour les SelectFields
    const concepts = graphData.nodes.filter((n) => n.type === "concept").map((n) => ({ id: n.id, label: n.label }));

    return (
      <RelationForm
        key={formKey}
        nodeType={node.type}
        initialData={{
          name: node.label,
          description: (node.properties?.description as string) || "",
          sourceConceptId: (node.properties?.sourceConceptId as string) || "",
          targetConceptId: (node.properties?.targetConceptId as string) || "",
          relationType: (node.properties?.relationType as "is_a" | "has_part" | "has_subclass" | "part_of" | "other") || "other",
        }}
        concepts={concepts}
        edit={isEditing}
        onSubmit={async (data) => {
          await handleUpdateNode(data, node.id, node.type);
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
      let createdNode: Concept | Attribute;
      let newNode: GraphNode;

      if (nodeData.type === "concept") {
        // Create concept
        const createData: ConceptCreate = {
          name: nodeData.name,
          description: nodeData.description,
          graph_id: id,
          x_position: Math.random() * 400 + 100,
          y_position: Math.random() * 400 + 100,
        };

        createdNode = await conceptService.create(createData);

        newNode = {
          id: createdNode.id,
          label: createdNode.name,
          type: "concept",
          properties: {
            description: createdNode.description || "",
            attributes: [],
          },
        };
      } else if (nodeData.type === "attribute") {
        // Create attribute
        // Attribute is created without concept_id (standalone) and can be linked to a concept later
        const createData: AttributeCreateType = {
          name: nodeData.name,
          description: nodeData.description,
          graph_id: id,
          type: "string", // Default type
          is_required: false,
          is_unique: false,
          x_position: Math.random() * 400 + 100,
          y_position: Math.random() * 400 + 100,
        };

        createdNode = await attributeService.create(createData);

        newNode = {
          id: createdNode.id,
          label: createdNode.name,
          type: "attribute",
          properties: {
            description: createdNode.description || "",
            dataType: (createdNode as Attribute).type || "string",
            isRequired: (createdNode as Attribute).is_required || false,
            isUnique: (createdNode as Attribute).is_unique || false,
          },
        };
      } else {
        // Relation - création de relation entre deux concepts
        const relationData = nodeData as {
          name: string;
          description: string;
          sourceConceptId?: string;
          targetConceptId?: string;
          relationType?: string;
        };

        if (!relationData.sourceConceptId || !relationData.targetConceptId || !relationData.relationType) {
          toast({
            title: "Informations manquantes",
            description: "Veuillez spécifier le concept source, le concept cible et le type de relation",
            variant: "destructive",
          });
          return;
        }

        const createData: RelationshipCreate = {
          name: relationData.name, // Le nom de la relation
          type: relationData.relationType as "is_a" | "has_part" | "has_subclass" | "part_of" | "other",
          source_concept_id: relationData.sourceConceptId,
          target_concept_id: relationData.targetConceptId,
          description: relationData.description,
          metamodel_id: id,
        };

        const createdRelation = await relationshipService.create(createData);

        // Créer un nœud pour la relation (pour l'affichage dans le graphe)
        newNode = {
          id: createdRelation.id,
          label: createdRelation.name, // Utiliser le nom de la relation
          type: "relation",
          properties: {
            name: createdRelation.name,
            description: createdRelation.description || "",
            relationType: createdRelation.type,
            sourceConceptId: createdRelation.source_concept_id,
            targetConceptId: createdRelation.target_concept_id,
          },
        };

        // Créer également une arête pour visualiser la relation dans le graphe
        const newEdge: GraphEdge = {
          id: `edge-${createdRelation.id}`,
          source: createdRelation.source_concept_id,
          target: createdRelation.target_concept_id,
          label: createdRelation.name, // Utiliser le nom de la relation, pas le type
          type: "relation",
        };

        // Ajouter à la fois le nœud et l'arête
        setGraphData((prev) => ({
          nodes: [...prev.nodes, newNode],
          edges: [...prev.edges, newEdge],
        }));

        toast({
          title: "Relation créée",
          description: `Relation "${createdRelation.type}" créée avec succès`,
        });

        setIsCreateNodeOpen(false);
        return;
      }

      // Add new node to graph
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
      console.error(`Error creating ${nodeData.type}:`, error);
      toast({
        title: "Erreur",
        description: `Impossible de créer ${nodeData.type === "concept" ? "le concept" : nodeData.type === "attribute" ? "l'attribut" : "la relation"}`,
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
        concepts={graphData.nodes.filter((n) => n.type === "concept").map((n) => ({ id: n.id, label: n.label }))}
      />
    </div>
  );
}
