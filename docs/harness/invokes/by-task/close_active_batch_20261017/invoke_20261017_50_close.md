# invoke · 2026-10-17 · 50 CLOSE：active 批量关账（七档 · close/active-batch-20261017）

> **帽位**：50 CLOSE（维护者令「判断当前任务是否已经完成并安排后续任务」→ 判定 active/ 七档全实质完成 → 「好的」授权统一 CLOSE 关账）
> **分支**：`close/active-batch-20261017`（base origin/master `833f605`）
> **CLOSE 档**：`docs/tasks/close/` 六件（五单档 + 一 co-CLOSE 合一档）

---

## 一 · 前置核验（关账判定依据）

| task | 交付证据 | 判定 |
|------|----------|------|
| arch_browser_eng_graph_mermaid | PR #257 MERGED squash `833f605`（2026-10-17）· TC-1–TC-6 全绿 | ✅ 完成 |
| hitl_resume_replay_contract | PR #248 MERGED squash `acac5e6`（2026-10-13 · head `task/hitl-resume-obs-drafts`）· TC1–TC5 全勾 | ✅ 完成 |
| hitl_n1_locked_branch_inject | PR #238 MERGED squash `8dd15ee`（2026-10-11） | ✅ 完成 |
| verify-upstream-dual-address | PR #240 MERGED squash `93c4960`（2026-10-11）· 上游 SpecWave #35/#36 已提 | ✅ 完成 |
| n40_1_log_init_window | PR #239 MERGED squash `9c07ab4`（2026-10-11） | ✅ 完成 |
| lg_rag_sse_run_worker | PR #250 MERGED squash `56e4a9f`（2026-10-14）· B1–B6/B3/B5 PASS | ✅ 完成 |
| lg_rag_sse_disconnect_completion | 零合并交付 · Wave A TC5 live×3 FAIL 停派 · 正文不再修订钉案 · run_worker co-CLOSE 承接 | ✅ 收尾关账 |

## 二 · 落盘清单（本批量 CLOSE 增量）

1. `git mv` 七档 `docs/tasks/active/ → docs/tasks/done/` · 状态行全改 **CLOSED**（各含 PR/squash 链）· 修订记录各补 CLOSED 行（run_worker 兼回填经验总结占位）。
2. `docs/tasks/active/README.md` 登记表：补登六行（五单 + 一 co-CLOSE）· 删两行过期 SSE active 行（run_worker「未 commit」表述随 PR #250 事实作废）。
3. 址B 复制件六件落盘 `docs/audits/task-review/`：`20261011_hitl-n1-locked-branch-inject_r1.md` / `20261011_verify-upstream-dual-address_r1.md` / `20261011_n40-1-log-init-window_r1.md` / `20261012_hitl-resume-replay-contract_r1.md` / `20261013_lg-rag-sse-disconnect-completion_r1.md` / `20261014_lg-rag-sse-run-worker_r1.md`（双址规约 §二 过渡期口径 · 址A 原件不动）。mermaid 为追溯档无独立 R 审查文 → 无复制件，走豁免扩列（见 §三）。
4. CLOSE 档六件：`close_arch_browser_eng_graph_mermaid_20261017.md` · `close_hitl_resume_replay_contract_20261017.md` · `close_hitl_n1_locked_branch_inject_20261017.md` · `close_verify_upstream_dual_address_20261017.md` · `close_n40_1_log_init_window_20261017.md` · `close_lg_rag_sse_run_worker_co_disconnect_20261017.md`（co-CLOSE 合一）。
5. 本 invoke。

## 三 · 质量钉复跑（重定向取真码）

| 钉 | 命令 | 结果 |
|----|------|------|
| 归档后仓级 verify（首跑） | `npx --yes spec-wave verify --target . > /tmp/verify_close_batch.log 2>&1` | **EXIT=2** · reviews 缺口 1：`task_arch_browser_eng_graph_mermaid.md` missing R<n> review（追溯档无独立审查文 · 预期内） |
| 豁免扩列 | `docs/harness/legacy-gate-exempt.yaml` 新增 slug `arch-browser-eng-graph-mermaid`（四字段齐 · reason 如实注记追溯性质+30 invoke 证据址 · 承 PR #245 扩列纪律 · 本批量 CLOSE PR 即人审面） | 复跑 **EXIT=0 · VERIFY: PASS** |
| 逐档 task lint | `npx --yes spec-wave task lint --file docs/tasks/done/<七档>` | 7/7 **LINT: PASS**（mermaid 首跑 FAIL：验收节非勾选形态+缺自检结论节 → 机读形态修订（✅→`- [x]` · 验收内容零变更）后 PASS · 余 W5/W6 warn-only 过渡期照登） |

## 四 · 交付与移交

- 单一 commit → 推送 → PR（base master）→ CI 监视 → **绿后不合并**，报维护者裁定合并。
- 移交清理项：已并分支 `task/arch-browser-eng-graph-mermaid` / `task/hitl-n1-locked-branch-inject` / `task/n40-1-log-init-window` / `task/verify-upstream-dual-address` / `task/hitl-resume-obs-drafts` / `task/lg-rag-sse-run-worker` / `task/lg-rag-sse-disconnect-completion`（本地/远端）与本关账分支 —— PR 合并后由 00 统一清理（本 CLOSE 不删任何东西）。
- 纪律遵守：纯文档零实现码改动；只 add 本线件。
