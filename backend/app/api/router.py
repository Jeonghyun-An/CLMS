from fastapi import APIRouter

from app.api import (
    checklists,
    documents,
    feedback,
    projects,
    regulations,
    reports,
    reviews,
)

api_router = APIRouter()

api_router.include_router(projects.router, prefix="/projects", tags=["Projects"])
api_router.include_router(documents.router, prefix="/documents", tags=["Documents"])
api_router.include_router(reviews.router, prefix="/reviews", tags=["Reviews"])
api_router.include_router(reports.router, prefix="/reports", tags=["Reports"])
api_router.include_router(regulations.router, prefix="/regulations", tags=["Regulations"])
api_router.include_router(checklists.router, prefix="/checklists", tags=["Checklists"])
api_router.include_router(feedback.router, prefix="/feedback", tags=["Feedback"])