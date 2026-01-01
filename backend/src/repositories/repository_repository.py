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
        
        # Auto-generate full_name if not provided
        full_name = repo_data.full_name or f"{owner_username}/{repo_data.name}"
        
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
            github_created_at: $github_created_at,
            github_updated_at: $github_updated_at,
            github_pushed_at: $github_pushed_at,
            created_at: datetime(),
            updated_at: datetime()
        })
        CREATE (u)-[:OWNS]->(r)
        RETURN r
        """
        
        params = {
            "id": repo_id,
            "owner_username": owner_username,
            "name": repo_data.name,
            "full_name": full_name,
            "description": repo_data.description,
            "github_id": repo_data.github_id,
            "url": repo_data.url,
            "private": repo_data.private,
            "github_created_at": repo_data.github_created_at,
            "github_updated_at": repo_data.github_updated_at,
            "github_pushed_at": repo_data.github_pushed_at
        }
        
        result = self.db.execute_query(query, params)
        if result:
            return Repository(
                id=repo_id,
                owner_username=owner_username,
                name=repo_data.name,
                full_name=full_name,
                description=repo_data.description,
                github_id=repo_data.github_id,
                url=repo_data.url,
                private=repo_data.private,
                github_created_at=repo_data.github_created_at,
                github_updated_at=repo_data.github_updated_at,
                github_pushed_at=repo_data.github_pushed_at,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
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
        
        from neo4j.time import DateTime as Neo4jDateTime
        
        for record in result:
            repo_node = record["r"]
            
            # Convertir les dates Neo4j en datetime Python
            created_at = repo_node.get("created_at", datetime.utcnow())
            if isinstance(created_at, Neo4jDateTime):
                created_at = created_at.to_native()
            
            updated_at = repo_node.get("updated_at")
            if updated_at and isinstance(updated_at, Neo4jDateTime):
                updated_at = updated_at.to_native()
            
            github_created_at = repo_node.get("github_created_at")
            if github_created_at and isinstance(github_created_at, Neo4jDateTime):
                github_created_at = github_created_at.to_native()
            
            github_updated_at = repo_node.get("github_updated_at")
            if github_updated_at and isinstance(github_updated_at, Neo4jDateTime):
                github_updated_at = github_updated_at.to_native()
            
            github_pushed_at = repo_node.get("github_pushed_at")
            if github_pushed_at and isinstance(github_pushed_at, Neo4jDateTime):
                github_pushed_at = github_pushed_at.to_native()
            
            repositories.append(Repository(
                id=repo_node["id"],
                name=repo_node["name"],
                full_name=repo_node["full_name"],
                description=repo_node.get("description"),
                github_id=repo_node["github_id"],
                url=repo_node["url"],
                private=repo_node.get("private", False),
                owner_username=owner_username,
                created_at=created_at,
                updated_at=updated_at,
                github_created_at=github_created_at,
                github_updated_at=github_updated_at,
                github_pushed_at=github_pushed_at
            ))
        
        return repositories
    
    async def get_by_github_id(self, github_id: int) -> Optional[Repository]:
        """Get a repository by its GitHub ID"""
        query = """
        MATCH (u:User)-[:OWNS]->(r:Repository {github_id: $github_id})
        RETURN r, u.username as owner_username
        """
        
        result = self.db.execute_query(query, {"github_id": github_id})
        if result and len(result) > 0:
            from neo4j.time import DateTime as Neo4jDateTime
            
            record = result[0]
            repo_node = record["r"]
            
            # Convertir les dates Neo4j en datetime Python
            created_at = repo_node.get("created_at", datetime.utcnow())
            if isinstance(created_at, Neo4jDateTime):
                created_at = created_at.to_native()
            
            updated_at = repo_node.get("updated_at")
            if updated_at and isinstance(updated_at, Neo4jDateTime):
                updated_at = updated_at.to_native()
            
            return Repository(
                id=repo_node["id"],
                name=repo_node["name"],
                full_name=repo_node["full_name"],
                description=repo_node.get("description"),
                github_id=repo_node["github_id"],
                url=repo_node["url"],
                private=repo_node.get("private", False),
                owner_username=record["owner_username"],
                created_at=created_at,
                updated_at=updated_at
            )
        return None
    
    async def update_repository(self, repo_id: str, repo_data: RepositoryCreate) -> Optional[Repository]:
        """Update an existing repository"""
        query = """
        MATCH (u:User)-[:OWNS]->(r:Repository {id: $repo_id})
        SET r.name = $name,
            r.full_name = $full_name,
            r.description = $description,
            r.url = $url,
            r.private = $private,
            r.updated_at = datetime()
        RETURN r, u.username as owner_username
        """
        
        params = {
            "repo_id": repo_id,
            **repo_data.model_dump()
        }
        
        result = self.db.execute_query(query, params)
        if result and len(result) > 0:
            from neo4j.time import DateTime as Neo4jDateTime
            
            record = result[0]
            repo_node = record["r"]
            
            # Convertir les dates Neo4j en datetime Python
            created_at = repo_node.get("created_at", datetime.utcnow())
            if isinstance(created_at, Neo4jDateTime):
                created_at = created_at.to_native()
            
            updated_at = repo_node.get("updated_at")
            if updated_at and isinstance(updated_at, Neo4jDateTime):
                updated_at = updated_at.to_native()
            
            github_created_at = repo_node.get("github_created_at")
            if github_created_at and isinstance(github_created_at, Neo4jDateTime):
                github_created_at = github_created_at.to_native()
            
            github_updated_at = repo_node.get("github_updated_at")
            if github_updated_at and isinstance(github_updated_at, Neo4jDateTime):
                github_updated_at = github_updated_at.to_native()
            
            github_pushed_at = repo_node.get("github_pushed_at")
            if github_pushed_at and isinstance(github_pushed_at, Neo4jDateTime):
                github_pushed_at = github_pushed_at.to_native()
            
            return Repository(
                id=repo_node["id"],
                name=repo_node["name"],
                full_name=repo_node["full_name"],
                description=repo_node.get("description"),
                github_id=repo_node["github_id"],
                url=repo_node["url"],
                private=repo_node.get("private", False),
                owner_username=record["owner_username"],
                created_at=created_at,
                updated_at=updated_at,
                github_created_at=github_created_at,
                github_updated_at=github_updated_at,
                github_pushed_at=github_pushed_at
            )
        return None

    async def delete_repository(self, repo_id: str) -> bool:
        """Delete a repository by ID"""
        query = """
        MATCH (r:Repository {id: $repo_id})
        DETACH DELETE r
        RETURN count(r) as deleted
        """
        
        result = self.db.execute_query(query, {"repo_id": repo_id})
        return result is not None and len(result) > 0 and result[0]["deleted"] > 0
