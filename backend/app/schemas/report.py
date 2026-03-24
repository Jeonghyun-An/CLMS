from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import Field

from app.schemas.common import BaseSchema, BBox


class ReportFileResponse(BaseSchema):
    report_id: int
    review_run_id: int
    report_type: str = Field(..., example="pdf")
    file_path: str
    download_url: str
    created_at: datetime


class GeneratedChecklistItemResponse(BaseSchema):
    item_code: str
    title: str
    description: Optional[str] = None
    required_flag: bool = True
    result: str = Field(..., example="pass")
    comment: Optional[str] = None
    related_issue_id: Optional[int] = None


class GeneratedChecklistResponse(BaseSchema):
    review_run_id: int
    items: list[GeneratedChecklistItemResponse]


class HighlightItemResponse(BaseSchema):
    issue_id: int
    page_no: int
    bbox: BBox
    color: str = Field(..., example="red")
    label: str = Field(..., example="금액 불일치")


class HighlightResponse(BaseSchema):
    review_run_id: int
    document_id: int
    items: list[HighlightItemResponse]


class HighlightFileResponse(BaseSchema):
    review_run_id: int
    document_id: int
    rendered_file_path: str
    download_url: str