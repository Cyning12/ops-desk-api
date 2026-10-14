#!/bin/bash
# 40 live：剥离 proxy + tracer off · 端口 8051
env -u http_proxy -u https_proxy -u all_proxy -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY \
  -u NO_PROXY -u no_proxy -u NODE_USE_ENV_PROXY \
  OPS_CHAT_TRACER=off \
  uv run uvicorn app.main:app --host 127.0.0.1 --port 8051
