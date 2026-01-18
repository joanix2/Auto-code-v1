import { useCallback } from "react";
import * as d3 from "d3";
import { ZOOM_IN_FACTOR, ZOOM_OUT_FACTOR, FIT_TO_SCREEN_PADDING, ZOOM_SCALE_EXTENT } from "../utils/constants";
import { GraphNode } from "../types";

interface UseZoomControlsParams {
  svgRef: React.RefObject<SVGSVGElement>;
  zoomBehaviorRef: React.MutableRefObject<d3.ZoomBehavior<SVGSVGElement, unknown> | null>;
  dimensions: { width: number; height: number };
  nodes: GraphNode[];
  nodeRadius: number;
  setTransform: (transform: d3.ZoomTransform) => void;
}

/**
 * Creates and configures zoom behavior
 */
export const createZoomBehavior = (
  svg: d3.Selection<SVGSVGElement, unknown, null, undefined>,
  g: d3.Selection<SVGGElement, unknown, null, undefined>,
  onTransform: (transform: d3.ZoomTransform) => void,
) => {
  return d3
    .zoom<SVGSVGElement, unknown>()
    .scaleExtent(ZOOM_SCALE_EXTENT)
    .filter((event) => {
      // Allow zoom/pan only on background, not on nodes (circles) or text
      // This allows drag behavior on nodes to work on mobile
      const target = event.target as HTMLElement;
      const tagName = target.tagName?.toUpperCase();

      // Block zoom on interactive elements
      if (tagName === "CIRCLE" || tagName === "TEXT") {
        return false;
      }

      // Allow zoom with modifier keys or wheel
      if (event.ctrlKey || event.type === "wheel") {
        return true;
      }

      // Allow pan/zoom on background (no button pressed means left click/touch)
      return !event.button;
    })
    .touchable(() => true) // Enable touch support
    .on("zoom", (event) => {
      g.attr("transform", event.transform);
      onTransform(event.transform);
    });
};

export function useZoomControls({ svgRef, zoomBehaviorRef, dimensions, nodes, nodeRadius, setTransform }: UseZoomControlsParams) {
  const handleZoomIn = useCallback(() => {
    if (!svgRef.current || !zoomBehaviorRef.current) return;
    const svg = d3.select(svgRef.current);
    const currentTransform = d3.zoomTransform(svgRef.current);
    const centerX = dimensions.width / 2;
    const centerY = dimensions.height / 2;

    const point = [(centerX - currentTransform.x) / currentTransform.k, (centerY - currentTransform.y) / currentTransform.k];
    const newK = currentTransform.k * ZOOM_IN_FACTOR;
    const newTransform = d3.zoomIdentity.translate(centerX - point[0] * newK, centerY - point[1] * newK).scale(newK);

    svg.transition().duration(300).call(zoomBehaviorRef.current.transform, newTransform);
  }, [svgRef, zoomBehaviorRef, dimensions]);

  const handleZoomOut = useCallback(() => {
    if (!svgRef.current || !zoomBehaviorRef.current) return;
    const svg = d3.select(svgRef.current);
    const currentTransform = d3.zoomTransform(svgRef.current);
    const centerX = dimensions.width / 2;
    const centerY = dimensions.height / 2;

    const point = [(centerX - currentTransform.x) / currentTransform.k, (centerY - currentTransform.y) / currentTransform.k];
    const newK = currentTransform.k * ZOOM_OUT_FACTOR;
    const newTransform = d3.zoomIdentity.translate(centerX - point[0] * newK, centerY - point[1] * newK).scale(newK);

    svg.transition().duration(300).call(zoomBehaviorRef.current.transform, newTransform);
  }, [svgRef, zoomBehaviorRef, dimensions]);

  const handleReset = useCallback(() => {
    if (!svgRef.current || !zoomBehaviorRef.current) return;
    const svg = d3.select(svgRef.current);
    svg.transition().duration(300).call(zoomBehaviorRef.current.transform, d3.zoomIdentity);
    setTransform(d3.zoomIdentity);
  }, [svgRef, zoomBehaviorRef, setTransform]);

  const handleFitToScreen = useCallback(() => {
    if (!svgRef.current || !zoomBehaviorRef.current || !nodes.length) return;

    const svg = d3.select(svgRef.current);
    const bounds = {
      minX: Math.min(...nodes.map((n) => n.x || 0)),
      maxX: Math.max(...nodes.map((n) => n.x || 0)),
      minY: Math.min(...nodes.map((n) => n.y || 0)),
      maxY: Math.max(...nodes.map((n) => n.y || 0)),
    };

    const graphWidth = bounds.maxX - bounds.minX + nodeRadius * 4;
    const graphHeight = bounds.maxY - bounds.minY + nodeRadius * 4;
    const scale = Math.min(dimensions.width / graphWidth, dimensions.height / graphHeight, 1) * FIT_TO_SCREEN_PADDING;

    const translateX = (dimensions.width - (bounds.minX + bounds.maxX) * scale) / 2;
    const translateY = (dimensions.height - (bounds.minY + bounds.maxY) * scale) / 2;

    const newTransform = d3.zoomIdentity.translate(translateX, translateY).scale(scale);

    svg.transition().duration(300).call(zoomBehaviorRef.current.transform, newTransform);
    setTransform(newTransform);
  }, [svgRef, zoomBehaviorRef, dimensions, nodes, nodeRadius, setTransform]);

  return {
    handleZoomIn,
    handleZoomOut,
    handleReset,
    handleFitToScreen,
  };
}
