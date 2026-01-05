"""
Tests for Message Service
"""

import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime

from src.services.message_service import MessageService
from src.models.message import Message


class TestMessageService:
    """Test cases for MessageService"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.mock_repo = Mock()
        self.service = MessageService(message_repo=self.mock_repo)
    
    def test_get_message_count(self):
        """Test getting message count"""
        # Arrange
        ticket_id = "ticket-123"
        mock_messages = [
            Message(
                id="1",
                ticket_id=ticket_id,
                role="user",
                content="Test 1",
                timestamp=datetime.now()
            ),
            Message(
                id="2",
                ticket_id=ticket_id,
                role="assistant",
                content="Test 2",
                timestamp=datetime.now()
            ),
        ]
        self.mock_repo.get_by_ticket_id.return_value = mock_messages
        
        # Act
        count = self.service.get_message_count(ticket_id)
        
        # Assert
        assert count == 2
        self.mock_repo.get_by_ticket_id.assert_called_once_with(ticket_id)
    
    def test_is_over_limit_true(self):
        """Test is_over_limit returns True when over limit"""
        # Arrange
        ticket_id = "ticket-123"
        mock_messages = [Mock() for _ in range(51)]
        self.mock_repo.get_by_ticket_id.return_value = mock_messages
        
        # Act
        result = self.service.is_over_limit(ticket_id, 50)
        
        # Assert
        assert result is True
    
    def test_is_over_limit_false(self):
        """Test is_over_limit returns False when within limit"""
        # Arrange
        ticket_id = "ticket-123"
        mock_messages = [Mock() for _ in range(30)]
        self.mock_repo.get_by_ticket_id.return_value = mock_messages
        
        # Act
        result = self.service.is_over_limit(ticket_id, 50)
        
        # Assert
        assert result is False
    
    def test_get_last_message(self):
        """Test getting last message"""
        # Arrange
        ticket_id = "ticket-123"
        expected_message = Message(
            id="last",
            ticket_id=ticket_id,
            role="assistant",
            content="Last message",
            timestamp=datetime.now()
        )
        self.mock_repo.get_latest_by_ticket_id.return_value = expected_message
        
        # Act
        result = self.service.get_last_message(ticket_id)
        
        # Assert
        assert result == expected_message
        self.mock_repo.get_latest_by_ticket_id.assert_called_once_with(ticket_id)
    
    def test_get_message_stats(self):
        """Test getting message statistics"""
        # Arrange
        ticket_id = "ticket-123"
        now = datetime.now()
        mock_messages = [
            Message(
                id="1",
                ticket_id=ticket_id,
                role="user",
                content="User message",
                timestamp=now,
                tokens_used=10
            ),
            Message(
                id="2",
                ticket_id=ticket_id,
                role="assistant",
                content="Assistant message",
                timestamp=now,
                tokens_used=20
            ),
            Message(
                id="3",
                ticket_id=ticket_id,
                role="system",
                content="System message",
                timestamp=now,
                tokens_used=5
            ),
        ]
        self.mock_repo.get_by_ticket_id.return_value = mock_messages
        
        # Act
        stats = self.service.get_message_stats(ticket_id)
        
        # Assert
        assert stats["total"] == 3
        assert stats["user_messages"] == 1
        assert stats["assistant_messages"] == 1
        assert stats["system_messages"] == 1
        assert stats["total_tokens"] == 35
        assert "first_message_at" in stats
        assert "last_message_at" in stats
    
    def test_check_limit_and_get_stats(self):
        """Test checking limit and getting stats together"""
        # Arrange
        ticket_id = "ticket-123"
        limit = 50
        mock_messages = [Mock() for _ in range(30)]
        last_message = Message(
            id="last",
            ticket_id=ticket_id,
            role="user",
            content="Last",
            timestamp=datetime.now()
        )
        
        self.mock_repo.get_by_ticket_id.return_value = mock_messages
        self.mock_repo.get_latest_by_ticket_id.return_value = last_message
        
        # Act
        result = self.service.check_limit_and_get_stats(ticket_id, limit)
        
        # Assert
        assert result["count"] == 30
        assert result["limit"] == 50
        assert result["over_limit"] is False
        assert result["remaining"] == 20
        assert result["last_message"] == last_message
    
    def test_check_limit_and_get_stats_over_limit(self):
        """Test check_limit_and_get_stats when over limit"""
        # Arrange
        ticket_id = "ticket-123"
        limit = 50
        mock_messages = [Mock() for _ in range(60)]
        
        self.mock_repo.get_by_ticket_id.return_value = mock_messages
        self.mock_repo.get_latest_by_ticket_id.return_value = None
        
        # Act
        result = self.service.check_limit_and_get_stats(ticket_id, limit)
        
        # Assert
        assert result["count"] == 60
        assert result["over_limit"] is True
        assert result["remaining"] == 0
