"""Ollama local LLM provider implementation."""
import json
from typing import Any, AsyncIterator, Dict, List, Optional
import aiohttp

from ..core.interface import ConfigError, LLMProvider, ProviderError
from ..core.types import Message, ModelInfo, ProviderConfig, ProviderType, ToolDefinition


class OllamaProvider(LLMProvider):
    """Ollama local LLM provider."""
    
    def __init__(self, config: ProviderConfig):
        """Initialize Ollama provider."""
        # Set base_url before calling super().__init__() which calls _validate_config()
        self.base_url = config.base_url or "http://localhost:11434"
        super().__init__(config)
    
    def _validate_config(self) -> None:
        """Validate Ollama configuration."""
        # Ollama doesn't require API key, default URL is fine
        pass
    
    async def create_message(
        self,
        messages: List[Message],
        tools: Optional[List[ToolDefinition]] = None,
        stream: bool = False,
        **kwargs: Any
    ) -> AsyncIterator[Dict[str, Any]]:
        """Create a message with Ollama."""
        try:
            # Convert messages to Ollama format
            ollama_messages = [
                {
                    "role": msg.role.value,
                    "content": msg.content
                }
                for msg in messages
            ]
            
            # Prepare request
            payload = {
                "model": self.config.model or "llama3.2",
                "messages": ollama_messages,
                "stream": stream,
                "options": {
                    "temperature": self.config.temperature,
                }
            }
            
            if self.config.max_tokens:
                payload["options"]["num_predict"] = self.config.max_tokens
            
            # Note: Ollama tool support is limited, we'll skip tools for now
            # if tools:
            #     payload["tools"] = [tool.to_dict() for tool in tools]
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/chat",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=self.config.timeout)
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise ProviderError(f"Ollama API error: {error_text}")
                    
                    if stream:
                        async for line in response.content:
                            if line:
                                try:
                                    chunk = json.loads(line)
                                    
                                    if "message" in chunk and "content" in chunk["message"]:
                                        content = chunk["message"]["content"]
                                        if content:
                                            yield {
                                                "type": "text",
                                                "content": content
                                            }
                                    
                                    if chunk.get("done", False):
                                        yield {
                                            "type": "completion",
                                            "reason": "stop"
                                        }
                                except json.JSONDecodeError:
                                    continue
                    else:
                        data = await response.json()
                        
                        if "message" in data and "content" in data["message"]:
                            yield {
                                "type": "text",
                                "content": data["message"]["content"]
                            }
                        
                        yield {
                            "type": "completion",
                            "reason": "stop"
                        }
        
        except aiohttp.ClientError as e:
            raise ProviderError(f"Ollama connection error: {e}") from e
        except Exception as e:
            raise ProviderError(f"Unexpected error: {e}") from e
    
    async def list_models(self) -> List[ModelInfo]:
        """List available Ollama models."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/api/tags",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status != 200:
                        return []
                    
                    data = await response.json()
                    models = []
                    
                    for model in data.get("models", []):
                        models.append(ModelInfo(
                            id=model["name"],
                            provider=ProviderType.OLLAMA,
                            name=model["name"],
                            context_window=model.get("details", {}).get("parameter_size", "unknown"),
                            supports_tools=False,  # Limited tool support in Ollama
                            supports_streaming=True
                        ))
                    
                    return models
        except Exception:
            # Return default models if can't connect
            return [
                ModelInfo(
                    id="llama3.2",
                    provider=ProviderType.OLLAMA,
                    name="Llama 3.2",
                    context_window=128_000,
                    supports_tools=False,
                    supports_streaming=True
                ),
                ModelInfo(
                    id="codellama",
                    provider=ProviderType.OLLAMA,
                    name="Code Llama",
                    context_window=16_000,
                    supports_tools=False,
                    supports_streaming=True
                ),
            ]
    
    def get_cost_per_token(self, model: str) -> tuple[float, float]:
        """Get cost per million tokens for a model."""
        # Ollama is free (local)
        return (0.0, 0.0)
