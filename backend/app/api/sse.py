"""
SSE（Server-Sent Events）实时推送端点
打通"Hermes → Webhook → Office OS → 前端"的实时通道
前端用 EventSource 订阅，实时收到任务状态/进度/会议消息
"""
import asyncio
import json
import logging
from datetime import datetime
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

# 日志记录器：记录丢消息等异常情况
logger = logging.getLogger("sse")

router = APIRouter(prefix="/api/sse", tags=["SSE 实时推送"])

# 全局订阅者列表：每个订阅者一个 asyncio.Queue
_subscribers: list[asyncio.Queue] = []


def broadcast(event_type: str, data: dict) -> None:
    """
    向所有订阅者推送一条事件
    被 webhook.py / meetings.py 调用
    小白解释：就像群发消息，告诉所有在线的前端"有新事件了"
    """
    message = {"event": event_type, "data": data, "timestamp": datetime.utcnow().isoformat()}
    dropped = 0
    for queue in _subscribers:
        try:
            queue.put_nowait(message)
        except asyncio.QueueFull:
            # 队列满则跳过，但记录日志方便排查丢消息问题
            dropped += 1
    # 如果有丢消息，记录警告日志（小白解释：打印一条警告到日志文件，方便事后排查）
    if dropped > 0:
        logger.warning(
            f"SSE broadcast 丢弃 {dropped}/{len(_subscribers)} 条事件（event={event_type}）"
        )


async def _event_stream():
    """SSE 事件流生成器，每个客户端连接时创建独立队列"""
    queue: asyncio.Queue = asyncio.Queue(maxsize=100)
    _subscribers.append(queue)
    try:
        # 发送连接成功消息
        yield f"event: connected\ndata: {json.dumps({'message': 'SSE connected'})}\n\n"
        while True:
            msg = await queue.get()
            event_type = msg["event"]
            data = json.dumps(msg["data"], ensure_ascii=False)
            yield f"event: {event_type}\ndata: {data}\n\n"
    except asyncio.CancelledError:
        pass
    finally:
        if queue in _subscribers:
            _subscribers.remove(queue)


@router.get("/tasks")
async def sse_tasks():
    """订阅任务状态/进度/步骤事件"""
    return StreamingResponse(
        _event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Nginx 不缓冲
        },
    )


@router.get("/meetings")
async def sse_meetings():
    """订阅会议消息（Agent 发言实时到达）"""
    return StreamingResponse(
        _event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
