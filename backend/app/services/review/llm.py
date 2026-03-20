"""
LLM 기반 정성 검사

실제 연동: settings.VLLM_BASE_URL → OpenAI 호환 API
PoC: USE_MOCK_LLM=true 시 하드코딩 응답 반환
"""

import json
import uuid
from typing import Optional

import httpx

from app.core.config import settings
from app.schemas.review import ReviewIssue, LegalCitation, IssueType, IssueSeverity
from app.data.knowledge_base import CheckRule, ARTICLE_MAP
from app.services.review.rag import RetrievedChunk

USE_MOCK = getattr(settings, "USE_MOCK_LLM", True)


# ─── Mock 응답 (PoC용) ───────────────────────────────────────────────────────

MOCK_RESPONSES: dict[str, dict] = {
    "rule_approval_line": {
        "has_issue": True,
        "severity": "warning",
        "title": "결재선 적정성 확인 필요",
        "description": (
            "계약금액이 2억원으로 확인되나 결재선에 담당과장 전결로만 기재되어 있습니다. "
            "서초구 사무전결규정에 따르면 1억원 이상 5억원 미만 공사계약은 국장 전결이 필요합니다."
        ),
        "location": "결재란",
        "detected_value": "담당과장 전결",
        "expected_value": "국장 전결 (1억~5억원 공사)",
        "confidence": 0.85,
    },
    "rule_labor_cost": {
        "has_issue": True,
        "severity": "warning",
        "title": "노임단가 기준 적용 여부 불명확",
        "description": (
            "산출내역서의 노임단가 항목에 근거 기준이 명시되어 있지 않습니다. "
            "고용노동부 고시 기준 적용 여부를 확인하시기 바랍니다."
        ),
        "location": "산출내역서 노임단가 항목",
        "detected_value": None,
        "expected_value": "고용노동부 고시 기준 노임단가 명시",
        "confidence": 0.72,
    },
    "rule_missing_clause": {
        "has_issue": False,
        "severity": "info",
        "title": "",
        "description": "필수 계약 조항이 모두 포함되어 있습니다.",
        "location": None,
        "detected_value": None,
        "expected_value": None,
        "confidence": 0.90,
    },
}


# ─── 프롬프트 빌더 ──────────────────────────────────────────────────────────

def build_prompt(doc_text: str, rule: CheckRule, chunks: list[RetrievedChunk]) -> str:
    context = "\n\n".join(
        f"[{c.source} {c.article}] {c.title}\n{c.content}" for c in chunks
    )
    return f"""당신은 지방자치단체 공공계약 전문 법률 검토 AI입니다.

## 검사 항목
- 규칙명: {rule['name']}
- 설명: {rule['description']}

## 관련 법령/지침
{context}

## 검토 대상 문서 (발췌)
{doc_text[:2000]}

반드시 아래 JSON 형식으로만 응답하세요:
{{
  "has_issue": true 또는 false,
  "severity": "error" 또는 "warning" 또는 "info",
  "title": "이슈 제목",
  "description": "상세 설명 (2~3문장)",
  "location": "문서 내 위치 또는 null",
  "detected_value": "발견된 값 또는 null",
  "expected_value": "기준 값 또는 null",
  "confidence": 0.0~1.0
}}"""


# ─── LLM 호출 ───────────────────────────────────────────────────────────────

async def _call_vllm(prompt: str) -> dict:
    """vLLM OpenAI 호환 API 호출"""
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            f"{settings.VLLM_BASE_URL}/chat/completions",
            json={
                "model": settings.VLLM_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1,
                "max_tokens": 512,
                "response_format": {"type": "json_object"},
            },
        )
        resp.raise_for_status()
        return json.loads(resp.json()["choices"][0]["message"]["content"])


async def run_llm_check(
    doc_text: str,
    rule: CheckRule,
    context_chunks: list[RetrievedChunk],
) -> Optional[ReviewIssue]:
    """LLM 기반 정성 검사 실행"""
    try:
        if USE_MOCK:
            result = MOCK_RESPONSES.get(rule["id"], {
                "has_issue": False, "severity": "info", "title": "",
                "description": "이슈가 발견되지 않았습니다.",
                "location": None, "detected_value": None, "expected_value": None,
                "confidence": 0.7,
            })
        else:
            result = await _call_vllm(build_prompt(doc_text, rule, context_chunks))

        if not result.get("has_issue"):
            return None

        art = ARTICLE_MAP.get(rule["legal_basis"])
        citations = []
        if art:
            citations.append(LegalCitation(
                article_id=rule["legal_basis"],
                source=art["source"], article=art["article"],
                title=art["title"],
                relevant_excerpt=art["content"][:120] + "…",
            ))
        for chunk in context_chunks[:2]:
            if chunk.article_id != rule["legal_basis"]:
                citations.append(LegalCitation(
                    article_id=chunk.article_id, source=chunk.source,
                    article=chunk.article, title=chunk.title,
                    relevant_excerpt=chunk.content[:100] + "…",
                ))

        return ReviewIssue(
            issue_id=f"iss_{uuid.uuid4().hex[:8]}",
            rule_id=rule["id"],
            issue_type=IssueType.compliance_risk,
            severity=IssueSeverity(result.get("severity", "warning")),
            title=result.get("title", rule["name"]),
            description=result.get("description", ""),
            location=result.get("location"),
            detected_value=result.get("detected_value"),
            expected_value=result.get("expected_value"),
            citations=citations,
            rag_confidence=float(result.get("confidence", 0.7)),
            retrieval_source="mock_llm" if USE_MOCK else "vector",
        )

    except Exception as e:
        print(f"[LLMChecker] {rule['id']} failed: {e}")
        return None
