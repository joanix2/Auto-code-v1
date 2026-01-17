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
   * Formulaire NodeForm à afficher pour le nœud
   * Le formulaire gère automatiquement la section "Informations" et "Propriétés"
   * @param node - Le nœud à afficher
   * @param isEditing - Si le formulaire est en mode édition
   * @param onCancelEdit - Callback pour annuler l'édition
   */
  renderForm?: (node: GraphNode, isEditing: boolean, onCancelEdit: () => void) => React.ReactNode;
}

export const GraphNodePanel: React.FC<GraphNodePanelProps> = ({ node, isOpen, onClose, onEdit, onDelete, className, renderForm }) => {
  const [isMobile, setIsMobile] = useState(false);
  const [isEditing, setIsEditing] = useState(false);

  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768); // 768px = md breakpoint
    };

    checkMobile();
    window.addEventListener("resize", checkMobile);
    return () => window.removeEventListener("resize", checkMobile);
  }, []);

  // Reset edit mode when node changes
  useEffect(() => {
    setIsEditing(false);
  }, [node?.id]);

  const handleEdit = () => {
    setIsEditing(true);
  };

  const handleCancelEdit = () => {
    setIsEditing(false);
  };

  const PanelContent = () => {
    if (!node) return null;

    // Si un formulaire est fourni, l'utiliser (il gère tout : Informations + Propriétés)
    if (renderForm) {
      return (
        <div className="space-y-4">
          {renderForm(node, isEditing, handleCancelEdit)}

          {/* Boutons d'actions en dehors du formulaire */}
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
        </div>
      );
    }

    // Affichage par défaut (si pas de formulaire fourni)
    return (
      <div className="space-y-4">
        <div>
          <h3 className="font-semibold mb-2">Informations</h3>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-sm text-muted-foreground">Label:</span>
              <span className="text-sm">{node.label}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-muted-foreground">Type:</span>
              <Badge variant="secondary">{node.type}</Badge>
            </div>
            {node.properties?.description && (
              <div className="flex justify-between">
                <span className="text-sm text-muted-foreground">Description:</span>
                <span className="text-sm">{String(node.properties.description)}</span>
              </div>
            )}
          </div>
        </div>

        <div>
          <h3 className="font-semibold mb-2">Propriétés</h3>
          {node.properties && Object.keys(node.properties).filter((key) => key !== "name" && key !== "description").length > 0 ? (
            <div className="space-y-2">
              {Object.entries(node.properties)
                .filter(([key]) => key !== "name" && key !== "description")
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

        {(onEdit || onDelete) && (
          <div className="pt-4 space-y-2">
            {onEdit && (
              <Button variant="outline" className="w-full" onClick={() => onEdit(node)}>
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
