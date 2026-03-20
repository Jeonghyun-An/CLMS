from fastapi import APIRouter
from app.api.v1.endpoints import upload, review

api_router = APIRouter()

api_router.include_router(upload.router, prefix="/upload",  tags=["upload"])
api_router.include_router(review.router, prefix="/review",  tags=["review"])


@api_router.get("/ping")
async def ping():
    return {"message": "pong"}
