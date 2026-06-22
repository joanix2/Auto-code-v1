import React from "react";
import { Button } from "@/components/ui/button";
import { ZoomIn, ZoomOut, Maximize2, RotateCcw, Move, Circle, GitBranch, Trash2 } from "lucide-react";
import type { GraphMode } from "@/lib/graph-modes";
import { cn } from "@/lib/utils";

const MODE_ICONS: Record<GraphMode, React.ReactNode> = {
  move: <Move className="h-4 w-4" />,
  node: <Circle className="h-4 w-4" />,
  edge: <GitBranch className="h-4 w-4" />,
  delete: <Trash2 className="h-4 w-4" />,
};

const MODE_LABELS: Record<GraphMode, string> = {
  move: "Déplacer",
  node: "Noeud",
  edge: "Arrête",
  delete: "Suppr.",
};

const ALL_MODES: GraphMode[] = ["move", "node", "edge", "delete"];

interface ZoomControlsProps {
  onZoomIn: () => void;
  onZoomOut: () => void;
  onFitToScreen: () => void;
  onReset: () => void;
  mode: GraphMode;
  onModeChange: (mode: GraphMode) => void;
}

export const ZoomControls: React.FC<ZoomControlsProps> = ({ onZoomIn, onZoomOut, onFitToScreen, onReset, mode, onModeChange }) => {
  return (
    <div className="absolute top-2 right-2 flex flex-col gap-1 bg-white rounded-lg shadow-md p-1 z-10">
      {ALL_MODES.map((m) => (
        <Button
          key={m}
          variant="ghost"
          size="icon"
          onClick={() => onModeChange(m)}
          className={cn("h-8 w-8", mode === m && "bg-accent text-accent-foreground")}
          title={MODE_LABELS[m]}
        >
          {MODE_ICONS[m]}
        </Button>
      ))}

      <div className="w-full border-t my-1" />

      <Button variant="ghost" size="icon" onClick={onZoomIn} className="h-8 w-8" title="Zoom in">
        <ZoomIn className="h-4 w-4" />
      </Button>
      <Button variant="ghost" size="icon" onClick={onZoomOut} className="h-8 w-8" title="Zoom out">
        <ZoomOut className="h-4 w-4" />
      </Button>
      <Button variant="ghost" size="icon" onClick={onFitToScreen} className="h-8 w-8" title="Ajuster">
        <Maximize2 className="h-4 w-4" />
      </Button>
      <Button variant="ghost" size="icon" onClick={onReset} className="h-8 w-8" title="Réinitialiser">
        <RotateCcw className="h-4 w-4" />
      </Button>
    </div>
  );
};
