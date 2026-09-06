"""Session management commands."""
from datetime import datetime

from ..storage import StorageManager


class SessionManager:
    """Manage chat sessions."""
    
    def __init__(self):
        """Initialize session manager."""
        self.storage = StorageManager()
    
    def list_sessions(self, limit: int = 20):
        """List recent sessions."""
        sessions = self.storage.list_sessions(limit=limit)
        
        if not sessions:
            print("\nNo sessions found.")
            return
        
        print(f"\n📋 Recent Sessions ({len(sessions)}):")
        print("=" * 100)
        print(f"{'Session ID':<25} {'Provider':<12} {'Model':<30} {'Messages':<10} {'Cost':<12}")
        print("-" * 100)
        
        for session in sessions:
            messages_count = len(self.storage.get_messages(session.id))
            print(
                f"{session.id:<25} "
                f"{session.provider_type:<12} "
                f"{session.model:<30} "
                f"{messages_count:<10} "
                f"${session.total_cost:<11.6f}"
            )
        
        print()
    
    def show_session(self, session_id: str):
        """Show detailed session information."""
        session = self.storage.get_session(session_id)
        
        if not session:
            print(f"\n❌ Session not found: {session_id}")
            return
        
        messages = self.storage.get_messages(session_id)
        
        print(f"\n📊 Session Details: {session_id}")
        print("=" * 80)
        print(f"Provider: {session.provider_type}")
        print(f"Model: {session.model}")
        print(f"Created: {session.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Updated: {session.updated_at.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"\nToken Usage:")
        print(f"  Input tokens: {session.total_input_tokens:,}")
        print(f"  Output tokens: {session.total_output_tokens:,}")
        print(f"  Total cost: ${session.total_cost:.6f}")
        
        print(f"\n💬 Messages ({len(messages)}):")
        print("-" * 80)
        
        for i, msg in enumerate(messages, 1):
            timestamp = msg.created_at.strftime('%H:%M:%S')
            content_preview = msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
            print(f"\n{i}. [{msg.role.upper()}] @ {timestamp}")
            print(f"   {content_preview}")
            
            # Show tool calls if any
            tool_calls = self.storage.get_tool_calls(msg.id)
            if tool_calls:
                for tc in tool_calls:
                    status = "✓" if tc.success else "✗"
                    print(f"   {status} Tool: {tc.tool_name} ({tc.duration_ms:.1f}ms)")
        
        print()
    
    def delete_session(self, session_id: str):
        """Delete a session."""
        session = self.storage.get_session(session_id)
        
        if not session:
            print(f"\n❌ Session not found: {session_id}")
            return
        
        # Confirm deletion
        response = input(f"\n⚠️  Delete session {session_id}? This cannot be undone. (y/N): ")
        
        if response.lower() != 'y':
            print("Cancelled.")
            return
        
        self.storage.delete_session(session_id)
        print(f"\n✅ Session deleted: {session_id}")
    
    def show_stats(self):
        """Show database statistics."""
        stats = self.storage.get_stats()
        
        print("\n📈 Database Statistics:")
        print("=" * 80)
        print(f"Total Sessions: {stats['total_sessions']:,}")
        print(f"Total Messages: {stats['total_messages']:,}")
        print(f"Total Tool Calls: {stats['total_tool_calls']:,}")
        print(f"\nToken Usage:")
        print(f"  Input tokens: {stats['total_input_tokens']:,}")
        print(f"  Output tokens: {stats['total_output_tokens']:,}")
        print(f"  Total tokens: {stats['total_input_tokens'] + stats['total_output_tokens']:,}")
        print(f"\nTotal Cost: ${stats['total_cost']:.6f}")
        print()
