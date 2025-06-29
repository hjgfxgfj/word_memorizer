#!/bin/bash

# 英语单词记忆系统 Docker 运行脚本
# 支持 macOS 和 Linux 的 GUI 显示

echo "🚀 启动英语单词记忆系统 Docker 容器..."

# 检测操作系统
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    echo "📱 检测到 macOS 系统"
    
    # 检查XQuartz状态
    if ! command -v xhost &> /dev/null && ! [ -f "/opt/X11/bin/xhost" ]; then
        echo "❌ XQuartz 未安装"
        echo "📥 请运行: brew install --cask xquartz"
        echo "🔄 安装后需要注销重新登录"
        exit 1
    fi
    
    # 设置PATH包含XQuartz
    export PATH="/opt/X11/bin:$PATH"
    
    # 检查XQuartz是否运行
    if ! pgrep -f "Xquartz\|X11" > /dev/null; then
        echo "❌ XQuartz 未运行"
        echo "🚀 请启动 XQuartz:"
        echo "   1. 在应用程序/实用工具中找到 XQuartz"
        echo "   2. 启动 XQuartz"
        echo "   3. 在 XQuartz -> 偏好设置 -> 安全性 中:"
        echo "      ☑ 允许来自网络客户端的连接"
        echo "   4. 重新运行此脚本"
        exit 1
    fi
    
    echo "✅ XQuartz 正在运行"
    
    # 允许Docker访问X11
    xhost +localhost
    
    # 设置DISPLAY变量
    export DISPLAY=host.docker.internal:0
    
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    echo "🐧 检测到 Linux 系统"
    
    # 允许Docker访问X11
    xhost +local:docker
    
    # 设置DISPLAY变量
    export DISPLAY=${DISPLAY:-:0}
    
else
    echo "❌ 不支持的操作系统: $OSTYPE"
    echo "🔧 目前支持 macOS 和 Linux"
    exit 1
fi

# 构建Docker镜像
echo "🔨 构建 Docker 镜像..."
docker build -t word-memorizer .

if [ $? -ne 0 ]; then
    echo "❌ Docker 镜像构建失败"
    exit 1
fi

# 运行容器
echo "▶️ 启动容器..."

if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS 运行命令
    echo "🔗 使用 host.docker.internal:0 进行 X11 转发"
    docker run -it --rm \
        --name word-memorizer \
        -e DISPLAY=host.docker.internal:0 \
        -v "$(pwd)/data":/app/data \
        word-memorizer
        
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux 运行命令
    docker run -it --rm \
        --name word-memorizer \
        -e DISPLAY=${DISPLAY} \
        -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
        -v "$(pwd)/data":/app/data \
        --device /dev/snd \
        word-memorizer
fi

echo "✅ 容器已停止"

# 清理X11权限
if [[ "$OSTYPE" == "darwin"* ]]; then
    xhost -localhost
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    xhost -local:docker
fi

echo "🧹 已清理 X11 权限"