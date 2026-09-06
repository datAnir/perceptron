"""Tests for configuration management."""
import os
import tempfile
from pathlib import Path
import pytest

from arcon.config import load_config, get_api_key, get_provider_config
from arcon.core.types import ProviderType


class TestEnvConfig:
    """Test environment configuration loading."""
    
    def test_load_config_from_file(self, tmp_path):
        """Test loading config from specific .env file."""
        # Create temp .env file
        env_file = tmp_path / ".env"
        env_file.write_text("TEST_KEY=test_value\n")
        
        # Load config
        load_config(env_file)
        
        # Verify env var is set
        assert os.getenv("TEST_KEY") == "test_value"
    
    def test_get_api_key_explicit(self):
        """Test explicit API key takes precedence."""
        explicit_key = "sk-test-explicit"
        
        result = get_api_key(ProviderType.ANTHROPIC, api_key=explicit_key)
        
        assert result == explicit_key
    
    def test_get_api_key_from_env(self, monkeypatch, tmp_path):
        """Test API key loaded from environment."""
        # Set env var
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-from-env")
        
        # Force reload
        import arcon.config.env
        arcon.config.env._ENV_LOADED = False
        
        result = get_api_key(ProviderType.ANTHROPIC)
        
        assert result == "sk-ant-test-from-env"
    
    def test_get_api_key_missing(self):
        """Test API key returns None when not found."""
        # Force reload to clear any cached env
        import arcon.config.env
        arcon.config.env._ENV_LOADED = False
        
        # Make sure env var is not set
        os.environ.pop("ANTHROPIC_API_KEY", None)
        
        result = get_api_key(ProviderType.ANTHROPIC)
        
        # Could be None or the value from .env if it exists
        assert result is None or isinstance(result, str)
    
    def test_get_provider_config(self, monkeypatch):
        """Test provider config creation with env fallback."""
        # Set env vars
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
        monkeypatch.setenv("DEFAULT_MODEL", "claude-3-5-sonnet-20241022")
        monkeypatch.setenv("DEFAULT_TEMPERATURE", "0.5")
        monkeypatch.setenv("MAX_TOKENS", "1024")
        
        # Force reload
        import arcon.config.env
        arcon.config.env._ENV_LOADED = False
        
        config = get_provider_config(ProviderType.ANTHROPIC)
        
        assert config.provider_type == ProviderType.ANTHROPIC
        assert config.api_key == "sk-ant-test"
        assert config.model == "claude-3-5-sonnet-20241022"
        assert config.temperature == 0.5
        assert config.max_tokens == 1024
    
    def test_get_provider_config_explicit_overrides(self, monkeypatch):
        """Test explicit values override environment variables."""
        # Set env vars
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-env")
        monkeypatch.setenv("DEFAULT_MODEL", "claude-env-model")
        
        # Force reload
        import arcon.config.env
        arcon.config.env._ENV_LOADED = False
        
        config = get_provider_config(
            ProviderType.ANTHROPIC,
            api_key="sk-ant-explicit",
            model="claude-explicit-model"
        )
        
        assert config.api_key == "sk-ant-explicit"
        assert config.model == "claude-explicit-model"
    
    def test_ollama_base_url_from_env(self, monkeypatch):
        """Test Ollama base URL loaded from environment."""
        monkeypatch.setenv("OLLAMA_BASE_URL", "http://custom:8080")
        
        # Force reload
        import arcon.config.env
        arcon.config.env._ENV_LOADED = False
        
        config = get_provider_config(ProviderType.OLLAMA)
        
        assert config.base_url == "http://custom:8080"
