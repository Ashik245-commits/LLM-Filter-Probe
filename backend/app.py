"""
FastAPI 主应用 (重构版)

实现 WebSocket 路由和 REST API
采用模块化架构，分离路由、模型、中间件
"""
import logging
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 导入配置和日志
from core.logging_config import configure_logging, get_audit_logger, EndpointFilter
from core.config_loader import load_system_config
from core.config_manager import init_config_manager

# 导入中间件
from middleware.logging import RequestLoggingMiddleware
from middleware.error_handler import ErrorHandlerMiddleware

# 导入路由
from routes.api import router as api_router
from routes.websocket import router as websocket_router

# ============ 初始化系统配置 =============

# 初始化系统层配置 (应用启动最开始)
system_config = load_system_config()

# 配置统一日志 (从 system.json 读取日志级别)
configure_logging(level=getattr(logging, system_config.log_level.upper()))
logger = logging.getLogger(__name__)
audit_logger = get_audit_logger()

# 初始化全局配置管理器
init_config_manager()

logger.info("LLM-Filter-Probe 后端启动")

# ============ FastAPI 应用初始化 =============

app = FastAPI(
    title="LLM-Filter-Probe",
    description="采用混合算法的高效敏感内容检测工具",
    version="1.0.0"
)

# ============ 添加中间件 =============

# 添加请求日志中间件
app.add_middleware(RequestLoggingMiddleware)

# 添加错误处理中间件
app.add_middleware(ErrorHandlerMiddleware)

# 添加 CORS 中间件 (从 system.json 读取 CORS 配置)
app.add_middleware(
    CORSMiddleware,
    allow_origins=system_config.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

# ============ 注册路由 =============

# 注册 API 路由
app.include_router(api_router)

# 注册 WebSocket 路由
app.include_router(websocket_router)

# ============ 根路由和健康检查 =============

@app.get("/")
async def root():
    """根路由"""
    return {
        "name": "LLM-Filter-Probe",
        "version": "1.0.0",
        "description": "采用混合算法的高效敏感内容检测工具",
        "docs": "/docs",
        "health": "/health",
        "diagnostics": "/api/diagnostics"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }


# ============ 应用启动与关闭事件 =============

@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    logger.info("应用启动完成")
    
    # 配置日志过滤器，减少健康检查端点产生的日志噪声
    health_check_filter = EndpointFilter()
    
    # 为 uvicorn.access logger 应用过滤器
    uvicorn_access_logger = logging.getLogger("uvicorn.access")
    for handler in uvicorn_access_logger.handlers:
        handler.addFilter(health_check_filter)
    
    logger.info("日志过滤器已应用 - /api/health 和 /health 端点的访问日志已禁用")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    logger.info("应用正在关闭...")


if __name__ == "__main__":
    import uvicorn
    
    # 从 system.json 读取服务器配置
    uvicorn.run(
        "app:app",
        host=system_config.host,
        port=system_config.port,
        reload=True,
        log_level=system_config.log_level.lower()
    )
