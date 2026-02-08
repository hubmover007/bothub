"""
BotHub 认领系统 - API 路由
完整的机器人注册、认领、审批流程
"""

import secrets
from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database import get_db
from app.models.bot import Bot, BotStatus
from app.models.claim import (
    User, ClaimRequest, BotAccessGrant,
    ClaimType, ClaimStatus
)
from app.schemas.claim import (
    BotRegister, BotRegisterResponse, BotCard, BotUpdate,
    ClaimRequestCreate, ClaimRequestResponse, ClaimApproval,
    FeishuOAuthCallback, AccessGrantCreate, AccessGrantResponse,
    NotificationCreate
)
from app.services.feishu import get_feishu_service
from app.core.deps import get_current_user, get_current_user_optional

router = APIRouter(prefix="/claim", tags=["claim"])


# ========== 机器人注册 ==========

@router.post("/bots/register", response_model=BotRegisterResponse)
def register_bot(
    bot_data: BotRegister,
    db: Session = Depends(get_db)
):
    """
    机器人自注册
    
    生成唯一的认领码，机器人状态为 unclaimed
    """
    # 检查bot_id是否已存在
    existing = db.query(Bot).filter(Bot.bot_id == bot_data.bot_id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Bot ID '{bot_data.bot_id}' already exists"
        )
    
    # 生成认领码（20字符，URL安全）
    claim_code = secrets.token_urlsafe(15)
    
    # 创建机器人
    new_bot = Bot(
        bot_id=bot_data.bot_id,
        bot_name=bot_data.bot_name,
        feishu_app_id=bot_data.feishu_app_id,
        feishu_bot_id=bot_data.feishu_bot_id,
        description=bot_data.description,
        capabilities=bot_data.capabilities,
        endpoint=bot_data.endpoint,
        version=bot_data.version,
        status=BotStatus.UNCLAIMED,
        claim_code=claim_code,
        claim_code_expires_at=datetime.utcnow() + timedelta(days=7)  # 7天有效期
    )
    
    db.add(new_bot)
    db.commit()
    db.refresh(new_bot)
    
    # 构造认领URL
    from app.config import settings
    claim_url = f"{settings.FRONTEND_URL}/claim?code={claim_code}"
    
    return BotRegisterResponse(
        id=new_bot.id,
        bot_id=new_bot.bot_id,
        bot_name=new_bot.bot_name,
        status=new_bot.status,
        claim_code=claim_code,
        claim_url=claim_url,
        claim_code_expires_at=new_bot.claim_code_expires_at,
        feishu_app_id=new_bot.feishu_app_id
    )


@router.post("/bots/{bot_id}/avatar")
async def upload_bot_avatar(
    bot_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """上传机器人头像"""
    bot = db.query(Bot).filter(Bot.bot_id == bot_id).first()
    if not bot:
        raise HTTPException(404, "Bot not found")
    
    # 只有所有者可以上传
    if bot.owner_id != current_user.id:
        raise HTTPException(403, "Only owner can upload avatar")
    
    # TODO: 保存文件到OSS/S3
    # 这里简化处理，实际应该上传到云存储
    filename = f"avatars/{bot.id}_{file.filename}"
    avatar_url = f"https://cdn.bothub.com/{filename}"
    
    bot.avatar_url = avatar_url
    db.commit()
    
    return {"avatar_url": avatar_url}


# ========== 飞书 OAuth ==========

@router.post("/oauth/feishu/callback")
def feishu_oauth_callback(
    callback: FeishuOAuthCallback,
    db: Session = Depends(get_db)
):
    """
    飞书 OAuth 回调
    
    用code换取用户信息，创建或更新用户
    """
    feishu = get_feishu_service()
    
    try:
        # 获取用户信息
        user_info = feishu.get_user_info_by_code(callback.code)
        
        # 查找或创建用户
        user = db.query(User).filter(
            User.feishu_user_id == user_info.user_id
        ).first()
        
        if not user:
            user = User(
                feishu_user_id=user_info.user_id,
                feishu_open_id=user_info.open_id,
                name=user_info.name,
                email=user_info.email,
                avatar_url=user_info.avatar_url
            )
            db.add(user)
        else:
            # 更新用户信息
            user.name = user_info.name
            user.email = user_info.email
            user.avatar_url = user_info.avatar_url
            user.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(user)
        
        # 生成JWT token（这里简化，实际应该用JWT）
        access_token = secrets.token_urlsafe(32)
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": str(user.id),
                "name": user.name,
                "email": user.email,
                "avatar_url": user.avatar_url
            }
        }
    
    except Exception as e:
        raise HTTPException(500, f"OAuth failed: {str(e)}")


# ========== 认领流程 ==========

@router.post("/request", response_model=ClaimRequestResponse)
def create_claim_request(
    claim_data: ClaimRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    创建认领请求
    
    - 所有者认领：使用claim_code
    - 非所有者认领：使用bot_id + claim_type (hire/share)
    """
    feishu = get_feishu_service()
    
    # 1. 获取用户的飞书信息（通过OAuth已验证）
    user_info = feishu.get_user_info_by_code(claim_data.feishu_code)
    
    # 2. 查找机器人
    if claim_data.claim_code:
        # 使用认领码（所有者认领）
        bot = db.query(Bot).filter(
            Bot.claim_code == claim_data.claim_code,
            Bot.status == BotStatus.UNCLAIMED
        ).first()
        
        if not bot:
            raise HTTPException(404, "Invalid or expired claim code")
        
        # 检查认领码是否过期
        if bot.claim_code_expires_at < datetime.utcnow():
            raise HTTPException(400, "Claim code expired")
        
        claim_type = ClaimType.OWNER
    
    elif claim_data.bot_id:
        # 使用bot_id（非所有者认领）
        bot = db.query(Bot).filter(Bot.bot_id == claim_data.bot_id).first()
        
        if not bot:
            raise HTTPException(404, "Bot not found")
        
        if bot.status == BotStatus.UNCLAIMED:
            raise HTTPException(400, "Bot must be claimed by owner first")
        
        claim_type = claim_data.claim_type
        
        if claim_type == ClaimType.OWNER:
            raise HTTPException(400, "Cannot claim as owner without claim code")
    
    else:
        raise HTTPException(400, "Must provide claim_code or bot_id")
    
    # 3. 飞书关系验证
    if bot.feishu_app_id:
        relationship = feishu.verify_bot_relationship(
            bot_app_id=bot.feishu_app_id,
            user_id=user_info.user_id
        )
        
        feishu_verified = relationship.verified
        feishu_verification_data = relationship.verification_data
        
        # 如果是所有者认领，必须验证关系
        if claim_type == ClaimType.OWNER and not relationship.is_owner:
            raise HTTPException(
                403,
                "You are not the owner of this Feishu bot app"
            )
    else:
        # 机器人没有绑定飞书App，跳过验证
        feishu_verified = True
        feishu_verification_data = {"note": "No Feishu App ID provided"}
    
    # 4. 创建认领请求
    claim_request = ClaimRequest(
        bot_id=bot.id,
        requester_id=current_user.id,
        claim_type=claim_type,
        message=claim_data.message,
        feishu_verified=feishu_verified,
        feishu_verification_data=feishu_verification_data,
        status=ClaimStatus.PENDING if claim_type != ClaimType.OWNER else ClaimStatus.APPROVED,
        expires_at=datetime.utcnow() + timedelta(days=30)
    )
    
    db.add(claim_request)
    
    # 5. 如果是所有者认领，直接批准
    if claim_type == ClaimType.OWNER:
        bot.owner_id = current_user.id
        bot.status = BotStatus.CLAIMED
        bot.claimed_at = datetime.utcnow()
        bot.claim_code = None  # 清除认领码
        claim_request.status = ClaimStatus.APPROVED
        claim_request.approved_at = datetime.utcnow()
        claim_request.approved_by = current_user.id
    else:
        # 非所有者认领，通知所有者
        send_claim_notification(bot, claim_request, db)
    
    db.commit()
    db.refresh(claim_request)
    
    return ClaimRequestResponse(
        id=claim_request.id,
        bot_id=claim_request.bot_id,
        bot_name=bot.bot_name,
        requester=current_user,
        claim_type=claim_request.claim_type,
        status=claim_request.status,
        message=claim_request.message,
        feishu_verified=claim_request.feishu_verified,
        created_at=claim_request.created_at
    )


@router.post("/approve", response_model=ClaimRequestResponse)
def approve_claim_request(
    approval: ClaimApproval,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    批准或拒绝认领请求
    
    只有机器人所有者可以批准
    """
    claim_request = db.query(ClaimRequest).filter(
        ClaimRequest.id == approval.request_id
    ).first()
    
    if not claim_request:
        raise HTTPException(404, "Claim request not found")
    
    bot = db.query(Bot).filter(Bot.id == claim_request.bot_id).first()
    
    # 检查权限：只有所有者可以批准
    if bot.owner_id != current_user.id:
        raise HTTPException(403, "Only bot owner can approve claim requests")
    
    # 检查状态
    if claim_request.status != ClaimStatus.PENDING:
        raise HTTPException(400, f"Request is already {claim_request.status.value}")
    
    # 更新状态
    if approval.approved:
        claim_request.status = ClaimStatus.APPROVED
        claim_request.approved_at = datetime.utcnow()
        claim_request.approved_by = current_user.id
        claim_request.approval_message = approval.message
        
        # 创建访问授权
        access_grant = BotAccessGrant(
            bot_id=bot.id,
            user_id=claim_request.requester_id,
            access_type=claim_request.claim_type,
            permissions={
                "can_invoke": True,
                "can_view_logs": claim_request.claim_type == ClaimType.HIRE,
                "can_modify_settings": False
            },
            is_active=True
        )
        db.add(access_grant)
        
        # 通知请求者
        send_approval_notification(bot, claim_request, True, db)
    else:
        claim_request.status = ClaimStatus.REJECTED
        claim_request.approval_message = approval.message
        
        # 通知请求者
        send_approval_notification(bot, claim_request, False, db)
    
    db.commit()
    db.refresh(claim_request)
    
    return ClaimRequestResponse(
        id=claim_request.id,
        bot_id=claim_request.bot_id,
        bot_name=bot.bot_name,
        requester=claim_request.requester,
        claim_type=claim_request.claim_type,
        status=claim_request.status,
        message=claim_request.message,
        feishu_verified=claim_request.feishu_verified,
        created_at=claim_request.created_at
    )


# ========== 通知系统 ==========

def send_claim_notification(bot: Bot, claim_request: ClaimRequest, db: Session):
    """发送认领请求通知给所有者"""
    if not bot.owner:
        return
    
    feishu = get_feishu_service()
    
    # 构造交互式卡片
    card = {
        "config": {
            "wide_screen_mode": True
        },
        "elements": [
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"**{claim_request.requester.name}** 请求{claim_request.claim_type.value}你的机器人 **{bot.bot_name}**"
                }
            },
            {
                "tag": "div",
                "text": {
                    "tag": "plain_text",
                    "content": f"理由：{claim_request.message or '无'}"
                }
            },
            {
                "tag": "action",
                "actions": [
                    {
                        "tag": "button",
                        "text": {
                            "tag": "plain_text",
                            "content": "批准"
                        },
                        "type": "primary",
                        "value": {
                            "request_id": str(claim_request.id),
                            "action": "approve"
                        }
                    },
                    {
                        "tag": "button",
                        "text": {
                            "tag": "plain_text",
                            "content": "拒绝"
                        },
                        "type": "danger",
                        "value": {
                            "request_id": str(claim_request.id),
                            "action": "reject"
                        }
                    }
                ]
            }
        ]
    }
    
    # 发送飞书消息
    message_id = feishu.send_interactive_card(
        receive_id=bot.owner.feishu_user_id,
        card=card,
        receive_id_type="user_id"
    )
    
    return message_id


def send_approval_notification(
    bot: Bot,
    claim_request: ClaimRequest,
    approved: bool,
    db: Session
):
    """发送审批结果通知"""
    feishu = get_feishu_service()
    
    status_text = "已批准" if approved else "已拒绝"
    color = "green" if approved else "red"
    
    card = {
        "config": {
            "wide_screen_mode": True
        },
        "header": {
            "title": {
                "tag": "plain_text",
                "content": f"认领请求{status_text}"
            },
            "template": color
        },
        "elements": [
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"你对机器人 **{bot.bot_name}** 的{claim_request.claim_type.value}请求{status_text}"
                }
            }
        ]
    }
    
    if claim_request.approval_message:
        card["elements"].append({
            "tag": "div",
            "text": {
                "tag": "plain_text",
                "content": f"回复：{claim_request.approval_message}"
            }
        })
    
    message_id = feishu.send_interactive_card(
        receive_id=claim_request.requester.feishu_user_id,
        card=card,
        receive_id_type="user_id"
    )
    
    return message_id
