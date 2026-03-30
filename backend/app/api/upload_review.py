"""
POST /projects/{project_id}/reviews/upload/stream
  - 파일 여러 개 한 번에 업로드
  - 파일별 순차 OCR (페이지는 병렬)
  - SSE로 진행상태 스트리밍
  - 전체 완료 시 review_run_id 반환
"""

from __future__ import annotations

import asyncio
import base64
import concurrent.futures
import json
import os
import threading
from datetime import datetime

import httpx
from fastapi import APIRouter, File, Form, UploadFile, HTTPException
from fastapi.responses import StreamingResponse

from app.schemas.enums import ReviewStatus

router = APIRouter()

VLLM_BASE_URL = os.getenv("VLLM_BASE_URL", "http://host.docker.internal:18080/v1")
VLLM_MODEL    = os.getenv("VLLM_MODEL", "gemma-3-12b")
OCR_WORKERS   = int(os.getenv("OCR_WORKERS", "8"))
OCR_TIMEOUT   = int(os.getenv("OCR_TIMEOUT", "120"))
PDF_SAVE_DIR  = os.getenv("PDF_SAVE_DIR", "/data/clms_seocho")

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
# OCR 단일 페이지
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
            {"block_id": idx + 1, "text": b.get("text", ""), "bbox": b.get("bbox", [0,0,0,0])}
            for idx, b in enumerate(content.get("blocks", []))
        ]
        return {"page_no": page_num, "blocks": blocks}

    except Exception as e:
        print(f"[OCR] p.{page_num} 오류: {e}")
        return None


# ──────────────────────────────────────────────
# PDF → OCR (페이지 병렬, SSE 콜백 포함)
# ──────────────────────────────────────────────

async def _run_ocr_with_progress(
    pdf_bytes: bytes,
    document_id: int,
    on_page_done=None,   # async callable(page_no, done, total)
    filename: str = "",
) -> dict:
    import fitz

    # ── 캐시 히트 확인 (미리 OCR 돌려놓은 파일 있으면 스킵)
    if filename:
        from pathlib import Path
        from app.services.storage.minio_client import load_ocr_cache
        stem   = Path(filename).stem                              # 확장자 제거
        cached = load_ocr_cache(stem)                             # MinIO에서 로드
        if cached:
            cached["document_id"] = document_id
            if on_page_done:
                total = len(cached.get("pages", []))
                for p in cached.get("pages", []):
                    await on_page_done(p["page_no"], p["page_no"], total)
            return cached

    doc    = fitz.open(stream=pdf_bytes, filetype="pdf")
    images = []
    for i in range(len(doc)):
        pix     = doc[i].get_pixmap(dpi=150)
        img_b64 = base64.b64encode(pix.tobytes("png")).decode("utf-8")
        images.append((i + 1, img_b64))
    doc.close()

    total        = len(images)
    pages_done   = 0
    ocr_results  = {}
    results_lock = threading.Lock()

    def _ocr_and_store(page_num, img_b64):
        result = _ocr_page(page_num, img_b64)
        with results_lock:
            if result:
                ocr_results[page_num] = result
        return page_num

    loop = asyncio.get_event_loop()
    with concurrent.futures.ThreadPoolExecutor(max_workers=OCR_WORKERS) as executor:
        futures = [
            loop.run_in_executor(executor, _ocr_and_store, pn, img)
            for pn, img in images
        ]
        for coro in asyncio.as_completed(futures):
            page_num    = await coro
            pages_done += 1
            if on_page_done:
                await on_page_done(page_num, pages_done, total)

    return {
        "document_id": document_id,
        "pages": sorted(ocr_results.values(), key=lambda x: x["page_no"]),
    }


# ──────────────────────────────────────────────
# 다중 파일 업로드 + SSE 스트리밍
# ──────────────────────────────────────────────

@router.post(
    "/upload/stream",
    summary="파일 업로드 → 검토 실행 (SSE)",
    description="""
PDF 파일 여러 개를 한 번에 업로드하면 OCR → 검토까지 실행합니다.
진행상태는 SSE로 실시간 전달됩니다.

**SSE 이벤트:**
- `file_start`  : 파일 OCR 시작 { filename, file_index, total_files, total_pages }
- `ocr_page`    : 페이지 완료   { page_no, done, total, progress }
- `file_done`   : 파일 검토 완료 { filename, issue_count, doc_type, progress }
- `all_done`    : 전체 완료     { review_run_id, total_issues, files }
- `error`       : 오류          { filename, message }

**프론트 호출:**
```js
const form = new FormData()
files.forEach(f => form.append('files', f))
form.append('use_llm', 'true')
const res = await fetch('/api/v1/projects/1/reviews/upload/stream', {
  method: 'POST', body: form
})
```
""",
)
async def upload_and_review_stream(
    project_id: int,
    files:           list[UploadFile] = File(..., description="검토 파일들"),
    use_llm:         bool             = Form(True),
    file_categories: str              = Form("{}",  description="파일명→doc_type JSON"),
) -> StreamingResponse:

    # 사용자가 지정한 카테고리 파싱
    import json as _json
    try:
        _user_categories: dict[str, str] = _json.loads(file_categories)
    except Exception:
        _user_categories = {}

    ALLOWED_EXT = {".pdf", ".hwp", ".hwpx", ".xlsx", ".xls", ".txt"}

    # 파일 검증 + 읽기
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

        def sse(event_type: str, data: dict) -> str:
            return f"data: {json.dumps({'type': event_type, **data}, ensure_ascii=False)}\n\n"

        run_id        = _next_run_id()
        all_issues    = []
        file_results  = []
        total_files   = len(file_list)

        # ── 파일별 순차 처리
        for file_idx, file_info in enumerate(file_list):
            filename  = file_info["filename"]
            pdf_bytes = file_info["bytes"]
            doc_id    = run_id * 100 + file_idx + 1

            try:
                # ── PDF 파일 서버에 저장 (캐시 빌더 스크립트에서도 재사용 가능)
                try:
                    os.makedirs(PDF_SAVE_DIR, exist_ok=True)
                    pdf_save_path = os.path.join(PDF_SAVE_DIR, filename)
                    with open(pdf_save_path, "wb") as f:
                        f.write(pdf_bytes)
                    print(f"[Upload] PDF 저장: {pdf_save_path}")
                except Exception as e:
                    print(f"[Upload] PDF 저장 실패 (무시): {e}")

                # 페이지 수 미리 파악
                import fitz
                tmp_doc     = fitz.open(stream=pdf_bytes, filetype="pdf")
                total_pages = len(tmp_doc)
                tmp_doc.close()

                yield sse("file_start", {
                    "filename":    filename,
                    "file_index":  file_idx + 1,
                    "total_files": total_files,
                    "total_pages": total_pages,
                })

                # OCR 진행상태 콜백
                async def on_page_done(page_no, done, total,
                                       _fi=file_idx, _fn=filename, _tf=total_files):
                    # 전체 진행률: 파일별 60% 비중
                    file_progress = done / total
                    overall = (_fi / _tf) + (file_progress * 0.6 / _tf)
                    # yield는 클로저에서 직접 못 쓰므로 queue 방식
                    progress_queue.append(sse("ocr_page", {
                        "filename":  _fn,
                        "page_no":   page_no,
                        "done":      done,
                        "total":     total,
                        "progress":  round(overall, 3),
                    }))

                progress_queue: list[str] = []

                # OCR 실행 (캐시 있으면 스킵, 없으면 병렬 처리)
                ocr_task = asyncio.create_task(
                    _run_ocr_with_progress(pdf_bytes, doc_id, on_page_done, filename)
                )

                # OCR 돌면서 큐에 쌓인 SSE 메시지 flush
                while not ocr_task.done():
                    await asyncio.sleep(0.1)
                    while progress_queue:
                        yield progress_queue.pop(0)

                ocr_result = await ocr_task
                while progress_queue:
                    yield progress_queue.pop(0)

                # OCR 결과 저장 (인메모리 + MinIO)
                if run_id not in _ocr_store:
                    _ocr_store[run_id] = {}
                _ocr_store[run_id][doc_id] = ocr_result

                from pathlib import Path
                from app.services.storage.minio_client import save_ocr_cache, upload_pdf
                _stem = Path(filename).stem
                # MinIO에 OCR 캐시 저장 (비동기)
                loop = asyncio.get_event_loop()
                loop.run_in_executor(None, save_ocr_cache, _stem, ocr_result)
                # MinIO에 PDF 원본 저장 (비동기)
                loop.run_in_executor(None, upload_pdf, pdf_bytes, filename)

                # 어댑터 + 타입 감지
                adapted   = adapt(ocr_result, doc_id)
                full_text = "\n".join(b.text for b in adapted.blocks)

                # 사용자 지정 카테고리 우선, 없으면 자동 감지
                if filename in _user_categories and _user_categories[filename]:
                    doc_type = _user_categories[filename]
                    print(f"[Upload] {filename} → 사용자 지정 doc_type: {doc_type}")
                else:
                    doc_type = detect_doc_type(full_text, filename)
                    print(f"[Upload] {filename} → 자동 감지 doc_type: {doc_type}")

                # 검토 실행
                issues = await run_hybrid_review(
                    full_text=full_text,
                    document_id=doc_id,
                    review_run_id=run_id,
                    use_llm=use_llm,
                    doc_type=doc_type,
                )

                all_issues.extend(issues)
                file_results.append({
                    "filename":    filename,
                    "doc_type":    doc_type,
                    "document_id": doc_id,
                    "issue_count": len(issues),
                    "full_text":   full_text,
                    "page_count":  total_pages,
                })

                # 문서 메타 등록 (documents API 조회용)
                try:
                    from app.api.documents import register_document
                    register_document(doc_id, {
                        "project_id":  project_id,
                        "filename":    filename,
                        "doc_type":    doc_type,
                        "document_id": doc_id,
                        "file_size":   len(pdf_bytes),
                        "page_count":  total_pages,
                        "uploaded_at": datetime.now().isoformat(),
                    })
                except Exception:
                    pass

                overall_progress = (file_idx + 1) / total_files
                yield sse("file_done", {
                    "filename":    filename,
                    "doc_type":    doc_type,
                    "issue_count": len(issues),
                    "progress":    round(overall_progress, 3),
                })

            except Exception as e:
                yield sse("error", {"filename": filename, "message": str(e)})

        # ── 전체 이슈 id 재부여 + 저장
        for i, iss in enumerate(all_issues, start=1):
            iss["id"]            = i
            iss["review_run_id"] = run_id

       # 전체 문서 텍스트 합산 (채팅 RAG용)
        combined_text = "\n".join(
            f"=== {f['filename']} ===\n{f.get('full_text', '')}"
            for f in file_results
        )

        store_data = {
            "project_id":   project_id,
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
            print(f"[Redis] 저장 실패 (인메모리 유지): {e}")
        try:
            from app.api.projects import _get_project, _save_project

            project = _get_project(project_id)
            if project:
                project["latest_review_id"] = run_id
                project["latest_review_status"] = ReviewStatus.completed
                project["updated_at"] = datetime.now().isoformat()
                _save_project(project_id, project)
        except Exception as e:
            print(f"[Project] 최신 검토 상태 갱신 실패: {e}")
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


# ──────────────────────────────────────────────
# OCR 결과 저장소 (인메모리 + 파일 동시 저장)
# ──────────────────────────────────────────────
_ocr_store: dict[int, dict[int, dict]] = {}   # { review_run_id: { document_id: ocr_result } }
OCR_SAVE_DIR = os.getenv("OCR_SAVE_DIR", "/data/ocr_results")


def _save_ocr_to_file(run_id: int, ocr_result: dict, filename: str):
    """OCR 결과를 JSON 파일로 저장"""
    try:
        from pathlib import Path
        os.makedirs(OCR_SAVE_DIR, exist_ok=True)
        stem     = Path(filename).stem
        out_path = os.path.join(OCR_SAVE_DIR, f"ocr_{stem}.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(ocr_result, f, ensure_ascii=False, indent=2)
        print(f"[OCR] 파일 저장: {out_path}")
        return out_path
    except Exception as e:
        print(f"[OCR] 파일 저장 실패: {e}")
        return None


# ──────────────────────────────────────────────
# OCR 결과 조회 API
# ──────────────────────────────────────────────

@router.get(
    "/ocr/{review_run_id}",
    summary="OCR 결과 조회",
    description="""
검토 실행 후 OCR 결과(페이지별 블록 텍스트)를 조회합니다.

**파라미터:**
- `page`: 특정 페이지만 조회 (없으면 전체)
- `text_only`: True면 텍스트만, False면 bbox 포함 전체 반환
""",
)
async def get_ocr_result(
    project_id:    int,
    review_run_id: int,
    page:          int  | None = None,
    text_only:     bool        = False,
):
    from app.api.reviews import _get_review_in_project

    review = _get_review_in_project(review_run_id, project_id)
    if not review:
        raise HTTPException(status_code=404, detail="해당 프로젝트의 검토 결과가 없습니다.")

    files = review.get("files", [])
    target_document_id = files[0]["document_id"] if files else None

    ocr_map = _ocr_store.get(review_run_id, {})
    ocr = ocr_map.get(target_document_id) if target_document_id is not None else None

    # 인메모리에 없으면 MinIO에서 복원
    if not ocr:
        try:
            from app.services.storage.minio_client import load_ocr_cache
            from pathlib import Path

            stems = [Path(f["filename"]).stem for f in files] if files else []

            for f in files:
                stem = Path(f["filename"]).stem
                cached = load_ocr_cache(stem)
                if cached:
                    if review_run_id not in _ocr_store:
                        _ocr_store[review_run_id] = {}
                    _ocr_store[review_run_id][f["document_id"]] = cached

                    if f["document_id"] == target_document_id:
                        ocr = cached
                        print(f"[OCR] MinIO에서 복원: {stem}")
                        break
        except Exception as e:
            print(f"[OCR] MinIO 복원 실패: {e}")

    if not ocr:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="OCR 결과가 없습니다. 파일을 다시 업로드해주세요.")

    pages = ocr.get("pages", [])

    # 특정 페이지 필터
    if page is not None:
        pages = [p for p in pages if p["page_no"] == page]
        if not pages:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail=f"{page}페이지 OCR 결과가 없습니다.")

    # text_only 모드: bbox 제거하고 텍스트만
    if text_only:
        result = {
            "document_id": ocr["document_id"],
            "total_pages": len(ocr["pages"]),
            "pages": [
                {
                    "page_no":    p["page_no"],
                    "text":       "\n".join(b["text"] for b in p["blocks"] if b.get("text")),
                    "block_count": len(p["blocks"]),
                }
                for p in pages
            ],
        }
    else:
        result = {
            "document_id": ocr["document_id"],
            "total_pages": len(ocr["pages"]),
            "pages": pages,
        }

    return {"success": True, "data": result}


@router.get(
    "/ocr/{review_run_id}/text",
    summary="OCR 전체 텍스트 조회 (plain text)",
    description="OCR 결과를 페이지 구분선과 함께 plain text로 반환합니다.",
)
async def get_ocr_full_text(
    project_id:    int,
    review_run_id: int,
):
    from app.api.reviews import _get_review_in_project

    review = _get_review_in_project(review_run_id, project_id)
    if not review:
        raise HTTPException(status_code=404, detail="해당 프로젝트의 검토 결과가 없습니다.")

    files = review.get("files", [])
    target_document_id = files[0]["document_id"] if files else None

    ocr_map = _ocr_store.get(review_run_id, {})
    ocr = ocr_map.get(target_document_id) if target_document_id is not None else None

    if not ocr:
        try:
            from app.services.storage.minio_client import load_ocr_cache
            from pathlib import Path
    
            for f in files:
                stem = Path(f["filename"]).stem
                cached = load_ocr_cache(stem)
                if cached:
                    if review_run_id not in _ocr_store:
                        _ocr_store[review_run_id] = {}
                    _ocr_store[review_run_id][f["document_id"]] = cached
    
                    if f["document_id"] == target_document_id:
                        ocr = cached
                        print(f"[OCR] MinIO에서 복원: {stem}")
                        break
        except Exception as e:
            print(f"[OCR] MinIO 복원 실패: {e}")
    if not ocr:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="OCR 결과가 없습니다.")

    lines = []
    for p in ocr.get("pages", []):
        lines.append(f"\n{'='*50}")
        lines.append(f"  Page {p['page_no']}")
        lines.append(f"{'='*50}")
        for b in p.get("blocks", []):
            if b.get("text"):
                lines.append(b["text"])

    from fastapi.responses import PlainTextResponse
    return PlainTextResponse("\n".join(lines))