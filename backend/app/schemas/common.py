from __future__ import annotations

from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel, Field, ConfigDict


T = TypeVar("T")


class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class BaseResponse(BaseSchema, Generic[T]):
    success: bool = True
    message: str = "OK"
    data: Optional[T] = None


class ErrorResponse(BaseSchema):
    success: bool = False
    message: str
    error_code: str
    details: Optional[Any] = None


class PaginationMeta(BaseSchema):
    page: int = Field(..., ge=1, description="현재 페이지")
    size: int = Field(..., ge=1, le=100, description="페이지 크기")
    total: int = Field(..., ge=0, description="전체 건수")
    total_pages: int = Field(..., ge=0, description="전체 페이지 수")


class BBox(BaseSchema):
    x1: float = Field(..., description="좌상단 X")
    y1: float = Field(..., description="좌상단 Y")
    x2: float = Field(..., description="우하단 X")
    y2: float = Field(..., description="우하단 Y")


class DeleteResponse(BaseSchema):
    deleted: bool = True
    id: int


class HealthCheckResponse(BaseSchema):
    status: str = "ok"
    service: str = "clms-seocho-backend"