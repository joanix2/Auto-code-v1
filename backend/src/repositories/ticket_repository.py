"""Ticket repository - handles ticket data access"""
from typing import List, Optional
from src.database import Neo4jConnection
from src.models.ticket import Ticket, TicketCreate, TicketUpdate, TicketStatus
from datetime import datetime
import uuid


def neo4j_datetime_to_python(neo4j_dt) -> datetime:
    """Convert Neo4j DateTime to Python datetime"""
    if neo4j_dt is None:
        return datetime.utcnow()
    if isinstance(neo4j_dt, datetime):
        return neo4j_dt
    # Neo4j DateTime has to_native() method
    if hasattr(neo4j_dt, 'to_native'):
        return neo4j_dt.to_native()
    return datetime.utcnow()


class TicketRepository:
    """Repository for managing ticket data"""
    
    def __init__(self, db: Neo4jConnection):
        self.db = db
    
    async def create_ticket(self, ticket_data: TicketCreate, created_by: str) -> Optional[Ticket]:
        """Create a new ticket"""
        ticket_id = str(uuid.uuid4())
        query = """
        MATCH (u:User {username: $created_by})
        MATCH (r:Repository {id: $repository_id})
        CREATE (t:Ticket {
            id: $id,
            title: $title,
            description: $description,
            repository_id: $repository_id,
            priority: $priority,
            ticket_type: $ticket_type,
            status: 'open',
            created_at: datetime()
        })
        CREATE (u)-[:CREATED]->(t)
        CREATE (t)-[:FOR_REPO]->(r)
        RETURN t, r.name as repository_name
        """
        
        params = {
            "id": ticket_id,
            "created_by": created_by,
            "title": ticket_data.title,
            "description": ticket_data.description or "",
            "repository_id": ticket_data.repository_id,
            "priority": ticket_data.priority.value,
            "ticket_type": ticket_data.ticket_type.value
        }
        
        result = self.db.execute_query(query, params)
        if result:
            record = result[0]
            return Ticket(
                id=ticket_id,
                title=ticket_data.title,
                description=ticket_data.description,
                repository_id=ticket_data.repository_id,
                repository_name=record.get("repository_name"),
                priority=ticket_data.priority,
                ticket_type=ticket_data.ticket_type,
                created_by=created_by,
                status=TicketStatus.open
            )
        return None
    
    async def get_tickets_by_repository(self, repository_id: str) -> List[Ticket]:
        """Get all tickets for a repository"""
        query = """
        MATCH (t:Ticket {repository_id: $repository_id})<-[:CREATED]-(u:User)
        MATCH (t)-[:FOR_REPO]->(r:Repository)
        RETURN t, u.username as created_by, r.name as repository_name
        ORDER BY t.created_at DESC
        """
        
        result = self.db.execute_query(query, {"repository_id": repository_id})
        tickets = []
        
        for record in result:
            ticket_node = record["t"]
            tickets.append(Ticket(
                id=ticket_node["id"],
                title=ticket_node["title"],
                description=ticket_node["description"],
                repository_id=ticket_node["repository_id"],
                repository_name=record.get("repository_name"),
                priority=ticket_node["priority"],
                ticket_type=ticket_node["ticket_type"],
                status=TicketStatus(ticket_node["status"]),
                created_by=record["created_by"],
                created_at=neo4j_datetime_to_python(ticket_node.get("created_at"))
            ))
        
        return tickets
    
    async def update_ticket_status(self, ticket_id: str, status: str) -> bool:
        """Update ticket status"""
        query = """
        MATCH (t:Ticket {id: $ticket_id})
        SET t.status = $status, t.updated_at = datetime()
        RETURN t
        """
        
        result = self.db.execute_query(query, {"ticket_id": ticket_id, "status": status})
        return bool(result)
    
    async def get_ticket_by_id(self, ticket_id: str) -> Optional[Ticket]:
        """Get a ticket by ID"""
        query = """
        MATCH (t:Ticket {id: $ticket_id})<-[:CREATED]-(u:User)
        MATCH (t)-[:FOR_REPO]->(r:Repository)
        RETURN t, u.username as created_by, r.name as repository_name, r.id as repository_id
        """
        
        result = self.db.execute_query(query, {"ticket_id": ticket_id})
        if not result:
            return None
        
        record = result[0]
        ticket_node = record["t"]
        
        return Ticket(
            id=ticket_node["id"],
            title=ticket_node["title"],
            description=ticket_node.get("description"),
            repository_id=record["repository_id"],
            repository_name=record.get("repository_name"),
            priority=ticket_node["priority"],
            ticket_type=ticket_node["ticket_type"],
            status=TicketStatus(ticket_node["status"]),
            created_by=record["created_by"],
            created_at=neo4j_datetime_to_python(ticket_node.get("created_at")),
            updated_at=neo4j_datetime_to_python(ticket_node.get("updated_at")) if ticket_node.get("updated_at") else None
        )
    
    async def update_ticket(self, ticket_id: str, ticket_data: TicketUpdate) -> Optional[Ticket]:
        """Update a ticket"""
        # Build dynamic update query
        updates = []
        params = {"ticket_id": ticket_id}
        
        if ticket_data.title is not None:
            updates.append("t.title = $title")
            params["title"] = ticket_data.title
        
        if ticket_data.description is not None:
            updates.append("t.description = $description")
            params["description"] = ticket_data.description
        
        if ticket_data.status is not None:
            updates.append("t.status = $status")
            params["status"] = ticket_data.status.value
        
        if ticket_data.priority is not None:
            updates.append("t.priority = $priority")
            params["priority"] = ticket_data.priority.value
        
        if not updates:
            # No updates, just return the existing ticket
            return await self.get_ticket_by_id(ticket_id)
        
        updates.append("t.updated_at = datetime()")
        update_clause = ", ".join(updates)
        
        query = f"""
        MATCH (t:Ticket {{id: $ticket_id}})<-[:CREATED]-(u:User)
        MATCH (t)-[:FOR_REPO]->(r:Repository)
        SET {update_clause}
        RETURN t, u.username as created_by, r.name as repository_name, r.id as repository_id
        """
        
        result = self.db.execute_query(query, params)
        if not result:
            return None
        
        record = result[0]
        ticket_node = record["t"]
        
        return Ticket(
            id=ticket_node["id"],
            title=ticket_node["title"],
            description=ticket_node.get("description"),
            repository_id=record["repository_id"],
            repository_name=record.get("repository_name"),
            priority=ticket_node["priority"],
            ticket_type=ticket_node["ticket_type"],
            status=TicketStatus(ticket_node["status"]),
            created_by=record["created_by"],
            created_at=neo4j_datetime_to_python(ticket_node.get("created_at")),
            updated_at=neo4j_datetime_to_python(ticket_node.get("updated_at")) if ticket_node.get("updated_at") else None
        )
    
    async def delete_ticket(self, ticket_id: str) -> bool:
        """Delete a ticket"""
        query = """
        MATCH (t:Ticket {id: $ticket_id})
        DETACH DELETE t
        RETURN count(t) as deleted
        """
        
        result = self.db.execute_query(query, {"ticket_id": ticket_id})
        return bool(result and result[0]["deleted"] > 0)

