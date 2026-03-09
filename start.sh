#!/bin/bash

echo "🚀 启动硅基印务局..."

# 启动Docker服务
docker-compose up -d

# 等待数据库启动
echo "⏳ 等待数据库启动..."
sleep 5

# 初始化数据库
echo "📦 初始化数据库..."
docker-compose exec -T backend python -m app.init_db

echo "✅ 启动完成！"
echo ""
echo "访问地址："
echo "  前端: http://localhost:7847"
echo "  API文档: http://localhost:9527/docs"
echo "  Flower监控: http://localhost:8527"
echo ""
echo "查看日志: docker-compose logs -f"
echo "停止服务: docker-compose down"
