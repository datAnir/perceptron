"""Tests for provider implementations."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from arcon.core.types import Message, ProviderConfig, ProviderType, Role, ToolDefinition, ToolParameter
from arcon.core.interface import ConfigError, ProviderError
from arcon.providers import AnthropicProvider, OpenAIProvider, OllamaProvider, ProviderResolver


class TestProviderResolver:
    """Test ProviderResolver factory."""
    
    def test_create_anthropic_provider(self):
        """Test creating Anthropic provider."""
        config = ProviderConfig(
            provider_type=ProviderType.ANTHROPIC,
            api_key="sk-ant-test-key"
        )
        provider = ProviderResolver.create(config)
        assert isinstance(provider, AnthropicProvider)
    
    def test_create_openai_provider(self):
        """Test creating OpenAI provider."""
        config = ProviderConfig(
            provider_type=ProviderType.OPENAI,
            api_key="sk-test-key"
        )
        provider = ProviderResolver.create(config)
        assert isinstance(provider, OpenAIProvider)
    
    def test_create_ollama_provider(self):
        """Test creating Ollama provider."""
        config = ProviderConfig(
            provider_type=ProviderType.OLLAMA
        )
        provider = ProviderResolver.create(config)
        assert isinstance(provider, OllamaProvider)
    
    def test_get_provider_convenience(self):
        """Test get_provider convenience method."""
        provider = ProviderResolver.get_provider(
            provider_type=ProviderType.ANTHROPIC,
            api_key="sk-ant-test-key",
            model="claude-opus-4-6"
        )
        assert isinstance(provider, AnthropicProvider)
        assert provider.config.model == "claude-opus-4-6"
    
    def test_list_providers(self):
        """Test listing available providers."""
        providers = ProviderResolver.list_providers()
        assert ProviderType.ANTHROPIC in providers
        assert ProviderType.OPENAI in providers
        assert ProviderType.OLLAMA in providers


class TestAnthropicProvider:
    """Test AnthropicProvider."""
    
    def test_init_with_valid_key(self):
        """Test initialization with valid API key."""
        config = ProviderConfig(
            provider_type=ProviderType.ANTHROPIC,
            api_key="sk-ant-test-key"
        )
        provider = AnthropicProvider(config)
        assert provider.provider_type == "anthropic"
    
    def test_init_with_invalid_key(self):
        """Test initialization with invalid API key."""
        config = ProviderConfig(
            provider_type=ProviderType.ANTHROPIC,
            api_key="invalid-key"
        )
        with pytest.raises(ConfigError, match="Invalid Anthropic API key"):
            AnthropicProvider(config)
    
    def test_init_without_key(self):
        """Test initialization without API key."""
        config = ProviderConfig(
            provider_type=ProviderType.ANTHROPIC
        )
        with pytest.raises(ConfigError, match="API key is required"):
            AnthropicProvider(config)
    
    @pytest.mark.asyncio
    async def test_list_models(self):
        """Test listing Anthropic models."""
        config = ProviderConfig(
            provider_type=ProviderType.ANTHROPIC,
            api_key="sk-ant-test-key"
        )
        provider = AnthropicProvider(config)
        models = await provider.list_models()
        
        assert len(models) > 0
        assert any(m.id == "claude-opus-4-6" for m in models)
        assert all(m.provider == ProviderType.ANTHROPIC for m in models)
    
    def test_get_cost_per_token(self):
        """Test getting cost per token."""
        config = ProviderConfig(
            provider_type=ProviderType.ANTHROPIC,
            api_key="sk-ant-test-key"
        )
        provider = AnthropicProvider(config)
        
        input_cost, output_cost = provider.get_cost_per_token("claude-opus-4-6")
        assert input_cost == 15.0
        assert output_cost == 75.0
        
        # Unknown model should return 0.0, 0.0
        input_cost, output_cost = provider.get_cost_per_token("unknown-model")
        assert input_cost == 0.0
        assert output_cost == 0.0
    
    @pytest.mark.asyncio
    async def test_create_message_basic(self):
        """Test basic message creation (mocked)."""
        config = ProviderConfig(
            provider_type=ProviderType.ANTHROPIC,
            api_key="sk-ant-test-key",
            model="claude-opus-4-6"
        )
        provider = AnthropicProvider(config)
        
        # Mock the client
        mock_response = MagicMock()
        mock_response.content = [MagicMock(type="text", text="Hello!")]
        mock_response.stop_reason = "end_turn"
        
        with patch.object(provider.client.messages, 'create', new=AsyncMock(return_value=mock_response)):
            messages = [Message(role=Role.USER, content="Hi")]
            chunks = []
            
            async for chunk in provider.create_message(messages, stream=False):
                chunks.append(chunk)
            
            assert len(chunks) == 2  # text chunk + completion chunk
            assert chunks[0]["type"] == "text"
            assert chunks[0]["content"] == "Hello!"
            assert chunks[1]["type"] == "completion"


class TestOpenAIProvider:
    """Test OpenAIProvider."""
    
    def test_init_with_valid_key(self):
        """Test initialization with valid API key."""
        config = ProviderConfig(
            provider_type=ProviderType.OPENAI,
            api_key="sk-test-key"
        )
        provider = OpenAIProvider(config)
        assert provider.provider_type == "openai"
    
    def test_init_with_invalid_key(self):
        """Test initialization with invalid API key."""
        config = ProviderConfig(
            provider_type=ProviderType.OPENAI,
            api_key="invalid-key"
        )
        with pytest.raises(ConfigError, match="Invalid OpenAI API key"):
            OpenAIProvider(config)
    
    def test_init_without_key(self):
        """Test initialization without API key."""
        config = ProviderConfig(
            provider_type=ProviderType.OPENAI
        )
        with pytest.raises(ConfigError, match="API key is required"):
            OpenAIProvider(config)
    
    @pytest.mark.asyncio
    async def test_list_models(self):
        """Test listing OpenAI models."""
        config = ProviderConfig(
            provider_type=ProviderType.OPENAI,
            api_key="sk-test-key"
        )
        provider = OpenAIProvider(config)
        models = await provider.list_models()
        
        assert len(models) > 0
        assert any(m.id == "gpt-4-turbo" for m in models)
        assert all(m.provider == ProviderType.OPENAI for m in models)
    
    def test_get_cost_per_token(self):
        """Test getting cost per token."""
        config = ProviderConfig(
            provider_type=ProviderType.OPENAI,
            api_key="sk-test-key"
        )
        provider = OpenAIProvider(config)
        
        input_cost, output_cost = provider.get_cost_per_token("gpt-4-turbo")
        assert input_cost == 10.0
        assert output_cost == 30.0


class TestOllamaProvider:
    """Test OllamaProvider."""
    
    def test_init_default_url(self):
        """Test initialization with default URL."""
        config = ProviderConfig(
            provider_type=ProviderType.OLLAMA
        )
        provider = OllamaProvider(config)
        assert provider.base_url == "http://localhost:11434"
    
    def test_init_custom_url(self):
        """Test initialization with custom URL."""
        config = ProviderConfig(
            provider_type=ProviderType.OLLAMA,
            base_url="http://custom-host:11434"
        )
        provider = OllamaProvider(config)
        assert provider.base_url == "http://custom-host:11434"
    
    @pytest.mark.asyncio
    async def test_list_models_fallback(self):
        """Test listing models when connection fails."""
        config = ProviderConfig(
            provider_type=ProviderType.OLLAMA
        )
        provider = OllamaProvider(config)
        
        # Should return default models if can't connect
        models = await provider.list_models()
        assert len(models) > 0
        assert all(m.provider == ProviderType.OLLAMA for m in models)
    
    def test_get_cost_per_token(self):
        """Test getting cost per token (should be free)."""
        config = ProviderConfig(
            provider_type=ProviderType.OLLAMA
        )
        provider = OllamaProvider(config)
        
        input_cost, output_cost = provider.get_cost_per_token("llama3.2")
        assert input_cost == 0.0
        assert output_cost == 0.0
