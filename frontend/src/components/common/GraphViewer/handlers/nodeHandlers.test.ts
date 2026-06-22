import { describe, it, expect, vi } from "vitest";
import { createNodeClickHandler } from "./nodeHandlers";
import type { GraphNode } from "../types";

function makeNode(overrides: Partial<GraphNode> = {}): GraphNode {
  return { id: "n1", label: "test", type: "Sort", properties: {}, ...overrides };
}

function setup() {
  const modeRef = { current: "move" as const };
  const edgeDragState = { sourceNode: null as GraphNode | null, targetNode: null as GraphNode | null, isDrawing: false };
  const setEdgeDragState = vi.fn();
  const setShowEdgeTypeSelector = vi.fn();
  const setSelectedNodeData = vi.fn();
  const setShowNodePanel = vi.fn();
  const getAvailableEdgeTypes = vi.fn(() => []);
  const onCreateEdge = vi.fn();
  const onNodeClick = vi.fn();
  const onDeleteNode = vi.fn();

  const handler = createNodeClickHandler({
    modeRef,
    edgeDragState,
    setEdgeDragState,
    setShowEdgeTypeSelector,
    setSelectedNodeData,
    setShowNodePanel,
    getAvailableEdgeTypes,
    onCreateEdge,
    onNodeClick,
    onDeleteNode,
  });

  return { handler, modeRef, edgeDragState, setEdgeDragState, setShowEdgeTypeSelector, setSelectedNodeData, setShowNodePanel, getAvailableEdgeTypes, onCreateEdge, onNodeClick, onDeleteNode };
}

describe("createNodeClickHandler", () => {
  it("en mode move: selectionne le noeud et ouvre le panel", () => {
    const { handler, setSelectedNodeData, setShowNodePanel, onNodeClick } = setup();
    const node = makeNode();
    handler(node);
    expect(setSelectedNodeData).toHaveBeenCalledWith(node);
    expect(setShowNodePanel).toHaveBeenCalledWith(true);
    expect(onNodeClick).toHaveBeenCalledWith(node);
  });

  it("en mode edge sans source: definit la source", () => {
    const { handler, modeRef, setEdgeDragState } = setup();
    modeRef.current = "edge";
    const node = makeNode();
    handler(node);
    expect(setEdgeDragState).toHaveBeenCalledWith({ sourceNode: node, targetNode: null, isDrawing: false });
  });

  it("en mode edge avec source differente: cree l'arete si 1 seul type", () => {
    const { handler, modeRef, edgeDragState, setEdgeDragState, getAvailableEdgeTypes, onCreateEdge } = setup();
    modeRef.current = "edge";
    const source = makeNode({ id: "src" });
    const target = makeNode({ id: "tgt" });
    edgeDragState.sourceNode = source;
    getAvailableEdgeTypes.mockReturnValue([{ name: "has_sort" } as any]);
    handler(target);
    expect(onCreateEdge).toHaveBeenCalledWith("src", "tgt", "has_sort");
    expect(setEdgeDragState).toHaveBeenCalledWith({ sourceNode: null, targetNode: null, isDrawing: false });
  });

  it("en mode edge avec meme noeud: annule", () => {
    const { handler, modeRef, edgeDragState, setEdgeDragState } = setup();
    modeRef.current = "edge";
    const node = makeNode({ id: "same" });
    edgeDragState.sourceNode = node;
    handler(node);
    expect(setEdgeDragState).toHaveBeenCalledWith({ sourceNode: null, targetNode: null, isDrawing: false });
  });

  it("en mode delete: appelle onDeleteNode", () => {
    const { handler, modeRef, onDeleteNode } = setup();
    modeRef.current = "delete";
    const node = makeNode();
    handler(node);
    expect(onDeleteNode).toHaveBeenCalledWith(node);
  });
});
