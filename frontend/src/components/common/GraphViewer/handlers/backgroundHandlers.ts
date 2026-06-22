import { GraphNode } from "../types";
import type { GraphMode } from "@/lib/graph-modes";

interface BackgroundHandlerParams {
  mode: GraphMode;
  dragStartPosRef: React.MutableRefObject<{ x: number; y: number } | null>;
  clickThreshold: number;
  setSelectedNodeData: (node: null) => void;
  setShowNodePanel: (show: boolean) => void;
  onBackgroundClick?: () => void;
  untitledCounter: React.MutableRefObject<number>;
  onCreateNode?: (node: GraphNode) => void;
}

export function createBackgroundHandlers({
  mode, dragStartPosRef, clickThreshold, setSelectedNodeData, setShowNodePanel,
  onBackgroundClick, untitledCounter, onCreateNode,
}: BackgroundHandlerParams) {
  return {
    onPointerDown: (event: PointerEvent) => {
      dragStartPosRef.current = { x: event.clientX, y: event.clientY };
    },
    onPointerUp: (event: PointerEvent, svgPoint?: { x: number; y: number }) => {
      if (!dragStartPosRef.current) return;
      const dx = Math.abs(event.clientX - dragStartPosRef.current.x);
      const dy = Math.abs(event.clientY - dragStartPosRef.current.y);

      if (dx < clickThreshold && dy < clickThreshold) {
        if (mode === "node" && onCreateNode && svgPoint) {
          untitledCounter.current += 1;
          onCreateNode({
            id: `new-${Date.now()}`,
            label: `untitled-${untitledCounter.current}`,
            type: "Sort",
            properties: {},
            x: svgPoint.x,
            y: svgPoint.y,
          });
        } else {
          setSelectedNodeData(null);
          setShowNodePanel(false);
          onBackgroundClick?.();
        }
      }
      dragStartPosRef.current = null;
    },
  };
}
