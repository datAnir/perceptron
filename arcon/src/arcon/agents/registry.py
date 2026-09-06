"""Agent registry for managing and routing agents."""

from typing import Optional

from .base import Agent
from ..core.interface import ConfigError


class AgentRegistry:
    """Registry for managing available agents."""
    
    def __init__(self):
        """Initialize empty agent registry."""
        self._agents: dict[str, Agent] = {}
    
    def register(self, agent: Agent) -> None:
        """Register an agent.
        
        Args:
            agent: Agent instance to register
        
        Raises:
            ConfigError: If agent name already registered
        """
        if agent.name in self._agents:
            raise ConfigError(
                f"Agent '{agent.name}' is already registered"
            )
        
        self._agents[agent.name] = agent
    
    def unregister(self, name: str) -> None:
        """Unregister an agent by name.
        
        Args:
            name: Name of agent to remove
        """
        self._agents.pop(name, None)
    
    def get(self, name: str) -> Agent:
        """Get agent by name.
        
        Args:
            name: Agent name
        
        Returns:
            Agent instance
        
        Raises:
            ConfigError: If agent not found
        """
        if name not in self._agents:
            raise ConfigError(f"Agent '{name}' not found in registry")
        
        return self._agents[name]
    
    def has(self, name: str) -> bool:
        """Check if agent is registered.
        
        Args:
            name: Agent name
        
        Returns:
            True if agent exists, False otherwise
        """
        return name in self._agents
    
    def list_all(self) -> list[Agent]:
        """List all registered agents.
        
        Returns:
            List of all agent instances
        """
        return list(self._agents.values())
    
    def list_names(self) -> list[str]:
        """List all agent names.
        
        Returns:
            Sorted list of agent names
        """
        return sorted(self._agents.keys())
    
    def get_by_type(self, agent_type: str) -> list[Agent]:
        """Get agents by type.
        
        Args:
            agent_type: Agent type to filter by
        
        Returns:
            List of agents matching the type
        """
        return [
            agent for agent in self._agents.values()
            if agent.agent_type == agent_type
        ]
    
    def get_by_specialization(self, specialization: str) -> list[Agent]:
        """Get agents by specialization.
        
        Args:
            specialization: Specialization to filter by (e.g., "python", "django")
        
        Returns:
            List of agents with matching specialization
        """
        return [
            agent for agent in self._agents.values()
            if specialization.lower() in [s.lower() for s in agent.specialization]
        ]
    
    def get_by_tag(self, tag: str) -> list[Agent]:
        """Get agents by tag.
        
        Args:
            tag: Tag to filter by
        
        Returns:
            List of agents with matching tag
        """
        return [
            agent for agent in self._agents.values()
            if tag.lower() in [t.lower() for t in agent.metadata.tags]
        ]
    
    def route_query(self, query: str, context: Optional[dict] = None) -> Optional[Agent]:
        """Route query to best matching agent.
        
        Simple keyword-based routing. Can be enhanced with ML in Phase 2.
        
        Args:
            query: User query
            context: Optional context with hints (e.g., file extension, language)
        
        Returns:
            Best matching agent, or None if no match
        """
        query_lower = query.lower()
        
        # Priority 1: Explicit agent mention
        for name in self._agents.keys():
            name_lower = name.lower()
            if name_lower in query_lower or name_lower.replace("-", " ") in query_lower:
                return self._agents[name]
        
        # Priority 2: Context hints (e.g., file extension)
        if context:
            file_ext = context.get("file_extension", "").lower()
            language = context.get("language", "").lower()
            
            # Map file extensions to specializations
            ext_map = {
                ".py": "python",
                ".ts": "typescript",
                ".js": "javascript",
                ".java": "java",
                ".rs": "rust",
                ".go": "go",
                ".rb": "ruby",
            }
            
            specialization = ext_map.get(file_ext) or language
            if specialization:
                matches = self.get_by_specialization(specialization)
                if matches:
                    # Prefer code-review agents
                    reviewers = [a for a in matches if "review" in a.agent_type]
                    return reviewers[0] if reviewers else matches[0]
        
        # Priority 3: Keyword matching in query
        keyword_map = {
            "review": "review",
            "debug": "debugging",
            "bug": "debugging",
            "error": "debugging",
            "troubleshoot": "debugging",
            "test": "testing",
            "unittest": "testing",
            "pytest": "testing",
            "code": "general",
            "help": "general",
            "write": "general",
            "create": "general",
            "build": "general",
        }
        
        for keyword, agent_type in keyword_map.items():
            if keyword in query_lower:
                matches = self.get_by_type(agent_type)
                if matches:
                    return matches[0]
        
        # Fallback: Return general coding assistant if available
        for agent in self._agents.values():
            if "coding" in agent.name.lower() or "assistant" in agent.name.lower():
                return agent
        
        # Last resort: Return any agent
        if self._agents:
            return list(self._agents.values())[0]
        
        # No agents registered
        return None
    
    def clear(self) -> None:
        """Clear all registered agents."""
        self._agents.clear()
    
    def count(self) -> int:
        """Get number of registered agents.
        
        Returns:
            Number of agents
        """
        return len(self._agents)
    
    def to_dict(self) -> dict:
        """Convert registry to dictionary.
        
        Returns:
            Dictionary mapping names to agent configs
        """
        return {
            name: agent.to_dict()
            for name, agent in self._agents.items()
        }


# Global registry instance
_global_registry: Optional[AgentRegistry] = None


def get_global_registry() -> AgentRegistry:
    """Get or create global agent registry.
    
    Returns:
        Global AgentRegistry instance
    """
    global _global_registry
    
    if _global_registry is None:
        _global_registry = AgentRegistry()
    
    return _global_registry
