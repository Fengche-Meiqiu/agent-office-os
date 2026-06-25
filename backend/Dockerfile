# Agent Office OS 后端 Dockerfile
# 轻量化镜像，适配 4C4G 腾讯云服务器

# 使用 Python 3.11 slim 精简镜像（约 150MB，比完整版小很多）
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量，减少 Python 缓存（省磁盘）
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

# 复制依赖文件并安装
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目代码
COPY . .

# 创建数据和存储目录
RUN mkdir -p /app/data /app/storage/uploads /app/storage/outputs

# 暴露端口
EXPOSE 8000

# 启动命令：单 worker 模式（省内存）
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
