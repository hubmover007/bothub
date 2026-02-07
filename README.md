# 🤖 BotHub - 机器人管理平台

公司内部 AI 机器人统一管理和协作平台

## 🌟 功能特性

### 已实现功能 ✅

**核心功能**:
- 🏛️ **机器人大厅** - 展示所有注册的机器人
- 🔍 **搜索和筛选** - 按名称、状态、能力筛选
- 📊 **机器人详情** - 查看完整的机器人信息
- 💓 **心跳检测** - 实时监控机器人在线状态
- 📝 **机器人注册** - API 支持机器人自动注册

**技术栈**:
- **后端**: FastAPI + PostgreSQL + SQLAlchemy
- **前端**: React 18 + TypeScript + Vite + Tailwind CSS
- **数据管理**: React Query (TanStack Query)
- **路由**: React Router v6
- **容器化**: Docker + Docker Compose

### 待开发功能 📋

**Phase 2**:
- 🔐 飞书 OAuth 登录
- 👥 用户权限管理
- 🔔 实时通知系统
- 📈 性能监控图表

**Phase 3**:
- 🤝 机器人间通信协议
- 🎨 机器人能力市场
- 📦 插件系统
- 🌐 多语言支持

---

## 🚀 快速开始

### 方式一：Docker Compose（推荐）

```bash
# 克隆项目
cd ~/clawd/projects/bothub

# 启动所有服务（数据库 + 后端 + 前端）
docker-compose up -d

# 查看日志
docker-compose logs -f

# 访问应用
# 前端: http://localhost:3000
# 后端 API: http://localhost:8000
# API 文档: http://localhost:8000/docs
```

### 方式二：本地开发

**后端**:
```bash
cd backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，设置 DATABASE_URL

# 启动服务
uvicorn app.main:app --reload

# API 运行在 http://localhost:8000
```

**前端**:
```bash
cd frontend

# 安装依赖
npm install

# 配置环境变量
cp .env .env.local
# 编辑 .env.local，设置 VITE_API_BASE_URL

# 启动开发服务器
npm run dev

# 前端运行在 http://localhost:5173
```

---

## 📡 API 文档

### 机器人注册

```bash
POST /api/v1/bots/register
Content-Type: application/json

{
  "bot_id": "xiaobai-bot",
  "bot_name": "小白",
  "owner_id": "ou_397a15637cc1e4e9e1d01751c3ee5469",
  "description": "阳光快乐的 AI 宠物狗",
  "capabilities": ["code", "cloud", "chat"],
  "endpoint": "https://bot.example.com/api",
  "version": "1.0.0"
}
```

### 心跳上报

```bash
POST /api/v1/bots/heartbeat
Content-Type: application/json

{
  "bot_id": "xiaobai-bot",
  "status": "online"
}
```

### 获取机器人列表

```bash
GET /api/v1/bots?status=online&skip=0&limit=20
```

### 获取机器人详情

```bash
GET /api/v1/bots/xiaobai-bot
```

完整 API 文档: http://localhost:8000/docs

---

## 🗂️ 项目结构

```
bothub/
├── backend/                # 后端 FastAPI 项目
│   ├── app/
│   │   ├── main.py        # 应用入口
│   │   ├── config.py      # 配置管理
│   │   ├── database.py    # 数据库连接
│   │   ├── models/        # 数据模型
│   │   ├── schemas/       # Pydantic 模型
│   │   ├── api/v1/        # API 路由
│   │   └── core/          # 核心功能（认证、依赖）
│   ├── tests/             # 测试
│   ├── requirements.txt   # Python 依赖
│   ├── Dockerfile         # Docker 镜像
│   └── .env.example       # 环境变量模板
├── frontend/              # 前端 React 项目
│   ├── src/
│   │   ├── pages/         # 页面组件
│   │   ├── components/    # 通用组件
│   │   ├── api/           # API 客户端
│   │   ├── types/         # TypeScript 类型
│   │   ├── utils/         # 工具函数
│   │   ├── App.tsx        # 应用根组件
│   │   └── main.tsx       # 入口文件
│   ├── package.json       # Node 依赖
│   ├── Dockerfile         # Docker 镜像
│   └── .env               # 环境变量
├── docker-compose.yml     # Docker Compose 配置
├── ARCHITECTURE.md        # 架构文档
└── README.md              # 本文件
```

---

## 🛠️ 开发指南

### 添加新的 API 端点

1. 在 `backend/app/schemas/` 创建 Pydantic 模型
2. 在 `backend/app/api/v1/` 创建路由
3. 在 `backend/app/main.py` 注册路由

### 添加新的前端页面

1. 在 `frontend/src/pages/` 创建页面组件
2. 在 `frontend/src/App.tsx` 添加路由
3. 在导航栏添加链接（如需要）

### 数据库迁移

```bash
# 如果数据模型有变化，需要重新创建表
docker-compose down -v  # 删除数据卷
docker-compose up -d    # 重新启动
```

---

## 🚀 部署到阿里云 ECS

### 准备工作

1. 确保 ECS 实例已安装 Docker 和 Docker Compose
2. 配置安全组开放端口：80, 443, 8000, 3000
3. 配置域名解析（可选）

### 部署步骤

```bash
# 1. 连接到 ECS
ssh -i openclaw-ali-xjp.pem root@43.106.14.55

# 2. 克隆或上传项目
git clone <repository_url>
cd bothub

# 3. 配置生产环境变量
cp backend/.env.example backend/.env
vim backend/.env  # 修改数据库密码、SECRET_KEY 等

# 4. 启动服务
docker-compose up -d

# 5. 配置 Nginx 反向代理（可选）
# 将前端和后端统一到 80 端口
```

### Nginx 配置示例

```nginx
server {
    listen 80;
    server_name bothub.example.com;

    # 前端
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # 后端 API
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # API 文档
    location /docs {
        proxy_pass http://localhost:8000;
    }
}
```

---

## 🔒 安全建议

1. **生产环境**:
   - 修改 `backend/.env` 中的 `SECRET_KEY`
   - 修改数据库密码
   - 设置 `DEBUG=false`
   - 使用 HTTPS

2. **数据库**:
   - 定期备份
   - 不要暴露到公网
   - 使用强密码

3. **认证**:
   - 实现飞书 OAuth 登录
   - 使用 JWT Token
   - 设置合理的过期时间

---

## 📊 监控和日志

```bash
# 查看所有服务状态
docker-compose ps

# 查看后端日志
docker-compose logs -f backend

# 查看前端日志
docker-compose logs -f frontend

# 查看数据库日志
docker-compose logs -f postgres

# 进入容器
docker-compose exec backend bash
docker-compose exec postgres psql -U bothub
```

---

## 🐛 常见问题

### 前端无法连接后端

检查 `.env` 中的 `VITE_API_BASE_URL` 是否正确。

### 数据库连接失败

1. 确保 PostgreSQL 服务已启动
2. 检查 `DATABASE_URL` 配置
3. 查看数据库日志：`docker-compose logs postgres`

### 端口被占用

修改 `docker-compose.yml` 中的端口映射。

---

## 📝 更新日志

### v1.0.0 (2026-02-07)

**已完成**:
- ✅ 后端 API 框架（FastAPI）
- ✅ 数据库模型（PostgreSQL + SQLAlchemy）
- ✅ 前端框架（React + TypeScript + Vite）
- ✅ 机器人大厅页面
- ✅ 机器人详情页面
- ✅ API 客户端封装
- ✅ Docker 容器化
- ✅ Docker Compose 编排

**待完善**:
- 🔄 飞书 OAuth 登录
- 🔄 权限管理系统
- 🔄 实时监控图表
- 🔄 机器人通信协议

---

## 👥 贡献者

- **小白** (AI Assistant) - 项目开发
- **张云飞** - 产品需求和指导

---

## 📄 许可证

内部项目，版权所有 © 2026
