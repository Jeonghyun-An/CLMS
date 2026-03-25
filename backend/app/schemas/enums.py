from enum import Enum


class ProjectStatus(str, Enum):
    draft = "draft"
    in_review = "in_review"
    completed = "completed"
    archived = "archived"


class ParseStatus(str, Enum):
    pending = "pending"
    processing = "processing"
    done = "done"
    failed = "failed"


class ReviewStatus(str, Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


class ReviewResult(str, Enum):
    pass_ = "pass"
    conditional_pass = "conditional_pass"
    fail = "fail"


class SeverityLevel(str, Enum):
    info = "info"
    warning = "warning"
    high = "high"
    critical = "critical"


class IssueCategory(str, Enum):
    missing = "missing"
    inconsistency = "inconsistency"
    regulation_violation = "regulation_violation"
    approval_rule = "approval_rule"
    checklist_fail = "checklist_fail"
    table_validation = "table_validation"
    typo = "typo"


class RegulationType(str, Enum):
    law = "law"
    guideline = "guideline"
    internal_rule = "internal_rule"


class FeedbackType(str, Enum):
    correct = "correct"
    incorrect = "incorrect"
    partial = "partial"


class FileFormat(str, Enum):
    pdf = "pdf"
    hwp = "hwp"
    hwpx = "hwpx"
    xlsx = "xlsx"
    docx = "docx"
    image = "image"


class DocumentType(str, Enum):
    plan = "plan"
    official_notice = "official_notice"
    proposal_request = "proposal_request"
    bid_document = "bid_document"
    estimate_sheet = "estimate_sheet"
    design_sheet = "design_sheet"
    contract_draft = "contract_draft"
    attachment = "attachment"
    unknown = "unknown"