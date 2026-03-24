from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.router import api_router
from app.schemas.common import HealthCheckResponse
from app.core.database import create_all_tables

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="서초구 AI 계약서류 검토시스템 백엔드 API",
    docs_url=settings.docs_url,
    redoc_url=settings.redoc_url,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "version": settings.app_version}


@app.get("/", response_model=HealthCheckResponse, tags=["Health"])
async def root() -> HealthCheckResponse:
    return HealthCheckResponse()


@app.on_event("startup")
def on_startup() -> None:
    pass
    # create_all_tables()