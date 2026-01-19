from typing import List, Optional, Dict, Any
from ...base_service import BaseService
from ....repositories.MDE.M2.metamodel_repository import MetamodelRepository
from ....repositories.MDE.M2.concept_repository import ConceptRepository
from ....repositories.MDE.M2.attribute_repository import AttributeRepository
from ....repositories.MDE.M2.relationship_repository import RelationshipRepository
from ....repositories.MDE.M2.metamodel_edge_repository import MetamodelEdgeRepository
from src.models.MDE.M2 import Metamodel, MetamodelCreate, MetamodelUpdate
import logging

logger = logging.getLogger(__name__)


class MetamodelService(BaseService[Metamodel]):
    def __init__(
        self, 
        repository: MetamodelRepository,
        concept_repository: Optional[ConceptRepository] = None,
        attribute_repository: Optional[AttributeRepository] = None,
        relationship_repository: Optional[RelationshipRepository] = None,
        edge_repository: Optional[MetamodelEdgeRepository] = None
    ):
        """
        Initialize metamodel service
        
        Args:
            repository: MetamodelRepository instance
            concept_repository: ConceptRepository instance (optional)
            attribute_repository: AttributeRepository instance (optional)
            relationship_repository: RelationshipRepository instance (optional)
            edge_repository: MetamodelEdgeRepository instance (optional)
        """
        self.repository = repository
        self.concept_repository = concept_repository
        self.attribute_repository = attribute_repository
        self.relationship_repository = relationship_repository
        self.edge_repository = edge_repository

    # Implementation of BaseService interface
    
    async def create(self, data: Dict[str, Any]) -> Metamodel:
        """Create a new metamodel"""
        logger.info(f"🚀 Service: Creating metamodel: {data.get('name')}")
        return await self.repository.create(data)
    
    async def get_by_id(self, entity_id: str) -> Optional[Metamodel]:
        """Get metamodel by ID"""
        logger.info(f"🔍 Service: Getting metamodel by ID: {entity_id}")
        return await self.repository.get_by_id(entity_id)
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Metamodel]:
        """Get all metamodels with optional pagination"""
        logger.info(f"🔍 Service: Getting all metamodels (skip={skip}, limit={limit})")
        return await self.repository.get_all(skip, limit)
    
    async def update(self, entity_id: str, update_data: Dict[str, Any]) -> Optional[Metamodel]:
        """Update metamodel"""
        logger.info(f"✏️ Service: Updating metamodel: {entity_id}")
        return await self.repository.update(entity_id, update_data)
    
    async def delete(self, entity_id: str) -> bool:
        """Delete metamodel"""
        logger.info(f"🗑️ Service: Deleting metamodel: {entity_id}")
        return await self.repository.delete(entity_id)

    # Custom methods

    async def get_by_name(self, name: str) -> Optional[Metamodel]:
        """Get a metamodel by name"""
        logger.info(f"🔍 Service: Getting metamodel by name: {name}")
        return await self.repository.get_by_name(name)

    async def get_by_status(self, status: str) -> List[Metamodel]:
        """Get all metamodels with a specific status"""
        logger.info(f"🔍 Service: Getting metamodels with status: {status}")
        return await self.repository.get_by_status(status)

    async def get_by_author(self, author: str) -> List[Metamodel]:
        """Get all metamodels by author"""
        logger.info(f"🔍 Service: Getting metamodels by author: {author}")
        return await self.repository.get_by_author(author)

    async def validate_metamodel(self, metamodel_id: str) -> Metamodel:
        """Change metamodel status to validated"""
        logger.info(f"✅ Service: Validating metamodel: {metamodel_id}")
        return await self.update(metamodel_id, {"status": "validated"})

    async def deprecate_metamodel(self, metamodel_id: str) -> Metamodel:
        """Change metamodel status to deprecated"""
        logger.info(f"⚠️ Service: Deprecating metamodel: {metamodel_id}")
        return await self.update(metamodel_id, {"status": "deprecated"})

    async def get_metamodel_with_graph(self, metamodel_id: str) -> Dict[str, Any]:
        """
        Get a complete metamodel with all its nodes and edges as a graph structure
        
        Returns a dictionary containing:
        - metamodel: The complete Metamodel object (not a dict)
        - nodes: List of all nodes with their graph representation
        - edges: List of all edges with their graph representation
        
        Args:
            metamodel_id: ID of the metamodel
            
        Returns:
            Dict with keys: metamodel, nodes, edges
        """
        logger.info(f"📊 Service: Getting complete metamodel graph: {metamodel_id}")
        
        # Récupérer le metamodel
        metamodel = await self.get_by_id(metamodel_id)
        if not metamodel:
            raise ValueError(f"Metamodel {metamodel_id} not found")
        
        nodes = []
        edges = []
        
        # Récupérer les Concepts
        if self.concept_repository:
            concepts = await self.concept_repository.get_by_metamodel(metamodel_id)
            nodes.extend([c.to_graph_dict() for c in concepts])
            logger.info(f"  ✓ Found {len(concepts)} concepts")
        
        # Récupérer TOUS les Attributs (standalone ET attachés à des concepts)
        if self.attribute_repository:
            attributes = await self.attribute_repository.get_by_metamodel(metamodel_id)
            nodes.extend([a.to_graph_dict() for a in attributes])
            logger.info(f"  ✓ Found {len(attributes)} attributes (standalone and attached)")
        
        # Récupérer les Relations
        if self.relationship_repository:
            relationships = await self.relationship_repository.get_by_metamodel(metamodel_id)
            nodes.extend([r.to_graph_dict() for r in relationships])
            logger.info(f"  ✓ Found {len(relationships)} relationships")
        
        # Créer un Set des IDs de nœuds existants
        node_ids = {node["id"] for node in nodes}
        logger.info(f"  📋 Total node IDs: {len(node_ids)}")
        
        # Récupérer les Edges
        if self.edge_repository:
            metamodel_edges = await self.edge_repository.get_by_metamodel(metamodel_id)
            
            # Filtrer les edges orphelins (qui pointent vers des nœuds inexistants)
            valid_edges = []
            orphaned_edges = []
            
            for edge in metamodel_edges:
                edge_dict = edge.to_graph_dict()
                has_valid_source = edge_dict["source"] in node_ids
                has_valid_target = edge_dict["target"] in node_ids
                
                if has_valid_source and has_valid_target:
                    valid_edges.append(edge_dict)
                else:
                    orphaned_edges.append({
                        "id": edge_dict["id"],
                        "source": edge_dict["source"],
                        "target": edge_dict["target"],
                        "type": edge_dict["type"],
                        "source_exists": has_valid_source,
                        "target_exists": has_valid_target
                    })
            
            edges = valid_edges
            
            if orphaned_edges:
                logger.warning(f"  ⚠️ Found {len(orphaned_edges)} orphaned edges (will be filtered out)")
                for orphan in orphaned_edges[:5]:  # Log first 5 only
                    logger.warning(f"    - Edge {orphan['id']}: source={orphan['source']} (exists={orphan['source_exists']}), target={orphan['target']} (exists={orphan['target_exists']})")
            
            logger.info(f"  ✓ Found {len(edges)} valid edges ({len(orphaned_edges)} orphaned edges filtered)")
        
        # Construire le résultat avec l'objet Metamodel complet
        result = {
            "metamodel": metamodel,  # Retourner l'objet complet, pas to_graph_dict()
            "nodes": nodes,  # Chaque node utilise to_graph_dict()
            "edges": edges,  # Chaque edge utilise to_graph_dict()
            "edgeConstraints": metamodel.allowed_edge_types  # Edge type constraints from the graph
        }
        
        logger.info(f"✅ Complete graph: {len(nodes)} nodes, {len(edges)} edges")
        return result
