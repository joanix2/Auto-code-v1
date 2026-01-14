import * as d3 from "d3";
import { GraphNode } from "./types";
import { ZOOM_SCALE_EXTENT, ZOOM_IN_FACTOR, ZOOM_OUT_FACTOR, FIT_TO_SCREEN_PADDING } from "./constants";

/**
 * Creates and configures zoom behavior
 */
export const createZoomBehavior = (
  svg: d3.Selection<SVGSVGElement, unknown, null, undefined>,
  g: d3.Selection<SVGGElement, unknown, null, undefined>,
  onTransform: (transform: d3.ZoomTransform) => void
) => {
  return d3
    .zoom<SVGSVGElement, unknown>()
    .scaleExtent(ZOOM_SCALE_EXTENT)
    .filter((event) => {
      // Allow zoom/pan only on background, not on nodes (circles) or text
      // This allows drag behavior on nodes to work on mobile
      const target = event.target as HTMLElement;
      const tagName = target.tagName?.toUpperCase();

      console.log("[ZOOM FILTER]", {
        eventType: event.type,
        targetTag: tagName,
        button: event.button,
        ctrlKey: event.ctrlKey,
        target: target,
      });

      // Block zoom on interactive elements
      if (tagName === "CIRCLE" || tagName === "TEXT") {
        console.log("[ZOOM FILTER] Blocked - interactive element");
        return false;
      }

      // Allow zoom with modifier keys or wheel
      if (event.ctrlKey || event.type === "wheel") {
        console.log("[ZOOM FILTER] Allowed - modifier key or wheel");
        return true;
      }

      // Allow pan/zoom on background (no button pressed means left click/touch)
      const allowed = !event.button;
      console.log("[ZOOM FILTER]", allowed ? "Allowed - background" : "Blocked - button pressed");
      return allowed;
    })
    .touchable(() => true) // Enable touch support
    .on("zoom", (event) => {
      console.log("[ZOOM]", {
        eventType: event.type,
        transform: {
          x: event.transform.x,
          y: event.transform.y,
          k: event.transform.k,
        },
        sourceEvent: event.sourceEvent?.type,
      });
      g.attr("transform", event.transform);
      onTransform(event.transform);
    });
};

/**
 * Zoom in handler
 */
export const handleZoomIn = (svgRef: SVGSVGElement | null, zoomBehavior: d3.ZoomBehavior<SVGSVGElement, unknown> | null) => {
  if (!svgRef || !zoomBehavior) return;
  const svg = d3.select(svgRef);
  svg.transition().duration(300).call(zoomBehavior.scaleBy, ZOOM_IN_FACTOR);
};

/**
 * Zoom out handler
 */
export const handleZoomOut = (svgRef: SVGSVGElement | null, zoomBehavior: d3.ZoomBehavior<SVGSVGElement, unknown> | null) => {
  if (!svgRef || !zoomBehavior) return;
  const svg = d3.select(svgRef);
  svg.transition().duration(300).call(zoomBehavior.scaleBy, ZOOM_OUT_FACTOR);
};

/**
 * Reset zoom handler
 */
export const handleResetZoom = (svgRef: SVGSVGElement | null, zoomBehavior: d3.ZoomBehavior<SVGSVGElement, unknown> | null, onTransformUpdate: (transform: d3.ZoomTransform) => void) => {
  if (!svgRef || !zoomBehavior) return;
  const svg = d3.select(svgRef);
  svg.transition().duration(300).call(zoomBehavior.transform, d3.zoomIdentity);
  onTransformUpdate(d3.zoomIdentity);
};

/**
 * Fit to screen handler
 */
export const handleFitToScreen = (
  svgRef: SVGSVGElement | null,
  zoomBehavior: d3.ZoomBehavior<SVGSVGElement, unknown> | null,
  nodes: GraphNode[],
  width: number,
  height: number,
  nodeRadius: number,
  onTransformUpdate: (transform: d3.ZoomTransform) => void
) => {
  if (!svgRef || !zoomBehavior || !nodes.length) return;

  const svg = d3.select(svgRef);
  const bounds = {
    minX: Math.min(...nodes.map((n) => n.x || 0)),
    maxX: Math.max(...nodes.map((n) => n.x || 0)),
    minY: Math.min(...nodes.map((n) => n.y || 0)),
    maxY: Math.max(...nodes.map((n) => n.y || 0)),
  };

  const graphWidth = bounds.maxX - bounds.minX + nodeRadius * 4;
  const graphHeight = bounds.maxY - bounds.minY + nodeRadius * 4;
  const scale = Math.min(width / graphWidth, height / graphHeight, 1) * FIT_TO_SCREEN_PADDING;

  const translateX = (width - (bounds.minX + bounds.maxX) * scale) / 2;
  const translateY = (height - (bounds.minY + bounds.maxY) * scale) / 2;

  const newTransform = d3.zoomIdentity.translate(translateX, translateY).scale(scale);

  svg.transition().duration(300).call(zoomBehavior.transform, newTransform);
  onTransformUpdate(newTransform);
};
