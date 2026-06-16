# =============================================================================
# 市场咨询任务跟踪工具 - Docker CI 环境
# =============================================================================
# 使用方法：
# 1. 安装 Docker Desktop (Windows/macOS) 或 Docker (Linux)
# 2. 在项目目录运行：docker build -t market-task-tracker-ci .
# 3. 运行测试：docker run --rm market-task-tracker-ci
# =============================================================================

FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖（PyQt5需要）
RUN apt-get update && apt-get install -y \
    libqt5gui5 \
    libqt5widgets5 \
    libqt5core5a \
    libegl1 \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

# 设置虚拟显示服务器（用于无头模式运行PyQt5）
ENV DISPLAY=:99

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 安装开发依赖
RUN pip install --no-cache-dir \
    pylint \
    pytest \
    pytest-cov \
    pytest-qt

# 复制源代码
COPY src/ ./src/

# 设置Python路径
ENV PYTHONPATH=/app/src

# 运行测试
CMD ["sh", "-c", "Xvfb :99 -screen 0 1024x768x24 & sleep 2 && pytest src/tests/ -v --tb=short"]
