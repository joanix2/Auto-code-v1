/**
 * M3 Types — matching the rewriting-logic M3 graph labels.
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
  sourceNodeTypes: string[];
  targetNodeTypes: string[];
  directed: boolean;
}

export function allowsConnection(
  edgeType: M3EdgeType,
  sourceNodeType: string,
  targetNodeType: string,
): boolean {
  return (
    edgeType.sourceNodeTypes.includes(sourceNodeType) &&
    edgeType.targetNodeTypes.includes(targetNodeType)
  );
}

export function getAllowedEdgeTypes(
  edgeTypes: M3EdgeType[],
  sourceNodeType: string,
  targetNodeType: string,
): M3EdgeType[] {
  return edgeTypes.filter((et) => allowsConnection(et, sourceNodeType, targetNodeType));
}
