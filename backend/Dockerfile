# backend/Dockerfile
FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=120

WORKDIR /app

RUN --mount=type=cache,target=/var/cache/apt \
    --mount=type=cache,target=/var/lib/apt/lists \
    set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
      gcc \
      libffi-dev \
      libgomp1 \
      libglib2.0-0 \
      libgl1 \
      curl \
      ca-certificates; \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# # torch — cu124 빌드 (CUDA 12.8 forward compatible)
# RUN pip install torch==2.5.1+cu124 \
#     --index-url https://download.pytorch.org/whl/cu124

# # PaddlePaddle — CUDA 12.8 nightly 최신버전
# RUN pip install paddlepaddle-gpu==3.0.0.dev20250811 \
#     -i https://www.paddlepaddle.org.cn/packages/nightly/cu128/

RUN --mount=type=cache,target=/root/.cache/pip \
    python -m pip install -U pip setuptools wheel && \
    python -m pip install --prefer-binary -r requirements.txt

COPY app/ ./app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]