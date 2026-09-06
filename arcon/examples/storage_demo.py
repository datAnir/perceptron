#!/usr/bin/env python3
"""
Example demonstrating Arcon's SQLite storage layer.

This example shows how to:
1. Create and persist sessions
2. Add messages with token tracking
3. Log tool calls
4. Query session history
5. Get database statistics
"""

from arcon.storage import StorageManager
from arcon.core.types import ProviderType, Role


def main():
    """Demonstrate storage operations."""
    
    print("=" * 80)
    print("Arcon - Storage Layer Demo")
    print("=" * 80)
    
    # Create storage manager
    storage = StorageManager("demo.db")
    print("\n✅ Storage manager initialized (demo.db)")
    
    # Create a session
    print("\n📦 Creating session...")
    session = storage.create_session(
        session_id="demo-session-001",
        provider_type=ProviderType.ANTHROPIC,
        model="claude-3-5-sonnet-20241022",
        temperature=0.7,
        max_tokens=2048,
        working_dir="/tmp/demo",
        extra_data={"user": "demo_user", "project": "arcon_demo"}
    )
    
    print(f"   Session ID: {session.id}")
    print(f"   Provider: {session.provider_type}")
    print(f"   Model: {session.model}")
    
    # Add user message
    print("\n💬 Adding user message...")
    user_msg = storage.add_message(
        session_id=session.id,
        role=Role.USER,
        content="Can you read the contents of /tmp/test.txt?",
        input_tokens=15,
        output_tokens=0,
        cost=0.000045
    )
    print(f"   Message ID: {user_msg.id}")
    print(f"   Role: {user_msg.role}")
    print(f"   Content: {user_msg.content}")
    
    # Add assistant message with tool call
    print("\n🤖 Adding assistant message...")
    assistant_msg = storage.add_message(
        session_id=session.id,
        role=Role.ASSISTANT,
        content="I'll read that file for you.",
        input_tokens=15,
        output_tokens=8,
        cost=0.000165
    )
    
    print("\n🔧 Logging tool call...")
    tool_call = storage.add_tool_call(
        message_id=assistant_msg.id,
        tool_name="read_file",
        parameters={"path": "/tmp/test.txt"},
        result="File contents: Hello, world!",
        success=True,
        duration_ms=12.5
    )
    print(f"   Tool: {tool_call.tool_name}")
    print(f"   Success: {bool(tool_call.success)}")
    print(f"   Duration: {tool_call.duration_ms}ms")
    
    # Add final assistant message
    print("\n🤖 Adding final response...")
    storage.add_message(
        session_id=session.id,
        role=Role.ASSISTANT,
        content="The file contains: 'Hello, world!'",
        input_tokens=20,
        output_tokens=12,
        cost=0.00024
    )
    
    # Retrieve session with updated totals
    print("\n📊 Session Summary:")
    session = storage.get_session(session.id)
    print(f"   Total Input Tokens: {session.total_input_tokens:,}")
    print(f"   Total Output Tokens: {session.total_output_tokens:,}")
    print(f"   Total Cost: ${session.total_cost:.6f}")
    
    # List all messages
    print("\n📜 Message History:")
    messages = storage.get_messages(session.id)
    print(f"   Total Messages: {len(messages)}")
    for i, msg in enumerate(messages, 1):
        content_preview = msg.content[:50] + "..." if len(msg.content) > 50 else msg.content
        print(f"   {i}. [{msg.role}] {content_preview}")
        
        # Show tool calls if any
        tool_calls = storage.get_tool_calls(msg.id)
        if tool_calls:
            for tc in tool_calls:
                print(f"      └─ Tool: {tc.tool_name} ({tc.duration_ms}ms)")
    
    # Database statistics
    print("\n📈 Database Statistics:")
    stats = storage.get_stats()
    print(f"   Total Sessions: {stats['total_sessions']}")
    print(f"   Total Messages: {stats['total_messages']}")
    print(f"   Total Tool Calls: {stats['total_tool_calls']}")
    print(f"   Total Tokens: {stats['total_input_tokens'] + stats['total_output_tokens']:,}")
    print(f"   Total Cost: ${stats['total_cost']:.6f}")
    
    print("\n" + "=" * 80)
    print("✅ Demo complete! Database saved to demo.db")
    print("=" * 80)


if __name__ == "__main__":
    main()
