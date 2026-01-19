import React from "react";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { EdgeType } from "../types";

interface EdgeTypeSelectorProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  sourceNode: { id: string; label: string; type?: string } | null;
  targetNode: { id: string; label: string; type?: string } | null;
  availableEdgeTypes: EdgeType[];
  onSelectEdgeType: (edgeType: string) => void;
}

export function EdgeTypeSelector({ open, onOpenChange, sourceNode, targetNode, availableEdgeTypes, onSelectEdgeType }: EdgeTypeSelectorProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Créer un lien</DialogTitle>
          <DialogDescription>
            Choisissez le type de lien entre "{sourceNode?.label}" et "{targetNode?.label}"
          </DialogDescription>
        </DialogHeader>

        <div className="grid gap-3 py-4">
          {availableEdgeTypes.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-4">Aucun type de lien disponible entre ces deux nœuds</p>
          ) : (
            availableEdgeTypes.map((edgeType) => (
              <Button
                key={edgeType.edgeType}
                variant="outline"
                className="justify-start h-auto py-3 px-4"
                onClick={() => {
                  onSelectEdgeType(edgeType.edgeType);
                  onOpenChange(false);
                }}
              >
                <div className="text-left">
                  <div className="font-semibold">{edgeType.label}</div>
                  {edgeType.description && <div className="text-xs text-muted-foreground mt-1">{edgeType.description}</div>}
                </div>
              </Button>
            ))
          )}
        </div>

        <div className="flex justify-end">
          <Button variant="ghost" onClick={() => onOpenChange(false)}>
            Annuler
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
