"""
MinIO 파일 저장 서비스
────────────────────────────────────────────────────────────
PDF 원본, OCR 캐시 JSON을 MinIO contract-bucket에 저장/조회

버킷 구조:
  contract-bucket/
    pdfs/         {파일명}           ← 업로드된 PDF 원본
    ocr/          ocr_{stem}.json   ← OCR 캐시
"""

from __future__ import annotations

import io
import json
import os

from minio import Minio
from minio.error import S3Error

MINIO_ENDPOINT   = os.getenv("MINIO_ENDPOINT",   "minio:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY",  "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY",  "minioadmin")
MINIO_SECURE     = os.getenv("MINIO_SECURE",      "false").lower() == "true"
MINIO_BUCKET     = os.getenv("MINIO_BUCKET",      "contract-bucket")


def _get_client() -> Minio:
    return Minio(
        MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=MINIO_SECURE,
    )


# ──────────────────────────────────────────────
# PDF 저장 / 조회
# ──────────────────────────────────────────────

def upload_pdf(pdf_bytes: bytes, filename: str) -> str | None:
    """
    PDF 파일을 MinIO에 저장.
    반환: object_name (pdfs/{filename}) 또는 None (실패)
    """
    try:
        client      = _get_client()
        object_name = f"pdfs/{filename}"
        client.put_object(
            MINIO_BUCKET,
            object_name,
            data=io.BytesIO(pdf_bytes),
            length=len(pdf_bytes),
            content_type="application/pdf",
        )
        print(f"[MinIO] PDF 저장: {object_name}")
        return object_name
    except S3Error as e:
        print(f"[MinIO] PDF 저장 실패: {e}")
        return None


# ──────────────────────────────────────────────
# OCR 캐시 저장 / 조회
# ──────────────────────────────────────────────

def save_ocr_cache(stem: str, ocr_result: dict) -> bool:
    """
    OCR 결과 JSON을 MinIO에 저장.
    캐시 키: ocr/{stem}.json
    """
    try:
        client      = _get_client()
        object_name = f"ocr/ocr_{stem}.json"
        data        = json.dumps(ocr_result, ensure_ascii=False, indent=2).encode("utf-8")
        client.put_object(
            MINIO_BUCKET,
            object_name,
            data=io.BytesIO(data),
            length=len(data),
            content_type="application/json",
        )
        print(f"[MinIO] OCR 캐시 저장: {object_name}")
        return True
    except S3Error as e:
        print(f"[MinIO] OCR 캐시 저장 실패: {e}")
        return False


def load_ocr_cache(stem: str) -> dict | None:
    """
    MinIO에서 OCR 캐시 로드.
    반환: OCR 결과 dict 또는 None (없거나 실패)
    """
    try:
        client      = _get_client()
        object_name = f"ocr/ocr_{stem}.json"
        response    = client.get_object(MINIO_BUCKET, object_name)
        data        = response.read()
        response.close()
        response.release_conn()
        print(f"[MinIO] OCR 캐시 히트: {object_name}")
        return json.loads(data.decode("utf-8"))
    except S3Error as e:
        if e.code == "NoSuchKey":
            return None   # 캐시 없음 — 정상
        print(f"[MinIO] OCR 캐시 로드 실패: {e}")
        return None
    except Exception as e:
        print(f"[MinIO] OCR 캐시 로드 오류: {e}")
        return None


def ocr_cache_exists(stem: str) -> bool:
    """OCR 캐시 존재 여부 확인"""
    try:
        client = _get_client()
        client.stat_object(MINIO_BUCKET, f"ocr/ocr_{stem}.json")
        return True
    except S3Error:
        return False