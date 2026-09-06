"""Tests for agent system."""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from arcon.agents import (
    Agent,
    AgentMetadata,
    AgentLoader,
    YAMLAgent,
    AgentRegistry,
    get_global_registry,
)
from arcon.core.interface import ConfigError, LLMProvider
from arcon.core.types import Message, Role, ProviderConfig, ProviderType
from arcon.tools import ToolRegistry


class MockAgent(Agent):
    """Mock agent for testing."""
    
    def _create_metadata(self) -> AgentMetadata:
        return AgentMetadata(
            name="mock-agent",
            description="A mock agent for testing",
            agent_type="test",
            specialization=["testing", "mock"],
            tags=["test", "mock"],
        )
    
    def _create_instructions(self) -> str:
        return "You are a mock agent for testing purposes."
    
    def _create_allowed_tools(self) -> list[str]:
        return ["read_file", "write_file"]


class MockProvider(LLMProvider):
    """Mock provider for testing."""
    
    def __init__(self):
        config = ProviderConfig(
            provider_type=ProviderType.ANTHROPIC,
            api_key="test-key",
            model="test-model",
        )
        super().__init__(config)
    
    def _validate_config(self) -> None:
        pass
    
    async def create_message(self, **kwargs):
        yield {"type": "text", "content": "Mock response"}
    
    def list_models(self):
        return []
    
    def get_cost_per_token(self, model: str):
        return (0.0, 0.0)
    
    @property
    def provider_type(self):
        return ProviderType.ANTHROPIC


class TestAgentMetadata:
    """Test AgentMetadata class."""
    
    def test_metadata_creation(self):
        """Test creating agent metadata."""
        metadata = AgentMetadata(
            name="test-agent",
            description="Test description",
            agent_type="test",
            specialization=["python"],
            tags=["test"],
        )
        
        assert metadata.name == "test-agent"
        assert metadata.description == "Test description"
        assert metadata.agent_type == "test"
        assert "python" in metadata.specialization
    
    def test_metadata_to_dict(self):
        """Test converting metadata to dict."""
        metadata = AgentMetadata(
            name="test-agent",
            description="Test description",
            agent_type="test",
        )
        
        data = metadata.to_dict()
        assert data["name"] == "test-agent"
        assert data["description"] == "Test description"
        assert data["agent_type"] == "test"


class TestAgentBase:
    """Test Agent base class."""
    
    def test_agent_creation(self):
        """Test creating an agent."""
        agent = MockAgent()
        
        assert agent.name == "mock-agent"
        assert agent.description == "A mock agent for testing"
        assert agent.agent_type == "test"
        assert "testing" in agent.specialization
    
    def test_agent_properties(self):
        """Test agent properties."""
        agent = MockAgent(temperature=0.5, max_tokens=2000)
        
        assert agent.temperature == 0.5
        assert agent.max_tokens == 2000
        assert agent.instructions == "You are a mock agent for testing purposes."
        assert agent.allowed_tools == ["read_file", "write_file"]
    
    def test_set_provider(self):
        """Test setting provider."""
        agent = MockAgent()
        provider = MockProvider()
        
        assert agent.provider is None
        agent.set_provider(provider)
        assert agent.provider is provider
    
    def test_get_available_tools_no_registry(self):
        """Test getting tools with no registry."""
        agent = MockAgent()
        tools = agent.get_available_tools()
        
        assert tools == []
    
    def test_get_available_tools_with_registry(self):
        """Test getting tools with registry."""
        from arcon.tools import get_global_registry as get_tool_registry
        
        agent = MockAgent(tool_registry=get_tool_registry())
        tools = agent.get_available_tools()
        
        # Should have filtered tools (only read_file and write_file)
        assert len(tools) >= 2
        tool_names = [t["name"] for t in tools]
        assert "read_file" in tool_names
        assert "write_file" in tool_names
        assert "bash_execute" not in tool_names  # Not in allowed_tools
    
    @pytest.mark.asyncio
    async def test_invoke_without_provider(self):
        """Test invoking without provider raises error."""
        agent = MockAgent()
        
        with pytest.raises(ValueError, match="Provider must be set"):
            async for _ in agent.invoke("test query"):
                pass
    
    @pytest.mark.asyncio
    async def test_invoke_with_provider(self):
        """Test invoking agent with provider."""
        agent = MockAgent()
        provider = MockProvider()
        agent.set_provider(provider)
        
        chunks = []
        async for chunk in agent.invoke("test query"):
            chunks.append(chunk)
        
        assert len(chunks) == 1
        assert chunks[0]["content"] == "Mock response"
    
    @pytest.mark.asyncio
    async def test_invoke_with_context(self):
        """Test invoking with conversation context."""
        agent = MockAgent()
        provider = MockProvider()
        agent.set_provider(provider)
        
        context = [
            Message(role=Role.USER, content="Previous message"),
            Message(role=Role.ASSISTANT, content="Previous response"),
        ]
        
        chunks = []
        async for chunk in agent.invoke("test query", context=context):
            chunks.append(chunk)
        
        assert len(chunks) > 0
    
    def test_agent_to_dict(self):
        """Test converting agent to dict."""
        agent = MockAgent()
        data = agent.to_dict()
        
        assert "metadata" in data
        assert "instructions" in data
        assert "allowed_tools" in data
        assert data["temperature"] == 0.7
        assert data["max_tokens"] == 4000


class TestYAMLAgent:
    """Test YAMLAgent class."""
    
    def test_yaml_agent_creation(self):
        """Test creating agent from YAML config."""
        config = {
            "name": "yaml-test-agent",
            "description": "Test agent from YAML",
            "type": "test",
            "instructions": "Test instructions",
            "specialization": ["python"],
            "tools": ["read_file"],
            "temperature": 0.5,
        }
        
        agent = YAMLAgent(config)
        
        assert agent.name == "yaml-test-agent"
        assert agent.description == "Test agent from YAML"
        assert agent.agent_type == "test"
        assert agent.temperature == 0.5
        assert agent.allowed_tools == ["read_file"]
    
    def test_yaml_agent_missing_fields(self):
        """Test YAML agent with missing required fields."""
        config = {
            "name": "incomplete-agent",
            # Missing description, type, instructions
        }
        
        with pytest.raises(ConfigError, match="missing required fields"):
            YAMLAgent(config)
    
    def test_yaml_agent_defaults(self):
        """Test YAML agent with default values."""
        config = {
            "name": "minimal-agent",
            "description": "Minimal config",
            "type": "test",
            "instructions": "Test",
        }
        
        agent = YAMLAgent(config)
        
        assert agent.temperature == 0.7  # Default
        assert agent.max_tokens == 4000  # Default
        assert agent.allowed_tools == []  # Default (all tools)


class TestAgentLoader:
    """Test AgentLoader class."""
    
    def test_load_agent_success(self):
        """Test loading agent from YAML file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agents_dir = Path(tmpdir) / "agents"
            agents_dir.mkdir()
            
            agent_file = agents_dir / "test-agent.yaml"
            agent_file.write_text("""name: "test-agent"
description: "Test agent"
type: "test"
instructions: "Test instructions"
specialization: ["python"]
tools: ["read_file"]
""")
            
            loader = AgentLoader(agents_dir)
            agent = loader.load_agent(agent_file)
            
            assert agent.name == "test-agent"
            assert agent.description == "Test agent"
    
    def test_load_agent_file_not_found(self):
        """Test loading non-existent file."""
        loader = AgentLoader()
        
        with pytest.raises(ConfigError, match="not found"):
            loader.load_agent(Path("/nonexistent/agent.yaml"))
    
    def test_load_agent_invalid_yaml(self):
        """Test loading invalid YAML."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agents_dir = Path(tmpdir)
            agent_file = agents_dir / "bad.yaml"
            agent_file.write_text("invalid: yaml: content:")
            
            loader = AgentLoader(agents_dir)
            
            with pytest.raises(ConfigError, match="Invalid YAML"):
                loader.load_agent(agent_file)
    
    def test_load_all_agents(self):
        """Test loading all agents from directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agents_dir = Path(tmpdir) / "agents"
            agents_dir.mkdir()
            
            # Create two valid agents
            for i in range(2):
                agent_file = agents_dir / f"agent{i}.yaml"
                agent_file.write_text(f"""name: "agent-{i}"
description: "Agent {i}"
type: "test"
instructions: "Test"
""")
            
            loader = AgentLoader(agents_dir)
            agents = loader.load_all_agents()
            
            assert len(agents) == 2
            names = [a.name for a in agents]
            assert "agent-0" in names
            assert "agent-1" in names
    
    def test_get_agent_names(self):
        """Test getting agent names."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agents_dir = Path(tmpdir) / "agents"
            agents_dir.mkdir()
            
            (agents_dir / "agent1.yaml").write_text("test")
            (agents_dir / "agent2.yml").write_text("test")
            
            loader = AgentLoader(agents_dir)
            names = loader.get_agent_names()
            
            assert "agent1" in names
            assert "agent2" in names


class TestAgentRegistry:
    """Test AgentRegistry class."""
    
    def test_register_agent(self):
        """Test registering an agent."""
        registry = AgentRegistry()
        agent = MockAgent()
        
        registry.register(agent)
        assert registry.has("mock-agent")
        assert registry.count() == 1
    
    def test_register_duplicate(self):
        """Test registering duplicate agent."""
        registry = AgentRegistry()
        agent1 = MockAgent()
        agent2 = MockAgent()
        
        registry.register(agent1)
        
        with pytest.raises(ConfigError, match="already registered"):
            registry.register(agent2)
    
    def test_get_agent(self):
        """Test getting agent by name."""
        registry = AgentRegistry()
        agent = MockAgent()
        registry.register(agent)
        
        retrieved = registry.get("mock-agent")
        assert retrieved.name == "mock-agent"
    
    def test_get_nonexistent(self):
        """Test getting non-existent agent."""
        registry = AgentRegistry()
        
        with pytest.raises(ConfigError, match="not found"):
            registry.get("nonexistent")
    
    def test_list_operations(self):
        """Test list operations."""
        registry = AgentRegistry()
        agent = MockAgent()
        registry.register(agent)
        
        assert len(registry.list_all()) == 1
        assert "mock-agent" in registry.list_names()
    
    def test_get_by_type(self):
        """Test filtering by type."""
        registry = AgentRegistry()
        agent = MockAgent()
        registry.register(agent)
        
        test_agents = registry.get_by_type("test")
        assert len(test_agents) == 1
        assert test_agents[0].name == "mock-agent"
    
    def test_get_by_specialization(self):
        """Test filtering by specialization."""
        registry = AgentRegistry()
        agent = MockAgent()
        registry.register(agent)
        
        testing_agents = registry.get_by_specialization("testing")
        assert len(testing_agents) == 1
    
    def test_get_by_tag(self):
        """Test filtering by tag."""
        registry = AgentRegistry()
        agent = MockAgent()
        registry.register(agent)
        
        test_tag_agents = registry.get_by_tag("test")
        assert len(test_tag_agents) == 1
    
    def test_route_query_by_name(self):
        """Test routing by agent name mention."""
        registry = AgentRegistry()
        agent = MockAgent()
        registry.register(agent)
        
        routed = registry.route_query("use mock-agent for this")
        assert routed is not None
        assert routed.name == "mock-agent"
    
    def test_route_query_by_context(self):
        """Test routing by context hints."""
        registry = AgentRegistry()
        agent = MockAgent()
        registry.register(agent)
        
        context = {"file_extension": ".test", "language": "testing"}
        routed = registry.route_query("help with this", context=context)
        assert routed is not None
    
    def test_route_query_no_match(self):
        """Test routing with no match."""
        registry = AgentRegistry()
        
        routed = registry.route_query("random query")
        assert routed is None
    
    def test_clear_registry(self):
        """Test clearing registry."""
        registry = AgentRegistry()
        agent = MockAgent()
        registry.register(agent)
        
        assert registry.count() == 1
        registry.clear()
        assert registry.count() == 0


class TestGlobalRegistry:
    """Test global agent registry."""
    
    def test_global_registry_singleton(self):
        """Test global registry is singleton."""
        registry1 = get_global_registry()
        registry2 = get_global_registry()
        
        assert registry1 is registry2
