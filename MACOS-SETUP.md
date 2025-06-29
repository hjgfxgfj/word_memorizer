# 🍎 macOS Docker 设置指南

本指南帮助macOS用户成功运行英语单词记忆系统的Docker版本。

## 📋 前置要求

### 必需组件
1. **Docker Desktop for Mac**
2. **XQuartz** (X11服务器，用于GUI显示)

## 🚀 安装步骤

### 1. 安装 Docker Desktop
```bash
# 使用 Homebrew (推荐)
brew install --cask docker

# 或手动下载安装
# https://desktop.docker.com/mac/main/amd64/Docker.dmg
```

### 2. 安装 XQuartz
```bash
# 使用 Homebrew
brew install --cask xquartz

# 或手动下载安装
# https://www.xquartz.org/
```

### 3. 配置 XQuartz
安装后**必须注销并重新登录**，然后：

1. 启动 XQuartz (在应用程序/实用工具中)
2. 打开 XQuartz -> 偏好设置 -> 安全性
3. **勾选** "允许来自网络客户端的连接"
4. 重启 XQuartz

### 4. 运行项目
```bash
# 克隆项目
git clone https://github.com/BillWang-dev/word_memorizer.git
cd word_memorizer

# 运行启动脚本
./docker-run.sh
```

## 🔧 详细配置

### XQuartz 安全设置
```
XQuartz -> 偏好设置 -> 安全性
┌─────────────────────────────────┐
│ ☑ 允许来自网络客户端的连接        │
│ ☑ 允许来自本地主机的连接         │
│ ☐ 始终信任客户端               │
└─────────────────────────────────┘
```

### 验证 XQuartz 运行状态
```bash
# 检查 XQuartz 进程
ps aux | grep -i xquartz

# 检查 X11 转发
echo $DISPLAY

# 测试 xhost 命令
xhost
```

## 🐛 故障排除

### 问题1：显示错误 "couldn't connect to display"

**可能原因**：
- XQuartz 未运行
- XQuartz 安全设置未正确配置
- 没有注销重新登录

**解决步骤**：
```bash
# 1. 确保 XQuartz 正在运行
open -a XQuartz

# 2. 等待几秒让 XQuartz 完全启动
sleep 3

# 3. 重新运行脚本
./docker-run.sh
```

### 问题2：XQuartz 启动但仍然无法连接

**解决方案**：
```bash
# 手动配置 X11 转发
export DISPLAY=:0
xhost +localhost

# 然后运行 Docker
docker run -it --rm \
    -e DISPLAY=host.docker.internal:0 \
    -v "$(pwd)/data":/app/data \
    word-memorizer
```

### 问题3：权限被拒绝

**解决方案**：
```bash
# 重置 xhost 权限
xhost -
xhost +localhost

# 或完全重置
sudo xhost +
```

### 问题4：Docker 构建失败

**解决方案**：
```bash
# 清理 Docker 缓存
docker system prune -a

# 重新构建镜像
docker build --no-cache -t word-memorizer .
```

## 💡 最佳实践

### 1. 自动启动设置
将 XQuartz 设为开机自启：
```bash
# 添加到登录项
osascript -e 'tell application "System Events" to make login item at end with properties {path:"/Applications/Utilities/XQuartz.app", hidden:false}'
```

### 2. 创建便捷脚本
创建 `~/run-word-memorizer.sh`：
```bash
#!/bin/bash
cd ~/path/to/word_memorizer
open -a XQuartz
sleep 3
./docker-run.sh
```

### 3. 验证环境
运行前快速检查：
```bash
# 检查 Docker
docker --version

# 检查 XQuartz
xhost

# 检查显示
echo $DISPLAY
```

## ⚡ 快速启动清单

启动前确保：
- [ ] Docker Desktop 正在运行
- [ ] XQuartz 已安装并配置正确
- [ ] XQuartz 正在运行 (菜单栏有 X 图标)
- [ ] 在项目目录中运行 `./docker-run.sh`

## 🔍 调试信息

如果遇到问题，收集以下信息：

```bash
# 系统信息
sw_vers

# Docker 版本
docker --version

# XQuartz 版本
/Applications/Utilities/XQuartz.app/Contents/MacOS/X11 -version

# 显示设置
echo $DISPLAY
xhost

# 进程状态  
ps aux | grep -i xquartz
```

## 📊 性能提示

- **内存**：为 Docker Desktop 分配至少 4GB 内存
- **磁盘**：确保有至少 2GB 可用空间
- **网络**：如果构建缓慢，配置 Docker 镜像源

## ❓ 常见问题

**Q: 为什么需要 XQuartz？**
A: Docker 容器内的 GUI 应用需要 X11 服务器来显示界面，macOS 默认不包含 X11。

**Q: 可以不用 XQuartz 吗？**
A: 可以考虑使用 VNC 或者运行纯命令行版本，但会失去 GUI 功能。

**Q: 性能会比原生应用慢吗？**
A: 会有轻微延迟，但对于此应用影响很小。

**Q: 数据会保存吗？**
A: 是的，学习进度保存在 `data/` 目录，会持久化保存。

---

**提示**：首次运行时 Docker 镜像构建需要几分钟，请耐心等待。

需要更多帮助？查看 [DOCKER.md](DOCKER.md) 或提交 Issue。