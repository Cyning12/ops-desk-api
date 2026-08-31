# Invoke：10-task · lg-rag-sse-resume

| 字段 | 值 |
|---|---|
| hat_id | 10-task |
| task_slug | `lg-rag-sse-resume` |
| task_paths | `docs/tasks/active/task_lg_rag_sse_resume.md` |
| related_review_or_none | 无（本帽结束后交 20） |
| git_branch | `task/lg-rag-sse-resume` |
| created_utc_or_local | 2026-08-31 |
| notes | 00 已起草初稿；10 补全/收紧，**不实现代码** |

---

## 可复制 Prompt 快照

hat_id：10-task  
task_slug：lg-rag-sse-resume  
本帽禁区：不实现代码、不改 CI、不签发 HG-AUDIT-R1

必读：`docs/harness/prompts/10-task-requirements.md` · 已落盘 task 初稿 · `05` §4.2/§4.3/§9/§10.3 · session ROADMAP **仅 L-c**（L-a/L-b/L-d 勿重开）

只做什么：
1. `npx dsh-coding-kit@1.10.0 task lint --file docs/tasks/active/task_lg_rag_sse_resume.md`；FAIL 则补结构（验收 / failure_paths / wiki_delta 已有则勿删）
2. 核对 00 定夺与非范围：slug=`lg-rag-sse-resume`；新表 `ops_lg_rag_run_events`；`POST /lg-rag/replay`；断连仍「尽量跑完」；404；禁止 T3 重做 / T5 / T6 / C0–C4 / lg_rag→chat|session 依赖
3. 若缺「旧测 grep 影响面」则补齐；补 `### 自检结论`
4. 思考轮：本 task 由 SPEC（05 + ROADMAP）承载，**不必**强行加 R0–R5（无节仅 W4）
5. 回填本 invoke 交付摘要；下一棒 20-task-audit

禁止扩 scope。禁止改 `app/` / `tests/`。

## 签收栏

00 代签落盘 · 维护者 Prompt 授权 · 2026-08-31

---

## 交付摘要

| 项 | 内容 |
|---|---|
| **验证** | `npx dsh-coding-kit@1.10.0 task lint --file docs/tasks/active/task_lg_rag_sse_resume.md` → exit **0** · **PASS**（W4：无思考轮节 · SPEC 承载合法）；可选 `task lint-wiki-delta --target .` → exit **0** · **PASS** |
| **变更路径** | `docs/tasks/active/task_lg_rag_sse_resume.md`（补自检 · 收紧非范围/旧测验收）；本 invoke 交付摘要 |
| **未改** | `app/` · `tests/` · alembic · CI · 图谱 YAML 实现 · `HG-AUDIT-R1`（仍 pending） |
| **内容可交 20** | **是**（结构齐全；00 定夺钉死项保留；无内容阻塞） |
| **需 00 定夺** | **none**（slug / 新表 / `/replay` / 断连仍跑完 / 404 / freeze 扩展均已钉；若 20 坚持拆新 freeze id → 退回 00） |
| **下一棒** | **20-task-audit**（落盘 review 后由 00 代签 `HG-AUDIT-R1`） |
