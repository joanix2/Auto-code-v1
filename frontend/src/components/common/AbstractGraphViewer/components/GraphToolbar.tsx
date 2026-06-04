import React from "react";
import { Plus, Link, Send, Circle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

interface GraphToolbarProps {
  prompt: string;
  onPromptChange: (prompt: string) => void;
  onSendPrompt: () => void;
  onAddNode: () => void;
  isEdgeMode: boolean;
  onToggleEdgeMode: () => void;
  className?: string;
}

export const GraphToolbar: React.FC<GraphToolbarProps> = ({ prompt, onPromptChange, onSendPrompt, onAddNode, isEdgeMode, onToggleEdgeMode, className = "" }) => {
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      onSendPrompt();
    }
  };

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
        {/* Champ de prompt - largeur maximale sur desktop, réduit sur mobile */}
        <div className="relative flex-1 min-w-[150px]">
          <Input type="text" placeholder="Demandez à l'IA de modifier le graphe..." value={prompt} onChange={(e) => onPromptChange(e.target.value)} onKeyDown={handleKeyDown} className="pr-10 h-9" />
          <Button onClick={onSendPrompt} variant="ghost" size="icon" className="absolute right-1 top-1/2 -translate-y-1/2 h-7 w-7" disabled={!prompt.trim()}>
            <Send className="h-4 w-4" />
          </Button>
        </div>
        {/* Bouton Ajouter un nœud - texte complet sur desktop, icône seulement sur mobile */}
        <Button onClick={onAddNode} variant="default" size="sm" className="shrink-0">
          <Plus className="h-4 w-4 md:mr-2" />
          <span className="hidden md:inline">Ajouter un nœud</span>
        </Button>
        {/* Bouton Mode Edge/Node - avec indicateur visuel actif/inactif */}
        <Button onClick={onToggleEdgeMode} variant={isEdgeMode ? "default" : "outline"} size="sm" className="shrink-0">
          {isEdgeMode ? <Link className="h-4 w-4 md:mr-2" /> : <Circle className="h-4 w-4 md:mr-2" />}
          <span className="hidden md:inline">{isEdgeMode ? "Mode Arrête" : "Mode Noeud"}</span>
        </Button>
      </div>
    </div>
  );
};
