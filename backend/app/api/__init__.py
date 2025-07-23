"""API 路由包初始化"""

from fastapi import APIRouter

from .tools import router as tools_router
from .system import router as system_router
from .logs import router as logs_router
from .mcp_unified import router as mcp_unified_router
from .mcp_agent import router as mcp_agent_router
from .mcp_http import router as mcp_http_router
from .mcp_proxy import router as mcp_proxy_router
from .fastmcp_proxy import router as fastmcp_proxy_router
from .user import router as user_router
from .proxy import router as proxy_router

from .auth import router as auth_router

from .docs import router as docs_router

# 创建主路由器
api_router = APIRouter(prefix="/api/v1")

# 注册所有路由
api_router.include_router(auth_router)
api_router.include_router(tools_router)
api_router.include_router(system_router)
api_router.include_router(logs_router)
api_router.include_router(mcp_agent_router)
api_router.include_router(mcp_unified_router)
api_router.include_router(mcp_http_router)
api_router.include_router(mcp_proxy_router)
api_router.include_router(fastmcp_proxy_router)
api_router.include_router(user_router)
api_router.include_router(proxy_router)


api_router.include_router(docs_router)

# 添加直接的MCP端点（避免重定向问题）
from .mcp_http import handle_mcp_request, mcp_info
api_router.get("/mcp")(mcp_info)
api_router.post("/mcp")(handle_mcp_request)

__all__ = ["api_router"]
