export function createBackgroundHandlers(
  dragStartPosRef: React.MutableRefObject<{ x: number; y: number } | null>,
  clickThreshold: number,
  setSelectedNodeData: (node: null) => void,
  setShowNodePanel: (show: boolean) => void,
  onBackgroundClick?: () => void,
) {
  return {
    onPointerDown: (event: PointerEvent) => {
      dragStartPosRef.current = { x: event.clientX, y: event.clientY };
    },
    onPointerUp: (event: PointerEvent) => {
      if (dragStartPosRef.current) {
        const dx = Math.abs(event.clientX - dragStartPosRef.current.x);
        const dy = Math.abs(event.clientY - dragStartPosRef.current.y);

        if (dx < clickThreshold && dy < clickThreshold) {
          setSelectedNodeData(null);
          setShowNodePanel(false);
          if (onBackgroundClick) onBackgroundClick();
        }
      }
      dragStartPosRef.current = null;
    },
  };
}
