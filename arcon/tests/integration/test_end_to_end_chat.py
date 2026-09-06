"""End-to-end chat integration tests."""
import os
import pytest
from pathlib import Path

from arcon.providers import ProviderResolver
from arcon.core.types import ProviderType, Role
from arcon.core.session import Session
from arcon.storage import StorageManager


@pytest.mark.skipif(
    not os.getenv("ANTHROPIC_API_KEY"),
    reason="Requires ANTHROPIC_API_KEY environment variable"
)
@pytest.mark.asyncio
async def test_basic_chat_flow():
    """Test basic chat flow with real API."""
    # Initialize components
    provider = ProviderResolver.get_provider(ProviderType.ANTHROPIC)
    working_dir = Path("test_workspace")
    working_dir.mkdir(exist_ok=True)
    
    session = Session(provider=provider, working_dir=str(working_dir))
    
    # Add user message
    session.add_message(Role.USER, "What is 2 + 2? Answer with just the number.")
    
    # Get response
    response_chunks = []
    async for chunk in session.send_message("What is 2 + 2? Answer with just the number."):
        if isinstance(chunk, dict) and chunk.get("type") == "text":
            response_chunks.append(chunk.get("content", ""))
        elif isinstance(chunk, str):
            response_chunks.append(chunk)
    
    full_response = "".join(response_chunks)
    
    # Verify response
    assert len(full_response) > 0
    assert "4" in full_response
    
    # Check session state
    assert len(session.messages) == 2  # user + assistant
    assert session.total_input_tokens > 0
    assert session.total_output_tokens > 0
    
    # Cleanup
    import shutil
    shutil.rmtree(working_dir, ignore_errors=True)


@pytest.mark.asyncio
async def test_session_persistence():
    """Test session persistence to database."""
    storage = StorageManager(":memory:")
    session_id = "test-session-001"
    
    # Create session
    storage.create_session(
        session_id=session_id,
        provider_type=ProviderType.ANTHROPIC,
        model="claude-3-5-sonnet-20241022",
        temperature=0.7,
        max_tokens=4096,
        working_dir="/tmp/test",
    )
    
    # Add messages
    msg1_id = storage.add_message(
        session_id=session_id,
        role=Role.USER,
        content="Hello, how are you?",
    )
    
    msg2_id = storage.add_message(
        session_id=session_id,
        role=Role.ASSISTANT,
        content="I'm doing well, thank you for asking!",
    )
    
    # Retrieve session
    retrieved_session = storage.get_session(session_id)
    assert retrieved_session is not None
    assert retrieved_session.id == session_id
    
    # Retrieve messages
    messages = storage.get_messages(session_id)
    assert len(messages) == 2
    assert messages[0].id == msg1_id.id
    assert messages[0].role == Role.USER.value
    assert messages[1].id == msg2_id.id
    assert messages[1].role == Role.ASSISTANT.value


@pytest.mark.asyncio
async def test_multi_turn_conversation():
    """Test multi-turn conversation with context."""
    storage = StorageManager(":memory:")
    session_id = "test-multi-turn"
    
    # Create session
    storage.create_session(
        session_id=session_id,
        provider_type=ProviderType.ANTHROPIC,
        model="claude-3-5-sonnet-20241022",
    )
    
    # Turn 1
    storage.add_message(
        session_id=session_id,
        role=Role.USER,
        content="My favorite color is blue.",
    )
    storage.add_message(
        session_id=session_id,
        role=Role.ASSISTANT,
        content="I'll remember that your favorite color is blue.",
    )
    
    # Turn 2
    storage.add_message(
        session_id=session_id,
        role=Role.USER,
        content="What's my favorite color?",
    )
    storage.add_message(
        session_id=session_id,
        role=Role.ASSISTANT,
        content="Your favorite color is blue.",
    )
    
    # Verify conversation flow
    messages = storage.get_messages(session_id)
    assert len(messages) == 4
    
    # Check alternating roles
    assert messages[0].role == Role.USER.value
    assert messages[1].role == Role.ASSISTANT.value
    assert messages[2].role == Role.USER.value
    assert messages[3].role == Role.ASSISTANT.value


@pytest.mark.asyncio
async def test_session_statistics():
    """Test session statistics calculation."""
    storage = StorageManager(":memory:")
    
    # Create multiple sessions
    for i in range(3):
        session_id = f"test-session-{i}"
        storage.create_session(
            session_id=session_id,
            provider_type=ProviderType.ANTHROPIC,
            model="claude-3-5-sonnet-20241022",
        )
        
        # Add messages
        storage.add_message(
            session_id=session_id,
            role=Role.USER,
            content=f"Message {i}",
        )
        storage.add_message(
            session_id=session_id,
            role=Role.ASSISTANT,
            content=f"Response {i}",
        )
    
    # Get statistics
    stats = storage.get_stats()
    
    assert stats["total_sessions"] == 3
    assert stats["total_messages"] == 6
    assert stats["total_tool_calls"] == 0


@pytest.mark.asyncio
async def test_session_cleanup():
    """Test session deletion."""
    storage = StorageManager(":memory:")
    session_id = "test-cleanup"
    
    # Create session with messages
    storage.create_session(
        session_id=session_id,
        provider_type=ProviderType.ANTHROPIC,
        model="claude-3-5-sonnet-20241022",
    )
    storage.add_message(
        session_id=session_id,
        role=Role.USER,
        content="Test message",
    )
    
    # Verify exists
    assert storage.get_session(session_id) is not None
    
    # Delete
    storage.delete_session(session_id)
    
    # Verify deleted
    assert storage.get_session(session_id) is None
    assert len(storage.get_messages(session_id)) == 0
