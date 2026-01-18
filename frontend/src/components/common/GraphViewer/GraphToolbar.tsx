import React from "react";
import { Plus, Link, Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

interface GraphToolbarProps {
  searchQuery: string;
  onSearchChange: (query: string) => void;
  onAddNode: () => void;
  isEdgeMode: boolean;
  onToggleEdgeMode: () => void;
  className?: string;
}

export const GraphToolbar: React.FC<GraphToolbarProps> = ({ searchQuery, onSearchChange, onAddNode, isEdgeMode, onToggleEdgeMode, className = "" }) => {
  return (
    <div
      className={cn(
        "absolute bottom-0 md:bottom-4 left-1/2 -translate-x-1/2",
        "bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/80",
        "border rounded-t-lg md:rounded-lg shadow-lg",
        "max-w-2xl w-full md:mx-4",
        className,
      )}
    >
      <div className="flex items-center gap-2 px-4 py-3 overflow-x-auto">
        {/* Champ de recherche - largeur maximale sur desktop, réduit sur mobile */}
        <div className="relative flex-1 min-w-[150px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input type="text" placeholder="Rechercher un nœud..." value={searchQuery} onChange={(e) => onSearchChange(e.target.value)} className="pl-9 h-9" />
        </div>

        {/* Bouton Ajouter un nœud - texte complet sur desktop, icône seulement sur mobile */}
        <Button onClick={onAddNode} variant="default" size="sm" className="shrink-0">
          <Plus className="h-4 w-4 md:mr-2" />
          <span className="hidden md:inline">Ajouter un nœud</span>
        </Button>

        {/* Bouton Mode Edge/Node - avec indicateur visuel actif/inactif */}
        <Button onClick={onToggleEdgeMode} variant={isEdgeMode ? "default" : "outline"} size="sm" className="shrink-0">
          <Link className="h-4 w-4 md:mr-2" />
          <span className="hidden md:inline">{isEdgeMode ? "Mode Lien (actif)" : "Mode Lien"}</span>
        </Button>
      </div>
    </div>
  );
};
