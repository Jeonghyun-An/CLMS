"""
계약서류 검토 룰 엔진 (PoC)
────────────────────────────────────────────────────────────
입력:  ParsedDocument (텍스트 + 페이지별 블록 목록)
출력:  List[ReviewIssue]  (이슈 카드 1개 = 딕셔너리)

OCR 후배가 넘겨주는 포맷 기준:
  {
    "document_id": int,
    "pages": [
      {
        "page_no": int,
        "blocks": [
          { "block_id": int, "text": str, "bbox": [x1,y1,x2,y2] }
        ]
      }
    ]
  }
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from app.services.review.rules import RULES


# ──────────────────────────────────────────────
# 데이터 구조
# ──────────────────────────────────────────────

@dataclass
class ParsedBlock:
    block_id: int
    page_no: int
    text: str
    bbox: list[float]  # [x1, y1, x2, y2]


@dataclass
class ParsedDocument:
    document_id: int
    blocks: list[ParsedBlock] = field(default_factory=list)

    @property
    def full_text(self) -> str:
        return "\n".join(b.text for b in self.blocks)

    @classmethod
    def from_ocr_json(cls, ocr_data: dict) -> "ParsedDocument":
        """OCR 후배가 넘겨주는 JSON → ParsedDocument 변환"""
        doc = cls(document_id=ocr_data["document_id"])
        for page in ocr_data.get("pages", []):
            page_no = page["page_no"]
            for block in page.get("blocks", []):
                doc.blocks.append(
                    ParsedBlock(
                        block_id=block["block_id"],
                        page_no=page_no,
                        text=block["text"],
                        bbox=block.get("bbox", [0, 0, 0, 0]),
                    )
                )
        return doc


@dataclass
class ReviewIssue:
    rule_id: str
    category: str           # IssueCategory
    severity: str           # SeverityLevel
    title: str
    description: str
    recommendation: str
    law_ref: str | None
    # 근거 위치
    evidence_blocks: list[dict] = field(default_factory=list)
    # 하이라이트용 (page_no, bbox)
    highlights: list[dict] = field(default_factory=list)


# ──────────────────────────────────────────────
# 헬퍼
# ──────────────────────────────────────────────

def _find_blocks_with_keywords(
    blocks: list[ParsedBlock], keywords: list[str]
) -> list[ParsedBlock]:
    """키워드 중 하나라도 포함하는 블록 목록 반환"""
    result = []
    for block in blocks:
        if any(kw in block.text for kw in keywords):
            result.append(block)
    return result


def _extract_amount(text: str) -> int | None:
    """
    텍스트에서 금액(정수) 추출.
    - '1,550,000,000원' → 1550000000
    - '15억5천만원' 같은 한글 단위는 미지원 (PoC 범위 외)
    """
    # 쉼표 포함 숫자 + 원
    m = re.search(r"([\d,]+)\s*원", text)
    if m:
        try:
            return int(m.group(1).replace(",", ""))
        except ValueError:
            pass
    return None


# ──────────────────────────────────────────────
# 체크 타입별 핸들러
# ──────────────────────────────────────────────

def _check_keyword_missing(
    rule: dict, doc: ParsedDocument
) -> ReviewIssue | None:
    keywords: list[str] = rule["params"]["keywords"]
    matched = _find_blocks_with_keywords(doc.blocks, keywords)
    if matched:
        return None  # 키워드 존재 → 문제 없음

    # 키워드가 하나도 없으면 이슈
    return ReviewIssue(
        rule_id=rule["id"],
        category=rule["category"],
        severity=rule["severity"],
        title=rule["title"],
        description=rule["description"],
        recommendation=rule["recommendation"],
        law_ref=rule["law_ref"],
        evidence_blocks=[],
        highlights=[],
    )


def _check_regex_match(
    rule: dict, doc: ParsedDocument
) -> ReviewIssue | None:
    pattern: str = rule["params"]["pattern"]
    condition: str = rule["params"]["violation_condition"]

    matched_blocks: list[ParsedBlock] = []
    for block in doc.blocks:
        m = re.search(pattern, block.text)
        if m:
            matched_blocks.append(block)

            # 숫자 비교 조건
            if condition == "value_lt" and m.lastindex:
                try:
                    val = int(m.group(rule["params"]["capture_group"]))
                    if val >= rule["params"]["threshold"]:
                        matched_blocks.pop()  # 기준 이상이면 정상
                except (ValueError, IndexError):
                    pass

    is_violation = bool(matched_blocks) if condition in ("found", "value_lt") else False
    if not is_violation:
        return None

    highlights = [
        {"page_no": b.page_no, "bbox": b.bbox, "block_id": b.block_id}
        for b in matched_blocks
    ]
    evidences = [
        {"block_id": b.block_id, "page_no": b.page_no, "quoted_text": b.text[:120]}
        for b in matched_blocks
    ]
    return ReviewIssue(
        rule_id=rule["id"],
        category=rule["category"],
        severity=rule["severity"],
        title=rule["title"],
        description=rule["description"],
        recommendation=rule["recommendation"],
        law_ref=rule["law_ref"],
        evidence_blocks=evidences,
        highlights=highlights,
    )


def _check_amount_threshold(
    rule: dict, doc: ParsedDocument
) -> ReviewIssue | None:
    amount_keywords: list[str] = rule["params"]["amount_keywords"]
    threshold: int = rule["params"]["threshold"]
    condition: str = rule["params"]["violation_condition"]

    matched = _find_blocks_with_keywords(doc.blocks, amount_keywords)
    for block in matched:
        amount = _extract_amount(block.text)
        if amount is None:
            continue
        triggered = (condition == "gte" and amount >= threshold) or \
                    (condition == "lt" and amount < threshold)
        if triggered:
            return ReviewIssue(
                rule_id=rule["id"],
                category=rule["category"],
                severity=rule["severity"],
                title=rule["title"],
                description=f"{rule['description']} (감지 금액: {amount:,}원)",
                recommendation=rule["recommendation"],
                law_ref=rule["law_ref"],
                evidence_blocks=[
                    {"block_id": block.block_id, "page_no": block.page_no,
                     "quoted_text": block.text[:120]}
                ],
                highlights=[
                    {"page_no": block.page_no, "bbox": block.bbox,
                     "block_id": block.block_id}
                ],
            )
    return None


# ──────────────────────────────────────────────
# 메인 엔진
# ──────────────────────────────────────────────

HANDLER_MAP = {
    "keyword_missing": _check_keyword_missing,
    "regex_match": _check_regex_match,
    "amount_threshold": _check_amount_threshold,
}


def run_review(doc: ParsedDocument) -> list[ReviewIssue]:
    """
    단일 문서에 대해 전체 룰을 실행하고 이슈 목록 반환.
    """
    issues: list[ReviewIssue] = []
    for rule in RULES:
        handler = HANDLER_MAP.get(rule["check_type"])
        if handler is None:
            continue
        try:
            issue = handler(rule, doc)
            if issue:
                issues.append(issue)
        except Exception as e:
            # 개별 룰 오류가 전체를 막지 않도록
            print(f"[RuleEngine] 룰 {rule['id']} 오류: {e}")
    return issues


def run_review_from_ocr(ocr_data: dict) -> list[ReviewIssue]:
    """OCR JSON을 바로 받아서 검토 실행 (편의 함수)"""
    doc = ParsedDocument.from_ocr_json(ocr_data)
    return run_review(doc)


# ──────────────────────────────────────────────
# 결과 직렬화 (API 응답용)
# ──────────────────────────────────────────────

def issues_to_api_response(
    issues: list[ReviewIssue],
    review_run_id: int = 0,
    document_id: int = 0,
) -> list[dict]:
    """ReviewIssue 리스트 → FastAPI 응답 딕셔너리 리스트"""
    from datetime import datetime

    result = []
    for i, issue in enumerate(issues, start=1):
        result.append({
            "id": i,
            "review_run_id": review_run_id,
            "document_id": document_id,
            "rule_id": issue.rule_id,
            "severity": issue.severity,
            "category": issue.category,
            "title": issue.title,
            "description": issue.description,
            "recommendation": issue.recommendation,
            "regulation_refs": [
                {
                    "regulation_title": issue.law_ref,
                    "article_no": issue.rule_id,
                    "quoted_text": issue.law_ref,
                }
            ] if issue.law_ref else [],
            "evidences": issue.evidence_blocks,
            "highlights": issue.highlights,
            "status": "open",
            "created_at": datetime.now().isoformat(),
        })
    return result


def _check_order_check(rule: dict, doc: ParsedDocument) -> ReviewIssue | None:
    """문서 내 두 키워드의 등장 순서가 잘못된 경우 이슈 반환"""
    full = "\n".join(b.text for b in doc.blocks)
    first_kw  = rule["params"]["first_keyword"]
    second_kw = rule["params"]["second_keyword"]
    pos1 = full.find(first_kw)
    pos2 = full.find(second_kw)
    if pos1 == -1 or pos2 == -1:
        return None
    if pos1 >= pos2:
        return None  # 순서 정상

    evidence = [
        {"block_id": b.block_id, "page_no": b.page_no, "quoted_text": b.text[:80]}
        for b in doc.blocks
        if first_kw in b.text or second_kw in b.text
    ]
    return ReviewIssue(
        rule_id=rule["id"], category=rule["category"], severity=rule["severity"],
        title=rule["title"], description=rule["description"],
        recommendation=rule["recommendation"], law_ref=rule["law_ref"],
        evidence_blocks=evidence[:2],
        highlights=[{"page_no": e["page_no"], "bbox": [0,0,0,0], "block_id": e["block_id"]} for e in evidence[:1]],
    )


def _check_amount_mismatch(rule: dict, doc: ParsedDocument) -> ReviewIssue | None:
    """두 패턴이 동시에 존재할 때 금액 불일치 이슈 반환"""
    full = "\n".join(b.text for b in doc.blocks)
    p1   = rule["params"]["pattern_text_amount"]
    p2   = rule["params"]["pattern_table_amount"]
    cond = rule["params"]["violation_condition"]

    found1 = bool(re.search(p1, full))
    found2 = bool(re.search(p2, full))

    if cond == "both_found" and not (found1 and found2):
        return None

    evidence = [
        {"block_id": b.block_id, "page_no": b.page_no, "quoted_text": b.text[:80]}
        for b in doc.blocks
        if re.search(p1, b.text) or re.search(p2, b.text)
    ]
    return ReviewIssue(
        rule_id=rule["id"], category=rule["category"], severity=rule["severity"],
        title=rule["title"], description=rule["description"],
        recommendation=rule["recommendation"], law_ref=rule["law_ref"],
        evidence_blocks=evidence[:3],
        highlights=[{"page_no": e["page_no"], "bbox": [0,0,0,0], "block_id": e["block_id"]} for e in evidence[:2]],
    )


# 핸들러 맵에 등록
HANDLER_MAP["order_check"]     = _check_order_check
HANDLER_MAP["amount_mismatch"] = _check_amount_mismatch