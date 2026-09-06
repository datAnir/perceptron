"""Abstract base class for agents."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import AsyncGenerator, Optional

from ..core.types import Message, Role
from ..core.interface import LLMProvider
from ..tools.registry import ToolRegistry


@dataclass
class AgentMetadata:
    """Metadata for an agent."""
    
    name: str
    description: str
    agent_type: str  # e.g., "code-review", "build-resolver", "orchestrator"
    specialization: list[str] = field(default_factory=list)  # e.g., ["python", "django"]
    version: str = "1.0.0"
    author: str = "arcon"
    tags: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        """Convert metadata to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "agent_type": self.agent_type,
            "specialization": self.specialization,
            "version": self.version,
            "author": self.author,
            "tags": self.tags,
        }


class Agent(ABC):
    """Abstract base class for all agents.
    
    An agent is a specialized LLM persona with:
    - Specific instructions and expertise
    - Access to specific tools
    - Custom temperature and behavior
    - Ability to invoke the LLM with context
    """
    
    def __init__(
        self,
        provider: Optional[LLMProvider] = None,
        tool_registry: Optional[ToolRegistry] = None,
        temperature: float = 0.7,
        max_tokens: int = 4000,
    ):
        """Initialize agent.
        
        Args:
            provider: LLM provider to use (can be set later)
            tool_registry: Tool registry for available tools
            temperature: LLM temperature (0.0-1.0)
            max_tokens: Maximum tokens in response
        """
        self.provider = provider
        self.tool_registry = tool_registry
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._metadata = self._create_metadata()
        self._instructions = self._create_instructions()
        self._allowed_tools = self._create_allowed_tools()
    
    @abstractmethod
    def _create_metadata(self) -> AgentMetadata:
        """Create agent metadata.
        
        Must be implemented by subclasses to define agent identity.
        
        Returns:
            AgentMetadata with name, description, type, specialization
        """
        pass
    
    @abstractmethod
    def _create_instructions(self) -> str:
        """Create agent instructions.
        
        Must be implemented by subclasses to define agent behavior.
        
        Returns:
            String containing detailed instructions for the agent
        """
        pass
    
    def _create_allowed_tools(self) -> list[str]:
        """Define allowed tools for this agent.
        
        Override to restrict tools. Default allows all.
        
        Returns:
            List of tool names this agent can use
        """
        return []  # Empty list means all tools allowed
    
    @property
    def name(self) -> str:
        """Get agent name."""
        return self._metadata.name
    
    @property
    def description(self) -> str:
        """Get agent description."""
        return self._metadata.description
    
    @property
    def agent_type(self) -> str:
        """Get agent type."""
        return self._metadata.agent_type
    
    @property
    def specialization(self) -> list[str]:
        """Get agent specialization areas."""
        return self._metadata.specialization
    
    @property
    def metadata(self) -> AgentMetadata:
        """Get full agent metadata."""
        return self._metadata
    
    @property
    def instructions(self) -> str:
        """Get agent instructions."""
        return self._instructions
    
    @property
    def allowed_tools(self) -> list[str]:
        """Get allowed tool names."""
        return self._allowed_tools
    
    def set_provider(self, provider: LLMProvider) -> None:
        """Set the LLM provider.
        
        Args:
            provider: LLM provider instance
        """
        self.provider = provider
    
    def get_available_tools(self) -> list[dict]:
        """Get available tools for this agent.
        
        Returns:
            List of tool definitions in LLM format
        """
        if not self.tool_registry:
            return []
        
        tools = self.tool_registry.list_all()
        
        # Filter by allowed tools if specified
        if self._allowed_tools:
            tools = [t for t in tools if t.name in self._allowed_tools]
        
        return [t.to_dict() for t in tools]
    
    async def invoke(
        self,
        query: str,
        context: Optional[list[Message]] = None,
        skills: Optional[list[str]] = None,
        stream: bool = True,
    ) -> AsyncGenerator[dict, None]:
        """Invoke the agent with a query.
        
        Args:
            query: User query to process
            context: Previous conversation messages
            skills: Optional skill content to inject
            stream: Whether to stream the response
        
        Yields:
            Response chunks as dictionaries
        
        Raises:
            ValueError: If provider not set
        """
        if not self.provider:
            raise ValueError("Provider must be set before invoking agent")
        
        # Build system prompt with instructions and skills
        system_prompt = self._build_system_prompt(skills)
        
        # Build message history
        messages = []
        if context:
            messages.extend(context)
        
        # Add user query
        messages.append(Message(
            role=Role.USER,
            content=query
        ))
        
        # Get available tools
        tools = self.get_available_tools()
        
        # Invoke provider
        async for chunk in self.provider.create_message(
            messages=messages,
            system_prompt=system_prompt,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            tools=tools if tools else None,
            stream=stream,
        ):
            yield chunk
    
    def _build_system_prompt(self, skills: Optional[list[str]] = None) -> str:
        """Build system prompt with instructions and skills.
        
        Args:
            skills: Optional skill content to inject
        
        Returns:
            Complete system prompt
        """
        prompt_parts = [self._instructions]
        
        if skills:
            prompt_parts.append("\n\n## Available Skills\n")
            prompt_parts.extend(skills)
        
        return "\n".join(prompt_parts)
    
    def to_dict(self) -> dict:
        """Convert agent to dictionary.
        
        Returns:
            Dictionary with agent configuration
        """
        return {
            "metadata": self._metadata.to_dict(),
            "instructions": self._instructions,
            "allowed_tools": self._allowed_tools,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
