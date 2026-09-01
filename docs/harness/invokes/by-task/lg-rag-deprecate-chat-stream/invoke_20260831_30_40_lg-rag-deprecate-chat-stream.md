# Invoke：30（含 40）· lg-rag-deprecate-chat-stream（T6）

| 字段 | 值 |
|---|---|
| hat_id | 30（含 40） |
| task_slug | `lg-rag-deprecate-chat-stream` |
| task_paths | `docs/tasks/active/task_lg_rag_deprecate_chat_stream.md` |
| related_review_or_none | `docs/harness/reviews/task_lg_rag_deprecate_chat_stream_audit_R1_20260831.md` |
| git_branch | `task/lg-rag-deprecate-chat-stream` |
| created_utc_or_local | 2026-08-31 |
| notes | 00 代签 HG-AUDIT-R1 后派发；**仅 T6 `/chat/stream` 410**；禁止删 chat 代码/图/表 · 改 lg-rag · 改 WS/models/sessions.latest · 本仓改 Vue · 重开 T2–T5 · C0–C4 · 切分支/push/开 PR |

---

## 人工闸扫描（GATE_VERIFY · 30 重填 · 读 task 表）

| human_gate_id | task表status | 用户/invoke声称 | 一致？ | blocks_30 | 30可开工？ |
|---|---|---|---|---|---|
| HG-TASK-DRAFT | approved | 00 代签 | Y | N | Y |
| HG-AUDIT-R1 | approved | 00 代签 + R1 文 pass | Y | Y | Y |
| HG-GRAPH-MODULES | approved | 不新增一级模块 · 00 代签 · 仅 chat 行/flow 备注 | Y | N | Y |

reviews：`task_lg_rag_deprecate_chat_stream_audit_R1_20260831.md` 存在且内容 pass？ **是**（内容零阻塞 · 非阻塞 5 条 30 知情）

pre-30 invoke：00 + 10 已落盘？ **是**

机械：`npx dsh-coding-kit@1.10.0 verify --target . --task docs/tasks/active/task_lg_rag_deprecate_chat_stream.md` → **VERIFY: PASS**（exit 0 · 本棒复跑）

结论：**可进入读码/改码**（30 首输出已重扫本表）

---

## 可复制 Prompt 快照

hat_id：30（含 40 自检）  
task_slug：lg-rag-deprecate-chat-stream  
本帽禁区：不删 `app/ops/chat/**` 任何文件/拓扑；`app/ops/lg_rag/**` 零 diff；不动 WS/models/sessions.latest；不改 Vue；不直推 master；不切分支不 push 不开 PR。

首动作：GATE_VERIFY（FRAGMENT_30_gate_verify）→ 通过再改码。

00 定夺摘要：
- `POST /api/ops/chat/stream` → **410 Gone**（非 404 · 非删码）：JSON 迁移指针 → `/api/ops/lg-rag/stream` + `Deprecation` 头
- 保留 `Depends(get_current_user)` → 未登录仍 401；保留 models/sessions.latest/WS
- 测试：四 stream 用例改 410 断言；`test_chat_ws.py` / `test_auth.py` 零 diff
- 文档：05 §10.5 回写实现句；活引用 grep 清扫（历史归档/SPEC 旧陈述不改）
- 图谱：chat 行 + `10_flow_chat` deprecated 备注；不删节点/边/indexes
- PR 勿 auto-merge；不 CLOSE（留给 00）

验证：verify · ruff 触及路径 · pytest 全量 · graph-compile · lint-wiki-delta · lg_rag 零 diff。

完成后：回填本 invoke 交付摘要 + task「自检结论（执行者）」；**不 CLOSE（留给 00）**；commit 不 push。

## 签收栏

00 代签落盘 · 维护者 Prompt 授权 · 2026-08-31 · VERIFY PASS

---

## 交付摘要

| 项 | 结果 |
|---|---|
| GATE_VERIFY | PASS · 可开工（三闸 approved · verify exit 0 · 开工前与收尾各复跑一次均 PASS） |
| 实现 | `app/ops/chat/router.py` stream 端点函数体改 `HTTPException(410)`：detail `{error: chat_stream_deprecated, migrate_to: /api/ops/lg-rag/stream, message}` + 头 `Deprecation: true` · `Link: </api/ops/lg-rag/stream>; rel="successor-version"`；**保留** `Depends(get_current_user)`（未登录仍 401）；models/sessions.latest 两端点逐字保留；import 连带清理（R1 非阻塞 2 · 文件内 · 零删除） |
| 测试 | `tests/test_chat_router.py` 四 stream 用例（名保留）改 410 断言：success→410+body 三字段+双头 · requires_auth→401（鉴权前置）· invalid_session→410（不再解析 session）· existing_session_ok→410（docstring 留原 uuid 404 回归意图 · R1 非阻塞 4）；失效 helper/import 同步清理；本文件 **5 passed**（无需 DB）；`test_chat_ws.py` / `test_auth.py` / `test_chat_service.py` **零 diff** |
| 自检 | verify exit 0 · ruff 触及路径 exit 0 · pytest **CI 等价 exit 0**（464 passed · 39 skipped；本机带 PG 500 passed + 2 pre-existing 环境失败 · stash A/B 实证非回归 · CI 无 PG 必 skip）· graph-compile exit 0（9 graphs）· lint-wiki-delta PASS · `git diff master -- app/ops/lg_rag` 空 |
| 禁区核对 | `app/ops/chat/**` 零删除（仅 router.py 改）· `app/ops/lg_rag/**` 零 diff · WS/models/sessions.latest 零行为改动 · 无 Vue 改动 · 未切分支/未 push/未开 PR |
| 文档/图谱 | 05 §10.5 回写「api 实现（2026-08-31 · T6 已落地）」+ §11.4 修订行；活引用清扫 `docs/ios/api-auth-chat.md` · `docs/deployment/rag-frontend-api-plan.md` · `qdrant-server-upgrade.md` · `qdrant-migration-narrative.md`（边角命中分类落 task 自检表：guides/spec README 判历史/边界陈述不改）；`01_modules.md` chat 行备注 + 人签记录；`10_flow_chat.graph.yaml` description/version/节点 label deprecated 备注（+生成物 md / graph.json）；不删节点/边/indexes |
| R1 非阻塞 5 条 | 全部处置（用例名为准 · import 清理 · 边角分类 · 回归意图 docstring · WS 安全自述知悉）——明细见 task 自检结论（执行者） |
| 已知未测项 | 真 LLM/真客户端联调（task 钉死不连真 LLM）；iOS 迁移（另仓）；web 删 `useOpsChatSse`（另 task · Prompt 已落盘）；本机带 PG 2 个 WS 旧测期望过时（pre-existing · 建议另 task 对齐 R-3 事件面或按 CI 语义 skip） |
| 收尾 | task 验收 9 条勾选 + 自检结论（执行者）表 + 修订记录 30+40 行 + 文末「不 CLOSE（留给 00）」；分笔 commit · 未 push |

关键路径：
- `app/ops/chat/router.py`（410 + import 清理）· `tests/test_chat_router.py`（410 断言）
- `docs/spec/agent-infra/05_lg_rag_transport_and_session_plan_v0.md` §10.5/§11.4
- `docs/ios/api-auth-chat.md` · `docs/deployment/{rag-frontend-api-plan,qdrant-server-upgrade,qdrant-migration-narrative}.md`
- `docs/_tech_graph/l1/01_modules.md` · `10_flow_chat.graph.yaml`（+生成物 `10_flow_chat.md` · `shared/graph.json`）
