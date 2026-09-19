#!/bin/bash

# MySQL Docker 启动脚本

echo "正在启动 MySQL Docker 容器..."

# 检查 Docker 是否运行
if ! docker info > /dev/null 2>&1; then
    echo "错误: Docker 未运行，请先启动 Docker"
    exit 1
fi

# 启动容器
docker compose -p eaihub -f docker-compose.yml up -d

# 等待 MySQL 启动
echo "等待 MySQL 启动..."
sleep 10

# 检查容器状态
if docker ps | grep -q eaihub_mysql; then
    echo "✓ MySQL 容器启动成功！"
    echo ""
    echo "连接信息:"
    echo "  主机: localhost"
    echo "  端口: 5456"
    echo "  数据库: eaihub"
    echo "  用户: root"
    echo "  密码: 你的数据库密码"
    echo ""
    echo "停止容器: docker compose -p eaihub -f docker-compose.yml down"
    echo "查看日志: docker compose -p eaihub -f docker-compose.yml logs -f mysql"
else
    echo "✗ MySQL 容器启动失败，请检查日志"
    docker compose -p eaihub -f docker-compose.yml logs mysql
    exit 1
fi

