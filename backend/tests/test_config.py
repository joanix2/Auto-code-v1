"""
Test configuration module
"""
import pytest
from config import config


def test_config_loaded():
    """Test that configuration is loaded"""
    assert config is not None


def test_config_has_required_fields():
    """Test that config has required fields"""
    assert hasattr(config, 'RABBITMQ_HOST')
    assert hasattr(config, 'RABBITMQ_PORT')
    assert hasattr(config, 'API_HOST')
    assert hasattr(config, 'API_PORT')


def test_default_values():
    """Test default configuration values"""
    assert config.RABBITMQ_HOST == 'localhost' or config.RABBITMQ_HOST != ''
    assert config.RABBITMQ_PORT == 5672
    assert config.API_PORT == 8000
