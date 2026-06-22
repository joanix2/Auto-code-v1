import { describe, it, expect } from "vitest";
import { MODES, canTransition, transition, isEdgeMode, isMoveMode, isDeleteMode, isNodeCreationMode, type GraphMode } from "./graph-modes";

describe("graph-modes", () => {
  it("a 4 modes", () => {
    expect(Object.keys(MODES)).toHaveLength(4);
  });

  it("chaque mode a une icone, un label, et des transitions", () => {
    for (const mode of Object.values(MODES)) {
      expect(mode.key).toBeTruthy();
      expect(mode.label).toBeTruthy();
      expect(mode.icon).toBeTruthy();
      expect(mode.transitions.length).toBeGreaterThan(0);
    }
  });

  it("move peut transitionner vers node, edge, delete", () => {
    expect(canTransition("move", "node")).toBe(true);
    expect(canTransition("move", "edge")).toBe(true);
    expect(canTransition("move", "delete")).toBe(true);
    expect(canTransition("move", "move")).toBe(false);
  });

  it("transition valide change le mode", () => {
    expect(transition("move", "node")).toBe("node");
    expect(transition("delete", "move")).toBe("move");
  });

  it("transition invalide garde le mode actuel", () => {
    expect(transition("move", "move")).toBe("move");
  });

  it("isEdgeMode retourne true seulement pour edge", () => {
    expect(isEdgeMode("edge")).toBe(true);
    expect(isEdgeMode("move")).toBe(false);
    expect(isEdgeMode("node")).toBe(false);
    expect(isEdgeMode("delete")).toBe(false);
  });

  it("isMoveMode retourne true seulement pour move", () => {
    expect(isMoveMode("move")).toBe(true);
    expect(isMoveMode("node")).toBe(false);
  });

  it("isDeleteMode retourne true seulement pour delete", () => {
    expect(isDeleteMode("delete")).toBe(true);
    expect(isDeleteMode("move")).toBe(false);
  });

  it("isNodeCreationMode retourne true seulement pour node", () => {
    expect(isNodeCreationMode("node")).toBe(true);
    expect(isNodeCreationMode("move")).toBe(false);
  });

  it("tous les modes sont accessibles depuis au moins un autre mode", () => {
    const allModes: GraphMode[] = ["move", "node", "edge", "delete"];
    for (const target of allModes) {
      const reachable = allModes.some((source) => canTransition(source, target));
      expect(reachable).toBe(true);
    }
  });

  it("move ne peut pas transitionner vers move (pas de boucle)", () => {
    expect(canTransition("move", "move")).toBe(false);
    expect(canTransition("node", "node")).toBe(false);
    expect(canTransition("edge", "edge")).toBe(false);
    expect(canTransition("delete", "delete")).toBe(false);
  });
});
