# 🪟 Windows Docker 设置指南

本指南帮助Windows用户成功运行英语单词记忆系统的Docker版本。

## 📋 前置要求

### 必需组件
1. **Docker Desktop for Windows** 
2. **X11 服务器** (用于GUI显示)

## 🚀 方法一：WSL2 + Docker Desktop (推荐)

### 1. 安装 WSL2
```powershell
# 在管理员PowerShell中运行
wsl --install
```

### 2. 安装 Docker Desktop
- 下载：[Docker Desktop for Windows](https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe)
- 安装时确保启用 "Use WSL 2 based engine"
- 重启后在 Docker Desktop 设置中启用 WSL2 集成

### 3. 运行项目
```bash
# 在 WSL2 Ubuntu 中
cd /mnt/c/path/to/word_memorizer
./docker-run-windows.sh
```

---

## 🖥️ 方法二：Windows原生 + X11服务器

### 1. 安装 X11 服务器

#### 选项A：VcXsrv (推荐)
1. 下载：[VcXsrv Windows X Server](https://sourceforge.net/projects/vcxsrv/files/vcxsrv/)
2. 安装并启动 XLaunch
3. 配置设置：
   ```
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

#### 选项B：Xming (轻量)
1. 下载：[Xming](https://sourceforge.net/projects/xming/files/Xming/)
2. 安装后启动 Xming
3. 确保在系统托盘中看到 Xming 图标

### 2. 配置防火墙
1. 打开 Windows 设置 → 更新和安全 → Windows 安全中心
2. 防火墙和网络保护 → 允许应用通过防火墙
3. 更改设置 → 找到 VcXsrv → 勾选专用和公用网络

### 3. 运行项目
```batch
REM 双击运行批处理文件
docker-run-windows.bat

REM 或在命令提示符中运行
cd path\to\word_memorizer
docker-run-windows.bat
```

---

## 🛠️ 方法三：VMware/VirtualBox 虚拟机

### 1. 创建 Linux 虚拟机
- 推荐：Ubuntu 20.04 LTS 或更新版本
- 分配至少 2GB 内存和 20GB 磁盘空间

### 2. 在虚拟机中安装 Docker
```bash
sudo apt-get update
sudo apt-get install docker.io docker-compose
sudo usermod -aG docker $USER
```

### 3. 运行项目
```bash
git clone https://github.com/BillWang-dev/word_memorizer.git
cd word_memorizer
./docker-run.sh
```

---

## 🔧 故障排除

### 问题1：显示错误 "couldn't connect to display"
**原因**：X11服务器未运行或配置错误

**解决方案**：
1. 确保 VcXsrv 或 Xming 正在运行
2. 检查系统托盘是否有 X 服务器图标
3. 重新配置 X 服务器，确保 "Disable access control" 已启用

### 问题2：Windows 防火墙阻止连接
**解决方案**：
1. 临时关闭防火墙测试
2. 或在防火墙设置中允许 VcXsrv/Xming 通过

### 问题3：Docker 无法启动
**解决方案**：
1. 确保 Docker Desktop 正在运行
2. 检查 WSL2 是否正确安装
3. 重启 Docker Desktop

### 问题4：容器构建失败
**解决方案**：
```batch
REM 清理 Docker 缓存
docker system prune -a

REM 重新构建
docker build --no-cache -t word-memorizer .
```

---

## 📊 性能对比

| 方法 | 设置难度 | 性能 | 稳定性 | 推荐度 |
|------|----------|------|--------|--------|
| WSL2 + Docker | 中等 | 很好 | 很好 | ⭐⭐⭐⭐⭐ |
| 原生 + X11 | 简单 | 好 | 中等 | ⭐⭐⭐⭐ |
| 虚拟机 | 复杂 | 中等 | 很好 | ⭐⭐⭐ |

---

## 🎯 快速检查清单

运行前请确保：
- [ ] Docker Desktop 正在运行
- [ ] X11 服务器 (VcXsrv/Xming) 已启动
- [ ] Windows 防火墙允许 X11 服务器
- [ ] 项目已克隆到本地
- [ ] 在正确目录中运行脚本

---

## 💡 提示

1. **第一次运行**：Docker 镜像构建需要几分钟时间
2. **网络问题**：如果下载缓慢，可以配置 Docker 镜像源
3. **GUI 问题**：如果界面显示异常，尝试重启 X11 服务器
4. **音频问题**：Docker 中的音频支持有限，推荐在虚拟机中运行以获得完整音频体验

---

需要帮助？请查看项目的 [DOCKER.md](DOCKER.md) 文档或提交 Issue。