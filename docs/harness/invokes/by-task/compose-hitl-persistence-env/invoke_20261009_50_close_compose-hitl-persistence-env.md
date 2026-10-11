---
hat: 50
task_slug: compose-hitl-persistence-env
date: 2026-10-09
---

# invoke · 50+CLOSE · compose-hitl-persistence-env（compose 透传 OPS_HITL_PERSISTENCE）

## 收口结论

- 链路全通：10-task（config 小 task · 免 SPEC · 依据=验收偏差登记第 2 行处置令 · 锚点实读 docker-compose.yml:51-70 / persistence.py:22,40 / router.py:74-79 · early_stop at R3）→ 20-task-audit R1（PASS-WITH-NITS · 零内容阻塞 · 审查文 `docs/harness/reviews/task_compose_hitl_persistence_env_audit_R1_20261009.md`）→ 维护者三闸人签（HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES · 00 代录 2026-10-09）→ 30（`77382b8` · docker-compose.yml +3 行透传 · 钉死契约全守：无 `:-db` · 注释范式对齐 LG_RAG_DELEGATION_TOKEN_* · 插入位 :65/:66）→ 40（核验 7/7 PASS · A1–A5 逐项独立复跑不采信 30 自报 · 含 A2/A3 docker 端点真跑）。
- 闸链：三闸全 approved（维护者签 · 00 代录 · `invoke_20261009_00_human_sign_compose-hitl-persistence-env.md` 留痕）。
- PR [#207](https://github.com/Cyning12/ops-desk-api/pull/207)：CI 四绿 → merge master `61e44a8`（2026-10-09）。
- 归档：task → `done/`（头部状态 done · 验收 A1–A5 + F1 勾选 · 修订表 CLOSE 行）；active README 登记表补行；Hub `docs/tasks/done/README.md` engineering 域表行 + 修订记录行补登；本 CLOSE invoke 落盘。

## 交付摘要

| 项 | 内容 |
|---|---|
| **产出** | `docker-compose.yml` api.environment +3 行（两行中文注释 + `OPS_HITL_PERSISTENCE: ${OPS_HITL_PERSISTENCE:-}`）· 零生产码 |
| **验收** | A1 渲染对拍两态（diff 仅此一键）· A2 db 态 `/api/ops/hitl/runtime` 三键 `{"mode":"db","store":"DbHitlStore","persists":true}` · A3 默认零 diff（null 态 + 既有告警逐字一致）· A4 改动边界（`app/`/`tests/`/`alembic/`/`.github/` 零 diff）· A5 回归零新增红（hitl 98 passed） |
| **红线** | 默认值钉死为空（`:-` · 无 `:-db`/`:-memory`）· 语义不回读（persistence.py 零改动 · 空串≡缺省论证见 task R3） |

## 留痕

- 40 核验期端口 override 18000 复用健康 db/qdrant，不动 8000 残留 uvicorn；环境已复原。
- N3 注记化裁量成立：`tests/` 对 docker-compose grep 零命中 + `tests/` 零 diff + 全量回归由 PR CI 兜底（CI 四绿实证）。
- worktree `d1-compose-hitl-persistence` 与分支 `fix/compose-hitl-persistence-env` 清理留维护者裁决（active README 已登记）。

## 移交

- **留转**：验收 checklist 阶段 5（重启持久化 `OPS_HITL_PERSISTENCE=db` 全链复走）由维护者按 `docs/acceptance/20261009_chat-history-hitl-ux_local_acceptance.md` 另行组织——本 task 只解锁 compose 形态 env 透传通道，不代行验收。
- 全 docker 形态现可 `OPS_HITL_PERSISTENCE=db docker compose up -d` 直跑阶段 5；默认不设行为与 master 零 diff。
