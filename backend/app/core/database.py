"""数据库配置和连接管理"""

from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from typing import Generator

from .config import settings

# 创建数据库引擎
if settings.DATABASE_URL.startswith("sqlite"):
    # SQLite 特殊配置
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={
            "check_same_thread": False,
            "timeout": 20
        },
        poolclass=StaticPool,
        echo=settings.DEBUG
    )
else:
    # 其他数据库配置
    engine = create_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG
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
    from app.models import tool, system, log
    
    # 创建所有表
    Base.metadata.create_all(bind=engine)

def reset_db():
    """重置数据库（仅用于开发和测试）"""
    if not settings.DEBUG:
        raise RuntimeError("数据库重置仅允许在调试模式下执行")
    
    # 删除所有表
    Base.metadata.drop_all(bind=engine)
    
    # 重新创建所有表
    init_db()