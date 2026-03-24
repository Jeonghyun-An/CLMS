from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.common import BaseSchema, BBox, PaginationMeta
from app.schemas.enums import (
    DocumentType,
    IssueCategory,
    ParseStatus,
    ReviewResult,
    ReviewStatus,
    SeverityLevel,
)


class ReviewRunOptions(BaseSchema):
    run_entity_extraction: bool = True
    run_consistency_check: bool = True
    run_approval_line_check: bool = True
    generate_highlight: bool = True
    generate_report_pdf: bool = True
    generate_checklist: bool = True


class ReviewCreateRequest(BaseSchema):
    document_ids: list[int] = Field(..., min_length=1, description="검토 대상 문서 ID 목록")
    checklist_template_id: Optional[int] = None
    regulation_set_ids: list[int] = []
    options: ReviewRunOptions = ReviewRunOptions()


class ReviewCreateResponse(BaseSchema):
    review_run_id: int
    project_id: int
    status: ReviewStatus
    created_at: datetime


class ReviewStatusResponse(BaseSchema):
    review_run_id: int
    status: ReviewStatus
    progress: int = Field(..., ge=0, le=100)
    current_step: Optional[str] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None


class ReviewSummaryResponse(BaseSchema):
    review_run_id: int
    overall_result: ReviewResult
    risk_score: float
    issue_count: int
    high_issue_count: int = 0
    warning_issue_count: int = 0
    info_issue_count: int = 0
    summary_text: str


class RegulationReference(BaseSchema):
    regulation_id: Optional[int] = None
    regulation_title: Optional[str] = None
    article_id: Optional[int] = None
    article_no: Optional[str] = None
    article_title: Optional[str] = None
    quoted_text: Optional[str] = None


class IssueEvidenceResponse(BaseSchema):
    id: int
    document_id: int
    page_no: Optional[int] = None
    block_id: Optional[int] = None
    cell_id: Optional[int] = None
    quoted_text: Optional[str] = None
    bbox: Optional[BBox] = None


class ReviewIssueListItemResponse(BaseSchema):
    id: int
    document_id: Optional[int] = None
    severity: SeverityLevel
    category: IssueCategory
    title: str
    description: str
    recommendation: Optional[str] = None
    status: str
    created_at: datetime


class ReviewIssueListResponse(BaseSchema):
    items: list[ReviewIssueListItemResponse]
    meta: PaginationMeta


class ReviewIssueDetailResponse(BaseSchema):
    id: int
    review_run_id: int
    document_id: Optional[int] = None
    severity: SeverityLevel
    category: IssueCategory
    title: str
    description: str
    recommendation: Optional[str] = None
    regulation_refs: list[RegulationReference] = []
    evidences: list[IssueEvidenceResponse] = []
    status: str
    created_at: datetime


class ApprovalLineResponse(BaseSchema):
    review_run_id: int
    required: bool
    rule_id: Optional[int] = None
    rule_name: Optional[str] = None
    steps: list[str] = []
    reference_text: Optional[str] = None


class ReviewRunDocumentResponse(BaseSchema):
    document_id: int
    original_filename: str
    role_in_review: Optional[str] = None
    doc_type_confirmed: Optional[DocumentType] = None
    parse_status: ParseStatus


class ReviewRunDocumentsResponse(BaseSchema):
    review_run_id: int
    items: list[ReviewRunDocumentResponse]