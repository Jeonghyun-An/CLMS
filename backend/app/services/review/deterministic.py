"""
확정적 규칙 검사 엔진

수치 기반 조항(보증금 비율, 지체상금률 등)은 LLM 없이 이 엔진에서 처리.
정확도 100% 보장, 감사 추적 가능.

PoC: 문서 텍스트에서 정규식으로 수치 추출
실제: 파싱된 구조화 데이터(HWP 테이블, Excel 셀)에서 직접 추출
"""

import re
import uuid
from typing import Optional

from app.schemas.review import ReviewIssue, LegalCitation, IssueType, IssueSeverity
from app.data.knowledge_base import ARTICLE_MAP


def _make_issue(
    rule_id: str,
    issue_type: IssueType,
    severity: IssueSeverity,
    title: str,
    description: str,
    article_id: str,
    location: Optional[str] = None,
    detected: Optional[str] = None,
    expected: Optional[str] = None,
) -> ReviewIssue:
    art = ARTICLE_MAP.get(article_id)
    citations = []
    if art:
        citations = [LegalCitation(
            article_id=article_id,
            source=art["source"],
            article=art["article"],
            title=art["title"],
            relevant_excerpt=art["content"][:120] + "…",
        )]
    return ReviewIssue(
        issue_id=f"iss_{uuid.uuid4().hex[:8]}",
        rule_id=rule_id,
        issue_type=issue_type,
        severity=severity,
        title=title,
        description=description,
        location=location,
        detected_value=detected,
        expected_value=expected,
        citations=citations,
        rag_confidence=1.0,
        retrieval_source="deterministic",
    )


def check_deposit_ratio(text: str) -> list[ReviewIssue]:
    """계약보증금 비율 검사 (기준: 10% 이상)"""
    patterns = [
        r"계약보증금[^0-9]*([0-9]+(?:\.[0-9]+)?)\s*%",
        r"보증금[^0-9]*([0-9]+(?:\.[0-9]+)?)\s*%",
        r"보증금[^0-9]*100\s*분의\s*([0-9]+)",
    ]
    for pat in patterns:
        m = re.search(pat, text)
        if m:
            val = float(m.group(1))
            if val < 10:
                return [_make_issue(
                    rule_id="rule_deposit_ratio",
                    issue_type=IssueType.numeric_violation,
                    severity=IssueSeverity.error,
                    title="계약보증금 비율 부족",
                    description=f"계약보증금이 {val}%로 법정 기준 10% 미만입니다.",
                    article_id="lca_30_1",
                    location="계약보증금 조항",
                    detected=f"{val}%",
                    expected="10% 이상",
                )]
    return []


def check_penalty_rate(text: str, contract_type: str = "공사") -> list[ReviewIssue]:
    """지체상금률 검사 (공사 0.1% / 물품 0.15% / 용역 0.125%)"""
    standards = {"공사": 0.1, "물품": 0.15, "용역": 0.125}
    standard = standards.get(contract_type, 0.1)

    patterns = [
        r"지체상금[^0-9]*([0-9]+(?:\.[0-9]+)?)\s*%",
        r"지체상금률[^0-9]*1000\s*분의\s*([0-9]+(?:\.[0-9]+)?)",
    ]
    for pat in patterns:
        m = re.search(pat, text)
        if m:
            raw = float(m.group(1))
            val = raw / 10 if "1000" in pat else raw
            if val < standard:
                return [_make_issue(
                    rule_id="rule_penalty_rate",
                    issue_type=IssueType.numeric_violation,
                    severity=IssueSeverity.error,
                    title="지체상금률 기준 미달",
                    description=f"{contract_type} 계약의 지체상금률이 {val}%로 법정 기준 {standard}% 미만입니다.",
                    article_id="lca_66_1",
                    location="지체상금 조항",
                    detected=f"{val}%",
                    expected=f"{standard}% 이상",
                )]
    return []


def check_warranty_ratio(text: str) -> list[ReviewIssue]:
    """하자보수보증금 비율 검사 (기준: 2~5%)"""
    patterns = [
        r"하자보수보증금[^0-9]*([0-9]+(?:\.[0-9]+)?)\s*%",
        r"하자보[^0-9]*([0-9]+(?:\.[0-9]+)?)\s*%",
    ]
    for pat in patterns:
        m = re.search(pat, text)
        if m:
            val = float(m.group(1))
            if val < 2:
                return [_make_issue(
                    rule_id="rule_warranty_ratio",
                    issue_type=IssueType.numeric_violation,
                    severity=IssueSeverity.error,
                    title="하자보수보증금 비율 부족",
                    description=f"하자보수보증금이 {val}%로 최소 기준 2% 미만입니다.",
                    article_id="lca_62",
                    detected=f"{val}%", expected="2~5%",
                )]
            elif val > 5:
                return [_make_issue(
                    rule_id="rule_warranty_ratio",
                    issue_type=IssueType.numeric_violation,
                    severity=IssueSeverity.warning,
                    title="하자보수보증금 비율 초과",
                    description=f"하자보수보증금이 {val}%로 상한 기준 5%를 초과합니다.",
                    article_id="lca_62",
                    detected=f"{val}%", expected="2~5%",
                )]
    return []


RULE_FUNCTIONS = {
    "check_deposit_ratio": check_deposit_ratio,
    "check_penalty_rate": check_penalty_rate,
    "check_warranty_ratio": check_warranty_ratio,
}


def run_deterministic_checks(text: str, rules: list) -> list[ReviewIssue]:
    """deterministic 규칙 전체 실행"""
    issues: list[ReviewIssue] = []
    for rule in rules:
        if rule["rule_type"] != "deterministic":
            continue
        fn = RULE_FUNCTIONS.get(rule["check_fn"])
        if fn:
            try:
                issues.extend(fn(text))
            except Exception as e:
                print(f"[DeterministicEngine] {rule['id']} failed: {e}")
    return issues
