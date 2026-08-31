# Invoke：10-task · lg-rag-session-continuity

| 字段 | 值 |
|---|---|
| hat_id | 10-task |
| task_slug | `lg-rag-session-continuity` |
| task_paths | `docs/tasks/active/task_lg_rag_session_continuity.md` |
| related_review_or_none | 无（本帽结束后交 20） |
| git_branch | `task/lg-rag-session-continuity` |
| created_utc_or_local | 2026-08-31 |
| notes | 00 已起草初稿；10 补全/收紧，**不实现代码** |

---

## 可复制 Prompt 快照

hat_id：10-task  
task_slug：lg-rag-session-continuity  
本帽禁区：不实现代码、不改 CI、不签发 HG-AUDIT-R1

必读：`docs/harness/prompts/10-task-requirements.md` · 已落盘 task 初稿 · `05` §4/§9/§10.2 · session ROADMAP L-a/L-b/L-d（L-c=T4 勿塞）

只做什么：
1. `npx dsh-coding-kit@1.10.0 task lint --file docs/tasks/active/task_lg_rag_session_continuity.md`；FAIL 则补结构（验收标准 / failure_paths / wiki_delta 已有则勿删）
2. 核对 00 定夺与非范围：禁止 T4 replay、禁止 lg_rag→chat 依赖、freeze 沿用 lg-rag-sse-v1
3. 若缺「旧测 grep 影响面」则补（行为变更类）
4. 思考轮：本 task 由 SPEC 承载，**不必**强行加 R0–R5（无节仅 W4）
5. 回填本 invoke 交付摘要；下一棒 20-task-audit

禁止扩 scope 到 C0–C4 / T5 / T6。

## 签收栏

00 代签落盘 · 维护者 Prompt 授权 · 2026-08-31

---

## 交付摘要

- **验证命令**：`npx dsh-coding-kit@1.10.0 task lint --file docs/tasks/active/task_lg_rag_session_continuity.md` → **LINT: PASS**（exit 0）· **W4** 无思考轮节（SPEC 承载合法，未加 R0–R5）
- **变更路径**：
  - `docs/tasks/active/task_lg_rag_session_continuity.md`（补 `### 自检结论` 占位；收紧范围/非范围/验收/failure_paths/00 定夺；钉跨用户 thread→404；旧测 grep 影响面保留；`freeze_id=lg-rag-sse-v1`；HG-AUDIT-R1 仍 pending）
  - 本 invoke（本摘要）
- **未改**：`app/` · `tests/` · alembic · 图谱 YAML · CI · 未签发 HG-AUDIT-R1 · 未 commit
- **内容阻塞可交 20**：是（零内容阻塞）
- **需 00 定夺**：none（10 补钉：跨用户 `thread_id` → **404**；00 可改 403，不阻塞 20）
- **下一棒**：20-task-audit

---

## 修订记录

| 日期 | 说明 |
|---|---|
| 2026-08-31 | 00 落盘 invoke 骨架 |
| 2026-08-31 | 10-task 回填交付摘要 · lint PASS（W4） |
