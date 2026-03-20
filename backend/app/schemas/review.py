from __future__ import annotations
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class DocumentCategory(str, Enum):
    contract = "contract"           # 계약서
    specification = "specification" # 시방서/설계내역서
    cost = "cost"                   # 산출내역서/예산서
    guideline = "guideline"         # 가이드라인/내부지침
    law = "law"                     # 법령
    approval = "approval"           # 결재/전결규정
    other = "other"                 # 미분류


class ReviewStatus(str, Enum):
    pending = "pending"
    processing = "processing"
    done = "done"
    error = "error"


class IssueSeverity(str, Enum):
    error = "error"
    warning = "warning"
    info = "info"


class IssueType(str, Enum):
    numeric_violation = "numeric_violation"   # 수치 위반 (deterministic)
    missing_clause = "missing_clause"         # 조항 누락
    compliance_risk = "compliance_risk"       # 법적 리스크 (LLM)
    format_error = "format_error"             # 양식 오류


# ─── 문서 업로드 ─────────────────────────────────────────────────────────────

class DocumentUploadItem(BaseModel):
    id: str
    name: str
    category: DocumentCategory
    size: int


class DocumentUploadResponse(BaseModel):
    doc_id: str
    name: str
    category: DocumentCategory
    auto_category: DocumentCategory
    file_key: str
    size: int
    status: ReviewStatus = ReviewStatus.pending


# ─── 검토 결과 ───────────────────────────────────────────────────────────────

class LegalCitation(BaseModel):
    article_id: str
    source: str
    article: str
    title: str
    relevant_excerpt: str


class ReviewIssue(BaseModel):
    issue_id: str
    rule_id: str
    issue_type: IssueType
    severity: IssueSeverity
    title: str
    description: str
    location: Optional[str] = None
    detected_value: Optional[str] = None
    expected_value: Optional[str] = None
    citations: list[LegalCitation] = Field(default_factory=list)
    rag_confidence: float = 0.0
    retrieval_source: str = ""    # "deterministic" | "vector" | "graph" | "mock_llm"


class DocumentReviewResult(BaseModel):
    doc_id: str
    doc_name: str
    category: DocumentCategory
    status: ReviewStatus
    issues: list[ReviewIssue] = Field(default_factory=list)
    summary: str = ""
    error_count: int = 0
    warning_count: int = 0
    info_count: int = 0


class ReviewJobResponse(BaseModel):
    job_id: str
    status: ReviewStatus
    document_results: list[DocumentReviewResult] = Field(default_factory=list)
    total_errors: int = 0
    total_warnings: int = 0
    created_at: str
    completed_at: Optional[str] = None


# ─── SSE 이벤트 ──────────────────────────────────────────────────────────────

class SSEEventType(str, Enum):
    started = "started"
    step = "step"
    issue_found = "issue_found"
    doc_done = "doc_done"
    job_done = "job_done"
    error = "error"


class SSEEvent(BaseModel):
    event: SSEEventType
    job_id: str
    doc_id: Optional[str] = None
    doc_name: Optional[str] = None
    message: str = ""
    step: Optional[str] = None
    progress: float = 0.0
    issue: Optional[ReviewIssue] = None
    result: Optional[DocumentReviewResult] = None


# ─── 검토 시작 요청 ──────────────────────────────────────────────────────────

class ReviewStartRequest(BaseModel):
    documents: list[DocumentUploadItem]
