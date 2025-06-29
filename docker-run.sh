#!/bin/bash

# 英语单词记忆系统 Docker 运行脚本
# 支持 macOS 和 Linux 的 GUI 显示

echo "🚀 启动英语单词记忆系统 Docker 容器..."

# 检测操作系统并设置X11
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    echo "📱 检测到 macOS 系统"
    
    # 设置PATH包含XQuartz
    export PATH="/opt/X11/bin:$PATH"
    
    # 设置X11权限和显示
    xhost +localhost 2>/dev/null || echo "⚠️  请确保XQuartz正在运行并已配置安全设置"
    export DISPLAY=host.docker.internal:0
    
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    echo "🐧 检测到 Linux 系统"
    
    # 设置X11权限和显示
    xhost +local:docker 2>/dev/null
    export DISPLAY=${DISPLAY:-:0}
    
else
    echo "❌ 不支持的操作系统: $OSTYPE"
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