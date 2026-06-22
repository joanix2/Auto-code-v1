/**
 * Machine à états pour les modes du graphe.
 * Chaque mode définit les interactions possibles :
 * - move    → pan/zoom, glisser les nœuds
 * - node    → clic pour créer un nœud
 * - edge    → glisser d'un nœud à l'autre pour créer un lien
 * - delete  → clic sur un nœud pour le supprimer
 */

export type GraphMode = "move" | "node" | "edge" | "delete";

export interface ModeTransition {
  from: GraphMode;
  to: GraphMode;
  label: string;
}

/** Définition complète d'un mode */
export interface ModeDef {
  key: GraphMode;
  label: string;
  icon: string;          // nom lucide-react
  description: string;
  transitions: GraphMode[];
}

export const MODES: Record<GraphMode, ModeDef> = {
  move: {
    key: "move",
    label: "Déplacer",
    icon: "Move",
    description: "Panoramique, zoom, et glissement des nœuds",
    transitions: ["node", "edge", "delete"],
  },
  node: {
    key: "node",
    label: "Noeud",
    icon: "Circle",
    description: "Clic pour créer un nouveau nœud",
    transitions: ["move", "edge", "delete"],
  },
  edge: {
    key: "edge",
    label: "Arrête",
    icon: "GitBranch",
    description: "Glisser d'un nœud à l'autre pour créer un lien",
    transitions: ["move", "node", "delete"],
  },
  delete: {
    key: "delete",
    label: "Suppr.",
    icon: "Trash2",
    description: "Clic sur un nœud pour le supprimer",
    transitions: ["move", "node", "edge"],
  },
};

export function canTransition(from: GraphMode, to: GraphMode): boolean {
  return MODES[from].transitions.includes(to);
}

export function transition(from: GraphMode, to: GraphMode): GraphMode {
  if (!canTransition(from, to)) return from;
  return to;
}

export function isEdgeMode(mode: GraphMode): boolean {
  return mode === "edge";
}

export function isNodeCreationMode(mode: GraphMode): boolean {
  return mode === "node";
}

export function isDeleteMode(mode: GraphMode): boolean {
  return mode === "delete";
}

export function isMoveMode(mode: GraphMode): boolean {
  return mode === "move";
}
