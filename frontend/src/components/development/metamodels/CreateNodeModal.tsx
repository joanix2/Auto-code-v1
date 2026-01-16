import React, { useState } from "react";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

interface CreateNodeModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onCreateNode: (node: { name: string; description: string; type: "concept" | "attribute" }) => void;
}

export function CreateNodeModal({ open, onOpenChange, onCreateNode }: CreateNodeModalProps) {
  const [formData, setFormData] = useState({
    name: "",
    description: "",
    type: "concept" as "concept" | "attribute",
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.name.trim()) {
      return;
    }

    onCreateNode(formData);

    // Réinitialiser le formulaire
    setFormData({
      name: "",
      description: "",
      type: "concept",
    });

    onOpenChange(false);
  };

  const handleCancel = () => {
    // Réinitialiser le formulaire
    setFormData({
      name: "",
      description: "",
      type: "concept",
    });

    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>Créer un nouveau nœud</DialogTitle>
            <DialogDescription>Ajoutez un concept ou un attribut à votre métamodèle.</DialogDescription>
          </DialogHeader>

          <div className="grid gap-4 py-4">
            {/* Type de nœud */}
            <div className="grid gap-2">
              <Label htmlFor="node-type">Type de nœud</Label>
              <Select value={formData.type} onValueChange={(value: "concept" | "attribute") => setFormData({ ...formData, type: value })}>
                <SelectTrigger id="node-type">
                  <SelectValue placeholder="Sélectionner un type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="concept">
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 rounded-full bg-blue-500" />
                      <span>Concept</span>
                    </div>
                  </SelectItem>
                  <SelectItem value="attribute">
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 rounded-full bg-green-500" />
                      <span>Attribut</span>
                    </div>
                  </SelectItem>
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
                placeholder={formData.type === "concept" ? "Ex: Vehicle, Person, Product..." : "Ex: name, age, price..."}
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
                placeholder={formData.type === "concept" ? "Décrivez ce concept..." : "Décrivez cet attribut..."}
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
              Créer le nœud
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
