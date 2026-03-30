"""
대화형 질문 API — 검토된 문서 자동 RAG 컨텍스트
────────────────────────────────────────────────────────────
POST /projects/{project_id}/chat/stream
  - review_run_id 넘기면 해당 문서 텍스트 자동 로드
  - 문서 컨텍스트 시스템 프롬프트에 자동 주입
  - SSE 스트리밍
"""

from __future__ import annotations

import json
import os
import threading
from datetime import datetime
from typing import AsyncGenerator

import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

router = APIRouter()

VLLM_BASE_URL = os.getenv("VLLM_BASE_URL", "http://host.docker.internal:18080/v1")
VLLM_MODEL    = os.getenv("VLLM_MODEL", "gemma-3-12b")
TIMEOUT       = 120

# 대화 히스토리 저장소
# { project_id: { "context": str, "history": [...], "review_run_id": int } }
_chat_store: dict[int, dict] = {}
_store_lock  = threading.Lock()


def _get_or_create(project_id: int) -> dict:
    with _store_lock:
        if project_id not in _chat_store:
            _chat_store[project_id] = {
                "context":       "",
                "history":       [],
                "review_run_id": None,
                "document_id": None,
            }
        return _chat_store[project_id]


def _load_context_from_review(
    project_id: int,
    review_run_id: int,
    document_id: int | None = None,
) -> str:
    try:
        from app.api.reviews import _get_review_in_project, _review_store, _store_lock

        review = _get_review_in_project(review_run_id, project_id)

        # 인메모리에 없으면 Redis에서 복원
        if not review:
            try:
                from app.services.storage.redis_store import load_review
                loaded = load_review(review_run_id)
                if loaded:
                    with _store_lock:
                        _review_store[review_run_id] = loaded
                    review = loaded
                    print(f"[Chat] Redis 복원 성공: run_id={review_run_id}")
            except Exception as e:
                print(f"[Chat] Redis 복원 실패: {e}")

        if not review:
            print(f"[Chat] review 없음: run_id={review_run_id}, project_id={project_id}")
            return ""

        files = review.get("files", [])
        print(f"[Chat] files 수: {len(files)}, document_id 요청: {document_id}")

        if document_id is not None:
            for f in files:
                # 타입 안전 비교
                if int(f.get("document_id", -1)) == int(document_id):
                    text = f.get("full_text", "")
                    print(f"[Chat] 문서 매칭: {f.get('filename')}, text 길이: {len(text)}")
                    if text:
                        return text
            print(f"[Chat] document_id={document_id} 매칭 실패, 전체 텍스트 fallback")

        if files:
            combined = "\n\n".join(
                f"=== {f.get('filename', '')} ===\n{f.get('full_text', '')}"
                for f in files
                if f.get("full_text")  # 빈 텍스트 제외
            )
            if combined:
                return combined

        # files에 full_text 없으면 review 레벨 full_text
        return review.get("full_text", "")

    except Exception as e:
        print(f"[Chat] 컨텍스트 로드 오류: {e}")
        return ""
# ──────────────────────────────────────────────
# 스키마
# ──────────────────────────────────────────────

class ChatRequest(BaseModel):
    question:         str      = Field(..., min_length=1, max_length=2000)
    review_run_id:    int | None = Field(None,  description="검토 실행 ID")
    document_id:      int | None = Field(None,  description="문서 ID — 해당 문서 텍스트만 컨텍스트로 사용")
    document_context: str | None = Field(None,  description="직접 텍스트 제공 (review_run_id 없을 때)")
    session_reset:    bool     = Field(False, description="히스토리 초기화")


# ──────────────────────────────────────────────
# 시스템 프롬프트 빌더
# ──────────────────────────────────────────────

BASE_SYSTEM_PROMPT = """당신은 대한민국 지방자치단체 계약서류 전문 검토 AI 어시스턴트입니다.
사용자가 업로드한 계약 관련 문서를 기반으로 질문에 답변합니다.

답변 원칙:
1. 반드시 제공된 문서 내용을 근거로 답변하세요.
2. 문서에 없는 내용은 "문서에서 확인되지 않습니다"라고 명시하세요.
3. 법령 관련 답변 시 조항을 구체적으로 인용하세요.
4. 수치(금액, 기간, 비율)는 정확하게 인용하세요.
5. 답변은 간결하고 명확하게, 핵심을 먼저 말하세요.
6. 문제점 발견 시 근거와 함께 수정 방향을 제시하세요."""


def _build_system_prompt(context: str) -> str:
    if not context:
        return BASE_SYSTEM_PROMPT
    # 컨텍스트를 시스템 프롬프트에 포함 (토큰 절약을 위해 6000자 제한)
    return f"""{BASE_SYSTEM_PROMPT}

=== 검토 대상 문서 ===
{context[:6000]}
=== 문서 끝 ==="""


def _build_messages(
    question: str,
    system_prompt: str,
    history: list[dict],
) -> list[dict]:
    messages = [{"role": "system", "content": system_prompt}]
    # 최근 20턴만 포함
    for msg in history[-20:]:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": question})
    return messages


# ──────────────────────────────────────────────
# SSE 스트리밍 채팅
# ──────────────────────────────────────────────

@router.post(
    "/stream",
    summary="스트리밍 채팅 (SSE)",
    description="""
검토된 문서 기반 RAG 채팅.

**review_run_id 넘기면 문서 자동 로드:**
```json
{
  "question": "노임단가 기준이 맞게 적용되었나요?",
  "review_run_id": 1
}
```

**SSE 이벤트:**
- `chunk`: 텍스트 청크
- `done`: 완료 { message_count }
- `error`: 오류
""",
)
async def chat_stream(
    project_id: int,
    body: ChatRequest,
) -> StreamingResponse:

    store = _get_or_create(project_id)

    if body.session_reset:
        store["history"]       = []
        store["context"]       = ""
        store["review_run_id"] = None
        store["document_id"] = None

    # 컨텍스트 로드 우선순위:
    # 1) review_run_id로 _review_store에서 자동 로드
    # 2) document_context 직접 제공
    # 3) 기존 세션 컨텍스트 유지
    # 문서/검토가 바뀌면 컨텍스트 + 히스토리 갱신
    new_review  = body.review_run_id and body.review_run_id != store.get("review_run_id")
    new_doc = body.document_id is not None and body.document_id != store.get("document_id")

    if body.review_run_id and (new_review or new_doc):
        context = _load_context_from_review(project_id, body.review_run_id, body.document_id)
        if not context:
            print(f"[Chat] 컨텍스트 없음 — 빈 컨텍스트로 진행 (run_id={body.review_run_id})")
            context = ""
        store["context"]       = context
        store["review_run_id"] = body.review_run_id
        store["document_id"]   = body.document_id
        store["history"]       = []   # 문서 바뀌면 히스토리 초기화
    elif body.document_context:
        store["context"]    = body.document_context
        store["document_id"] = body.document_id

    system_prompt = _build_system_prompt(store["context"])
    messages      = _build_messages(body.question, system_prompt, store["history"])

    async def generate() -> AsyncGenerator[str, None]:
        full_answer = ""
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                async with client.stream(
                    "POST",
                    f"{VLLM_BASE_URL}/chat/completions",
                    json={
                        "model":       VLLM_MODEL,
                        "messages":    messages,
                        "max_tokens":  4096,
                        "temperature": 0.1,
                        "stream":      True,
                    },
                ) as resp:
                    resp.raise_for_status()
                    async for line in resp.aiter_lines():
                        if not line.startswith("data: "):
                            continue
                        raw = line[6:].strip()
                        if raw == "[DONE]":
                            break
                        try:
                            delta = json.loads(raw)["choices"][0]["delta"].get("content", "")
                            if delta:
                                full_answer += delta
                                yield f"data: {json.dumps({'type': 'chunk', 'content': delta}, ensure_ascii=False)}\n\n"
                        except (json.JSONDecodeError, KeyError):
                            continue

        except httpx.TimeoutException:
            yield f"data: {json.dumps({'type': 'error', 'content': 'vLLM 응답 시간 초과'})}\n\n"
            return
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
            return

        # 히스토리 저장
        with _store_lock:
            store["history"].append({"role": "user",      "content": body.question})
            store["history"].append({"role": "assistant",  "content": full_answer})

        yield f"data: {json.dumps({'type': 'done', 'message_count': len(store['history']) // 2})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ──────────────────────────────────────────────
# 히스토리 조회 / 초기화
# ──────────────────────────────────────────────

@router.get("/history", summary="대화 히스토리 조회")
async def get_chat_history(project_id: int):
    store = _get_or_create(project_id)
    return {
        "project_id":    project_id,
        "review_run_id": store.get("review_run_id"),
        "has_context":   bool(store["context"]),
        "message_count": len(store["history"]) // 2,
        "messages":      store["history"],
    }


@router.delete("/history", summary="대화 히스토리 초기화")
async def clear_chat_history(project_id: int):
    with _store_lock:
        if project_id in _chat_store:
            _chat_store[project_id] = {
                "context": "",
                "history": [],
                "review_run_id": None,
                "document_id": None,
            }
    return {"success": True}