FROM python:3.11-slim

WORKDIR /app

# China network mirrors (Tencent Cloud deploy target; harmless elsewhere).
RUN sed -i 's|deb.debian.org|mirrors.cloud.tencent.com|g' /etc/apt/sources.list.d/debian.sources \
    && apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# CPU-only torch：生产 2C4G 无 GPU；默认 CUDA 版会拖入数 GB nvidia-* 轮子
# （2026-08-25 deploy 实证 cudnn 366MB@0.67MB/s，超 60min 装不完）。
# 先装 CPU 版后，requirements 里 sentence-transformers 的 torch>=1.11 已被满足，不再拉 CUDA 版。
RUN pip install --no-cache-dir torch \
    --index-url https://download.pytorch.org/whl/cpu

RUN pip install --no-cache-dir -r requirements.txt \
    -i https://pypi.tuna.tsinghua.edu.cn/simple

COPY . .

# Let ops scripts (create_initial_user, import_from_supabase) import the app package.
ENV PYTHONPATH=/app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
