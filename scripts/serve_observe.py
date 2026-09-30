"""本地观察引导（D2 闸灰度 · RUNBOOK_delegation_token_observe_local_v1_zh.md）。

uvicorn 只配置自身 logger，root 停 WARNING 会吞掉 app 台账（如 delegation
`logger.info` 审计行）。本引导先把 root 放开到 INFO，再以 log_config=None
起 uvicorn（不动 uvicorn 既有 logger 配置）。仅本地观察用 · 非生产路径。
"""
import logging

import uvicorn

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
uvicorn.run("app.main:app", host="0.0.0.0", port=8000, log_config=None)
