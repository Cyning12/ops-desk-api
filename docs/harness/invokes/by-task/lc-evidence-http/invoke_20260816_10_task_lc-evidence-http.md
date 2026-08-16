# Invoke：10-task · lc-evidence-http

> **用途**：10-task 开局指令快照（把已签收 web SPEC 的 HTTP 契约写成可执行 api task）。  
> **非** 30：本帽不实现代码、不签发 `HG-AUDIT-R1`。

---

## 元信息表（必填）

| 字段 | 值 |
|------|-----|
| hat_id | 10-task |
| task_slug | `lc-evidence-http` |
| freeze_id | `lc-evidence-http-v1` |
| task_paths | `docs/tasks/active/task_lc_evidence_http.md` |
| related_review_or_none | `../ops-desk-web/docs/harness/reviews/spec_web-lc-evidence-page_audit_R1_20260816.md` |
| git_branch | `task/lc-evidence-http` |
| worktree_root | `.` |
| created_utc_or_local | 2026-08-16 |
| notes | 不实现代码；HG-TASK-DRAFT / HG-AUDIT-R1 = pending；基线 origin/master（PR #33） |

---

## 可复制 Prompt 快照

````text
你是 ops-desk-api 仓的 10-task Agent。Open Folder = 本仓根。分支必须保持 task/lc-evidence-http（从 origin/master 切出，勿叠 tracing）。

身份与禁止
- 把 web 已签收 SPEC 的 HTTP 契约写成可执行、可验收的 task。
- 不实现业务代码、不改 CI、不改 SPEC 实质条款。
- 不签发 HG-AUDIT-R1（保持 pending）。
- 不写绝对本机路径（task lint E6）。

必读
1. ../ops-desk-web/docs/spec/SPEC-web-lc-evidence-page_v1.md §3.2 与 00 签收注记
2. ../ops-desk-web/src/api/lcEvidence.ts
3. docs/harness/prompts/10-task-requirements.md
4. 对照样例：docs/tasks/done/task_langchain_evidence_chain.md
5. docs/_tech_graph/l1/01_modules.md
6. app/ops/lc_evidence_chain/types.py（snippet 为普通 @property）
7. app/ops/router.py · app/ops/deps.py

必须产出 A · Task 文件
路径：docs/tasks/active/task_lc_evidence_http.md
- task_slug = lc-evidence-http
- git_branch = task/lc-evidence-http
- test_strategy = required
- freeze_id = lc-evidence-http-v1
- code_quality_bar = L2_backend
- graph_change_layer = G-L1
- graph_delta = docs/_tech_graph/l1/01_modules.md
- wiki_delta = n/a + note
- invoke_retention_profile = default
- required_invoke_hats = 10,30
- thinking_profile = shortest（仍须 R0+R1–R5 与思考轮控制表）

人工闸（10 起草时）
- HG-GRAPH-MODULES = approved（D4-a 真值已存在；不新增一级模块）
- HG-TASK-DRAFT = pending
- HG-AUDIT-R1 = pending

范围
- POST /api/ops/lc-evidence/invoke
- CurrentUser cookie 鉴权
- 包装 ainvoke_evidence_answer
- 200 {ok:true,data}；evidence 必须含 snippet
- query min_length=1 max_length=8000 → 422
- 500 {ok:false,error:{code,message}}
- refuse 仍 200
- tests/test_lc_evidence_http.py mock 链
- G-L1 备注 HTTP 入口

非范围
- 不改 chat/graph.py / 不接 chat/stream
- 不做 SSE、tracing、前端、改 prompt

验收要点
- 401 / 422 / 200+snippet / 500 envelope
- git diff 不改 graph.py
- ruff + pytest + graph-compile.sh

产出 B · 本 invoke 落盘
路径：docs/harness/invokes/by-task/lc-evidence-http/invoke_20260816_10_task_lc-evidence-http.md
````

---

## 交付摘要（本帽结束时填）

- **验证命令**：`npx @cyning/harness task lint --file docs/tasks/active/task_lc_evidence_http.md`（见本会话输出）
- **变更路径**：
  - `docs/tasks/active/task_lc_evidence_http.md`
  - `docs/harness/invokes/by-task/lc-evidence-http/invoke_20260816_10_task_lc-evidence-http.md`
- **下一棒**：维护者签 `HG-TASK-DRAFT` → 20-task-audit 落 `docs/harness/reviews/task_lc_evidence_http_audit_R1_*.md` → 签 `HG-AUDIT-R1` → 30

---

## 纪律

| 规则 | 说明 |
|------|------|
| 同帽追问 | **不** 新增 invoke；沿用本节路径 |
| 打回重开 | 新文件或 `_r2` 后缀 |
| close 机械闸 | 按 `required_invoke_hats=10,30` |
