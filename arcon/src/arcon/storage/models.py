"""Database models for SQLAlchemy."""
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import (
    Column, String, Integer, Float, DateTime, JSON, ForeignKey, Text
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class SessionRecord(Base):
    """Database model for session records."""
    
    __tablename__ = "sessions"
    
    # Primary fields
    id = Column(String(36), primary_key=True)
    provider_type = Column(String(50), nullable=False)
    model = Column(String(100), nullable=False)
    
    # Configuration
    temperature = Column(Float, nullable=True)
    max_tokens = Column(Integer, nullable=True)
    working_dir = Column(String(500), nullable=True)
    
    # Token tracking
    total_input_tokens = Column(Integer, default=0)
    total_output_tokens = Column(Integer, default=0)
    total_cost = Column(Float, default=0.0)
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), 
                       onupdate=lambda: datetime.now(timezone.utc))
    
    # Extra data (renamed from metadata to avoid SQLAlchemy conflict)
    extra_data = Column(JSON, nullable=True)
    
    # Relationships
    messages = relationship("MessageRecord", back_populates="session", 
                           cascade="all, delete-orphan", order_by="MessageRecord.created_at")
    
    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<SessionRecord(id={self.id}, provider={self.provider_type}, "
            f"model={self.model}, messages={len(self.messages)})>"
        )


class MessageRecord(Base):
    """Database model for message records."""
    
    __tablename__ = "messages"
    
    # Primary fields
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(36), ForeignKey("sessions.id"), nullable=False)
    
    # Message content
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    
    # Token tracking
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    cost = Column(Float, default=0.0)
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Extra data (renamed from metadata to avoid SQLAlchemy conflict)
    extra_data = Column(JSON, nullable=True)
    
    # Relationships
    session = relationship("SessionRecord", back_populates="messages")
    tool_calls = relationship("ToolCallRecord", back_populates="message",
                             cascade="all, delete-orphan", order_by="ToolCallRecord.created_at")
    
    def __repr__(self) -> str:
        """String representation."""
        content_preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return (
            f"<MessageRecord(id={self.id}, session_id={self.session_id}, "
            f"role={self.role}, content='{content_preview}')>"
        )


class ToolCallRecord(Base):
    """Database model for tool call records."""
    
    __tablename__ = "tool_calls"
    
    # Primary fields
    id = Column(Integer, primary_key=True, autoincrement=True)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=False)
    
    # Tool information
    tool_name = Column(String(100), nullable=False)
    parameters = Column(JSON, nullable=True)
    result = Column(Text, nullable=True)
    
    # Execution details
    success = Column(Integer, default=1)  # SQLite boolean (0/1)
    error = Column(Text, nullable=True)
    duration_ms = Column(Float, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    message = relationship("MessageRecord", back_populates="tool_calls")
    
    def __repr__(self) -> str:
        """String representation."""
        status = "success" if self.success else "failed"
        return (
            f"<ToolCallRecord(id={self.id}, tool={self.tool_name}, "
            f"status={status})>"
        )
