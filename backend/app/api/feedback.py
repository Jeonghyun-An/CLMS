from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, status

from app.schemas.common import BaseResponse
from app.schemas.enums import FeedbackType
from app.schemas.feedback import (
    ReviewFeedbackCreateRequest,
    ReviewFeedbackListResponse,
    ReviewFeedbackResponse,
)

router = APIRouter()


@router.post(
    "/reviews/{review_run_id}/feedback",
    response_model=BaseResponse[ReviewFeedbackResponse],
    status_code=status.HTTP_201_CREATED,
    summary="검토 피드백 등록",
    description="검토 결과 또는 개별 이슈에 대한 사용자 피드백을 등록합니다.",
)
async def create_review_feedback(
    review_run_id: int,
    body: ReviewFeedbackCreateRequest,
) -> BaseResponse[ReviewFeedbackResponse]:
    data = ReviewFeedbackResponse(
        id=1,
        review_run_id=review_run_id,
        issue_id=body.issue_id,
        user_id=1,
        feedback_type=body.feedback_type,
        comment=body.comment,
        created_at=datetime.now(),
    )
    return BaseResponse(data=data)


@router.get(
    "/reviews/{review_run_id}/feedback",
    response_model=BaseResponse[ReviewFeedbackListResponse],
    summary="검토 피드백 목록 조회",
    description="검토 실행에 등록된 피드백 목록을 조회합니다.",
)
async def list_review_feedback(review_run_id: int) -> BaseResponse[ReviewFeedbackListResponse]:
    data = ReviewFeedbackListResponse(
        items=[
            ReviewFeedbackResponse(
                id=1,
                review_run_id=review_run_id,
                issue_id=9001,
                user_id=1,
                feedback_type=FeedbackType.correct,
                comment="금액 불일치 지적이 정확합니다.",
                created_at=datetime.now(),
            ),
            ReviewFeedbackResponse(
                id=2,
                review_run_id=review_run_id,
                issue_id=9002,
                user_id=2,
                feedback_type=FeedbackType.partial,
                comment="누락 항목은 맞지만 보완 문구는 수정 필요합니다.",
                created_at=datetime.now(),
            ),
        ]
    )
    return BaseResponse(data=data)