import React from "react";
import { Button } from "@/components/ui/button";
import { ZoomIn, ZoomOut, Maximize2, RotateCcw } from "lucide-react";

interface ZoomControlsProps {
  onZoomIn: () => void;
  onZoomOut: () => void;
  onFitToScreen: () => void;
  onReset: () => void;
}

export const ZoomControls: React.FC<ZoomControlsProps> = ({ onZoomIn, onZoomOut, onFitToScreen, onReset }) => {
  return (
    <div className="absolute top-2 left-2 flex flex-col gap-1 bg-white rounded-lg shadow-md p-1 z-10">
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
    </div>
  );
};
