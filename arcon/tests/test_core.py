"""Tests for core Arcon types and interfaces."""
import pytest
from pathlib import Path

from arcon.core.types import (
    Message,
    Role,
    ProviderType,
    ToolCall,
    ToolResult,
    ToolDefinition,
    ToolParameter,
    ModelInfo,
    ProviderConfig,
)
from arcon.core.interface import (
    ArconError,
    ProviderError,
    ToolError,
    SessionError,
    ConfigError,
)
from arcon.core.session import Session


class TestTypes:
    """Test core type definitions."""
    
    def test_role_enum(self):
        """Test Role enum values."""
        assert Role.USER == "user"
        assert Role.ASSISTANT == "assistant"
        assert Role.SYSTEM == "system"
    
    def test_provider_type_enum(self):
        """Test ProviderType enum values."""
        assert ProviderType.ANTHROPIC == "anthropic"
        assert ProviderType.OPENAI == "openai"
        assert ProviderType.OLLAMA == "ollama"
    
    def test_message_creation(self):
        """Test Message creation."""
        msg = Message(role=Role.USER, content="Hello")
        assert msg.role == Role.USER
        assert msg.content == "Hello"
        assert msg.tool_calls is None
        assert msg.tool_results is None
    
    def test_message_to_dict(self):
        """Test Message serialization."""
        msg = Message(role=Role.USER, content="Hello")
        data = msg.to_dict()
        
        assert data["role"] == "user"
        assert data["content"] == "Hello"
    
    def test_message_from_dict(self):
        """Test Message deserialization."""
        data = {"role": "user", "content": "Hello"}
        msg = Message.from_dict(data)
        
        assert msg.role == Role.USER
        assert msg.content == "Hello"
    
    def test_tool_call(self):
        """Test ToolCall creation."""
        tc = ToolCall(id="tc_1", name="read_file", arguments={"path": "test.py"})
        assert tc.id == "tc_1"
        assert tc.name == "read_file"
        assert tc.arguments == {"path": "test.py"}
    
    def test_tool_result(self):
        """Test ToolResult creation."""
        tr = ToolResult(tool_call_id="tc_1", output="file contents")
        assert tr.tool_call_id == "tc_1"
        assert tr.output == "file contents"
        assert tr.is_error is False
    
    def test_tool_definition(self):
        """Test ToolDefinition creation and serialization."""
        param = ToolParameter(
            name="path",
            type="string",
            description="File path",
            required=True
        )
        tool = ToolDefinition(
            name="read_file",
            description="Read a file",
            parameters=[param]
        )
        
        data = tool.to_dict()
        assert data["name"] == "read_file"
        assert data["description"] == "Read a file"
        assert "input_schema" in data
        assert "path" in data["input_schema"]["properties"]
    
    def test_provider_config(self):
        """Test ProviderConfig creation."""
        config = ProviderConfig(
            provider_type=ProviderType.ANTHROPIC,
            api_key="test_key",
            model="claude-opus-4-6",
            temperature=0.7
        )
        assert config.provider_type == ProviderType.ANTHROPIC
        assert config.api_key == "test_key"
        assert config.model == "claude-opus-4-6"
        assert config.temperature == 0.7


class TestExceptions:
    """Test exception hierarchy."""
    
    def test_arcon_error(self):
        """Test ArconError base exception."""
        with pytest.raises(ArconError):
            raise ArconError("Test error")
    
    def test_provider_error(self):
        """Test ProviderError."""
        with pytest.raises(ProviderError):
            raise ProviderError("Provider failed")
        
        # Should also be caught by ArconError
        with pytest.raises(ArconError):
            raise ProviderError("Provider failed")
    
    def test_tool_error(self):
        """Test ToolError."""
        with pytest.raises(ToolError):
            raise ToolError("Tool execution failed")
    
    def test_session_error(self):
        """Test SessionError."""
        with pytest.raises(SessionError):
            raise SessionError("Session error")
    
    def test_config_error(self):
        """Test ConfigError."""
        with pytest.raises(ConfigError):
            raise ConfigError("Invalid configuration")


class TestSession:
    """Test Session class."""
    
    def test_session_creation(self):
        """Test Session initialization."""
        session = Session()
        
        assert session.id is not None
        assert len(session.id) > 0
        assert session.working_dir == Path.cwd()
        assert len(session.messages) == 0
        assert session.metadata["status"] == "active"
    
    def test_session_with_id(self):
        """Test Session with custom ID."""
        session = Session(session_id="test-session-123")
        assert session.id == "test-session-123"
    
    def test_add_message(self):
        """Test adding messages to session."""
        session = Session()
        msg = Message(role=Role.USER, content="Hello")
        
        session.add_message(msg)
        
        assert len(session.messages) == 1
        assert session.messages[0] == msg
        assert session.metadata["message_count"] == 1
    
    def test_get_context(self):
        """Test getting conversation context."""
        session = Session()
        
        session.add_message(Message(role=Role.USER, content="Hello"))
        session.add_message(Message(role=Role.ASSISTANT, content="Hi"))
        session.add_message(Message(role=Role.USER, content="How are you?"))
        
        # Get all context
        context = session.get_context()
        assert len(context) == 3
        
        # Get limited context
        context = session.get_context(max_messages=2)
        assert len(context) == 2
        assert context[0].content == "Hi"
        assert context[1].content == "How are you?"
    
    def test_clear_context(self):
        """Test clearing conversation context."""
        session = Session()
        
        session.add_message(Message(role=Role.USER, content="Hello"))
        session.add_message(Message(role=Role.ASSISTANT, content="Hi"))
        
        assert len(session.messages) == 2
        
        session.clear_context()
        
        assert len(session.messages) == 0
        assert session.metadata["message_count"] == 0
    
    def test_session_to_dict(self):
        """Test session serialization."""
        session = Session(session_id="test-123")
        session.add_message(Message(role=Role.USER, content="Hello"))
        
        data = session.to_dict()
        
        assert data["id"] == "test-123"
        assert len(data["messages"]) == 1
        assert data["messages"][0]["content"] == "Hello"
        assert "metadata" in data
        assert "stats" in data
    
    def test_session_from_dict(self):
        """Test session deserialization."""
        data = {
            "id": "test-123",
            "working_dir": "/tmp/test",
            "messages": [
                {"role": "user", "content": "Hello"}
            ],
            "metadata": {
                "status": "active",
                "message_count": 1
            },
            "stats": {
                "total_input_tokens": 10,
                "total_output_tokens": 20,
                "total_cost_usd": 0.001
            }
        }
        
        session = Session.from_dict(data)
        
        assert session.id == "test-123"
        assert session.working_dir == Path("/tmp/test")
        assert len(session.messages) == 1
        assert session.messages[0].content == "Hello"
        assert session.metadata["status"] == "active"
    
    @pytest.mark.asyncio
    async def test_invoke_without_provider(self):
        """Test invoking session without provider raises error."""
        session = Session()
        
        with pytest.raises(SessionError, match="No provider configured"):
            async for _ in session.invoke("Hello"):
                pass
