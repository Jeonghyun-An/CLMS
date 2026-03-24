from __future__ import annotations

from datetime import datetime
from typing import Optional

from app.schemas.common import BaseSchema
from app.schemas.enums import FeedbackType


class ReviewFeedbackCreateRequest(BaseSchema):
    issue_id: Optional[int] = None
    feedback_type: FeedbackType
    comment: Optional[str] = None


class ReviewFeedbackResponse(BaseSchema):
    id: int
    review_run_id: int
    issue_id: Optional[int] = None
    user_id: int
    feedback_type: FeedbackType
    comment: Optional[str] = None
    created_at: datetime


class ReviewFeedbackListResponse(BaseSchema):
    items: list[ReviewFeedbackResponse]