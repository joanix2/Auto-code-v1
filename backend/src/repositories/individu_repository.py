"""
Repository pour la gestion des Individus dans Neo4j
"""
from typing import List, Optional
from datetime import datetime
import uuid

from src.models.individu import Individu, IndividuCreate, IndividuUpdate
from src.database import db


class IndividuRepository:
    """Repository pour les opérations CRUD sur les Individus"""
    
    @staticmethod
    def create(individu: IndividuCreate) -> Individu:
        """Crée un nouvel individu"""
        individu_id = f"individu-{uuid.uuid4().hex[:12]}"
        now = datetime.utcnow()
        
        query = """
        MATCH (c:Classe {id: $classe_id})-[:BELONGS_TO]->(p:Project {id: $project_id})
        CREATE (i:Individu {
            id: $id,
            label: $label,
            properties: $properties,
            created_at: datetime($created_at),
            updated_at: datetime($updated_at)
        })
        CREATE (i)-[:INSTANCE_OF]->(c)
        CREATE (i)-[:BELONGS_TO]->(p)
        RETURN i
        """
        
        with db.get_session() as session:
            result = session.run(
                query,
                id=individu_id,
                classe_id=individu.classe_id,
                project_id=individu.project_id,
                label=individu.label,
                properties=individu.properties or {},
                created_at=now.isoformat(),
                updated_at=now.isoformat()
            )
            record = result.single()
            if record:
                return IndividuRepository._node_to_individu(
                    record["i"], 
                    individu.classe_id, 
                    individu.project_id
                )
            raise Exception("Erreur lors de la création de l'individu")
    
    @staticmethod
    def get_by_id(individu_id: str) -> Optional[Individu]:
        """Récupère un individu par son ID"""
        query = """
        MATCH (i:Individu {id: $individu_id})-[:INSTANCE_OF]->(c:Classe)
        MATCH (i)-[:BELONGS_TO]->(p:Project)
        RETURN i, c.id as classe_id, p.id as project_id
        """
        
        with db.get_session() as session:
            result = session.run(query, individu_id=individu_id)
            record = result.single()
            if record:
                return IndividuRepository._node_to_individu(
                    record["i"], 
                    record["classe_id"], 
                    record["project_id"]
                )
            return None
    
    @staticmethod
    def get_by_project(project_id: str) -> List[Individu]:
        """Récupère tous les individus d'un projet"""
        query = """
        MATCH (i:Individu)-[:BELONGS_TO]->(p:Project {id: $project_id})
        MATCH (i)-[:INSTANCE_OF]->(c:Classe)
        RETURN i, c.id as classe_id, p.id as project_id
        ORDER BY i.label
        """
        
        with db.get_session() as session:
            result = session.run(query, project_id=project_id)
            return [
                IndividuRepository._node_to_individu(
                    record["i"], 
                    record["classe_id"], 
                    record["project_id"]
                ) 
                for record in result
            ]
    
    @staticmethod
    def get_by_classe(classe_id: str) -> List[Individu]:
        """Récupère tous les individus d'une classe"""
        query = """
        MATCH (i:Individu)-[:INSTANCE_OF]->(c:Classe {id: $classe_id})
        MATCH (i)-[:BELONGS_TO]->(p:Project)
        RETURN i, c.id as classe_id, p.id as project_id
        ORDER BY i.label
        """
        
        with db.get_session() as session:
            result = session.run(query, classe_id=classe_id)
            return [
                IndividuRepository._node_to_individu(
                    record["i"], 
                    record["classe_id"], 
                    record["project_id"]
                ) 
                for record in result
            ]
    
    @staticmethod
    def update(individu_id: str, individu_update: IndividuUpdate) -> Optional[Individu]:
        """Met à jour un individu"""
        update_fields = []
        params = {"individu_id": individu_id, "updated_at": datetime.utcnow().isoformat()}
        
        if individu_update.label is not None:
            update_fields.append("i.label = $label")
            params["label"] = individu_update.label
        
        if individu_update.properties is not None:
            update_fields.append("i.properties = $properties")
            params["properties"] = individu_update.properties
        
        if not update_fields:
            return IndividuRepository.get_by_id(individu_id)
        
        update_fields.append("i.updated_at = datetime($updated_at)")
        
        query = f"""
        MATCH (i:Individu {{id: $individu_id}})-[:INSTANCE_OF]->(c:Classe)
        MATCH (i)-[:BELONGS_TO]->(p:Project)
        SET {', '.join(update_fields)}
        RETURN i, c.id as classe_id, p.id as project_id
        """
        
        with db.get_session() as session:
            result = session.run(query, **params)
            record = result.single()
            if record:
                return IndividuRepository._node_to_individu(
                    record["i"], 
                    record["classe_id"], 
                    record["project_id"]
                )
            return None
    
    @staticmethod
    def delete(individu_id: str) -> bool:
        """Supprime un individu et toutes ses relations"""
        query = """
        MATCH (i:Individu {id: $individu_id})
        DETACH DELETE i
        RETURN count(i) as deleted
        """
        
        with db.get_session() as session:
            result = session.run(query, individu_id=individu_id)
            record = result.single()
            return record["deleted"] > 0 if record else False
    
    @staticmethod
    def _node_to_individu(node, classe_id: str, project_id: str) -> Individu:
        """Convertit un noeud Neo4j en objet Individu"""
        return Individu(
            id=node["id"],
            classe_id=classe_id,
            project_id=project_id,
            label=node["label"],
            properties=node.get("properties", {}),
            created_at=node["created_at"],
            updated_at=node.get("updated_at")
        )
