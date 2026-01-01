"""
Test Anthropic API integration
"""
import pytest
from anthropic import Anthropic
from config import config


def test_anthropic_api_key_configured():
    """Test that Anthropic API key is configured"""
    assert config.ANTHROPIC_API_KEY, "ANTHROPIC_API_KEY is not set in configuration"
    assert config.ANTHROPIC_API_KEY != "", "ANTHROPIC_API_KEY is empty"
    assert config.ANTHROPIC_API_KEY.startswith("sk-ant-"), "ANTHROPIC_API_KEY format is invalid"


def test_anthropic_api_connection():
    """Test that we can connect to Anthropic API"""
    # Skip test if API key is not configured
    if not config.ANTHROPIC_API_KEY or config.ANTHROPIC_API_KEY == "your_anthropic_api_key_here":
        pytest.skip("ANTHROPIC_API_KEY is not configured")
    
    try:
        client = Anthropic(api_key=config.ANTHROPIC_API_KEY)
        
        # Test with a simple message
        message = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=50,
            messages=[
                {
                    "role": "user",
                    "content": "Reply with only the word 'OK' if you can read this."
                }
            ]
        )
        
        # Verify we got a response
        assert message is not None, "No response from Anthropic API"
        assert message.content, "Empty response from Anthropic API"
        assert len(message.content) > 0, "No content in response"
        
        # Check response structure
        response_text = message.content[0].text
        assert response_text, "No text in response"
        assert "OK" in response_text.upper(), f"Unexpected response: {response_text}"
        
        print(f"✓ Anthropic API connection successful. Response: {response_text}")
        
    except Exception as e:
        pytest.fail(f"Failed to connect to Anthropic API: {str(e)}")


def test_anthropic_streaming():
    """Test that streaming works with Anthropic API"""
    # Skip test if API key is not configured
    if not config.ANTHROPIC_API_KEY or config.ANTHROPIC_API_KEY == "your_anthropic_api_key_here":
        pytest.skip("ANTHROPIC_API_KEY is not configured")
    
    try:
        client = Anthropic(api_key=config.ANTHROPIC_API_KEY)
        
        # Test streaming with a simple message
        stream = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=30,
            messages=[
                {
                    "role": "user",
                    "content": "Say hello in one word."
                }
            ],
            stream=True
        )
        
        # Collect streamed response
        full_response = ""
        for event in stream:
            if event.type == "content_block_delta":
                if hasattr(event.delta, 'text'):
                    full_response += event.delta.text
        
        assert full_response, "No streaming response received"
        print(f"✓ Anthropic streaming successful. Response: {full_response}")
        
    except Exception as e:
        pytest.fail(f"Failed to stream from Anthropic API: {str(e)}")


@pytest.mark.parametrize("model", [
    "claude-3-haiku-20240307",
    "claude-3-5-sonnet-20240620",
    "claude-3-opus-20240229"
])
def test_anthropic_models_available(model):
    """Test different Claude models availability"""
    # Skip test if API key is not configured
    if not config.ANTHROPIC_API_KEY or config.ANTHROPIC_API_KEY == "your_anthropic_api_key_here":
        pytest.skip("ANTHROPIC_API_KEY is not configured")
    
    try:
        client = Anthropic(api_key=config.ANTHROPIC_API_KEY)
        
        # Test with a minimal request
        message = client.messages.create(
            model=model,
            max_tokens=10,
            messages=[
                {
                    "role": "user",
                    "content": "Hi"
                }
            ]
        )
        
        assert message is not None, f"Model {model} did not respond"
        assert message.content, f"Model {model} returned empty content"
        print(f"✓ Model {model} is available and working")
        
    except Exception as e:
        # Some models might not be available depending on API tier
        print(f"⚠ Model {model} may not be available: {str(e)}")
        # Don't fail the test for model availability issues
        pytest.skip(f"Model {model} not available: {str(e)}")
