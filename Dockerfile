FROM python:3.11-slim

WORKDIR /app

# China network mirrors (Tencent Cloud deploy target; harmless elsewhere).
RUN sed -i 's|deb.debian.org|mirrors.cloud.tencent.com|g' /etc/apt/sources.list.d/debian.sources \
    && apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# pip 源：默认 PyPI；国内部署可 build-arg 切回 tuna（腾讯云机房实测）。
# 本机若只绑 tuna，常出现「fastapi … from versions: none」（镜像空/被墙），故保留 extra 兜底。
ARG PIP_INDEX_URL=https://pypi.org/simple
ARG PIP_EXTRA_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple

# CPU-only torch：生产 2C4G 无 GPU；默认 CUDA 版会拖入数 GB nvidia-* 轮子
# （2026-08-25 deploy 实证 cudnn 366MB@0.67MB/s，超 60min 装不完）。
# 先装 CPU 版后，requirements 里 sentence-transformers 的 torch>=1.11 已被满足，不再拉 CUDA 版。
# extra-index：pytorch cpu 依赖（sympy 等）可能链到 files.pythonhosted.org，
# 部署机直连超时（2026-08-25 run 32827272733）时走 PIP_EXTRA_INDEX_URL。
RUN pip install --no-cache-dir torch \
    --index-url https://download.pytorch.org/whl/cpu \
    --extra-index-url "${PIP_EXTRA_INDEX_URL}" \
    --extra-index-url "${PIP_INDEX_URL}" \
    --trusted-host pypi.org \
    --trusted-host files.pythonhosted.org \
    --trusted-host pypi.tuna.tsinghua.edu.cn \
    --default-timeout=120 --retries 5

RUN pip install --no-cache-dir -r requirements.txt \
    -i "${PIP_INDEX_URL}" \
    --extra-index-url "${PIP_EXTRA_INDEX_URL}" \
    --trusted-host pypi.org \
    --trusted-host files.pythonhosted.org \
    --trusted-host pypi.tuna.tsinghua.edu.cn \
    --default-timeout=120 --retries 5

COPY . .

# Let ops scripts (create_initial_user, import_from_supabase) import the app package.
ENV PYTHONPATH=/app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
