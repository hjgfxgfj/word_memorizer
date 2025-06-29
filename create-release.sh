#!/bin/bash

# 英语单词记忆系统 - 发布脚本
# 自动创建GitHub Release触发多平台构建

if [ $# -eq 0 ]; then
    echo "用法: ./create-release.sh <版本号>"
    echo "示例: ./create-release.sh v1.0.0"
    exit 1
fi

VERSION=$1

echo "🚀 准备发布版本: $VERSION"
echo "================================"

# 检查是否有未提交的更改
if [ -n "$(git status --porcelain)" ]; then
    echo "📝 发现未提交的更改，正在提交..."
    git add -A
    git commit -m "feat: 准备发布 $VERSION

- 添加GitHub Actions多平台自动构建
- 创建发布指南和下载链接
- 优化用户获取方式

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"
fi

# 创建标签
echo "🏷️  创建版本标签: $VERSION"
git tag $VERSION

# 推送到GitHub
echo "📤 推送到GitHub..."
git push origin main
git push origin $VERSION

echo ""
echo "✅ 发布完成！"
echo ""
echo "📋 后续步骤："
echo "1. 🔍 查看GitHub Actions构建状态:"
echo "   https://github.com/BillWang-dev/word_memorizer/actions"
echo ""
echo "2. 📦 构建完成后查看Release:"
echo "   https://github.com/BillWang-dev/word_memorizer/releases"
echo ""
echo "3. 📥 用户下载地址:"
echo "   - Windows: https://github.com/BillWang-dev/word_memorizer/releases/latest/download/WordMemorizer-Windows.zip"
echo "   - macOS: https://github.com/BillWang-dev/word_memorizer/releases/latest/download/WordMemorizer-macOS.zip"  
echo "   - Linux: https://github.com/BillWang-dev/word_memorizer/releases/latest/download/WordMemorizer-Linux.tar.gz"
echo ""
echo "🎉 用户现在可以直接下载可执行文件，无需安装Python或Docker！"