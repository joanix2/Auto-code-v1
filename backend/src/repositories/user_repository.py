"""
Repository pour la gestion des Users dans Neo4j
"""
from typing import List, Optional
from datetime import datetime
import uuid
from src.database import db
from src.models.user import User, UserCreate, UserUpdate
from src.utils.auth import get_password_hash, verify_password


class UserRepository:
    """Gestion des opérations CRUD pour les Users"""
    
    @staticmethod
    def create(user_data: UserCreate) -> User:
        """Crée un nouveau utilisateur dans Neo4j"""
        with db.get_session() as session:
            query = """
            CREATE (u:User {
                id: $id,
                username: $username,
                email: $email,
                full_name: $full_name,
                password: $password,
                is_active: $is_active,
                created_at: datetime($created_at),
                updated_at: datetime($created_at)
            })
            RETURN u
            """
            
            user_id = f"user-{uuid.uuid4()}"
            created_at = datetime.now().isoformat()
            
            # Utiliser 'name' comme alias pour 'full_name' si fourni
            full_name = user_data.full_name or user_data.name if hasattr(user_data, 'name') else None
            
            result = session.run(
                query,
                id=user_id,
                username=user_data.username,
                email=user_data.email,
                full_name=full_name,
                password=get_password_hash(user_data.password),
                is_active=True,
                created_at=created_at
            )
            
            record = result.single()
            return UserRepository._node_to_user(record["u"])
    
    @staticmethod
    def get_by_id(user_id: str) -> Optional[User]:
        """Récupère un utilisateur par son ID"""
        with db.get_session() as session:
            query = "MATCH (u:User {id: $id}) RETURN u"
            result = session.run(query, id=user_id)
            record = result.single()
            
            if record:
                return UserRepository._node_to_user(record["u"])
            return None
    
    @staticmethod
    def get_by_username(username: str) -> Optional[User]:
        """Récupère un utilisateur par son username"""
        with db.get_session() as session:
            query = "MATCH (u:User {username: $username}) RETURN u"
            result = session.run(query, username=username)
            record = result.single()
            
            if record:
                return UserRepository._node_to_user(record["u"])
            return None
    
    @staticmethod
    def get_all(skip: int = 0, limit: int = 100) -> List[User]:
        """Récupère tous les utilisateurs avec pagination"""
        with db.get_session() as session:
            query = """
            MATCH (u:User)
            RETURN u
            ORDER BY u.created_at DESC
            SKIP $skip
            LIMIT $limit
            """
            result = session.run(query, skip=skip, limit=limit)
            return [UserRepository._node_to_user(record["u"]) for record in result]
    
    @staticmethod
    def update(user_id: str, user_data: UserUpdate) -> Optional[User]:
        """Met à jour un utilisateur"""
        with db.get_session() as session:
            updates = []
            params = {"id": user_id, "updated_at": datetime.now().isoformat()}
            
            if user_data.username is not None:
                updates.append("u.username = $username")
                params["username"] = user_data.username
            
            if user_data.email is not None:
                updates.append("u.email = $email")
                params["email"] = user_data.email
            
            if user_data.full_name is not None:
                updates.append("u.full_name = $full_name")
                params["full_name"] = user_data.full_name
            
            if user_data.password is not None:
                updates.append("u.password = $password")
                params["password"] = get_password_hash(user_data.password)
            
            if not updates:
                return UserRepository.get_by_id(user_id)
            
            updates.append("u.updated_at = datetime($updated_at)")
            set_clause = ", ".join(updates)
            
            query = f"""
            MATCH (u:User {{id: $id}})
            SET {set_clause}
            RETURN u
            """
            
            result = session.run(query, **params)
            record = result.single()
            
            if record:
                return UserRepository._node_to_user(record["u"])
            return None
    
    @staticmethod
    def delete(user_id: str) -> bool:
        """Supprime un utilisateur"""
        with db.get_session() as session:
            query = """
            MATCH (u:User {id: $id})
            DELETE u
            RETURN count(u) as deleted_count
            """
            result = session.run(query, id=user_id)
            record = result.single()
            return record["deleted_count"] > 0
    
    @staticmethod
    def authenticate(username: str, password: str) -> Optional[User]:
        """Authentifie un utilisateur avec username et password"""
        with db.get_session() as session:
            query = "MATCH (u:User {username: $username}) RETURN u"
            result = session.run(query, username=username)
            record = result.single()
            
            if not record:
                return None
            
            user_node = record["u"]
            stored_password = user_node.get("password")
            
            if not stored_password or not verify_password(password, stored_password):
                return None
            
            return UserRepository._node_to_user(user_node)
    
    @staticmethod
    def _node_to_user(node) -> User:
        """Convertit un nœud Neo4j en objet User"""
        from neo4j.time import DateTime as Neo4jDateTime
        
        # Convertir les dates Neo4j en datetime Python
        created_at = node["created_at"]
        if isinstance(created_at, Neo4jDateTime):
            created_at = created_at.to_native()
        
        updated_at = node.get("updated_at")
        if updated_at and isinstance(updated_at, Neo4jDateTime):
            updated_at = updated_at.to_native()
        
        return User(
            id=node["id"],
            username=node["username"],
            email=node.get("email"),
            full_name=node.get("full_name"),
            password=node["password"],
            is_active=node.get("is_active", True),
            created_at=created_at,
            updated_at=updated_at
        )
