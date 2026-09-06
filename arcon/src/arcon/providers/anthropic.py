"""Anthropic Claude provider implementation."""
from typing import Any, AsyncIterator, Dict, List, Optional
import anthropic

from ..core.interface import ConfigError, LLMProvider, ProviderError
from ..core.types import Message, ModelInfo, ProviderConfig, ProviderType, ToolDefinition


class AnthropicProvider(LLMProvider):
    """Anthropic Claude LLM provider."""
    
    # Cost per 1M tokens (input, output) for various models
    COSTS = {
        "claude-opus-4-6": (15.0, 75.0),
        "claude-3-5-sonnet-20241022": (3.0, 15.0),
        "claude-3-5-haiku-20241022": (0.80, 4.0),
        "claude-3-opus-20240229": (15.0, 75.0),
        "claude-3-sonnet-20240229": (3.0, 15.0),
        "claude-3-haiku-20240307": (0.25, 1.25),
    }
    
    def __init__(self, config: ProviderConfig):
        """Initialize Anthropic provider."""
        super().__init__(config)
        self.client = anthropic.AsyncAnthropic(
            api_key=config.api_key,
            base_url=config.base_url,
            timeout=config.timeout,
        )
    
    def _validate_config(self) -> None:
        """Validate Anthropic configuration."""
        if not self.config.api_key:
            raise ConfigError("Anthropic API key is required")
        
        if not self.config.api_key.startswith("sk-ant-"):
            raise ConfigError("Invalid Anthropic API key format")
    
    async def create_message(
        self,
        messages: List[Message],
        tools: Optional[List[ToolDefinition]] = None,
        stream: bool = False,
        **kwargs: Any
    ) -> AsyncIterator[Dict[str, Any]]:
        """Create a message with Claude."""
        try:
            # Convert messages to Anthropic format
            anthropic_messages = []
            system_prompt = None
            
            for msg in messages:
                if msg.role.value == "system":
                    system_prompt = msg.content
                else:
                    anthropic_messages.append({
                        "role": msg.role.value,
                        "content": msg.content
                    })
            
            # Prepare request parameters
            request_params: Dict[str, Any] = {
                "model": self.config.model or "claude-opus-4-6",
                "messages": anthropic_messages,
                "max_tokens": self.config.max_tokens or 4096,
                "temperature": self.config.temperature,
                **kwargs
            }
            
            if system_prompt:
                request_params["system"] = system_prompt
            
            if tools:
                request_params["tools"] = [tool.to_dict() for tool in tools]
            
            if stream:
                async with self.client.messages.stream(**request_params) as stream_response:
                    async for event in stream_response:
                        if hasattr(event, "type"):
                            if event.type == "content_block_delta":
                                if hasattr(event.delta, "text"):
                                    yield {
                                        "type": "text",
                                        "content": event.delta.text
                                    }
                            elif event.type == "message_stop":
                                yield {
                                    "type": "completion",
                                    "reason": "stop"
                                }
            else:
                response = await self.client.messages.create(**request_params)
                
                # Yield complete response
                for block in response.content:
                    if block.type == "text":
                        yield {
                            "type": "text",
                            "content": block.text
                        }
                    elif block.type == "tool_use":
                        yield {
                            "type": "tool_call",
                            "tool_call": {
                                "id": block.id,
                                "name": block.name,
                                "arguments": block.input
                            }
                        }
                
                yield {
                    "type": "completion",
                    "reason": response.stop_reason or "stop"
                }
        
        except anthropic.APIError as e:
            raise ProviderError(f"Anthropic API error: {e}") from e
        except Exception as e:
            raise ProviderError(f"Unexpected error: {e}") from e
    
    async def list_models(self) -> List[ModelInfo]:
        """List available Anthropic models."""
        return [
            ModelInfo(
                id="claude-opus-4-6",
                provider=ProviderType.ANTHROPIC,
                name="Claude Opus 4.6",
                context_window=200_000,
                supports_tools=True,
                supports_streaming=True
            ),
            ModelInfo(
                id="claude-3-5-sonnet-20241022",
                provider=ProviderType.ANTHROPIC,
                name="Claude 3.5 Sonnet",
                context_window=200_000,
                supports_tools=True,
                supports_streaming=True
            ),
            ModelInfo(
                id="claude-3-5-haiku-20241022",
                provider=ProviderType.ANTHROPIC,
                name="Claude 3.5 Haiku",
                context_window=200_000,
                supports_tools=True,
                supports_streaming=True
            ),
            ModelInfo(
                id="claude-3-opus-20240229",
                provider=ProviderType.ANTHROPIC,
                name="Claude 3 Opus",
                context_window=200_000,
                supports_tools=True,
                supports_streaming=True
            ),
            ModelInfo(
                id="claude-3-sonnet-20240229",
                provider=ProviderType.ANTHROPIC,
                name="Claude 3 Sonnet",
                context_window=200_000,
                supports_tools=True,
                supports_streaming=True
            ),
            ModelInfo(
                id="claude-3-haiku-20240307",
                provider=ProviderType.ANTHROPIC,
                name="Claude 3 Haiku",
                context_window=200_000,
                supports_tools=True,
                supports_streaming=True
            ),
        ]
    
    def get_cost_per_token(self, model: str) -> tuple[float, float]:
        """Get cost per million tokens for a model."""
        return self.COSTS.get(model, (0.0, 0.0))
