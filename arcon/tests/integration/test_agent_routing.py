"""Agent routing integration tests."""
import pytest
from pathlib import Path

from arcon.agents import AgentRegistry, AgentLoader
from arcon.agents.base import Agent, AgentMetadata


class MockAgent(Agent):
    """Mock agent for testing."""
    
    def __init__(self, name: str, agent_type: str, keywords: list[str]):
        self._name = name
        self._type = agent_type
        self._keywords = keywords
        super().__init__(provider=None, tool_registry=None)
    
    def _create_metadata(self) -> AgentMetadata:
        return AgentMetadata(
            name=self._name,
            description=f"Test agent for {self._name}",
            agent_type=self._type,
            tags=self._keywords,
        )
    
    def _create_instructions(self) -> str:
        return f"Instructions for {self._name}"
    
    def _create_allowed_tools(self) -> list[str]:
        return []


@pytest.fixture
def agent_registry():
    """Create agent registry with test agents."""
    registry = AgentRegistry()
    
    # Register test agents
    registry.register(MockAgent(
        "CodingAssistant",
        "coding",
        ["code", "develop", "implement", "program"]
    ))
    registry.register(MockAgent(
        "Debugger",
        "debugging",
        ["debug", "fix", "bug", "error", "issue"]
    ))
    registry.register(MockAgent(
        "CodeReviewer",
        "review",
        ["review", "quality", "check", "audit"]
    ))
    registry.register(MockAgent(
        "TestEngineer",
        "testing",
        ["test", "tdd", "unittest", "coverage"]
    ))
    
    return registry


def test_route_by_explicit_name(agent_registry):
    """Test routing by explicit agent name."""
    agent = agent_registry.route_query("I want to use CodingAssistant")
    assert agent is not None
    assert agent.metadata.name == "CodingAssistant"


def test_route_by_keywords(agent_registry):
    """Test routing by keyword matching."""
    # Debug-related query
    agent = agent_registry.route_query("Help me debug this error")
    assert agent is not None
    assert agent.metadata.name == "Debugger"
    
    # Test-related query
    agent = agent_registry.route_query("Write unit tests for this function")
    assert agent is not None
    assert agent.metadata.name == "TestEngineer"
    
    # Review-related query
    agent = agent_registry.route_query("Can you review my code?")
    assert agent is not None
    assert agent.metadata.name == "CodeReviewer"


def test_route_by_type(agent_registry):
    """Test routing by agent type."""
    agents = agent_registry.get_by_type("debugging")
    assert len(agents) == 1
    assert agents[0].metadata.name == "Debugger"


def test_route_ambiguous_query(agent_registry):
    """Test routing with ambiguous query."""
    # Generic query that could match multiple agents
    agent = agent_registry.route_query("Help me with my code")
    # Should return some agent (fallback logic)
    assert agent is not None


def test_no_matching_agent(agent_registry):
    """Test when no agent matches."""
    # Query with no matching keywords
    agent = agent_registry.route_query("Tell me a joke")
    # Should return None or default agent
    assert agent is None or agent.metadata.name == "CodingAssistant"


def test_list_all_agents(agent_registry):
    """Test listing all agents."""
    agents = agent_registry.list_all()
    assert len(agents) == 4
    
    names = {a.metadata.name for a in agents}
    assert names == {"CodingAssistant", "Debugger", "CodeReviewer", "TestEngineer"}


@pytest.mark.asyncio
async def test_load_agents_from_yaml():
    """Test loading agents from YAML files."""
    agents_dir = Path("agents")
    if not agents_dir.exists():
        pytest.skip("Agents directory not found")
    
    loader = AgentLoader()
    registry = AgentRegistry()
    
    # Load all agent files
    loaded_count = 0
    for agent_file in agents_dir.glob("*.yaml"):
        try:
            agent = loader.load_agent(agent_file)
            registry.register(agent)
            loaded_count += 1
        except Exception as e:
            pytest.fail(f"Failed to load {agent_file}: {e}")
    
    assert loaded_count > 0
    assert len(registry.list_all()) == loaded_count


def test_agent_metadata_validation(agent_registry):
    """Test agent metadata is properly set."""
    agent = agent_registry.get("CodingAssistant")
    assert agent is not None
    
    metadata = agent.metadata
    assert metadata.name == "CodingAssistant"
    assert metadata.agent_type == "coding"
    assert len(metadata.tags) > 0
    assert "code" in metadata.tags


def test_agent_instructions(agent_registry):
    """Test agent instructions are accessible."""
    agent = agent_registry.get("Debugger")
    assert agent is not None
    
    instructions = agent.instructions
    assert isinstance(instructions, str)
    assert len(instructions) > 0
    assert "Debugger" in instructions
