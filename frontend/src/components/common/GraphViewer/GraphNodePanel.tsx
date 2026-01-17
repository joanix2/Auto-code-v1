import React, { useState, useEffect } from "react";
import { GraphNode } from "./types";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Edit, Trash2, X, Save } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";

export interface GraphNodePanelProps {
  node: GraphNode | null;
  isOpen: boolean;
  onClose: () => void;
  onEdit?: (node: GraphNode) => void;
  onDelete?: (node: GraphNode) => void;
  className?: string;
  /**
   * Formulaire personnalisé à afficher pour le nœud
   * Si fourni, il remplace l'affichage par défaut des propriétés
   */
  renderForm?: (node: GraphNode, isEditing: boolean, onCancelEdit: () => void) => React.ReactNode;
}

export const GraphNodePanel: React.FC<GraphNodePanelProps> = ({ node, isOpen, onClose, onEdit, onDelete, className, renderForm }) => {
  const [isMobile, setIsMobile] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editedLabel, setEditedLabel] = useState("");
  const [editedDescription, setEditedDescription] = useState("");

  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768); // 768px = md breakpoint
    };

    checkMobile();
    window.addEventListener("resize", checkMobile);
    return () => window.removeEventListener("resize", checkMobile);
  }, []);

  // Réinitialiser le mode édition quand le panel se ferme
  useEffect(() => {
    if (!isOpen) {
      setIsEditing(false);
    }
  }, [isOpen]);

  // Initialiser les valeurs éditées quand le nœud change
  useEffect(() => {
    if (node) {
      setEditedLabel(node.label);
      setEditedDescription((node.properties?.description as string) || "");
    }
  }, [node]);

  const handleEdit = () => {
    if (renderForm) {
      // Si un formulaire est fourni, basculer en mode édition
      setIsEditing(true);
    } else if (onEdit && node) {
      // Sinon, basculer en mode édition locale
      setIsEditing(true);
    }
  };

  const handleCancelEdit = () => {
    // Réinitialiser les valeurs
    if (node) {
      setEditedLabel(node.label);
      setEditedDescription((node.properties?.description as string) || "");
    }
    setIsEditing(false);
  };

  const handleSaveEdit = () => {
    if (node && onEdit) {
      // Créer un nouveau nœud avec les valeurs modifiées
      const updatedNode: GraphNode = {
        ...node,
        label: editedLabel,
        properties: {
          ...node.properties,
          name: editedLabel,
          description: editedDescription,
        },
      };
      onEdit(updatedNode);
      setIsEditing(false);
    }
  };

  const PanelContent = () => {
    if (!node) return null;

    // Section Informations (toujours affichée)
    const InfoSection = () => (
      <div>
        <h3 className="font-semibold mb-2">Informations</h3>
        <div className="space-y-3">
          {/* Label */}
          <div>
            <label className="block text-sm text-muted-foreground mb-1">Label:</label>
            {isEditing && !renderForm ? (
              <Input value={editedLabel} onChange={(e) => setEditedLabel(e.target.value)} placeholder="Nom du nœud" className="w-full" />
            ) : (
              <span className="text-sm block">{node.label}</span>
            )}
          </div>

          {/* Type */}
          <div className="flex justify-between items-center">
            <span className="text-sm text-muted-foreground">Type:</span>
            <Badge variant="secondary">{node.type}</Badge>
          </div>

          {/* Description */}
          <div>
            <label className="block text-sm text-muted-foreground mb-1">Description:</label>
            {isEditing && !renderForm ? (
              <Textarea value={editedDescription} onChange={(e) => setEditedDescription(e.target.value)} placeholder="Description du nœud" className="w-full min-h-[80px]" />
            ) : (
              <span className="text-sm block">{node.properties?.description ? String(node.properties.description) : <span className="text-muted-foreground italic">Non renseigné</span>}</span>
            )}
          </div>
        </div>
      </div>
    );

    // Si un formulaire personnalisé est fourni, l'utiliser avec la section Info
    if (renderForm) {
      return (
        <div className="space-y-4">
          <InfoSection />

          <div>
            <h3 className="font-semibold mb-2">Propriétés</h3>
            {renderForm(node, isEditing, handleCancelEdit)}
          </div>

          {!isEditing && (
            <div className="pt-2 space-y-2">
              <Button variant="outline" className="w-full" onClick={handleEdit}>
                <Edit className="h-4 w-4 mr-2" />
                Modifier
              </Button>
              {onDelete && (
                <Button variant="destructive" className="w-full" onClick={() => onDelete(node)}>
                  <Trash2 className="h-4 w-4 mr-2" />
                  Supprimer
                </Button>
              )}
            </div>
          )}

          {isEditing && !renderForm && (
            <div className="pt-2 space-y-2">
              <Button variant="default" className="w-full" onClick={handleSaveEdit}>
                <Save className="h-4 w-4 mr-2" />
                Enregistrer
              </Button>
              <Button variant="outline" className="w-full" onClick={handleCancelEdit}>
                <X className="h-4 w-4 mr-2" />
                Annuler
              </Button>
            </div>
          )}
        </div>
      );
    }

    // Affichage par défaut (propriétés)

    return (
      <div className="space-y-2">
        <InfoSection />

        <div>
          <h3 className="font-semibold mb-2">Propriétés</h3>
          {node.properties && Object.keys(node.properties).length > 0 ? (
            <div className="space-y-2">
              {Object.entries(node.properties)
                .filter(([key]) => key !== "name" && key !== "description") // Exclure name et description
                .map(([key, value]) => (
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

        {!isEditing && (onEdit || onDelete) && (
          <div className="pt-4 space-y-2">
            {onEdit && (
              <Button variant="outline" className="w-full" onClick={handleEdit}>
                <Edit className="h-4 w-4 mr-2" />
                Modifier
              </Button>
            )}
            {onDelete && (
              <Button variant="destructive" className="w-full" onClick={() => onDelete(node)}>
                <Trash2 className="h-4 w-4 mr-2" />
                Supprimer
              </Button>
            )}
          </div>
        )}

        {isEditing && (
          <div className="pt-4 space-y-2">
            <Button variant="default" className="w-full" onClick={handleSaveEdit}>
              <Save className="h-4 w-4 mr-2" />
              Enregistrer
            </Button>
            <Button variant="outline" className="w-full" onClick={handleCancelEdit}>
              <X className="h-4 w-4 mr-2" />
              Annuler
            </Button>
          </div>
        )}
      </div>
    );
  };

  return (
    <>
      {/* Mobile: Dialog (Popup centré) - Only render on mobile */}
      {isMobile && (
        <Dialog open={isOpen && !!node} onOpenChange={onClose}>
          <DialogContent className="max-w-md max-h-[80vh] overflow-y-auto">
            {node && (
              <>
                <DialogHeader>
                  <DialogTitle>Propriétés du nœud</DialogTitle>
                </DialogHeader>
                <div className="mt-4">
                  <PanelContent />
                </div>
              </>
            )}
          </DialogContent>
        </Dialog>
      )}

      {/* Desktop: Fixed panel with rounded corners - Only render on desktop */}
      {!isMobile && node && (
        <div
          className={cn(
            "absolute top-4 right-4 w-80 bg-background border rounded-lg shadow-lg transition-transform duration-300 pointer-events-auto z-10",
            isOpen ? "translate-x-0" : "translate-x-[calc(100%+16px)]",
            className,
          )}
        >
          <div className="p-4 border-b flex items-center justify-between">
            <h3 className="font-semibold">Propriétés du nœud</h3>
            <Button variant="ghost" size="icon" onClick={onClose} className="flex-shrink-0 ml-2">
              <X className="h-4 w-4" />
            </Button>
          </div>
          <div className="p-4 overflow-y-auto max-h-[calc(100vh-12rem)]">
            <PanelContent />
          </div>
        </div>
      )}
    </>
  );
};
