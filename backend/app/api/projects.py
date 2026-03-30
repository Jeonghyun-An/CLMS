"""
프로젝트 API — Redis 영속 저장
"""
from __future__ import annotations

import threading
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, status

from app.schemas.common import BaseResponse, DeleteResponse, PaginationMeta
from app.schemas.enums import ProjectStatus, ReviewStatus
from app.schemas.project import (
    ProjectCreateRequest,
    ProjectDetailResponse,
    ProjectListItem,
    ProjectListResponse,
    ProjectResponse,
    ProjectUpdateRequest,
)

router = APIRouter()

# ──────────────────────────────────────────────
# 저장소 — 인메모리 + Redis
# ──────────────────────────────────────────────
_project_store: dict[int, dict] = {}
_store_lock = threading.Lock()


def _next_project_id() -> int:
    try:
        from app.services.storage.redis_store import get_client
        return get_client().incr("clms:project_counter")
    except Exception:
        with _store_lock:
            return max(_project_store.keys(), default=0) + 1


def _save_project(pid: int, data: dict):
    with _store_lock:
        _project_store[pid] = data
    try:
        import json
        from app.services.storage.redis_store import get_client
        get_client().setex(
            f"clms:project:{pid}",
            60 * 60 * 24 * 30,  # 30일
            json.dumps(data, ensure_ascii=False, default=str),
        )
    except Exception as e:
        print(f"[Redis] 프로젝트 저장 실패: {e}")


def _get_project(pid: int) -> dict | None:
    if pid in _project_store:
        return _project_store[pid]
    try:
        import json
        from app.services.storage.redis_store import get_client
        raw = get_client().get(f"clms:project:{pid}")
        if raw:
            data = json.loads(raw)
            with _store_lock:
                _project_store[pid] = data
            return data
    except Exception:
        pass
    return None


def _list_all_projects() -> list[dict]:
    try:
        import json
        from app.services.storage.redis_store import get_client
        keys = get_client().keys("clms:project:*")
        projects = []
        for k in keys:
            if k.count(":") == 2:  # clms:project:{id} 형식만
                raw = get_client().get(k)
                if raw:
                    projects.append(json.loads(raw))
        return sorted(projects, key=lambda x: x.get("created_at", ""), reverse=True)
    except Exception:
        return list(_project_store.values())


# ──────────────────────────────────────────────
# 엔드포인트
# ──────────────────────────────────────────────

@router.post(
    "",
    response_model=BaseResponse[ProjectResponse],
    status_code=status.HTTP_201_CREATED,
    summary="프로젝트 생성",
)
async def create_project(body: ProjectCreateRequest) -> BaseResponse[ProjectResponse]:
    now = datetime.now().isoformat()
    pid = _next_project_id()
    data = {
        "id":          pid,
        "name":        body.name,
        "description": body.description,
        "status":      ProjectStatus.draft,
        "created_by":  1,
        "created_at":  now,
        "updated_at":  now,
        "document_count": 0,
        "latest_review_id": None,
        "latest_review_status": None,
    }
    _save_project(pid, data)
    return BaseResponse(data=ProjectResponse(**{**data, "created_at": datetime.fromisoformat(now), "updated_at": datetime.fromisoformat(now)}))


@router.get(
    "",
    response_model=BaseResponse[ProjectListResponse],
    summary="프로젝트 목록",
)
async def list_projects(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status_filter: ProjectStatus | None = Query(None, alias="status"),
    keyword: str | None = Query(None),
) -> BaseResponse[ProjectListResponse]:
    all_projects = _list_all_projects()
    try:
        from app.api.documents import _document_store

        for p in all_projects:
            pid = p.get("id")
            p["document_count"] = sum(
                1 for meta in _document_store.values()
                if meta.get("project_id") == pid
            )
    except Exception:
        pass

    if status_filter:
        all_projects = [p for p in all_projects if p.get("status") == status_filter]
    if keyword:
        all_projects = [p for p in all_projects if keyword in p.get("name", "")]

    total = len(all_projects)
    start = (page - 1) * size
    paged = all_projects[start:start + size]

    items = [
        ProjectListItem(
            id=p["id"],
            name=p["name"],
            description=p.get("description"),
            status=p.get("status", ProjectStatus.draft),
            document_count=p.get("document_count", 0),
            latest_review_status=p.get("latest_review_status"),
            created_at=datetime.fromisoformat(p["created_at"]),
            updated_at=datetime.fromisoformat(p["updated_at"]),
        )
        for p in paged
    ]

    return BaseResponse(data=ProjectListResponse(
        items=items,
        meta=PaginationMeta(page=page, size=size, total=total, total_pages=(total + size - 1) // size or 1),
    ))


@router.get(
    "/{project_id}",
    response_model=BaseResponse[ProjectDetailResponse],
    summary="프로젝트 상세",
)
async def get_project(project_id: int) -> BaseResponse[ProjectDetailResponse]:
    p = _get_project(project_id)
    if not p:
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다.")
    try:
        from app.api.documents import _document_store
        p["document_count"] = sum(
            1 for meta in _document_store.values()
            if meta.get("project_id") == project_id
        )
    except Exception:
        pass
    return BaseResponse(data=ProjectDetailResponse(
        id=p["id"],
        name=p["name"],
        description=p.get("description"),
        status=p.get("status", ProjectStatus.draft),
        created_by=p.get("created_by", 1),
        created_at=datetime.fromisoformat(p["created_at"]),
        updated_at=datetime.fromisoformat(p["updated_at"]),
        document_count=p.get("document_count", 0),
        latest_review_id=p.get("latest_review_id"),
        latest_review_status=p.get("latest_review_status"),
    ))


@router.put(
    "/{project_id}",
    response_model=BaseResponse[ProjectResponse],
    summary="프로젝트 수정",
)
async def update_project(project_id: int, body: ProjectUpdateRequest) -> BaseResponse[ProjectResponse]:
    p = _get_project(project_id)
    if not p:
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다.")

    now = datetime.now().isoformat()
    if body.name is not None:
        p["name"] = body.name
    if body.description is not None:
        p["description"] = body.description
    if body.status is not None:
        p["status"] = body.status
    p["updated_at"] = now

    _save_project(project_id, p)
    return BaseResponse(data=ProjectResponse(**{**p, "created_at": datetime.fromisoformat(p["created_at"]), "updated_at": datetime.fromisoformat(now)}))


@router.delete(
    "/{project_id}",
    response_model=BaseResponse[DeleteResponse],
    summary="프로젝트 삭제",
)
async def delete_project(project_id: int) -> BaseResponse[DeleteResponse]:
    p = _get_project(project_id)
    if not p:
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다.")
    with _store_lock:
        _project_store.pop(project_id, None)
    try:
        from app.services.storage.redis_store import get_client
        get_client().delete(f"clms:project:{project_id}")
    except Exception:
        pass
    return BaseResponse(data=DeleteResponse(deleted=True, id=project_id))