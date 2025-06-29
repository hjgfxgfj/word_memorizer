#!/bin/bash

# 英语单词记忆系统 Windows Docker 运行脚本
# 支持 WSL2 和 Windows X11 服务器

echo "🪟 Windows 环境下的英语单词记忆系统启动脚本"

# 检测运行环境
if grep -qEi "(Microsoft|WSL)" /proc/version &> /dev/null; then
    echo "🐧 检测到 WSL2 环境"
    IS_WSL=true
elif [[ -n "$WSLENV" ]]; then
    echo "🐧 检测到 WSL 环境"
    IS_WSL=true
else
    echo "🪟 检测到 Windows 原生环境"
    IS_WSL=false
fi

# 检查Docker是否可用
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装或未启动"
    echo "📥 请安装 Docker Desktop for Windows"
    echo "🔗 下载地址: https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe"
    exit 1
fi

# 检查Docker是否运行
if ! docker info &> /dev/null; then
    echo "❌ Docker 未运行"
    echo "🚀 请启动 Docker Desktop"
    exit 1
fi

echo "✅ Docker 环境检查通过"

# 构建Docker镜像
echo "🔨 构建 Docker 镜像..."
docker build -t word-memorizer .

if [ $? -ne 0 ]; then
    echo "❌ Docker 镜像构建失败"
    exit 1
fi

# 根据环境设置不同的运行参数
if [ "$IS_WSL" = true ]; then
    echo "🐧 在 WSL2 环境中启动..."
    
    # 设置 WSL2 的 DISPLAY
    export DISPLAY=$(cat /etc/resolv.conf | grep nameserver | awk '{print $2}'):0
    
    echo "📺 DISPLAY 设置为: $DISPLAY"
    echo "⚠️  请确保在 Windows 中运行了 X11 服务器（如 VcXsrv）"
    echo "📋 VcXsrv 配置："
    echo "   - Display number: 0"
    echo "   - Start no client: ✓"
    echo "   - Disable access control: ✓"
    echo ""
    
    # WSL2 运行命令
    docker run -it --rm \
        --name word-memorizer \
        -e DISPLAY=$DISPLAY \
        -v "$(pwd)/data":/app/data \
        word-memorizer
        
else
    echo "🪟 在 Windows 原生环境中启动..."
    echo "⚠️  请确保已安装并启动 X11 服务器（VcXsrv 或 Xming）"
    
    # Windows 原生运行命令
    docker run -it --rm \
        --name word-memorizer \
        -e DISPLAY=host.docker.internal:0 \
        -v "$(pwd)/data":/app/data \
        word-memorizer
fi

echo "✅ 容器已停止"

# 显示帮助信息
echo ""
echo "📚 如果遇到 GUI 显示问题："
echo "1. 🔧 确保 X11 服务器正在运行"
echo "2. 🔓 检查防火墙设置，允许 Docker 连接"
echo "3. 🔄 重启 Docker Desktop"
echo "4. 📖 查看完整文档: DOCKER.md"