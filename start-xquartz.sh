#!/bin/bash

echo "🍎 macOS XQuartz 启动助手"
echo "=========================="

# 检查XQuartz是否安装
if [ ! -d "/Applications/Utilities/XQuartz.app" ]; then
    echo "❌ XQuartz 未安装"
    echo "📥 请运行: brew install --cask xquartz"
    exit 1
fi

# 启动XQuartz
echo "🚀 启动 XQuartz..."
open -a XQuartz

# 等待XQuartz启动
echo "⏳ 等待 XQuartz 启动 (5秒)..."
sleep 5

# 检查是否启动成功
if pgrep -f "Xquartz\|X11" > /dev/null; then
    echo "✅ XQuartz 已启动"
    
    # 设置X11转发权限
    export PATH="/opt/X11/bin:$PATH"
    xhost +localhost 2>/dev/null && echo "✅ X11权限设置成功" || echo "⚠️  请手动配置XQuartz安全设置"
    
    echo ""
    echo "📋 重要配置检查："
    echo "1. 确保 XQuartz -> 偏好设置 -> 安全性 中已勾选:"
    echo "   ☑ 允许来自网络客户端的连接"
    echo ""
    echo "2. 如果是首次安装，可能需要注销重新登录"
    echo ""
    echo "🎯 现在可以运行: ./docker-run.sh"
    
else
    echo "❌ XQuartz 启动失败"
    echo "💡 请手动启动 XQuartz 并配置安全设置"
fi