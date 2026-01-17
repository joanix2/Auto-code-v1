import React, { useState, useEffect } from "react";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

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
}

export function CreateNodeModal({ open, onOpenChange, onCreateNode, nodeTypes, defaultType, editMode = false, initialData, title, description }: CreateNodeModalProps) {
  const [formData, setFormData] = useState({
    name: "",
    description: "",
    type: defaultType || nodeTypes[0]?.value || "",
  });

  // Charger les données initiales en mode édition
  useEffect(() => {
    if (editMode && initialData) {
      setFormData(initialData);
    } else if (!editMode) {
      setFormData({
        name: "",
        description: "",
        type: defaultType || nodeTypes[0]?.value || "",
      });
    }
  }, [editMode, initialData, open, defaultType, nodeTypes]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.name.trim()) {
      return;
    }

    onCreateNode(formData);

    // Réinitialiser le formulaire seulement en mode création
    if (!editMode) {
      setFormData({
        name: "",
        description: "",
        type: defaultType || nodeTypes[0]?.value || "",
      });
    }

    onOpenChange(false);
  };

  const handleCancel = () => {
    // Réinitialiser le formulaire seulement en mode création
    if (!editMode) {
      setFormData({
        name: "",
        description: "",
        type: defaultType || nodeTypes[0]?.value || "",
      });
    }

    onOpenChange(false);
  };

  // Trouver la config du type actuel
  const currentTypeConfig = nodeTypes.find((t) => t.value === formData.type);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>{title || (editMode ? "Modifier le nœud" : "Créer un nouveau nœud")}</DialogTitle>
            <DialogDescription>{description || (editMode ? "Modifiez les propriétés du nœud." : "Ajoutez un nœud à votre graphe.")}</DialogDescription>
          </DialogHeader>

          <div className="grid gap-4 py-4">
            {/* Type de nœud - Désactivé en mode édition */}
            <div className="grid gap-2">
              <Label htmlFor="node-type">Type de nœud</Label>
              <Select value={formData.type} onValueChange={(value: string) => setFormData({ ...formData, type: value })} disabled={editMode}>
                <SelectTrigger id="node-type">
                  <SelectValue placeholder="Sélectionner un type" />
                </SelectTrigger>
                <SelectContent>
                  {nodeTypes.map((nodeType) => (
                    <SelectItem key={nodeType.value} value={nodeType.value}>
                      <div className="flex items-center gap-2">
                        <div className="w-3 h-3 rounded-full" style={{ backgroundColor: nodeType.color }} />
                        <span>{nodeType.label}</span>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Nom du nœud */}
            <div className="grid gap-2">
              <Label htmlFor="node-name">
                Nom <span className="text-destructive">*</span>
              </Label>
              <Input
                id="node-name"
                placeholder={currentTypeConfig?.placeholder || "Nom du nœud..."}
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                required
                autoFocus
              />
            </div>

            {/* Description */}
            <div className="grid gap-2">
              <Label htmlFor="node-description">Description</Label>
              <Textarea
                id="node-description"
                placeholder={currentTypeConfig?.descriptionPlaceholder || "Décrivez ce nœud..."}
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                rows={3}
              />
            </div>
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={handleCancel}>
              Annuler
            </Button>
            <Button type="submit" disabled={!formData.name.trim()}>
              {editMode ? "Enregistrer" : "Créer le nœud"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
