"""MCPS.ONE 后端应用主入口"""

import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import logging
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.append(str(Path(__file__).parent))

from app.core.config import settings
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
from app.models import Base
from app.services.mcp_unified_service import unified_service

# 配置日志
# 确保日志目录存在
log_dir = Path(settings.LOGS_DIR)
log_dir.mkdir(parents=True, exist_ok=True)

# 设置日志文件路径
log_file = log_dir / "app.log"

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(str(log_file))
    ]
)

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("启动 MCPS.ONE 后端服务...")
    
    try:
        # 确保必要的目录存在
        ensure_directory(Path(settings.DATA_DIR))
        ensure_directory(Path(settings.LOGS_DIR))
        
        # 创建数据库表 - 由 alembic 管理
        # Base.metadata.create_all(bind=engine)
        logger.info("数据库连接初始化完成")
        
        # 初始化统一MCP服务
        logger.info("初始化MCP统一服务...")
        await unified_service.initialize()
        
        # 根据配置自动启动MCP服务
        if settings.MCP_AUTO_START and unified_service.mode.value != "disabled":
            logger.info("自动启动MCP服务...")
            await unified_service.start_service()
            status = await unified_service.get_service_status()
            logger.info(f"MCP服务状态: 模式={status.mode.value}, 代理运行={status.proxy_running}, 服务端运行={status.server_running}")
        
        logger.info(f"MCPS.ONE 后端服务启动成功，监听端口: {settings.PORT}")
        
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
            if settings.MCP_GRACEFUL_SHUTDOWN:
                await unified_service.stop_service()
            logger.info("MCP统一服务已关闭")
        
        logger.info("MCPS.ONE 后端服务已关闭")
    except Exception as e:
        logger.error(f"应用关闭时发生错误: {e}")

# 创建 FastAPI 应用
app = FastAPI(
    title=settings.APP_NAME,
    description="MCPS.ONE - MCP 服务器管理平台后端 API",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan
)

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加受信任主机中间件
if settings.ALLOWED_HOSTS:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS
    )

# 注册 API 路由
app.include_router(api_router)

# 注册 WebSocket 路由
from app.websocket import websocket_endpoint
app.websocket("/ws")(websocket_endpoint)

# 静态文件服务（如果需要）
static_dir = Path("./static")
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# 静态文件服务（前端构建产物）
frontend_dist = Path("../frontend/dist")
if frontend_dist.exists():
    app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets")

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
        }
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
        }
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
        }
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
        }
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
        }
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
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """处理通用异常"""
    logger.error(f"未处理的异常: {str(exc)} - {request.url}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_SERVER_ERROR",
            "message": "服务器内部错误" if not settings.DEBUG else str(exc)
        }
    )

# 健康检查端点
@app.get("/health")
async def health_check():
    """健康检查"""
    try:
        # 检查数据库连接
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        
        return {
            "status": "healthy",
            "timestamp": "2024-01-01T00:00:00Z",
            "version": "1.0.0",
            "debug": settings.DEBUG
        }
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )

# 根路径
@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "欢迎使用 MCPS.ONE API",
        "version": "1.0.0",
        "docs_url": "/docs" if settings.DEBUG else None
    }

# 前端路由处理
if frontend_dist.exists():
    @app.get("/{path:path}")
    async def serve_frontend_routes(path: str):
        """处理前端路由"""
        file_path = frontend_dist / path
        if file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(frontend_dist / "index.html"))

if __name__ == "__main__":
    # 开发环境直接运行
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=True
    )