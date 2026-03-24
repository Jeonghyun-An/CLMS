from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import Field

from app.schemas.common import BaseSchema, BBox, PaginationMeta
from app.schemas.enums import DocumentType, FileFormat, ParseStatus


class DocumentUploadItemResponse(BaseSchema):
    id: int
    project_id: int
    original_filename: str
    file_format: FileFormat
    mime_type: str
    file_size: int
    doc_type_predicted: Optional[DocumentType] = None
    doc_type_confirmed: Optional[DocumentType] = None
    parse_status: ParseStatus
    uploaded_at: datetime


class DocumentUploadResponse(BaseSchema):
    items: list[DocumentUploadItemResponse]


class DocumentListItemResponse(BaseSchema):
    id: int
    original_filename: str
    file_format: FileFormat
    file_size: int
    doc_type_predicted: Optional[DocumentType] = None
    doc_type_confirmed: Optional[DocumentType] = None
    parse_status: ParseStatus
    uploaded_by: int
    uploaded_at: datetime


class DocumentListResponse(BaseSchema):
    items: list[DocumentListItemResponse]
    meta: PaginationMeta


class DocumentDetailResponse(BaseSchema):
    id: int
    project_id: int
    original_filename: str
    stored_path: str
    file_format: FileFormat
    mime_type: str
    file_size: int
    doc_type_predicted: Optional[DocumentType] = None
    doc_type_confirmed: Optional[DocumentType] = None
    parse_status: ParseStatus
    page_count: Optional[int] = None
    entity_count: int = 0
    table_count: int = 0
    uploaded_by: int
    uploaded_at: datetime


class DocumentTypeUpdateRequest(BaseSchema):
    doc_type_confirmed: DocumentType = Field(..., example=DocumentType.plan)


class DocumentTypeUpdateResponse(BaseSchema):
    id: int
    doc_type_predicted: Optional[DocumentType] = None
    doc_type_confirmed: DocumentType
    updated_at: datetime


class DocumentBlockResponse(BaseSchema):
    id: int
    block_type: str
    block_order: int
    text: str
    bbox: Optional[BBox] = None
    structure_path: Optional[str] = None


class DocumentPageResponse(BaseSchema):
    id: int
    page_no: int
    width: Optional[float] = None
    height: Optional[float] = None
    image_path: Optional[str] = None
    blocks: list[DocumentBlockResponse] = []


class DocumentStructureResponse(BaseSchema):
    document_id: int
    pages: list[DocumentPageResponse]


class ExtractedEntityResponse(BaseSchema):
    id: int
    entity_type: str
    entity_label: str
    entity_value: str
    normalized_value: Optional[str] = None
    confidence: Optional[float] = None
    source_page_no: Optional[int] = None
    source_block_id: Optional[int] = None
    source_cell_id: Optional[int] = None
    bbox: Optional[BBox] = None


class DocumentEntitiesResponse(BaseSchema):
    document_id: int
    items: list[ExtractedEntityResponse]


class TableCellResponse(BaseSchema):
    id: int
    row_index: int
    col_index: int
    cell_address: Optional[str] = None
    text: Optional[str] = None
    numeric_value: Optional[float] = None
    formula: Optional[str] = None
    rowspan: int = 1
    colspan: int = 1
    bbox: Optional[BBox] = None


class DocumentTableResponse(BaseSchema):
    id: int
    page_id: Optional[int] = None
    table_order: int
    title: Optional[str] = None
    row_count: int
    col_count: int
    cells: list[TableCellResponse] = []


class DocumentTablesResponse(BaseSchema):
    document_id: int
    items: list[DocumentTableResponse]