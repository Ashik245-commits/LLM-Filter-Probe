"""
后端应用入口文件

这个文件作为 uvicorn 的入口点，确保相对导入正确工作
"""
from app import app

if __name__ == "__main__":
    import uvicorn
    from core.config_loader import init_system_config
    
    # 从 system.json 读取服务器配置
    system_config = init_system_config()
    
    uvicorn.run(
        "main:app",
        host=system_config.host,
        port=system_config.port,
        reload=True,
        log_level=system_config.log_level.lower()
    )
