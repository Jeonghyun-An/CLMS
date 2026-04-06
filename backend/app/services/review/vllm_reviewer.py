"""
vLLM 계약서류 검토 클라이언트 — 문서 타입별 룰셋 + 프롬프트 연동
────────────────────────────────────────────────────────────
- docker-compose의 vLLM 서버 (Gemma-3-12b) 호출
- OpenAI 호환 API (/v1/chat/completions) 사용
- 문서 타입(bid_notice / proposal_request / plan)별 룰셋 자동 선택
- 룰 엔진(정량) + vLLM(정성) 하이브리드
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from typing import TYPE_CHECKING

import httpx

if TYPE_CHECKING:
    from app.services.review.engine import ParsedDocument

VLLM_BASE_URL = os.getenv("VLLM_BASE_URL", "http://host.docker.internal:18080/v1")
VLLM_MODEL    = os.getenv("VLLM_MODEL", "gemma-3-12b")
TIMEOUT       = 120


async def call_vllm(
    text: str,
    already_found: list[str],
    system_prompt: str,
    max_tokens: int = 1500,
) -> list[dict]:
    user_msg = f"""다음 계약서류를 검토해주세요.

=== 문서 텍스트 ===
{text[:4000]}
=== 끝 ===

이미 감지된 이슈 (중복 제외):
{chr(10).join(f'- {t}' for t in already_found) if already_found else '없음'}

위 문서에서 추가로 발견된 문제점만 JSON 배열로 반환하세요."""

    payload = {
        "model":       VLLM_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_msg},
        ],
        "max_tokens":  max_tokens,
        "temperature": 0.1,
        "top_p":       0.9,
    }

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.post(
                f"{VLLM_BASE_URL}/chat/completions",
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"].strip()
        return _parse_llm_response(content)
    except httpx.TimeoutException:
        print(f"[vLLM] 타임아웃 ({TIMEOUT}s)")
        return []
    except httpx.HTTPStatusError as e:
        print(f"[vLLM] HTTP {e.response.status_code}")
        return []
    except Exception as e:
        print(f"[vLLM] 오류: {e}")
        return []


def _parse_llm_response(content: str) -> list[dict]:
    content = content.strip()
    if content.startswith("```"):
        content = "\n".join(
            l for l in content.splitlines()
            if not l.strip().startswith("```")
        )
    start = content.find("[")
    end   = content.rfind("]") + 1
    if start == -1 or end == 0:
        return []
    try:
        issues = json.loads(content[start:end])
        return [_normalize_llm_issue(i) for i in issues if isinstance(i, dict)]
    except json.JSONDecodeError:
        return []


def _normalize_llm_issue(raw: dict) -> dict:
    valid_sev = {"critical", "high", "warning", "info"}
    valid_cat = {"missing", "regulation_violation", "inconsistency", "typo", "approval_rule"}
    severity = raw.get("severity", "warning")
    if severity not in valid_sev:
        severity = "warning"
    category = raw.get("category", "inconsistency")
    if category not in valid_cat:
        category = "inconsistency"
    quoted  = raw.get("quoted_text")
    law_ref = raw.get("law_ref")
    return {
        "rule_id":         raw.get("rule_id", "L000"),
        "severity":        severity,
        "category":        category,
        "title":           raw.get("title", "검토 필요"),
        "description":     raw.get("description", ""),
        "recommendation":  raw.get("recommendation", ""),
        "regulation_refs": [{"regulation_title": law_ref, "article_no": raw.get("rule_id"), "quoted_text": law_ref}] if law_ref else [],
        "evidences":       [{"block_id": None, "page_no": 1, "quoted_text": quoted}] if quoted else [],
        "highlights":      [],
        "status":          "open",
        "source":          "llm",
        "created_at":      datetime.now().isoformat(),
    }
def _find_bbox_for_quoted_text(
    quoted_text: str,
    parsed_doc: "ParsedDocument",
) -> list[dict]:
    """quoted_text와 매칭되는 블록 찾아서 bbox 반환"""
    if not quoted_text or not parsed_doc:
        return []

    search = quoted_text[:30].strip()
    candidates = []

    for block in parsed_doc.blocks:
        # 정확 매칭
        if search in block.text or block.text[:30] in quoted_text:
            if any(v > 0 for v in block.bbox):
                candidates.append({
                    "page_no":  block.page_no,
                    "bbox":     block.bbox,
                    "block_id": block.block_id,
                })

    # 정확 매칭 없으면 단어 단위 fuzzy 매칭
    if not candidates:
        words = set(search.split())
        for block in parsed_doc.blocks:
            block_words = set(block.text.split())
            overlap = words & block_words
            if len(overlap) >= min(2, len(words)) and any(v > 0 for v in block.bbox):
                candidates.append({
                    "page_no":  block.page_no,
                    "bbox":     block.bbox,
                    "block_id": block.block_id,
                })

    return candidates[:3]  # 최대 3개

async def run_hybrid_review(
    full_text: str,
    document_id: int = 0,
    review_run_id: int = 0,
    use_llm: bool = True,
    doc_type: str = "unknown",
    parsed_doc: "ParsedDocument | None" = None,  # ← 추가
) -> list[dict]:
    from app.services.review.engine import (
        ParsedBlock, ParsedDocument, ReviewIssue,
        HANDLER_MAP, issues_to_api_response,
    )
    from app.services.review.doc_type_dispatcher import (
        get_rules_for_doc_type, get_system_prompt,
    )

    # 1) 문서 파싱 — parsed_doc 있으면 bbox 살아있는 blocks 사용
    if parsed_doc is not None:
        doc = parsed_doc
    else:
        doc = ParsedDocument(document_id=document_id)
        for i, line in enumerate(full_text.splitlines(), start=1):
            line = line.strip()
            if line:
                doc.blocks.append(ParsedBlock(i, 1, line, [0, 0, 0, 0]))

    # 2) 룰 엔진
    rules = get_rules_for_doc_type(doc_type)
    rule_issues_raw: list[ReviewIssue] = []
    for rule in rules:
        handler = HANDLER_MAP.get(rule["check_type"])
        if not handler:
            continue
        try:
            issue = handler(rule, doc)
            if issue:
                rule_issues_raw.append(issue)
        except Exception as e:
            print(f"[RuleEngine] 룰 {rule['id']} 오류: {e}")

    rule_issues = issues_to_api_response(rule_issues_raw, review_run_id, document_id)
    for i, iss in enumerate(rule_issues, start=1):
        iss["id"]            = i
        iss["review_run_id"] = review_run_id
        iss["document_id"]   = document_id
        iss["source"]        = "rule"

    # 3) vLLM
    llm_issues: list[dict] = []
    if use_llm:
        system_prompt = get_system_prompt(doc_type)
        already_found = [iss["title"] for iss in rule_issues]
        llm_issues    = await call_vllm(full_text, already_found, system_prompt)
        start_id = len(rule_issues) + 1
        for i, iss in enumerate(llm_issues, start=start_id):
            iss["id"]            = i
            iss["review_run_id"] = review_run_id
            iss["document_id"]   = document_id
            
            # ← 여기 추가: quoted_text → bbox 역추적
            if parsed_doc and iss.get("evidences"):
                quoted = iss["evidences"][0].get("quoted_text", "")
                if quoted:
                    try:
                        from app.services.storage.milvus_store import search_blocks
                        iss["highlights"] = search_blocks(quoted, parsed_doc)
                    except Exception as e:
                        print(f"[vLLM] Milvus 검색 실패: {e}")
                        iss["highlights"] = _find_bbox_for_quoted_text(quoted, parsed_doc)

    # 4) 심각도 순 정렬 + 합산
    sev_order = {"critical": 0, "high": 1, "warning": 2, "info": 3}
    return sorted(
        rule_issues + llm_issues,
        key=lambda x: sev_order.get(x.get("severity", "info"), 9),
    )

def run_hybrid_review_sync(
    full_text: str,
    document_id: int = 0,
    review_run_id: int = 0,
    use_llm: bool = True,
    doc_type: str = "unknown",
    parsed_doc: "ParsedDocument | None" = None,
) -> list[dict]:
    """
    ⚠️  FastAPI(uvloop) 환경에서는 사용 불가.
    CLI / pytest 환경에서만 사용.
    """
    import asyncio
    return asyncio.run(
        run_hybrid_review(full_text, document_id, review_run_id, use_llm, doc_type, parsed_doc)
    )