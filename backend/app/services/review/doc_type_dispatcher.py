"""
문서 타입 자동 감지 + 룰셋 디스패처
────────────────────────────────────────────────────────────
파일명 또는 텍스트 키워드로 문서 타입을 판별하고
해당 룰셋을 반환.

지원 문서 타입:
  bid_notice        입찰공고문
  proposal_request  제안요청서
  plan              계획서
"""

from __future__ import annotations

import re

from app.services.review.rules import RULES as RULES_BID_NOTICE
from app.services.review.rules_proposal_request import RULES_PROPOSAL_REQUEST


# ──────────────────────────────────────────────
# 계획서 룰 (인라인 정의 — 추후 별도 파일로 분리 가능)
# ──────────────────────────────────────────────

RULES_PLAN: list[dict] = [
    {
        "id": "PL001",
        "category": "missing",
        "severity": "high",
        "title": "사업명 누락",
        "description": "계획서에 사업명이 명시되지 않았습니다.",
        "recommendation": "계획서 표제부에 사업명을 명확히 기재하세요.",
        "law_ref": None,
        "check_type": "keyword_missing",
        "params": {"keywords": ["사업명", "용역명", "과업명"]},
    },
    {
        "id": "PL002",
        "category": "missing",
        "severity": "high",
        "title": "사업기간 누락",
        "description": "계획서에 사업기간(착수~완료)이 명시되지 않았습니다.",
        "recommendation": "착수일, 완료일 또는 용역기간(N일)을 명시하세요.",
        "law_ref": "지방계약법 시행령 제50조",
        "check_type": "keyword_missing",
        "params": {"keywords": ["사업기간", "용역기간", "착수", "완료"]},
    },
    {
        "id": "PL003",
        "category": "missing",
        "severity": "high",
        "title": "총사업비 누락",
        "description": "계획서에 총사업비가 명시되지 않았습니다.",
        "recommendation": "총사업비(부가가치세 포함/별도 여부 포함)를 기재하세요.",
        "law_ref": None,
        "check_type": "keyword_missing",
        "params": {"keywords": ["총사업비", "사업비", "예산"]},
    },
    {
        "id": "PL004",
        "category": "missing",
        "severity": "high",
        "title": "발주기관 누락",
        "description": "계획서에 발주기관이 명시되지 않았습니다.",
        "recommendation": "발주기관명을 기재하세요.",
        "law_ref": None,
        "check_type": "keyword_missing",
        "params": {"keywords": ["발주기관", "발주처", "서초구"]},
    },
    {
        "id": "PL005",
        "category": "missing",
        "severity": "warning",
        "title": "담당부서/담당자 누락",
        "description": "계획서에 담당부서 또는 담당자 정보가 없습니다.",
        "recommendation": "담당부서명, 담당자명, 연락처를 기재하세요.",
        "law_ref": None,
        "check_type": "keyword_missing",
        "params": {"keywords": ["담당", "담당자", "담당부서"]},
    },
    {
        "id": "PL006",
        "category": "missing",
        "severity": "warning",
        "title": "추진 배경/목적 누락",
        "description": "계획서에 사업 추진 배경 및 목적이 없습니다.",
        "recommendation": "사업 추진 배경, 목적, 필요성을 기재하세요.",
        "law_ref": None,
        "check_type": "keyword_missing",
        "params": {"keywords": ["추진 배경", "사업 목적", "필요성"]},
    },
    {
        "id": "PL007",
        "category": "approval_rule",
        "severity": "info",
        "title": "고액 사업 결재선 안내",
        "description": "1억원 이상 사업은 국장 이상 결재가 필요합니다.",
        "recommendation": "사무전결규정에 따라 결재선을 확인하세요.",
        "law_ref": "서초구 사무전결규정",
        "check_type": "amount_threshold",
        "params": {
            "amount_keywords": ["총사업비", "사업비", "예산"],
            "threshold": 100_000_000,
            "violation_condition": "gte",
        },
    },
]


# ──────────────────────────────────────────────
# 문서 타입 감지
# ──────────────────────────────────────────────

DOC_TYPE_PATTERNS = {
    "bid_notice": [
        r"입찰\s*공고",
        r"용\s*역\s*입\s*찰",
        r"공고\s*제\d+",
        r"기초금액",
        r"낙찰하한",
    ],
    "proposal_request": [
        r"제\s*안\s*요\s*청\s*서",
        r"요구사항번호",
        r"FCR-\d+",
        r"PER-\d+",
        r"노임단가",
    ],
    "plan": [
        r"계\s*획\s*서",
        r"추진\s*계획",
        r"사업\s*계획",
        r"업무\s*계획",
        r"추진\s*일정",
    ],
}


def detect_doc_type(text: str, filename: str = "") -> str:
    """
    텍스트 또는 파일명으로 문서 타입 감지.
    반환: "bid_notice" | "proposal_request" | "plan" | "unknown"
    """
    # 파일명 우선 판별
    fname = filename.lower()
    if any(kw in fname for kw in ["입찰공고", "공고문", "bid"]):
        return "bid_notice"
    if any(kw in fname for kw in ["제안요청서", "rfp"]):
        return "proposal_request"
    if any(kw in fname for kw in ["제안서", "proposal"]):
        return "proposal"
    if any(kw in fname for kw in ["계획서", "plan"]):
        return "plan"
    if any(kw in fname for kw in ["계약서", "contract"]):
        return "contract"

    # 텍스트 키워드 스코어링
    scores = {doc_type: 0 for doc_type in DOC_TYPE_PATTERNS}
    for doc_type, patterns in DOC_TYPE_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text[:3000]):  # 앞 3000자만 검사 (표지/서두)
                scores[doc_type] += 1

    best = max(scores, key=lambda k: scores[k])
    return best if scores[best] > 0 else "unknown"


def get_rules_for_doc_type(doc_type: str) -> list[dict]:
    """문서 타입에 맞는 룰셋 반환"""
    ruleset_map = {
        "bid_notice":       RULES_BID_NOTICE,
        "proposal_request": RULES_PROPOSAL_REQUEST,
        "proposal":         RULES_PROPOSAL_REQUEST,  # 제안서도 제안요청서 룰로 검토
        "plan":             RULES_PLAN,
        "contract":         RULES_BID_NOTICE,  # 계약서류는 일단 입찰공고문 룰로 검토
        "unknown":          RULES_BID_NOTICE,  # 기본값
    }
    return ruleset_map.get(doc_type, RULES_BID_NOTICE)


# ──────────────────────────────────────────────
# 문서 타입별 vLLM 시스템 프롬프트
# ──────────────────────────────────────────────

SYSTEM_PROMPTS = {
    "bid_notice": """당신은 대한민국 지방자치단체 입찰공고문 전문 검토 AI입니다.
지방계약법, 소프트웨어진흥법 등 관련 법령 기준으로 입찰공고문을 검토합니다.
금액 표기, 단독이행 여부, 낙찰하한율, 입찰보증금 등 필수 항목을 중점 검토하세요.""",

    "proposal_request": """당신은 대한민국 지방자치단체 제안요청서(RFP) 전문 검토 AI입니다.
제안요청서의 기능 요구사항, 성능 기준, 노임단가 기준, 필수 기재사항 누락 여부를 검토합니다.
한국소프트웨어산업협회(KOSA) 공표 노임단가 기준 준수 여부를 특히 확인하세요.""",

    "plan": """당신은 대한민국 지방자치단체 사업 계획서 전문 검토 AI입니다.
사업명, 기간, 예산, 발주기관, 담당자 등 필수 항목과
사무전결규정에 따른 결재선 적정성을 검토합니다.""",

    "unknown": """당신은 대한민국 지방자치단체 계약서류 전문 검토 AI입니다.
법령·지침·내부규정 준수 여부와 필수 항목 누락 여부를 검토합니다.""",
}


def get_system_prompt(doc_type: str) -> str:
    base = """
반드시 아래 JSON 형식만 반환하세요. 다른 텍스트는 절대 포함하지 마세요:
[
  {
    "rule_id": "L001",
    "severity": "critical|high|warning|info",
    "category": "missing|regulation_violation|inconsistency|typo|approval_rule",
    "title": "이슈 제목 (20자 이내)",
    "description": "구체적인 문제 설명",
    "recommendation": "수정 권고사항",
    "law_ref": "근거 법령 또는 null",
    "quoted_text": "문제가 된 원문 텍스트 (없으면 null)"
  }
]
이슈가 없으면 빈 배열 [] 을 반환하세요."""

    return SYSTEM_PROMPTS.get(doc_type, SYSTEM_PROMPTS["unknown"]) + base