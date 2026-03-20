"""
검토 엔드포인트

POST /api/v1/review/start  → SSE 스트림 (검토 진행 상태 실시간 전송)
"""

import asyncio
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from app.schemas.review import ReviewStartRequest, SSEEvent
from app.services.review.pipeline import run_review_job

router = APIRouter()


def _sse(event: SSEEvent) -> str:
    return f"data: {event.model_dump_json()}\n\n"


@router.post("/start")
async def start_review(body: ReviewStartRequest, request: Request):
    """
    검토 시작 → SSE 스트림

    Nginx 설정 참고: infra/nginx/conf.d/default.conf
        location /api/review/stream {
            proxy_buffering off;
            proxy_cache off;
            chunked_transfer_encoding on;
        }

    프론트엔드 수신 방법:
        const res = await fetch('/api/v1/review/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ documents }),
        })
        const reader = res.body.getReader()
    """
    docs = [d.model_dump() for d in body.documents]

    async def stream():
        try:
            async for event in run_review_job(docs):
                if await request.is_disconnected():
                    break
                yield _sse(event)
                await asyncio.sleep(0)  # 이벤트 루프 양보 → 스트리밍 보장
        except asyncio.CancelledError:
            pass
        except Exception as e:
            from app.schemas.review import SSEEventType
            yield _sse(SSEEvent(
                event=SSEEventType.error,
                job_id="unknown",
                message=f"서버 오류: {e}",
            ))

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
