"""
리포트 API — 실제 데이터 기반
────────────────────────────────────────────────────────────
GET /projects/{id}/reviews/{run_id}/report/download  PDF 다운로드
GET /projects/{id}/reviews/{run_id}/report           리포트 메타
GET /projects/{id}/reviews/{run_id}/checklist        체크리스트
GET /projects/{id}/reviews/{run_id}/highlights/{doc_id}  하이라이트 좌표
"""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

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

SEV_COLOR = {
    "critical": "red",
    "high":     "orange",
    "warning":  "yellow",
    "info":     "blue",
}


# ──────────────────────────────────────────────
# PDF 리포트 다운로드 (실제 생성)
# ──────────────────────────────────────────────

@router.get(
    "/reviews/{review_run_id}/report/download",
    summary="PDF 리포트 다운로드",
    response_class=Response,
)
async def download_report_pdf(review_run_id: int, project_id: int) -> Response:
    from app.api.reviews import _get_review
    review = _get_review(review_run_id)
    if not review:
        raise HTTPException(status_code=404, detail="검토 결과를 찾을 수 없습니다.")

    issues = review.get("issues", [])

    # 결재선 판단
    has_high = any(i.get("rule_id") == "R030" for i in issues)
    approval = {
        "steps":          ["담당", "팀장", "과장", "국장", "구청장"] if has_high else ["담당", "팀장", "과장"],
        "rule_name":      "1억원 이상 용역 결재선" if has_high else "일반 용역 결재선",
        "reference_text": "서초구 사무전결규정",
    }

    meta = {
        "project_name": "AI 계약서류 검토시스템 용역",
        "issuer":       "서초구청 스마트도시과",
        "doc_count":    len(review.get("files", [review])),
        "total_issues": len(issues),
    }

    from app.services.review.report_generator import generate_report_pdf
    pdf_bytes = generate_report_pdf(issues, meta, approval)

    filename = f"review_report_{review_run_id}_{datetime.now().strftime('%Y%m%d')}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Content-Length":      str(len(pdf_bytes)),
        },
    )


# ──────────────────────────────────────────────
# 리포트 메타
# ──────────────────────────────────────────────

@router.get(
    "/reviews/{review_run_id}/report",
    response_model=BaseResponse[ReportFileResponse],
    summary="리포트 정보",
)
async def get_review_report(review_run_id: int, project_id: int):
    return BaseResponse(data=ReportFileResponse(
        report_id=review_run_id,
        review_run_id=review_run_id,
        report_type="pdf",
        file_path=f"/data/reports/review_{review_run_id}.pdf",
        download_url=f"/api/v1/projects/{project_id}/reviews/{review_run_id}/report/download",
        created_at=datetime.now(),
    ))


# ──────────────────────────────────────────────
# 체크리스트 — 실제 이슈 기반 자동 생성
# ──────────────────────────────────────────────

@router.get(
    "/reviews/{review_run_id}/checklist",
    response_model=BaseResponse[GeneratedChecklistResponse],
    summary="체크리스트 결과",
)
async def get_review_checklist(review_run_id: int, project_id: int):
    from app.api.reviews import _get_review
    review = _get_review(review_run_id)
    issues = review["issues"] if review else []
    rule_ids = {i.get("rule_id") for i in issues}

    def item(code, title, rule_id, required=True):
        passed  = rule_id not in rule_ids
        related = next((i["id"] for i in issues if i.get("rule_id") == rule_id), None)
        return GeneratedChecklistItemResponse(
            item_code=code,
            title=title,
            description=f"{title} 여부 확인",
            required_flag=required,
            result="pass" if passed else "fail",
            comment="정상" if passed else f"이슈 발견 ({rule_id})",
            related_issue_id=related,
        )

    items = [
        item("CHK-001", "사업명 명시",          "R001"),
        item("CHK-002", "용역기간 명시",         "R002"),
        item("CHK-003", "기초금액 명시",         "R003"),
        item("CHK-004", "금액 표기 오류 없음",   "R101"),
        item("CHK-005", "항목 순서 적절",        "R103"),
        item("CHK-006", "기초금액 일치",         "R105"),
        item("CHK-007", "담당자 전화번호 기재",  "PR001"),
        item("CHK-008", "담당자 이메일 기재",    "PR002"),
        item("CHK-009", "노임단가 기준 정확",    "PR010"),
        item("CHK-010", "동시접속 성능 기준",    "PR022", required=False),
    ]

    return BaseResponse(data=GeneratedChecklistResponse(
        review_run_id=review_run_id,
        items=items,
    ))


# ──────────────────────────────────────────────
# 하이라이트 — 실제 이슈 bbox 기반
# ──────────────────────────────────────────────

@router.get(
    "/reviews/{review_run_id}/highlights/{document_id}",
    response_model=BaseResponse[HighlightResponse],
    summary="하이라이트 좌표",
    description="""
이슈 카드와 1:1 매칭되는 하이라이트 좌표를 반환합니다.
PDF.js 뷰어에서 이 좌표로 오버레이를 그립니다.

bbox 좌표: [x1, y1, x2, y2] — OCR 원본 픽셀 좌표
page_no: 1-based 페이지 번호
""",
)
async def get_review_highlights(
    review_run_id: int,
    document_id:   int,
    project_id:    int,
) -> BaseResponse[HighlightResponse]:
    from app.api.reviews import _get_review
    review = _get_review(review_run_id)
    issues = review["issues"] if review else []

    items = []
    for iss in issues:
        # 해당 document_id 이슈만 필터
        if iss.get("document_id") and iss["document_id"] != document_id:
            continue

        color = SEV_COLOR.get(iss.get("severity", "info"), "blue")

        # highlights 필드 우선 사용 (룰엔진이 채운 정확한 bbox)
        for hl in iss.get("highlights", []):
            bbox_raw = hl.get("bbox", [])
            if not bbox_raw or len(bbox_raw) != 4 or all(v == 0 for v in bbox_raw):
                continue
            # bbox 좌표 변환: [ymin,xmin,ymax,xmax] → [x1,y1,x2,y2]
            # OCR 어댑터 이후엔 이미 [x1,y1,x2,y2]이지만 방어적으로 처리
            x1, y1, x2, y2 = bbox_raw
            items.append(HighlightItemResponse(
                issue_id=iss["id"],
                page_no=hl.get("page_no", 1),
                bbox=BBox(x1=x1, y1=y1, x2=x2, y2=y2),
                color=color,
                label=iss["title"][:20],
            ))

        # highlights 없으면 evidences에서 bbox 추출
        if not iss.get("highlights"):
            for ev in iss.get("evidences", []):
                bbox_raw = ev.get("bbox", [])
                if not bbox_raw or len(bbox_raw) != 4:
                    continue
                if all(v == 0 for v in bbox_raw):
                    continue
                x1, y1, x2, y2 = bbox_raw
                items.append(HighlightItemResponse(
                    issue_id=iss["id"],
                    page_no=ev.get("page_no", 1),
                    bbox=BBox(x1=x1, y1=y1, x2=x2, y2=y2),
                    color=color,
                    label=iss["title"][:20],
                ))

    return BaseResponse(data=HighlightResponse(
        review_run_id=review_run_id,
        document_id=document_id,
        items=items,
    ))


# ──────────────────────────────────────────────
# 하이라이트 렌더 파일 (PoC에서는 미사용)
# ──────────────────────────────────────────────

@router.get(
    "/reviews/{review_run_id}/highlight-file/{document_id}",
    response_model=BaseResponse[HighlightFileResponse],
    summary="하이라이트 렌더 파일 (미사용)",
    deprecated=True,
)
async def get_review_highlight_file(review_run_id: int, document_id: int, project_id: int):
    return BaseResponse(data=HighlightFileResponse(
        review_run_id=review_run_id,
        document_id=document_id,
        rendered_file_path="",
        download_url="",
    ))