"""
Repository pour la gestion des Relations dans Neo4j
"""
from typing import List, Optional
from datetime import datetime
import uuid

from src.models.relation import (
    Relation, RelationCreate, RelationUpdate,
    RelationType, RelationTypeCreate, RelationTypeUpdate
)
from src.database import db


class RelationTypeRepository:
    """Repository pour les types de relations"""
    
    @staticmethod
    def create(relation_type: RelationTypeCreate) -> RelationType:
        """Crée un nouveau type de relation"""
        type_id = f"reltype-{uuid.uuid4().hex[:12]}"
        now = datetime.utcnow()
        
        query = """
        MATCH (p:Project {id: $project_id})
        CREATE (rt:RelationType {
            id: $id,
            name: $name,
            description: $description,
            color: $color,
            properties_schema: $properties_schema,
            created_at: datetime($created_at),
            updated_at: datetime($updated_at)
        })
        CREATE (rt)-[:BELONGS_TO]->(p)
        RETURN rt
        """
        
        with db.get_session() as session:
            result = session.run(
                query,
                id=type_id,
                project_id=relation_type.project_id,
                name=relation_type.name,
                description=relation_type.description,
                color=relation_type.color or "#6B7280",
                properties_schema=relation_type.properties_schema or {},
                created_at=now.isoformat(),
                updated_at=now.isoformat()
            )
            record = result.single()
            if record:
                return RelationTypeRepository._node_to_type(record["rt"], relation_type.project_id)
            raise Exception("Erreur lors de la création du type de relation")
    
    @staticmethod
    def get_by_id(type_id: str) -> Optional[RelationType]:
        """Récupère un type de relation par son ID"""
        query = """
        MATCH (rt:RelationType {id: $type_id})-[:BELONGS_TO]->(p:Project)
        RETURN rt, p.id as project_id
        """
        
        with db.get_session() as session:
            result = session.run(query, type_id=type_id)
            record = result.single()
            if record:
                return RelationTypeRepository._node_to_type(record["rt"], record["project_id"])
            return None
    
    @staticmethod
    def get_by_project(project_id: str) -> List[RelationType]:
        """Récupère tous les types de relations d'un projet"""
        query = """
        MATCH (rt:RelationType)-[:BELONGS_TO]->(p:Project {id: $project_id})
        RETURN rt, p.id as project_id
        ORDER BY rt.name
        """
        
        with db.get_session() as session:
            result = session.run(query, project_id=project_id)
            return [RelationTypeRepository._node_to_type(record["rt"], record["project_id"]) for record in result]
    
    @staticmethod
    def update(type_id: str, type_update: RelationTypeUpdate) -> Optional[RelationType]:
        """Met à jour un type de relation"""
        update_fields = []
        params = {"type_id": type_id, "updated_at": datetime.utcnow().isoformat()}
        
        if type_update.name is not None:
            update_fields.append("rt.name = $name")
            params["name"] = type_update.name
        
        if type_update.description is not None:
            update_fields.append("rt.description = $description")
            params["description"] = type_update.description
        
        if type_update.color is not None:
            update_fields.append("rt.color = $color")
            params["color"] = type_update.color
        
        if type_update.properties_schema is not None:
            update_fields.append("rt.properties_schema = $properties_schema")
            params["properties_schema"] = type_update.properties_schema
        
        if not update_fields:
            return RelationTypeRepository.get_by_id(type_id)
        
        update_fields.append("rt.updated_at = datetime($updated_at)")
        
        query = f"""
        MATCH (rt:RelationType {{id: $type_id}})-[:BELONGS_TO]->(p:Project)
        SET {', '.join(update_fields)}
        RETURN rt, p.id as project_id
        """
        
        with db.get_session() as session:
            result = session.run(query, **params)
            record = result.single()
            if record:
                return RelationTypeRepository._node_to_type(record["rt"], record["project_id"])
            return None
    
    @staticmethod
    def delete(type_id: str) -> bool:
        """Supprime un type de relation"""
        query = """
        MATCH (rt:RelationType {id: $type_id})
        DETACH DELETE rt
        RETURN count(rt) as deleted
        """
        
        with db.get_session() as session:
            result = session.run(query, type_id=type_id)
            record = result.single()
            return record["deleted"] > 0 if record else False
    
    @staticmethod
    def _node_to_type(node, project_id: str) -> RelationType:
        """Convertit un noeud Neo4j en objet RelationType"""
        return RelationType(
            id=node["id"],
            project_id=project_id,
            name=node["name"],
            description=node.get("description"),
            color=node.get("color", "#6B7280"),
            properties_schema=node.get("properties_schema", {}),
            created_at=node["created_at"],
            updated_at=node.get("updated_at")
        )


class RelationRepository:
    """Repository pour les relations entre individus"""
    
    @staticmethod
    def create(relation: RelationCreate) -> Relation:
        """Crée une nouvelle relation"""
        relation_id = f"relation-{uuid.uuid4().hex[:12]}"
        now = datetime.utcnow()
        
        query = """
        MATCH (from:Individu {id: $from_id})-[:BELONGS_TO]->(p:Project {id: $project_id})
        MATCH (to:Individu {id: $to_id})-[:BELONGS_TO]->(p)
        MATCH (rt:RelationType {id: $type_id})-[:BELONGS_TO]->(p)
        CREATE (from)-[r:RELATED_TO {
            id: $id,
            type_id: $type_id,
            properties: $properties,
            created_at: datetime($created_at),
            updated_at: datetime($updated_at)
        }]->(to)
        RETURN r, $from_id as from_id, $to_id as to_id, $type_id as type_id, $project_id as project_id
        """
        
        with db.get_session() as session:
            result = session.run(
                query,
                id=relation_id,
                from_id=relation.from_individu_id,
                to_id=relation.to_individu_id,
                type_id=relation.type_id,
                project_id=relation.project_id,
                properties=relation.properties or {},
                created_at=now.isoformat(),
                updated_at=now.isoformat()
            )
            record = result.single()
            if record:
                return RelationRepository._rel_to_relation(
                    record["r"],
                    record["type_id"],
                    record["from_id"],
                    record["to_id"],
                    record["project_id"]
                )
            raise Exception("Erreur lors de la création de la relation")
    
    @staticmethod
    def get_by_id(relation_id: str) -> Optional[Relation]:
        """Récupère une relation par son ID"""
        query = """
        MATCH (from:Individu)-[r:RELATED_TO {id: $relation_id}]->(to:Individu)
        MATCH (from)-[:BELONGS_TO]->(p:Project)
        RETURN r, from.id as from_id, to.id as to_id, r.type_id as type_id, p.id as project_id
        """
        
        with db.get_session() as session:
            result = session.run(query, relation_id=relation_id)
            record = result.single()
            if record:
                return RelationRepository._rel_to_relation(
                    record["r"],
                    record["type_id"],
                    record["from_id"],
                    record["to_id"],
                    record["project_id"]
                )
            return None
    
    @staticmethod
    def get_by_project(project_id: str) -> List[Relation]:
        """Récupère toutes les relations d'un projet"""
        query = """
        MATCH (from:Individu)-[r:RELATED_TO]->(to:Individu)
        MATCH (from)-[:BELONGS_TO]->(p:Project {id: $project_id})
        RETURN r, from.id as from_id, to.id as to_id, r.type_id as type_id, p.id as project_id
        """
        
        with db.get_session() as session:
            result = session.run(query, project_id=project_id)
            return [
                RelationRepository._rel_to_relation(
                    record["r"],
                    record["type_id"],
                    record["from_id"],
                    record["to_id"],
                    record["project_id"]
                )
                for record in result
            ]
    
    @staticmethod
    def get_by_individu(individu_id: str) -> List[Relation]:
        """Récupère toutes les relations d'un individu"""
        query = """
        MATCH (i:Individu {id: $individu_id})-[:BELONGS_TO]->(p:Project)
        MATCH (from:Individu)-[r:RELATED_TO]-(i)
        RETURN r, from.id as from_id, 
               CASE WHEN from.id = $individu_id THEN endNode(r).id ELSE i.id END as to_id,
               r.type_id as type_id, p.id as project_id
        """
        
        with db.get_session() as session:
            result = session.run(query, individu_id=individu_id)
            return [
                RelationRepository._rel_to_relation(
                    record["r"],
                    record["type_id"],
                    record["from_id"],
                    record["to_id"],
                    record["project_id"]
                )
                for record in result
            ]
    
    @staticmethod
    def update(relation_id: str, relation_update: RelationUpdate) -> Optional[Relation]:
        """Met à jour une relation"""
        if relation_update.properties is None:
            return RelationRepository.get_by_id(relation_id)
        
        query = """
        MATCH (from:Individu)-[r:RELATED_TO {id: $relation_id}]->(to:Individu)
        MATCH (from)-[:BELONGS_TO]->(p:Project)
        SET r.properties = $properties, r.updated_at = datetime($updated_at)
        RETURN r, from.id as from_id, to.id as to_id, r.type_id as type_id, p.id as project_id
        """
        
        with db.get_session() as session:
            result = session.run(
                query,
                relation_id=relation_id,
                properties=relation_update.properties,
                updated_at=datetime.utcnow().isoformat()
            )
            record = result.single()
            if record:
                return RelationRepository._rel_to_relation(
                    record["r"],
                    record["type_id"],
                    record["from_id"],
                    record["to_id"],
                    record["project_id"]
                )
            return None
    
    @staticmethod
    def delete(relation_id: str) -> bool:
        """Supprime une relation"""
        query = """
        MATCH ()-[r:RELATED_TO {id: $relation_id}]-()
        DELETE r
        RETURN count(r) as deleted
        """
        
        with db.get_session() as session:
            result = session.run(query, relation_id=relation_id)
            record = result.single()
            return record["deleted"] > 0 if record else False
    
    @staticmethod
    def _rel_to_relation(rel, type_id: str, from_id: str, to_id: str, project_id: str) -> Relation:
        """Convertit une relation Neo4j en objet Relation"""
        return Relation(
            id=rel["id"],
            type_id=type_id,
            from_individu_id=from_id,
            to_individu_id=to_id,
            project_id=project_id,
            properties=rel.get("properties", {}),
            created_at=rel["created_at"],
            updated_at=rel.get("updated_at")
        )
