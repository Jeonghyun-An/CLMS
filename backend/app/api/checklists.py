from __future__ import annotations

from fastapi import APIRouter

from app.schemas.checklist import (
    ChecklistTemplateDetailResponse,
    ChecklistTemplateItemResponse,
    ChecklistTemplateListItemResponse,
    ChecklistTemplateListResponse,
)
from app.schemas.common import BaseResponse
from app.schemas.enums import DocumentType

router = APIRouter()


@router.get(
    "/templates",
    response_model=BaseResponse[ChecklistTemplateListResponse],
    summary="체크리스트 템플릿 목록 조회",
    description="문서 유형별 체크리스트 템플릿 목록을 조회합니다.",
)
async def list_checklist_templates() -> BaseResponse[ChecklistTemplateListResponse]:
    data = ChecklistTemplateListResponse(
        items=[
            ChecklistTemplateListItemResponse(
                id=1,
                name="계획서 검토 체크리스트",
                doc_type=DocumentType.plan,
                version="v1.0",
                is_active=True,
            ),
            ChecklistTemplateListItemResponse(
                id=2,
                name="산출내역서 검토 체크리스트",
                doc_type=DocumentType.estimate_sheet,
                version="v1.0",
                is_active=True,
            ),
        ]
    )
    return BaseResponse(data=data)


@router.get(
    "/templates/{template_id}",
    response_model=BaseResponse[ChecklistTemplateDetailResponse],
    summary="체크리스트 템플릿 상세 조회",
    description="체크리스트 템플릿의 상세 항목을 조회합니다.",
)
async def get_checklist_template(template_id: int) -> BaseResponse[ChecklistTemplateDetailResponse]:
    data = ChecklistTemplateDetailResponse(
        id=template_id,
        name="계획서 검토 체크리스트",
        doc_type=DocumentType.plan,
        version="v1.0",
        is_active=True,
        items=[
            ChecklistTemplateItemResponse(
                id=101,
                item_code="CHK-001",
                item_title="사업명 명시 여부",
                description="문서 내 사업명이 명시되어 있는지 확인",
                required_flag=True,
                related_regulation_id=1,
                related_article_id=11,
                rule_expression="exists(entity:project_name)",
            ),
            ChecklistTemplateItemResponse(
                id=102,
                item_code="CHK-002",
                item_title="총 금액 일치 여부",
                description="관련 문서 간 총 금액이 일치하는지 확인",
                required_flag=True,
                related_regulation_id=1,
                related_article_id=12,
                rule_expression="compare(amount_total, related_docs)",
            ),
        ],
    )
    return BaseResponse(data=data)