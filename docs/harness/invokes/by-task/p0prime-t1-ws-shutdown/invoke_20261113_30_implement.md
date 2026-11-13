# invoke · 30-implement · p0prime-t1-ws-shutdown · 2026-11-13

- **hat**：30-implement（改码）
- **闸核验**：HG-TASK-DRAFT=approved · HG-AUDIT-R1=approved（m00177）· HG-GRAPH-MODULES=approved（01_modules.md 签收行）
- **改动**：
  - `app/ops/router.py`：删 `from app.ops.chat.ws import router as chat_ws_router`（:11）与 `router.include_router(chat_ws_router)`（:33）
  - 删 `app/ops/chat/ws.py`
  - `app/config.py`：删 `ops_chat_ws_enabled`（:50，P5 不带闸保留）
  - 删 `tests/test_chat_ws.py`；新增 `tests/test_chat_ws_removed.py` 负向回归
  - `docs/_tech_graph/l1/01_modules.md`：chat 行备注 + HG-GRAPH-MODULES 签收行
- **自检**：pytest 全绿 · ruff PASS · grep 残留为零 · graph-compile PASS
