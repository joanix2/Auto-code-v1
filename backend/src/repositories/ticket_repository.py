"""Ticket repository - handles ticket data access"""
from typing import List, Optional
from src.database import Neo4jConnection
from src.models.ticket import Ticket, TicketCreate, TicketUpdate, TicketStatus
from datetime import datetime
import uuid


class TicketRepository:
    """Repository for managing ticket data"""
    
    def __init__(self, db: Neo4jConnection):
        self.db = db
    
    async def create_ticket(self, ticket_data: TicketCreate, created_by: str) -> Optional[Ticket]:
        """Create a new ticket"""
        ticket_id = str(uuid.uuid4())
        query = """
        MATCH (u:User {username: $created_by})
        MATCH (r:Repository {full_name: $repository})
        CREATE (t:Ticket {
            id: $id,
            title: $title,
            description: $description,
            repository: $repository,
            priority: $priority,
            type: $type,
            status: 'pending',
            created_at: datetime()
        })
        CREATE (u)-[:CREATED]->(t)
        CREATE (t)-[:FOR_REPO]->(r)
        RETURN t
        """
        
        params = {
            "id": ticket_id,
            "created_by": created_by,
            **ticket_data.model_dump()
        }
        
        result = self.db.execute_query(query, params)
        if result:
            return Ticket(
                id=ticket_id,
                created_by=created_by,
                status=TicketStatus.pending,
                **ticket_data.model_dump()
            )
        return None
    
    async def get_tickets_by_repository(self, repository: str) -> List[Ticket]:
        """Get all tickets for a repository"""
        query = """
        MATCH (t:Ticket {repository: $repository})<-[:CREATED]-(u:User)
        RETURN t, u.username as created_by
        ORDER BY t.created_at DESC
        """
        
        result = self.db.execute_query(query, {"repository": repository})
        tickets = []
        
        for record in result:
            ticket_node = record["t"]
            tickets.append(Ticket(
                id=ticket_node["id"],
                title=ticket_node["title"],
                description=ticket_node["description"],
                repository=ticket_node["repository"],
                priority=ticket_node["priority"],
                type=ticket_node["type"],
                status=TicketStatus(ticket_node["status"]),
                created_by=record["created_by"],
                created_at=ticket_node.get("created_at", datetime.utcnow())
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
