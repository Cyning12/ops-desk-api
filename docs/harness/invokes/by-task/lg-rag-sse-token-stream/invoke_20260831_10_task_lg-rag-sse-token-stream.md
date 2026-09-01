# Invoke：10-task · lg-rag-sse-token-stream

| 字段 | 值 |
|---|---|
| hat_id | 10-task |
| task_slug | `lg-rag-sse-token-stream` |
| task_paths | `docs/tasks/active/task_lg_rag_sse_token_stream.md` |
| related_review_or_none | 无（本帽结束后交 20） |
| git_branch | `task/lg-rag-sse-token-stream` |
| created_utc_or_local | 2026-08-31 |
| notes | 00 已起草初稿（00 定夺钉死）；10 补全/收紧，**不实现代码** |

---

## 可复制 Prompt 快照

hat_id：10-task  
task_slug：lg-rag-sse-token-stream  
本帽禁区：不实现代码、不改 CI、不签发 HG-AUDIT-R1

必读：`docs/harness/prompts/10-task-requirements.md` · 已落盘 task 初稿（00 定夺钉死）· `05` §4.2/§9/§10.4 · `WAVE_READINESS_lg_rag_sse_v0.md` §1（web 闸 · 不阻塞 api T5）

只做什么：
1. `npx dsh-coding-kit@1.10.0 task lint --file docs/tasks/active/task_lg_rag_sse_token_stream.md`；FAIL 则补结构（验收 / failure_paths / wiki_delta 已有则勿删）
2. 核对 00 定夺与非范围：slug=`lg-rag-sse-token-stream`；`answer` 单 event_type（delta 多帧 + 终帧 `final` · T2 兼容）；aggregator 必做 / direct_answer 同协议或降级；落盘/replay 含 delta；seq 单调不串台；freeze 扩展 `lg-rag-sse-v1`；禁止 T6 / C0–C4 / 重开 T3·T4 / 改 `chat/graph.py` / lg_rag→chat|session 依赖边
3. 若缺「旧测 grep 影响面」或 direct_answer 验收钩则补齐；补 `### 自检结论`
4. 思考轮：本 task 由 SPEC（05 §4.2/§9/§10.4 + WAVE_READINESS §1）承载，**不必**强行加 R0–R5（无节仅 W4）
5. 回填本 invoke 交付摘要；下一棒 20-task-audit

禁止扩 scope。禁止改 `app/` / `tests/`。

## 签收栏

00 代签落盘 · 维护者 Prompt 授权 · 2026-08-31

---

## 交付摘要

| 项 | 内容 |
|---|---|
| **验证** | `npx dsh-coding-kit@1.10.0 task lint --file docs/tasks/active/task_lg_rag_sse_token_stream.md` → exit **0** · **PASS**（W4：无思考轮节 · SPEC 05 §10.4 承载合法）；`npx --yes dsh-coding-kit@1.10.0 task lint-wiki-delta --target .` → exit **0** · **PASS**（scope=all · scanned=97 · issues=0） |
| **变更路径** | `docs/tasks/active/task_lg_rag_sse_token_stream.md`（补 `### 自检结论` · 补 direct_answer 同协议/降级验收钩 · 修订记录追加 10-task 行）；本 invoke |
| **未改** | `app/` · `tests/` · alembic · CI · 图谱 YAML 实现 · 00 定夺钉死项（无实质改动）· `HG-AUDIT-R1`（仍 pending） |
| **内容可交 20** | **是**（结构齐全；00 定夺钉死项保留；无内容阻塞） |
| **需 00 定夺** | **none**（slug / 协议 delta+final / 覆盖 aggregator 必做·direct_answer 降级 / freeze 扩展 / api-only 先合均已钉；若 20 坚持拆新 freeze id → 退回 00） |
| **下一棒** | **20-task-audit**（落盘 review 后由 00 代签 `HG-AUDIT-R1`） |
