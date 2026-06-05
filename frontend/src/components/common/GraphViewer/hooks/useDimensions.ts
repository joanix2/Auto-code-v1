import { useEffect, useState, RefObject } from "react";

interface Dimensions {
  width: number;
  height: number;
}

/**
 * Custom hook to handle responsive dimensions
 */
export const useDimensions = (containerRef: RefObject<HTMLDivElement>, width?: number, height?: number): Dimensions => {
  const [dimensions, setDimensions] = useState<Dimensions>({ width: 800, height: 600 });

  useEffect(() => {
    const updateDimensions = () => {
      if (containerRef.current) {
        const rect = containerRef.current.getBoundingClientRect();
        const newWidth = width || rect.width || 800;
        const newHeight = height || rect.height || 600;
        setDimensions({
          width: Math.max(newWidth, 200),
          height: Math.max(newHeight, 200),
        });
      }
    };

    updateDimensions();
    const resizeObserver = new ResizeObserver(updateDimensions);
    if (containerRef.current) {
      resizeObserver.observe(containerRef.current);
    }
    window.addEventListener("resize", updateDimensions);
    return () => {
      resizeObserver.disconnect();
      window.removeEventListener("resize", updateDimensions);
    };
  }, [containerRef, width, height]);

  return dimensions;
};
