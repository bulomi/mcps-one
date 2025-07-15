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
    
    # 数据库调试配置
    DB_ECHO: bool = False  # 控制SQLAlchemy是否显示SQL查询日志
    
    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    ALLOWED_HOSTS: List[str] = ["*"]
    
    # 数据库配置
    DATABASE_URL: str = "sqlite:///./data/mcps.db"

    
    # 数据目录配置
    DATA_DIR: Path = Path("./data")
    TOOLS_DIR: Path = Path("./data/tools")
    LOGS_DIR: Path = Path("./data/logs")

    
    # MCP 配置
    MCP_MAX_PROCESSES: int = 10
    MCP_PROCESS_TIMEOUT: int = 30
    MCP_RESTART_DELAY: int = 5
    
    # MCP 服务端配置
    ENABLE_MCP_SERVER: bool = False  # 是否启用MCP服务端
    MCP_SERVER_TRANSPORT: str = "stdio"  # MCP服务端传输协议: stdio, http
    MCP_SERVER_HOST: str = "127.0.0.1"  # MCP服务端HTTP模式主机地址
    MCP_SERVER_PORT: int = 8001  # MCP服务端HTTP模式端口
    MCP_SERVER_LOG_LEVEL: str = "INFO"  # MCP服务端日志级别
    MCP_SERVER_SHOW_BANNER: bool = True  # 是否显示启动横幅
    MCP_SERVER_UVICORN_CONFIG: Optional[dict] = None  # Uvicorn自定义配置
    MCP_SERVER_MIDDLEWARE: Optional[list] = None  # 中间件配置
    MCP_SERVER_STATELESS_HTTP: bool = False  # 是否使用无状态HTTP模式
    
    # MCP统一服务配置
    MCP_SERVICE_MODE: str = "both"  # MCP服务模式 (proxy, server, both, disabled)
    MCP_AUTO_START: bool = True  # 是否自动启动MCP服务
    MCP_GRACEFUL_SHUTDOWN: bool = True  # 是否优雅关闭MCP服务
    MCP_MAX_CONNECTIONS: int = 10  # MCP服务端最大连接数
    MCP_CONNECTION_TIMEOUT: int = 30  # MCP连接超时时间(秒)
    MCP_TOOL_STARTUP_TIMEOUT: int = 60  # 工具启动超时时间(秒)
    MCP_HEALTH_CHECK_INTERVAL: int = 30  # 健康检查间隔(秒)
    MCP_RETRY_COUNT: int = 3  # 重试次数
    MCP_ENABLE_METRICS: bool = True  # 是否启用性能指标收集
    
    # 安全配置
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE: Optional[str] = None
    
    # 健康检查配置
    HEALTH_CHECK_ENABLED: bool = True  # 是否启用健康检查
    HEALTH_CHECK_ENDPOINT: str = "/health"  # 健康检查端点
    HEALTH_CHECK_TIMEOUT: int = 5  # 健康检查超时时间(秒)
    
    # 监控配置
    METRICS_ENABLED: bool = True  # 是否启用指标收集
    METRICS_ENDPOINT: str = "/metrics"  # 指标端点
    PROMETHEUS_ENABLED: bool = False  # 是否启用Prometheus指标
    
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
    
    def validate_mcp_server_config(self) -> bool:
        """验证MCP服务端配置"""
        errors = []
        
        # 验证传输协议
        if self.MCP_SERVER_TRANSPORT not in ["stdio", "http"]:
            errors.append(f"无效的MCP传输协议: {self.MCP_SERVER_TRANSPORT}")
        
        # 验证HTTP配置
        if self.MCP_SERVER_TRANSPORT == "http":
            if not (1 <= self.MCP_SERVER_PORT <= 65535):
                errors.append(f"无效的MCP服务端端口: {self.MCP_SERVER_PORT}")
            
            if not self.MCP_SERVER_HOST:
                errors.append("HTTP模式下MCP服务端主机地址不能为空")
        
        # 验证日志级别
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.MCP_SERVER_LOG_LEVEL not in valid_log_levels:
            errors.append(f"无效的MCP服务端日志级别: {self.MCP_SERVER_LOG_LEVEL}")
        
        # 验证超时配置
        if self.MCP_CONNECTION_TIMEOUT <= 0:
            errors.append(f"MCP连接超时时间必须大于0: {self.MCP_CONNECTION_TIMEOUT}")
        
        if self.MCP_TOOL_STARTUP_TIMEOUT <= 0:
            errors.append(f"MCP工具启动超时时间必须大于0: {self.MCP_TOOL_STARTUP_TIMEOUT}")
        
        if errors:
            raise ValueError("MCP服务端配置验证失败:\n" + "\n".join(errors))
        
        return True
    
    def get_mcp_server_config(self) -> dict:
        """获取MCP服务端配置字典"""
        self.validate_mcp_server_config()
        
        config = {
            "transport": self.MCP_SERVER_TRANSPORT,
            "host": self.MCP_SERVER_HOST,
            "port": self.MCP_SERVER_PORT,
            "log_level": self.MCP_SERVER_LOG_LEVEL,
            "show_banner": self.MCP_SERVER_SHOW_BANNER,
            "stateless_http": self.MCP_SERVER_STATELESS_HTTP,
            "max_connections": self.MCP_MAX_CONNECTIONS,
            "connection_timeout": self.MCP_CONNECTION_TIMEOUT,
            "tool_startup_timeout": self.MCP_TOOL_STARTUP_TIMEOUT,
            "health_check_enabled": self.HEALTH_CHECK_ENABLED,
            "metrics_enabled": self.METRICS_ENABLED,
        }
        
        # 添加可选配置
        if self.MCP_SERVER_UVICORN_CONFIG:
            config["uvicorn_config"] = self.MCP_SERVER_UVICORN_CONFIG
        
        if self.MCP_SERVER_MIDDLEWARE:
            config["middleware"] = self.MCP_SERVER_MIDDLEWARE
        
        return config

# 创建全局配置实例
settings = Settings()