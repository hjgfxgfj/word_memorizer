# 英语单词记忆系统 Docker镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    python3-tk \
    python3-dev \
    portaudio19-dev \
    libportaudio2 \
    libasound2-dev \
    libpulse-dev \
    fonts-noto-cjk \
    fonts-liberation \
    libgtk-3-0 \
    libglib2.0-0 \
    libgdk-pixbuf2.0-0 \
    libcairo-gobject2 \
    libpango-1.0-0 \
    libatk1.0-0 \
    libcairo2 \
    libgdk-pixbuf2.0-0 \
    libgtk-3-0 \
    libgstreamer1.0-0 \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-ugly \
    gstreamer1.0-libav \
    gstreamer1.0-tools \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV DISPLAY=:0
ENV QT_X11_NO_MITSHM=1

# 复制项目文件
COPY requirements-basic.txt .
COPY logic/ ./logic/
COPY audio/ ./audio/
COPY ui/ ./ui/
COPY data/ ./data/
COPY scripts/ ./scripts/
COPY test_installation.py .
COPY CLAUDE.md .
COPY README.md .

# 安装Python依赖 (分阶段安装以应对网络问题)
RUN pip install --upgrade pip && \
    pip install --timeout=300 --retries=3 numpy scipy && \
    pip install --timeout=300 --retries=3 matplotlib Pillow && \
    pip install --timeout=300 --retries=3 pandas && \
    pip install --timeout=300 --retries=3 --no-cache-dir -r requirements-basic.txt

# 创建非root用户
RUN useradd -m -s /bin/bash worduser && \
    chown -R worduser:worduser /app

USER worduser

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python test_installation.py || exit 1

# 暴露端口（如果将来需要web界面）
EXPOSE 8080

# 启动命令
CMD ["python", "ui/main.py"]