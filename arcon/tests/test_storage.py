"""Tests for storage layer."""
import tempfile
from pathlib import Path
import pytest

from arcon.storage import StorageManager, SessionRecord, MessageRecord, ToolCallRecord
from arcon.core.types import ProviderType, Role


@pytest.fixture
def storage():
    """Create temporary storage manager for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        manager = StorageManager(str(db_path))
        yield manager
        # Cleanup is automatic with tempfile


class TestStorageManager:
    """Test storage manager initialization."""
    
    def test_create_storage_manager(self, storage):
        """Test storage manager creation."""
        assert storage is not None
        assert storage.database_path.exists()
    
    def test_database_tables_created(self, storage):
        """Test that database tables are created."""
        # Try to query each table
        db = storage._get_db()
        try:
            assert db.query(SessionRecord).count() == 0
            assert db.query(MessageRecord).count() == 0
            assert db.query(ToolCallRecord).count() == 0
        finally:
            db.close()


class TestSessionOperations:
    """Test session CRUD operations."""
    
    def test_create_session(self, storage):
        """Test creating a session."""
        session = storage.create_session(
            session_id="test-session-1",
            provider_type=ProviderType.ANTHROPIC,
            model="claude-3-5-sonnet-20241022",
            temperature=0.7,
            max_tokens=2048,
            working_dir="/tmp/test",
            extra_data={"test": "data"}
        )
        
        assert session.id == "test-session-1"
        assert session.provider_type == "anthropic"
        assert session.model == "claude-3-5-sonnet-20241022"
        assert session.temperature == 0.7
        assert session.max_tokens == 2048
        assert session.working_dir == "/tmp/test"
        assert session.extra_data == {"test": "data"}
        assert session.total_input_tokens == 0
        assert session.total_output_tokens == 0
        assert session.total_cost == 0.0
        assert session.created_at is not None
        assert session.updated_at is not None
    
    def test_get_session(self, storage):
        """Test retrieving a session."""
        # Create session
        storage.create_session(
            session_id="test-session-2",
            provider_type=ProviderType.OPENAI,
            model="gpt-4"
        )
        
        # Retrieve session
        session = storage.get_session("test-session-2")
        
        assert session is not None
        assert session.id == "test-session-2"
        assert session.provider_type == "openai"
        assert session.model == "gpt-4"
    
    def test_get_nonexistent_session(self, storage):
        """Test retrieving a nonexistent session."""
        session = storage.get_session("nonexistent")
        assert session is None
    
    def test_update_session_tokens(self, storage):
        """Test updating session token counts."""
        # Create session
        storage.create_session(
            session_id="test-session-3",
            provider_type=ProviderType.ANTHROPIC,
            model="claude-3-haiku-20240307"
        )
        
        # Update tokens
        result = storage.update_session_tokens(
            session_id="test-session-3",
            input_tokens=100,
            output_tokens=200,
            cost=0.05
        )
        
        assert result is True
        
        # Verify update
        session = storage.get_session("test-session-3")
        assert session.total_input_tokens == 100
        assert session.total_output_tokens == 200
        assert session.total_cost == 0.05
        
        # Update again (should accumulate)
        storage.update_session_tokens(
            session_id="test-session-3",
            input_tokens=50,
            output_tokens=100,
            cost=0.025
        )
        
        session = storage.get_session("test-session-3")
        assert session.total_input_tokens == 150
        assert session.total_output_tokens == 300
        assert abs(session.total_cost - 0.075) < 0.0001  # Float precision
    
    def test_list_sessions(self, storage):
        """Test listing sessions."""
        # Create multiple sessions
        for i in range(5):
            storage.create_session(
                session_id=f"session-{i}",
                provider_type=ProviderType.ANTHROPIC,
                model="claude-3-5-sonnet-20241022"
            )
        
        # List sessions
        sessions = storage.list_sessions(limit=10)
        
        assert len(sessions) == 5
        # Should be ordered by most recent (updated_at desc)
        assert sessions[0].id == "session-4"
        assert sessions[-1].id == "session-0"
    
    def test_list_sessions_with_pagination(self, storage):
        """Test session listing with pagination."""
        # Create 10 sessions
        for i in range(10):
            storage.create_session(
                session_id=f"session-{i}",
                provider_type=ProviderType.ANTHROPIC,
                model="claude-3-5-sonnet-20241022"
            )
        
        # Get first page
        page1 = storage.list_sessions(limit=5, offset=0)
        assert len(page1) == 5
        assert page1[0].id == "session-9"
        
        # Get second page
        page2 = storage.list_sessions(limit=5, offset=5)
        assert len(page2) == 5
        assert page2[0].id == "session-4"
    
    def test_delete_session(self, storage):
        """Test deleting a session."""
        # Create session
        storage.create_session(
            session_id="test-delete",
            provider_type=ProviderType.ANTHROPIC,
            model="claude-3-5-sonnet-20241022"
        )
        
        # Verify it exists
        assert storage.get_session("test-delete") is not None
        
        # Delete it
        result = storage.delete_session("test-delete")
        assert result is True
        
        # Verify it's gone
        assert storage.get_session("test-delete") is None
    
    def test_delete_nonexistent_session(self, storage):
        """Test deleting a nonexistent session."""
        result = storage.delete_session("nonexistent")
        assert result is False


class TestMessageOperations:
    """Test message CRUD operations."""
    
    def test_add_message(self, storage):
        """Test adding a message."""
        # Create session first
        storage.create_session(
            session_id="msg-test-1",
            provider_type=ProviderType.ANTHROPIC,
            model="claude-3-5-sonnet-20241022"
        )
        
        # Add message
        message = storage.add_message(
            session_id="msg-test-1",
            role=Role.USER,
            content="Hello, how are you?",
            input_tokens=10,
            output_tokens=0,
            cost=0.001,
            extra_data={"source": "test"}
        )
        
        assert message.session_id == "msg-test-1"
        assert message.role == "user"
        assert message.content == "Hello, how are you?"
        assert message.input_tokens == 10
        assert message.output_tokens == 0
        assert message.cost == 0.001
        assert message.extra_data == {"source": "test"}
        assert message.created_at is not None
    
    def test_add_message_updates_session_totals(self, storage):
        """Test that adding messages updates session totals."""
        # Create session
        storage.create_session(
            session_id="msg-test-2",
            provider_type=ProviderType.ANTHROPIC,
            model="claude-3-5-sonnet-20241022"
        )
        
        # Add messages
        storage.add_message(
            session_id="msg-test-2",
            role=Role.USER,
            content="Message 1",
            input_tokens=10,
            output_tokens=0,
            cost=0.001
        )
        
        storage.add_message(
            session_id="msg-test-2",
            role=Role.ASSISTANT,
            content="Message 2",
            input_tokens=0,
            output_tokens=20,
            cost=0.002
        )
        
        # Check session totals
        session = storage.get_session("msg-test-2")
        assert session.total_input_tokens == 10
        assert session.total_output_tokens == 20
        assert session.total_cost == 0.003
    
    def test_get_messages(self, storage):
        """Test retrieving messages."""
        # Create session
        storage.create_session(
            session_id="msg-test-3",
            provider_type=ProviderType.ANTHROPIC,
            model="claude-3-5-sonnet-20241022"
        )
        
        # Add messages
        for i in range(5):
            storage.add_message(
                session_id="msg-test-3",
                role=Role.USER if i % 2 == 0 else Role.ASSISTANT,
                content=f"Message {i}"
            )
        
        # Get all messages
        messages = storage.get_messages("msg-test-3")
        
        assert len(messages) == 5
        assert messages[0].content == "Message 0"
        assert messages[-1].content == "Message 4"
    
    def test_get_messages_with_limit(self, storage):
        """Test retrieving messages with limit."""
        # Create session
        storage.create_session(
            session_id="msg-test-4",
            provider_type=ProviderType.ANTHROPIC,
            model="claude-3-5-sonnet-20241022"
        )
        
        # Add 10 messages
        for i in range(10):
            storage.add_message(
                session_id="msg-test-4",
                role=Role.USER,
                content=f"Message {i}"
            )
        
        # Get limited messages
        messages = storage.get_messages("msg-test-4", limit=5)
        
        assert len(messages) == 5
    
    def test_get_message_by_id(self, storage):
        """Test retrieving a specific message."""
        # Create session
        storage.create_session(
            session_id="msg-test-5",
            provider_type=ProviderType.ANTHROPIC,
            model="claude-3-5-sonnet-20241022"
        )
        
        # Add message
        msg = storage.add_message(
            session_id="msg-test-5",
            role=Role.USER,
            content="Test message"
        )
        
        # Retrieve by ID
        retrieved = storage.get_message(msg.id)
        
        assert retrieved is not None
        assert retrieved.id == msg.id
        assert retrieved.content == "Test message"


class TestToolCallOperations:
    """Test tool call operations."""
    
    def test_add_tool_call(self, storage):
        """Test adding a tool call."""
        # Create session and message
        storage.create_session(
            session_id="tool-test-1",
            provider_type=ProviderType.ANTHROPIC,
            model="claude-3-5-sonnet-20241022"
        )
        
        msg = storage.add_message(
            session_id="tool-test-1",
            role=Role.ASSISTANT,
            content="Using tool..."
        )
        
        # Add tool call
        tool_call = storage.add_tool_call(
            message_id=msg.id,
            tool_name="read_file",
            parameters={"path": "/tmp/test.txt"},
            result="File contents here",
            success=True,
            duration_ms=15.5
        )
        
        assert tool_call.message_id == msg.id
        assert tool_call.tool_name == "read_file"
        assert tool_call.parameters == {"path": "/tmp/test.txt"}
        assert tool_call.result == "File contents here"
        assert tool_call.success == 1
        assert tool_call.error is None
        assert tool_call.duration_ms == 15.5
    
    def test_add_failed_tool_call(self, storage):
        """Test adding a failed tool call."""
        # Create session and message
        storage.create_session(
            session_id="tool-test-2",
            provider_type=ProviderType.ANTHROPIC,
            model="claude-3-5-sonnet-20241022"
        )
        
        msg = storage.add_message(
            session_id="tool-test-2",
            role=Role.ASSISTANT,
            content="Attempting tool..."
        )
        
        # Add failed tool call
        tool_call = storage.add_tool_call(
            message_id=msg.id,
            tool_name="bash_execute",
            parameters={"command": "invalid"},
            success=False,
            error="Command failed",
            duration_ms=5.2
        )
        
        assert tool_call.success == 0
        assert tool_call.error == "Command failed"
        assert tool_call.result is None
    
    def test_get_tool_calls(self, storage):
        """Test retrieving tool calls."""
        # Create session and message
        storage.create_session(
            session_id="tool-test-3",
            provider_type=ProviderType.ANTHROPIC,
            model="claude-3-5-sonnet-20241022"
        )
        
        msg = storage.add_message(
            session_id="tool-test-3",
            role=Role.ASSISTANT,
            content="Using multiple tools..."
        )
        
        # Add multiple tool calls
        for i in range(3):
            storage.add_tool_call(
                message_id=msg.id,
                tool_name=f"tool_{i}",
                parameters={"index": i},
                result=f"Result {i}",
                success=True
            )
        
        # Get tool calls
        tool_calls = storage.get_tool_calls(msg.id)
        
        assert len(tool_calls) == 3
        assert tool_calls[0].tool_name == "tool_0"
        assert tool_calls[2].tool_name == "tool_2"


class TestUtilityOperations:
    """Test utility operations."""
    
    def test_get_stats(self, storage):
        """Test getting database statistics."""
        # Create some data
        storage.create_session(
            session_id="stats-test-1",
            provider_type=ProviderType.ANTHROPIC,
            model="claude-3-5-sonnet-20241022"
        )
        
        storage.create_session(
            session_id="stats-test-2",
            provider_type=ProviderType.OPENAI,
            model="gpt-4"
        )
        
        msg1 = storage.add_message(
            session_id="stats-test-1",
            role=Role.USER,
            content="Message 1",
            input_tokens=100,
            output_tokens=200,
            cost=0.05
        )
        
        storage.add_tool_call(
            message_id=msg1.id,
            tool_name="test_tool",
            success=True
        )
        
        # Get stats
        stats = storage.get_stats()
        
        assert stats["total_sessions"] == 2
        assert stats["total_messages"] == 1
        assert stats["total_tool_calls"] == 1
        assert stats["total_input_tokens"] == 100
        assert stats["total_output_tokens"] == 200
        assert stats["total_cost"] == 0.05
    
    def test_clear_all(self, storage):
        """Test clearing all data."""
        # Create some data
        storage.create_session(
            session_id="clear-test",
            provider_type=ProviderType.ANTHROPIC,
            model="claude-3-5-sonnet-20241022"
        )
        
        msg = storage.add_message(
            session_id="clear-test",
            role=Role.USER,
            content="Test"
        )
        
        storage.add_tool_call(
            message_id=msg.id,
            tool_name="test",
            success=True
        )
        
        # Verify data exists
        stats_before = storage.get_stats()
        assert stats_before["total_sessions"] > 0
        
        # Clear all
        storage.clear_all()
        
        # Verify data is gone
        stats_after = storage.get_stats()
        assert stats_after["total_sessions"] == 0
        assert stats_after["total_messages"] == 0
        assert stats_after["total_tool_calls"] == 0
