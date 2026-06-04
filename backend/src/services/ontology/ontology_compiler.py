"""
Ontology Compiler — transforms between Ontology (Open World) and IR graph (Closed World).

The compiler is the *bridge* between the two knowledge representation layers:

1. **compile_to_ir(ontology) → dict**: Takes an Open World ontology and produces
   a Closed World IR graph. Concepts with confidence < 0.5 are excluded.
   Properties become attribute nodes. Relations become edges. Taxonomies
   become SUBCLASS_OF hierarchy edges.

2. **extract_ontology_from_ir(ir_graph) → OntologyGraph**: Reverse direction.
   Takes a validated IR graph and reconstructs an ontology from it.
   All IR nodes become concepts with confidence=1.0.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from src.services.ontology.ontology_models import (
    Concept,
    OntologyGraph,
    Property,
    SemanticRelation,
    Taxonomy,
)

logger = logging.getLogger(__name__)

# Default confidence threshold for compiling to IR
DEFAULT_CONFIDENCE_THRESHOLD = 0.5


class OntologyCompiler:
    """Compiles ontology graphs to/from the IR (Intermediate Representation) format.

    The compiler enforces the Open World → Closed World boundary:
    - Low-confidence concepts are excluded.
    - Ambiguous relations are resolved.
    - Taxonomies are flattened into SUBCLASS_OF edges.
    """

    def __init__(self, confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD):
        """Initialize the compiler.

        Args:
            confidence_threshold: Minimum confidence for a concept to be
                included when compiling to IR (default 0.5).
        """
        self.confidence_threshold = confidence_threshold

    # ------------------------------------------------------------------
    # Ontology → IR
    # ------------------------------------------------------------------

    def compile_to_ir(self, ontology: OntologyGraph) -> dict[str, Any]:
        """Transform an ontology into an IR graph dict.

        The IR graph follows the schema defined in ``src.models.graph.schema``
        with ``metadata``, ``nodes``, and ``edges``.

        Compilation rules:
        - Concepts with confidence < threshold are excluded.
        - Each included concept becomes a node with type "concept".
        - Each property becomes an attribute node linked via HAS_ATTRIBUTE.
        - Each semantic relation becomes an edge.
        - Each taxonomy becomes SUBCLASS_OF edges between concepts.
        - Only edges between included concepts are kept.

        Args:
            ontology: The OntologyGraph to compile.

        Returns:
            A dict conforming to the IR graph format.
        """
        # 1. Filter concepts by confidence
        included_concepts = {
            cid: c
            for cid, c in ontology.concepts.items()
            if c.confidence >= self.confidence_threshold
        }

        excluded_ids = set(ontology.concepts.keys()) - set(included_concepts.keys())
        if excluded_ids:
            logger.info(
                f"Excluded {len(excluded_ids)} low-confidence concept(s): "
                f"{', '.join(sorted(excluded_ids))}"
            )

        # 2. Build nodes
        nodes: list[dict[str, Any]] = []
        attribute_node_map: dict[str, str] = {}  # property_key -> attribute node id

        for concept in included_concepts.values():
            node_id = concept.id
            nodes.append({
                "id": node_id,
                "name": concept.name,
                "description": concept.description,
                "type": "concept",
                "label": concept.name,
                "confidence": concept.confidence,
            })

            # Create attribute nodes for each property
            for prop in concept.properties:
                attr_id = f"{concept.id}_{prop.name}"
                nodes.append({
                    "id": attr_id,
                    "name": prop.name,
                    "description": f"{prop.name} property of {concept.name}",
                    "type": "attribute",
                    "label": prop.name,
                    "dataType": prop.type,
                    "cardinality": prop.cardinality,
                })
                attribute_node_map[f"{concept.id}.{prop.name}"] = attr_id

        # 3. Build edges
        edges: list[dict[str, Any]] = []
        edge_id_counter = 0

        # 3a. Property edges (HAS_ATTRIBUTE)
        for concept in included_concepts.values():
            for prop in concept.properties:
                attr_id = attribute_node_map.get(f"{concept.id}.{prop.name}")
                if attr_id:
                    edges.append(self._make_edge(
                        f"has_attr_{concept.id}_{prop.name}",
                        concept.id,
                        attr_id,
                        "HAS_ATTRIBUTE",
                    ))

        # 3b. Semantic relation edges
        for rel in ontology.relations.values():
            if rel.source_id in included_concepts and rel.target_id in included_concepts:
                edges.append(self._make_edge(
                    rel.id,
                    rel.source_id,
                    rel.target_id,
                    rel.relation_type,
                    confidence=rel.confidence,
                ))

        # 3c. Taxonomy → SUBCLASS_OF edges
        for taxonomy in ontology.taxonomies.values():
            # Get parent concept for this taxonomy
            parent_concept = None
            if taxonomy.parent_id and taxonomy.parent_id in included_concepts:
                parent_concept = included_concepts[taxonomy.parent_id]
            elif taxonomy.parent_id:
                # If parent is excluded, skip this taxonomy
                continue

            for concept_id in taxonomy.concepts:
                if concept_id in included_concepts:
                    if parent_concept:
                        # Child → Parent: SUBCLASS_OF
                        edges.append(self._make_edge(
                            f"subclass_{concept_id}_{taxonomy.parent_id}",
                            concept_id,
                            taxonomy.parent_id,
                            "SUBCLASS_OF",
                        ))
                    # If parent_concept is None (root taxonomy), the concepts
                    # are just grouped but no SUBCLASS_OF edge is created

            # Handle parent-child taxonomy hierarchies
            # (taxonomy.parent_id points to the parent taxonomy)
            child_taxonomies = [
                t for t in ontology.taxonomies.values()
                if t.parent_id == taxonomy.id
            ]
            # For nested taxonomies, the child taxonomy's concepts
            # are already linked via parent_id → concept relationships
            # No additional edges needed beyond what's already generated

        # Build IR graph dict
        ir_graph: dict[str, Any] = {
            "metadata": {
                "id": ontology.id,
                "name": ontology.name,
                "description": ontology.description,
                "version": ontology.version,
                "status": "draft",
                "node_count": len(nodes),
                "edge_count": len(edges),
                "confidence_threshold": self.confidence_threshold,
            },
            "nodes": nodes,
            "edges": edges,
        }

        logger.info(
            f"Compiled ontology '{ontology.id}' to IR: "
            f"{len(nodes)} nodes, {len(edges)} edges "
            f"(threshold={self.confidence_threshold})"
        )
        return ir_graph

    # ------------------------------------------------------------------
    # IR → Ontology
    # ------------------------------------------------------------------

    @staticmethod
    def extract_ontology_from_ir(
        ir_graph: dict[str, Any], ontology_id: str | None = None
    ) -> OntologyGraph:
        """Reverse-compile an IR graph into an OntologyGraph.

        All IR nodes become concepts with confidence=1.0 (Closed World).
        Edges become semantic relations.

        Args:
            ir_graph: An IR graph dict (with metadata, nodes, edges).
            ontology_id: Optional ontology ID. If None, uses the IR graph's
                metadata id.

        Returns:
            The extracted OntologyGraph.

        Raises:
            ValueError: If the IR graph is missing required keys.
        """
        for key in ("metadata", "nodes", "edges"):
            if key not in ir_graph:
                raise ValueError(f"IR graph missing required key: '{key}'")

        meta = ir_graph.get("metadata", {})
        oid = ontology_id or meta.get("id", str(uuid.uuid4()))
        oname = meta.get("name", "Extracted Ontology")
        oversion = meta.get("version", "1.0.0")

        ontology = OntologyGraph(
            id=oid,
            name=oname,
            version=oversion,
            description=meta.get("description", ""),
        )

        # Build a mapping from node ID to concept ID
        # Concepts come from "concept" type nodes
        concept_id_map: dict[str, str] = {}

        # Also track attribute nodes for property extraction
        attribute_nodes: dict[str, dict[str, Any]] = {}

        for node in ir_graph.get("nodes", []):
            node_type = node.get("type", "")
            node_id = node.get("id", "")
            node_name = node.get("name", "")

            if node_type == "concept":
                concept = Concept(
                    id=node_id,
                    name=node_name,
                    description=node.get("description", ""),
                    confidence=node.get("confidence", 1.0),
                )
                ontology.add_concept(concept)
                concept_id_map[node_id] = node_id

            elif node_type == "attribute":
                # Store attribute nodes to link later via edges
                attribute_nodes[node_id] = node

        # Process edges to create relations and link properties
        for edge in ir_graph.get("edges", []):
            edge_type = edge.get("type", "RELATED_TO")
            source_id = edge.get("source", "")
            target_id = edge.get("target", "")

            if edge_type == "HAS_ATTRIBUTE":
                # Link attribute to its parent concept
                if target_id in attribute_nodes and source_id in concept_id_map:
                    attr = attribute_nodes[target_id]
                    prop = Property(
                        name=attr.get("name", "unknown"),
                        type=attr.get("dataType", "string"),
                        cardinality=attr.get("cardinality", "0..*"),
                    )
                    concept = ontology.get_concept(source_id)
                    if concept:
                        # Avoid duplicates
                        if prop.name not in {p.name for p in concept.properties}:
                            concept.properties.append(prop)

            elif edge_type == "SUBCLASS_OF":
                # Create a subclass relation
                rel = SemanticRelation(
                    id=edge.get("id", str(uuid.uuid4())),
                    name=f"SUBCLASS_OF: {source_id} → {target_id}",
                    source_id=source_id,
                    target_id=target_id,
                    relation_type="SUBCLASS_OF",
                    confidence=edge.get("confidence", 1.0),
                )
                ontology.add_relation(rel)

            else:
                # Generic relation
                if source_id in concept_id_map and target_id in concept_id_map:
                    rel = SemanticRelation(
                        id=edge.get("id", str(uuid.uuid4())),
                        name=edge.get("label", ""),
                        source_id=source_id,
                        target_id=target_id,
                        relation_type=edge_type,
                        confidence=edge.get("confidence", 1.0),
                    )
                    ontology.add_relation(rel)

        # Create a flat taxonomy from SUBCLASS_OF relations
        subclass_relations = [
            r for r in ontology.relations.values()
            if r.relation_type == "SUBCLASS_OF"
        ]
        if subclass_relations:
            # Group by target (parent concept)
            parent_groups: dict[str, list[str]] = {}
            for rel in subclass_relations:
                parent = rel.target_id
                if parent not in parent_groups:
                    parent_groups[parent] = []
                parent_groups[parent].append(rel.source_id)

            for parent_id, child_ids in parent_groups.items():
                parent_concept = ontology.get_concept(parent_id)
                parent_name = parent_concept.name if parent_concept else parent_id
                taxonomy = Taxonomy(
                    id=f"taxonomy_{parent_id}",
                    name=f"{parent_name} hierarchy",
                    parent_id=parent_id,
                    concepts=child_ids,
                )
                ontology.add_taxonomy(taxonomy)

        logger.info(
            f"Extracted ontology '{oid}' from IR: "
            f"{len(ontology.concepts)} concepts, "
            f"{len(ontology.relations)} relations, "
            f"{len(ontology.taxonomies)} taxonomies"
        )
        return ontology

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _make_edge(
        edge_id: str,
        source: str,
        target: str,
        edge_type: str,
        **extra: Any,
    ) -> dict[str, Any]:
        """Create an edge dict for the IR graph.

        Args:
            edge_id: Unique edge identifier.
            source: Source node ID.
            target: Target node ID.
            edge_type: Edge type string.
            **extra: Additional properties to include.

        Returns:
            An edge dict in IR format.
        """
        edge: dict[str, Any] = {
            "id": edge_id,
            "source": source,
            "target": target,
            "type": edge_type,
            "directed": True,
        }
        edge.update(extra)
        return edge
