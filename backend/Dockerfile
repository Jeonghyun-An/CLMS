FROM python:3.11-slim

WORKDIR /app

# 시스템 의존성 —  PaddleOCR 추가
RUN apt-get update && apt-get install -y \
    gcc \
    libffi-dev \
    libgomp1 \
    libglib2.0-0 \
    libgl1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# torch — cu124 빌드 (CUDA 12.8 forward compatible)
RUN pip install torch==2.5.1+cu124 \
    --index-url https://download.pytorch.org/whl/cu124

# PaddlePaddle — CUDA 12.8 nightly 최신버전
RUN pip install paddlepaddle-gpu==3.0.0.dev20250811 \
    -i https://www.paddlepaddle.org.cn/packages/nightly/cu128/

# 나머지 패키지
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]