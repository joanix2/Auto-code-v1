"""
MetamodelEdge Repository - Database operations for metamodel edges (DOMAIN, RANGE, HAS_ATTRIBUTE, SUBCLASS_OF)
"""
from typing import List, Dict, Any, Optional
import logging

from ...base import BaseRepository, convert_neo4j_types
from src.models.MDE.M2 import MetamodelEdge, MetamodelEdgeType

logger = logging.getLogger(__name__)


class MetamodelEdgeRepository(BaseRepository[MetamodelEdge]):
    """Repository for metamodel edge CRUD operations"""

    def __init__(self, db):
        super().__init__(db, MetamodelEdge, "MetamodelEdge")

    async def get_by_metamodel(self, metamodel_id: str) -> List[MetamodelEdge]:
        """
        Get all edges (connections) for a specific metamodel
        
        Récupère tous les types d'edges:
        - DOMAIN: (Relation)-[:DOMAIN]->(Concept)
        - RANGE: (Relation)-[:RANGE]->(Concept)
        - HAS_ATTRIBUTE: (Concept)-[:HAS_ATTRIBUTE]->(Attribute)
        - SUBCLASS_OF: (Concept)-[:SUBCLASS_OF]->(Concept)
        
        Args:
            metamodel_id: ID du metamodel
            
        Returns:
            List[MetamodelEdge]: Liste de tous les edges du metamodel
        """
        edges = []
        
        # 1. Récupérer les edges DOMAIN (Relation → Concept source)
        domain_edges = await self._get_domain_edges(metamodel_id)
        edges.extend(domain_edges)
        
        # 2. Récupérer les edges RANGE (Relation → Concept target)
        range_edges = await self._get_range_edges(metamodel_id)
        edges.extend(range_edges)
        
        # 3. Récupérer les edges HAS_ATTRIBUTE (Concept → Attribute)
        attribute_edges = await self._get_has_attribute_edges(metamodel_id)
        edges.extend(attribute_edges)
        
        # 4. Récupérer les edges SUBCLASS_OF (Concept → Concept parent)
        subclass_edges = await self._get_subclass_of_edges(metamodel_id)
        edges.extend(subclass_edges)
        
        logger.info(f"Found {len(edges)} edges for metamodel {metamodel_id}")
        return edges

    async def _get_domain_edges(self, metamodel_id: str) -> List[MetamodelEdge]:
        """Récupérer les edges DOMAIN: (Relation)-[:DOMAIN]->(Concept)"""
        query = """
        MATCH (metamodel:Metamodel {id: $metamodel_id})
        MATCH (metamodel)-[:HAS_RELATION]->(rel:Relationship)
        MATCH (rel)-[edge:DOMAIN]->(concept:Concept)
        RETURN 
            rel.id as source_id,
            rel.name as source_label,
            concept.id as target_id,
            concept.name as target_label,
            'domain' as edge_type,
            $metamodel_id as graph_id
        """
        
        result = self.db.execute_query(query, {"metamodel_id": metamodel_id})
        
        edges = []
        for record in result:
            edge_data = {
                "id": f"domain-{record['source_id']}-{record['target_id']}",
                "name": f"domain-{record['source_label']}-{record['target_label']}",
                "edge_type": MetamodelEdgeType.DOMAIN,
                "source_id": record["source_id"],
                "target_id": record["target_id"],
                "source_label": record["source_label"],
                "target_label": record["target_label"],
                "graph_id": metamodel_id,
                "description": f"Domain of {record['source_label']}"
            }
            edges.append(MetamodelEdge(**edge_data))
        
        logger.debug(f"Found {len(edges)} DOMAIN edges")
        return edges

    async def _get_range_edges(self, metamodel_id: str) -> List[MetamodelEdge]:
        """Récupérer les edges RANGE: (Relation)-[:RANGE]->(Concept)"""
        query = """
        MATCH (metamodel:Metamodel {id: $metamodel_id})
        MATCH (metamodel)-[:HAS_RELATION]->(rel:Relationship)
        MATCH (rel)-[edge:RANGE]->(concept:Concept)
        RETURN 
            rel.id as source_id,
            rel.name as source_label,
            concept.id as target_id,
            concept.name as target_label,
            'range' as edge_type,
            $metamodel_id as graph_id
        """
        
        result = self.db.execute_query(query, {"metamodel_id": metamodel_id})
        
        edges = []
        for record in result:
            edge_data = {
                "id": f"range-{record['source_id']}-{record['target_id']}",
                "name": f"range-{record['source_label']}-{record['target_label']}",
                "edge_type": MetamodelEdgeType.RANGE,
                "source_id": record["source_id"],
                "target_id": record["target_id"],
                "source_label": record["source_label"],
                "target_label": record["target_label"],
                "graph_id": metamodel_id,
                "description": f"Range of {record['source_label']}"
            }
            edges.append(MetamodelEdge(**edge_data))
        
        logger.debug(f"Found {len(edges)} RANGE edges")
        return edges

    async def _get_has_attribute_edges(self, metamodel_id: str) -> List[MetamodelEdge]:
        """Récupérer les edges HAS_ATTRIBUTE: (Concept)-[:HAS_ATTRIBUTE]->(Attribute)"""
        query = """
        MATCH (metamodel:Metamodel {id: $metamodel_id})
        MATCH (metamodel)-[:HAS_CONCEPT]->(concept:Concept)
        MATCH (concept)-[edge:HAS_ATTRIBUTE]->(attr:Attribute)
        RETURN 
            concept.id as source_id,
            concept.name as source_label,
            attr.id as target_id,
            attr.name as target_label,
            'has_attribute' as edge_type,
            $metamodel_id as graph_id
        """
        
        result = self.db.execute_query(query, {"metamodel_id": metamodel_id})
        
        edges = []
        for record in result:
            edge_data = {
                "id": f"has_attribute-{record['source_id']}-{record['target_id']}",
                "name": f"has_attribute-{record['source_label']}-{record['target_label']}",
                "edge_type": MetamodelEdgeType.HAS_ATTRIBUTE,
                "source_id": record["source_id"],
                "target_id": record["target_id"],
                "source_label": record["source_label"],
                "target_label": record["target_label"],
                "graph_id": metamodel_id,
                "description": f"{record['source_label']} has {record['target_label']}"
            }
            edges.append(MetamodelEdge(**edge_data))
        
        logger.debug(f"Found {len(edges)} HAS_ATTRIBUTE edges")
        return edges

    async def _get_subclass_of_edges(self, metamodel_id: str) -> List[MetamodelEdge]:
        """Récupérer les edges SUBCLASS_OF: (Concept)-[:SUBCLASS_OF]->(Concept parent)"""
        query = """
        MATCH (metamodel:Metamodel {id: $metamodel_id})
        MATCH (metamodel)-[:HAS_CONCEPT]->(child:Concept)
        MATCH (child)-[edge:SUBCLASS_OF]->(parent:Concept)
        RETURN 
            child.id as source_id,
            child.name as source_label,
            parent.id as target_id,
            parent.name as target_label,
            'subclass_of' as edge_type,
            $metamodel_id as graph_id
        """
        
        result = self.db.execute_query(query, {"metamodel_id": metamodel_id})
        
        edges = []
        for record in result:
            edge_data = {
                "id": f"subclass_of-{record['source_id']}-{record['target_id']}",
                "name": f"subclass_of-{record['source_label']}-{record['target_label']}",
                "edge_type": MetamodelEdgeType.SUBCLASS_OF,
                "source_id": record["source_id"],
                "target_id": record["target_id"],
                "source_label": record["source_label"],
                "target_label": record["target_label"],
                "graph_id": metamodel_id,
                "description": f"{record['source_label']} is a {record['target_label']}"
            }
            edges.append(MetamodelEdge(**edge_data))
        
        logger.debug(f"Found {len(edges)} SUBCLASS_OF edges")
        return edges

    async def get_by_type(self, metamodel_id: str, edge_type: MetamodelEdgeType) -> List[MetamodelEdge]:
        """
        Get edges of a specific type for a metamodel
        
        Args:
            metamodel_id: ID du metamodel
            edge_type: Type d'edge (DOMAIN, RANGE, HAS_ATTRIBUTE, SUBCLASS_OF)
            
        Returns:
            List[MetamodelEdge]: Liste des edges du type spécifié
        """
        if edge_type == MetamodelEdgeType.DOMAIN:
            return await self._get_domain_edges(metamodel_id)
        elif edge_type == MetamodelEdgeType.RANGE:
            return await self._get_range_edges(metamodel_id)
        elif edge_type == MetamodelEdgeType.HAS_ATTRIBUTE:
            return await self._get_has_attribute_edges(metamodel_id)
        elif edge_type == MetamodelEdgeType.SUBCLASS_OF:
            return await self._get_subclass_of_edges(metamodel_id)
        else:
            logger.warning(f"Unknown edge type: {edge_type}")
            return []

    async def create_edge(
        self, 
        metamodel_id: str,
        source_id: str,
        target_id: str,
        edge_type: MetamodelEdgeType
    ) -> MetamodelEdge:
        """
        Create a new edge between two nodes
        
        Args:
            metamodel_id: ID du metamodel
            source_id: ID du noeud source
            target_id: ID du noeud cible
            edge_type: Type d'edge à créer
            
        Returns:
            MetamodelEdge: L'edge créé
        """
        # Déterminer les types de noeuds selon le type d'edge
        if edge_type == MetamodelEdgeType.DOMAIN:
            # DOMAIN: Relation → Concept
            query = """
            MATCH (rel:Relationship {id: $source_id})
            MATCH (concept:Concept {id: $target_id})
            MERGE (rel)-[edge:DOMAIN]->(concept)
            RETURN rel.id as source_id, rel.name as source_label,
                   concept.id as target_id, concept.name as target_label
            """
        elif edge_type == MetamodelEdgeType.RANGE:
            # RANGE: Relation → Concept
            query = """
            MATCH (rel:Relationship {id: $source_id})
            MATCH (concept:Concept {id: $target_id})
            MERGE (rel)-[edge:RANGE]->(concept)
            RETURN rel.id as source_id, rel.name as source_label,
                   concept.id as target_id, concept.name as target_label
            """
        elif edge_type == MetamodelEdgeType.HAS_ATTRIBUTE:
            # HAS_ATTRIBUTE: Concept → Attribute
            query = """
            MATCH (concept:Concept {id: $source_id})
            MATCH (attr:Attribute {id: $target_id})
            MERGE (concept)-[edge:HAS_ATTRIBUTE]->(attr)
            SET attr.concept_id = $source_id
            RETURN concept.id as source_id, concept.name as source_label,
                   attr.id as target_id, attr.name as target_label
            """
        elif edge_type == MetamodelEdgeType.SUBCLASS_OF:
            # SUBCLASS_OF: Concept → Concept
            query = """
            MATCH (child:Concept {id: $source_id})
            MATCH (parent:Concept {id: $target_id})
            MERGE (child)-[edge:SUBCLASS_OF]->(parent)
            RETURN child.id as source_id, child.name as source_label,
                   parent.id as target_id, parent.name as target_label
            """
        else:
            raise ValueError(f"Unknown edge type: {edge_type}")
        
        result = self.db.execute_query(
            query,
            {"source_id": source_id, "target_id": target_id}
        )
        
        if not result:
            raise ValueError(f"Failed to create {edge_type.value} edge from {source_id} to {target_id}")
        
        record = result[0]
        edge_data = {
            "id": f"{edge_type.value}-{source_id}-{target_id}",
            "name": f"{edge_type.value}-{record['source_label']}-{record['target_label']}",
            "edge_type": edge_type,
            "source_id": record["source_id"],
            "target_id": record["target_id"],
            "source_label": record["source_label"],
            "target_label": record["target_label"],
            "graph_id": metamodel_id,
            "description": f"{edge_type.value} edge"
        }
        
        edge = MetamodelEdge(**edge_data)
        logger.info(f"Created {edge_type.value} edge: {source_id} → {target_id}")
        return edge

    async def delete_edge(
        self,
        source_id: str,
        target_id: str,
        edge_type: MetamodelEdgeType
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
        
        result = self.db.execute_query(
            query,
            {"source_id": source_id, "target_id": target_id}
        )
        
        deleted = result[0]["deleted_count"] > 0 if result else False
        
        if deleted:
            logger.info(f"Deleted {edge_type.value} edge: {source_id} → {target_id}")
        else:
            logger.warning(f"Edge not found: {edge_type.value} {source_id} → {target_id}")
        
        return deleted
