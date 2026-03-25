import fitz
import requests
import base64
import json
import os
import concurrent.futures
import threading
import argparse

VLLM_URL   = os.getenv("VLLM_BASE_URL", "http://host.docker.internal:18080/v1") + "/chat/completions"
MODEL_NAME = os.getenv("VLLM_MODEL", "gemma-3-12b")
CACHE_DIR  = os.getenv("OCR_SAVE_DIR", "/data/ocr_results")

SYSTEM_PROMPT = """You are a highly precise RAG-optimized Document Parser.
Your task is to extract information from the provided document image (which contains complex and nested tables) into strictly atomic, self-contained Korean sentences.

[EXTRACTION RULES FOR RAG]
1. CONTEXT INHERITANCE (MERGED CELLS): For tables with merged cells (e.g., a "Category" or "Quantity" column spanning multiple rows), you MUST inherit and apply that parent context to EVERY corresponding child row. Never leave a child item orphaned without its category or quantity.
2. NATURAL SENTENCE GENERATION: Do not just list Key-Value pairs. Synthesize all related hierarchical headers and cell values into one natural, complete Korean sentence ending with an appropriate verb contextually derived from the table's purpose (e.g., "~이다", "~한다", "~로 구성된다").
   - Example pattern: Instead of "[Category: Server, Item: GPU, Spec: 24GB VRAM]", generate a cohesive sentence like "Server 카테고리의 GPU 사양은 24GB VRAM이다."
3. COMPLEX & NESTED TABLES: Reconstruct the logical relationship between table headers and cell values to support the generation of the self-contained sentences described above.
4. SENTENCE CONTINUITY: If a single sentence, paragraph, or logical phrase is split across multiple lines, rows, or cells, you MUST merge them into one continuous string without arbitrary line breaks. Do not split a single thought.
5. ATOMICITY: Every distinct clause, list item, bullet point, or specific table data point must be a separate block.
6. NO PAGE NUMBERS: Strictly exclude all page numbers, headers, or footers from the "text" field.
7. SYMBOLS: Preserve symbols like □, ■, ○, [ ] as they indicate important status, selection, or hierarchy.

[JSON SCHEMA]
{
  "blocks": [
    { "text": "Extracted self-contained Korean sentence", "bbox": [ymin, xmin, ymax, xmax] }
  ]
}
Output ONLY valid JSON. No backticks, no markdown formatting."""

file_lock = threading.Lock()

def process_and_save_final(base64_image, page_num, doc_id, output_path, final_data):
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": [{"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}]}
        ],
        "max_tokens": 8192,
        "temperature": 0.0
    }

    try:
        response = requests.post(VLLM_URL, json=payload, timeout=120)

        if response.status_code == 200:
            resp = response.json()
            raw = resp["choices"][0]["message"]["content"].strip()
            clean_json = raw.split("```json")[-1].split("```")[0].strip()
            content = json.loads(clean_json)

            page_entry = {
                "page_no": page_num,
                "blocks": [
                    {
                        "block_id": idx + 1,
                        "text": block.get("text", ""),
                        "bbox": block.get("bbox", [0, 0, 0, 0])
                    }
                    for idx, block in enumerate(content.get("blocks", []))
                ]
            }

            with file_lock:
                existing_pages = {p["page_no"]: p for p in final_data["pages"]}
                existing_pages[page_num] = page_entry
                final_data["pages"] = sorted(existing_pages.values(), key=lambda x: x["page_no"])

                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(final_data, f, ensure_ascii=False, indent=2)

                print(f"[Page {page_num:3d}] 저장 완료 | {len(page_entry['blocks'])}개 블록")
            return True
        else:
            print(f"[Page {page_num:3d}] API 오류: {response.status_code}")
            return False

    except Exception as e:
        print(f"[Page {page_num:3d}] 오류: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="PDF OCR 캐시 생성기")
    parser.add_argument("--pdf",      required=True,       help="PDF 파일 경로")
    parser.add_argument("--doc_id",   type=int, default=1001, help="문서 ID")
    parser.add_argument("--workers",  type=int, default=8,    help="동시 처리 스레드 수")
    parser.add_argument("--dpi",      type=int, default=150,  help="이미지 DPI (기본 150)")
    parser.add_argument("--out_dir",  default=CACHE_DIR,      help="캐시 저장 디렉토리")
    args = parser.parse_args()

    if not os.path.exists(args.pdf):
        print(f"[Error] 파일 없음: {args.pdf}")
        return

    # 캐시 파일명: ocr_{원본파일명}.json  ← FastAPI 캐시 히트 형식과 동일
    filename   = os.path.basename(args.pdf)
    os.makedirs(args.out_dir, exist_ok=True)
    output_path = os.path.join(args.out_dir, f"ocr_{filename}.json")

    # 이미 캐시 있으면 스킵
    if os.path.exists(output_path):
        print(f"[Skip] 캐시 이미 존재: {output_path}")
        print("  → 재생성하려면 캐시 파일을 삭제하고 다시 실행하세요.")
        return

    final_data = {"document_id": args.doc_id, "pages": []}

    doc    = fitz.open(args.pdf)
    images = []
    for i in range(len(doc)):
        pix     = doc[i].get_pixmap(dpi=args.dpi)
        img_b64 = base64.b64encode(pix.tobytes("png")).decode("utf-8")
        images.append((i + 1, img_b64))
    doc.close()

    print(f"[시작] {filename} | 총 {len(images)}페이지 | workers={args.workers} | dpi={args.dpi}")
    print(f"[저장] {output_path}")

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = [
            executor.submit(process_and_save_final, img, p, args.doc_id, output_path, final_data)
            for p, img in images
        ]
        concurrent.futures.wait(futures)

    success = sum(1 for p in final_data["pages"] if p["blocks"])
    print(f"\n[완료] {success}/{len(images)} 페이지 성공")
    print(f"[캐시] {output_path}")
    print(f"\n→ FastAPI 서버가 이 파일명으로 '{filename}'을 업로드하면 OCR 스킵합니다.")


if __name__ == "__main__":
    main()