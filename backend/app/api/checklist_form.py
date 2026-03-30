"""
체크리스트 API — RFP 예시 기반 계약 유형 체크리스트
────────────────────────────────────────────────────────────
GET  /projects/{project_id}/checklist/form
     체크리스트 폼 정의 (질문 + 선택지) 반환

POST /projects/{project_id}/checklist/save
     사용자 선택값 저장

GET  /projects/{project_id}/checklist/result/{review_run_id}
     AI 판단 계약 유형 + 사용자 선택 비교 결과
"""

from __future__ import annotations

import threading
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.schemas.common import BaseResponse

router = APIRouter()

# ──────────────────────────────────────────────
# 인메모리 저장소 (PoC용)
# { project_id: { "selections": {...}, "saved_at": str } }
# ──────────────────────────────────────────────
_checklist_store: dict[int, dict] = {}
_store_lock = threading.Lock()


# ──────────────────────────────────────────────
# 체크리스트 폼 정의
# ──────────────────────────────────────────────

CHECKLIST_FORM = {
    "title": "체크리스트",
    "description": "목표 달성에 도움이 되도록 맞춤설정 할 수 있습니다.",
    "questions": [
        {
            "id": "q1",
            "text": "1. 계약목적물 분류상 어떤 계약인가요?",
            "type": "single_select",
            "options": [
                {"id": "q1_construction", "label": "공사"},
                {"id": "q1_service",      "label": "용역"},
                {"id": "q1_goods",        "label": "물품"},
            ],
        },
        {
            "id": "q2",
            "text": "2. 구체적으로 어떤 계약인지요?",
            "note": "*용역 및 물품계약의 경우 1천만원 이상 중소기업자간 경쟁제품에 해당된다면 '직접생산확인서' 확인 필요",
            "type": "conditional_select",
            "groups": [
                {
                    "condition": "q1_construction",
                    "label": "공사계약",
                    "type": "multi_select",
                    "options": [
                        {"id": "q2_general",    "label": "종합"},
                        {"id": "q2_expert",     "label": "전문"},
                        {"id": "q2_electric",   "label": "전기"},
                        {"id": "q2_ict",        "label": "정보통신"},
                        {"id": "q2_fire",       "label": "소방"},
                    ],
                },
                {
                    "condition": "q1_service",
                    "label": "용역계약",
                    "type": "multi_select",
                    "options": [
                        {"id": "q2_general_svc",  "label": "일반"},
                        {"id": "q2_tech_svc",     "label": "기술"},
                        {"id": "q2_learning_svc", "label": "학습"},
                    ],
                },
                {
                    "condition": "q1_goods",
                    "label": "물품계약",
                    "type": "multi_select",
                    "options": [
                        {"id": "q2_manufacture", "label": "제조구매"},
                        {"id": "q2_purchase",    "label": "구매"},
                    ],
                },
            ],
        },
        {
            "id": "q3",
            "text": "3. 사업 소요예산에 가능한 계약은?",
            "type": "multi_select_grouped",
            "groups": [
                {
                    "id": "q3_sole1",
                    "label": "1인견적 수의계약이 가능한지",
                    "type": "checkbox_with_children",
                    "children": [
                        {"id": "q3_sole1_2000", "label": "추정가격 2천만원 이하"},
                        {"id": "q3_sole1_5000", "label": "추정가격 5천만원 이하"},
                    ],
                },
                {
                    "id": "q3_sole2",
                    "label": "2인견적 수의계약(전자공개)이 가능한지",
                    "type": "checkbox_with_children",
                    "children": [
                        {"id": "q3_sole2_general4",  "label": "종합공사 4억 이하"},
                        {"id": "q3_sole2_expert2",   "label": "전문공사 2억 이하"},
                        {"id": "q3_sole2_etc",       "label": "전기, 통신 등 기타공사 1억6천 이하"},
                        {"id": "q3_sole2_svc_goods", "label": "용역·물품 1억 이하"},
                    ],
                },
                {
                    "id": "q3_open",
                    "label": "공개경쟁입찰로 진행할 것인지",
                    "type": "checkbox",
                },
            ],
        },
        {
            "id": "q4",
            "text": "4. 경쟁형태를 어떻게 결정할 것인지?",
            "type": "multi_select_grouped",
            "groups": [
                {
                    "id": "q4_sole",
                    "label": "수의계약",
                    "type": "checkbox_with_children",
                    "children": [
                        {"id": "q4_sole_1", "label": "1인견적"},
                        {"id": "q4_sole_2", "label": "2인견적 (전자공개)"},
                    ],
                },
                {
                    "id": "q4_compete",
                    "label": "경쟁계약입찰",
                    "type": "checkbox_with_children",
                    "children": [
                        {"id": "q4_compete_general",    "label": "일반경쟁계약"},
                        {"id": "q4_compete_local",      "label": "지명경쟁계약"},
                        {"id": "q4_compete_restricted", "label": "제한경쟁계약(지역제한, 실적제한 등)"},
                    ],
                },
            ],
        },
    ],
}


# ──────────────────────────────────────────────
# 스키마
# ──────────────────────────────────────────────

class ChecklistSaveRequest(BaseModel):
    review_run_id: int | None = None
    selections: dict[str, Any]   # { "q1": "q1_service", "q2": ["q2_tech_svc"], ... }


class ChecklistWarning(BaseModel):
    code:        str
    message:     str
    detail:      str | None = None


class ChecklistResultResponse(BaseModel):
    project_id:    int
    review_run_id: int | None
    selections:    dict[str, Any]
    warnings:      list[ChecklistWarning]
    ai_detected:   dict[str, Any] | None  # AI가 문서에서 판단한 계약 유형
    saved_at:      str | None


# ──────────────────────────────────────────────
# 엔드포인트
# ──────────────────────────────────────────────

@router.get(
    "/form",
    summary="체크리스트 폼 조회",
    description="계약 유형 체크리스트 질문 및 선택지 반환",
)
async def get_checklist_form(project_id: int):
    return BaseResponse(data=CHECKLIST_FORM)


@router.post(
    "/save",
    summary="체크리스트 저장",
    description="사용자 선택값 저장",
)
async def save_checklist(
    project_id: int,
    body: ChecklistSaveRequest,
):
    if body.review_run_id is not None:
        from app.api.reviews import _get_review_in_project

        review = _get_review_in_project(body.review_run_id, project_id)
        if not review:
            raise HTTPException(status_code=404, detail="해당 프로젝트의 검토 결과가 없습니다.")

    with _store_lock:
        _checklist_store[project_id] = {
            "review_run_id": body.review_run_id,
            "selections":    body.selections,
            "saved_at":      datetime.now().isoformat(),
        }

    return BaseResponse(data={"saved": True, "project_id": project_id})

@router.get(
    "/result",
    response_model=BaseResponse[ChecklistResultResponse],
    summary="체크리스트 결과 조회",
    description="저장된 선택값 + AI 판단 계약 유형 비교 결과 반환",
)
async def get_checklist_result(
    project_id:    int,
    review_run_id: int | None = None,
):
    store = _checklist_store.get(project_id, {})
    selections = store.get("selections", {})

    # AI 판단 계약 유형 (review_store에서 가져오기)
    ai_detected = None
    target_review_run_id = review_run_id or store.get("review_run_id")

    if target_review_run_id:
        from app.api.reviews import _get_review_in_project

        review = _get_review_in_project(target_review_run_id, project_id)
        if not review:
            raise HTTPException(status_code=404, detail="해당 프로젝트의 검토 결과가 없습니다.")

        files = review.get("files", [])
        doc_type = files[0].get("doc_type", "unknown") if files else review.get("doc_type", "unknown")

        ai_detected = _detect_contract_type_from_issues(
            review.get("issues", []),
            doc_type,
        )

    # 경고 생성 (사용자 선택 vs AI 판단 비교)
    warnings = _generate_warnings(selections, ai_detected)

    return BaseResponse(
        data=ChecklistResultResponse(
            project_id=project_id,
            review_run_id=target_review_run_id,
            selections=selections,
            warnings=warnings,
            ai_detected=ai_detected,
            saved_at=store.get("saved_at"),
        )
    )


# ──────────────────────────────────────────────
# 헬퍼 — AI 계약 유형 판단
# ──────────────────────────────────────────────

def _detect_contract_type_from_issues(
    issues: list[dict],
    doc_type: str,
) -> dict:
    """
    검토 이슈 + 문서 타입으로 계약 유형 추정.
    실제로는 LLM이 판단하지만 PoC에서는 키워드 기반.
    """
    # 전체 텍스트에서 계약 유형 키워드 찾기
    all_text = " ".join(
        iss.get("description", "") + " " + iss.get("title", "")
        for iss in issues
    )

    contract_type = "unknown"
    if "용역" in all_text or doc_type in ("proposal_request", "bid_notice"):
        contract_type = "service"
    elif "공사" in all_text:
        contract_type = "construction"
    elif "물품" in all_text:
        contract_type = "goods"

    # 금액 추정
    amount_hint = None
    for iss in issues:
        desc = iss.get("description", "")
        if "1,550,000,000" in desc or "15억" in desc:
            amount_hint = 1_550_000_000
        elif "110,000,000" in desc or "1억1천" in desc:
            amount_hint = 110_000_000

    return {
        "contract_type": contract_type,
        "contract_type_label": {
            "service":      "용역",
            "construction": "공사",
            "goods":        "물품",
            "unknown":      "미확인",
        }.get(contract_type, "미확인"),
        "estimated_amount": amount_hint,
        "competition_type": "open" if (amount_hint or 0) >= 100_000_000 else "sole",
    }


def _generate_warnings(
    selections: dict,
    ai_detected: dict | None,
) -> list[ChecklistWarning]:
    """사용자 선택값과 AI 판단 비교 → 경고 생성"""
    warnings = []
    if not ai_detected or not selections:
        return warnings

    # 계약 유형 불일치
    q1 = selections.get("q1", "")
    ai_type = ai_detected.get("contract_type", "unknown")
    type_map = {"q1_service": "service", "q1_construction": "construction", "q1_goods": "goods"}

    if q1 and type_map.get(q1) != ai_type and ai_type != "unknown":
        label = ai_detected.get("contract_type_label", "")
        warnings.append(ChecklistWarning(
            code="CONTRACT_TYPE_MISMATCH",
            message="항목 미충족",
            detail=f"용역 계약이 아닌 {label} 계약으로 판단됨",
        ))

    # 금액 기준 불일치
    amount = ai_detected.get("estimated_amount")
    if amount and amount >= 100_000_000:
        q3_open = selections.get("q3_open", False)
        if not q3_open:
            warnings.append(ChecklistWarning(
                code="COMPETITION_TYPE_REQUIRED",
                message="공개경쟁입찰 필요",
                detail=f"추정금액 {amount:,}원으로 공개경쟁입찰 대상입니다.",
            ))

    return warnings