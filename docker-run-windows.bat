@echo off
REM 英语单词记忆系统 Windows 批处理启动脚本
REM 支持 Docker Desktop for Windows

echo 🪟 Windows 英语单词记忆系统启动脚本
echo.

REM 检查Docker是否安装
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker 未安装
    echo 📥 请安装 Docker Desktop for Windows
    echo 🔗 下载地址: https://desktop.docker.com/win/main/amd64/Docker Desktop Installer.exe
    pause
    exit /b 1
)

REM 检查Docker是否运行
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker 未运行
    echo 🚀 请启动 Docker Desktop
    pause
    exit /b 1
)

echo ✅ Docker 环境检查通过
echo.

echo 🔍 检查 X11 服务器状态...
netstat -an | findstr :6000 >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ X11 服务器正在运行 (端口 6000)
) else (
    echo ❌ X11 服务器未运行
    echo.
    echo 🚨 请先启动 X11 服务器：
    echo    1. 下载 VcXsrv: https://sourceforge.net/projects/vcxsrv/files/vcxsrv/
    echo    2. 安装后启动 XLaunch
    echo    3. 配置选项：
    echo       - Display number: 0
    echo       - Multiple windows: ✓
    echo       - Start no client: ✓
    echo       - Disable access control: ✓
    echo.
    echo 💡 启动 VcXsrv 后请重新运行此脚本
    pause
    exit /b 1
)
echo.

REM 构建Docker镜像
echo 🔨 构建 Docker 镜像...
docker build -t word-memorizer .
if %errorlevel% neq 0 (
    echo ❌ Docker 镜像构建失败
    pause
    exit /b 1
)

echo.
echo 📺 准备启动 GUI 应用...
echo ⚠️  请确保已安装并启动 X11 服务器
echo.
echo 🔧 推荐的 X11 服务器配置：
echo    VcXsrv: https://sourceforge.net/projects/vcxsrv/
echo    配置: Display number=0, Start no client=✓, Disable access control=✓
echo.

REM 运行容器
echo ▶️ 启动容器...
docker run -it --rm ^
    --name word-memorizer ^
    -e DISPLAY=host.docker.internal:0 ^
    -v "%cd%\data":/app/data ^
    word-memorizer

echo.
echo ✅ 容器已停止
echo.
echo 📚 如果遇到问题：
echo 1. 🔧 确保 VcXsrv 或 Xming 正在运行
echo 2. 🔓 检查 Windows 防火墙设置
echo 3. 🔄 重启 Docker Desktop
echo 4. 📖 查看完整文档: DOCKER.md
echo.
pause