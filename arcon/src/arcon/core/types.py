"""Core type definitions for Arcon."""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union


class Role(str, Enum):
    """Message role types."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ProviderType(str, Enum):
    """Supported LLM provider types."""
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    OLLAMA = "ollama"


@dataclass
class ToolCall:
    """Represents a tool call from the LLM."""
    id: str
    name: str
    arguments: Dict[str, Any]


@dataclass
class ToolResult:
    """Represents the result of a tool execution."""
    tool_call_id: str
    output: str
    is_error: bool = False


@dataclass
class Message:
    """Represents a message in a conversation."""
    role: Role
    content: str
    tool_calls: Optional[List[ToolCall]] = None
    tool_results: Optional[List[ToolResult]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary format."""
        result: Dict[str, Any] = {
            "role": self.role.value,
            "content": self.content,
        }
        
        if self.tool_calls:
            result["tool_calls"] = [
                {
                    "id": tc.id,
                    "name": tc.name,
                    "arguments": tc.arguments
                }
                for tc in self.tool_calls
            ]
        
        if self.tool_results:
            result["tool_results"] = [
                {
                    "tool_call_id": tr.tool_call_id,
                    "output": tr.output,
                    "is_error": tr.is_error
                }
                for tr in self.tool_results
            ]
        
        if self.metadata:
            result["metadata"] = self.metadata
        
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        """Create message from dictionary format."""
        tool_calls = None
        if "tool_calls" in data:
            tool_calls = [
                ToolCall(
                    id=tc["id"],
                    name=tc["name"],
                    arguments=tc["arguments"]
                )
                for tc in data["tool_calls"]
            ]
        
        tool_results = None
        if "tool_results" in data:
            tool_results = [
                ToolResult(
                    tool_call_id=tr["tool_call_id"],
                    output=tr["output"],
                    is_error=tr.get("is_error", False)
                )
                for tr in data["tool_results"]
            ]
        
        return cls(
            role=Role(data["role"]),
            content=data["content"],
            tool_calls=tool_calls,
            tool_results=tool_results,
            metadata=data.get("metadata", {})
        )


@dataclass
class ToolParameter:
    """Represents a parameter for a tool."""
    name: str
    type: str
    description: str
    required: bool = True
    default: Optional[Any] = None


@dataclass
class ToolDefinition:
    """Defines a tool that can be used by the LLM."""
    name: str
    description: str
    parameters: List[ToolParameter]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for API calls."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": {
                    param.name: {
                        "type": param.type,
                        "description": param.description
                    }
                    for param in self.parameters
                },
                "required": [
                    param.name for param in self.parameters if param.required
                ]
            }
        }


@dataclass
class ModelInfo:
    """Information about an available model."""
    id: str
    provider: ProviderType
    name: str
    context_window: int
    supports_tools: bool = True
    supports_streaming: bool = True


@dataclass
class ProviderConfig:
    """Configuration for an LLM provider."""
    provider_type: ProviderType
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model: Optional[str] = None
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    timeout: int = 60
