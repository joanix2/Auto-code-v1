"""
Message Service
Business logic for message operations
Used by both API and CLI
"""

from typing import Optional
from datetime import datetime
import uuid
from ...repositories.message_repository import MessageRepository
from ...models.message import Message
from ...models.ticket import Ticket
from ..utils.template_service import TemplateService


class MessageService:
    """Service for message business logic"""
    
    def __init__(self, message_repo: Optional[MessageRepository] = None):
        """
        Initialize message service
        
        Args:
            message_repo: Optional message repository instance (for testing)
        """
        self.message_repo = message_repo or MessageRepository()
        self.template_service = TemplateService()
    
    def get_message_count(self, ticket_id: str) -> int:
        """
        Get the number of messages for a ticket
        
        Args:
            ticket_id: Ticket ID
            
        Returns:
            Number of messages for the ticket
            
        Examples:
            >>> service = MessageService()
            >>> count = service.get_message_count("ticket-123")
            >>> print(f"Ticket has {count} messages")
        """
        messages = self.message_repo.get_by_ticket_id(ticket_id)
        return len(messages)
    
    def is_over_limit(self, ticket_id: str, limit: int) -> bool:
        """
        Check if the number of messages exceeds a given limit
        
        Args:
            ticket_id: Ticket ID
            limit: Maximum number of messages allowed
            
        Returns:
            True if message count > limit, False otherwise
            
        Examples:
            >>> service = MessageService()
            >>> if service.is_over_limit("ticket-123", 50):
            ...     print("Too many messages!")
        """
        count = self.get_message_count(ticket_id)
        return count > limit
    
    def get_last_message(self, ticket_id: str) -> Optional[Message]:
        """
        Get the last (most recent) message for a ticket
        
        Args:
            ticket_id: Ticket ID
            
        Returns:
            The most recent message, or None if no messages exist
            
        Examples:
            >>> service = MessageService()
            >>> last_msg = service.get_last_message("ticket-123")
            >>> if last_msg:
            ...     print(f"Last message: {last_msg.content}")
        """
        return self.message_repo.get_latest_by_ticket_id(ticket_id)
    
    def get_messages(self, ticket_id: str, limit: Optional[int] = None) -> list[Message]:
        """
        Get all messages for a ticket
        
        Args:
            ticket_id: Ticket ID
            limit: Optional limit on number of messages to return
            
        Returns:
            List of messages ordered by timestamp
            
        Examples:
            >>> service = MessageService()
            >>> messages = service.get_messages("ticket-123", limit=10)
        """
        return self.message_repo.get_by_ticket_id(ticket_id, limit=limit)
    
    def create_message(self, message: Message) -> Message:
        """
        Create a new message
        
        Args:
            message: Message object to create
            
        Returns:
            Created message with ID
            
        Examples:
            >>> from src.models.message import Message
            >>> service = MessageService()
            >>> msg = Message(
            ...     ticket_id="ticket-123",
            ...     role="user",
            ...     content="Hello"
            ... )
            >>> created = service.create_message(msg)
        """
        return self.message_repo.create(message)
    
    def get_message_stats(self, ticket_id: str) -> dict:
        """
        Get statistics about messages for a ticket
        
        Args:
            ticket_id: Ticket ID
            
        Returns:
            Dictionary with message statistics
            
        Examples:
            >>> service = MessageService()
            >>> stats = service.get_message_stats("ticket-123")
            >>> print(f"Total: {stats['total']}, User: {stats['user_messages']}")
        """
        messages = self.get_messages(ticket_id)
        
        stats = {
            "total": len(messages),
            "user_messages": sum(1 for m in messages if m.role == "user"),
            "assistant_messages": sum(1 for m in messages if m.role == "assistant"),
            "system_messages": sum(1 for m in messages if m.role == "system"),
            "total_tokens": sum(m.tokens_used or 0 for m in messages),
        }
        
        if messages:
            stats["first_message_at"] = messages[0].timestamp
            stats["last_message_at"] = messages[-1].timestamp
        
        return stats
    
    def check_limit_and_get_stats(self, ticket_id: str, limit: int) -> dict:
        """
        Check message limit and get stats in one call (optimization)
        
        Args:
            ticket_id: Ticket ID
            limit: Message limit to check
            
        Returns:
            Dictionary with limit check and stats
            
        Examples:
            >>> service = MessageService()
            >>> result = service.check_limit_and_get_stats("ticket-123", 50)
            >>> if result['over_limit']:
            ...     print(f"Exceeded by {result['count'] - 50} messages")
        """
        count = self.get_message_count(ticket_id)
        last_message = self.get_last_message(ticket_id)
        
        return {
            "count": count,
            "limit": limit,
            "over_limit": count > limit,
            "remaining": max(0, limit - count),
            "last_message": last_message,
        }
    
    def get_or_create_initial_message(
        self,
        ticket: Ticket,
        repository_name: Optional[str] = None
    ) -> Message:
        """
        Get the last message for a ticket, or create an initial message if none exists
        
        Uses Jinja2 templating to create a formatted initial message from ticket properties.
        
        Args:
            ticket: Ticket object
            repository_name: Optional repository name for the message
            
        Returns:
            Last message if exists, or newly created initial message
            
        Examples:
            >>> from src.models.ticket import Ticket, TicketStatus, TicketPriority, TicketType
            >>> service = MessageService()
            >>> ticket = Ticket(
            ...     id="ticket-123",
            ...     title="Fix login bug",
            ...     description="Users cannot login",
            ...     status=TicketStatus.open,
            ...     priority=TicketPriority.high,
            ...     ticket_type=TicketType.bugfix
            ... )
            >>> message = service.get_or_create_initial_message(ticket)
        """
        # Try to get existing message
        last_message = self.get_last_message(ticket.id)
        
        if last_message:
            return last_message
        
        # No message exists, create initial message from ticket
        content = self.template_service.render_ticket_initial_message(
            title=ticket.title,
            description=ticket.description,
            ticket_type=ticket.ticket_type.value if ticket.ticket_type else None,
            priority=ticket.priority.value if ticket.priority else None,
            repository_name=repository_name,
            ticket_id=ticket.id,
            status=ticket.status.value if ticket.status else None,
        )
        
        # Create initial message
        initial_message = Message(
            id=str(uuid.uuid4()),
            ticket_id=ticket.id,
            role="system",
            content=content,
            timestamp=datetime.utcnow(),
            metadata={
                "source": "auto_generated",
                "type": "initial_message",
                "created_from_ticket": True,
            }
        )
        
        # Save and return
        return self.create_message(initial_message)
