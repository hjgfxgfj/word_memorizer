# 🐳 Docker 部署指南

本文档介绍如何使用 Docker 运行英语单词记忆系统，让其他用户可以轻松使用你的项目。

## 📋 前置要求

### 🖥️ 系统要求
- Docker 20.10+
- Docker Compose 2.0+
- 支持 GUI 显示的环境

### 🍎 macOS 用户
```bash
# 安装 Docker Desktop
brew install --cask docker

# 安装 XQuartz (GUI 支持)
brew install --cask xquartz

# 重启后在 XQuartz 设置中启用 "Allow connections from network clients"
```

### 🐧 Linux 用户
```bash
# 安装 Docker
sudo apt-get update
sudo apt-get install docker.io docker-compose

# 添加用户到 docker 组
sudo usermod -aG docker $USER
```

### 🪟 Windows 用户

Windows用户有以下几种运行方式：

#### 方式一：WSL2 + Docker Desktop（推荐）
```bash
# 1. 安装 WSL2
wsl --install

# 2. 安装 Docker Desktop for Windows
# 下载：https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe
# 确保启用 WSL2 集成

# 3. 在 WSL2 Ubuntu 中运行
wsl
cd /mnt/c/path/to/word_memorizer
./docker-run-windows.sh
```

#### 方式二：VMware/VirtualBox Linux虚拟机
```bash
# 1. 安装 Ubuntu 20.04+ 虚拟机
# 2. 在虚拟机中安装 Docker
sudo apt-get update
sudo apt-get install docker.io docker-compose

# 3. 克隆项目并运行
git clone https://github.com/BillWang-dev/word_memorizer.git
cd word_memorizer
./docker-run.sh
```

#### 方式三：Windows本地X11服务器

**步骤1：安装X11服务器**
```powershell
# 推荐 VcXsrv（更稳定）
# 下载：https://sourceforge.net/projects/vcxsrv/files/vcxsrv/

# 或者 Xming（更轻量）
# 下载：https://sourceforge.net/projects/xming/files/Xming/
```

**步骤2：配置X11服务器**
```
启动 VcXsrv，配置如下：
┌─────────────────────────────────┐
│ Display settings:               │
│ ☑ Multiple windows              │
│ Display number: 0               │
│                                 │
│ Client startup:                 │
│ ☑ Start no client              │
│                                 │
│ Extra settings:                 │
│ ☑ Disable access control       │
│ ☑ Native opengl                │
└─────────────────────────────────┘
```

**步骤3：配置Windows防火墙**
```powershell
# 允许 VcXsrv 通过防火墙
# 设置 > 更新和安全 > Windows 安全中心 > 防火墙和网络保护
# 允许应用通过防火墙 > 更改设置 > 找到 VcXsrv > 勾选专用和公用
```

**步骤4：运行容器**
```batch
# 使用批处理文件（推荐）
docker-run-windows.bat

# 或手动运行
docker run -it --rm \
    -e DISPLAY=host.docker.internal:0 \
    -v "%cd%\data":/app/data \
    word-memorizer
```

## 🚀 快速启动

### 🪟 Windows 用户
```batch
REM 方法一：双击批处理文件（最简单）
docker-run-windows.bat

REM 方法二：WSL2中运行脚本
wsl
./docker-run-windows.sh

REM 方法三：PowerShell中手动运行
git clone https://github.com/BillWang-dev/word_memorizer.git
cd word_memorizer
docker build -t word-memorizer .
docker run -it --rm -e DISPLAY=host.docker.internal:0 -v "${PWD}\data":/app/data word-memorizer
```

### 🍎🐧 macOS/Linux 用户
```bash
# 克隆项目
git clone https://github.com/BillWang-dev/word_memorizer.git
cd word_memorizer

# 运行启动脚本
./docker-run.sh
```

### 方法二：使用 docker-compose
```bash
# 启动服务
docker-compose up --build

# 后台运行
docker-compose up -d --build

# 停止服务
docker-compose down
```

### 方法三：手动运行 Docker
```bash
# 构建镜像
docker build -t word-memorizer .

# macOS 运行
xhost +localhost
docker run -it --rm \
    -e DISPLAY=host.docker.internal:0 \
    -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
    -v "$(pwd)/data":/app/data \
    word-memorizer

# Linux 运行
xhost +local:docker
docker run -it --rm \
    -e DISPLAY=${DISPLAY} \
    -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
    -v "$(pwd)/data":/app/data \
    --device /dev/snd \
    word-memorizer
```

## 📁 数据持久化

Docker 容器会自动挂载以下目录：
- `./data` → 学习进度和词汇数据
- 音频缓存和 AI 缓存会保存在 Docker volume 中

## 🔧 配置说明

### 环境变量
- `DISPLAY`: GUI 显示配置
- `PULSE_RUNTIME_PATH`: 音频支持（Linux）

### 端口映射
- `8080`: 预留端口（将来可能的 Web 界面）

### 挂载点
- `/tmp/.X11-unix`: X11 socket（GUI 支持）
- `/app/data`: 数据目录
- `/run/user/1000/pulse`: PulseAudio（Linux 音频）

## 🐛 故障排除

### GUI 无法显示
**macOS:**
```bash
# 确保 XQuartz 正在运行
open -a XQuartz

# 检查 X11 转发
xhost +localhost
echo $DISPLAY
```

**Linux:**
```bash
# 检查 X11 权限
xhost +local:docker

# 检查 DISPLAY 变量
echo $DISPLAY

# 如果是 Wayland，可能需要切换到 X11
```

### 音频问题
**Linux:**
```bash
# 检查音频设备
docker run --rm --device /dev/snd alpine ls -la /dev/snd

# 检查 PulseAudio
pulseaudio --check -v
```

**macOS:**
```bash
# Docker Desktop 中的音频支持有限
# 建议在本地运行或使用 Linux 环境
```

### 容器构建失败
```bash
# 清理 Docker 缓存
docker system prune -a

# 重新构建
docker build --no-cache -t word-memorizer .
```

### 权限问题
```bash
# 修复文件权限
sudo chown -R $USER:$USER data/

# 检查 Docker 权限
docker ps
```

## 📊 性能优化

### 镜像大小优化
当前镜像大小约 500MB，包含：
- Python 3.11 运行时
- GUI 支持库
- 音频处理库
- 中文字体支持

### 内存使用
- 基础内存: ~100MB
- GUI 运行时: ~200-300MB
- 推荐内存: 512MB+

### CPU 使用
- TTS 处理期间 CPU 使用较高
- 正常使用时 CPU 使用很低

## 🔒 安全注意事项

1. **X11 转发**: 只在需要时启用，使用后及时关闭
2. **网络模式**: 使用 `host` 模式以简化 GUI 显示
3. **用户权限**: 容器内使用非 root 用户
4. **数据隔离**: 敏感数据通过 volume 挂载

## 📦 分发建议

### Docker Hub 发布
```bash
# 标记镜像
docker tag word-memorizer your-username/word-memorizer:latest

# 推送到 Docker Hub
docker push your-username/word-memorizer:latest
```

### GitHub Packages
```bash
# 标记镜像
docker tag word-memorizer ghcr.io/billwang-dev/word-memorizer:latest

# 推送到 GitHub Packages
docker push ghcr.io/billwang-dev/word-memorizer:latest
```

### 一键部署脚本
为用户提供简单的部署脚本：
```bash
curl -sSL https://raw.githubusercontent.com/BillWang-dev/word_memorizer/main/docker-run.sh | bash
```

## 🌐 Web 版本考虑

将来可以考虑添加 Web 界面：
- 使用 FastAPI 或 Flask 作为后端
- React 或 Vue.js 作为前端
- 通过 WebRTC 支持音频播放
- 无需 X11 转发，更易部署

## ❓ 常见问题

**Q: 为什么选择 Docker？**
A: Docker 可以解决环境依赖问题，让用户无需配置 Python 环境就能使用。

**Q: 性能会受影响吗？**
A: GUI 应用在 Docker 中运行会有轻微性能损失，但对于此应用影响很小。

**Q: 支持 Windows 吗？**
A: 完全支持！提供了多种运行方式：
- WSL2 + Docker Desktop（最佳体验）
- VMware/VirtualBox Linux虚拟机（最稳定）
- Windows原生 + X11服务器（最简单）

**Q: 数据会丢失吗？**
A: 不会，学习进度保存在挂载的 `data` 目录中。

---

🎉 现在其他用户只需要一个命令就能使用你的英语单词记忆系统了！