"""OpenAI provider implementation."""
from typing import Any, AsyncIterator, Dict, List, Optional
import openai

from ..core.interface import ConfigError, LLMProvider, ProviderError
from ..core.types import Message, ModelInfo, ProviderConfig, ProviderType, ToolDefinition


class OpenAIProvider(LLMProvider):
    """OpenAI LLM provider."""
    
    # Cost per 1M tokens (input, output) for various models
    COSTS = {
        "gpt-4-turbo": (10.0, 30.0),
        "gpt-4-turbo-2024-04-09": (10.0, 30.0),
        "gpt-4": (30.0, 60.0),
        "gpt-4-0613": (30.0, 60.0),
        "gpt-3.5-turbo": (0.50, 1.50),
        "gpt-3.5-turbo-0125": (0.50, 1.50),
    }
    
    def __init__(self, config: ProviderConfig):
        """Initialize OpenAI provider."""
        super().__init__(config)
        self.client = openai.AsyncOpenAI(
            api_key=config.api_key,
            base_url=config.base_url,
            timeout=config.timeout,
        )
    
    def _validate_config(self) -> None:
        """Validate OpenAI configuration."""
        if not self.config.api_key:
            raise ConfigError("OpenAI API key is required")
        
        if not self.config.api_key.startswith("sk-"):
            raise ConfigError("Invalid OpenAI API key format")
    
    async def create_message(
        self,
        messages: List[Message],
        tools: Optional[List[ToolDefinition]] = None,
        stream: bool = False,
        **kwargs: Any
    ) -> AsyncIterator[Dict[str, Any]]:
        """Create a message with OpenAI."""
        try:
            # Convert messages to OpenAI format
            openai_messages = [
                {
                    "role": msg.role.value,
                    "content": msg.content
                }
                for msg in messages
            ]
            
            # Prepare request parameters
            request_params: Dict[str, Any] = {
                "model": self.config.model or "gpt-4-turbo",
                "messages": openai_messages,
                "temperature": self.config.temperature,
                **kwargs
            }
            
            if self.config.max_tokens:
                request_params["max_tokens"] = self.config.max_tokens
            
            if tools:
                request_params["tools"] = [
                    {
                        "type": "function",
                        "function": {
                            "name": tool.name,
                            "description": tool.description,
                            "parameters": tool.to_dict()["input_schema"]
                        }
                    }
                    for tool in tools
                ]
            
            if stream:
                stream_response = await self.client.chat.completions.create(
                    stream=True,
                    **request_params
                )
                
                async for chunk in stream_response:
                    if chunk.choices:
                        delta = chunk.choices[0].delta
                        
                        if delta.content:
                            yield {
                                "type": "text",
                                "content": delta.content
                            }
                        
                        if delta.tool_calls:
                            for tool_call in delta.tool_calls:
                                if tool_call.function:
                                    yield {
                                        "type": "tool_call",
                                        "tool_call": {
                                            "id": tool_call.id or "",
                                            "name": tool_call.function.name or "",
                                            "arguments": tool_call.function.arguments or ""
                                        }
                                    }
                        
                        if chunk.choices[0].finish_reason:
                            yield {
                                "type": "completion",
                                "reason": chunk.choices[0].finish_reason
                            }
            else:
                response = await self.client.chat.completions.create(**request_params)
                
                # Yield complete response
                if response.choices:
                    choice = response.choices[0]
                    
                    if choice.message.content:
                        yield {
                            "type": "text",
                            "content": choice.message.content
                        }
                    
                    if choice.message.tool_calls:
                        for tool_call in choice.message.tool_calls:
                            yield {
                                "type": "tool_call",
                                "tool_call": {
                                    "id": tool_call.id,
                                    "name": tool_call.function.name,
                                    "arguments": tool_call.function.arguments
                                }
                            }
                    
                    yield {
                        "type": "completion",
                        "reason": choice.finish_reason or "stop"
                    }
        
        except openai.APIError as e:
            raise ProviderError(f"OpenAI API error: {e}") from e
        except Exception as e:
            raise ProviderError(f"Unexpected error: {e}") from e
    
    async def list_models(self) -> List[ModelInfo]:
        """List available OpenAI models."""
        return [
            ModelInfo(
                id="gpt-4-turbo",
                provider=ProviderType.OPENAI,
                name="GPT-4 Turbo",
                context_window=128_000,
                supports_tools=True,
                supports_streaming=True
            ),
            ModelInfo(
                id="gpt-4",
                provider=ProviderType.OPENAI,
                name="GPT-4",
                context_window=8_192,
                supports_tools=True,
                supports_streaming=True
            ),
            ModelInfo(
                id="gpt-3.5-turbo",
                provider=ProviderType.OPENAI,
                name="GPT-3.5 Turbo",
                context_window=16_384,
                supports_tools=True,
                supports_streaming=True
            ),
        ]
    
    def get_cost_per_token(self, model: str) -> tuple[float, float]:
        """Get cost per million tokens for a model."""
        return self.COSTS.get(model, (0.0, 0.0))
