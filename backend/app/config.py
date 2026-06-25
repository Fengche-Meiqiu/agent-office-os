"""
应用配置文件
所有可配置项集中在这里，方便部署时修改
"""
import os
from pathlib import Path


class Settings:
    """全局配置类，从环境变量读取，带默认值"""

    # ===== 应用基础 =====
    # 应用名称
    APP_NAME: str = "Agent Office OS"
    # 运行环境：development / production
    ENV: str = os.getenv("ENV", "development")
    # 是否调试模式（reload 模式会触发 multiprocessing，某些环境不兼容）
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    # ===== 数据库 =====
    # SQLite 数据库文件路径
    # 存放在 backend/data/office.db
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    DB_PATH: Path = DATA_DIR / "office.db"
    # SQLAlchemy 连接字符串
    DATABASE_URL: str = f"sqlite:///{DB_PATH}"

    # ===== Hermes 对接 =====
    # Hermes API 地址（本机部署，默认 8001 端口，部署时按实际修改）
    HERMES_URL: str = os.getenv("HERMES_URL", "http://localhost:8001")
    # Hermes 发现 Agent 的同步周期（秒）
    DISCOVER_INTERVAL: int = 300  # 5 分钟

    # ===== 文件存储 =====
    # 成果文件、上传文件存储目录
    STORAGE_DIR: Path = BASE_DIR / "storage"
    UPLOAD_DIR: Path = STORAGE_DIR / "uploads"
    OUTPUT_DIR: Path = STORAGE_DIR / "outputs"

    # ===== CORS 跨域 =====
    # 允许的前端来源（开发环境允许 localhost）
    CORS_ORIGINS: list = [
        "http://localhost:5173",  # Vite 开发服务器
        "http://localhost:3000",  # 备用前端端口
        "http://127.0.0.1:5173",
    ]

    # ===== 服务器 =====
    # 监听端口
    PORT: int = int(os.getenv("PORT", "8000"))
    # Uvicorn worker 数量（省内存用 1 个）
    WORKERS: int = int(os.getenv("WORKERS", "1"))

    def ensure_dirs(self):
        """确保所有必要目录存在"""
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.STORAGE_DIR.mkdir(parents=True, exist_ok=True)
        self.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        self.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# 全局配置实例
settings = Settings()
settings.ensure_dirs()
