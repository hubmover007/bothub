# BotHub 后端开发任务

## 目标
创建完整的 FastAPI 后端项目，包括数据库模型、API 路由、认证系统。

## 项目结构
创建以下目录和文件：

```
backend/
├── requirements.txt
├── .env.example
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── bot.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── bot.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       └── bots.py
│   └── core/
│       ├── __init__.py
│       ├── security.py
│       └── deps.py
└── tests/
    ├── __init__.py
    └── test_bots.py
```

## 实现要求

### 1. requirements.txt
```
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
pydantic==2.5.0
pydantic-settings==2.1.0
python-jose[cryptography]==3.3.0
python-multipart==0.0.6
```

### 2. app/config.py
- 使用 pydantic-settings 管理配置
- 从环境变量读取 DATABASE_URL, SECRET_KEY 等

### 3. app/database.py
- SQLAlchemy engine 和 session
- Base 模型

### 4. app/models/bot.py
机器人模型，字段：
- id (UUID, primary key)
- bot_id (String, unique)
- bot_name (String)
- owner_id (UUID)
- description (Text, nullable)
- status (String, default='offline')
- capabilities (JSON)
- endpoint (String, nullable)
- version (String, nullable)
- created_at, updated_at, last_heartbeat_at (DateTime)

### 5. app/schemas/bot.py
Pydantic 模型：
- BotCreate
- BotUpdate  
- BotHeartbeat
- BotResponse

### 6. app/api/v1/bots.py
API 路由：
- POST /api/v1/bots/register - 注册机器人
- POST /api/v1/bots/heartbeat - 心跳上报
- GET /api/v1/bots - 获取列表（支持分页和过滤）
- GET /api/v1/bots/{bot_id} - 获取详情

### 7. app/main.py
- 创建 FastAPI app
- CORS 配置
- 路由注册
- 健康检查端点 GET /health

### 8. .env.example
环境变量模板

### 9. tests/test_bots.py
基本的 pytest 测试用例

请创建所有这些文件，确保代码完整可运行。
