"""
검토 실행 API — 목업 → 룰 엔진 연동 버전
────────────────────────────────────────────────────────────
POST /projects/{project_id}/reviews          검토 실행 (OCR JSON → 룰 엔진)
GET  /reviews/{review_run_id}/status         검토 상태
GET  /reviews/{review_run_id}/summary        검토 요약
GET  /reviews/{review_run_id}/issues         이슈 목록
GET  /reviews/{review_run_id}/issues/{id}    이슈 상세
GET  /reviews/{review_run_id}/approval-line  결재선 안내
GET  /reviews/{review_run_id}/documents      검토 문서 목록
"""

from __future__ import annotations

import threading
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Body, HTTPException, Query, status

from app.schemas.common import BaseResponse, BBox, PaginationMeta
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
from app.services.review.engine import (
    ParsedDocument,
    issues_to_api_response,
    run_review,
    run_review_from_ocr,
)

router = APIRouter()

# ──────────────────────────────────────────────
# 인메모리 저장소 (PoC용 — DB 없이 동작)
# ──────────────────────────────────────────────
# { review_run_id: { "status": ..., "issues": [...], "document_id": int } }
_review_store: dict[int, dict[str, Any]] = {}
_review_counter = 0
_store_lock = threading.Lock()


def _next_run_id() -> int:
    global _review_counter
    with _store_lock:
        _review_counter += 1
        return _review_counter


# ──────────────────────────────────────────────
# 엔드포인트
# ──────────────────────────────────────────────

@router.post(
    "",
    response_model=BaseResponse[ReviewCreateResponse],
    status_code=status.HTTP_201_CREATED,
    summary="검토 실행",
    description="""
OCR 결과 JSON을 body에 포함하거나, document_ids만 넘기면 목업 텍스트로 실행합니다.

**OCR JSON 포맷 (body.ocr_data):**
```json
{
  "document_id": 1001,
  "pages": [
    {
      "page_no": 1,
      "blocks": [
        { "block_id": 1, "text": "용역 계획서", "bbox": [100,100,320,145] }
      ]
    }
  ]
}
```
ocr_data 없이 호출하면 샘플 텍스트로 룰 엔진을 실행합니다.
""",
)
async def create_review(
    project_id: int,
    body: ReviewCreateRequest,
    ocr_data: dict | None = Body(None, embed=True, description="OCR 파싱 결과 JSON"),
) -> BaseResponse[ReviewCreateResponse]:
    run_id = _next_run_id()
    doc_id = body.document_ids[0] if body.document_ids else 1001

    # OCR 데이터가 있으면 실제 엔진, 없으면 샘플로 실행
    if ocr_data:
        ocr_data["document_id"] = doc_id
        issues_raw = run_review_from_ocr(ocr_data)
    else:
        issues_raw = run_review(_make_sample_document(doc_id))

    issues_serialized = issues_to_api_response(issues_raw, run_id, doc_id)

    with _store_lock:
        _review_store[run_id] = {
            "status": ReviewStatus.completed,
            "document_id": doc_id,
            "issues": issues_serialized,
            "started_at": datetime.now().isoformat(),
            "finished_at": datetime.now().isoformat(),
        }

    return BaseResponse(
        data=ReviewCreateResponse(
            review_run_id=run_id,
            project_id=project_id,
            status=ReviewStatus.completed,
            created_at=datetime.now(),
        )
    )


@router.get(
    "/reviews/{review_run_id}/status",
    response_model=BaseResponse[ReviewStatusResponse],
    summary="검토 상태 조회",
)
async def get_review_status(review_run_id: int) -> BaseResponse[ReviewStatusResponse]:
    store = _review_store.get(review_run_id)
    return BaseResponse(
        data=ReviewStatusResponse(
            review_run_id=review_run_id,
            status=store["status"] if store else ReviewStatus.pending,
            progress=100 if store else 0,
            current_step="완료" if store else "대기",
            started_at=datetime.fromisoformat(store["started_at"]) if store else None,
            finished_at=datetime.fromisoformat(store["finished_at"]) if store else None,
        )
    )


@router.get(
    "/reviews/{review_run_id}/summary",
    response_model=BaseResponse[ReviewSummaryResponse],
    summary="검토 요약",
)
async def get_review_summary(review_run_id: int) -> BaseResponse[ReviewSummaryResponse]:
    store = _review_store.get(review_run_id)
    issues = store["issues"] if store else []

    counts = {"high": 0, "critical": 0, "warning": 0, "info": 0}
    for iss in issues:
        sev = iss.get("severity", "info")
        counts[sev] = counts.get(sev, 0) + 1

    high_cnt = counts["high"] + counts["critical"]
    warn_cnt = counts["warning"]
    info_cnt = counts["info"]
    total = len(issues)

    if high_cnt > 0:
        overall = ReviewResult.fail
        risk = min(0.9, 0.5 + high_cnt * 0.1)
    elif warn_cnt > 0:
        overall = ReviewResult.conditional_pass
        risk = min(0.49, 0.2 + warn_cnt * 0.05)
    else:
        overall = ReviewResult.pass_
        risk = 0.05

    return BaseResponse(
        data=ReviewSummaryResponse(
            review_run_id=review_run_id,
            overall_result=overall,
            risk_score=round(risk, 2),
            issue_count=total,
            high_issue_count=high_cnt,
            warning_issue_count=warn_cnt,
            info_issue_count=info_cnt,
            summary_text=(
                f"총 {total}건의 검토 항목이 발견되었습니다. "
                f"위반 {high_cnt}건, 경고 {warn_cnt}건, 참고 {info_cnt}건."
            ),
        )
    )


@router.get(
    "/reviews/{review_run_id}/issues",
    response_model=BaseResponse[ReviewIssueListResponse],
    summary="검토 이슈 목록",
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
    store = _review_store.get(review_run_id)
    all_issues = store["issues"] if store else []

    # 필터
    filtered = [
        iss for iss in all_issues
        if (severity is None or iss["severity"] == severity.value)
        and (category is None or iss["category"] == category.value)
        and (document_id is None or iss["document_id"] == document_id)
    ]

    total = len(filtered)
    start = (page - 1) * size
    paged = filtered[start: start + size]

    items = [
        ReviewIssueListItemResponse(
            id=iss["id"],
            document_id=iss["document_id"],
            severity=iss["severity"],
            category=iss["category"],
            title=iss["title"],
            description=iss["description"],
            recommendation=iss["recommendation"],
            status=iss["status"],
            created_at=datetime.fromisoformat(iss["created_at"]),
        )
        for iss in paged
    ]

    return BaseResponse(
        data=ReviewIssueListResponse(
            items=items,
            meta=PaginationMeta(
                page=page, size=size, total=total,
                total_pages=max(1, (total + size - 1) // size),
            ),
        )
    )


@router.get(
    "/reviews/{review_run_id}/issues/{issue_id}",
    response_model=BaseResponse[ReviewIssueDetailResponse],
    summary="검토 이슈 상세",
)
async def get_review_issue_detail(
    review_run_id: int,
    issue_id: int,
) -> BaseResponse[ReviewIssueDetailResponse]:
    store = _review_store.get(review_run_id)
    if not store:
        raise HTTPException(status_code=404, detail="검토 결과를 찾을 수 없습니다.")

    iss = next((i for i in store["issues"] if i["id"] == issue_id), None)
    if not iss:
        raise HTTPException(status_code=404, detail="이슈를 찾을 수 없습니다.")

    regulation_refs = [
        RegulationReference(
            regulation_title=ref["regulation_title"],
            article_no=ref["article_no"],
            quoted_text=ref["quoted_text"],
        )
        for ref in iss.get("regulation_refs", [])
    ]

    evidences = [
        IssueEvidenceResponse(
            id=j,
            document_id=iss["document_id"],
            page_no=ev.get("page_no"),
            block_id=ev.get("block_id"),
            quoted_text=ev.get("quoted_text"),
            bbox=BBox(**dict(zip(["x1","y1","x2","y2"], ev["bbox"])))
                 if ev.get("bbox") and len(ev.get("bbox", [])) == 4 else None,
        )
        for j, ev in enumerate(iss.get("evidences", []), start=1)
    ]

    return BaseResponse(
        data=ReviewIssueDetailResponse(
            id=iss["id"],
            review_run_id=review_run_id,
            document_id=iss["document_id"],
            severity=iss["severity"],
            category=iss["category"],
            title=iss["title"],
            description=iss["description"],
            recommendation=iss["recommendation"],
            regulation_refs=regulation_refs,
            evidences=evidences,
            status=iss["status"],
            created_at=datetime.fromisoformat(iss["created_at"]),
        )
    )


@router.get(
    "/reviews/{review_run_id}/approval-line",
    response_model=BaseResponse[ApprovalLineResponse],
    summary="결재선 안내",
)
async def get_approval_line(review_run_id: int) -> BaseResponse[ApprovalLineResponse]:
    store = _review_store.get(review_run_id)
    issues = store["issues"] if store else []

    # R030 (고액 결재선) 이슈 여부로 결재선 결정
    has_high_amount = any(i["rule_id"] == "R030" for i in issues)

    if has_high_amount:
        steps = ["담당", "팀장", "과장", "국장", "구청장"]
        rule_name = "1억원 이상 용역 계약 결재선"
    else:
        steps = ["담당", "팀장", "과장"]
        rule_name = "일반 용역 계약 결재선"

    return BaseResponse(
        data=ApprovalLineResponse(
            review_run_id=review_run_id,
            required=True,
            rule_id=3001,
            rule_name=rule_name,
            steps=steps,
            reference_text="서초구 사무전결규정",
        )
    )


@router.get(
    "/reviews/{review_run_id}/documents",
    response_model=BaseResponse[ReviewRunDocumentsResponse],
    summary="검토 대상 문서 목록",
)
async def get_review_documents(review_run_id: int) -> BaseResponse[ReviewRunDocumentsResponse]:
    store = _review_store.get(review_run_id)
    doc_id = store["document_id"] if store else 1001

    return BaseResponse(
        data=ReviewRunDocumentsResponse(
            review_run_id=review_run_id,
            items=[
                ReviewRunDocumentResponse(
                    document_id=doc_id,
                    original_filename="입찰공고문.pdf",
                    role_in_review="bid_notice",
                    doc_type_confirmed=DocumentType.bid_document,
                    parse_status=ParseStatus.done,
                )
            ],
        )
    )


# ──────────────────────────────────────────────
# 샘플 문서 (OCR 없을 때 데모용)
# ──────────────────────────────────────────────

def _make_sample_document(document_id: int) -> ParsedDocument:
    """
    실제 입찰공고문 내용 기반 샘플.
    정상 문서 → 거의 이슈 없음.
    비정상 문서 시뮬레이션은 아래 _make_abnormal_sample() 참고.
    """
    from app.services.review.engine import ParsedBlock, ParsedDocument

    blocks = [
        ParsedBlock(1, 1, "서초구 공고 제2026-24호", [50, 30, 300, 55]),
        ParsedBlock(2, 1, "용역 입찰 공고(긴급)", [100, 60, 400, 95]),
        ParsedBlock(3, 1, "AI 계약서류 검토시스템 용역", [100, 100, 420, 130]),
        ParsedBlock(4, 1, "1. 용역명 : AI 계약서류 검토시스템 구축 용역", [50, 160, 500, 185]),
        ParsedBlock(5, 1, "용역기간 : 착수일로부터 180일", [50, 190, 400, 215]),
        ParsedBlock(6, 1, "기초금액 : 금1,550,000,000원(일억오천오백만원, 부가가치세 별도)", [50, 220, 550, 245]),
        ParsedBlock(7, 1, "발주기관 : 서초구청 스마트도시과", [50, 250, 400, 275]),
        ParsedBlock(8, 1, "담당 : 박우현 ☎02-2155-6431", [50, 280, 350, 305]),
        ParsedBlock(9, 1, "입찰 마감 : 2026. 3. 27.(금) 16:00", [50, 310, 400, 335]),
        ParsedBlock(10, 2, "본 용역은 단독이행만 가능합니다.(공동도급 허용하지 않음)", [50, 50, 500, 75]),
        ParsedBlock(11, 2, "입찰보증금은 면제되되, 입찰보증금 지급각서로 갈음함.", [50, 80, 500, 105]),
        ParsedBlock(12, 2, "낙찰하한율: 사업금액의 100분의 80 미만일 경우 30% 감점", [50, 110, 520, 135]),
        ParsedBlock(13, 2, "지방자치단체를 당사자로 하는 계약에 관한 법률 시행령 제13조", [50, 140, 530, 165]),
    ]
    return ParsedDocument(document_id=document_id, blocks=blocks)


def _make_abnormal_sample(document_id: int) -> ParsedDocument:
    """
    비정상 문서 샘플 — 여러 룰 위반 포함.
    테스트 또는 데모 Before/After 용.
    """
    from app.services.review.engine import ParsedBlock, ParsedDocument

    blocks = [
        ParsedBlock(1, 1, "서초구 공고", [50, 30, 200, 55]),
        # 사업명 없음 (R001 트리거)
        # 용역기간 없음 (R002 트리거)
        ParsedBlock(2, 1, "총사업비 : 15억5000만원", [50, 80, 350, 105]),  # 단위 혼용 (R020 트리거)
        # 발주기관 없음 (R004 트리거)
        # 담당자 없음 (R005 트리거)
        # 마감일 없음 (R006 트리거)
        # 단독이행/공동도급 없음 (R010 트리거)
        # 입찰보증금 없음 (R011 트리거)
        ParsedBlock(3, 1, "계약보증금 5/100", [50, 110, 300, 135]),  # 5% < 10% (R012 트리거)
        # 낙찰하한 없음 (R013 트리거)
        # 부가세 없음 (R014 트리거)
        ParsedBlock(4, 1, "제출기한 : 2026-03-27 16:00", [50, 140, 400, 165]),  # 날짜 형식 (R021)
    ]
    return ParsedDocument(document_id=document_id, blocks=blocks)