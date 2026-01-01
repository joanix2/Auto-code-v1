"""Repository repository - handles repository data access"""
from typing import List, Optional
from src.database import Neo4jConnection
from src.models.repository import Repository, RepositoryCreate
from datetime import datetime
import uuid


class RepositoryRepository:
    """Repository for managing repository data"""
    
    def __init__(self, db: Neo4jConnection):
        self.db = db
    
    async def create_repository(self, repo_data: RepositoryCreate, owner_username: str) -> Optional[Repository]:
        """Create a new repository"""
        repo_id = str(uuid.uuid4())
        query = """
        MATCH (u:User {username: $owner_username})
        CREATE (r:Repository {
            id: $id,
            name: $name,
            full_name: $full_name,
            description: $description,
            github_id: $github_id,
            url: $url,
            private: $private,
            created_at: datetime()
        })
        CREATE (u)-[:OWNS]->(r)
        RETURN r
        """
        
        params = {
            "id": repo_id,
            "owner_username": owner_username,
            **repo_data.model_dump()
        }
        
        result = self.db.execute_query(query, params)
        if result:
            return Repository(
                id=repo_id,
                owner_username=owner_username,
                **repo_data.model_dump()
            )
        return None
    
    async def get_repositories_by_owner(self, owner_username: str) -> List[Repository]:
        """Get all repositories for a user"""
        query = """
        MATCH (u:User {username: $owner_username})-[:OWNS]->(r:Repository)
        RETURN r
        ORDER BY r.created_at DESC
        """
        
        result = self.db.execute_query(query, {"owner_username": owner_username})
        repositories = []
        
        for record in result:
            repo_node = record["r"]
            repositories.append(Repository(
                id=repo_node["id"],
                name=repo_node["name"],
                full_name=repo_node["full_name"],
                description=repo_node.get("description"),
                github_id=repo_node["github_id"],
                url=repo_node["url"],
                private=repo_node.get("private", False),
                owner_username=owner_username,
                created_at=repo_node.get("created_at", datetime.utcnow())
            ))
        
        return repositories
