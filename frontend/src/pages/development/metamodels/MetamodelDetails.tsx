import React, { useEffect, useState, useCallback } from "react";
import { useParams } from "react-router-dom";
import { Metamodel } from "@/types/metamodel";
import { metamodelService } from "@/services/metamodelService";
import { conceptService, ConceptCreate, type Concept } from "@/services/conceptService";
import { attributeService, type AttributeCreate as AttributeCreateType, type Attribute } from "@/services/attributeService";
import { relationshipService, type Relationship, type RelationshipCreate } from "@/services/relationshipService";
import { edgeService } from "@/services/edgeService";
import { Database, Plus } from "lucide-react";
import { useToast } from "@/components/ui/use-toast";
import { GraphViewer, CreateNodeModal, type EdgeTypeConstraint } from "@/components/common/GraphViewer";
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
  const [edgeConstraints, setEdgeConstraints] = useState<EdgeTypeConstraint[]>([]);

  // Sample graph data - À remplacer par les vraies données du métamodèle
  const [graphData, setGraphData] = useState<GraphData>({
    nodes: [],
    edges: [],
  });

  const loadMetamodel = useCallback(async () => {
    if (!id) return;

    try {
      setLoading(true);

      // Charger le graphe complet (nodes + edges + metamodel details) depuis la nouvelle route optimisée
      const graphData = await metamodelService.getGraph(id);

      // Extraire les détails du metamodel depuis la réponse
      setMetamodel(graphData.metamodel); // Charger les contraintes de liens
      const constraints = await metamodelService.getEdgeConstraints(id);
      setEdgeConstraints(constraints);

      // Transformer les nodes du backend au format GraphNode
      const nodes = graphData.nodes.map((node) => ({
        id: node.id,
        label: node.label || node.name,
        type: node.type as "concept" | "attribute" | "relation",
        properties: {
          description: node.description || "",
          ...(node.x && node.y ? { x_position: node.x, y_position: node.y } : {}),
          // Propriétés spécifiques aux Attributes
          ...(node.dataType ? { dataType: node.dataType } : {}),
          ...(node.isRequired !== undefined ? { isRequired: node.isRequired } : {}),
          ...(node.isUnique !== undefined ? { isUnique: node.isUnique } : {}),
          // Propriétés spécifiques aux Relations
          ...(node.relationType ? { relationType: node.relationType } : {}),
        },
      }));

      // Créer un Set des IDs de nœuds existants pour la validation
      const nodeIds = new Set(nodes.map((n) => n.id));

      // Transformer et filtrer les edges du backend au format GraphEdge
      // Ne garder que les edges qui pointent vers des nœuds existants
      const allEdges = graphData.edges.map((edge) => ({
        id: edge.id,
        source: edge.source,
        target: edge.target,
        label: edge.label,
        type: edge.type,
      }));

      const validEdges = allEdges.filter((edge) => {
        const hasValidSource = nodeIds.has(edge.source);
        const hasValidTarget = nodeIds.has(edge.target);

        if (!hasValidSource || !hasValidTarget) {
          console.warn(`⚠️ Edge orphelin ignoré: ${edge.id} (source: ${edge.source}, target: ${edge.target})`);
          return false;
        }
        return true;
      });

      setGraphData({ nodes, edges: validEdges });

      console.log(
        `📊 Graphe chargé: ${nodes.length} noeuds, ${validEdges.length} edges${allEdges.length !== validEdges.length ? ` (${allEdges.length - validEdges.length} edges orphelins ignorés)` : ""}`,
      );
    } catch (error) {
      console.error("Error loading metamodel:", error);
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

  const handleEdgeClick = async (edge: GraphEdge) => {
    // Supprimer directement sans confirmation
    try {
      // Extraire les IDs source et target (peuvent être des strings ou des GraphNode)
      const sourceId = typeof edge.source === "string" ? edge.source : edge.source.id;
      const targetId = typeof edge.target === "string" ? edge.target : edge.target.id;

      // Supprimer l'edge via l'API
      await edgeService.delete(sourceId, targetId, edge.type || "");

      // Retirer l'edge du graphe local et filtrer les edges invalides
      setGraphData((prev: GraphData) => {
        const updatedEdges = prev.edges.filter((e) => e.id !== edge.id);

        // Vérifier que tous les edges restants pointent vers des nœuds existants
        const nodeIds = new Set(prev.nodes.map((n) => n.id));
        const validEdges = updatedEdges.filter((e) => {
          const srcId = typeof e.source === "string" ? e.source : e.source.id;
          const tgtId = typeof e.target === "string" ? e.target : e.target.id;
          return nodeIds.has(srcId) && nodeIds.has(tgtId);
        });

        return {
          nodes: prev.nodes,
          edges: validEdges,
        };
      });

      toast({
        title: "Lien supprimé",
        description: `Le lien "${edge.label || edge.type}" a été supprimé`,
      });
    } catch (error) {
      console.error("Error deleting edge:", error);
      toast({
        title: "Erreur",
        description: "Impossible de supprimer le lien",
        variant: "destructive",
      });
    }
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

  const handleCreateEdge = async (sourceNodeId: string, targetNodeId: string, edgeType: string) => {
    if (!id) return;

    try {
      // Créer l'edge en base de données via l'API
      const createdEdge = await edgeService.create({
        graph_id: id,
        source_id: sourceNodeId,
        target_id: targetNodeId,
        edge_type: edgeType,
      });

      // Ajouter l'edge au graphe local
      const newEdge: GraphEdge = {
        id: createdEdge.id,
        source: sourceNodeId,
        target: targetNodeId,
        label: edgeType,
        type: edgeType,
      };

      setGraphData((prev: GraphData) => ({
        nodes: prev.nodes,
        edges: [...prev.edges, newEdge],
      }));

      toast({
        title: "Lien créé",
        description: `Lien de type "${edgeType}" créé avec succès`,
      });
    } catch (error) {
      console.error("Error creating edge:", error);
      toast({
        title: "Erreur",
        description: "Impossible de créer le lien",
        variant: "destructive",
      });
    }
  };

  const handleUpdateNode = async (nodeData: { name: string; description?: string; [key: string]: unknown }, nodeId: string, nodeType: string, isCreation = false) => {
    try {
      let updatedNode: Concept | Attribute | Relationship;

      if (nodeType === "concept") {
        // Créer ou mettre à jour le concept via l'API
        if (isCreation) {
          updatedNode = await conceptService.create({
            name: nodeData.name,
            description: nodeData.description || "",
            graph_id: id,
            x_position: Math.random() * 400 + 100,
            y_position: Math.random() * 400 + 100,
          });
        } else {
          updatedNode = await conceptService.update(nodeId, {
            name: nodeData.name,
            description: nodeData.description || "",
          });
        }
      } else if (nodeType === "attribute") {
        // Créer ou mettre à jour l'attribut via l'API
        const attributeData = nodeData as {
          name: string;
          description?: string;
          dataType?: string;
          isRequired?: boolean;
          isUnique?: boolean;
        };
        if (isCreation) {
          updatedNode = await attributeService.create({
            name: attributeData.name,
            description: attributeData.description || "",
            graph_id: id,
            type: attributeData.dataType || "string",
            is_required: attributeData.isRequired || false,
            is_unique: attributeData.isUnique || false,
            x_position: Math.random() * 400 + 100,
            y_position: Math.random() * 400 + 100,
          });
        } else {
          updatedNode = await attributeService.update(nodeId, {
            name: attributeData.name,
            description: attributeData.description || "",
            type: attributeData.dataType || "string",
            is_required: attributeData.isRequired || false,
            is_unique: attributeData.isUnique || false,
          });
        }
      } else if (nodeType === "relation") {
        // Créer ou mettre à jour la relation via l'API
        const relationData = nodeData as {
          name: string;
          description?: string;
          relationType?: string;
        };
        if (isCreation) {
          // Les connexions source/target se font via les edges DOMAIN/RANGE, pas directement sur la relation
          updatedNode = await relationshipService.create({
            name: relationData.name,
            type: relationData.relationType as "is_a" | "has_part" | "has_subclass" | "part_of" | "other",
            description: relationData.description || "",
            graph_id: id,
            x_position: Math.random() * 400 + 100,
            y_position: Math.random() * 400 + 100,
          });
        } else {
          updatedNode = await relationshipService.update(nodeId, {
            name: relationData.name,
            type: relationData.relationType as "is_a" | "has_part" | "has_subclass" | "part_of" | "other",
            description: relationData.description || "",
          });
        }
      } else {
        throw new Error(`${isCreation ? "Create" : "Update"} not implemented for node type: ${nodeType}`);
      }

      console.log(`📦 ${nodeType} ${isCreation ? "créé" : "mis à jour"} par le backend:`, updatedNode);

      // Mettre à jour ou ajouter le nœud dans le graphe local
      if (isCreation) {
        // Création : ajouter un nouveau nœud
        const newNode: GraphNode = {
          id: updatedNode.id,
          label: nodeType === "relation" ? (updatedNode as Relationship).name : (updatedNode as Concept | Attribute).name,
          type: nodeType,
          properties: {
            description: updatedNode.description || "",
            ...(nodeType === "attribute" && {
              dataType: (updatedNode as Attribute).type || "string",
              isRequired: (updatedNode as Attribute).is_required || false,
              isUnique: (updatedNode as Attribute).is_unique || false,
            }),
            ...(nodeType === "relation" && {
              relationType: (updatedNode as Relationship).type || "other",
            }),
          },
        };

        setGraphData((prev: GraphData) => ({
          nodes: [...prev.nodes, newNode],
          edges: prev.edges,
        }));
      } else {
        // Mise à jour : modifier le nœud existant
        setGraphData((prev: GraphData) => ({
          nodes: prev.nodes.map((node) =>
            node.id === nodeId
              ? {
                  ...node,
                  label: nodeType === "relation" ? (updatedNode as Relationship).name : (updatedNode as Concept | Attribute).name,
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
                    }),
                  },
                }
              : node,
          ),
          edges: prev.edges,
        }));
      }

      toast({
        title: `${nodeType === "concept" ? "Concept" : nodeType === "attribute" ? "Attribut" : "Relation"} ${isCreation ? "créé" : "mis à jour"}`,
        description: `${nodeType === "concept" ? "Le concept" : nodeType === "attribute" ? "L'attribut" : "La relation"} "${nodeData.name || "sans nom"}" a été ${isCreation ? "créé" : "mis à jour"}`,
      });
    } catch (error) {
      console.error(`Error ${isCreation ? "creating" : "updating"} ${nodeType}:`, error);
      toast({
        title: "Erreur",
        description: `Impossible de ${isCreation ? "créer" : "mettre à jour"} ${nodeType === "concept" ? "le concept" : nodeType === "attribute" ? "l'attribut" : "la relation"}`,
        variant: "destructive",
      });
      throw error; // Re-throw pour que le formulaire puisse gérer l'erreur
    }
  };

  // Fonction de rendu du formulaire pour le GraphNodePanel
  const renderConceptForm = (node: GraphNode, isEditing: boolean, onCancelEdit: () => void, onTypeChange?: (newType: string) => void) => {
    // Utiliser une key pour forcer React à recréer le composant quand les données changent
    // Inclure le type dans la key pour détecter les changements de type
    const formKey = `${node.id}-${node.type}-${node.label}-${node.properties?.description || ""}`;

    // Déterminer si c'est une création (pas d'ID) ou une édition
    const isCreation = !node.id || node.id === "";

    return (
      <ConceptForm
        key={formKey}
        nodeType={node.type}
        isCreation={isCreation} // ✅ Mode création ou modification
        onTypeChange={onTypeChange} // ✅ Passer le callback
        initialData={{
          name: node.label,
          description: (node.properties?.description as string) || "",
          type: node.type, // ✅ Ajouter le type dans initialData
        }}
        edit={isEditing}
        onSubmit={async (data) => {
          await handleUpdateNode(data, node.id, node.type, isCreation);
          onCancelEdit(); // Sortir du mode édition après la sauvegarde
        }}
        onCancel={onCancelEdit}
      />
    );
  };

  // Fonction de rendu pour les attributs (Data Properties)
  const renderAttributeForm = (node: GraphNode, isEditing: boolean, onCancelEdit: () => void, onTypeChange?: (newType: string) => void) => {
    const formKey = `${node.id}-${node.type}-${node.label}-${node.properties?.description || ""}-${node.properties?.dataType || ""}`;
    const isCreation = !node.id || node.id === "";

    return (
      <AttributeForm
        key={formKey}
        nodeType={node.type}
        isCreation={isCreation} // ✅ Mode création ou modification
        onTypeChange={onTypeChange} // ✅ Passer le callback
        initialData={{
          name: node.label,
          description: (node.properties?.description as string) || "",
          dataType: (node.properties?.dataType as string) || "",
          isRequired: (node.properties?.isRequired as boolean) || false,
          isUnique: (node.properties?.isUnique as boolean) || false,
          type: node.type, // ✅ Ajouter le type dans initialData
        }}
        edit={isEditing}
        onSubmit={async (data) => {
          await handleUpdateNode(data, node.id, node.type, isCreation);
          onCancelEdit();
        }}
        onCancel={onCancelEdit}
      />
    );
  };

  // Fonction de rendu pour les relations (Object Properties)
  const renderRelationForm = (node: GraphNode, isEditing: boolean, onCancelEdit: () => void, onTypeChange?: (newType: string) => void) => {
    const formKey = `${node.id}-${node.type}-${node.label}-${node.properties?.description || ""}-${node.properties?.relationType || ""}`;
    const isCreation = !node.id || node.id === "";

    return (
      <RelationForm
        key={formKey}
        nodeType={node.type}
        isCreation={isCreation} // ✅ Mode création ou modification
        onTypeChange={onTypeChange} // ✅ Passer le callback
        initialData={{
          name: node.label || "",
          description: (node.properties?.description as string) || "",
          relationType: (node.properties?.relationType as "is_a" | "has_part" | "has_subclass" | "part_of" | "other") || null, // ✅ null en création
          type: node.type, // ✅ Ajouter le type dans initialData
        }}
        edit={isEditing}
        onSubmit={async (data) => {
          await handleUpdateNode(data, node.id, node.type, isCreation);
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
        // Relation - noeud simple (les connexions se font via edges DOMAIN/RANGE)
        const relationData = nodeData as {
          name: string;
          description: string;
          relationType?: string;
        };

        if (!relationData.relationType) {
          toast({
            title: "Informations manquantes",
            description: "Veuillez spécifier le type de relation",
            variant: "destructive",
          });
          return;
        }

        const createData: RelationshipCreate = {
          name: relationData.name,
          type: relationData.relationType as "is_a" | "has_part" | "has_subclass" | "part_of" | "other",
          description: relationData.description,
          graph_id: id,
          x_position: Math.random() * 400 + 100,
          y_position: Math.random() * 400 + 100,
        };

        const createdRelation = await relationshipService.create(createData);

        // Créer un nœud pour la relation
        newNode = {
          id: createdRelation.id,
          label: createdRelation.name,
          type: "relation",
          properties: {
            name: createdRelation.name,
            description: createdRelation.description || "",
            relationType: createdRelation.type,
          },
        };
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
          edgeTypeConstraints={edgeConstraints}
          onCreateEdge={handleCreateEdge}
          onAddNode={() => setIsCreateNodeOpen(true)}
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

      {/* Modale de création de nœud */}
      <CreateNodeModal
        open={isCreateNodeOpen}
        onOpenChange={setIsCreateNodeOpen}
        onCreateNode={handleCreateNode}
        nodeTypes={nodeTypeConfigs}
        title="Créer un nouveau nœud"
        description="Ajoutez un concept, un attribut ou une relation à votre métamodèle."
        renderForm={(node, isEditing, onCancel, onTypeChange) => {
          const formRenderer = nodeForms[node.type as keyof typeof nodeForms];
          return formRenderer ? formRenderer(node, isEditing, onCancel, onTypeChange) : null;
        }}
      />
    </div>
  );
}
