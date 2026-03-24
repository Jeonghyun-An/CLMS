from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, File, Form, Query, UploadFile, status

from app.schemas.common import BBox, BaseResponse, DeleteResponse, PaginationMeta
from app.schemas.document import (
    DocumentBlockResponse,
    DocumentDetailResponse,
    DocumentEntitiesResponse,
    DocumentListItemResponse,
    DocumentListResponse,
    DocumentPageResponse,
    DocumentStructureResponse,
    DocumentTableResponse,
    DocumentTablesResponse,
    DocumentTypeUpdateRequest,
    DocumentTypeUpdateResponse,
    DocumentUploadItemResponse,
    DocumentUploadResponse,
    ExtractedEntityResponse,
    TableCellResponse,
)
from app.schemas.enums import DocumentType, FileFormat, ParseStatus

router = APIRouter()


@router.post(
    "/projects/{project_id}/documents",
    response_model=BaseResponse[DocumentUploadResponse],
    status_code=status.HTTP_201_CREATED,
    summary="문서 업로드",
    description="프로젝트에 문서를 업로드합니다. 현재는 Swagger 확인용 mock 응답입니다.",
)
async def upload_documents(
    project_id: int,
    files: list[UploadFile] = File(..., description="업로드할 문서 파일들"),
    document_group_name: str | None = Form(None, description="문서 그룹명"),
) -> BaseResponse[DocumentUploadResponse]:
    items = []
    for idx, file in enumerate(files, start=1):
        filename_lower = file.filename.lower()
        if filename_lower.endswith(".pdf"):
            file_format = FileFormat.pdf
        elif filename_lower.endswith(".hwpx"):
            file_format = FileFormat.hwpx
        elif filename_lower.endswith(".hwp"):
            file_format = FileFormat.hwp
        elif filename_lower.endswith(".xlsx"):
            file_format = FileFormat.xlsx
        else:
            file_format = FileFormat.docx

        items.append(
            DocumentUploadItemResponse(
                id=idx,
                project_id=project_id,
                original_filename=file.filename,
                file_format=file_format,
                mime_type=file.content_type or "application/octet-stream",
                file_size=0,
                doc_type_predicted=DocumentType.unknown,
                doc_type_confirmed=None,
                parse_status=ParseStatus.pending,
                uploaded_at=datetime.now(),
            )
        )

    return BaseResponse(data=DocumentUploadResponse(items=items))


@router.get(
    "/projects/{project_id}/documents",
    response_model=BaseResponse[DocumentListResponse],
    summary="프로젝트 문서 목록 조회",
    description="프로젝트에 속한 문서 목록을 조회합니다.",
)
async def list_project_documents(
    project_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    parse_status: ParseStatus | None = Query(None),
    doc_type: DocumentType | None = Query(None),
    keyword: str | None = Query(None),
) -> BaseResponse[DocumentListResponse]:
    items = [
        DocumentListItemResponse(
            id=1001,
            original_filename="계획서.hwpx",
            file_format=FileFormat.hwpx,
            file_size=102400,
            doc_type_predicted=DocumentType.plan,
            doc_type_confirmed=doc_type or DocumentType.plan,
            parse_status=parse_status or ParseStatus.done,
            uploaded_by=1,
            uploaded_at=datetime.now(),
        )
    ]
    data = DocumentListResponse(
        items=items,
        meta=PaginationMeta(page=page, size=size, total=1, total_pages=1),
    )
    return BaseResponse(data=data)


@router.get(
    "/documents/{document_id}",
    response_model=BaseResponse[DocumentDetailResponse],
    summary="문서 상세 조회",
    description="문서 상세 메타데이터를 조회합니다.",
)
async def get_document(document_id: int) -> BaseResponse[DocumentDetailResponse]:
    data = DocumentDetailResponse(
        id=document_id,
        project_id=1,
        original_filename="계획서.hwpx",
        stored_path="/data/documents/plan_001.hwpx",
        file_format=FileFormat.hwpx,
        mime_type="application/octet-stream",
        file_size=102400,
        doc_type_predicted=DocumentType.plan,
        doc_type_confirmed=DocumentType.plan,
        parse_status=ParseStatus.done,
        page_count=12,
        entity_count=8,
        table_count=2,
        uploaded_by=1,
        uploaded_at=datetime.now(),
    )
    return BaseResponse(data=data)


@router.patch(
    "/documents/{document_id}/doc-type",
    response_model=BaseResponse[DocumentTypeUpdateResponse],
    summary="문서 유형 수정",
    description="자동 분류된 문서 유형을 사용자가 확정/수정합니다.",
)
async def update_document_type(
    document_id: int,
    body: DocumentTypeUpdateRequest,
) -> BaseResponse[DocumentTypeUpdateResponse]:
    data = DocumentTypeUpdateResponse(
        id=document_id,
        doc_type_predicted=DocumentType.unknown,
        doc_type_confirmed=body.doc_type_confirmed,
        updated_at=datetime.now(),
    )
    return BaseResponse(data=data)


@router.get(
    "/documents/{document_id}/structure",
    response_model=BaseResponse[DocumentStructureResponse],
    summary="문서 구조 조회",
    description="페이지/블록 구조를 조회합니다.",
)
async def get_document_structure(document_id: int) -> BaseResponse[DocumentStructureResponse]:
    data = DocumentStructureResponse(
        document_id=document_id,
        pages=[
            DocumentPageResponse(
                id=1,
                page_no=1,
                width=595.0,
                height=842.0,
                image_path="/data/pages/doc_1_page_1.png",
                blocks=[
                    DocumentBlockResponse(
                        id=1,
                        block_type="title",
                        block_order=1,
                        text="용역 계획서",
                        bbox=BBox(x1=100, y1=100, x2=320, y2=145),
                        structure_path="1.title.1",
                    ),
                    DocumentBlockResponse(
                        id=2,
                        block_type="paragraph",
                        block_order=2,
                        text="본 사업의 추진 배경 및 목적은 다음과 같다.",
                        bbox=BBox(x1=100, y1=180, x2=500, y2=240),
                        structure_path="1.paragraph.1",
                    ),
                ],
            )
        ],
    )
    return BaseResponse(data=data)


@router.get(
    "/documents/{document_id}/entities",
    response_model=BaseResponse[DocumentEntitiesResponse],
    summary="문서 엔티티 조회",
    description="문서에서 추출한 핵심 항목을 조회합니다.",
)
async def get_document_entities(document_id: int) -> BaseResponse[DocumentEntitiesResponse]:
    data = DocumentEntitiesResponse(
        document_id=document_id,
        items=[
            ExtractedEntityResponse(
                id=1,
                entity_type="title",
                entity_label="문서명",
                entity_value="용역 계획서",
                normalized_value="용역 계획서",
                confidence=0.99,
                source_page_no=1,
                source_block_id=1,
                bbox=BBox(x1=100, y1=100, x2=320, y2=145),
            ),
            ExtractedEntityResponse(
                id=2,
                entity_type="amount",
                entity_label="총사업비",
                entity_value="120,000,000원",
                normalized_value="120000000",
                confidence=0.95,
                source_page_no=2,
                source_block_id=7,
                bbox=BBox(x1=120, y1=410, x2=300, y2=440),
            ),
        ],
    )
    return BaseResponse(data=data)


@router.get(
    "/documents/{document_id}/tables",
    response_model=BaseResponse[DocumentTablesResponse],
    summary="문서 표 조회",
    description="문서 내 표 구조 및 셀 정보를 조회합니다.",
)
async def get_document_tables(document_id: int) -> BaseResponse[DocumentTablesResponse]:
    data = DocumentTablesResponse(
        document_id=document_id,
        items=[
            DocumentTableResponse(
                id=1,
                page_id=2,
                table_order=1,
                title="산출내역서",
                row_count=2,
                col_count=3,
                cells=[
                    TableCellResponse(
                        id=1,
                        row_index=1,
                        col_index=1,
                        cell_address="A1",
                        text="항목명",
                        rowspan=1,
                        colspan=1,
                    ),
                    TableCellResponse(
                        id=2,
                        row_index=1,
                        col_index=2,
                        cell_address="B1",
                        text="수량",
                        rowspan=1,
                        colspan=1,
                    ),
                    TableCellResponse(
                        id=3,
                        row_index=1,
                        col_index=3,
                        cell_address="C1",
                        text="금액",
                        rowspan=1,
                        colspan=1,
                    ),
                ],
            )
        ],
    )
    return BaseResponse(data=data)


@router.delete(
    "/documents/{document_id}",
    response_model=BaseResponse[DeleteResponse],
    summary="문서 삭제",
    description="문서를 삭제합니다.",
)
async def delete_document(document_id: int) -> BaseResponse[DeleteResponse]:
    return BaseResponse(data=DeleteResponse(deleted=True, id=document_id))