"""
BotHub 认领系统 - Pydantic Schemas
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID
from pydantic import BaseModel, Field, HttpUrl

from app.models.claim import ClaimType, ClaimStatus, BotStatus


# ========== 用户相关 ==========

class UserBase(BaseModel):
    feishu_user_id: str
    name: str
    email: Optional[str] = None
    avatar_url: Optional[str] = None


class UserCreate(UserBase):
    feishu_open_id: Optional[str] = None


class UserResponse(UserBase):
    id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True


# ========== 机器人注册 ==========

class BotRegister(BaseModel):
    """机器人注册请求"""
    bot_id: str = Field(..., description="机器人唯一ID")
    bot_name: str = Field(..., description="机器人名称")
    feishu_app_id: Optional[str] = Field(None, description="飞书应用ID")
    feishu_bot_id: Optional[str] = Field(None, description="飞书机器人ID")
    description: Optional[str] = None
    capabilities: Dict[str, Any] = Field(default_factory=dict)
    endpoint: Optional[str] = None
    version: Optional[str] = None


class BotRegisterResponse(BaseModel):
    """机器人注册响应"""
    id: UUID
    bot_id: str
    bot_name: str
    status: BotStatus
    claim_code: str
    claim_url: str
    claim_code_expires_at: datetime
    feishu_app_id: Optional[str]
    
    class Config:
        from_attributes = True


# ========== 机器人信息 ==========

class BotCard(BaseModel):
    """机器人卡片信息（前端展示）"""
    id: UUID
    bot_id: str
    bot_name: str
    description: Optional[str]
    avatar_url: Optional[str]
    status: BotStatus
    feishu_app_id: Optional[str]
    
    # 所有者信息
    owner: Optional[UserResponse] = None
    claimed_at: Optional[datetime] = None
    
    # 认领状态
    is_claimed: bool
    can_claim: bool  # 当前用户是否可以认领
    
    # 统计信息
    capabilities: Dict[str, Any]
    version: Optional[str]
    last_heartbeat_at: Optional[datetime]
    
    created_at: datetime


class BotUpdate(BaseModel):
    """机器人更新"""
    bot_name: Optional[str] = None
    description: Optional[str] = None
    avatar_url: Optional[str] = None
    capabilities: Optional[Dict[str, Any]] = None
    endpoint: Optional[str] = None
    version: Optional[str] = None


# ========== 认领请求 ==========

class ClaimRequestCreate(BaseModel):
    """创建认领请求"""
    claim_code: Optional[str] = Field(None, description="认领码（所有者认领时使用）")
    bot_id: Optional[str] = Field(None, description="机器人ID（非所有者认领时使用）")
    claim_type: ClaimType = Field(..., description="认领类型")
    message: Optional[str] = Field(None, description="认领理由")
    feishu_code: str = Field(..., description="飞书 OAuth 授权码")


class ClaimRequestResponse(BaseModel):
    """认领请求响应"""
    id: UUID
    bot_id: UUID
    bot_name: str
    requester: UserResponse
    claim_type: ClaimType
    status: ClaimStatus
    message: Optional[str]
    feishu_verified: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class ClaimApproval(BaseModel):
    """认领批准/拒绝"""
    request_id: UUID
    approved: bool
    message: Optional[str] = None


# ========== 飞书验证 ==========

class FeishuOAuthCallback(BaseModel):
    """飞书 OAuth 回调"""
    code: str
    state: Optional[str] = None


class FeishuUserInfo(BaseModel):
    """飞书用户信息"""
    user_id: str
    open_id: str
    name: str
    email: Optional[str]
    avatar_url: Optional[str]


class FeishuBotRelationship(BaseModel):
    """飞书机器人与用户关系验证结果"""
    is_owner: bool
    relationship_type: Optional[str] = None  # "owner", "admin", "member", None
    verified: bool
    verification_data: Dict[str, Any] = Field(default_factory=dict)


# ========== 访问授权 ==========

class AccessGrantCreate(BaseModel):
    """创建访问授权"""
    bot_id: UUID
    user_id: UUID
    access_type: ClaimType
    permissions: Dict[str, bool] = Field(default_factory=lambda: {
        "can_invoke": True,
        "can_view_logs": False,
        "can_modify_settings": False
    })
    valid_until: Optional[datetime] = None


class AccessGrantResponse(BaseModel):
    """访问授权响应"""
    id: UUID
    bot_id: UUID
    user_id: UUID
    access_type: ClaimType
    permissions: Dict[str, bool]
    valid_from: datetime
    valid_until: Optional[datetime]
    is_active: bool
    
    class Config:
        from_attributes = True


# ========== 通知 ==========

class NotificationCreate(BaseModel):
    """创建通知"""
    user_id: UUID
    title: str
    content: str
    notification_type: str  # "claim_request", "claim_approved", etc.
    related_bot_id: Optional[UUID] = None
    related_request_id: Optional[UUID] = None
    
    # 飞书通知配置
    feishu_notify: bool = True
    feishu_message_type: str = "interactive"  # "text", "interactive"


class NotificationResponse(BaseModel):
    """通知响应"""
    id: UUID
    user_id: UUID
    title: str
    content: str
    is_read: bool
    feishu_message_id: Optional[str]
    created_at: datetime
