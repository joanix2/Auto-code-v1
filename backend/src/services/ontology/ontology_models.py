"""
Ontology Models — Pydantic models for the Open World ontology layer.

These models represent:
- **Concepts**: entities/types in the domain
- **Properties**: attributes of concepts
- **SemanticRelations**: relationships between concepts
- **Taxonomies**: classification hierarchies
- **InferenceRules**: deductive rules for generating new knowledge
- **Facts**: declared or inferred statements with confidence scores

The ontology operates in "Open World" mode: absence of information
does NOT mean false. Knowledge can be incomplete and hypothetical.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class Property(BaseModel):
    """A property/attribute of an ontological concept.

    Attributes:
        name: Property name.
        type: Data type of the property (e.g. string, integer, boolean).
        cardinality: Cardinality constraint (e.g. "1", "0..*", "1..*").
    """

    name: str = Field(..., description="Property name")
    type: str = Field(default="string", description="Data type of the property")
    cardinality: str = Field(default="0..*", description="Cardinality constraint")


class Concept(BaseModel):
    """An ontological concept — represents a type/category in the domain.

    Concepts are the fundamental building blocks of the ontology.
    They can be abstract or concrete, with associated properties
    and a confidence score indicating their certainty.

    Attributes:
        id: Unique concept identifier.
        name: Human-readable concept name.
        description: Description of what this concept represents.
        properties: List of properties/attributes of this concept.
        confidence: Confidence score (0.0–1.0) for this concept.
            Low-confidence concepts may be excluded when compiling to IR.
    """

    id: str = Field(..., description="Unique concept identifier")
    name: str = Field(..., description="Human-readable concept name")
    description: str = Field(default="", description="Description of the concept")
    properties: list[Property] = Field(
        default_factory=list, description="Properties/attributes of this concept"
    )
    confidence: float = Field(
        default=1.0, ge=0.0, le=1.0, description="Confidence score (0.0–1.0)"
    )


class SemanticRelation(BaseModel):
    """A semantic relation between two concepts.

    Defines how concepts relate to each other in the ontology.
    Relations are typed (e.g. IS_A, PART_OF, RELATED_TO) and
    have a confidence score.

    Attributes:
        id: Unique relation identifier.
        name: Human-readable relation name.
        source_id: ID of the source concept.
        target_id: ID of the target concept.
        relation_type: Type of relation (e.g. IS_A, PART_OF, RELATED_TO).
        confidence: Confidence score (0.0–1.0).
    """

    id: str = Field(..., description="Unique relation identifier")
    name: str = Field(default="", description="Human-readable relation name")
    source_id: str = Field(..., description="ID of the source concept")
    target_id: str = Field(..., description="ID of the target concept")
    relation_type: str = Field(
        default="RELATED_TO", description="Type of relation (IS_A, PART_OF, etc.)"
    )
    confidence: float = Field(
        default=1.0, ge=0.0, le=1.0, description="Confidence score (0.0–1.0)"
    )


class Taxonomy(BaseModel):
    """A classification hierarchy in the ontology.

    Taxonomies organize concepts into hierarchical structures
    (classifications). A taxonomy can have a parent (sub-taxonomy)
    and contains a list of concept IDs.

    Attributes:
        id: Unique taxonomy identifier.
        name: Human-readable taxonomy name.
        parent_id: Optional ID of the parent taxonomy.
        concepts: List of concept IDs belonging to this taxonomy.
    """

    id: str = Field(..., description="Unique taxonomy identifier")
    name: str = Field(..., description="Human-readable taxonomy name")
    parent_id: str | None = Field(
        default=None, description="ID of the parent taxonomy (if any)"
    )
    concepts: list[str] = Field(
        default_factory=list, description="List of concept IDs in this taxonomy"
    )


class InferenceRule(BaseModel):
    """A deductive inference rule for generating new knowledge.

    Rules use template strings for conditions and conclusions.
    When the condition matches existing facts/concepts, the conclusion
    is generated with a discounted confidence score.

    Attributes:
        id: Unique rule identifier.
        name: Human-readable rule name.
        condition: Template string describing the condition pattern.
        conclusion: Template string describing the conclusion pattern.
        confidence_discount: Multiplier applied to source confidence (0.0–1.0).
            Inferred facts get confidence = source_confidence × discount.
    """

    id: str = Field(..., description="Unique rule identifier")
    name: str = Field(..., description="Human-readable rule name")
    condition: str = Field(
        ...,
        description="Template string for the condition pattern",
        examples=["is_a(?X, ?Y) AND is_a(?Y, ?Z)"],
    )
    conclusion: str = Field(
        ...,
        description="Template string for the conclusion pattern",
        examples=["is_a(?X, ?Z)"],
    )
    confidence_discount: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Confidence multiplier for inferred facts",
    )


class FactSource(str, Enum):
    """Source of a fact — declared or inferred."""

    DECLARED = "DECLARED"
    """Fact was explicitly declared by the user or extracted from input."""

    INFERRED = "INFERRED"
    """Fact was derived by the inference engine."""


class Fact(BaseModel):
    """A fact in the ontology — can be declared or inferred.

    Facts are statements about the domain. Each fact has a
    confidence score and a justification explaining how it
    was derived (for inferred facts).

    Attributes:
        id: Unique fact identifier.
        statement: The fact statement (e.g. "is_a(Car, Vehicle)").
        source: Whether the fact is DECLARED or INFERRED.
        confidence: Confidence score (0.0–1.0).
        justification: Explanation of how this fact was derived.
            For DECLARED facts, this is typically empty or "Declared fact".
            For INFERRED facts, this includes the rule and source facts.
        created_at: Timestamp when the fact was created.
    """

    id: str = Field(..., description="Unique fact identifier")
    statement: str = Field(..., description="The fact statement")
    source: FactSource = Field(
        default=FactSource.DECLARED, description="Source of the fact"
    )
    confidence: float = Field(
        default=1.0, ge=0.0, le=1.0, description="Confidence score (0.0–1.0)"
    )
    justification: str = Field(
        default="", description="Justification for how the fact was derived"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Creation timestamp"
    )


class OntologyGraph(BaseModel):
    """Container for the complete ontology graph.

    An OntologyGraph holds all concepts, relations, taxonomies,
    rules, and facts that make up the ontology. It also includes
    metadata for identification and versioning.

    Attributes:
        id: Unique ontology identifier.
        name: Human-readable ontology name.
        description: Description of the ontology.
        version: Version string.
        concepts: Dictionary mapping concept ID → Concept.
        relations: Dictionary mapping relation ID → SemanticRelation.
        taxonomies: Dictionary mapping taxonomy ID → Taxonomy.
        rules: Dictionary mapping rule ID → InferenceRule.
        facts: Dictionary mapping fact ID → Fact.
        metadata: Additional metadata key-value pairs.
        created_at: Creation timestamp.
        updated_at: Last update timestamp.
    """

    id: str = Field(..., description="Unique ontology identifier")
    name: str = Field(..., description="Human-readable ontology name")
    description: str = Field(default="", description="Description of the ontology")
    version: str = Field(default="1.0.0", description="Version string")
    concepts: dict[str, Concept] = Field(
        default_factory=dict, description="Map of concept ID → Concept"
    )
    relations: dict[str, SemanticRelation] = Field(
        default_factory=dict, description="Map of relation ID → SemanticRelation"
    )
    taxonomies: dict[str, Taxonomy] = Field(
        default_factory=dict, description="Map of taxonomy ID → Taxonomy"
    )
    rules: dict[str, InferenceRule] = Field(
        default_factory=dict, description="Map of rule ID → InferenceRule"
    )
    facts: dict[str, Fact] = Field(
        default_factory=dict, description="Map of fact ID → Fact"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Creation timestamp"
    )
    updated_at: datetime | None = Field(
        default=None, description="Last update timestamp"
    )

    def add_concept(self, concept: Concept) -> None:
        """Add a concept to the ontology.

        Args:
            concept: The Concept to add.
        """
        self.concepts[concept.id] = concept
        self.updated_at = datetime.utcnow()

    def add_relation(self, relation: SemanticRelation) -> None:
        """Add a semantic relation to the ontology.

        Args:
            relation: The SemanticRelation to add.
        """
        self.relations[relation.id] = relation
        self.updated_at = datetime.utcnow()

    def add_taxonomy(self, taxonomy: Taxonomy) -> None:
        """Add a taxonomy to the ontology.

        Args:
            taxonomy: The Taxonomy to add.
        """
        self.taxonomies[taxonomy.id] = taxonomy
        self.updated_at = datetime.utcnow()

    def add_rule(self, rule: InferenceRule) -> None:
        """Add an inference rule to the ontology.

        Args:
            rule: The InferenceRule to add.
        """
        self.rules[rule.id] = rule
        self.updated_at = datetime.utcnow()

    def add_fact(self, fact: Fact) -> None:
        """Add a fact to the ontology.

        Args:
            fact: The Fact to add.
        """
        self.facts[fact.id] = fact
        self.updated_at = datetime.utcnow()

    def get_concept(self, concept_id: str) -> Concept | None:
        """Get a concept by ID.

        Args:
            concept_id: The concept ID to look up.

        Returns:
            The Concept if found, None otherwise.
        """
        return self.concepts.get(concept_id)

    def get_relation(self, relation_id: str) -> SemanticRelation | None:
        """Get a relation by ID.

        Args:
            relation_id: The relation ID to look up.

        Returns:
            The SemanticRelation if found, None otherwise.
        """
        return self.relations.get(relation_id)

    def get_facts_by_statement(self, statement: str) -> list[Fact]:
        """Get all facts matching a given statement.

        Args:
            statement: The statement to match.

        Returns:
            List of matching Facts.
        """
        return [f for f in self.facts.values() if f.statement == statement]

    def get_declared_facts(self) -> list[Fact]:
        """Get all declared (non-inferred) facts.

        Returns:
            List of Facts with source=DECLARED.
        """
        return [f for f in self.facts.values() if f.source == FactSource.DECLARED]

    def get_inferred_facts(self) -> list[Fact]:
        """Get all inferred facts.

        Returns:
            List of Facts with source=INFERRED.
        """
        return [f for f in self.facts.values() if f.source == FactSource.INFERRED]

    def get_concepts_by_confidence(self, threshold: float = 0.5) -> list[Concept]:
        """Get concepts with confidence at or above a threshold.

        Args:
            threshold: Minimum confidence threshold (default 0.5).

        Returns:
            List of Concepts meeting the threshold.
        """
        return [
            c for c in self.concepts.values() if c.confidence >= threshold
        ]

    def to_dict(self) -> dict[str, Any]:
        """Serialize the ontology to a dictionary.

        Returns:
            Dictionary representation of the ontology.
        """
        return self.model_dump(mode="json")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> OntologyGraph:
        """Deserialize a dictionary to an OntologyGraph.

        Args:
            data: Dictionary representation of the ontology.

        Returns:
            The deserialized OntologyGraph.
        """
        return cls.model_validate(data)
