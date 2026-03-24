from __future__ import annotations

from typing import Optional

from app.schemas.common import BaseSchema
from app.schemas.enums import DocumentType


class ChecklistTemplateListItemResponse(BaseSchema):
    id: int
    name: str
    doc_type: Optional[DocumentType] = None
    version: Optional[str] = None
    is_active: bool


class ChecklistTemplateListResponse(BaseSchema):
    items: list[ChecklistTemplateListItemResponse]


class ChecklistTemplateItemResponse(BaseSchema):
    id: int
    item_code: str
    item_title: str
    description: Optional[str] = None
    required_flag: bool
    related_regulation_id: Optional[int] = None
    related_article_id: Optional[int] = None
    rule_expression: Optional[str] = None


class ChecklistTemplateDetailResponse(BaseSchema):
    id: int
    name: str
    doc_type: Optional[DocumentType] = None
    version: Optional[str] = None
    is_active: bool
    items: list[ChecklistTemplateItemResponse]