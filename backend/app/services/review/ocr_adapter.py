"""
OCR 어댑터 — 다양한 OCR 출력 포맷을 룰 엔진 입력으로 변환
────────────────────────────────────────────────────────────
지원 포맷:

  [A] OCR 포맷 (pymupdf + vLLM 직접 호출) ← 현재 메인
      {
        "document_id": 1001,
        "pages": [
          { "page_no": 1, "blocks": [
              { "block_id": 1, "text": "...", "bbox": [ymin, xmin, ymax, xmax] }
          ]}
        ]
      }
      ※ bbox 좌표 순서: [ymin, xmin, ymax, xmax] → 엔진용 [x1,y1,x2,y2]로 자동 변환

  [B] content 텍스트 덩어리 포맷 (기존 PaddleOCR 저장 포맷)
      [{"page": 1, "content": "전체텍스트..."}, ...]

  [C] PaddleOCR raw blocks 포맷 (bbox 4점 좌표)
      [{"page": 1, "blocks": [{"bbox": [[x1,y1],...], "text": "...", "confidence": 0.9}]}]

  [D] zerox 출력 포맷 (ZeroxOutput 객체 또는 직렬화 dict)
      ZeroxOutput(pages=[Page(content="마크다운텍스트", page=1), ...])

adapt() 함수 하나로 포맷 자동 감지.
"""

from __future__ import annotations

import re as _re

from app.services.review.engine import ParsedBlock, ParsedDocument


# ──────────────────────────────────────────────
# [A] OCR 포맷 (메인)
# document_id + pages + blocks + bbox [ymin,xmin,ymax,xmax]
# ──────────────────────────────────────────────

def from_junior_format(
    ocr_result: dict,
    document_id: int = 0,
) -> ParsedDocument:
    """
    bbox 좌표 변환: [ymin, xmin, ymax, xmax] → [x1, y1, x2, y2]
    """
    doc_id = ocr_result.get("document_id", document_id) or document_id
    doc = ParsedDocument(document_id=doc_id)
    block_id = 1

    for page in ocr_result.get("pages", []):
        page_no = page.get("page_no", 1)
        for block in page.get("blocks", []):
            text = block.get("text", "").strip()
            if not text:
                continue

            # bbox: [ymin, xmin, ymax, xmax] → [x1, y1, x2, y2]
            raw = block.get("bbox", [0, 0, 0, 0])
            source = block.get("source", "gemma")
            if len(raw) == 4:
                if source == "fitz":
                    bbox = raw
                else:
                    ymin, xmin, ymax, xmax = raw
                    bbox = [xmin, ymin, xmax, ymax]
            else:
                bbox = [0, 0, 0, 0]

            doc.blocks.append(ParsedBlock(
                block_id=block_id,
                page_no=page_no,
                text=text,
                bbox=bbox,
            ))
            block_id += 1

    return doc


# ──────────────────────────────────────────────
# [B] content 텍스트 덩어리 포맷
# [{"page": 1, "content": "전체텍스트..."}, ...]
# ──────────────────────────────────────────────

def from_content_format(
    ocr_result: list[dict],
    document_id: int = 0,
) -> ParsedDocument:
    doc = ParsedDocument(document_id=document_id)
    block_id = 1

    for page_data in ocr_result:
        page_no = page_data.get("page") or page_data.get("page_no") or 1
        content = page_data.get("content") or page_data.get("text") or ""

        for line in content.splitlines():
            line = line.strip()
            if not line:
                continue
            doc.blocks.append(ParsedBlock(
                block_id=block_id,
                page_no=page_no,
                text=line,
                bbox=[0, 0, 0, 0],
            ))
            block_id += 1

    return doc


# ──────────────────────────────────────────────
# [C] PaddleOCR raw blocks (bbox 4점 좌표)
# [{"page": 1, "blocks": [{"bbox": [[x1,y1],...], "text": "...", "confidence": 0.9}]}]
# ──────────────────────────────────────────────

def from_paddle_format(
    ocr_result: list[dict],
    document_id: int = 0,
) -> ParsedDocument:
    doc = ParsedDocument(document_id=document_id)
    block_id = 1

    for page_data in ocr_result:
        page_no = page_data.get("page") or page_data.get("page_no") or 1
        for block in page_data.get("blocks", []):
            text = block.get("text", "").strip()
            if not text:
                continue
            bbox = _paddle_bbox_to_xyxy(block.get("bbox", []))
            doc.blocks.append(ParsedBlock(
                block_id=block_id,
                page_no=page_no,
                text=text,
                bbox=bbox,
            ))
            block_id += 1

    return doc


def _paddle_bbox_to_xyxy(raw_bbox: list) -> list[float]:
    """PaddleOCR 4점 좌표 → [x1, y1, x2, y2]"""
    if not raw_bbox or len(raw_bbox) < 4:
        return [0, 0, 0, 0]
    try:
        xs = [pt[0] for pt in raw_bbox]
        ys = [pt[1] for pt in raw_bbox]
        return [min(xs), min(ys), max(xs), max(ys)]
    except (IndexError, TypeError):
        return [0, 0, 0, 0]


# ──────────────────────────────────────────────
# [D] zerox 출력 (ZeroxOutput 객체 또는 dict)
# ZeroxOutput(pages=[Page(content="마크다운", page=1), ...])
# ──────────────────────────────────────────────

def from_zerox_output(
    zerox_output,
    document_id: int = 0,
) -> ParsedDocument:
    doc = ParsedDocument(document_id=document_id)
    block_id = 1

    pages = zerox_output.pages if hasattr(zerox_output, "pages") \
            else zerox_output.get("pages", [])

    for page_obj in pages:
        if hasattr(page_obj, "content"):
            page_no = getattr(page_obj, "page", 1)
            content = page_obj.content or ""
        else:
            page_no = page_obj.get("page") or page_obj.get("page_no") or 1
            content = page_obj.get("content") or ""

        # 마크다운 문법 제거
        content = _re.sub(r"^#{1,6}\s*", "", content, flags=_re.MULTILINE)
        content = _re.sub(r"\*{1,2}(.+?)\*{1,2}", r"\1", content)
        content = _re.sub(r"^-{3,}\s*$", "", content, flags=_re.MULTILINE)

        for line in content.splitlines():
            line = line.strip()
            if not line:
                continue
            doc.blocks.append(ParsedBlock(
                block_id=block_id,
                page_no=page_no,
                text=line,
                bbox=[0, 0, 0, 0],
            ))
            block_id += 1

    return doc


# ──────────────────────────────────────────────
# 자동 감지 어댑터
# ──────────────────────────────────────────────

def adapt(
    ocr_result,
    document_id: int = 0,
) -> ParsedDocument:
    """
    포맷 자동 감지 후 변환.
    어떤 포맷으로 넘겨도 이 함수 하나만 호출하면 됨.

    우선순위:
      1. ZeroxOutput 객체 (pages 속성 있음)
      2. OCR 포맷 (dict + document_id + pages 키)
      3. zerox dict 직렬화 (dict + pages 키)
      4. PaddleOCR raw (list + blocks 키)
      5. content 텍스트 덩어리 (list + content/text 키)
    """
    # [D] ZeroxOutput 객체
    if hasattr(ocr_result, "pages"):
        return from_zerox_output(ocr_result, document_id)

    # dict 타입
    if isinstance(ocr_result, dict):
        # [A] OCR 포맷: document_id + pages 둘 다 있음
        if "pages" in ocr_result and "document_id" in ocr_result:
            return from_junior_format(ocr_result, document_id)
        # [D] zerox dict 직렬화: pages만 있음
        if "pages" in ocr_result:
            return from_zerox_output(ocr_result, document_id)
        return ParsedDocument(document_id=document_id)

    # list 타입
    if not ocr_result:
        return ParsedDocument(document_id=document_id)

    first = ocr_result[0]

    # [C] PaddleOCR raw
    if isinstance(first, dict) and "blocks" in first and isinstance(first["blocks"], list):
        # blocks 안에 bbox가 리스트의 리스트인지 확인 (4점 좌표)
        sample_blocks = first.get("blocks", [])
        if sample_blocks and isinstance(sample_blocks[0].get("bbox", None), list) \
                and sample_blocks[0]["bbox"] and isinstance(sample_blocks[0]["bbox"][0], list):
            return from_paddle_format(ocr_result, document_id)

    # [B] content 텍스트 덩어리
    if isinstance(first, dict) and ("content" in first or "text" in first):
        return from_content_format(ocr_result, document_id)

    return ParsedDocument(document_id=document_id)