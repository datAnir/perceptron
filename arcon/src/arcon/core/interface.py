"""Abstract interfaces for Arcon core components."""
from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Dict, List, Optional

from .types import Message, ModelInfo, ProviderConfig, ToolDefinition


class ArconError(Exception):
    """Base exception for all Arcon errors."""
    pass


class ProviderError(ArconError):
    """Error related to LLM provider operations."""
    pass


class ToolError(ArconError):
    """Error related to tool execution."""
    pass


class SessionError(ArconError):
    """Error related to session management."""
    pass


class ConfigError(ArconError):
    """Error related to configuration."""
    pass


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    def __init__(self, config: ProviderConfig):
        """Initialize provider with configuration."""
        self.config = config
        self._validate_config()
    
    @abstractmethod
    def _validate_config(self) -> None:
        """Validate provider configuration.
        
        Raises:
            ConfigError: If configuration is invalid.
        """
        pass
    
    @abstractmethod
    async def create_message(
        self,
        messages: List[Message],
        tools: Optional[List[ToolDefinition]] = None,
        stream: bool = False,
        **kwargs: Any
    ) -> AsyncIterator[Dict[str, Any]]:
        """Create a message with the LLM.
        
        Args:
            messages: Conversation history
            tools: Available tools for the LLM
            stream: Whether to stream the response
            **kwargs: Additional provider-specific parameters
            
        Yields:
            Dictionary with response chunks:
            - {"type": "text", "content": str}
            - {"type": "tool_call", "tool_call": ToolCall}
            - {"type": "completion", "reason": str}
            
        Raises:
            ProviderError: If API call fails
        """
        pass
    
    @abstractmethod
    async def list_models(self) -> List[ModelInfo]:
        """List available models for this provider.
        
        Returns:
            List of available models with their capabilities
            
        Raises:
            ProviderError: If unable to fetch models
        """
        pass
    
    @abstractmethod
    def get_cost_per_token(self, model: str) -> tuple[float, float]:
        """Get cost per token for a specific model.
        
        Args:
            model: Model identifier
            
        Returns:
            Tuple of (input_cost_per_1m_tokens, output_cost_per_1m_tokens)
        """
        pass
    
    @property
    def provider_type(self) -> str:
        """Get the provider type."""
        return self.config.provider_type.value
    
    @property
    def is_configured(self) -> bool:
        """Check if provider is properly configured."""
        try:
            self._validate_config()
            return True
        except ConfigError:
            return False
