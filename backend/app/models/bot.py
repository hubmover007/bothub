"""
BotHub Bot Model - 机器人模型
整合了认领系统的所有字段
"""

import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum

from sqlalchemy import Column, String, DateTime, Text, JSON, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class BotStatus(str, Enum):
    """机器人状态"""
    UNCLAIMED = "unclaimed"  # 未认领
    CLAIMED = "claimed"      # 已认领（有所有者）
    OFFLINE = "offline"      # 离线
    ONLINE = "online"        # 在线
    BUSY = "busy"           # 忙碌
    ERROR = "error"         # 错误


class Bot(Base):
    """Bot model representing a registered bot in the system."""

    __tablename__ = "bots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bot_id = Column(String(255), unique=True, nullable=False, index=True)
    bot_name = Column(String(255), nullable=False)
    
    # 飞书相关
    feishu_app_id = Column(String(128), nullable=True, index=True)
    feishu_bot_id = Column(String(128), nullable=True)
    
    # 所有者
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    
    # 基本信息
    description = Column(Text, nullable=True)
    avatar_url = Column(String(512), nullable=True)
    status = Column(SQLEnum(BotStatus), default=BotStatus.OFFLINE, nullable=False)
    
    # 能力和配置
    capabilities = Column(JSON, default=dict, nullable=False)
    endpoint = Column(String(512), nullable=True)
    version = Column(String(50), nullable=True)
    
    # 认领码
    claim_code = Column(String(64), unique=True, nullable=True, index=True)
    claim_code_expires_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    claimed_at = Column(DateTime, nullable=True)
    last_heartbeat_at = Column(DateTime, nullable=True)
    
    # 关系
    owner = relationship("User", back_populates="owned_bots", foreign_keys=[owner_id])
    claim_requests = relationship("ClaimRequest", back_populates="bot", cascade="all, delete-orphan")
    access_grants = relationship("BotAccessGrant", back_populates="bot", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Bot(id={self.id}, bot_id={self.bot_id}, name={self.bot_name})>"

    def to_dict(self) -> Dict[str, Any]:
        """Convert bot instance to dictionary."""
        return {
            "id": str(self.id),
            "bot_id": self.bot_id,
            "bot_name": self.bot_name,
            "feishu_app_id": self.feishu_app_id,
            "owner_id": str(self.owner_id) if self.owner_id else None,
            "description": self.description,
            "avatar_url": self.avatar_url,
            "status": self.status.value if isinstance(self.status, Enum) else self.status,
            "capabilities": self.capabilities,
            "endpoint": self.endpoint,
            "version": self.version,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "claimed_at": self.claimed_at.isoformat() if self.claimed_at else None,
            "last_heartbeat_at": self.last_heartbeat_at.isoformat() if self.last_heartbeat_at else None,
        }
