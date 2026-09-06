"""Session management for Arcon."""
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, AsyncIterator, Dict, List, Optional

from .interface import LLMProvider, SessionError
from .types import Message, Role


class Session:
    """Manages a conversation session with an LLM."""
    
    def __init__(
        self,
        session_id: Optional[str] = None,
        working_dir: Optional[Path] = None,
        provider: Optional[LLMProvider] = None,
    ):
        """Initialize a session.
        
        Args:
            session_id: Unique session identifier (generated if not provided)
            working_dir: Working directory for this session
            provider: LLM provider to use
        """
        self.id = session_id or self._generate_session_id()
        self.working_dir = working_dir or Path.cwd()
        self.provider = provider
        self.messages: List[Message] = []
        self.metadata: Dict[str, Any] = {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "status": "active",
        }
        self._total_input_tokens = 0
        self._total_output_tokens = 0
        self._total_cost_usd = 0.0
    
    @staticmethod
    def _generate_session_id() -> str:
        """Generate a unique session identifier."""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        short_uuid = str(uuid.uuid4())[:8]
        return f"{timestamp}-{short_uuid}"
    
    def add_message(self, message: Message) -> None:
        """Add a message to the session history.
        
        Args:
            message: Message to add
        """
        self.messages.append(message)
        self.metadata["updated_at"] = datetime.now(timezone.utc).isoformat()
        self.metadata["message_count"] = len(self.messages)
    
    async def invoke(
        self,
        query: str,
        system_prompt: Optional[str] = None,
        stream: bool = True,
        **kwargs: Any
    ) -> AsyncIterator[Dict[str, Any]]:
        """Invoke the LLM with a query.
        
        Args:
            query: User query
            system_prompt: Optional system prompt to prepend
            stream: Whether to stream the response
            **kwargs: Additional parameters for the provider
            
        Yields:
            Response chunks from the provider
            
        Raises:
            SessionError: If provider is not configured
        """
        if not self.provider:
            raise SessionError("No provider configured for this session")
        
        # Add user message
        user_message = Message(role=Role.USER, content=query)
        self.add_message(user_message)
        
        # Prepare messages for provider
        messages_to_send = self.messages.copy()
        if system_prompt and (not messages_to_send or messages_to_send[0].role != Role.SYSTEM):
            messages_to_send.insert(0, Message(role=Role.SYSTEM, content=system_prompt))
        
        # Invoke provider
        assistant_content = ""
        async for chunk in self.provider.create_message(
            messages=messages_to_send,
            stream=stream,
            **kwargs
        ):
            if chunk.get("type") == "text":
                assistant_content += chunk.get("content", "")
            yield chunk
        
        # Add assistant response to history
        if assistant_content:
            assistant_message = Message(role=Role.ASSISTANT, content=assistant_content)
            self.add_message(assistant_message)
    
    def get_context(self, max_messages: Optional[int] = None) -> List[Message]:
        """Get conversation context.
        
        Args:
            max_messages: Maximum number of recent messages to return
            
        Returns:
            List of messages (most recent if max_messages is specified)
        """
        if max_messages:
            return self.messages[-max_messages:]
        return self.messages.copy()
    
    def clear_context(self) -> None:
        """Clear conversation context."""
        self.messages.clear()
        self.metadata["updated_at"] = datetime.now(timezone.utc).isoformat()
        self.metadata["message_count"] = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary format.
        
        Returns:
            Dictionary representation of the session
        """
        return {
            "id": self.id,
            "working_dir": str(self.working_dir),
            "messages": [msg.to_dict() for msg in self.messages],
            "metadata": self.metadata,
            "stats": {
                "total_input_tokens": self._total_input_tokens,
                "total_output_tokens": self._total_output_tokens,
                "total_cost_usd": self._total_cost_usd,
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], provider: Optional[LLMProvider] = None) -> "Session":
        """Create session from dictionary format.
        
        Args:
            data: Dictionary representation
            provider: LLM provider to use
            
        Returns:
            Reconstructed session
        """
        session = cls(
            session_id=data["id"],
            working_dir=Path(data["working_dir"]),
            provider=provider
        )
        session.messages = [Message.from_dict(msg) for msg in data["messages"]]
        session.metadata = data["metadata"]
        
        if "stats" in data:
            stats = data["stats"]
            session._total_input_tokens = stats.get("total_input_tokens", 0)
            session._total_output_tokens = stats.get("total_output_tokens", 0)
            session._total_cost_usd = stats.get("total_cost_usd", 0.0)
        
        return session
