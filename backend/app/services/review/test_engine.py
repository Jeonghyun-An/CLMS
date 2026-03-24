"""
룰 엔진 단독 실행 테스트
────────────────────────────────────────────────────────────
실행:  python -m app.services.review.test_engine
       (backend/ 디렉토리에서)
"""

import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../.."))

from app.services.review.engine import (
    ParsedBlock,
    ParsedDocument,
    run_review,
    issues_to_api_response,
)

# ──────────────────────────────────────────────
# 테스트 1: 정상 문서 (이슈 최소)
# ──────────────────────────────────────────────
def test_normal():
    doc = ParsedDocument(document_id=1001, blocks=[
        ParsedBlock(1, 1, "서초구 공고 제2026-24호", [50,30,300,55]),
        ParsedBlock(2, 1, "AI 계약서류 검토시스템 용역", [100,60,420,95]),
        ParsedBlock(3, 1, "용역기간 : 착수일로부터 180일", [50,100,400,125]),
        ParsedBlock(4, 1, "기초금액 : 금1,550,000,000원 부가가치세 별도", [50,130,550,155]),
        ParsedBlock(5, 1, "발주기관 : 서초구청 스마트도시과", [50,160,400,185]),
        ParsedBlock(6, 1, "담당 : 박우현 ☎02-2155-6431", [50,190,350,215]),
        ParsedBlock(7, 1, "입찰 마감 : 2026. 3. 27.(금) 16:00", [50,220,400,245]),
        ParsedBlock(8, 2, "단독이행만 가능합니다(공동도급 허용하지 않음)", [50,50,500,75]),
        ParsedBlock(9, 2, "입찰보증금은 면제됨", [50,80,400,105]),
        ParsedBlock(10, 2, "낙찰하한율 80 기준 적용", [50,110,400,135]),
        ParsedBlock(11, 2, "지방계약법 시행령 제13조에 의거", [50,140,450,165]),
        ParsedBlock(12, 2, "사업명 : AI 계약서류 검토시스템 구축", [50,170,450,195]),
    ])
    return run_review(doc)


# ──────────────────────────────────────────────
# 테스트 2: 비정상 문서 (다수 이슈)
# ──────────────────────────────────────────────
def test_abnormal():
    doc = ParsedDocument(document_id=1002, blocks=[
        ParsedBlock(1, 1, "서초구 공고", [50,30,200,55]),
        # 사업명/용역기간/발주기관/담당자/마감일 없음
        ParsedBlock(2, 1, "총 사업비 : 15억5000만원", [50,80,350,105]),   # 단위 혼용
        ParsedBlock(3, 1, "계약보증금 5/100", [50,110,300,135]),          # 5% 위반
        ParsedBlock(4, 1, "제출기한 : 2026-03-27 16:00", [50,140,400,165]), # 날짜 형식
        # 단독이행/입찰보증금/낙찰하한/부가세 없음
    ])
    return run_review(doc)


# ──────────────────────────────────────────────
# OCR JSON 포맷 테스트
# ──────────────────────────────────────────────
def test_ocr_json():
    from app.services.review.engine import run_review_from_ocr
    ocr_data = {
        "document_id": 1003,
        "pages": [
            {
                "page_no": 1,
                "blocks": [
                    {"block_id": 1, "text": "서초구 입찰공고", "bbox": [50,30,300,55]},
                    {"block_id": 2, "text": "사업명 : AI 계약검토 시스템 구축", "bbox": [50,60,400,85]},
                    {"block_id": 3, "text": "용역기간 : 착수 후 180일", "bbox": [50,90,350,115]},
                    {"block_id": 4, "text": "기초금액 : 1,550,000,000원 부가가치세 포함", "bbox": [50,120,500,145]},
                    {"block_id": 5, "text": "발주기관 : 서초구청", "bbox": [50,150,300,175]},
                    {"block_id": 6, "text": "담당 ☎ 02-2155-6431", "bbox": [50,180,300,205]},
                    {"block_id": 7, "text": "마감 : 2026. 3. 27. 16:00", "bbox": [50,210,350,235]},
                    {"block_id": 8, "text": "단독이행 가능, 공동도급 불허", "bbox": [50,240,400,265]},
                    {"block_id": 9, "text": "입찰보증금 면제", "bbox": [50,270,300,295]},
                    {"block_id": 10, "text": "낙찰하한 80% 적용", "bbox": [50,300,300,325]},
                    {"block_id": 11, "text": "지방계약법 제12조 준수", "bbox": [50,330,400,355]},
                ]
            }
        ]
    }
    return run_review_from_ocr(ocr_data)


# ──────────────────────────────────────────────
# 메인
# ──────────────────────────────────────────────
def print_issues(label: str, issues):
    print(f"\n{'='*60}")
    print(f"  {label}  →  총 {len(issues)}건 이슈")
    print(f"{'='*60}")
    serialized = issues_to_api_response(issues)
    for iss in serialized:
        sev_icon = {"critical": "🔴", "high": "🟠", "warning": "🟡", "info": "🔵"}.get(iss["severity"], "⚪")
        print(f"\n  {sev_icon} [{iss['rule_id']}] {iss['title']}")
        print(f"     카테고리  : {iss['category']}")
        print(f"     설명      : {iss['description']}")
        print(f"     권고사항  : {iss['recommendation']}")
        if iss["regulation_refs"]:
            print(f"     근거법령  : {iss['regulation_refs'][0]['regulation_title']}")
        if iss["highlights"]:
            print(f"     하이라이트: {len(iss['highlights'])}건")


if __name__ == "__main__":
    print_issues("정상 문서 (입찰공고문 정상버전)", test_normal())
    print_issues("비정상 문서 (입찰공고문 비정상버전)", test_abnormal())
    print_issues("OCR JSON 포맷 입력 테스트", test_ocr_json())

    print("\n\n[전체 JSON 출력 예시 — 비정상 문서]")
    print(json.dumps(
        issues_to_api_response(test_abnormal(), review_run_id=1, document_id=1002),
        ensure_ascii=False, indent=2
    ))