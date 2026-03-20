"""
검토 파이프라인 오케스트레이터

흐름:
1. 텍스트 추출  (PoC: mock / 실제: MinIO → HWP·PDF·Excel 파서)
2. 규칙 매핑
3. Deterministic 검사  (수치: 보증금·지체상금·하자보증)
4. Vector RAG          (Milvus)
5. Graph RAG           (Neo4j)
6. LLM 정성 검사       (vLLM)
7. 요약 생성
8. SSE 이벤트 스트림
"""

import uuid
import asyncio
from datetime import datetime, timezone
from typing import AsyncGenerator

from app.schemas.review import (
    SSEEvent, SSEEventType,
    DocumentReviewResult, ReviewJobResponse,
    ReviewStatus, DocumentCategory, ReviewIssue,
)
from app.data.knowledge_base import get_relevant_rules
from app.services.review.deterministic import run_deterministic_checks
from app.services.review.rag import retrieve_context, retrieve_graph_context
from app.services.review.llm import run_llm_check


# ─── Mock 문서 텍스트 ────────────────────────────────────────────────────────
# 실제: MinIO 다운로드 → 파서(pyhwp / pdfplumber / openpyxl)

MOCK_TEXTS: dict[str, str] = {
    "contract": """
제1조 (목적) 본 계약은 서초구청과 (주)한국건설 간 도로 보수공사 시행에 관한 사항을 정한다.
제2조 (계약금액) 계약금액은 금 이억원(200,000,000원)으로 한다.
제3조 (계약보증금) 계약금액의 100분의 8에 해당하는 금액을 계약보증금으로 납부하여야 한다.
제4조 (지체상금) 지체일수에 지체상금률 1000분의 0.8을 곱하여 산출한 금액을 납부하여야 한다.
제5조 (하자보수보증금) 하자보수보증금은 계약금액의 100분의 3으로 한다.
결재선: 담당과장 전결
""",
    "cost": """
산출내역서
항목: 콘크리트 타설
- 재료비: 5,000,000원 / 노무비: 3,200,000원 (노임단가 기준 미기재) / 경비: 800,000원
항목: 철근 배근
- 재료비: 8,000,000원 / 노무비: 4,500,000원 / 경비: 1,200,000원
""",
    "specification": "제1장 일반사항\n1.1 공사 개요: 서초구 도로 보수 공사\n1.2 적용 기준: 국토부 표준시방서 2023",
    "approval": "본 계약(계약금액 2억원)에 대한 결재권자:\n담당과장 전결 처리",
    "other": "기타 문서입니다.",
}


async def _extract_text(doc_id: str, category: str) -> str:
    """
    문서 텍스트 추출

    실제 구현:
        obj = minio_client.get_object(settings.MINIO_BUCKET, file_key)
        if ext == ".hwp":   return hwp5_to_text(obj)
        if ext == ".pdf":   return pdfplumber.open(obj).pages[0].extract_text()
        if ext == ".xlsx":  return openpyxl_to_text(obj)
    """
    await asyncio.sleep(0.3)
    return MOCK_TEXTS.get(category, MOCK_TEXTS["other"])


def _build_summary(issues: list[ReviewIssue], doc_name: str) -> str:
    errors = sum(1 for i in issues if i.severity.value == "error")
    warnings = sum(1 for i in issues if i.severity.value == "warning")
    if not issues:
        return f"'{doc_name}'에서 법령·지침 위반 사항이 발견되지 않았습니다."
    parts = [f"'{doc_name}' 검토 결과,"]
    if errors:
        parts.append(f"수정 필요 오류 {errors}건")
    if warnings:
        parts.append(f"확인 필요 경고 {warnings}건")
    return " ".join(parts) + "이 발견되었습니다."


# ─── 단일 문서 파이프라인 ────────────────────────────────────────────────────

async def review_document(
    job_id: str,
    doc_id: str,
    doc_name: str,
    category: str,
) -> AsyncGenerator[SSEEvent, None]:
    base = dict(job_id=job_id, doc_id=doc_id, doc_name=doc_name)

    yield SSEEvent(**base, event=SSEEventType.step, step="extracting",
                   message="문서 텍스트 추출 중...", progress=0.10)
    text = await _extract_text(doc_id, category)
    await asyncio.sleep(0.1)

    yield SSEEvent(**base, event=SSEEventType.step, step="rule_mapping",
                   message="검사 규칙 매핑 중...", progress=0.20)
    rules = get_relevant_rules(category)
    det_rules = [r for r in rules if r["rule_type"] == "deterministic"]
    llm_rules  = [r for r in rules if r["rule_type"] == "llm"]

    all_issues: list[ReviewIssue] = []

    # Deterministic
    yield SSEEvent(**base, event=SSEEventType.step, step="rule_check",
                   message=f"수치 규칙 검사 중... ({len(det_rules)}항목)", progress=0.35)
    for issue in run_deterministic_checks(text, det_rules):
        all_issues.append(issue)
        yield SSEEvent(**base, event=SSEEventType.issue_found,
                       message=issue.title, issue=issue, progress=0.40)
    await asyncio.sleep(0.1)

    # Vector RAG
    yield SSEEvent(**base, event=SSEEventType.step, step="rag_search",
                   message="관련 법령 벡터 검색 중...", progress=0.50)
    rag_query = f"{doc_name} {' '.join(r['name'] for r in llm_rules)}"
    vector_chunks = await retrieve_context(rag_query, category=category, top_k=4)
    await asyncio.sleep(0.2)

    # Graph RAG
    yield SSEEvent(**base, event=SSEEventType.step, step="graph_search",
                   message="조항 그래프 탐색 중...", progress=0.62)
    graph_chunks = await retrieve_graph_context(
        [c.article_id for c in vector_chunks[:2]], depth=1
    )
    all_chunks = vector_chunks + graph_chunks
    await asyncio.sleep(0.2)

    # LLM
    yield SSEEvent(**base, event=SSEEventType.step, step="llm_check",
                   message=f"LLM 정성 검사 중... ({len(llm_rules)}항목)", progress=0.75)
    for rule in llm_rules:
        issue = await run_llm_check(text, rule, all_chunks)
        if issue:
            all_issues.append(issue)
            yield SSEEvent(**base, event=SSEEventType.issue_found,
                           message=issue.title, issue=issue, progress=0.82)
        await asyncio.sleep(0.15)

    # 요약
    yield SSEEvent(**base, event=SSEEventType.step, step="summarizing",
                   message="검토 요약 생성 중...", progress=0.92)
    await asyncio.sleep(0.1)

    result = DocumentReviewResult(
        doc_id=doc_id, doc_name=doc_name,
        category=DocumentCategory(category),
        status=ReviewStatus.done,
        issues=all_issues,
        summary=_build_summary(all_issues, doc_name),
        error_count=sum(1 for i in all_issues if i.severity.value == "error"),
        warning_count=sum(1 for i in all_issues if i.severity.value == "warning"),
        info_count=sum(1 for i in all_issues if i.severity.value == "info"),
    )
    yield SSEEvent(**base, event=SSEEventType.doc_done,
                   message=result.summary, result=result, progress=1.0)


# ─── 전체 Job ────────────────────────────────────────────────────────────────

async def run_review_job(
    documents: list[dict],
) -> AsyncGenerator[SSEEvent, None]:
    """
    다수 문서 순차 검토 + SSE 스트림

    향후: asyncio.gather() 로 병렬화 → Celery/ARQ 큐로 오프로드
    """
    job_id = f"job_{uuid.uuid4().hex[:10]}"
    created_at = datetime.now(timezone.utc).isoformat()

    yield SSEEvent(event=SSEEventType.started, job_id=job_id,
                   message=f"검토 시작: {len(documents)}개 문서", progress=0.0)

    results: list[DocumentReviewResult] = []

    for doc in documents:
        async for event in review_document(
            job_id=job_id,
            doc_id=doc["id"],
            doc_name=doc["name"],
            category=doc.get("category", "other"),
        ):
            if event.event == SSEEventType.doc_done and event.result:
                results.append(event.result)
            yield event

    total_errors   = sum(r.error_count for r in results)
    total_warnings = sum(r.warning_count for r in results)

    yield SSEEvent(
        event=SSEEventType.job_done,
        job_id=job_id,
        message=f"전체 검토 완료 — 오류 {total_errors}건, 경고 {total_warnings}건",
        progress=1.0,
        result=DocumentReviewResult(
            doc_id="__job__", doc_name="전체 요약",
            category=DocumentCategory.other,
            status=ReviewStatus.done,
            summary=ReviewJobResponse(
                job_id=job_id, status=ReviewStatus.done,
                document_results=results,
                total_errors=total_errors, total_warnings=total_warnings,
                created_at=created_at,
                completed_at=datetime.now(timezone.utc).isoformat(),
            ).model_dump_json(),
        ),
    )
