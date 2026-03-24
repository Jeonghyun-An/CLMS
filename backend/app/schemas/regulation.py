from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from app.schemas.common import BaseSchema, PaginationMeta
from app.schemas.enums import RegulationType


class RegulationListItemResponse(BaseSchema):
    id: int
    regulation_type: RegulationType
    title: str
    version: Optional[str] = None
    effective_date: Optional[date] = None
    is_active: bool
    created_at: datetime


class RegulationListResponse(BaseSchema):
    items: list[RegulationListItemResponse]
    meta: PaginationMeta


class RegulationDetailResponse(BaseSchema):
    id: int
    regulation_type: RegulationType
    title: str
    version: Optional[str] = None
    effective_date: Optional[date] = None
    source_path: Optional[str] = None
    is_active: bool
    created_at: datetime


class RegulationArticleResponse(BaseSchema):
    id: int
    article_no: Optional[str] = None
    article_title: Optional[str] = None
    content: str
    parent_article_id: Optional[int] = None


class RegulationArticlesResponse(BaseSchema):
    regulation_id: int
    items: list[RegulationArticleResponse]


class RegulationSearchResultItem(BaseSchema):
    regulation_id: int
    regulation_title: str
    article_id: Optional[int] = None
    article_no: Optional[str] = None
    article_title: Optional[str] = None
    chunk_text: str
    score: float


class RegulationSearchResponse(BaseSchema):
    query: str
    items: list[RegulationSearchResultItem]