from fastapi import APIRouter

api_router = APIRouter()

# 엔드포인트 추가는 각 파일 구현 후 여기서 include
# from app.api.v1.endpoints import upload, review, admin
# api_router.include_router(upload.router, prefix="/upload", tags=["upload"])
# api_router.include_router(review.router, prefix="/review", tags=["review"])
# api_router.include_router(admin.router, prefix="/admin", tags=["admin"])

@api_router.get("/ping")
async def ping():
    return {"message": "pong"}