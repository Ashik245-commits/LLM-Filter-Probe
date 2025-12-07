"""
WebSocket 路由 (WebSocket Routes)

包含所有 WebSocket 端点
"""
import logging
from typing import Dict, Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from handlers.session_manager import get_session_manager

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"]) 


@router.websocket("/ws/scan/{session_id}")
async def websocket_scan(websocket: WebSocket, session_id: str):
    """
    WebSocket 扫描端点
    
    客户端消息格式:
    {
        "type": "scan_text",
        "data": {
            "text": "...",
            "segment_size": 1000  # 可选
        }
    }
    """
    logger.info(f"[WS] 收到WebSocket连接请求: session_id={session_id}")
    
    await websocket.accept()
    logger.info(f"[WS] WebSocket连接已接受: session_id={session_id}")
    
    # 获取全局会话管理器并检查会话
    session_manager = get_session_manager()
    session = session_manager.get_session(session_id)
    if not session:
        logger.error(f"[WS] 会话不存在: session_id={session_id}")
        logger.info(f"[WS] 当前活动会话: {list(session_manager.sessions.keys())}")
        await websocket.send_json({
            "event": "error",
            "message": "会话不存在"
        })
        await websocket.close()
        return
    
    logger.info(f"[WS] 会话验证成功: session_id={session_id}")
    
    # 设置消息回调
    async def message_callback(msg: Dict[str, Any]):
        try:
            # 发送前记录关键事件，便于排查前端未显示的问题
            msg_type = msg.get('type') if isinstance(msg, dict) else None
            if msg_type in ('unknown_status_code', 'log'):
                try:
                    preview = msg.get('message', '')[:80] if isinstance(msg, dict) else ''
                    logger.info(f"[WS:{session_id}] → 推送事件: type={msg_type} {('|' + preview) if preview else ''}")
                except Exception:
                    pass
            await websocket.send_json(msg)
        except Exception as e:
            logger.error(f"发送消息失败: {str(e)}")
            # 当发送消息失败（通常表示连接已断开），立即设置停止标志
            if session and session.websocket_handler:
                session.websocket_handler.should_stop = True
                logger.warning(f"[{session_id}] 检测到连接断开，已设置停止标志，扫描将在下一个检查点中止。")
    
    await session.websocket_handler.set_message_callback(message_callback)
    
    try:
        while True:
            # 接收客户端消息
            data = await websocket.receive_text()
            
            # 处理消息
            success = await session.websocket_handler.handle_message(data)
            
            if not success:
                logger.warning(f"消息处理失败: {data[:100]}")
    
    except WebSocketDisconnect:
        logger.warning(f"客户端断开连接: {session_id}，正在尝试停止扫描任务...")
        if session and session.websocket_handler:
            # 当客户端断开连接时，立即设置停止标志
            session.websocket_handler.should_stop = True
            logger.info(f"[{session_id}] 停止标志已设置，扫描将在下一个检查点中止。")
    except Exception as e:
        logger.error(f"WebSocket 错误: {str(e)}", exc_info=True)
        try:
            await websocket.send_json({
                "event": "error",
                "message": f"服务器错误: {str(e)}"
            })
        except:
            pass
