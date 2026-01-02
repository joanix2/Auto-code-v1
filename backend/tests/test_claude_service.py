"""Tests for Claude AI Service"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from src.services.claude_service import ClaudeService
import os


class TestClaudeService:
    """Test suite for ClaudeService"""
    
    def test_init_with_api_key(self):
        """Test initialization with API key"""
        service = ClaudeService(api_key="test-key-123")
        assert service.api_key == "test-key-123"
        assert service.model == "claude-3-5-sonnet-20241022"
        assert service.base_url == "https://api.anthropic.com/v1"
    
    def test_init_without_api_key_raises_error(self):
        """Test initialization without API key raises ValueError"""
        # Temporarily remove env var if it exists
        old_key = os.environ.pop("ANTHROPIC_API_KEY", None)
        
        try:
            with pytest.raises(ValueError, match="ANTHROPIC_API_KEY not provided"):
                ClaudeService()
        finally:
            # Restore env var
            if old_key:
                os.environ["ANTHROPIC_API_KEY"] = old_key
    
    def test_generate_ticket_prompt(self):
        """Test prompt generation for ticket"""
        service = ClaudeService(api_key="test-key")
        
        prompt = service.generate_ticket_prompt(
            ticket_title="Add login feature",
            ticket_description="Implement user authentication",
            ticket_type="feature",
            priority="high",
            repository_name="test-repo"
        )
        
        assert "Add login feature" in prompt
        assert "Implement user authentication" in prompt
        assert "✨ Nouvelle fonctionnalité" in prompt
        assert "🟠 HAUTE" in prompt
        assert "test-repo" in prompt
    
    def test_generate_ticket_prompt_with_path(self):
        """Test prompt generation with repository path"""
        service = ClaudeService(api_key="test-key")
        
        prompt = service.generate_ticket_prompt(
            ticket_title="Fix bug",
            ticket_description="Fix critical issue",
            ticket_type="bugfix",
            priority="critical",
            repository_name="test-repo",
            repository_path="/path/to/repo"
        )
        
        assert "Fix bug" in prompt
        assert "🐛 Correction de bug" in prompt
        assert "🔴 CRITIQUE" in prompt
        assert "/path/to/repo" in prompt
    
    @pytest.mark.asyncio
    async def test_send_message_success(self):
        """Test successful message sending to Claude API"""
        service = ClaudeService(api_key="test-key")
        
        mock_response = {
            "id": "msg_123",
            "type": "message",
            "role": "assistant",
            "content": [{"type": "text", "text": "Hello!"}],
            "model": "claude-3-5-sonnet-20241022",
            "usage": {"input_tokens": 10, "output_tokens": 5}
        }
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_post = AsyncMock()
            mock_post.return_value.json.return_value = mock_response
            mock_post.return_value.raise_for_status = Mock()
            
            mock_client.return_value.__aenter__.return_value.post = mock_post
            
            result = await service.send_message("Test prompt")
            
            assert result["id"] == "msg_123"
            assert result["content"][0]["text"] == "Hello!"
            assert result["model"] == "claude-3-5-sonnet-20241022"
    
    @pytest.mark.asyncio
    async def test_send_message_with_system_message(self):
        """Test sending message with system context"""
        service = ClaudeService(api_key="test-key")
        
        mock_response = {
            "id": "msg_456",
            "type": "message",
            "role": "assistant",
            "content": [{"type": "text", "text": "Response"}],
            "model": "claude-3-5-sonnet-20241022",
            "usage": {"input_tokens": 20, "output_tokens": 10}
        }
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_post = AsyncMock()
            mock_post.return_value.json.return_value = mock_response
            mock_post.return_value.raise_for_status = Mock()
            
            mock_client.return_value.__aenter__.return_value.post = mock_post
            
            result = await service.send_message(
                "User prompt",
                system_message="You are a helpful assistant"
            )
            
            # Verify the call was made with system message
            call_args = mock_post.call_args
            assert call_args[1]["json"]["system"] == "You are a helpful assistant"
            assert result["id"] == "msg_456"
    
    @pytest.mark.asyncio
    async def test_develop_ticket(self):
        """Test full ticket development workflow"""
        service = ClaudeService(api_key="test-key")
        
        mock_response = {
            "id": "msg_789",
            "type": "message",
            "role": "assistant",
            "content": [{"type": "text", "text": "Implementation code here"}],
            "model": "claude-3-5-sonnet-20241022",
            "usage": {"input_tokens": 100, "output_tokens": 500}
        }
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_post = AsyncMock()
            mock_post.return_value.json.return_value = mock_response
            mock_post.return_value.raise_for_status = Mock()
            
            mock_client.return_value.__aenter__.return_value.post = mock_post
            
            result = await service.develop_ticket(
                ticket_title="Add feature X",
                ticket_description="Detailed description",
                ticket_type="feature",
                priority="medium",
                repository_name="my-repo",
                repository_path="/path/to/repo"
            )
            
            assert "prompt" in result
            assert "response" in result
            assert "content" in result
            assert "model" in result
            assert "usage" in result
            assert result["content"] == "Implementation code here"
            assert result["model"] == "claude-3-5-sonnet-20241022"
    
    @pytest.mark.asyncio
    async def test_develop_ticket_with_additional_context(self):
        """Test ticket development with additional context"""
        service = ClaudeService(api_key="test-key")
        
        mock_response = {
            "id": "msg_999",
            "type": "message",
            "role": "assistant",
            "content": [{"type": "text", "text": "Code with context"}],
            "model": "claude-3-5-sonnet-20241022",
            "usage": {"input_tokens": 150, "output_tokens": 600}
        }
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_post = AsyncMock()
            mock_post.return_value.json.return_value = mock_response
            mock_post.return_value.raise_for_status = Mock()
            
            mock_client.return_value.__aenter__.return_value.post = mock_post
            
            result = await service.develop_ticket(
                ticket_title="Refactor module",
                ticket_description="Clean up code",
                ticket_type="refactor",
                priority="low",
                repository_name="test-repo",
                additional_context="Existing code:\ndef foo(): pass"
            )
            
            # Check that additional context is in the prompt
            assert "Contexte Additionnel" in result["prompt"]
            assert "def foo(): pass" in result["prompt"]
            assert result["content"] == "Code with context"
    
    @pytest.mark.asyncio
    async def test_api_error_handling(self):
        """Test handling of API errors"""
        service = ClaudeService(api_key="test-key")
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_post = AsyncMock()
            mock_post.return_value.raise_for_status.side_effect = Exception("API Error")
            
            mock_client.return_value.__aenter__.return_value.post = mock_post
            
            with pytest.raises(Exception, match="API Error"):
                await service.send_message("Test")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
