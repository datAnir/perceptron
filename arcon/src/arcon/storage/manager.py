"""Storage manager for database operations."""
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker, Session as DBSession

from .models import Base, SessionRecord, MessageRecord, ToolCallRecord
from ..core.types import Message, Role, ProviderType


class StorageManager:
    """Manager for persisting and retrieving session data."""
    
    def __init__(self, database_path: str = "arcon.db"):
        """Initialize storage manager.
        
        Args:
            database_path: Path to SQLite database file
        """
        self.database_path = Path(database_path)
        self.engine = create_engine(f"sqlite:///{self.database_path}", echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        # Create tables if they don't exist
        Base.metadata.create_all(self.engine)
    
    def _get_db(self) -> DBSession:
        """Get database session."""
        return self.SessionLocal()
    
    # Session operations
    
    def create_session(
        self,
        session_id: str,
        provider_type: ProviderType,
        model: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        working_dir: Optional[str] = None,
        extra_data: Optional[Dict[str, Any]] = None,
    ) -> SessionRecord:
        """Create a new session record.
        
        Args:
            session_id: Unique session identifier
            provider_type: Type of LLM provider
            model: Model name
            temperature: Temperature setting
            max_tokens: Max tokens setting
            working_dir: Working directory path
            extra_data: Additional metadata
            
        Returns:
            Created session record
        """
        db = self._get_db()
        try:
            session = SessionRecord(
                id=session_id,
                provider_type=provider_type.value,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                working_dir=working_dir,
                extra_data=extra_data,
            )
            db.add(session)
            db.commit()
            db.refresh(session)
            return session
        finally:
            db.close()
    
    def get_session(self, session_id: str) -> Optional[SessionRecord]:
        """Get session by ID.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session record or None if not found
        """
        db = self._get_db()
        try:
            return db.query(SessionRecord).filter(SessionRecord.id == session_id).first()
        finally:
            db.close()
    
    def update_session_tokens(
        self,
        session_id: str,
        input_tokens: int,
        output_tokens: int,
        cost: float,
    ) -> bool:
        """Update session token counts and cost.
        
        Args:
            session_id: Session identifier
            input_tokens: Input tokens to add
            output_tokens: Output tokens to add
            cost: Cost to add
            
        Returns:
            True if updated, False if session not found
        """
        db = self._get_db()
        try:
            session = db.query(SessionRecord).filter(SessionRecord.id == session_id).first()
            if not session:
                return False
            
            session.total_input_tokens += input_tokens
            session.total_output_tokens += output_tokens
            session.total_cost += cost
            session.updated_at = datetime.now(timezone.utc)
            
            db.commit()
            return True
        finally:
            db.close()
    
    def list_sessions(
        self,
        limit: int = 50,
        offset: int = 0,
    ) -> List[SessionRecord]:
        """List sessions ordered by most recent.
        
        Args:
            limit: Maximum number of sessions to return
            offset: Number of sessions to skip
            
        Returns:
            List of session records
        """
        db = self._get_db()
        try:
            return (
                db.query(SessionRecord)
                .order_by(desc(SessionRecord.updated_at))
                .limit(limit)
                .offset(offset)
                .all()
            )
        finally:
            db.close()
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session and all its messages.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if deleted, False if not found
        """
        db = self._get_db()
        try:
            session = db.query(SessionRecord).filter(SessionRecord.id == session_id).first()
            if not session:
                return False
            
            db.delete(session)
            db.commit()
            return True
        finally:
            db.close()
    
    # Message operations
    
    def add_message(
        self,
        session_id: str,
        role: Role,
        content: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        cost: float = 0.0,
        extra_data: Optional[Dict[str, Any]] = None,
    ) -> MessageRecord:
        """Add a message to a session.
        
        Args:
            session_id: Session identifier
            role: Message role
            content: Message content
            input_tokens: Input tokens used
            output_tokens: Output tokens used
            cost: Cost of this message
            extra_data: Additional metadata
            
        Returns:
            Created message record
        """
        db = self._get_db()
        try:
            message = MessageRecord(
                session_id=session_id,
                role=role.value,
                content=content,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost=cost,
                extra_data=extra_data,
            )
            db.add(message)
            db.commit()
            db.refresh(message)
            
            # Update session totals
            self.update_session_tokens(session_id, input_tokens, output_tokens, cost)
            
            return message
        finally:
            db.close()
    
    def get_messages(
        self,
        session_id: str,
        limit: Optional[int] = None,
    ) -> List[MessageRecord]:
        """Get messages for a session.
        
        Args:
            session_id: Session identifier
            limit: Maximum number of messages (most recent)
            
        Returns:
            List of message records in chronological order
        """
        db = self._get_db()
        try:
            query = db.query(MessageRecord).filter(
                MessageRecord.session_id == session_id
            ).order_by(MessageRecord.created_at)
            
            if limit:
                # Get most recent N messages
                query = query.limit(limit)
            
            return query.all()
        finally:
            db.close()
    
    def get_message(self, message_id: int) -> Optional[MessageRecord]:
        """Get a specific message by ID.
        
        Args:
            message_id: Message identifier
            
        Returns:
            Message record or None if not found
        """
        db = self._get_db()
        try:
            return db.query(MessageRecord).filter(MessageRecord.id == message_id).first()
        finally:
            db.close()
    
    # Tool call operations
    
    def add_tool_call(
        self,
        message_id: int,
        tool_name: str,
        parameters: Optional[Dict[str, Any]] = None,
        result: Optional[str] = None,
        success: bool = True,
        error: Optional[str] = None,
        duration_ms: Optional[float] = None,
    ) -> ToolCallRecord:
        """Add a tool call record to a message.
        
        Args:
            message_id: Message identifier
            tool_name: Name of the tool
            parameters: Tool parameters
            result: Tool execution result
            success: Whether tool execution succeeded
            error: Error message if failed
            duration_ms: Execution duration in milliseconds
            
        Returns:
            Created tool call record
        """
        db = self._get_db()
        try:
            tool_call = ToolCallRecord(
                message_id=message_id,
                tool_name=tool_name,
                parameters=parameters,
                result=result,
                success=1 if success else 0,
                error=error,
                duration_ms=duration_ms,
            )
            db.add(tool_call)
            db.commit()
            db.refresh(tool_call)
            return tool_call
        finally:
            db.close()
    
    def get_tool_calls(self, message_id: int) -> List[ToolCallRecord]:
        """Get tool calls for a message.
        
        Args:
            message_id: Message identifier
            
        Returns:
            List of tool call records
        """
        db = self._get_db()
        try:
            return (
                db.query(ToolCallRecord)
                .filter(ToolCallRecord.message_id == message_id)
                .order_by(ToolCallRecord.created_at)
                .all()
            )
        finally:
            db.close()
    
    # Utility operations
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics.
        
        Returns:
            Dictionary with database statistics
        """
        db = self._get_db()
        try:
            total_sessions = db.query(SessionRecord).count()
            total_messages = db.query(MessageRecord).count()
            total_tool_calls = db.query(ToolCallRecord).count()
            
            # Calculate total tokens and cost
            sessions = db.query(SessionRecord).all()
            total_input_tokens = sum(s.total_input_tokens for s in sessions)
            total_output_tokens = sum(s.total_output_tokens for s in sessions)
            total_cost = sum(s.total_cost for s in sessions)
            
            return {
                "total_sessions": total_sessions,
                "total_messages": total_messages,
                "total_tool_calls": total_tool_calls,
                "total_input_tokens": total_input_tokens,
                "total_output_tokens": total_output_tokens,
                "total_cost": total_cost,
            }
        finally:
            db.close()
    
    def clear_all(self) -> None:
        """Clear all data from database (for testing)."""
        db = self._get_db()
        try:
            db.query(ToolCallRecord).delete()
            db.query(MessageRecord).delete()
            db.query(SessionRecord).delete()
            db.commit()
        finally:
            db.close()
