# from pydantic_settings import BaseSettings
# from typing import List

# class Settings(BaseSettings):
#     # App
#     APP_NAME: str = "Contract Review API"
#     APP_VERSION: str = "0.1.0"
#     DEBUG: bool = False
#     API_V1_PREFIX: str = "/api/v1"

#     # CORS
#     ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]

#     # PostgreSQL
#     POSTGRES_HOST: str = "postgres"
#     POSTGRES_PORT: int = 5432
#     POSTGRES_DB: str = "contract_review"
#     POSTGRES_USER: str = "admin"
#     POSTGRES_PASSWORD: str = "password"

#     @property
#     def POSTGRES_URL(self) -> str:
#         return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

#     # Milvus
#     MILVUS_HOST: str = "milvus"
#     MILVUS_PORT: int = 19530

#     # Neo4j
#     NEO4J_URI: str = "bolt://neo4j:7687"
#     NEO4J_USER: str = "neo4j"
#     NEO4J_PASSWORD: str = "password"

#     # Redis
#     REDIS_HOST: str = "redis"
#     REDIS_PORT: int = 6379

#     @property
#     def REDIS_URL(self) -> str:
#         return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"

#     # MinIO
#     MINIO_ENDPOINT: str = "minio:9000"
#     MINIO_ACCESS_KEY: str = "minioadmin"
#     MINIO_SECRET_KEY: str = "minioadmin"
#     MINIO_BUCKET: str = "contract-docs"

#     # vLLM
#     VLLM_BASE_URL: str = "http://vllm:8000/v1"
#     VLLM_MODEL: str = "Qwen/Qwen2.5-72B-Instruct"

#     # JWT
#     SECRET_KEY: str = "change-this-in-production"
#     ALGORITHM: str = "HS256"
#     ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 8  # 8시간

#     class Config:
#         env_file = ".env"
#         case_sensitive = True

# settings = Settings()
from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = Field(default="CLMS SEOCHO API")
    app_version: str = Field(default="0.1.0")
    app_env: Literal["local", "dev", "prod", "test"] = Field(default="local")
    debug: bool = Field(default=True)

    api_v1_prefix: str = Field(default="/api/v1")
    docs_url: str = Field(default="/docs")
    redoc_url: str = Field(default="/redoc")

    secret_key: str = Field(default="landsoft-seocho2026")
    algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=60 * 24)

    db_host: str = Field(default="localhost")
    db_port: int = Field(default=5432)
    db_name: str = Field(default="clms_seocho")
    db_user: str = Field(default="postgres")
    db_password: str = Field(default="postgres")

    db_echo: bool = Field(default=False)
    db_pool_pre_ping: bool = Field(default=True)

    cors_allow_origins: str = Field(default="*")
    cors_allow_credentials: bool = Field(default=True)
    cors_allow_methods: str = Field(default="*")
    cors_allow_headers: str = Field(default="*")

    upload_dir: str = Field(default="./uploads")
    data_dir: str = Field(default="./data")

    redis_url: str = Field(default="redis://localhost:6379/0")
    milvus_host: str = Field(default="localhost")
    milvus_port: int = Field(default=19530)
    minio_endpoint: str = Field(default="localhost:9000")
    minio_access_key: str = Field(default="minioadmin")
    minio_secret_key: str = Field(default="minioadmin")
    minio_secure: bool = Field(default=False)
    
    neo4j_uri: str = Field(default="bolt://localhost:7687")
    neo4j_user: str = Field(default="neo4j")
    neo4j_password: str = Field(default="password123")

    vllm_base_url: str = Field(default="http://localhost:18080/v1")
    vllm_model: str = Field(default="gemma-3-12b")

    @property
    def sqlalchemy_database_uri(self) -> str:
        return (
            f"postgresql+psycopg2://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @property
    def cors_origins_list(self) -> list[str]:
        if self.cors_allow_origins.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_allow_origins.split(",") if origin.strip()]

    @property
    def cors_methods_list(self) -> list[str]:
        if self.cors_allow_methods.strip() == "*":
            return ["*"]
        return [method.strip() for method in self.cors_allow_methods.split(",") if method.strip()]

    @property
    def cors_headers_list(self) -> list[str]:
        if self.cors_allow_headers.strip() == "*":
            return ["*"]
        return [header.strip() for header in self.cors_allow_headers.split(",") if header.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()