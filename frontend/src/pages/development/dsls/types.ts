import { NodeType } from "@/components/common/GraphViewer";

/**
 * Type Concept du DSL
 */
export class DSLConceptNodeType extends NodeType {
  readonly id = "concept";
  readonly label = "Concept";
  readonly labelPlural = "Concepts";
  readonly gender = "m" as const;
  readonly article = "le";
}

/**
 * Type Attribut du DSL
 */
export class DSLAttributeNodeType extends NodeType {
  readonly id = "attribute";
  readonly label = "Attribut";
  readonly labelPlural = "Attributs";
  readonly gender = "m" as const;
  readonly article = "l'";
}

/**
 * Type Relation du DSL
 */
export class DSLRelationNodeType extends NodeType {
  readonly id = "relation";
  readonly label = "Relation";
  readonly labelPlural = "Relations";
  readonly gender = "f" as const;
  readonly article = "la";
}

/**
 * Instances singleton des types de nœuds
 */
export const CONCEPT_TYPE = new DSLConceptNodeType();
export const ATTRIBUTE_TYPE = new DSLAttributeNodeType();
export const RELATION_TYPE = new DSLRelationNodeType();

/**
 * Union type des IDs de nœuds disponibles
 */
export type NodeTypeId = "concept" | "attribute" | "relation";

/**
 * Map pour accéder facilement aux types par ID
 */
export const NODE_TYPES: Record<NodeTypeId, NodeType> = {
  concept: CONCEPT_TYPE,
  attribute: ATTRIBUTE_TYPE,
  relation: RELATION_TYPE,
};
