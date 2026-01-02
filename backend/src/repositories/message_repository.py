"""
Message Repository
Database operations for Message model
"""

from typing import List, Optional
from datetime import datetime
import uuid

from ..database import db
from ..models.message import Message


class MessageRepository:
    """Repository for Message operations"""
    
    @staticmethod
    def create(message: Message) -> Message:
        """
        Create a new message in the database
        
        Args:
            message: Message object to create
            
        Returns:
            Created message with ID
        """
        if not message.id:
            message.id = str(uuid.uuid4())
        
        query = """
        CREATE (m:Message {
            id: $id,
            ticket_id: $ticket_id,
            role: $role,
            content: $content,
            timestamp: datetime($timestamp),
            metadata: $metadata,
            model: $model,
            tokens_used: $tokens_used,
            step: $step
        })
        RETURN m
        """
        
        params = {
            "id": message.id,
            "ticket_id": message.ticket_id,
            "role": message.role,
            "content": message.content,
            "timestamp": message.timestamp.isoformat(),
            "metadata": message.metadata,
            "model": message.model,
            "tokens_used": message.tokens_used,
            "step": message.step
        }
        
        db.execute_query(query, params)
        
        # Create relationship to ticket
        relation_query = """
        MATCH (t:Ticket {id: $ticket_id})
        MATCH (m:Message {id: $message_id})
        CREATE (t)-[:HAS_MESSAGE]->(m)
        """
        
        db.execute_query(relation_query, {
            "ticket_id": message.ticket_id,
            "message_id": message.id
        })
        
        return message
    
    @staticmethod
    def get_by_id(message_id: str) -> Optional[Message]:
        """
        Get a message by ID
        
        Args:
            message_id: Message ID
            
        Returns:
            Message if found, None otherwise
        """
        query = """
        MATCH (m:Message {id: $message_id})
        RETURN m
        """
        
        result = db.execute_query(query, {"message_id": message_id})
        
        if not result:
            return None
        
        record = result[0]
        message_data = record["m"]
        
        return Message(
            id=message_data["id"],
            ticket_id=message_data["ticket_id"],
            role=message_data["role"],
            content=message_data["content"],
            timestamp=message_data["timestamp"].to_native(),
            metadata=message_data.get("metadata"),
            model=message_data.get("model"),
            tokens_used=message_data.get("tokens_used"),
            step=message_data.get("step")
        )
    
    @staticmethod
    def get_by_ticket_id(ticket_id: str, limit: Optional[int] = None) -> List[Message]:
        """
        Get all messages for a ticket, ordered by timestamp
        
        Args:
            ticket_id: Ticket ID
            limit: Optional limit on number of messages to return
            
        Returns:
            List of messages for the ticket
        """
        query = """
        MATCH (t:Ticket {id: $ticket_id})-[:HAS_MESSAGE]->(m:Message)
        RETURN m
        ORDER BY m.timestamp ASC
        """
        
        if limit:
            query += f" LIMIT {limit}"
        
        result = db.execute_query(query, {"ticket_id": ticket_id})
        
        messages = []
        for record in result:
            message_data = record["m"]
            messages.append(Message(
                id=message_data["id"],
                ticket_id=message_data["ticket_id"],
                role=message_data["role"],
                content=message_data["content"],
                timestamp=message_data["timestamp"].to_native(),
                metadata=message_data.get("metadata"),
                model=message_data.get("model"),
                tokens_used=message_data.get("tokens_used"),
                step=message_data.get("step")
            ))
        
        return messages
    
    @staticmethod
    def get_latest_by_ticket_id(ticket_id: str) -> Optional[Message]:
        """
        Get the most recent message for a ticket
        
        Args:
            ticket_id: Ticket ID
            
        Returns:
            Latest message if exists, None otherwise
        """
        query = """
        MATCH (t:Ticket {id: $ticket_id})-[:HAS_MESSAGE]->(m:Message)
        RETURN m
        ORDER BY m.timestamp DESC
        LIMIT 1
        """
        
        result = db.execute_query(query, {"ticket_id": ticket_id})
        
        if not result:
            return None
        
        message_data = result[0]["m"]
        return Message(
            id=message_data["id"],
            ticket_id=message_data["ticket_id"],
            role=message_data["role"],
            content=message_data["content"],
            timestamp=message_data["timestamp"].to_native(),
            metadata=message_data.get("metadata"),
            model=message_data.get("model"),
            tokens_used=message_data.get("tokens_used"),
            step=message_data.get("step")
        )
    
    @staticmethod
    def get_by_step(ticket_id: str, step: str) -> List[Message]:
        """
        Get messages for a specific workflow step
        
        Args:
            ticket_id: Ticket ID
            step: Workflow step (e.g., "analysis", "code_generation")
            
        Returns:
            List of messages for that step
        """
        query = """
        MATCH (t:Ticket {id: $ticket_id})-[:HAS_MESSAGE]->(m:Message {step: $step})
        RETURN m
        ORDER BY m.timestamp ASC
        """
        
        result = db.execute_query(query, {
            "ticket_id": ticket_id,
            "step": step
        })
        
        messages = []
        for record in result:
            message_data = record["m"]
            messages.append(Message(
                id=message_data["id"],
                ticket_id=message_data["ticket_id"],
                role=message_data["role"],
                content=message_data["content"],
                timestamp=message_data["timestamp"].to_native(),
                metadata=message_data.get("metadata"),
                model=message_data.get("model"),
                tokens_used=message_data.get("tokens_used"),
                step=message_data.get("step")
            ))
        
        return messages
    
    @staticmethod
    def update(message_id: str, content: Optional[str] = None, 
               metadata: Optional[dict] = None, tokens_used: Optional[int] = None) -> Optional[Message]:
        """
        Update a message
        
        Args:
            message_id: Message ID
            content: New content
            metadata: Updated metadata
            tokens_used: Updated token count
            
        Returns:
            Updated message if found, None otherwise
        """
        updates = []
        params = {"message_id": message_id}
        
        if content is not None:
            updates.append("m.content = $content")
            params["content"] = content
        
        if metadata is not None:
            updates.append("m.metadata = $metadata")
            params["metadata"] = metadata
        
        if tokens_used is not None:
            updates.append("m.tokens_used = $tokens_used")
            params["tokens_used"] = tokens_used
        
        if not updates:
            return MessageRepository.get_by_id(message_id)
        
        query = f"""
        MATCH (m:Message {{id: $message_id}})
        SET {', '.join(updates)}
        RETURN m
        """
        
        result = db.execute_query(query, params)
        
        if not result:
            return None
        
        message_data = result[0]["m"]
        return Message(
            id=message_data["id"],
            ticket_id=message_data["ticket_id"],
            role=message_data["role"],
            content=message_data["content"],
            timestamp=message_data["timestamp"].to_native(),
            metadata=message_data.get("metadata"),
            model=message_data.get("model"),
            tokens_used=message_data.get("tokens_used"),
            step=message_data.get("step")
        )
    
    @staticmethod
    def delete(message_id: str) -> bool:
        """
        Delete a message
        
        Args:
            message_id: Message ID
            
        Returns:
            True if deleted, False if not found
        """
        query = """
        MATCH (m:Message {id: $message_id})
        DETACH DELETE m
        RETURN count(m) as deleted_count
        """
        
        result = db.execute_query(query, {"message_id": message_id})
        return result[0]["deleted_count"] > 0 if result else False
    
    @staticmethod
    def delete_by_ticket_id(ticket_id: str) -> int:
        """
        Delete all messages for a ticket
        
        Args:
            ticket_id: Ticket ID
            
        Returns:
            Number of messages deleted
        """
        query = """
        MATCH (t:Ticket {id: $ticket_id})-[:HAS_MESSAGE]->(m:Message)
        DETACH DELETE m
        RETURN count(m) as deleted_count
        """
        
        result = db.execute_query(query, {"ticket_id": ticket_id})
        return result[0]["deleted_count"] if result else 0
    
    @staticmethod
    def get_conversation_summary(ticket_id: str) -> dict:
        """
        Get summary statistics for a ticket's conversation
        
        Args:
            ticket_id: Ticket ID
            
        Returns:
            Dictionary with conversation statistics
        """
        query = """
        MATCH (t:Ticket {id: $ticket_id})-[:HAS_MESSAGE]->(m:Message)
        RETURN 
            count(m) as total_messages,
            sum(m.tokens_used) as total_tokens,
            collect(DISTINCT m.role) as roles,
            collect(DISTINCT m.step) as steps,
            min(m.timestamp) as first_message,
            max(m.timestamp) as last_message
        """
        
        result = db.execute_query(query, {"ticket_id": ticket_id})
        
        if not result:
            return {
                "total_messages": 0,
                "total_tokens": 0,
                "roles": [],
                "steps": [],
                "first_message": None,
                "last_message": None
            }
        
        record = result[0]
        return {
            "total_messages": record["total_messages"],
            "total_tokens": record["total_tokens"] or 0,
            "roles": record["roles"],
            "steps": [s for s in record["steps"] if s is not None],
            "first_message": record["first_message"].to_native() if record["first_message"] else None,
            "last_message": record["last_message"].to_native() if record["last_message"] else None
        }
