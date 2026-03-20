"""
문서 업로드 엔드포인트

POST /api/v1/upload/documents    - 파일 업로드 (멀티파트)
PATCH /api/v1/upload/documents/{id} - 카테고리 변경 저장
"""

import re
from fastapi import APIRouter, UploadFile, File
from pydantic import BaseModel

from app.schemas.review import DocumentUploadResponse, DocumentCategory, ReviewStatus

router = APIRouter()


def _classify_filename(name: str) -> str:
    n = name.lower().replace("-", "").replace("_", "").replace(" ", "")
    rules = [
        ("contract",      ["계약서", "계약", "공사계약", "용역계약", "contract"]),
        ("specification", ["시방서", "설계내역서", "설계서", "도면"]),
        ("cost",          ["산출내역서", "예산서", "원가계산서", "견적서", "노임단가"]),
        ("guideline",     ["가이드라인", "지침", "매뉴얼", "안내"]),
        ("law",           ["법령", "시행령", "조례", "규칙", "지방계약법"]),
        ("approval",      ["전결", "결재", "사무전결"]),
    ]
    best, score = "other", 0
    for cat, keywords in rules:
        s = sum(len(k) for k in keywords if k in n)
        if s > score:
            best, score = cat, s
    return best


@router.post("/documents", response_model=list[DocumentUploadResponse])
async def upload_documents(files: list[UploadFile] = File(...)):
    """
    파일 업로드

    실제 구현:
        content = await file.read()
        minio_client.put_object(settings.MINIO_BUCKET, file_key, content, ...)
        # DB에 메타데이터 저장 (SQLAlchemy)
    """
    results = []
    for f in files:
        auto_cat = _classify_filename(f.filename or "")
        results.append(DocumentUploadResponse(
            doc_id=f"doc_{abs(hash(f.filename)) % 0xFFFFFF:06x}",
            name=f.filename or "",
            category=DocumentCategory(auto_cat),
            auto_category=DocumentCategory(auto_cat),
            file_key=f"uploads/poc/{f.filename}",
            size=f.size or 0,
        ))
    return results


class CategoryUpdateBody(BaseModel):
    category: str


@router.patch("/documents/{doc_id}")
async def update_category(doc_id: str, body: CategoryUpdateBody):
    """
    카테고리 변경 저장

    실제 구현:
        await db.execute(
            "UPDATE documents SET category=:cat WHERE id=:id",
            {"cat": body.category, "id": doc_id}
        )
    """
    return {"doc_id": doc_id, "category": body.category, "updated": True}
