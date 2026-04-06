"""
Redis 기반 영속 저장소
────────────────────────────────────────────────────────────
- 검토 결과 (_review_store) → Redis Hash
- 검토 ID 카운터 (_review_counter) → Redis INCR
- 채팅 히스토리 (_chat_store) → Redis Hash
- TTL: 7일 (발표 후에도 유지)
"""

from __future__ import annotations

import json
import os

import redis

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
TTL       = 60 * 60 * 24 * 7  # 7일

_client: redis.Redis | None = None


def get_client() -> redis.Redis:
    global _client
    if _client is None:
        _client = redis.from_url(REDIS_URL, decode_responses=True)
    return _client


# ──────────────────────────────────────────────
# 검토 ID 카운터
# ──────────────────────────────────────────────

def next_review_id() -> int:
    """재시작해도 이어서 증가하는 ID"""
    try:
        return get_client().incr("clms:review_counter")
    except Exception as e:
        print(f"[Redis] ID 생성 실패, 타임스탬프 사용: {e}")
        import time
        return int(time.time() * 1000) % 100000


# ──────────────────────────────────────────────
# 검토 결과 저장소
# ──────────────────────────────────────────────

def save_review(run_id: int, data: dict) -> bool:
    """검토 결과 저장"""
    try:
        import copy
        data = copy.deepcopy(data)  # 원본 데이터 보호
        
        key = f"clms:review:{run_id}"
        # full_text는 용량이 크므로 별도 키로 분리
        full_text = data.pop("full_text", "")
        files     = data.get("files", [])

        # files 안의 full_text도 별도 저장
        for i, f in enumerate(files):
            ft = f.pop("full_text", "")
            if ft:
                get_client().setex(
                    f"clms:review:{run_id}:file:{f.get('document_id', i)}:text",
                    TTL, ft
                )

        client = get_client()
        client.setex(key, TTL, json.dumps(data, ensure_ascii=False))
        if full_text:
            client.setex(f"{key}:text", TTL, full_text)
        return True
    except Exception as e:
        print(f"[Redis] 검토 결과 저장 실패: {e}")
        return False


def load_review(run_id: int) -> dict | None:
    """검토 결과 로드"""
    try:
        client = get_client()
        key    = f"clms:review:{run_id}"
        raw    = client.get(key)
        if not raw:
            return None
        data      = json.loads(raw)
        full_text = client.get(f"{key}:text") or ""
        data["full_text"] = full_text

        # files 안의 full_text 복원
        for f in data.get("files", []):
            doc_id = f.get("document_id")
            if doc_id:
                ft = client.get(f"clms:review:{run_id}:file:{doc_id}:text") or ""
                f["full_text"] = ft
        return data
    except Exception as e:
        print(f"[Redis] 검토 결과 로드 실패: {e}")
        return None


def list_reviews(limit: int = 50) -> list[int]:
    """최근 검토 run_id 목록"""
    try:
        keys = get_client().keys("clms:review:*")
        ids  = []
        for k in keys:
            parts = k.split(":")
            if len(parts) == 3 and parts[2].isdigit():
                ids.append(int(parts[2]))
        return sorted(ids, reverse=True)[:limit]
    except Exception:
        return []


# ──────────────────────────────────────────────
# 채팅 히스토리
# ──────────────────────────────────────────────

def save_chat(project_id: int, data: dict) -> bool:
    try:
        # full_text(context)는 별도 저장
        context = data.pop("context", "")
        client  = get_client()
        key     = f"clms:chat:{project_id}"
        client.setex(key, TTL, json.dumps(data, ensure_ascii=False))
        if context:
            client.setex(f"{key}:context", TTL, context)
        return True
    except Exception as e:
        print(f"[Redis] 채팅 저장 실패: {e}")
        return False


def load_chat(project_id: int) -> dict | None:
    try:
        client = get_client()
        key    = f"clms:chat:{project_id}"
        raw    = client.get(key)
        if not raw:
            return None
        data    = json.loads(raw)
        context = client.get(f"{key}:context") or ""
        data["context"] = context
        return data
    except Exception as e:
        print(f"[Redis] 채팅 로드 실패: {e}")
        return None