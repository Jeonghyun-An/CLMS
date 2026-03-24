from __future__ import annotations

from datetime import date, datetime

from fastapi import APIRouter, Query

from app.schemas.common import BaseResponse, PaginationMeta
from app.schemas.enums import RegulationType
from app.schemas.regulation import (
    RegulationArticleResponse,
    RegulationArticlesResponse,
    RegulationDetailResponse,
    RegulationListItemResponse,
    RegulationListResponse,
    RegulationSearchResponse,
    RegulationSearchResultItem,
)

router = APIRouter()


@router.get(
    "",
    response_model=BaseResponse[RegulationListResponse],
    summary="규정 목록 조회",
    description="법령, 지침, 내부규정 목록을 조회합니다.",
)
async def list_regulations(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    regulation_type: RegulationType | None = Query(None),
    keyword: str | None = Query(None),
    is_active: bool | None = Query(None),
) -> BaseResponse[RegulationListResponse]:
    item_type = regulation_type or RegulationType.law
    active_value = True if is_active is None else is_active

    data = RegulationListResponse(
        items=[
            RegulationListItemResponse(
                id=1,
                regulation_type=item_type,
                title="지방계약법 시행지침",
                version="2026.01",
                effective_date=date(2026, 1, 1),
                is_active=active_value,
                created_at=datetime.now(),
            ),
            RegulationListItemResponse(
                id=2,
                regulation_type=RegulationType.internal_rule,
                title="사무전결규정",
                version="2025.12",
                effective_date=date(2025, 12, 1),
                is_active=True,
                created_at=datetime.now(),
            ),
        ],
        meta=PaginationMeta(page=page, size=size, total=2, total_pages=1),
    )
    return BaseResponse(data=data)


@router.get(
    "/{regulation_id}",
    response_model=BaseResponse[RegulationDetailResponse],
    summary="규정 상세 조회",
    description="특정 법령/지침/내부규정의 상세 정보를 조회합니다.",
)
async def get_regulation(regulation_id: int) -> BaseResponse[RegulationDetailResponse]:
    data = RegulationDetailResponse(
        id=regulation_id,
        regulation_type=RegulationType.guideline,
        title="지방계약법 시행지침",
        version="2026.01",
        effective_date=date(2026, 1, 1),
        source_path="/data/regulations/local_contract_guideline_202601.pdf",
        is_active=True,
        created_at=datetime.now(),
    )
    return BaseResponse(data=data)


@router.get(
    "/{regulation_id}/articles",
    response_model=BaseResponse[RegulationArticlesResponse],
    summary="규정 조문 조회",
    description="규정에 포함된 조문 또는 항목을 조회합니다.",
)
async def get_regulation_articles(regulation_id: int) -> BaseResponse[RegulationArticlesResponse]:
    data = RegulationArticlesResponse(
        regulation_id=regulation_id,
        items=[
            RegulationArticleResponse(
                id=11,
                article_no="제11조",
                article_title="계약 체결 기준",
                content="계약 체결 시 금액, 기간, 계약방법 등에 관한 기준을 확인하여야 한다.",
                parent_article_id=None,
            ),
            RegulationArticleResponse(
                id=12,
                article_no="제12조",
                article_title="필수 서류 검토",
                content="계약 유형에 따라 필수 서류를 제출받아 검토하여야 한다.",
                parent_article_id=None,
            ),
        ],
    )
    return BaseResponse(data=data)


@router.get(
    "/search",
    response_model=BaseResponse[RegulationSearchResponse],
    summary="규정 검색",
    description="RAG 기반 규정 검색 결과를 조회합니다.",
)
async def search_regulations(
    query: str = Query(..., min_length=1, description="검색 질의"),
    doc_type: str | None = Query(None, description="문서 유형"),
    top_k: int = Query(5, ge=1, le=20, description="검색 결과 개수"),
) -> BaseResponse[RegulationSearchResponse]:
    items = [
        RegulationSearchResultItem(
            regulation_id=1,
            regulation_title="지방계약법 시행지침",
            article_id=11,
            article_no="제11조",
            article_title="계약 체결 기준",
            chunk_text="계약 체결 시 금액, 기간, 계약방법 등에 관한 기준을 확인하여야 한다.",
            score=0.9321,
        ),
        RegulationSearchResultItem(
            regulation_id=2,
            regulation_title="사무전결규정",
            article_id=21,
            article_no="제21조",
            article_title="결재선 기준",
            chunk_text="계약 규모에 따라 담당, 팀장, 과장, 국장 결재 절차를 따른다.",
            score=0.9012,
        ),
    ][:top_k]

    data = RegulationSearchResponse(query=query, items=items)
    return BaseResponse(data=data)