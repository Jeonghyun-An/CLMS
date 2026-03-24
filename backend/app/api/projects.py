from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Query, status

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


@router.post(
    "",
    response_model=BaseResponse[ProjectResponse],
    status_code=status.HTTP_201_CREATED,
    summary="프로젝트 생성",
    description="새로운 계약 검토 프로젝트를 생성합니다.",
)
async def create_project(body: ProjectCreateRequest) -> BaseResponse[ProjectResponse]:
    now = datetime.now()
    data = ProjectResponse(
        id=1,
        name=body.name,
        description=body.description,
        status=ProjectStatus.draft,
        created_by=1,
        created_at=now,
        updated_at=now,
    )
    return BaseResponse(data=data)


@router.get(
    "",
    response_model=BaseResponse[ProjectListResponse],
    summary="프로젝트 목록 조회",
    description="프로젝트 목록을 페이징하여 조회합니다.",
)
async def list_projects(
    page: int = Query(1, ge=1, description="페이지 번호"),
    size: int = Query(20, ge=1, le=100, description="페이지 크기"),
    status_filter: ProjectStatus | None = Query(None, alias="status", description="프로젝트 상태"),
    keyword: str | None = Query(None, description="프로젝트명 검색어"),
) -> BaseResponse[ProjectListResponse]:
    items = [
        ProjectListItem(
            id=1,
            name="서초구 AI 계약검토 PoC",
            description="샘플 프로젝트",
            status=status_filter or ProjectStatus.draft,
            document_count=3,
            latest_review_status=ReviewStatus.pending,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
    ]
    data = ProjectListResponse(
        items=items,
        meta=PaginationMeta(page=page, size=size, total=1, total_pages=1),
    )
    return BaseResponse(data=data)


@router.get(
    "/{project_id}",
    response_model=BaseResponse[ProjectDetailResponse],
    summary="프로젝트 상세 조회",
    description="특정 프로젝트의 상세 정보를 조회합니다.",
)
async def get_project(project_id: int) -> BaseResponse[ProjectDetailResponse]:
    data = ProjectDetailResponse(
        id=project_id,
        name="서초구 AI 계약검토 PoC",
        description="샘플 프로젝트 상세",
        status=ProjectStatus.draft,
        created_by=1,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        document_count=5,
        latest_review_id=101,
        latest_review_status=ReviewStatus.running,
    )
    return BaseResponse(data=data)


@router.put(
    "/{project_id}",
    response_model=BaseResponse[ProjectResponse],
    summary="프로젝트 수정",
    description="프로젝트 정보를 수정합니다.",
)
async def update_project(
    project_id: int,
    body: ProjectUpdateRequest,
) -> BaseResponse[ProjectResponse]:
    now = datetime.now()
    data = ProjectResponse(
        id=project_id,
        name=body.name or "서초구 AI 계약검토 PoC",
        description=body.description,
        status=body.status or ProjectStatus.draft,
        created_by=1,
        created_at=now,
        updated_at=now,
    )
    return BaseResponse(data=data)


@router.delete(
    "/{project_id}",
    response_model=BaseResponse[DeleteResponse],
    summary="프로젝트 삭제",
    description="프로젝트를 삭제합니다.",
)
async def delete_project(project_id: int) -> BaseResponse[DeleteResponse]:
    return BaseResponse(data=DeleteResponse(deleted=True, id=project_id))