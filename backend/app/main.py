"""MCPS.ONE 后端应用主入口"""

import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from starlette.middleware.base import BaseHTTPMiddleware
import logging
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.append(str(Path(__file__).parent))

from app.core.unified_config_manager import init_unified_config_manager, get_unified_config_manager

# 初始化并获取统一配置管理器
config_manager = init_unified_config_manager()
settings = config_manager  # 临时兼容性别名
from app.core.database import engine, SessionLocal
from app.api import api_router
from app.utils.exceptions import (
    MCPSException,
    ToolError,
    MCPProtocolError,
    SystemConfigError,
    DatabaseError,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    RateLimitError
)
from app.utils.helpers import ensure_directory
# from app.models import Base  # 未使用，已注释
from app.services.mcp.mcp_unified_service import unified_service

# 配置日志
# 确保日志目录存在
log_dir = Path(config_manager.get("logging.logs_dir", "./data/logs"))
log_dir.mkdir(parents=True, exist_ok=True)

# 设置日志文件路径
log_file = log_dir / "app.log"

logging.basicConfig(
    level=logging.DEBUG,  # 临时设置为DEBUG级别
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(str(log_file))
    ]
)

# 禁用watchfiles的DEBUG日志
logging.getLogger('watchfiles.main').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("启动 MCPS.ONE 后端服务...")

    try:
        # 确保必要的目录存在
        ensure_directory(Path(config_manager.get("app.data_dir", "./data")))
        ensure_directory(Path(config_manager.get("logging.logs_dir", "./data/logs")))

        # 创建数据库表 - 由 alembic 管理
        # Base.metadata.create_all(bind=engine)
        logger.info("数据库连接初始化完成")

        # 配置管理系统已通过统一配置管理器初始化
        logger.info("配置管理系统已初始化完成")

        # 初始化默认用户
        logger.info("初始化默认用户...")
        from app.services.users import UserService
        db = SessionLocal()
        try:
            user_service = UserService(db)
            user = user_service.get_or_create_default_user()
            logger.info(f"默认用户已准备就绪: {user.username}")
        finally:
            db.close()

        # 初始化统一MCP服务
        logger.info("初始化MCP统一服务...")
        await unified_service.initialize()
        logger.info("MCP统一服务初始化完成")

        # 根据配置自动启动MCP服务
        if config_manager.get("mcp.auto_start", True) and unified_service.mode.value != "disabled":
            logger.info("自动启动MCP服务...")
            await unified_service.start_service()
            status = await unified_service.get_service_status()
            logger.info(f"MCP服务状态: 模式={status.mode.value}, 代理运行={status.proxy_running}, 服务端运行={status.server_running}")

        logger.info(f"MCPS.ONE 后端服务启动成功，监听端口: {config_manager.get('server.port', 8000)}")

    except Exception as e:
        logger.error(f"应用启动失败: {e}")
        raise

    yield

    # 关闭时执行
    logger.info("正在关闭 MCPS.ONE 后端服务...")

    try:
        # 优雅关闭MCP服务
        if unified_service.is_running:
            logger.info("正在关闭MCP统一服务...")
            if config_manager.get("mcp.graceful_shutdown", True):
                await unified_service.stop_service()
            logger.info("MCP统一服务已关闭")

        logger.info("MCPS.ONE 后端服务已关闭")
    except Exception as e:
        logger.error(f"应用关闭时发生错误: {e}")

# 创建 FastAPI 应用
app = FastAPI(
    title=config_manager.get("app.name", "MCPS.ONE"),
    description="MCPS.ONE - MCP 服务器管理平台后端 API",
    version="1.0.0",
    docs_url="/docs" if config_manager.get("server.debug", False) else None,
    redoc_url="/redoc" if config_manager.get("server.debug", False) else None,
    openapi_url="/openapi.json" if config_manager.get("server.debug", False) else None,
    lifespan=lifespan
)

# 配置JSON编码器，确保中文字符正确显示
import json
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse as OriginalJSONResponse

class CustomJSONResponse(OriginalJSONResponse):
    def render(self, content) -> bytes:
        return json.dumps(
            content,
            ensure_ascii=False,
            allow_nan=False,
            indent=None,
            separators=(',', ':'),
        ).encode('utf-8')

# 设置默认响应类
app.default_response_class = CustomJSONResponse

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=config_manager.get("server.allowed_origins", ["http://localhost:3000", "http://127.0.0.1:3000"]),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加尾部斜杠重定向中间件
class TrailingSlashMiddleware(BaseHTTPMiddleware):
    """处理尾部斜杠的中间件"""
    async def dispatch(self, request: Request, call_next):
        # 先尝试原始请求
        response = await call_next(request)

        # 如果返回404，尝试斜杠重定向
        if response.status_code == 404:
            if request.url.path != "/":
                if request.url.path.endswith("/"):
                    # 如果路径以斜杠结尾，尝试去掉斜杠
                    new_path = request.url.path.rstrip("/")
                    new_url = request.url.replace(path=new_path)
                    return RedirectResponse(url=str(new_url), status_code=307)
                else:
                    # 如果路径不以斜杠结尾，尝试添加斜杠
                    new_path = request.url.path + "/"
                    new_url = request.url.replace(path=new_path)
                    return RedirectResponse(url=str(new_url), status_code=307)

        return response

# 临时禁用TrailingSlashMiddleware以解决307重定向问题
# app.add_middleware(TrailingSlashMiddleware)

# 添加受信任主机中间件
allowed_hosts = config_manager.get("server.allowed_hosts", ["localhost", "127.0.0.1"])
if allowed_hosts:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=allowed_hosts
    )

# 静态文件服务（如果需要）
static_dir = Path(config_manager.get("server.static_dir", "./static"))
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# 上传文件服务
# 使用配置管理器中指定的uploads目录
uploads_dir = Path(config_manager.get("server.uploads_dir", "./uploads"))
uploads_dir.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")

# 静态文件服务（前端构建产物）
frontend_dist = Path("../frontend/dist")
if frontend_dist.exists():
    app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets")

# 注册 WebSocket 路由
from app.websocket import websocket_endpoint
app.websocket("/ws")(websocket_endpoint)

# 注册 API 路由
app.include_router(api_router)

# 全局异常处理器
@app.exception_handler(MCPSException)
async def mcps_exception_handler(request: Request, exc: MCPSException):
    """处理自定义异常"""
    logger.error(f"MCPS异常: {exc.message} - {request.url}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.error_code,
            "message": exc.message,
            "details": exc.details
        },
        media_type="application/json; charset=utf-8"
    )

@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    """处理验证异常"""
    logger.warning(f"验证异常: {exc.message} - {request.url}")
    return JSONResponse(
        status_code=400,
        content={
            "error": "VALIDATION_ERROR",
            "message": exc.message,
            "details": exc.details
        },
        media_type="application/json; charset=utf-8"
    )

@app.exception_handler(AuthenticationError)
async def authentication_exception_handler(request: Request, exc: AuthenticationError):
    """处理认证异常"""
    logger.warning(f"认证异常: {exc.message} - {request.url}")
    return JSONResponse(
        status_code=401,
        content={
            "error": "AUTHENTICATION_ERROR",
            "message": exc.message
        },
        media_type="application/json; charset=utf-8"
    )

@app.exception_handler(AuthorizationError)
async def authorization_exception_handler(request: Request, exc: AuthorizationError):
    """处理授权异常"""
    logger.warning(f"授权异常: {exc.message} - {request.url}")
    return JSONResponse(
        status_code=403,
        content={
            "error": "AUTHORIZATION_ERROR",
            "message": exc.message
        },
        media_type="application/json; charset=utf-8"
    )

@app.exception_handler(RateLimitError)
async def rate_limit_exception_handler(request: Request, exc: RateLimitError):
    """处理限流异常"""
    logger.warning(f"限流异常: {exc.message} - {request.url}")
    return JSONResponse(
        status_code=429,
        content={
            "error": "RATE_LIMIT_ERROR",
            "message": exc.message
        },
        media_type="application/json; charset=utf-8"
    )

# 添加 FastAPI 验证错误处理器
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError as PydanticValidationError

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """处理 FastAPI 请求验证错误"""
    logger.error(f"请求验证错误: {exc.errors()} - {request.url}")
    return JSONResponse(
        status_code=422,
        content={
            "error": "VALIDATION_ERROR",
            "message": "请求参数验证失败",
            "details": exc.errors()
        },
        media_type="application/json; charset=utf-8"
    )

@app.exception_handler(PydanticValidationError)
async def pydantic_validation_exception_handler(request: Request, exc: PydanticValidationError):
    """处理 Pydantic 验证错误"""
    logger.error(f"Pydantic验证错误: {exc.errors()} - {request.url}")
    return JSONResponse(
        status_code=422,
        content={
            "error": "VALIDATION_ERROR",
            "message": "数据验证失败",
            "details": exc.errors()
        },
        media_type="application/json; charset=utf-8"
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """处理 HTTP 异常"""
    logger.warning(f"HTTP异常: {exc.detail} - {request.url}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "HTTP_ERROR",
            "message": exc.detail
        },
        media_type="application/json; charset=utf-8"
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """处理通用异常"""
    logger.error(f"未处理的异常: {str(exc)} - {request.url}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_SERVER_ERROR",
            "message": "服务器内部错误" if not config_manager.get("server.debug", False) else str(exc)
        },
        media_type="application/json; charset=utf-8"
    )

# 健康检查端点
@app.get("/health")
async def health_check():
    """健康检查"""
    try:
        # 检查数据库连接
        from sqlalchemy import text
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()

        return {
            "status": "healthy",
            "timestamp": "2024-01-01T00:00:00Z",
            "version": "1.0.0",
            "debug": config_manager.get("server.debug", False)
        }
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e)
            },
            media_type="application/json; charset=utf-8"
        )

# 前端路由处理 - SPA catch-all 路由（临时禁用以解决API路由问题）
# if frontend_dist.exists():
#     @app.get("/")
#     async def serve_frontend_index():
#         """提供前端入口页面"""
#         return FileResponse(str(frontend_dist / "index.html"))
#
#     # SPA catch-all 路由 - 处理所有前端路由
#     @app.get("/{full_path:path}")
#     async def serve_frontend_spa(request: Request, full_path: str):
#         """SPA catch-all 路由，处理所有前端路由"""
#         # 排除 API 路径、静态资源路径和其他特殊路径
#         if (
#             full_path.startswith("api/") or
#             full_path.startswith("static/") or
#             full_path.startswith("uploads/") or
#             full_path.startswith("assets/") or
#             full_path == "ws" or
#             full_path.startswith("ws/") or
#             full_path.startswith("docs") or
#             full_path.startswith("redoc") or
#             full_path == "openapi.json" or
#             full_path == "health" or
#             full_path == "favicon.ico"
#         ):
#             # 这些路径应该由其他路由处理，如果到这里说明没有匹配的路由
#             from fastapi import HTTPException
#             raise HTTPException(status_code=404, detail="Not Found")
#
#         # 对于前端路径，返回前端 index.html
#         return FileResponse(str(frontend_dist / "index.html"))
# else:
# 如果前端不存在，提供API信息
@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "欢迎使用 MCPS.ONE API",
        "version": "1.0.0",
        "docs_url": "/docs" if config_manager.get("server.debug", False) else None
    }

if __name__ == "__main__":
    # 开发环境直接运行
    uvicorn.run(
        "main:app",
        host=config_manager.get("server.host", "0.0.0.0"),
        port=config_manager.get("server.port", 8000),
        reload=config_manager.get("server.debug", False),
        log_level=config_manager.get("logging.level", "info").lower(),
        access_log=True
    )
