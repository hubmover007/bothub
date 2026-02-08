"""
BotHub 认领系统 - 数据库模型
支持所有者认领和非所有者认领（雇佣/分享）
"""

import uuid
from datetime import datetime
from typing import Optional
from enum import Enum

from sqlalchemy import Column, String, DateTime, Text, JSON, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class ClaimType(str, Enum):
    """认领类型"""
    OWNER = "owner"  # 所有者认领
    HIRE = "hire"    # 雇佣（非所有者）
    SHARE = "share"  # 分享（非所有者）


class ClaimStatus(str, Enum):
    """认领状态"""
    PENDING = "pending"      # 等待确认
    APPROVED = "approved"    # 已批准
    REJECTED = "rejected"    # 已拒绝
    EXPIRED = "expired"      # 已过期


class User(Base):
    """用户模型"""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    feishu_user_id = Column(String(128), unique=True, nullable=False, index=True)
    feishu_open_id = Column(String(128), unique=True, nullable=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    avatar_url = Column(String(512), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    owned_bots = relationship("Bot", back_populates="owner", foreign_keys="Bot.owner_id")
    claim_requests = relationship("ClaimRequest", back_populates="requester")


class ClaimRequest(Base):
    """认领请求"""
    __tablename__ = "claim_requests"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # 关联
    bot_id = Column(UUID(as_uuid=True), ForeignKey("bots.id"), nullable=False, index=True)
    requester_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # 认领类型
    claim_type = Column(SQLEnum(ClaimType), nullable=False)
    status = Column(SQLEnum(ClaimStatus), default=ClaimStatus.PENDING, nullable=False)
    
    # 请求信息
    message = Column(Text, nullable=True)  # 认领理由
    
    # 飞书验证信息
    feishu_verified = Column(Boolean, default=False)
    feishu_verification_data = Column(JSON, nullable=True)
    
    # 审批信息
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    approval_message = Column(Text, nullable=True)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    approved_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    
    # 关系
    bot = relationship("Bot", back_populates="claim_requests")
    requester = relationship("User", back_populates="claim_requests", foreign_keys=[requester_id])
    approver = relationship("User", foreign_keys=[approved_by])
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "bot_id": str(self.bot_id),
            "requester_id": str(self.requester_id),
            "claim_type": self.claim_type.value,
            "status": self.status.value,
            "message": self.message,
            "feishu_verified": self.feishu_verified,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
        }


class BotAccessGrant(Base):
    """机器人访问授权（雇佣/分享后的权限）"""
    __tablename__ = "bot_access_grants"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # 关联
    bot_id = Column(UUID(as_uuid=True), ForeignKey("bots.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # 访问类型
    access_type = Column(SQLEnum(ClaimType), nullable=False)  # hire 或 share
    
    # 权限设置
    permissions = Column(JSON, default=dict)  # {"can_invoke": true, "can_view_logs": false, ...}
    
    # 有效期
    valid_from = Column(DateTime, default=datetime.utcnow)
    valid_until = Column(DateTime, nullable=True)
    
    # 状态
    is_active = Column(Boolean, default=True)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    revoked_at = Column(DateTime, nullable=True)
    
    # 关系
    bot = relationship("Bot", back_populates="access_grants")
    user = relationship("User")
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "bot_id": str(self.bot_id),
            "user_id": str(self.user_id),
            "access_type": self.access_type.value,
            "permissions": self.permissions,
            "valid_from": self.valid_from.isoformat() if self.valid_from else None,
            "valid_until": self.valid_until.isoformat() if self.valid_until else None,
            "is_active": self.is_active,
        }
