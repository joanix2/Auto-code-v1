"""
Repository pour la gestion des Classes dans Neo4j
"""
from typing import List, Optional
from datetime import datetime
import uuid

from src.models.classe import Classe, ClasseCreate, ClasseUpdate
from src.database import db


class ClasseRepository:
    """Repository pour les opérations CRUD sur les Classes"""
    
    @staticmethod
    def create(classe: ClasseCreate) -> Classe:
        """Crée une nouvelle classe"""
        classe_id = f"classe-{uuid.uuid4().hex[:12]}"
        now = datetime.utcnow()
        
        query = """
        MATCH (p:Project {id: $project_id})
        CREATE (c:Classe {
            id: $id,
            name: $name,
            description: $description,
            color: $color,
            icon: $icon,
            properties_schema: $properties_schema,
            created_at: datetime($created_at),
            updated_at: datetime($updated_at)
        })
        CREATE (c)-[:BELONGS_TO]->(p)
        RETURN c
        """
        
        with db.get_session() as session:
            result = session.run(
                query,
                id=classe_id,
                project_id=classe.project_id,
                name=classe.name,
                description=classe.description,
                color=classe.color or "#3B82F6",
                icon=classe.icon,
                properties_schema=classe.properties_schema or {},
                created_at=now.isoformat(),
                updated_at=now.isoformat()
            )
            record = result.single()
            if record:
                return ClasseRepository._node_to_classe(record["c"], classe.project_id)
            raise Exception("Erreur lors de la création de la classe")
    
    @staticmethod
    def get_by_id(classe_id: str) -> Optional[Classe]:
        """Récupère une classe par son ID"""
        query = """
        MATCH (c:Classe {id: $classe_id})-[:BELONGS_TO]->(p:Project)
        RETURN c, p.id as project_id
        """
        
        with db.get_session() as session:
            result = session.run(query, classe_id=classe_id)
            record = result.single()
            if record:
                return ClasseRepository._node_to_classe(record["c"], record["project_id"])
            return None
    
    @staticmethod
    def get_by_project(project_id: str) -> List[Classe]:
        """Récupère toutes les classes d'un projet"""
        query = """
        MATCH (c:Classe)-[:BELONGS_TO]->(p:Project {id: $project_id})
        RETURN c, p.id as project_id
        ORDER BY c.name
        """
        
        with db.get_session() as session:
            result = session.run(query, project_id=project_id)
            return [ClasseRepository._node_to_classe(record["c"], record["project_id"]) for record in result]
    
    @staticmethod
    def update(classe_id: str, classe_update: ClasseUpdate) -> Optional[Classe]:
        """Met à jour une classe"""
        update_fields = []
        params = {"classe_id": classe_id, "updated_at": datetime.utcnow().isoformat()}
        
        if classe_update.name is not None:
            update_fields.append("c.name = $name")
            params["name"] = classe_update.name
        
        if classe_update.description is not None:
            update_fields.append("c.description = $description")
            params["description"] = classe_update.description
        
        if classe_update.color is not None:
            update_fields.append("c.color = $color")
            params["color"] = classe_update.color
        
        if classe_update.icon is not None:
            update_fields.append("c.icon = $icon")
            params["icon"] = classe_update.icon
        
        if classe_update.properties_schema is not None:
            update_fields.append("c.properties_schema = $properties_schema")
            params["properties_schema"] = classe_update.properties_schema
        
        if not update_fields:
            return ClasseRepository.get_by_id(classe_id)
        
        update_fields.append("c.updated_at = datetime($updated_at)")
        
        query = f"""
        MATCH (c:Classe {{id: $classe_id}})-[:BELONGS_TO]->(p:Project)
        SET {', '.join(update_fields)}
        RETURN c, p.id as project_id
        """
        
        with db.get_session() as session:
            result = session.run(query, **params)
            record = result.single()
            if record:
                return ClasseRepository._node_to_classe(record["c"], record["project_id"])
            return None
    
    @staticmethod
    def delete(classe_id: str) -> bool:
        """Supprime une classe et tous ses individus"""
        query = """
        MATCH (c:Classe {id: $classe_id})
        OPTIONAL MATCH (c)<-[:INSTANCE_OF]-(i:Individu)
        OPTIONAL MATCH (i)-[r:RELATED_TO]-()
        DETACH DELETE c, i, r
        RETURN count(c) as deleted
        """
        
        with db.get_session() as session:
            result = session.run(query, classe_id=classe_id)
            record = result.single()
            return record["deleted"] > 0 if record else False
    
    @staticmethod
    def _node_to_classe(node, project_id: str) -> Classe:
        """Convertit un noeud Neo4j en objet Classe"""
        return Classe(
            id=node["id"],
            project_id=project_id,
            name=node["name"],
            description=node.get("description"),
            color=node.get("color", "#3B82F6"),
            icon=node.get("icon"),
            properties_schema=node.get("properties_schema", {}),
            created_at=node["created_at"],
            updated_at=node.get("updated_at")
        )
