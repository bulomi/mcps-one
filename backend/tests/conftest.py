import pytest
import asyncio
import sys
import os
from typing import Generator, AsyncGenerator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.core.database import get_db, Base
from app.models.tool import MCPTool
from app.models.session import MCPSession
from app.models.task import MCPTask

# 创建测试数据库
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def db_session():
    """创建测试数据库会话"""
    # 创建所有表
    Base.metadata.create_all(bind=engine)

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        # 清理测试数据
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """创建测试客户端"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def sample_tool_data():
    """示例工具数据"""
    return {
        "name": "test_tool",
        "display_name": "测试工具",
        "description": "这是一个测试工具",
        "command": "python test_tool.py",
        "type": "custom",
        "category": "test",
        "auto_start": False
    }


@pytest.fixture
def sample_session_data():
    """示例会话数据"""
    return {
        "session_id": "test_session_001",
        "name": "test_session",
        "description": "测试会话",
        "tool_id": None,  # 将在测试中设置
        "status": "active",
        "session_type": "user"
    }


@pytest.fixture
def sample_task_data():
    """示例任务数据"""
    return {
        "task_id": "test_task_001",
        "name": "test_task",
        "description": "测试任务",
        "session_id": None,  # 将在测试中设置
        "status": "pending",
        "priority": "normal",
        "task_type": "single_tool"
    }
