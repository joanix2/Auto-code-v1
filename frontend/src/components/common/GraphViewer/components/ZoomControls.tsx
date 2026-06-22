import React from "react";
import { Button } from "@/components/ui/button";
import { ZoomIn, ZoomOut, Maximize2, RotateCcw, Move, Circle, GitBranch, Trash2 } from "lucide-react";
import type { GraphMode } from "../hooks/useGraphState";
import { cn } from "@/lib/utils";

const MODES: { key: GraphMode; label: string; icon: React.ReactNode }[] = [
  { key: "move", label: "Déplacer", icon: <Move className="h-4 w-4" /> },
  { key: "node", label: "Noeud", icon: <Circle className="h-4 w-4" /> },
  { key: "edge", label: "Arrête", icon: <GitBranch className="h-4 w-4" /> },
  { key: "delete", label: "Suppr.", icon: <Trash2 className="h-4 w-4" /> },
];

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
      {/* Zoom group */}
      <Button variant="ghost" size="icon" onClick={onZoomIn} className="h-8 w-8" title="Zoom in">
        <ZoomIn className="h-4 w-4" />
      </Button>
      <Button variant="ghost" size="icon" onClick={onZoomOut} className="h-8 w-8" title="Zoom out">
        <ZoomOut className="h-4 w-4" />
      </Button>
      <Button variant="ghost" size="icon" onClick={onFitToScreen} className="h-8 w-8" title="Fit to screen">
        <Maximize2 className="h-4 w-4" />
      </Button>
      <Button variant="ghost" size="icon" onClick={onReset} className="h-8 w-8" title="Reset zoom">
        <RotateCcw className="h-4 w-4" />
      </Button>

      {/* Separator */}
      <div className="w-full border-t my-1" />

      {/* Mode group */}
      {MODES.map((m) => (
        <Button
          key={m.key}
          variant="ghost"
          size="icon"
          onClick={() => onModeChange(m.key)}
          className={cn("h-8 w-8 relative", mode === m.key && "bg-accent text-accent-foreground")}
          title={m.label}
        >
          {m.icon}
        </Button>
      ))}
    </div>
  );
};
