"""
제안요청서 검토 룰셋
────────────────────────────────────────────────────────────
실제 문서 기반 (서초구 AI 계약서류 검토시스템 구축 제안요청서)

[정상 문서 기준]
  p.1  표지: 담당자 소속/성명/전화번호/이메일 모두 기재
  p.18 FCR-010: 노임단가 기준 = 한국소프트웨어산업협회 공표
  p.20 PER-001: 검토 3분 이내, 탐지율 90% 이상
  p.20 PER-002: 동시접속 50명 이상

[비정상 문서 - 오류 유형]
  1. 노임단가 기준 오기재 (한국SW산업협회 → 다른 기관명)
  2. 담당자 전화번호 누락
  3. 담당자 이메일 누락
"""

from __future__ import annotations

RULES_PROPOSAL_REQUEST: list[dict] = [

    # ───────────────────────────────────────────
    # 1. 표지 필수항목 누락
    # ───────────────────────────────────────────
    {
        "id": "PR001",
        "category": "missing",
        "severity": "high",
        "title": "담당자 전화번호 누락",
        "description": "제안요청서 표지에 담당자 전화번호가 기재되지 않았습니다.",
        "recommendation": "표지의 '전화번호' 항목에 담당자 연락처를 기재하세요. (예: 02-2155-6431)",
        "law_ref": "행정기관 공문서 작성 기준",
        "check_type": "keyword_missing",
        "params": {
            "keywords": ["전화번호", "☎", "Tel", "02-"],
        },
    },
    {
        "id": "PR002",
        "category": "missing",
        "severity": "high",
        "title": "담당자 이메일 누락",
        "description": "제안요청서 표지에 담당자 이메일이 기재되지 않았습니다.",
        "recommendation": "표지의 'e-mail' 항목에 담당자 이메일을 기재하세요. (예: whpark@seocho.go.kr)",
        "law_ref": "행정기관 공문서 작성 기준",
        "check_type": "keyword_missing",
        "params": {
            "keywords": ["e-mail", "E-Mail", "이메일", "@seocho.go.kr", "@"],
        },
    },
    {
        "id": "PR003",
        "category": "missing",
        "severity": "warning",
        "title": "담당자 소속 부서 누락",
        "description": "제안요청서 표지에 담당자 소속 부서가 명시되지 않았습니다.",
        "recommendation": "표지의 '소속' 항목에 담당 부서명을 기재하세요. (예: 스마트도시과)",
        "law_ref": None,
        "check_type": "keyword_missing",
        "params": {
            "keywords": ["스마트도시과", "소속", "담당부서"],
        },
    },
    {
        "id": "PR004",
        "category": "missing",
        "severity": "warning",
        "title": "문의처 정보 누락",
        "description": "제안요청서 본문의 제안관련 문의처 정보가 누락되었습니다.",
        "recommendation": "제안관련 문의처(사업부서, 전화번호, 이메일)를 본문에 기재하세요.",
        "law_ref": None,
        "check_type": "keyword_missing",
        "params": {
            "keywords": ["문의처", "문의사항", "담당자"],
        },
    },

    # ───────────────────────────────────────────
    # 2. 노임단가 기준 오기재
    # ───────────────────────────────────────────
    {
        "id": "PR010",
        "category": "regulation_violation",
        "severity": "critical",
        "title": "노임단가 기준 기관 오기재",
        "description": "노임단가 기준이 '한국소프트웨어산업협회' 공표 기준이 아닌 다른 기관으로 잘못 기재되었습니다.",
        "recommendation": "노임단가 기준을 '한국소프트웨어산업협회(KOSA) 공표 SW기술자 노임단가'로 수정하세요.",
        "law_ref": "소프트웨어진흥법 제48조 및 SW기술자 노임단가 고시",
        "check_type": "keyword_missing",
        "params": {
            "keywords": ["한국소프트웨어산업협회", "KOSA", "SW기술자 노임단가"],
        },
    },
    {
        "id": "PR011",
        "category": "typo",
        "severity": "high",
        "title": "노임단가 기준 연도 오기재 의심",
        "description": "노임단가 기준 연도가 최신 공표 연도와 다를 수 있습니다.",
        "recommendation": "입찰 공고일 기준 최신 노임단가(한국소프트웨어산업협회 공표)를 적용하세요.",
        "law_ref": "소프트웨어진흥법 제48조",
        "check_type": "regex_match",
        "params": {
            # 2024 이전 연도 노임단가 기재 시 경고
            "pattern": r"노임단가.{0,20}(2023|2022|2021|2020)",
            "violation_condition": "found",
        },
    },

    # ───────────────────────────────────────────
    # 3. 성능 요구사항 누락/오기재
    # ───────────────────────────────────────────
    {
        "id": "PR020",
        "category": "missing",
        "severity": "high",
        "title": "검토 성능 기준(3분) 누락",
        "description": "단일 계약서류 검토 결과 생성 3분 이내 성능 기준이 명시되지 않았습니다.",
        "recommendation": "PER-001 성능 요구사항에 '단일 계약 서류의 검토 결과 생성 3분 이내' 기준을 기재하세요.",
        "law_ref": None,
        "check_type": "keyword_missing",
        "params": {
            "keywords": ["3분", "3분 이내", "검토 결과 생성"],
        },
    },
    {
        "id": "PR021",
        "category": "missing",
        "severity": "high",
        "title": "오류 탐지율(90%) 기준 누락",
        "description": "주요 오류 탐지율 90% 이상 기준이 명시되지 않았습니다.",
        "recommendation": "PER-001에 '필수 서류 누락, 잘못된 수치 등 주요 오류 탐지율 90% 이상' 기준을 기재하세요.",
        "law_ref": None,
        "check_type": "keyword_missing",
        "params": {
            "keywords": ["탐지율", "90%", "90 %"],
        },
    },
    {
        "id": "PR022",
        "category": "missing",
        "severity": "warning",
        "title": "동시접속 사용자 기준(50명) 누락",
        "description": "동시접속 사용자 최소 50명 이상 수용 성능 기준이 없습니다.",
        "recommendation": "PER-002에 '동시접속 사용자 최소 50명 이상 지원' 기준을 명시하세요.",
        "law_ref": None,
        "check_type": "keyword_missing",
        "params": {
            "keywords": ["50명", "동시접속", "동시 이용"],
        },
    },

    # ───────────────────────────────────────────
    # 4. 핵심 기능 요구사항 누락
    # ───────────────────────────────────────────
    {
        "id": "PR030",
        "category": "missing",
        "severity": "high",
        "title": "다중 포맷 처리 요구사항 누락",
        "description": "hwp, hwpx, xlsx, pdf 등 다중 포맷 처리 요구사항이 없습니다.",
        "recommendation": "FCR-002에 hwp, hwpx, xlsx, pdf 등 지원 포맷과 처리 방식을 명시하세요.",
        "law_ref": None,
        "check_type": "keyword_missing",
        "params": {
            "keywords": ["hwpx", "xlsx", "다중 포맷", "다중포맷"],
        },
    },
    {
        "id": "PR031",
        "category": "missing",
        "severity": "warning",
        "title": "결재선 적정성 판단 기능 누락",
        "description": "사무전결규정에 따른 결재선 적합성 자동 판단 기능 요구사항이 없습니다.",
        "recommendation": "FCR-012 결재선 적정성 판단 기능을 기재하세요.",
        "law_ref": "서초구 사무전결규정",
        "check_type": "keyword_missing",
        "params": {
            "keywords": ["결재선", "전결", "사무전결"],
        },
    },
    {
        "id": "PR032",
        "category": "missing",
        "severity": "warning",
        "title": "RAG 기반 법령 검토 기능 누락",
        "description": "법령·지침·내부규정 RAG 기반 검토 기능 요구사항이 없습니다.",
        "recommendation": "개인별/부서별 커스텀 RAG 시스템 구현 요구사항(FCR-009)을 기재하세요.",
        "law_ref": None,
        "check_type": "keyword_missing",
        "params": {
            "keywords": ["RAG", "법령", "지침"],
        },
    },

    # ───────────────────────────────────────────
    # 5. 사업 기본 정보 누락
    # ───────────────────────────────────────────
    {
        "id": "PR040",
        "category": "missing",
        "severity": "high",
        "title": "사업명 누락",
        "description": "제안요청서에 사업명이 명시되지 않았습니다.",
        "recommendation": "표지 및 본문에 사업명을 기재하세요.",
        "law_ref": None,
        "check_type": "keyword_missing",
        "params": {
            "keywords": ["사업명", "사업 명", "AI 계약서류"],
        },
    },
    {
        "id": "PR041",
        "category": "missing",
        "severity": "high",
        "title": "주관기관 누락",
        "description": "제안요청서에 주관기관이 명시되지 않았습니다.",
        "recommendation": "표지에 주관기관(서초구청 등)을 기재하세요.",
        "law_ref": None,
        "check_type": "keyword_missing",
        "params": {
            "keywords": ["주관기관", "서초구", "발주기관"],
        },
    },
]