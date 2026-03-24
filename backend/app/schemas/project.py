from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import Field

from app.schemas.common import BaseSchema, PaginationMeta
from app.schemas.enums import ProjectStatus, ReviewStatus


class ProjectCreateRequest(BaseSchema):
    name: str = Field(..., min_length=1, max_length=255, example="서초구 AI 계약검토 PoC")
    description: Optional[str] = Field(None, example="2026년 시범사업 계약서류 자동검토 프로젝트")


class ProjectUpdateRequest(BaseSchema):
    name: Optional[str] = Field(None, min_length=1, max_length=255, example="서초구 AI 계약검토 PoC 수정")
    description: Optional[str] = Field(None, example="설명 수정")
    status: Optional[ProjectStatus] = Field(None, example=ProjectStatus.in_review)


class ProjectResponse(BaseSchema):
    id: int
    name: str
    description: Optional[str] = None
    status: ProjectStatus
    created_by: int
    created_at: datetime
    updated_at: datetime


class ProjectListItem(BaseSchema):
    id: int
    name: str
    description: Optional[str] = None
    status: ProjectStatus
    document_count: int = 0
    latest_review_status: Optional[ReviewStatus] = None
    created_at: datetime
    updated_at: datetime


class ProjectListResponse(BaseSchema):
    items: list[ProjectListItem]
    meta: PaginationMeta


class ProjectDetailResponse(BaseSchema):
    id: int
    name: str
    description: Optional[str] = None
    status: ProjectStatus
    created_by: int
    created_at: datetime
    updated_at: datetime
    document_count: int = 0
    latest_review_id: Optional[int] = None
    latest_review_status: Optional[ReviewStatus] = None