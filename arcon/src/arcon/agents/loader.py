"""Agent loader for loading agent definitions from YAML files."""

from pathlib import Path
from typing import Optional

import yaml

from .base import Agent, AgentMetadata
from ..core.interface import LLMProvider, ConfigError
from ..tools.registry import ToolRegistry


class YAMLAgent(Agent):
    """Agent loaded from YAML configuration."""
    
    def __init__(
        self,
        config: dict,
        provider: Optional[LLMProvider] = None,
        tool_registry: Optional[ToolRegistry] = None,
    ):
        """Initialize agent from YAML config.
        
        Args:
            config: Parsed YAML configuration
            provider: LLM provider to use
            tool_registry: Tool registry for available tools
        
        Raises:
            ConfigError: If config is invalid
        """
        self._config = config
        self._validate_config()
        
        # Extract temperature and max_tokens from config
        temperature = config.get("temperature", 0.7)
        max_tokens = config.get("max_tokens", 4000)
        
        super().__init__(
            provider=provider,
            tool_registry=tool_registry,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    
    def _validate_config(self) -> None:
        """Validate YAML configuration.
        
        Raises:
            ConfigError: If required fields are missing
        """
        required_fields = ["name", "description", "type", "instructions"]
        missing = [f for f in required_fields if f not in self._config]
        
        if missing:
            raise ConfigError(
                f"Agent config missing required fields: {', '.join(missing)}"
            )
    
    def _create_metadata(self) -> AgentMetadata:
        """Create agent metadata from config."""
        return AgentMetadata(
            name=self._config["name"],
            description=self._config["description"],
            agent_type=self._config["type"],
            specialization=self._config.get("specialization", []),
            version=self._config.get("version", "1.0.0"),
            author=self._config.get("author", "arcon"),
            tags=self._config.get("tags", []),
        )
    
    def _create_instructions(self) -> str:
        """Create agent instructions from config."""
        return self._config["instructions"]
    
    def _create_allowed_tools(self) -> list[str]:
        """Define allowed tools from config."""
        return self._config.get("tools", [])


class AgentLoader:
    """Loader for agent definitions from YAML files."""
    
    def __init__(self, agents_dir: Optional[Path] = None):
        """Initialize agent loader.
        
        Args:
            agents_dir: Directory containing agent YAML files
        """
        self.agents_dir = agents_dir or Path("agents")
    
    def load_agent(
        self,
        agent_file: Path,
        provider: Optional[LLMProvider] = None,
        tool_registry: Optional[ToolRegistry] = None,
    ) -> YAMLAgent:
        """Load a single agent from YAML file.
        
        Args:
            agent_file: Path to agent YAML file
            provider: LLM provider to use
            tool_registry: Tool registry for available tools
        
        Returns:
            Loaded YAMLAgent instance
        
        Raises:
            ConfigError: If file not found or invalid YAML
        """
        if not agent_file.exists():
            raise ConfigError(f"Agent file not found: {agent_file}")
        
        try:
            with open(agent_file, "r") as f:
                config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ConfigError(f"Invalid YAML in {agent_file}: {e}")
        
        if not isinstance(config, dict):
            raise ConfigError(f"Agent file must contain a YAML dictionary: {agent_file}")
        
        return YAMLAgent(config, provider=provider, tool_registry=tool_registry)
    
    def load_all_agents(
        self,
        provider: Optional[LLMProvider] = None,
        tool_registry: Optional[ToolRegistry] = None,
    ) -> list[YAMLAgent]:
        """Load all agents from agents directory.
        
        Args:
            provider: LLM provider to use
            tool_registry: Tool registry for available tools
        
        Returns:
            List of loaded YAMLAgent instances
        """
        if not self.agents_dir.exists():
            return []
        
        agents = []
        for yaml_file in self.agents_dir.glob("*.yaml"):
            try:
                agent = self.load_agent(yaml_file, provider, tool_registry)
                agents.append(agent)
            except ConfigError:
                # Skip invalid agent files
                continue
        
        # Also check for .yml extension
        for yml_file in self.agents_dir.glob("*.yml"):
            try:
                agent = self.load_agent(yml_file, provider, tool_registry)
                agents.append(agent)
            except ConfigError:
                continue
        
        return agents
    
    def get_agent_names(self) -> list[str]:
        """Get names of all available agents.
        
        Returns:
            List of agent names (without .yaml extension)
        """
        if not self.agents_dir.exists():
            return []
        
        names = []
        for yaml_file in self.agents_dir.glob("*.yaml"):
            names.append(yaml_file.stem)
        for yml_file in self.agents_dir.glob("*.yml"):
            names.append(yml_file.stem)
        
        return sorted(set(names))
