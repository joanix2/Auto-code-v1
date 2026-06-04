"""
DSLEdge Repository - Database operations for dsl edges (DOMAIN, RANGE, HAS_ATTRIBUTE, SUBCLASS_OF)
"""

import logging
from typing import Any

from src.models.dsl import DSLEdge, DSLEdgeType

from ..base import BaseRepository

logger = logging.getLogger(__name__)


class DSLEdgeRepository(BaseRepository[DSLEdge]):
    """Repository for dsl edge CRUD operations"""

    def __init__(self, db):
        super().__init__(db, DSLEdge, "DSLEdge")

    async def get_by_dsl(self, dsl_id: str) -> list[DSLEdge]:
        """
        Get all edges (connections) for a specific dsl

        Récupère tous les types d'edges:
        - DOMAIN: (Relation)-[:DOMAIN]->(DSLConcept)
        - RANGE: (Relation)-[:RANGE]->(DSLConcept)
        - HAS_ATTRIBUTE: (DSLConcept)-[:HAS_ATTRIBUTE]->(DSLAttribute)
        - SUBCLASS_OF: (DSLConcept)-[:SUBCLASS_OF]->(DSLConcept)

        Args:
            dsl_id: ID du dsl

        Returns:
            List[DSLEdge]: Liste de tous les edges du dsl
        """
        edges = []

        # 1. Récupérer les edges DOMAIN (Relation → DSLConcept source)
        domain_edges = await self._get_domain_edges(dsl_id)
        edges.extend(domain_edges)

        # 2. Récupérer les edges RANGE (Relation → DSLConcept target)
        range_edges = await self._get_range_edges(dsl_id)
        edges.extend(range_edges)

        # 3. Récupérer les edges HAS_ATTRIBUTE (DSLConcept → DSLAttribute)
        attribute_edges = await self._get_has_attribute_edges(dsl_id)
        edges.extend(attribute_edges)

        # 4. Récupérer les edges SUBCLASS_OF (DSLConcept → DSLConcept parent)
        subclass_edges = await self._get_subclass_of_edges(dsl_id)
        edges.extend(subclass_edges)

        logger.info(f"Found {len(edges)} edges for dsl {dsl_id}")
        return edges

    async def _get_domain_edges(self, dsl_id: str) -> list[DSLEdge]:
        """Récupérer les edges DOMAIN: (Relation)-[:DOMAIN]->(DSLConcept)"""
        query = """
        MATCH (dsl:DSLGraph {id: $dsl_id})
        MATCH (dsl)-[:HAS_RELATION]->(rel:DSLRelation)
        MATCH (rel)-[edge:DOMAIN]->(concept:DSLConcept)
        RETURN 
            rel.id as source_id,
            rel.name as source_label,
            concept.id as target_id,
            concept.name as target_label,
            'domain' as edge_type,
            $dsl_id as graph_id
        """

        result = self.db.execute_query(query, {"dsl_id": dsl_id})

        edges = []
        for record in result:
            edge_data = {
                "id": f"domain-{record['source_id']}-{record['target_id']}",
                "name": f"domain-{record['source_label']}-{record['target_label']}",
                "edge_type": DSLEdgeType.DOMAIN,
                "source_id": record["source_id"],
                "target_id": record["target_id"],
                "source_label": record["source_label"],
                "target_label": record["target_label"],
                "graph_id": dsl_id,
                "description": f"Domain of {record['source_label']}",
            }
            edges.append(DSLEdge(**edge_data))

        logger.debug(f"Found {len(edges)} DOMAIN edges")
        return edges

    async def _get_range_edges(self, dsl_id: str) -> list[DSLEdge]:
        """Récupérer les edges RANGE: (Relation)-[:RANGE]->(DSLConcept)"""
        query = """
        MATCH (dsl:DSLGraph {id: $dsl_id})
        MATCH (dsl)-[:HAS_RELATION]->(rel:DSLRelation)
        MATCH (rel)-[edge:RANGE]->(concept:DSLConcept)
        RETURN 
            rel.id as source_id,
            rel.name as source_label,
            concept.id as target_id,
            concept.name as target_label,
            'range' as edge_type,
            $dsl_id as graph_id
        """

        result = self.db.execute_query(query, {"dsl_id": dsl_id})

        edges = []
        for record in result:
            edge_data = {
                "id": f"range-{record['source_id']}-{record['target_id']}",
                "name": f"range-{record['source_label']}-{record['target_label']}",
                "edge_type": DSLEdgeType.RANGE,
                "source_id": record["source_id"],
                "target_id": record["target_id"],
                "source_label": record["source_label"],
                "target_label": record["target_label"],
                "graph_id": dsl_id,
                "description": f"Range of {record['source_label']}",
            }
            edges.append(DSLEdge(**edge_data))

        logger.debug(f"Found {len(edges)} RANGE edges")
        return edges

    async def _get_has_attribute_edges(self, dsl_id: str) -> list[DSLEdge]:
        """Récupérer les edges HAS_ATTRIBUTE: (DSLConcept)-[:HAS_ATTRIBUTE]->(DSLAttribute)"""
        query = """
        MATCH (dsl:DSLGraph {id: $dsl_id})
        MATCH (dsl)-[:HAS_CONCEPT]->(concept:DSLConcept)
        MATCH (concept)-[edge:HAS_ATTRIBUTE]->(attr:DSLAttribute)
        RETURN 
            concept.id as source_id,
            concept.name as source_label,
            attr.id as target_id,
            attr.name as target_label,
            'has_attribute' as edge_type,
            $dsl_id as graph_id
        """

        result = self.db.execute_query(query, {"dsl_id": dsl_id})

        edges = []
        for record in result:
            edge_data = {
                "id": f"has_attribute-{record['source_id']}-{record['target_id']}",
                "name": f"has_attribute-{record['source_label']}-{record['target_label']}",
                "edge_type": DSLEdgeType.HAS_ATTRIBUTE,
                "source_id": record["source_id"],
                "target_id": record["target_id"],
                "source_label": record["source_label"],
                "target_label": record["target_label"],
                "graph_id": dsl_id,
                "description": f"{record['source_label']} has {record['target_label']}",
            }
            edges.append(DSLEdge(**edge_data))

        logger.debug(f"Found {len(edges)} HAS_ATTRIBUTE edges")
        return edges

    async def _get_subclass_of_edges(self, dsl_id: str) -> list[DSLEdge]:
        """Récupérer les edges SUBCLASS_OF: (DSLConcept)-[:SUBCLASS_OF]->(DSLConcept parent)"""
        query = """
        MATCH (dsl:DSLGraph {id: $dsl_id})
        MATCH (dsl)-[:HAS_CONCEPT]->(child:DSLConcept)
        MATCH (child)-[edge:SUBCLASS_OF]->(parent:DSLConcept)
        RETURN 
            child.id as source_id,
            child.name as source_label,
            parent.id as target_id,
            parent.name as target_label,
            'subclass_of' as edge_type,
            $dsl_id as graph_id
        """

        result = self.db.execute_query(query, {"dsl_id": dsl_id})

        edges = []
        for record in result:
            edge_data = {
                "id": f"subclass_of-{record['source_id']}-{record['target_id']}",
                "name": f"subclass_of-{record['source_label']}-{record['target_label']}",
                "edge_type": DSLEdgeType.SUBCLASS_OF,
                "source_id": record["source_id"],
                "target_id": record["target_id"],
                "source_label": record["source_label"],
                "target_label": record["target_label"],
                "graph_id": dsl_id,
                "description": f"{record['source_label']} is a {record['target_label']}",
            }
            edges.append(DSLEdge(**edge_data))

        logger.debug(f"Found {len(edges)} SUBCLASS_OF edges")
        return edges

    async def get_by_type(
        self, dsl_id: str, edge_type: DSLEdgeType
    ) -> list[DSLEdge]:
        """
        Get edges of a specific type for a dsl

        Args:
            dsl_id: ID du dsl
            edge_type: Type d'edge (DOMAIN, RANGE, HAS_ATTRIBUTE, SUBCLASS_OF)

        Returns:
            List[DSLEdge]: Liste des edges du type spécifié
        """
        if edge_type == DSLEdgeType.DOMAIN:
            return await self._get_domain_edges(dsl_id)
        elif edge_type == DSLEdgeType.RANGE:
            return await self._get_range_edges(dsl_id)
        elif edge_type == DSLEdgeType.HAS_ATTRIBUTE:
            return await self._get_has_attribute_edges(dsl_id)
        elif edge_type == DSLEdgeType.SUBCLASS_OF:
            return await self._get_subclass_of_edges(dsl_id)
        else:
            logger.warning(f"Unknown edge type: {edge_type}")
            return []

    async def create_edge(
        self, dsl_id: str, source_id: str, target_id: str, edge_type: DSLEdgeType
    ) -> DSLEdge:
        """
        Create a new edge between two nodes

        Args:
            dsl_id: ID du dsl
            source_id: ID du noeud source
            target_id: ID du noeud cible
            edge_type: Type d'edge à créer

        Returns:
            DSLEdge: L'edge créé

        Raises:
            ValueError: Si l'edge existe déjà
        """
        # Vérifier si l'edge existe déjà
        edge_rel_type = edge_type.value.upper()
        check_query = f"""
        MATCH (source {{id: $source_id}})-[edge:{edge_rel_type}]->(target {{id: $target_id}})
        RETURN count(edge) as edge_count
        """

        check_result = self.db.execute_query(
            check_query, {"source_id": source_id, "target_id": target_id}
        )

        if check_result and check_result[0]["edge_count"] > 0:
            raise ValueError(
                f"Un lien de type {edge_type.value} existe déjà entre {source_id} et {target_id}"
            )

        # Déterminer les types de noeuds selon le type d'edge
        if edge_type == DSLEdgeType.DOMAIN:
            # DOMAIN: Relation → DSLConcept
            query = """
            MATCH (rel:DSLRelation {id: $source_id})
            MATCH (concept:DSLConcept {id: $target_id})
            MERGE (rel)-[edge:DOMAIN]->(concept)
            RETURN rel.id as source_id, rel.name as source_label,
                   concept.id as target_id, concept.name as target_label
            """
        elif edge_type == DSLEdgeType.RANGE:
            # RANGE: Relation → DSLConcept
            query = """
            MATCH (rel:DSLRelation {id: $source_id})
            MATCH (concept:DSLConcept {id: $target_id})
            MERGE (rel)-[edge:RANGE]->(concept)
            RETURN rel.id as source_id, rel.name as source_label,
                   concept.id as target_id, concept.name as target_label
            """
        elif edge_type == DSLEdgeType.HAS_ATTRIBUTE:
            # HAS_ATTRIBUTE: DSLConcept → DSLAttribute
            query = """
            MATCH (concept:DSLConcept {id: $source_id})
            MATCH (attr:DSLAttribute {id: $target_id})
            MERGE (concept)-[edge:HAS_ATTRIBUTE]->(attr)
            SET attr.concept_id = $source_id
            RETURN concept.id as source_id, concept.name as source_label,
                   attr.id as target_id, attr.name as target_label
            """
        elif edge_type == DSLEdgeType.SUBCLASS_OF:
            # SUBCLASS_OF: DSLConcept → DSLConcept
            query = """
            MATCH (child:DSLConcept {id: $source_id})
            MATCH (parent:DSLConcept {id: $target_id})
            MERGE (child)-[edge:SUBCLASS_OF]->(parent)
            RETURN child.id as source_id, child.name as source_label,
                   parent.id as target_id, parent.name as target_label
            """
        else:
            raise ValueError(f"Unknown edge type: {edge_type}")

        result = self.db.execute_query(query, {"source_id": source_id, "target_id": target_id})

        if not result:
            raise ValueError(
                f"Failed to create {edge_type.value} edge from {source_id} to {target_id}"
            )

        record = result[0]
        edge_data = {
            "id": f"{edge_type.value}-{source_id}-{target_id}",
            "name": f"{edge_type.value}-{record['source_label']}-{record['target_label']}",
            "edge_type": edge_type,
            "source_id": record["source_id"],
            "target_id": record["target_id"],
            "source_label": record["source_label"],
            "target_label": record["target_label"],
            "graph_id": dsl_id,
            "description": f"{edge_type.value} edge",
        }

        edge = DSLEdge(**edge_data)
        logger.info(f"Created {edge_type.value} edge: {source_id} → {target_id}")
        return edge

    async def update_edge(
        self, source_id: str, target_id: str, edge_type: DSLEdgeType, updates: dict[str, Any]
    ) -> DSLEdge | None:
        """
        Update an edge's metadata (e.g. description)

        Args:
            source_id: ID du noeud source
            target_id: ID du noeud cible
            edge_type: Type d'edge
            updates: Fields to update on the edge relationship

        Returns:
            Updated DSLEdge or None if not found
        """
        rel_type = edge_type.value.upper()

        set_clauses = ", ".join(
            f"edge.{k} = ${k}" for k in updates if k not in ("source_id", "target_id", "edge_type")
        )
        if not set_clauses:
            # Just return existing edge
            return None

        params = {"source_id": source_id, "target_id": target_id, **updates}

        query = f"""
        MATCH (source {{id: $source_id}})-[edge:{rel_type}]->(target {{id: $target_id}})
        SET {set_clauses}
        SET edge.updated_at = datetime()
        RETURN edge
        """

        result = self.db.execute_query(query, params)

        if not result:
            logger.warning(
                f"Edge not found for update: {edge_type.value} {source_id} → {target_id}"
            )
            return None

        logger.info(f"Updated {edge_type.value} edge: {source_id} → {target_id}")
        # Return a constructed edge object (Neo4j relationships have limited properties)
        edge_data = {
            "id": f"{edge_type.value}-{source_id}-{target_id}",
            "name": f"{edge_type.value}-edge",
            "edge_type": edge_type,
            "source_id": source_id,
            "target_id": target_id,
            "graph_id": "",
            "description": updates.get("description", ""),
        }
        return DSLEdge(**edge_data)

    async def delete_edge(
        self, source_id: str, target_id: str, edge_type: DSLEdgeType
    ) -> bool:
        """
        Delete an edge between two nodes

        Args:
            source_id: ID du noeud source
            target_id: ID du noeud cible
            edge_type: Type d'edge à supprimer

        Returns:
            bool: True si l'edge a été supprimé
        """
        # Construire le nom de la relation Neo4j
        rel_type = edge_type.value.upper().replace("_", "_")

        query = f"""
        MATCH (source {{id: $source_id}})-[edge:{rel_type}]->(target {{id: $target_id}})
        DELETE edge
        RETURN count(edge) as deleted_count
        """

        result = self.db.execute_query(query, {"source_id": source_id, "target_id": target_id})

        deleted = result[0]["deleted_count"] > 0 if result else False

        if deleted:
            logger.info(f"Deleted {edge_type.value} edge: {source_id} → {target_id}")
        else:
            logger.warning(f"Edge not found: {edge_type.value} {source_id} → {target_id}")

        return deleted
