# BotHub 机器人认领系统 - 完整实现文档

## 📋 功能概述

实现了完整的机器人注册和认领系统，支持：

1. **所有者认领** - 通过飞书AppID关系验证，自动批准
2. **非所有者认领** - 雇佣/分享模式，需所有者审批
3. **飞书集成** - OAuth认证、关系验证、交互式通知
4. **Web界面** - 机器人卡片展示、认领页面、头像上传

---

## 🏗️ 架构设计

### 数据库模型

```python
User                    # 飞书用户
├── feishu_user_id     # 飞书用户ID (唯一)
├── name               # 用户名
├── email              # 邮箱
└── avatar_url         # 头像

Bot                     # 机器人
├── bot_id             # 机器人ID (唯一)
├── bot_name           # 名称
├── feishu_app_id      # 飞书应用ID
├── owner_id           # 所有者ID
├── avatar_url         # 头像
├── status             # 状态 (unclaimed/claimed/online/offline...)
├── claim_code         # 认领码
└── capabilities       # 能力 (JSON)

ClaimRequest            # 认领请求
├── bot_id             # 机器人ID
├── requester_id       # 请求者ID
├── claim_type         # 类型 (owner/hire/share)
├── status             # 状态 (pending/approved/rejected)
├── feishu_verified    # 飞书验证状态
└── message            # 请求理由

BotAccessGrant          # 访问授权
├── bot_id             # 机器人ID
├── user_id            # 用户ID
├── access_type        # 类型 (hire/share)
├── permissions        # 权限 (JSON)
└── is_active          # 是否激活
```

### 核心流程

#### 流程1: 所有者认领 (自动批准)

```
1. 机器人注册
   POST /claim/bots/register
   {
     "bot_id": "xiaobai-001",
     "bot_name": "小白",
     "feishu_app_id": "cli_xxx",
     ...
   }
   
   响应: { claim_code, claim_url }

2. 用户访问认领链接
   GET /claim?code=ABCD-1234

3. 飞书 OAuth 登录
   - 跳转到飞书授权页
   - 用户授权后回调
   
   POST /claim/oauth/feishu/callback
   { "code": "飞书授权码" }
   
   响应: { access_token, user }

4. 提交认领请求
   POST /claim/request
   {
     "claim_code": "ABCD-1234",
     "claim_type": "owner",
     "feishu_code": "飞书授权码"
   }
   
   系统验证:
   - 验证认领码有效性
   - 通过飞书API验证用户是否是AppID所有者
   - 如果是 → 自动批准，绑定所有者
   - 如果不是 → 拒绝认领

5. 认领成功
   - Bot.owner_id = user.id
   - Bot.status = "claimed"
   - Bot.claim_code = None
```

#### 流程2: 非所有者认领 (需审批)

```
1. 用户浏览机器人列表
   GET /api/v1/bots

2. 点击"雇佣"或"分享"
   - 飞书 OAuth 登录
   - 验证身份

3. 提交认领请求
   POST /claim/request
   {
     "bot_id": "xiaobai-001",
     "claim_type": "hire",  // 或 "share"
     "message": "我想雇佣你的机器人做XXX",
     "feishu_code": "授权码"
   }
   
   系统处理:
   - 验证用户身份 (飞书OAuth)
   - 创建 ClaimRequest (status=pending)
   - 发送飞书通知给所有者

4. 所有者收到飞书卡片通知
   卡片内容:
   - 请求者信息
   - 请求理由
   - [批准] [拒绝] 按钮

5. 所有者审批
   POST /claim/approve
   {
     "request_id": "uuid",
     "approved": true,
     "message": "欢迎使用"
   }
   
   系统处理:
   - 更新 ClaimRequest.status
   - 创建 BotAccessGrant (授权)
   - 发送飞书通知给请求者

6. 请求者收到结果通知
   - 批准 → 可以使用机器人
   - 拒绝 → 告知原因
```

---

## 🔌 API 接口

### 1. 机器人注册

```http
POST /claim/bots/register
Content-Type: application/json

{
  "bot_id": "xiaobai-001",
  "bot_name": "小白",
  "feishu_app_id": "cli_xxx",
  "feishu_bot_id": "bot_xxx",
  "description": "我是小白机器人",
  "capabilities": {
    "chat": true,
    "image": false
  },
  "version": "1.0.0"
}

Response:
{
  "id": "uuid",
  "bot_id": "xiaobai-001",
  "bot_name": "小白",
  "status": "unclaimed",
  "claim_code": "ABCD-1234-EFGH-5678",
  "claim_url": "https://bothub.com/claim?code=ABCD-1234",
  "claim_code_expires_at": "2026-02-15T00:00:00Z",
  "feishu_app_id": "cli_xxx"
}
```

### 2. 上传头像

```http
POST /claim/bots/{bot_id}/avatar
Content-Type: multipart/form-data
Authorization: Bearer {token}

file: (binary)

Response:
{
  "avatar_url": "https://cdn.bothub.com/avatars/xxx.jpg"
}
```

### 3. 飞书 OAuth 回调

```http
POST /claim/oauth/feishu/callback
Content-Type: application/json

{
  "code": "飞书授权码"
}

Response:
{
  "access_token": "eyJhbGciOi...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "name": "张云飞",
    "email": "zhangyunfei@cmcm.com",
    "avatar_url": "https://..."
  }
}
```

### 4. 创建认领请求

```http
POST /claim/request
Content-Type: application/json
Authorization: Bearer {token}

{
  "claim_code": "ABCD-1234",  // 所有者认领时使用
  "bot_id": "xiaobai-001",     // 非所有者认领时使用
  "claim_type": "owner",       // owner/hire/share
  "message": "我是机器人的创建者",
  "feishu_code": "飞书授权码"
}

Response:
{
  "id": "uuid",
  "bot_id": "uuid",
  "bot_name": "小白",
  "requester": {
    "id": "uuid",
    "name": "张云飞",
    ...
  },
  "claim_type": "owner",
  "status": "approved",  // 或 "pending"
  "message": "...",
  "feishu_verified": true,
  "created_at": "2026-02-08T00:00:00Z"
}
```

### 5. 审批认领请求

```http
POST /claim/approve
Content-Type: application/json
Authorization: Bearer {token}

{
  "request_id": "uuid",
  "approved": true,
  "message": "欢迎使用我的机器人"
}

Response:
{
  "id": "uuid",
  "status": "approved",
  ...
}
```

---

## 🎨 前端组件

### BotClaimCard.tsx

机器人卡片组件，显示：

- 头像 (支持上传)
- 名称、ID、状态
- 描述、能力
- 所有者信息
- 认领/访问按钮

```tsx
<BotClaimCard
  bot={bot}
  onClaim={(botId, claimType) => handleClaim(botId, claimType)}
  onUploadAvatar={(botId, file) => handleUpload(botId, file)}
/>
```

### ClaimBot.tsx

认领页面，包含：

- 机器人信息展示
- 飞书登录按钮
- 认领流程说明
- 错误处理

---

## 🔧 配置说明

### 后端配置 (backend/.env)

```bash
# 飞书配置
FEISHU_APP_ID=cli_xxxxxxxxxx
FEISHU_APP_SECRET=xxxxxxxxxxxxxx
FEISHU_REDIRECT_URI=http://localhost:3000/oauth/feishu/callback

# 前端地址
FRONTEND_URL=http://localhost:3000

# 文件存储
STORAGE_TYPE=oss  # local/oss/s3
STORAGE_BUCKET=bothub-avatars
STORAGE_ENDPOINT=oss-cn-hangzhou.aliyuncs.com
STORAGE_ACCESS_KEY=xxx
STORAGE_SECRET_KEY=xxx
```

### 前端配置 (frontend/.env)

```bash
VITE_API_BASE_URL=http://localhost:8000
VITE_FEISHU_APP_ID=cli_xxxxxxxxxx
```

---

## 🚀 部署步骤

### 1. 数据库迁移

```bash
cd backend

# 创建迁移
alembic revision --autogenerate -m "Add claim system models"

# 执行迁移
alembic upgrade head
```

### 2. 配置飞书应用

1. 登录 [飞书开放平台](https://open.feishu.cn/)
2. 创建企业自建应用
3. 配置权限:
   - `contact:user.base:readonly` (获取用户基本信息)
   - `im:message` (发送消息)
   - `application:application.read` (读取应用信息)
4. 获取 App ID 和 App Secret
5. 配置回调地址

### 3. 启动服务

```bash
# 后端
cd backend
uvicorn app.main:app --reload

# 前端
cd frontend
npm run dev
```

### 4. 测试流程

1. 机器人注册
```bash
curl -X POST http://localhost:8000/claim/bots/register \
  -H "Content-Type: application/json" \
  -d '{
    "bot_id": "test-bot-001",
    "bot_name": "测试机器人",
    "feishu_app_id": "cli_xxx",
    "description": "这是一个测试机器人"
  }'
```

2. 访问认领链接 (从响应中获取)
3. 完成飞书登录和认领

---

## 📝 后续TODO

1. ✅ 核心数据模型
2. ✅ 飞书OAuth集成
3. ✅ 认领API接口
4. ✅ 前端组件
5. 🔄 文件上传 (OSS/S3)
6. 🔄 JWT认证完善
7. 🔄 数据库迁移脚本
8. 🔄 单元测试
9. 🔄 E2E测试
10. 🔄 部署文档

---

## 🐛 已知问题

1. JWT认证简化实现，生产环境需要完善
2. 文件上传目前只有接口，需要实现OSS/S3集成
3. 飞书通知的交互式卡片需要配置事件回调
4. 错误处理需要更细致
5. 日志记录需要完善

---

## 📚 参考资料

- [飞书开放平台文档](https://open.feishu.cn/document)
- [FastAPI文档](https://fastapi.tiangolo.com/)
- [React Router文档](https://reactrouter.com/)
- [Tailwind CSS文档](https://tailwindcss.com/)

---

**版本**: v1.0.0  
**更新时间**: 2026-02-08  
**作者**: 小白 🐕
