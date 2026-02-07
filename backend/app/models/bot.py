import uuid
from datetime import datetime
from typing import Dict, Any, Optional

from sqlalchemy import Column, String, DateTime, Text, JSON
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class Bot(Base):
    """Bot model representing a registered bot in the system."""

    __tablename__ = "bots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bot_id = Column(String(255), unique=True, nullable=False, index=True)
    bot_name = Column(String(255), nullable=False)
    owner_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    description = Column(Text, nullable=True)
    status = Column(String(50), default="offline", nullable=False)
    capabilities = Column(JSON, default=dict, nullable=False)
    endpoint = Column(String(512), nullable=True)
    version = Column(String(50), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_heartbeat_at = Column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<Bot(id={self.id}, bot_id={self.bot_id}, name={self.bot_name})>"

    def to_dict(self) -> Dict[str, Any]:
        """Convert bot instance to dictionary."""
        return {
            "id": str(self.id),
            "bot_id": self.bot_id,
            "bot_name": self.bot_name,
            "owner_id": str(self.owner_id),
            "description": self.description,
            "status": self.status,
            "capabilities": self.capabilities,
            "endpoint": self.endpoint,
            "version": self.version,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_heartbeat_at": self.last_heartbeat_at.isoformat() if self.last_heartbeat_at else None,
        }
