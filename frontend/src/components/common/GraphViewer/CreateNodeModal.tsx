import React, { useState, useEffect } from "react";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { GraphNode } from "./types";

/**
 * Configuration d'un type de nœud
 */
export interface NodeTypeConfig {
  value: string;
  label: string;
  color: string;
  placeholder?: string;
  descriptionPlaceholder?: string;
}

interface CreateNodeModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onCreateNode: (node: { name: string; description: string; type: string; [key: string]: unknown }) => void;
  nodeTypes: NodeTypeConfig[];
  defaultType?: string;
  editMode?: boolean;
  initialData?: { name: string; description: string; type: string; [key: string]: unknown };
  title?: string;
  description?: string;
  /**
   * Fonction de rendu de formulaire par type
   * Prend un nœud (même en création avec données partielles), le mode édition, un callback d'annulation et un callback de changement de type
   * Le formulaire doit gérer sa propre soumission en appelant onCreateNode
   */
  renderForm?: (node: GraphNode, isEditing: boolean, onCancelEdit: () => void, onTypeChange?: (newType: string) => void) => React.ReactNode;
}

export function CreateNodeModal({ open, onOpenChange, onCreateNode, nodeTypes, defaultType, editMode = false, initialData, title, description, renderForm }: CreateNodeModalProps) {
  const [formData, setFormData] = useState<{
    name: string;
    description: string;
    type: string;
    [key: string]: unknown;
  }>({
    name: "",
    description: "",
    type: defaultType || nodeTypes[0]?.value || "", // ✅ Premier type par défaut
  });

  // Charger les données initiales en mode édition
  useEffect(() => {
    if (editMode && initialData) {
      setFormData(initialData);
    } else if (!editMode) {
      const defaultTypeValue = defaultType || nodeTypes[0]?.value || ""; // ✅ Premier type par défaut
      setFormData({
        name: "",
        description: "",
        type: defaultTypeValue,
      });
    }
  }, [editMode, initialData, open, defaultType, nodeTypes]);

  // ✅ Callback pour gérer le changement de type depuis le formulaire enfant
  const handleTypeChange = (newType: string) => {
    setFormData((prev) => ({
      ...prev,
      type: newType,
    }));
  };

  const handleCancel = () => {
    // Réinitialiser le formulaire seulement en mode création
    if (!editMode) {
      const defaultTypeValue = defaultType || nodeTypes[0]?.value || ""; // ✅ Premier type par défaut
      setFormData({
        name: "",
        description: "",
        type: defaultTypeValue,
      });
    }

    onOpenChange(false);
  };

  // Créer un nœud GraphNode à partir de formData pour le passer au formulaire
  const currentNode: GraphNode = {
    id: (formData.id as string) || "",
    label: formData.name,
    type: formData.type,
    properties: {
      name: formData.name,
      description: formData.description,
      type: formData.type,
      ...Object.fromEntries(Object.entries(formData).filter(([key]) => !["id", "name", "description", "type"].includes(key))),
    },
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px] max-h-[90vh] flex flex-col">
        <DialogHeader>
          <DialogTitle>{title || (editMode ? "Modifier le nœud" : "Créer un nouveau nœud")}</DialogTitle>
          <DialogDescription>{description || (editMode ? "Modifiez les propriétés du nœud." : "Ajoutez un nœud à votre graphe.")}</DialogDescription>
        </DialogHeader>

        <div className="grid gap-4 py-4 overflow-y-auto flex-1">
          {/* Afficher le formulaire spécifique au type si renderForm est fourni */}
          {renderForm ? renderForm(currentNode, true, handleCancel, handleTypeChange) : <div className="text-sm text-muted-foreground">Aucun formulaire disponible pour ce type de nœud.</div>}
        </div>
      </DialogContent>
    </Dialog>
  );
}
