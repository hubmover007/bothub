"""
飞书 OAuth 和验证服务
"""

import requests
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from app.schemas.claim import FeishuUserInfo, FeishuBotRelationship


class FeishuService:
    """飞书服务封装"""
    
    def __init__(self, app_id: str, app_secret: str):
        self.app_id = app_id
        self.app_secret = app_secret
        self.base_url = "https://open.feishu.cn/open-api"
        self._access_token = None
        self._token_expires_at = None
    
    def get_access_token(self) -> str:
        """获取 tenant_access_token"""
        # 如果token还有效，直接返回
        if self._access_token and self._token_expires_at:
            if datetime.utcnow() < self._token_expires_at:
                return self._access_token
        
        # 获取新token
        url = f"{self.base_url}/auth/v3/tenant_access_token/internal"
        payload = {
            "app_id": self.app_id,
            "app_secret": self.app_secret
        }
        
        response = requests.post(url, json=payload)
        response.raise_for_status()
        
        data = response.json()
        if data.get("code") != 0:
            raise Exception(f"获取access_token失败: {data.get('msg')}")
        
        self._access_token = data["tenant_access_token"]
        # token有效期2小时，提前5分钟刷新
        self._token_expires_at = datetime.utcnow() + timedelta(seconds=data["expire"] - 300)
        
        return self._access_token
    
    def get_user_info_by_code(self, code: str) -> FeishuUserInfo:
        """通过OAuth code获取用户信息"""
        # 1. 用code换取user_access_token
        token_url = f"{self.base_url}/authen/v1/access_token"
        token_payload = {
            "grant_type": "authorization_code",
            "code": code
        }
        
        token_response = requests.post(token_url, json=token_payload)
        token_response.raise_for_status()
        
        token_data = token_response.json()
        if token_data.get("code") != 0:
            raise Exception(f"换取user_access_token失败: {token_data.get('msg')}")
        
        user_access_token = token_data["data"]["access_token"]
        
        # 2. 用user_access_token获取用户信息
        user_url = f"{self.base_url}/authen/v1/user_info"
        headers = {
            "Authorization": f"Bearer {user_access_token}"
        }
        
        user_response = requests.get(user_url, headers=headers)
        user_response.raise_for_status()
        
        user_data = user_response.json()
        if user_data.get("code") != 0:
            raise Exception(f"获取用户信息失败: {user_data.get('msg')}")
        
        data = user_data["data"]
        return FeishuUserInfo(
            user_id=data["user_id"],
            open_id=data["open_id"],
            name=data.get("name", ""),
            email=data.get("email"),
            avatar_url=data.get("avatar_url")
        )
    
    def verify_bot_relationship(
        self,
        bot_app_id: str,
        user_id: str
    ) -> FeishuBotRelationship:
        """
        验证用户与机器人的关系
        检查用户是否是该飞书应用的所有者/管理员
        """
        access_token = self.get_access_token()
        
        # 获取应用信息
        app_url = f"{self.base_url}/application/v6/applications/{bot_app_id}"
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        
        try:
            app_response = requests.get(app_url, headers=headers)
            app_response.raise_for_status()
            
            app_data = app_response.json()
            if app_data.get("code") != 0:
                return FeishuBotRelationship(
                    is_owner=False,
                    verified=False,
                    verification_data={"error": app_data.get("msg")}
                )
            
            app_info = app_data["data"]["app"]
            
            # 检查是否是应用创建者
            creator_id = app_info.get("creator", {}).get("user_id")
            owner_id = app_info.get("owner", {}).get("user_id")
            
            is_owner = user_id in [creator_id, owner_id]
            
            # 检查是否是管理员
            admins_url = f"{self.base_url}/application/v6/applications/{bot_app_id}/app_admin_user_list"
            admins_response = requests.get(admins_url, headers=headers)
            
            is_admin = False
            if admins_response.status_code == 200:
                admins_data = admins_response.json()
                if admins_data.get("code") == 0:
                    admin_list = admins_data.get("data", {}).get("user_list", [])
                    is_admin = any(admin.get("user_id") == user_id for admin in admin_list)
            
            relationship_type = None
            if is_owner:
                relationship_type = "owner"
            elif is_admin:
                relationship_type = "admin"
            
            return FeishuBotRelationship(
                is_owner=is_owner or is_admin,  # 管理员也算"所有者"
                relationship_type=relationship_type,
                verified=True,
                verification_data={
                    "app_id": bot_app_id,
                    "app_name": app_info.get("app_name"),
                    "creator_id": creator_id,
                    "owner_id": owner_id,
                    "is_admin": is_admin
                }
            )
        
        except Exception as e:
            return FeishuBotRelationship(
                is_owner=False,
                verified=False,
                verification_data={"error": str(e)}
            )
    
    def send_message(
        self,
        receive_id: str,
        msg_type: str,
        content: Dict[str, Any],
        receive_id_type: str = "user_id"
    ) -> Optional[str]:
        """
        发送飞书消息
        
        Args:
            receive_id: 接收者ID（user_id, open_id, chat_id等）
            msg_type: 消息类型（text, interactive等）
            content: 消息内容
            receive_id_type: ID类型
        
        Returns:
            message_id: 消息ID
        """
        access_token = self.get_access_token()
        
        url = f"{self.base_url}/im/v1/messages"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        params = {
            "receive_id_type": receive_id_type
        }
        payload = {
            "receive_id": receive_id,
            "msg_type": msg_type,
            "content": content if isinstance(content, str) else str(content)
        }
        
        try:
            response = requests.post(url, headers=headers, params=params, json=payload)
            response.raise_for_status()
            
            data = response.json()
            if data.get("code") == 0:
                return data.get("data", {}).get("message_id")
            else:
                print(f"发送消息失败: {data.get('msg')}")
                return None
        
        except Exception as e:
            print(f"发送消息异常: {e}")
            return None
    
    def send_interactive_card(
        self,
        receive_id: str,
        card: Dict[str, Any],
        receive_id_type: str = "user_id"
    ) -> Optional[str]:
        """发送飞书交互式卡片"""
        import json
        
        content = json.dumps(card, ensure_ascii=False)
        return self.send_message(
            receive_id=receive_id,
            msg_type="interactive",
            content=content,
            receive_id_type=receive_id_type
        )


# 创建全局飞书服务实例（需要从配置读取）
def get_feishu_service(app_id: Optional[str] = None, app_secret: Optional[str] = None):
    """获取飞书服务实例"""
    from app.config import settings
    
    app_id = app_id or settings.FEISHU_APP_ID
    app_secret = app_secret or settings.FEISHU_APP_SECRET
    
    return FeishuService(app_id, app_secret)
