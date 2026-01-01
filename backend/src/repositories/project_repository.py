"""
Repository pour la gestion des Projects dans Neo4j
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

from src.models.project import Project, ProjectCreate, ProjectUpdate
from src.database import db
from src.services.levenshtein_service import search_by_similarity
from src.services.levenshtein_service import search_by_similarity


class ProjectRepository:
    """Repository pour les opérations CRUD sur les Projects"""
    
    @staticmethod
    def create(project: ProjectCreate) -> Project:
        """Crée un nouveau projet"""
        project_id = f"project-{uuid.uuid4().hex[:12]}"
        now = datetime.utcnow()
        
        query = """
        MATCH (u:User {id: $user_id})
        CREATE (p:Project {
            id: $id,
            name: $name,
            description: $description,
            settings: $settings,
            created_at: datetime($created_at),
            updated_at: datetime($updated_at)
        })
        CREATE (u)-[:OWNS]->(p)
        RETURN p
        """
        
        with db.get_session() as session:
            result = session.run(
                query,
                id=project_id,
                user_id=project.user_id,
                name=project.name,
                description=project.description,
                settings=project.settings or {},
                created_at=now.isoformat(),
                updated_at=now.isoformat()
            )
            record = result.single()
            if record:
                return ProjectRepository._node_to_project(record["p"], project.user_id)
            raise Exception("Erreur lors de la création du projet")
    
    @staticmethod
    def get_by_id(project_id: str) -> Optional[Project]:
        """Récupère un projet par son ID"""
        query = """
        MATCH (u:User)-[:OWNS]->(p:Project {id: $project_id})
        RETURN p, u.id as user_id
        """
        
        with db.get_session() as session:
            result = session.run(query, project_id=project_id)
            record = result.single()
            if record:
                return ProjectRepository._node_to_project(record["p"], record["user_id"])
            return None
    
    @staticmethod
    def get_by_user(user_id: str, skip: int = 0, limit: int = 100) -> List[Project]:
        """Récupère tous les projets d'un utilisateur"""
        query = """
        MATCH (u:User {id: $user_id})-[:OWNS]->(p:Project)
        RETURN p, u.id as user_id
        ORDER BY p.created_at DESC
        SKIP $skip
        LIMIT $limit
        """
        
        with db.get_session() as session:
            result = session.run(query, user_id=user_id, skip=skip, limit=limit)
            return [ProjectRepository._node_to_project(record["p"], record["user_id"]) for record in result]
    
    @staticmethod
    def update(project_id: str, project_update: ProjectUpdate) -> Optional[Project]:
        """Met à jour un projet"""
        update_fields = []
        params = {"project_id": project_id, "updated_at": datetime.utcnow().isoformat()}
        
        if project_update.name is not None:
            update_fields.append("p.name = $name")
            params["name"] = project_update.name
        
        if project_update.description is not None:
            update_fields.append("p.description = $description")
            params["description"] = project_update.description
        
        if project_update.settings is not None:
            update_fields.append("p.settings = $settings")
            params["settings"] = project_update.settings
        
        if not update_fields:
            return ProjectRepository.get_by_id(project_id)
        
        update_fields.append("p.updated_at = datetime($updated_at)")
        
        query = f"""
        MATCH (u:User)-[:OWNS]->(p:Project {{id: $project_id}})
        SET {', '.join(update_fields)}
        RETURN p, u.id as user_id
        """
        
        with db.get_session() as session:
            result = session.run(query, **params)
            record = result.single()
            if record:
                return ProjectRepository._node_to_project(record["p"], record["user_id"])
            return None
    
    @staticmethod
    def delete(project_id: str) -> bool:
        """Supprime un projet et toutes ses dépendances"""
        query = """
        MATCH (p:Project {id: $project_id})
        OPTIONAL MATCH (p)<-[:BELONGS_TO]-(c:Classe)
        OPTIONAL MATCH (p)<-[:BELONGS_TO]-(i:Individu)
        OPTIONAL MATCH (p)<-[:BELONGS_TO]-(rt:RelationType)
        OPTIONAL MATCH (i)-[r:RELATED_TO]-()
        DETACH DELETE p, c, i, rt, r
        RETURN count(p) as deleted
        """
        
        with db.get_session() as session:
            result = session.run(query, project_id=project_id)
            record = result.single()
            return record["deleted"] > 0 if record else False
    
    @staticmethod
    def search_by_name(user_id: str, search_term: str, threshold: float = 0.6) -> List[Project]:
        """
        Recherche des projets par nom avec distance de Levenshtein
        threshold: seuil de similarité minimum (0.0 à 1.0, par défaut 0.6)
        """
        # Récupérer tous les projets de l'utilisateur
        query = """
        MATCH (u:User {id: $user_id})-[:OWNS]->(p:Project)
        RETURN p, u.id as user_id
        """
        
        with db.get_session() as session:
            result = session.run(query, user_id=user_id)
            
            # Convertir en liste de tuples (nom, projet)
            items = []
            for record in result:
                project = ProjectRepository._node_to_project(record["p"], record["user_id"])
                items.append((project.name, project))
            
            # Utiliser le service Levenshtein pour filtrer et trier
            results = search_by_similarity(search_term, items, threshold)
            
            # Retourner uniquement les projets (sans les scores)
            return [project for project, score in results]
    
    @staticmethod
    def _node_to_project(node, user_id: str) -> Project:
        """Convertit un noeud Neo4j en objet Project"""
        return Project(
            id=node["id"],
            user_id=user_id,
            name=node["name"],
            description=node.get("description"),
            settings=node.get("settings", {}),
            created_at=node["created_at"],
            updated_at=node.get("updated_at")
        )
