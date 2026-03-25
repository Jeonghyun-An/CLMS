from __future__ import annotations

import threading
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

# 문서 메타 저장소 (upload 시 저장)
_document_store: dict[int, dict] = {}
_store_lock = threading.Lock()


def register_document(doc_id: int, meta: dict):
    """upload_review에서 호출 — 문서 메타 등록"""
    with _store_lock:
        _document_store[doc_id] = meta


def _get_file_format(filename: str) -> FileFormat:
    ext = filename.lower().rsplit(".", 1)[-1]
    return {
        "pdf":  FileFormat.pdf,
        "hwpx": FileFormat.hwpx,
        "hwp":  FileFormat.hwp,
        "xlsx": FileFormat.xlsx,
        "docx": FileFormat.docx,
    }.get(ext, FileFormat.pdf)


def _get_doc_type(doc_type_str: str) -> DocumentType:
    return {
        "bid_notice":       DocumentType.bid_document,
        "proposal_request": DocumentType.proposal,
        "plan":             DocumentType.plan,
    }.get(doc_type_str, DocumentType.unknown)


# ──────────────────────────────────────────────
# 문서 업로드 (메타 등록용 — 실제 파일 처리는 upload_review)
# ──────────────────────────────────────────────

@router.post(
    "/projects/{project_id}/documents",
    response_model=BaseResponse[DocumentUploadResponse],
    status_code=status.HTTP_201_CREATED,
    summary="문서 업로드 (메타 등록)",
)
async def upload_documents(
    project_id: int,
    files: list[UploadFile] = File(...),
    document_group_name: str | None = Form(None),
) -> BaseResponse[DocumentUploadResponse]:
    items = []
    for idx, file in enumerate(files, start=1):
        items.append(DocumentUploadItemResponse(
            id=idx,
            project_id=project_id,
            original_filename=file.filename,
            file_format=_get_file_format(file.filename),
            mime_type=file.content_type or "application/octet-stream",
            file_size=0,
            doc_type_predicted=DocumentType.unknown,
            doc_type_confirmed=None,
            parse_status=ParseStatus.pending,
            uploaded_at=datetime.now(),
        ))
    return BaseResponse(data=DocumentUploadResponse(items=items))


# ──────────────────────────────────────────────
# 문서 목록 — review_store files 기반
# ──────────────────────────────────────────────

@router.get(
    "/projects/{project_id}/documents",
    response_model=BaseResponse[DocumentListResponse],
    summary="프로젝트 문서 목록",
)
async def list_project_documents(
    project_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    parse_status: ParseStatus | None = Query(None),
    doc_type: DocumentType | None = Query(None),
    keyword: str | None = Query(None),
    review_run_id: int | None = Query(None, description="검토 실행 ID로 필터"),
) -> BaseResponse[DocumentListResponse]:
    items = []

    # review_run_id 있으면 해당 검토의 파일 목록
    if review_run_id:
        from app.api.reviews import _get_review
        review = _get_review(review_run_id)
        if review:
            for f in review.get("files", []):
                items.append(DocumentListItemResponse(
                    id=f["document_id"],
                    original_filename=f["filename"],
                    file_format=_get_file_format(f["filename"]),
                    file_size=0,
                    doc_type_predicted=_get_doc_type(f.get("doc_type", "")),
                    doc_type_confirmed=_get_doc_type(f.get("doc_type", "")),
                    parse_status=ParseStatus.done,
                    uploaded_by=1,
                    uploaded_at=datetime.now(),
                ))
    else:
        # _document_store에서 가져오기
        for doc_id, meta in _document_store.items():
            items.append(DocumentListItemResponse(
                id=doc_id,
                original_filename=meta.get("filename", ""),
                file_format=_get_file_format(meta.get("filename", "")),
                file_size=meta.get("file_size", 0),
                doc_type_predicted=_get_doc_type(meta.get("doc_type", "")),
                doc_type_confirmed=_get_doc_type(meta.get("doc_type", "")),
                parse_status=ParseStatus.done,
                uploaded_by=1,
                uploaded_at=datetime.fromisoformat(meta.get("uploaded_at", datetime.now().isoformat())),
            ))

    total = len(items)
    start = (page - 1) * size
    paged = items[start:start + size]

    return BaseResponse(data=DocumentListResponse(
        items=paged,
        meta=PaginationMeta(page=page, size=size, total=total,
                            total_pages=max(1, (total + size - 1) // size)),
    ))


# ──────────────────────────────────────────────
# 문서 상세
# ──────────────────────────────────────────────

@router.get(
    "/projects/{project_id}/documents/{document_id}",
    response_model=BaseResponse[DocumentDetailResponse],
    summary="문서 상세",
)
async def get_document(project_id: int, document_id: int) -> BaseResponse[DocumentDetailResponse]:
    meta = _document_store.get(document_id)

    if not meta:
        # review_store에서 찾기
        try:
            from app.services.storage.redis_store import get_client
            import json
            keys = get_client().keys("clms:review:*")
            for k in keys:
                if ":" not in k[len("clms:review:"):]:
                    raw = get_client().get(k)
                    if raw:
                        review = json.loads(raw)
                        for f in review.get("files", []):
                            if f.get("document_id") == document_id:
                                meta = f
                                break
                if meta:
                    break
        except Exception:
            pass

    if not meta:
        raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다.")

    filename = meta.get("filename", "")
    return BaseResponse(data=DocumentDetailResponse(
        id=document_id,
        project_id=project_id,
        original_filename=filename,
        stored_path=f"/data/clms_seocho/{filename}",
        file_format=_get_file_format(filename),
        mime_type="application/pdf",
        file_size=meta.get("file_size", 0),
        doc_type_predicted=_get_doc_type(meta.get("doc_type", "")),
        doc_type_confirmed=_get_doc_type(meta.get("doc_type", "")),
        parse_status=ParseStatus.done,
        page_count=meta.get("page_count", 0),
        entity_count=0,
        table_count=0,
        uploaded_by=1,
        uploaded_at=datetime.now(),
    ))


@router.patch(
    "/projects/{project_id}/documents/{document_id}/doc-type",
    response_model=BaseResponse[DocumentTypeUpdateResponse],
    summary="문서 유형 수정",
)
async def update_document_type(
    project_id: int,
    document_id: int,
    body: DocumentTypeUpdateRequest,
) -> BaseResponse[DocumentTypeUpdateResponse]:
    if document_id in _document_store:
        _document_store[document_id]["doc_type"] = body.doc_type_confirmed
    return BaseResponse(data=DocumentTypeUpdateResponse(
        id=document_id,
        doc_type_predicted=DocumentType.unknown,
        doc_type_confirmed=body.doc_type_confirmed,
        updated_at=datetime.now(),
    ))