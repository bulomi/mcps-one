"""数据库配置和连接管理"""

from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from typing import Generator

# 使用默认配置值避免循环导入
# 配置将在运行时通过环境变量或配置文件加载
import os

# 创建数据库引擎
database_url = os.getenv("DATABASE_URL", "sqlite:///./data/mcps.db")
db_echo = os.getenv("DB_ECHO", "false").lower() == "true"

if database_url.startswith("sqlite"):
    # SQLite 特殊配置
    engine = create_engine(
        database_url,
        connect_args={
            "check_same_thread": False,
            "timeout": 20
        },
        poolclass=StaticPool,
        echo=db_echo
    )
else:
    # 其他数据库配置
    engine = create_engine(
        database_url,
        echo=db_echo
    )

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基础模型类
Base = declarative_base()

# 元数据配置
metadata = MetaData()

def get_db() -> Generator:
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """初始化数据库"""
    # 导入所有模型以确保它们被注册
    from app.models import tool, system, log, user, proxy
    # from app.models import session, task  # 会话和任务管理功能已移除

    # 创建所有表
    Base.metadata.create_all(bind=engine)

def reset_db():
    """重置数据库（仅用于开发和测试）"""
    from .unified_config_manager import get_unified_config_manager
    config_manager = get_unified_config_manager()
    
    if not config_manager.get("server.debug", False):
        raise RuntimeError("数据库重置仅允许在调试模式下执行")

    # 删除所有表
    Base.metadata.drop_all(bind=engine)

    # 重新创建所有表
    init_db()
