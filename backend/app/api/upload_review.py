"""
POST /projects/{project_id}/reviews/upload/stream
  - 파일 여러 개 한 번에 업로드
  - 파일별 순차 처리
  - fitz 직접 추출 (표/스캔본은 Gemma OCR fallback)
  - gotenberg으로 비PDF 변환
  - SSE로 진행상태 스트리밍
"""

from __future__ import annotations

import asyncio
import base64
import json
import os
import threading
from datetime import datetime

import httpx
from fastapi import APIRouter, File, Form, UploadFile, HTTPException
from fastapi.responses import StreamingResponse

from app.schemas.enums import ReviewStatus

router = APIRouter()

VLLM_BASE_URL  = os.getenv("VLLM_BASE_URL", "http://host.docker.internal:18080/v1")
VLLM_MODEL     = os.getenv("VLLM_MODEL", "gemma-3-12b")
OCR_TIMEOUT    = int(os.getenv("OCR_TIMEOUT", "120"))
PDF_SAVE_DIR   = os.getenv("PDF_SAVE_DIR", "/data/clms_seocho")
GOTENBERG_URL  = os.getenv("GOTENBERG_URL", "http://gotenberg:3000")

OCR_SYSTEM_PROMPT = """You are a highly precise RAG-optimized Document Parser.
Your task is to extract information from the provided document image (which contains complex and nested tables) into strictly atomic, self-contained Korean sentences.

[EXTRACTION RULES FOR RAG]
1. CONTEXT INHERITANCE (MERGED CELLS): For tables with merged cells, you MUST inherit and apply that parent context to EVERY corresponding child row.
2. NATURAL SENTENCE GENERATION: Synthesize all related hierarchical headers and cell values into one natural, complete Korean sentence.
3. SENTENCE CONTINUITY: If a single sentence is split across multiple lines or cells, merge them into one continuous string.
4. ATOMICITY: Every distinct clause, list item, or table data point must be a separate block.
5. NO PAGE NUMBERS: Exclude all page numbers, headers, or footers.
6. SYMBOLS: Preserve symbols like □, ■, ○, [ ] as they indicate important status or hierarchy.

[JSON SCHEMA]
{
  "blocks": [
    { "text": "Extracted self-contained Korean sentence", "bbox": [ymin, xmin, ymax, xmax] }
  ]
}
Output ONLY valid JSON. No backticks, no markdown formatting."""


# ──────────────────────────────────────────────
# Gemma OCR — 단일 페이지 (스캔본/표 fallback용)
# ──────────────────────────────────────────────

def _ocr_page(page_num: int, base64_image: str) -> dict | None:
    payload = {
        "model": VLLM_MODEL,
        "messages": [
            {"role": "system", "content": OCR_SYSTEM_PROMPT},
            {"role": "user", "content": [
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}
            ]},
        ],
        "max_tokens": 8192,
        "temperature": 0.0,
    }
    try:
        resp = httpx.post(
            f"{VLLM_BASE_URL}/chat/completions",
            json=payload,
            timeout=OCR_TIMEOUT,
        )
        if resp.status_code != 200:
            print(f"[OCR] p.{page_num} HTTP {resp.status_code}")
            return None

        raw   = resp.json()["choices"][0]["message"]["content"].strip()
        clean = raw.split("```json")[-1].split("```")[0].strip()
        content = json.loads(clean)

        blocks = [
            {"block_id": idx + 1, "text": b.get("text", ""), "bbox": b.get("bbox", [0, 0, 0, 0])}
            for idx, b in enumerate(content.get("blocks", []))
        ]
        return {"page_no": page_num, "blocks": blocks}

    except Exception as e:
        print(f"[OCR] p.{page_num} 오류: {e}")
        return None


# ──────────────────────────────────────────────
# gotenberg — 비PDF 변환
# ──────────────────────────────────────────────

async def convert_to_pdf(file_bytes: bytes, filename: str) -> bytes:
    ext = filename.rsplit(".", 1)[-1].lower()
    if ext == "pdf":
        return file_bytes
    print(f"[Gotenberg] {filename} → PDF 변환 중...")
    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            f"{GOTENBERG_URL}/forms/libreoffice/convert",
            files={"files": (filename, file_bytes)},
        )
        resp.raise_for_status()
        print(f"[Gotenberg] {filename} → PDF 변환 완료")
        return resp.content

PADDLEOCR_URL = os.getenv("PADDLEOCR_URL", "http://paddleocr:8001")

async def ocr_with_paddle(img_b64: str, page_no: int) -> list[dict]:
    """PaddleOCR 서버로 이미지 전송 → 텍스트 + bbox"""
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            f"{PADDLEOCR_URL}/ocr/page",
            json={"image_base64": img_b64, "page_no": page_no},
        )
        resp.raise_for_status()
        data = resp.json()
        for blk in data["blocks"]:
            blk["source"] = "paddle"
        return data["blocks"]


def extract_with_fitz(pdf_bytes: bytes, document_id: int) -> dict:
    import fitz
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    pages = []
    pending_paddle = []  # (page_idx, img_b64) — 비동기로 나중에 처리

    for i in range(len(doc)):
        page = doc[i]

        try:
            has_table = len(page.find_tables().tables) > 0
        except Exception:
            has_table = False

        raw_blocks = page.get_text("blocks")
        has_text = any(b[4].strip() for b in raw_blocks)

        if not has_text:
            # 스캔본 → Gemma fallback (Paddle 대신)
            print(f"[fitz] p.{i+1} 스캔본 → Gemma OCR")
            pix = page.get_pixmap(dpi=150)
            img_b64 = base64.b64encode(pix.tobytes("png")).decode("utf-8")
            gemma_result = _ocr_page(i + 1, img_b64)
            if gemma_result:
                for blk in gemma_result["blocks"]:
                    blk["source"] = "gemma"
                parsed_blocks = gemma_result["blocks"]
            else:
                parsed_blocks = []
            pages.append({"page_no": i + 1, "blocks": parsed_blocks})
        else:
            # fitz 직접
            parsed_blocks = [
                {
                    "block_id": idx + 1,
                    "text": b[4].strip(),
                    "bbox": [b[0], b[1], b[2], b[3]],
                    "source": "fitz",
                }
                for idx, b in enumerate(raw_blocks)
                if b[4].strip()
            ]

            if has_table:
                # 표 있으면 PaddleOCR로 보완 예약
                pix = page.get_pixmap(dpi=300)
                img_b64 = base64.b64encode(pix.tobytes("png")).decode("utf-8")
                pending_paddle.append((i, img_b64))
                pages.append({"page_no": i + 1, "blocks": parsed_blocks, "_pending": True, "_fitz_blocks": parsed_blocks})
            else:
                pages.append({"page_no": i + 1, "blocks": parsed_blocks})

    doc.close()
    return {
        "document_id": document_id,
        "pages": pages,
        "_pending_paddle": pending_paddle,
    }

# ──────────────────────────────────────────────
# 다중 파일 업로드 + SSE 스트리밍
# ──────────────────────────────────────────────

_ocr_store: dict[int, dict[int, dict]] = {}


@router.post("/upload/stream", summary="파일 업로드 → 검토 실행 (SSE)")
async def upload_and_review_stream(
    project_id: int,
    files:           list[UploadFile] = File(...),
    use_llm:         bool             = Form(True),
    file_categories: str              = Form("{}"),
) -> StreamingResponse:

    import json as _json
    try:
        _user_categories: dict[str, str] = _json.loads(file_categories)
    except Exception:
        _user_categories = {}

    ALLOWED_EXT = {".pdf", ".hwp", ".hwpx", ".xlsx", ".xls", ".txt", ".pptx", ".ppt", ".docx", ".doc"}

    file_list = []
    for f in files:
        ext = "." + f.filename.rsplit(".", 1)[-1].lower() if "." in f.filename else ""
        if ext not in ALLOWED_EXT:
            raise HTTPException(status_code=400, detail=f"{f.filename}: 지원하지 않는 형식입니다.")
        data = await f.read()
        if not data:
            raise HTTPException(status_code=400, detail=f"{f.filename}: 빈 파일입니다.")
        file_list.append({"filename": f.filename, "bytes": data})

    async def generate():
        from app.api.reviews import _next_run_id, _review_store, _store_lock
        from app.services.review.ocr_adapter import adapt
        from app.services.review.doc_type_dispatcher import detect_doc_type
        from app.services.review.vllm_reviewer import run_hybrid_review
        from pathlib import Path
        from app.services.storage.minio_client import save_ocr_cache, upload_pdf, load_ocr_cache

        def sse(event_type: str, data: dict) -> str:
            return f"data: {json.dumps({'type': event_type, **data}, ensure_ascii=False)}\n\n"

        run_id      = _next_run_id()
        all_issues  = []
        file_results = []
        total_files  = len(file_list)
        loop         = asyncio.get_event_loop()

        for file_idx, file_info in enumerate(file_list):
            filename       = file_info["filename"]
            original_bytes = file_info["bytes"]

            try:
                # 1) PDF 변환
                pdf_bytes    = await convert_to_pdf(original_bytes, filename)
                pdf_filename = (
                    filename.rsplit(".", 1)[0] + ".pdf"
                    if not filename.lower().endswith(".pdf")
                    else filename
                )

                # 2) 로컬 저장
                try:
                    os.makedirs(PDF_SAVE_DIR, exist_ok=True)
                    with open(os.path.join(PDF_SAVE_DIR, pdf_filename), "wb") as f:
                        f.write(pdf_bytes)
                except Exception as e:
                    print(f"[Upload] 로컬 저장 실패 (무시): {e}")

                # 3) 페이지 수
                import fitz
                tmp = fitz.open(stream=pdf_bytes, filetype="pdf")
                total_pages = len(tmp)
                tmp.close()

                doc_id = run_id * 100 + file_idx + 1

                yield sse("file_start", {
                    "filename":    filename,
                    "file_index":  file_idx + 1,
                    "total_files": total_files,
                    "total_pages": total_pages,
                })

                # 4) 캐시 확인
                import copy
                stem   = Path(filename).stem
                cached = load_ocr_cache(stem)
                if cached:
                    ocr_result = copy.deepcopy(cached)
                    ocr_result["document_id"] = doc_id
                    print(f"[OCR] 캐시 히트: {stem}")
                    for p in ocr_result["pages"]:
                        yield sse("ocr_page", {
                            "filename": filename,
                            "page_no":  p["page_no"],
                            "done":     p["page_no"],
                            "total":    total_pages,
                            "progress": round(file_idx / total_files + p["page_no"] / total_pages * 0.6 / total_files, 3),
                        })
                else:
                    # 5) fitz 추출
                    ocr_result = await loop.run_in_executor(
                        None, extract_with_fitz, pdf_bytes, doc_id
                    )
                    # PaddleOCR 순차 처리
                    pending = ocr_result.pop("_pending_paddle", [])
                    if pending:
                        paddle_results = []
                        for page_idx, img_b64 in pending:
                            try:
                                result = await ocr_with_paddle(img_b64, page_idx + 1)
                                print(f"[Paddle] p.{page_idx+1} 블록 수: {len(result)}")
                                if result:
                                    print(f"  첫 블록: {result[0].get('text','')[:30]}, bbox={result[0].get('bbox')}")
                                paddle_results.append(result)
                            except Exception as e:
                                print(f"[Paddle] p.{page_idx+1} 오류: {e}")
                                paddle_results.append([])

                        for (page_idx, _), paddle_blocks in zip(pending, paddle_results):
                            if not paddle_blocks:
                                continue
                            page = ocr_result["pages"][page_idx]
                            fitz_blocks = page.get("_fitz_blocks", [])
                            if fitz_blocks:
                                existing_texts = {b["text"][:20] for b in fitz_blocks}
                                for blk in paddle_blocks:
                                    if blk["text"][:20] not in existing_texts:
                                        fitz_blocks.append(blk)
                                page["blocks"] = fitz_blocks
                            else:
                                page["blocks"] = paddle_blocks
                            page.pop("_pending", None)
                            page.pop("_fitz_blocks", None)

                    # 페이지별 SSE
                    for p in ocr_result["pages"]:
                        yield sse("ocr_page", {
                            "filename": filename,
                            "page_no":  p["page_no"],
                            "done":     p["page_no"],
                            "total":    total_pages,
                            "progress": round(file_idx / total_files + p["page_no"] / total_pages * 0.6 / total_files, 3),
                        })
                    # MinIO 캐시 저장
                    loop.run_in_executor(None, save_ocr_cache, stem, ocr_result)

                # 6) MinIO 원본/PDF 저장
                loop.run_in_executor(None, upload_pdf, original_bytes, f"originals/{filename}")
                loop.run_in_executor(None, upload_pdf, pdf_bytes, pdf_filename)

                # 7) 인메모리 저장
                if run_id not in _ocr_store:
                    _ocr_store[run_id] = {}
                _ocr_store[run_id][doc_id] = ocr_result

                # 8) 어댑터 + 타입 감지
                adapted   = adapt(ocr_result, doc_id)
                full_text = "\n".join(b.text for b in adapted.blocks)
                
                # milvus에 블록 저장
                try:
                    from app.services.storage.milvus_store import store_blocks
                    loop.run_in_executor(None, store_blocks, adapted)
                except Exception as e:
                    print(f"[Milvus] 블록 저장 실패: {e}")

                if filename in _user_categories and _user_categories[filename]:
                    doc_type = _user_categories[filename]
                else:
                    doc_type = detect_doc_type(full_text, filename)

                print(f"[Upload] {filename} → doc_type: {doc_type}")

                # 9) 룰엔진 + vLLM
                issues = await run_hybrid_review(
                    full_text=full_text,
                    document_id=doc_id,
                    review_run_id=run_id,
                    use_llm=use_llm,
                    doc_type=doc_type,
                    parsed_doc=adapted,
                )

                all_issues.extend(issues)
                file_results.append({
                    "filename":     filename,
                    "pdf_filename": pdf_filename,
                    "doc_type":     doc_type,
                    "document_id":  doc_id,
                    "issue_count":  len(issues),
                    "full_text":    full_text,
                    "page_count":   total_pages,
                })

                try:
                    from app.api.documents import register_document
                    register_document(doc_id, {
                        "project_id":   project_id,
                        "filename":     filename,
                        "pdf_filename": pdf_filename,
                        "doc_type":     doc_type,
                        "document_id":  doc_id,
                        "file_size":    len(pdf_bytes),
                        "page_count":   total_pages,
                        "uploaded_at":  datetime.now().isoformat(),
                    })
                except Exception:
                    pass

                yield sse("file_done", {
                    "filename":    filename,
                    "doc_type":    doc_type,
                    "issue_count": len(issues),
                    "progress":    round((file_idx + 1) / total_files, 3),
                })

            except Exception as e:
                print(f"[Upload] {filename} 오류: {e}")
                yield sse("error", {"filename": filename, "message": str(e)})

        # 전체 이슈 id 재부여
        for i, iss in enumerate(all_issues, start=1):
            iss["id"]            = i
            iss["review_run_id"] = run_id

        combined_text = "\n".join(
            f"=== {f['filename']} ===\n{f.get('full_text', '')}"
            for f in file_results
        )

        store_data = {
            "project_id":  project_id,
            "status":      ReviewStatus.completed,
            "document_id": file_results[0]["document_id"] if file_results else 0,
            "issues":      all_issues,
            "files":       file_results,
            "full_text":   combined_text,
            "started_at":  datetime.now().isoformat(),
            "finished_at": datetime.now().isoformat(),
        }
        with _store_lock:
            _review_store[run_id] = store_data

        try:
            from app.services.storage.redis_store import save_review
            save_review(run_id, dict(store_data))
        except Exception as e:
            print(f"[Redis] 저장 실패: {e}")

        try:
            from app.api.projects import _get_project, _save_project
            project = _get_project(project_id)
            if project:
                project["latest_review_id"]     = run_id
                project["latest_review_status"] = ReviewStatus.completed
                project["updated_at"]           = datetime.now().isoformat()
                _save_project(project_id, project)
        except Exception as e:
            print(f"[Project] 갱신 실패: {e}")

        yield sse("all_done", {
            "review_run_id": run_id,
            "total_issues":  len(all_issues),
            "files":         file_results,
            "progress":      1.0,
        })

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )