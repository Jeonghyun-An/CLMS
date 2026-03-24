from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter

from app.schemas.common import BBox, BaseResponse
from app.schemas.report import (
    GeneratedChecklistItemResponse,
    GeneratedChecklistResponse,
    HighlightFileResponse,
    HighlightItemResponse,
    HighlightResponse,
    ReportFileResponse,
)

router = APIRouter()


@router.get(
    "/reviews/{review_run_id}/report",
    response_model=BaseResponse[ReportFileResponse],
    summary="종합 리포트 조회",
    description="검토 결과로 생성된 종합 리포트 파일 정보를 조회합니다.",
)
async def get_review_report(review_run_id: int) -> BaseResponse[ReportFileResponse]:
    data = ReportFileResponse(
        report_id=3001,
        review_run_id=review_run_id,
        report_type="pdf",
        file_path=f"/data/reports/review_{review_run_id}.pdf",
        download_url=f"/files/reports/review_{review_run_id}.pdf",
        created_at=datetime.now(),
    )
    return BaseResponse(data=data)


@router.get(
    "/reviews/{review_run_id}/checklist",
    response_model=BaseResponse[GeneratedChecklistResponse],
    summary="생성 체크리스트 조회",
    description="검토 결과에 따라 생성된 체크리스트 결과를 조회합니다.",
)
async def get_review_checklist(review_run_id: int) -> BaseResponse[GeneratedChecklistResponse]:
    data = GeneratedChecklistResponse(
        review_run_id=review_run_id,
        items=[
            GeneratedChecklistItemResponse(
                item_code="CHK-001",
                title="사업기간 명시 여부",
                description="계획서 및 관련 문서에 사업기간이 명시되어 있는지 확인",
                required_flag=True,
                result="pass",
                comment="사업기간이 계획서 본문에 명시되어 있습니다.",
                related_issue_id=None,
            ),
            GeneratedChecklistItemResponse(
                item_code="CHK-002",
                title="총 금액 일치 여부",
                description="계획서, 시행문, 산출내역서 상 총액 일치 여부 확인",
                required_flag=True,
                result="fail",
                comment="계획서 본문 금액과 산출내역서 합계가 상이합니다.",
                related_issue_id=9001,
            ),
        ],
    )
    return BaseResponse(data=data)


@router.get(
    "/reviews/{review_run_id}/highlights/{document_id}",
    response_model=BaseResponse[HighlightResponse],
    summary="하이라이트 좌표 조회",
    description="문서 뷰어에서 사용할 하이라이트 좌표 목록을 조회합니다.",
)
async def get_review_highlights(
    review_run_id: int,
    document_id: int,
) -> BaseResponse[HighlightResponse]:
    data = HighlightResponse(
        review_run_id=review_run_id,
        document_id=document_id,
        items=[
            HighlightItemResponse(
                issue_id=9001,
                page_no=3,
                bbox=BBox(x1=120, y1=420, x2=300, y2=450),
                color="red",
                label="총 사업비 불일치",
            ),
            HighlightItemResponse(
                issue_id=9002,
                page_no=1,
                bbox=BBox(x1=100, y1=180, x2=220, y2=210),
                color="yellow",
                label="필수 항목 확인 필요",
            ),
        ],
    )
    return BaseResponse(data=data)


@router.get(
    "/reviews/{review_run_id}/highlight-file/{document_id}",
    response_model=BaseResponse[HighlightFileResponse],
    summary="하이라이트 렌더 파일 조회",
    description="하이라이트가 적용된 렌더링 결과 파일 경로를 조회합니다.",
)
async def get_review_highlight_file(
    review_run_id: int,
    document_id: int,
) -> BaseResponse[HighlightFileResponse]:
    data = HighlightFileResponse(
        review_run_id=review_run_id,
        document_id=document_id,
        rendered_file_path=f"/data/highlights/review_{review_run_id}_doc_{document_id}.pdf",
        download_url=f"/files/highlights/review_{review_run_id}_doc_{document_id}.pdf",
    )
    return BaseResponse(data=data)