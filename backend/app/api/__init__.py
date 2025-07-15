"""API 路由包初始化"""

from fastapi import APIRouter

from .tools import router as tools_router
from .system import router as system_router
from .logs import router as logs_router
from .mcp_agent import router as mcp_agent_router
from .mcp_unified import router as mcp_unified_router
from .user import router as user_router
from .proxy import router as proxy_router
from .sessions import router as sessions_router
from .tasks import router as tasks_router

# 创建主路由器
api_router = APIRouter(prefix="/api/v1")

# 注册所有路由
api_router.include_router(tools_router)
api_router.include_router(system_router)
api_router.include_router(logs_router)
api_router.include_router(mcp_agent_router)
api_router.include_router(mcp_unified_router)
api_router.include_router(user_router)
api_router.include_router(proxy_router)
api_router.include_router(sessions_router)
api_router.include_router(tasks_router)

__all__ = ["api_router"]