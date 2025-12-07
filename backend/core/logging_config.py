"""
统一日志配置（跨平台路径处理）
- 应用日志：backend/logs/app.log（滚动）
- 审计日志：backend/logs/audit.log（滚动）
- 控制台：简洁格式
"""
import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler

BASE_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = BASE_DIR / "logs"


class EndpointFilter(logging.Filter):
    """
    自定义日志过滤器 - 用于过滤特定端点和冗余日志
    过滤掉：
    - /api/health 和 /health 的访问日志
    - 重复的配置日志
    - 冗余的 DEBUG 信息
    """
    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        
        # 过滤掉健康检查日志
        if "/api/health" in message or "GET /health" in message:
            return False
        
        # Filter out verbose DEBUG logs, but keep session/config related ones.
        if record.levelno == logging.DEBUG:
            if "会话配置" in message or "ConfigResolver" in message or "最终配置" in message:
                return True
            return False
        
        return True


def _ensure_log_dir():
    LOG_DIR.mkdir(parents=True, exist_ok=True)


def _build_file_handler(filename: str, level: int) -> RotatingFileHandler:
    _ensure_log_dir()
    handler = RotatingFileHandler(
        LOG_DIR / filename,
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8"
    )
    # 详细格式：时间 | 级别 | 模块 | 函数 | 行号 | 消息
    fmt = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)-20s | %(funcName)-15s | %(lineno)-4d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(fmt)
    handler.setLevel(level)
    return handler


def configure_logging(level: int = logging.INFO):
    _ensure_log_dir()

    root = logging.getLogger()
    root.setLevel(level)

    # 清理旧 handlers 避免重复
    for h in list(root.handlers):
        root.removeHandler(h)

    # 控制台（简洁格式，便于实时查看）
    console = logging.StreamHandler()
    console.setLevel(level)
    console.setFormatter(logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s',
        datefmt='%H:%M:%S'
    ))
    # 添加过滤器
    console.addFilter(EndpointFilter())

    # 文件（保留详细信息）
    app_file = _build_file_handler("app.log", level)

    root.addHandler(console)
    root.addHandler(app_file)

    # ============ 关键修改：强制开启 HTTPX 和 HTTPCORE 的 DEBUG 日志 ============
    # 即使系统日志级别是 DEBUG，这两个库默认也是静默的
    # 显式设置为 DEBUG 级别，并输出到控制台
    logging.getLogger("httpx").setLevel(logging.DEBUG)
    logging.getLogger("httpcore").setLevel(logging.DEBUG)
    
    # 抑制第三方库的冗余日志
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.WARNING)

    # 配置审计 logger
    audit_logger = logging.getLogger("audit")
    for h in list(audit_logger.handlers):
        audit_logger.removeHandler(h)
    audit_logger.setLevel(level)
    audit_file = _build_file_handler("audit.log", level)
    audit_logger.addHandler(audit_file)


def get_audit_logger() -> logging.Logger:
    return logging.getLogger("audit")
