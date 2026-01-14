import { useEffect, useState, RefObject } from "react";

interface Dimensions {
  width: number;
  height: number;
}

/**
 * Custom hook to handle responsive dimensions
 */
export const useDimensions = (containerRef: RefObject<HTMLDivElement>, width?: number, height?: number): Dimensions => {
  const [dimensions, setDimensions] = useState<Dimensions>({ width: 0, height: 0 });

  useEffect(() => {
    const updateDimensions = () => {
      if (containerRef.current) {
        const rect = containerRef.current.getBoundingClientRect();
        setDimensions({
          width: width || rect.width,
          height: height || rect.height,
        });
      }
    };

    updateDimensions();
    window.addEventListener("resize", updateDimensions);
    return () => window.removeEventListener("resize", updateDimensions);
  }, [containerRef, width, height]);

  return dimensions;
};
