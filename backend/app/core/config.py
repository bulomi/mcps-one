"""应用配置模块"""

from pydantic_settings import BaseSettings
from typing import List, Optional
import os
from pathlib import Path

class Settings(BaseSettings):
    """应用配置类"""
    
    # 应用基础配置
    APP_NAME: str = "MCP 工具管理系统"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    ALLOWED_HOSTS: List[str] = ["*"]
    
    # 数据库配置
    DATABASE_URL: str = "sqlite:///./data/mcps.db"
    DATABASE_BACKUP_ENABLED: bool = True
    DATABASE_BACKUP_INTERVAL: str = "daily"
    
    # 数据目录配置
    DATA_DIR: Path = Path("./data")
    TOOLS_DIR: Path = Path("./data/tools")
    LOGS_DIR: Path = Path("./data/logs")
    BACKUPS_DIR: Path = Path("./data/backups")
    
    # MCP 配置
    MCP_MAX_PROCESSES: int = 10
    MCP_PROCESS_TIMEOUT: int = 30
    MCP_RESTART_DELAY: int = 5
    
    # 安全配置
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE: Optional[str] = None
    
    # WebSocket 配置
    WS_HEARTBEAT_INTERVAL: int = 30
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # 忽略额外的字段
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 确保数据目录存在
        self.ensure_directories()
    
    def ensure_directories(self):
        """确保必要的目录存在"""
        directories = [
            self.DATA_DIR,
            self.TOOLS_DIR,
            self.LOGS_DIR,
            self.BACKUPS_DIR
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    @property
    def database_url_sync(self) -> str:
        """同步数据库连接URL"""
        return self.DATABASE_URL
    
    @property
    def database_url_async(self) -> str:
        """异步数据库连接URL"""
        if self.DATABASE_URL.startswith("sqlite"):
            return self.DATABASE_URL.replace("sqlite://", "sqlite+aiosqlite://")
        return self.DATABASE_URL

# 创建全局配置实例
settings = Settings()