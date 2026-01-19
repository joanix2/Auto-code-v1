/**
 * M3 Types - Meta-metamodel type definitions
 *
 * These types match the backend M3 configuration exactly.
 */

export interface M3NodeType {
  name: string;
  description: string;
  label: string;
  labelPlural: string;
  gender: "m" | "f" | "n";
  article: string;
}

export interface M3EdgeType {
  name: string;
  description: string;
  sourceNodeTypes: string[]; // Array of allowed source node type IDs
  targetNodeTypes: string[]; // Array of allowed target node type IDs
  directed: boolean;
}

/**
 * Helper function to check if an edge type allows a connection
 */
export function allowsConnection(edgeType: M3EdgeType, sourceNodeType: string, targetNodeType: string): boolean {
  return edgeType.sourceNodeTypes.includes(sourceNodeType) && edgeType.targetNodeTypes.includes(targetNodeType);
}

/**
 * Helper function to get all allowed edge types between two node types
 */
export function getAllowedEdgeTypes(edgeTypes: M3EdgeType[], sourceNodeType: string, targetNodeType: string): M3EdgeType[] {
  return edgeTypes.filter((edgeType) => allowsConnection(edgeType, sourceNodeType, targetNodeType));
}
