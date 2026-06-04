"""
Query Service - Stateless graph query operations

Provides selectors, entity tree extraction, and graph traversal
functions that work directly with Neo4j through the existing repositories.
"""

from __future__ import annotations

import logging
from typing import Any

from src.repositories.MDE.M2.attribute_repository import AttributeRepository
from src.repositories.MDE.M2.concept_repository import ConceptRepository
from src.repositories.MDE.M2.metamodel_edge_repository import MetamodelEdgeRepository
from src.repositories.MDE.M2.metamodel_repository import MetamodelRepository
from src.repositories.MDE.M2.relationship_repository import RelationshipRepository
from src.repositories.base import convert_neo4j_types

logger = logging.getLogger(__name__)

# Mapping of node kind strings to Neo4j labels
NODE_KIND_LABELS: dict[str, str] = {
    "concept": "Concept",
    "attribute": "Attribute",
    "relation": "Relationship",
    "metamodel": "Metamodel",
}

# Mapping of edge kind strings to Neo4j relationship types
EDGE_KIND_TYPES: dict[str, str] = {
    "domain": "DOMAIN",
    "range": "RANGE",
    "has_attribute": "HAS_ATTRIBUTE",
    "subclass_of": "SUBCLASS_OF",
}


class QueryService:
    """Service providing graph query operations.
    
    All methods are read-only — they never modify the graph.
    Results are deterministic (same query = same result).
    """

    def __init__(self, db):
        """Initialize with a Neo4j connection and repositories.
        
        Args:
            db: Neo4jConnection instance (or MockNeo4jDB in tests)
        """
        self.db = db
        self.concept_repo = ConceptRepository(db)
        self.attribute_repo = AttributeRepository(db)
        self.relationship_repo = RelationshipRepository(db)
        self.edge_repo = MetamodelEdgeRepository(db)
        self.metamodel_repo = MetamodelRepository(db)

    # ------------------------------------------------------------------
    # Selectors
    # ------------------------------------------------------------------

    def get_nodes_by_kind(
        self, kind: str, graph_id: str | None = None
    ) -> list[dict[str, Any]]:
        """Get all nodes of a given kind (concept, attribute, relation, metamodel).
        
        Args:
            kind: Node type name — one of 'concept', 'attribute', 'relation', 'metamodel'.
            graph_id: Optional graph/metamodel ID to scope results.
            
        Returns:
            List of node dicts with Neo4j-native types converted.
            
        Raises:
            ValueError: If kind is unknown.
        """
        label = NODE_KIND_LABELS.get(kind)
        if label is None:
            raise ValueError(
                f"Unknown node kind '{kind}'. "
                f"Valid kinds: {', '.join(NODE_KIND_LABELS)}"
            )

        if graph_id:
            query = f"""
            MATCH (n:{label} {{graph_id: $graph_id}})
            RETURN n
            ORDER BY n.name
            """
            params = {"graph_id": graph_id}
        else:
            query = f"""
            MATCH (n:{label})
            RETURN n
            ORDER BY n.name
            """
            params = {}

        result = self.db.execute_query(query, params)
        nodes = []
        for row in result:
            node_data = convert_neo4j_types(row["n"])
            node_data["_kind"] = kind
            nodes.append(node_data)
        return nodes

    def get_edges_by_kind(
        self, kind: str, graph_id: str | None = None
    ) -> list[dict[str, Any]]:
        """Get all edges/relationships of a given kind.
        
        Note: In the Neo4j schema, edges are stored as Neo4j relationships
        with types like DOMAIN, RANGE, HAS_ATTRIBUTE, SUBCLASS_OF.
        
        Args:
            kind: Edge type name — one of 'domain', 'range', 'has_attribute', 'subclass_of'.
            graph_id: Optional graph/metamodel ID to scope results.
            
        Returns:
            List of edge dicts with source, target, and properties.
            
        Raises:
            ValueError: If kind is unknown.
        """
        rel_type = EDGE_KIND_TYPES.get(kind)
        if rel_type is None:
            raise ValueError(
                f"Unknown edge kind '{kind}'. "
                f"Valid kinds: {', '.join(EDGE_KIND_TYPES)}"
            )

        if graph_id:
            # Nodes are scoped by graph_id; we match both source and target
            query = f"""
            MATCH (source)-[r:{rel_type}]->(target)
            WHERE source.graph_id = $graph_id AND target.graph_id = $graph_id
            RETURN source.id AS source_id,
                   source.name AS source_label,
                   target.id AS target_id,
                   target.name AS target_label,
                   r
            ORDER BY source.name, target.name
            """
            params = {"graph_id": graph_id}
        else:
            query = f"""
            MATCH (source)-[r:{rel_type}]->(target)
            RETURN source.id AS source_id,
                   source.name AS source_label,
                   target.id AS target_id,
                   target.name AS target_label,
                   r
            ORDER BY source.name, target.name
            """
            params = {}

        result = self.db.execute_query(query, params)
        edges = []
        for row in result:
            edge_data = {
                "id": f"{kind}-{row['source_id']}-{row['target_id']}",
                "kind": kind,
                "type": rel_type,
                "source_id": row["source_id"],
                "source_label": row["source_label"],
                "target_id": row["target_id"],
                "target_label": row["target_label"],
            }
            # Add any relationship properties
            rel_node = row.get("r")
            if rel_node and hasattr(rel_node, "items"):
                props = convert_neo4j_types(dict(rel_node.items()))
                edge_data["properties"] = {
                    k: v for k, v in props.items()
                    if k not in ("id", "source_id", "target_id")
                }
            edges.append(edge_data)
        return edges

    def get_neighbors(
        self, node_id: str, graph_id: str | None = None
    ) -> list[dict[str, Any]]:
        """Get all neighboring nodes connected to a given node via any edge.
        
        Args:
            node_id: ID of the node to find neighbors for.
            graph_id: Optional graph/metamodel ID to scope results.
            
        Returns:
            List of neighbor node dicts, each with an added '_via' key
            describing the edge type that connects them.
        """
        params: dict[str, Any] = {"node_id": node_id}
        graph_filter = ""
        if graph_id:
            graph_filter = "AND n.graph_id = $graph_id"

        query = f"""
        MATCH (n {{id: $node_id}})
        OPTIONAL MATCH (n)-[r]->(neighbor)
        WHERE neighbor IS NOT NULL {graph_filter}
        RETURN neighbor, type(r) AS edge_type, 'outgoing' AS direction
        UNION
        MATCH (n {{id: $node_id}})
        OPTIONAL MATCH (neighbor)-[r]->(n)
        WHERE neighbor IS NOT NULL {graph_filter}
        RETURN neighbor, type(r) AS edge_type, 'incoming' AS direction
        """
        result = self.db.execute_query(query, params)
        seen: set[str] = set()
        neighbors = []
        for row in result:
            neighbor_data = row.get("neighbor")
            if neighbor_data is None:
                continue
            node_dict = convert_neo4j_types(dict(neighbor_data.items()))
            nid = node_dict.get("id")
            if nid in seen:
                continue
            seen.add(nid)
            node_dict["_via"] = {
                "edge_type": row["edge_type"],
                "direction": row["direction"],
            }
            neighbors.append(node_dict)
        return neighbors

    def get_incident_edges(
        self, node_id: str, graph_id: str | None = None
    ) -> list[dict[str, Any]]:
        """Get all edges incident to a given node.
        
        Args:
            node_id: ID of the node.
            graph_id: Optional graph/metamodel ID to scope results.
            
        Returns:
            List of edge dicts with direction (incoming/outgoing).
        """
        params: dict[str, Any] = {"node_id": node_id}
        graph_filter = ""
        if graph_id:
            graph_filter = (
                "AND (source.graph_id = $graph_id OR target.graph_id = $graph_id)"
            )

        # Outgoing edges
        query = f"""
        MATCH (source)-[r]->(target)
        WHERE source.id = $node_id {graph_filter}
        RETURN source.id AS source_id,
               source.name AS source_label,
               target.id AS target_id,
               target.name AS target_label,
               type(r) AS edge_type,
               'outgoing' AS direction
        UNION
        MATCH (source)-[r]->(target)
        WHERE target.id = $node_id {graph_filter}
        RETURN source.id AS source_id,
               source.name AS source_label,
               target.id AS target_id,
               target.name AS target_label,
               type(r) AS edge_type,
               'incoming' AS direction
        """
        result = self.db.execute_query(query, params)
        edges = []
        for row in result:
            edges.append({
                "id": f"{row['edge_type'].lower()}-{row['source_id']}-{row['target_id']}",
                "type": row["edge_type"],
                "direction": row["direction"],
                "source_id": row["source_id"],
                "source_label": row["source_label"],
                "target_id": row["target_id"],
                "target_label": row["target_label"],
            })
        return edges

    # ------------------------------------------------------------------
    # Entity Tree extraction
    # ------------------------------------------------------------------

    def get_entity_tree(
        self,
        root_id: str,
        max_depth: int = 5,
        graph_id: str | None = None,
        _visited: set[str] | None = None,
        _depth: int = 0,
    ) -> dict[str, Any] | None:
        """Build a recursive JSON entity tree from a root node.
        
        The tree structure is:
        {
          "entity": { node attributes },
          "fields": [ attribute-like connected nodes ],
          "relations": [ recursive entity tree for other connected nodes ]
        }
        
        This structure is designed to be consumed directly by Jinja2 templates.
        
        Args:
            root_id: ID of the root node.
            max_depth: Maximum recursion depth (default 5).
            graph_id: Optional graph/metamodel ID to scope the query.
            _visited: Internal set for cycle detection (do not pass externally).
            _depth: Internal recursion depth counter.
            
        Returns:
            Entity tree dict, or None if the root node is not found.
            
        Note:
            Cycle detection prevents infinite loops by tracking visited node IDs.
        """
        if _visited is None:
            _visited = set()

        # Prevent infinite recursion
        if _depth > max_depth:
            return None

        # Prevent cycles
        if root_id in _visited:
            return None
        _visited.add(root_id)

        # Get the root node data
        root_node = self._get_node_by_id(root_id)
        if root_node is None:
            return None

        tree: dict[str, Any] = {
            "entity": root_node,
            "fields": [],
            "relations": [],
        }

        # Find all incident edges to determine what's connected
        incident_edges = self.get_incident_edges(root_id, graph_id)
        processed: set[str] = set()

        for edge in incident_edges:
            # Determine the connected node ID
            if edge["direction"] == "outgoing":
                connected_id = edge["target_id"]
            else:
                connected_id = edge["source_id"]

            if connected_id in processed:
                continue
            processed.add(connected_id)

            # Fetch the connected node data
            connected_node = self._get_node_by_id(connected_id)
            if connected_node is None:
                continue

            edge_type = edge["type"].lower()

            # Categorize:
            # - Attributes linked via HAS_ATTRIBUTE or ATTRIBUTE_OF → "fields"
            # - Everything else → "relations" (with recursive tree)
            is_field = (
                edge_type in ("has_attribute", "attribute_of")
                or connected_node.get("_kind") == "attribute"
            )

            if is_field:
                # Flatten as a field (no recursion for attributes)
                tree["fields"].append({
                    "entity": connected_node,
                    "edge_type": edge["type"],
                    "direction": edge["direction"],
                })
            else:
                # Recursive relation tree (if not visited and depth allows)
                if connected_id not in _visited and _depth + 1 <= max_depth:
                    subtree = self.get_entity_tree(
                        root_id=connected_id,
                        max_depth=max_depth,
                        graph_id=graph_id,
                        _visited=_visited,
                        _depth=_depth + 1,
                    )
                    if subtree is not None:
                        subtree["_edge_type"] = edge["type"]
                        subtree["_direction"] = edge["direction"]
                        tree["relations"].append(subtree)

        return tree

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_node_by_id(self, node_id: str) -> dict[str, Any] | None:
        """Fetch any node by ID regardless of its label.
        
        Tries each known node label to find the node.
        
        Args:
            node_id: The node's unique ID.
            
        Returns:
            Node dict with converted types, or None if not found.
        """
        for kind, label in NODE_KIND_LABELS.items():
            query = f"""
            MATCH (n:{label} {{id: $id}})
            RETURN n
            """
            result = self.db.execute_query(query, {"id": node_id})
            if result:
                node_data = convert_neo4j_types(dict(result[0]["n"].items()))
                node_data["_kind"] = kind
                return node_data

        # Fallback: search across all nodes with this ID
        query = """
        MATCH (n {id: $id})
        RETURN n, labels(n) AS node_labels
        LIMIT 1
        """
        result = self.db.execute_query(query, {"id": node_id})
        if result:
            node_data = convert_neo4j_types(dict(result[0]["n"].items()))
            labels = result[0].get("node_labels", [])
            if labels:
                node_data["_kind"] = labels[0].lower()
            return node_data

        return None

    # ------------------------------------------------------------------
    # Pattern matching
    # ------------------------------------------------------------------

    def find_pattern(
        self,
        pattern: list[dict[str, Any]],
        graph_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Simple sub-graph pattern matching.
        
        Given a list of node specifiers with optional edge constraints,
        finds all matching sub-graphs in the database.
        
        Each pattern element is a dict with:
        - 'alias': str (variable name for the match)
        - 'kind': str | None (node kind: concept, attribute, relation, metamodel)
        - 'edges': list of dicts with:
            - 'to': str (alias of target node)
            - 'type': str | None (edge type to match)
            - 'direction': 'outgoing' | 'incoming' (default: 'outgoing')
        
        Example:
            pattern = [
                {"alias": "a", "kind": "concept"},
                {"alias": "b", "kind": "concept",
                 "edges": [{"to": "a", "type": "SUBCLASS_OF"}]},
            ]
        
        Args:
            pattern: List of node specifiers.
            graph_id: Optional graph/metamodel ID to scope.
            
        Returns:
            List of matched sub-graphs, each being a dict of alias → node data.
        """
        if not pattern:
            return []

        # Build MATCH clauses
        match_parts: list[str] = []
        where_parts: list[str] = []
        return_clauses: list[str] = []
        params: dict[str, Any] = {}
        param_idx = 0

        for spec in pattern:
            alias = spec["alias"]
            kind = spec.get("kind")
            label = NODE_KIND_LABELS.get(kind) if kind else None

            if label:
                match_parts.append(f"({alias}:{label})")
            else:
                match_parts.append(f"({alias})")

            return_clauses.append(alias)

            # Handle graph_id scope
            if graph_id:
                param_name = f"graph_id_{param_idx}"
                param_idx += 1
                where_parts.append(f"{alias}.graph_id = ${param_name}")
                params[param_name] = graph_id

            # Handle edge constraints
            edges = spec.get("edges", [])
            for edge_spec in edges:
                target_alias = edge_spec["to"]
                edge_type = edge_spec.get("type")
                direction = edge_spec.get("direction", "outgoing")

                if direction == "incoming":
                    if edge_type:
                        match_parts.append(
                            f"({alias})<-[{alias}_to_{target_alias}:{edge_type}]-({target_alias})"
                        )
                    else:
                        match_parts.append(
                            f"({alias})<-[{alias}_to_{target_alias}]-({target_alias})"
                        )
                else:
                    if edge_type:
                        match_parts.append(
                            f"({alias})-[{alias}_to_{target_alias}:{edge_type}]->({target_alias})"
                        )
                    else:
                        match_parts.append(
                            f"({alias})-[{alias}_to_{target_alias}]->({target_alias})"
                        )

        # Build final query
        match_clause = "MATCH " + ", ".join(match_parts)
        where_clause = ""
        if where_parts:
            where_clause = "WHERE " + " AND ".join(where_parts)
        return_clause = "RETURN " + ", ".join(f"DISTINCT {a}" for a in return_clauses)

        query = f"{match_clause} {where_clause} {return_clause}"
        logger.debug(f"Pattern query: {query}")

        result = self.db.execute_query(query, params)
        matches = []
        for row in result:
            match_dict: dict[str, Any] = {}
            for alias in return_clauses:
                node_data = row.get(alias)
                if node_data is not None:
                    converted = convert_neo4j_types(dict(node_data.items()))
                    match_dict[alias] = converted
            matches.append(match_dict)
        return matches
