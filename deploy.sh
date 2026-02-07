#!/bin/bash
# BotHub 一键部署脚本
# 在新创建的 ECS 实例上运行此脚本

set -e

INSTANCE_IP="43.106.2.121"
GITHUB_REPO="https://github.com/hubmover007/bothub.git"

echo "🚀 BotHub 一键部署脚本"
echo "========================"
echo "实例IP: $INSTANCE_IP"
echo ""

# 1. 更新系统
echo "📦 [1/8] 更新系统..."
apt-get update -qq

# 2. 安装必要工具
echo "🔧 [2/8] 安装基础工具..."
apt-get install -y -qq git curl wget

# 3. 安装 Docker
echo "🐳 [3/8] 安装 Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com | sh
    systemctl enable docker
    systemctl start docker
fi

# 4. 安装 Docker Compose
echo "📦 [4/8] 安装 Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep 'tag_name' | cut -d\" -f4)
    curl -L "https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

# 5. 克隆项目
echo "📥 [5/8] 克隆 BotHub 项目..."
cd /root
if [ -d "bothub" ]; then
    echo "⚠️  项目目录已存在，拉取最新代码..."
    cd bothub
    git pull
else
    git clone $GITHUB_REPO
    cd bothub
fi

# 6. 配置后端环境变量
echo "⚙️  [6/8] 配置后端环境变量..."
cd backend
cat > .env << 'EOF'
DATABASE_URL=postgresql://bothub:bothub_secure_2026@postgres:5432/bothub
SECRET_KEY=bothub-production-secret-key-2026-change-me
CORS_ORIGINS=http://43.106.2.121:3000,http://43.106.2.121,http://localhost:3000
DEBUG=false
APP_NAME=BotHub API
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
EOF

# 7. 配置前端环境变量
echo "⚙️  [7/8] 配置前端环境变量..."
cd ../frontend
cat > .env << 'EOF'
VITE_API_BASE_URL=http://43.106.2.121:8000
EOF

# 8. 启动所有服务
echo "🚀 [8/8] 启动 Docker 服务..."
cd ..
docker-compose down 2>/dev/null || true
docker-compose up -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 15

# 检查状态
echo ""
echo "📊 服务状态："
docker-compose ps

# 检查数据库
echo ""
echo "🔍 检查数据库连接..."
docker-compose exec -T backend python -c "from app.database import engine; engine.connect(); print('✅ 数据库连接成功')" 2>/dev/null || echo "⚠️  数据库启动中，请稍后..."

echo ""
echo "🎉 部署完成！"
echo "============================================"
echo "📱 访问地址："
echo "  🌐 前端: http://43.106.2.121:3000"
echo "  🔌 后端: http://43.106.2.121:8000"
echo "  📖 API文档: http://43.106.2.121:8000/docs"
echo "============================================"
echo ""
echo "💡 常用命令："
echo "  查看日志: docker-compose logs -f"
echo "  重启服务: docker-compose restart"
echo "  停止服务: docker-compose down"
echo "  查看状态: docker-compose ps"
echo ""
echo "✅ BotHub 已成功部署！"
