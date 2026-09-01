# Invoke：10-task · lg-rag-deprecate-chat-stream

| 字段 | 值 |
|---|---|
| hat_id | 10-task |
| task_slug | `lg-rag-deprecate-chat-stream` |
| task_paths | `docs/tasks/active/task_lg_rag_deprecate_chat_stream.md` |
| related_review_or_none | 无（本帽结束后交 20） |
| git_branch | `task/lg-rag-deprecate-chat-stream` |
| created_utc_or_local | 2026-08-31 |
| notes | 00 已起草初稿（00 定夺钉死）；10 补全/收紧，**不实现代码** |

---

## 可复制 Prompt 快照

hat_id：10-task  
task_slug：lg-rag-deprecate-chat-stream  
本帽禁区：不实现代码、不改 CI、不签发 HG-AUDIT-R1、不改 `app/` / `tests/`

必读：`docs/harness/prompts/10-task-requirements.md` · 已落盘 task 初稿（00 定夺钉死）· `05` §4.1/§10.5/§11 · T5 关账链（#105/#106）

只做什么：
1. `npx dsh-coding-kit@1.10.0 task lint --file docs/tasks/active/task_lg_rag_deprecate_chat_stream.md`；FAIL 则补结构（验收 / failure_paths / wiki_delta 已有则勿删）
2. 核对 00 定夺与非范围：slug=`lg-rag-deprecate-chat-stream`；`/chat/stream` → **410**（非 404 · 非删码）+ JSON 迁移指针 + `Deprecation` 头；`app/ops/chat/**` 零删除；保留 `GET /chat/models` · `GET /chat/sessions/latest` · WS `/chat/ws`；iOS 另仓；lg-rag 主路径零改动；禁止重开 T2–T5 / C0–C4 / chat 事件兼容层 / 改 freeze `lg-rag-sse-v1`
3. 事实核对：`app/ops/chat/router.py`（stream L34 · models L97 · sessions/latest L108）· `tests/test_chat_router.py`（L127/147/158/204）· `app/ops/chat/ws.py`（L79）；与现网不符才改并记录
4. 补遗漏验收钩：`Deprecation` 头取值形态建议 · 410 body 字段名建议 · grep 清扫检索词 · 保留端点旧测落点（test_auth.py sessions/latest · test_chat_ws.py）
5. 思考轮：本 task 由 SPEC（05 §4.1/§10.5/§11）+ T0–T5 关账链承载，**不必**强行加 R0–R5（无节仅 W4）
6. 补 `### 自检结论`；修订记录追加 10-task 行；回填本 invoke 交付摘要；下一棒 20-task-audit

禁止扩 scope。禁止改 `app/` / `tests/`。禁止改人工闸表状态（HG-AUDIT-R1 保持 pending）。

## 签收栏

00 代签落盘 · 维护者 Prompt 授权 · 2026-08-31

---

## 交付摘要

| 项 | 内容 |
|---|---|
| **验证** | `npx dsh-coding-kit@1.10.0 task lint --file docs/tasks/active/task_lg_rag_deprecate_chat_stream.md` → exit **0** · **PASS**（W4：无思考轮节 · SPEC 05 §4.1/§10.5 承载合法）；`npx --yes dsh-coding-kit@1.10.0 task lint-wiki-delta --target .` → exit **0** · **PASS** |
| **变更路径** | `docs/tasks/active/task_lg_rag_deprecate_chat_stream.md`（补 `### 自检结论` · 验收补 `Deprecation` 头/body 字段形态建议 + 鉴权次序建议 + grep 检索词 + 旧测落点 · graph_delta 钉明 `10_flow_chat.*` 存在 · 修订记录追加 10-task 行）；本 invoke |
| **事实核对** | **现网一致 · 零修正**：router.py `@router.post("/stream")` L34 ✓ · models L97 ✓ · sessions/latest L108 ✓；test_chat_router.py `/api/ops/chat/stream` L127/147/158/204 ✓（四用例 200/401/404/200）；ws.py WS `/chat/ws` L79 demo 未鉴权 ✓；补充落点：sessions/latest 旧测在 `tests/test_auth.py` L161+ · WS 测在 `tests/test_chat_ws.py` · README 无 chat/stream 引用 · 05 §10.5 在 L338 |
| **未改** | `app/` · `tests/` · alembic · CI · 图谱 YAML 实现 · 00 定夺钉死项（**零实质改动**）· `HG-AUDIT-R1`（仍 pending） |
| **内容可交 20** | **是**（结构齐全；00 定夺钉死项保留；无内容阻塞） |
| **需 00 定夺** | **none**（slug / 410 非 404 / 不删码 / 保留端点 / iOS 另仓 / lg-rag 零改动均已钉；形态建议类留给 30 落地定，非退回项） |
| **下一棒** | **20-task-audit**（落盘 review 后由 00 代签 `HG-AUDIT-R1`） |
