from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Query, status

from app.schemas.common import BBox, BaseResponse, PaginationMeta
from app.schemas.enums import (
    DocumentType,
    IssueCategory,
    ParseStatus,
    ReviewResult,
    ReviewStatus,
    SeverityLevel,
)
from app.schemas.review import (
    ApprovalLineResponse,
    IssueEvidenceResponse,
    RegulationReference,
    ReviewCreateRequest,
    ReviewCreateResponse,
    ReviewIssueDetailResponse,
    ReviewIssueListItemResponse,
    ReviewIssueListResponse,
    ReviewRunDocumentResponse,
    ReviewRunDocumentsResponse,
    ReviewStatusResponse,
    ReviewSummaryResponse,
)

router = APIRouter()


@router.post(
    "/projects/{project_id}/reviews",
    response_model=BaseResponse[ReviewCreateResponse],
    status_code=status.HTTP_201_CREATED,
    summary="검토 실행 요청",
    description="선택한 문서들을 기준으로 검토 작업을 생성합니다.",
)
async def create_review_run(
    project_id: int,
    body: ReviewCreateRequest,
) -> BaseResponse[ReviewCreateResponse]:
    data = ReviewCreateResponse(
        review_run_id=501,
        project_id=project_id,
        status=ReviewStatus.pending,
        created_at=datetime.now(),
    )
    return BaseResponse(data=data)


@router.get(
    "/reviews/{review_run_id}/status",
    response_model=BaseResponse[ReviewStatusResponse],
    summary="검토 상태 조회",
    description="검토 작업의 현재 진행 상태를 조회합니다.",
)
async def get_review_status(review_run_id: int) -> BaseResponse[ReviewStatusResponse]:
    data = ReviewStatusResponse(
        review_run_id=review_run_id,
        status=ReviewStatus.running,
        progress=65,
        current_step="rule_engine_review",
        started_at=datetime.now(),
        finished_at=None,
    )
    return BaseResponse(data=data)


@router.get(
    "/reviews/{review_run_id}/summary",
    response_model=BaseResponse[ReviewSummaryResponse],
    summary="검토 요약 조회",
    description="검토 결과의 종합 요약을 조회합니다.",
)
async def get_review_summary(review_run_id: int) -> BaseResponse[ReviewSummaryResponse]:
    data = ReviewSummaryResponse(
        review_run_id=review_run_id,
        overall_result=ReviewResult.conditional_pass,
        risk_score=72.5,
        issue_count=5,
        high_issue_count=2,
        warning_issue_count=2,
        info_issue_count=1,
        summary_text="총사업비 불일치와 첨부문서 누락이 확인되었습니다.",
    )
    return BaseResponse(data=data)


@router.get(
    "/reviews/{review_run_id}/documents",
    response_model=BaseResponse[ReviewRunDocumentsResponse],
    summary="검토 대상 문서 조회",
    description="검토 실행에 포함된 문서 목록을 조회합니다.",
)
async def get_review_documents(review_run_id: int) -> BaseResponse[ReviewRunDocumentsResponse]:
    data = ReviewRunDocumentsResponse(
        review_run_id=review_run_id,
        items=[
            ReviewRunDocumentResponse(
                document_id=1001,
                original_filename="계획서.hwpx",
                role_in_review="plan",
                doc_type_confirmed=DocumentType.plan,
                parse_status=ParseStatus.done,
            ),
            ReviewRunDocumentResponse(
                document_id=1002,
                original_filename="산출내역서.xlsx",
                role_in_review="estimate",
                doc_type_confirmed=DocumentType.estimate_sheet,
                parse_status=ParseStatus.done,
            ),
        ],
    )
    return BaseResponse(data=data)


@router.get(
    "/reviews/{review_run_id}/issues",
    response_model=BaseResponse[ReviewIssueListResponse],
    summary="검토 이슈 목록 조회",
    description="검토 결과에서 발생한 이슈 목록을 조회합니다.",
)
async def get_review_issues(
    review_run_id: int,
    severity: SeverityLevel | None = Query(None),
    category: IssueCategory | None = Query(None),
    document_id: int | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
) -> BaseResponse[ReviewIssueListResponse]:
    items = [
        ReviewIssueListItemResponse(
            id=9001,
            document_id=document_id or 1001,
            severity=severity or SeverityLevel.high,
            category=category or IssueCategory.inconsistency,
            title="총 사업비 불일치",
            description="계획서 본문 금액과 산출내역서 합계 금액이 서로 다릅니다.",
            recommendation="기준 금액 문서를 확정하고 모든 관련 문서를 동일하게 수정하세요.",
            status=status_filter or "open",
            created_at=datetime.now(),
        )
    ]
    data = ReviewIssueListResponse(
        items=items,
        meta=PaginationMeta(page=page, size=size, total=1, total_pages=1),
    )
    return BaseResponse(data=data)


@router.get(
    "/reviews/{review_run_id}/issues/{issue_id}",
    response_model=BaseResponse[ReviewIssueDetailResponse],
    summary="검토 이슈 상세 조회",
    description="이슈의 근거 문구, 규정 참조, 하이라이트 좌표를 상세 조회합니다.",
)
async def get_review_issue_detail(
    review_run_id: int,
    issue_id: int,
) -> BaseResponse[ReviewIssueDetailResponse]:
    data = ReviewIssueDetailResponse(
        id=issue_id,
        review_run_id=review_run_id,
        document_id=1001,
        severity=SeverityLevel.high,
        category=IssueCategory.inconsistency,
        title="총 사업비 불일치",
        description="계획서 본문 금액과 산출내역서 총액이 상이합니다.",
        recommendation="예산 기준 문서를 확정한 후 동일 금액으로 정정하십시오.",
        regulation_refs=[
            RegulationReference(
                regulation_id=1,
                regulation_title="내부 체크리스트",
                article_id=11,
                article_no="CHK-002",
                article_title="총 금액 일치 여부",
                quoted_text="계획서, 시행문, 내역서 상 금액은 상호 일치해야 한다.",
            )
        ],
        evidences=[
            IssueEvidenceResponse(
                id=1,
                document_id=1001,
                page_no=3,
                block_id=17,
                quoted_text="총 사업비 : 120,000,000원",
                bbox=BBox(x1=120, y1=420, x2=300, y2=450),
            ),
            IssueEvidenceResponse(
                id=2,
                document_id=1002,
                page_no=None,
                cell_id=220,
                quoted_text="합계 118,500,000",
                bbox=None,
            ),
        ],
        status="open",
        created_at=datetime.now(),
    )
    return BaseResponse(data=data)


@router.get(
    "/reviews/{review_run_id}/approval-line",
    response_model=BaseResponse[ApprovalLineResponse],
    summary="결재선 조회",
    description="검토 결과에 따라 적용된 결재선 안내를 조회합니다.",
)
async def get_approval_line(review_run_id: int) -> BaseResponse[ApprovalLineResponse]:
    data = ApprovalLineResponse(
        review_run_id=review_run_id,
        required=True,
        rule_id=3001,
        rule_name="5000만원 이상 용역 계약 결재선",
        steps=["담당", "팀장", "과장", "국장"],
        reference_text="사무전결규정 제X조",
    )
    return BaseResponse(data=data)