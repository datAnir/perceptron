"""Provider factory and resolver."""
from typing import Optional

from ..core.interface import ConfigError, LLMProvider
from ..core.types import ProviderConfig, ProviderType
from ..config import get_provider_config

from .anthropic import AnthropicProvider
from .openai import OpenAIProvider
from .ollama import OllamaProvider


class ProviderResolver:
    """Factory for creating LLM providers."""
    
    _PROVIDERS = {
        ProviderType.ANTHROPIC: AnthropicProvider,
        ProviderType.OPENAI: OpenAIProvider,
        ProviderType.OLLAMA: OllamaProvider,
    }
    
    @classmethod
    def create(cls, config: ProviderConfig) -> LLMProvider:
        """Create a provider instance from configuration.
        
        Args:
            config: Provider configuration
            
        Returns:
            Initialized provider instance
            
        Raises:
            ConfigError: If provider type is not supported
        """
        provider_class = cls._PROVIDERS.get(config.provider_type)
        
        if not provider_class:
            raise ConfigError(
                f"Unsupported provider type: {config.provider_type}. "
                f"Supported providers: {list(cls._PROVIDERS.keys())}"
            )
        
        return provider_class(config)
    
    @classmethod
    def get_provider(
        cls,
        provider_type: ProviderType,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> LLMProvider:
        """Convenience method to create a provider with env var fallback.
        
        Args:
            provider_type: Type of provider to create
            api_key: API key for the provider (falls back to env var)
            model: Model to use (falls back to env var)
            **kwargs: Additional configuration options
            
        Returns:
            Initialized provider instance
            
        Note:
            If api_key is not provided, it will be loaded from environment
            variables (ANTHROPIC_API_KEY, OPENAI_API_KEY, etc.)
        """
        # Use config utility to get config with env var fallback
        config = get_provider_config(
            provider_type=provider_type,
            api_key=api_key,
            model=model,
            **kwargs
        )
        
        return cls.create(config)
    
    @classmethod
    def list_providers(cls) -> list[ProviderType]:
        """List all supported provider types."""
        return list(cls._PROVIDERS.keys())
