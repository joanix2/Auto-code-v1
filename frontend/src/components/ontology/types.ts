import { NodeType } from "@/components/common/GraphViewer";

export class OntologyConceptNodeType extends NodeType {
  readonly id = "concept";
  readonly label = "Concept";
  readonly labelPlural = "Concepts";
  readonly gender = "m" as const;
  readonly article = "le";
}

export class OntologyRelationNodeType extends NodeType {
  readonly id = "relation";
  readonly label = "Relation";
  readonly labelPlural = "Relations";
  readonly gender = "f" as const;
  readonly article = "la";
}

export const ONTOLOGY_CONCEPT = new OntologyConceptNodeType();
export const ONTOLOGY_RELATION = new OntologyRelationNodeType();

export const ONTOLOGY_NODE_TYPES: Record<string, NodeType> = {
  concept: ONTOLOGY_CONCEPT,
  relation: ONTOLOGY_RELATION,
};
