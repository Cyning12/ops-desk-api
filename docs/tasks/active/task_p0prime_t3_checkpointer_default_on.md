# Task：P0' T3 PG checkpointer 默认翻开——LG_RAG_HTTP_CHECKPOINTER unset=postgres

> **状态**：in_progress（2026-11-13 起）  
> **类型**：运行时语义翻转（纯 env 默认值 · 零 DDL · 零新表/迁移）  
> **关联图谱**：`docs/_tech_graph/l1/01_modules.md`（lg_rag 行 PG checkpointer 段备注 + 签收行）  
> **落盘**：`docs/tasks/active/task_p0prime_t3_checkpointer_default_on.md`；验收后 `git mv` → `docs/tasks/done/`  
> **来源**：ops-desk-workspace `docs/01-scope/03-general-agent/06-kickoff-readiness.md` 任务卡 T3（issue #23 Round 4 裁定 P2 · 关键链 T1→T3→T4）

---

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `p0prime-t3-checkpointer-default-on` |
| **test_strategy** | `required` |
| **test_strategy_note** | 新真值表单测（unset→开 / postgres 各形态→开 / 空值·off·memory·0·none→关）；测试面 conftest autouse 统一压回 off；5 站点 delenv→setenv 手术；sse_hitl 反向对照语义反转改写 |
| **code_quality_bar** | `recommended` |
| **orchestration** | P0' 任务卡 T3（关键链 T1→T3→T4 · 依赖 T1 已闭环） |
| **semi_auto** | `false` |
| **audit_profile** | `human_only` |
| **invoke_retention_profile** | `default` |
| **required_invoke_hats** | `10,30,40` |
| **git_branch** | `task/p0prime-t3-checkpointer-default-on` |
| **graph_change_layer** | `G-L1` |
| **graph_delta** | `note-only` |
| **graph_delta_note** | 不新增模块/节点/边；`01_modules.md` lg_rag 行 PG checkpointer 段备注 + HG-GRAPH-MODULES 签收行 |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 本仓未启用 WikiTrack |
| **review_hat** | `20` |
| **close_pr_policy** | `required` |
| **experience_capture** | `recommended` |
| **kpi_rubric** | `KPI_RUBRIC_v1_2` |
| **kpi_aggregator** | `CLOSE` |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| **HG-TASK-DRAFT** | approved | 22-R1, 30 | 维护者授权（issue #23 R4 评论 + 会话 m00177「签收，开始」） |
| **HG-AUDIT-R1** | approved | 30 | 维护者会话签收（m00177「签收，开始」，覆盖 P0' T1–T7 全部任务卡） |
| **HG-GRAPH-MODULES** | approved | 30 | 仅备注追加，不新增一级模块；签收行见 `01_modules.md` |

---

## 背景与目标

`app/ops/lg_rag/checkpointer.py:30` `use_postgres_checkpointer()` 现状 = 仅显式 `postgres` 才开（默认关）。默认关意味着 HITL 批准后的跨请求 resume 在默认部署下必 503（`hitl/resume.py:317` fail-closed）——「能批准不能执行」的假安全感。R4 裁定 P2：**默认值翻转为 postgres**（纯 env 翻转、无 DDL、存量 run 无 checkpoint 属预期、503 防御保留），灰度三步（① 测试环境 HITL 全链回归 → ② 生产单副本翻转 → ③ 观察 1 周 resume 错误率 0）。

**翻转语义**：unset ⇒ 开（postgres）；显式 `postgres`（任意大小写/含空白）⇒ 开；其余任意值（含空串）⇒ 关。空串回退口保留 —— `.env` 空值压制与测试卫生的既有手法不变。

**完成态**：

- [ ] `checkpointer.py` 翻转 + docstring 改写；`router.py` / `sse_stream.py` docstring 同步。
- [ ] `tests/conftest.py` autouse fixture 统一 setenv 空值（测试面压回 off）。
- [ ] 5 站点 delenv→setenv 手术：sse_stream / sse_token_stream / sse_hitl 三 fixture + `test_hitl_resume.py` 反向对照 + query_rewrite fixture；sse_hitl `test_sse_does_not_open_pg_saver_by_default` 语义反转改写为「显式关回退口有效」对照。
- [ ] 新增 `tests/test_lg_rag_checkpointer.py` 真值表单测。
- [ ] 验收脚本对齐：`hitl_approval_loop.py` `_PG_CHECKPOINTER` 表达式对齐新真值表（.sh 恒 export 空值语义不变，注释修正）。
- [ ] `.env.example` / `GUIDE_env_inventory_v1.md` / `RUNBOOK_local-acceptance_v1_zh.md` / `RUNBOOK_hitl_ops_v1_zh.md` 注记同步。
- [ ] 图谱：`01_modules.md` lg_rag 行备注 + 签收行。
- [ ] N3 自注册：`registry.yaml` entry（status=active · base=`ee1941f`）。

**不做**（非范围）：

- alembic / 新表 / 迁移 零触碰（纯 env 翻转无 DDL，R4 裁定 P2）。
- 生产灰度动作（灰度三步 ②③ 属运营侧，本卡交付代码+测试面+文档）。
- resume/decide/HITL 链路任何行为改动（503 fail-closed 保留原样）。
- web / ios / workspace 仓零改动。

---

## 范围

- [ ] `app/ops/lg_rag/checkpointer.py`（翻转+docstring）、`router.py`（docstring）、`sse_stream.py`（docstring）
- [ ] `tests/conftest.py`（autouse fixture）、`tests/test_lg_rag_checkpointer.py`（新增）
- [ ] `tests/test_lg_rag_sse_stream.py`、`test_lg_rag_sse_token_stream.py`、`test_lg_rag_sse_hitl.py`、`test_hitl_resume.py`、`test_lg_rag_query_rewrite.py`
- [ ] `scripts/acceptance/hitl_approval_loop.py`、`hitl_approval_loop.sh`（表达式/注释）
- [ ] `.env.example`、`docs/guides/GUIDE_env_inventory_v1.md`、`RUNBOOK_local-acceptance_v1_zh.md`、`RUNBOOK_hitl_ops_v1_zh.md`
- [ ] `docs/_tech_graph/l1/01_modules.md`、`docs/harness/audit_gates/registry.yaml`

## 非范围

- `alembic/**`、`app/db/models.py`、hitl 链路行为代码（resume.py/decide.py）。
- `tests/test_lg_rag_sse_*` 中 PG 路径正向用例（`monkeypatch.setenv("postgres")` 的用例零 diff）。
- CI workflow（`.github/workflows/pytest.yml` 无 PG service 缺口仅注记，另 task 议）。

---

## 失败路径

| 触发条件 | 系统行为 | 可重试 | 用户可见 |
|----------|----------|--------|----------|
| 翻转后测试面未压回 off | 干净环境 lg-rag HTTP/SSE 用例真连 PG 全红 | conftest fixture 兜底 | CI 红 |
| 某站点仍 delenv | unset 吃到新默认=开 → 对照断言被翻 | 改 setenv 空值 | 本地/CI 红 |
| .sh 非 PG 档未显式置空 | 服务端默认开 → 验收脚本语义漂移 | .sh 恒 export 空值（已实证不变） | 验收脚本误报 |
| 存量 run 无 checkpoint resume | 503 fail-closed（预期行为保留） | 重发新 run | 409/503 明确错误码 |
| 在途面触碰 scripts/ 触发波次闸 | `test_wave_gate_registry` 红 | 提交后自清（T1/T2 已实证） | 本地红（CI 干净树绿） |

---

## 验收标准

- [ ] `use_postgres_checkpointer()` 真值表：unset→True；postgres（大小写/空白）→True；""/off/memory/0/none→False（新单测钉死）。
- [ ] 干净环境（无 .env、无 PG、无在途面）全量 `pytest` 零新增红（conftest 压回 off 生效）。
- [ ] hitl-browser-decide-v1 freeze 回归：HITL 相关测试件（test_hitl_* / test_lg_rag_sse_hitl）全绿。
- [ ] `ruff check app tests` 通过。
- [ ] `./scripts/graph-compile.sh` 通过。
- [ ] `npx spec-wave task lint` 通过。
- [ ] 提交到 `task/p0prime-t3-checkpointer-default-on` 并创建 PR。
- [ ] N-R2-1 复测：本机/docker 无 PG 不可行 → 记偏差「测试面回归绿 + N-R2-1 复测待首个 PG 环境」，登记 issue #23。

---

## 给执行帽的必读列表

1. `AGENTS.md`
2. `docs/tasks/done/task_p0prime_t1_ws_shutdown.md` / `task_p0prime_t2_chat_legacy_cleanup.md`（先例：提交先行 + 干净 worktree 全量验证）
3. `app/ops/lg_rag/checkpointer.py`、`router.py`、`sse_stream.py`、`run_worker.py`
4. `tests/conftest.py`（autouse fixture 体例 :185/:275/:282/:305）
5. `scripts/acceptance/hitl_approval_loop.sh`（:92-97 恒 export 机制）
6. `docs/harness/audit_gates/README.md`（N3 自注册程序）

---

## 思考轮控制

| 轮 | 结论 | early_stop | reason（early_stop） | residual_risks |
|----|------|------------|----------------------|----------------|
| R0 | 问题框定：默认关 ⇒ 默认部署 HITL resume 必 503（假安全感）；R4 P2 裁定翻转 | no | — | 存量 run 无 checkpoint 属预期（503 保留） |
| R1 | 开工闸：三闸 approved（m00177 覆盖 T1–T7） | no | — | 无 |
| R2 | 竖切：单 PR——翻转+docstring / conftest+测试手术+新单测 / 脚本+docs / 图谱+N3 | no | — | 在途面闸咬（scripts/）提交先行消解 |
| R3 | 失败语义：最锋利边界 = 测试面被新默认打爆（unset=on）；conftest autouse setenv 空值是全仓兜底 | no | — | CI 无 PG service（skip 绿缺口已注记另议） |
| R4 | 可测性：真值表单测钉死翻转语义；反向对照改写为「回退口有效」；hitl freeze 用例全绿回归 | no | — | N-R2-1 真 PG 复测本地不可行（docker/PG 均不可用） |
| R5 | 交付判定：纯 env 翻转零 DDL，范围 18 文件钉死，可交 30 | no | — | 灰度三步 ②③ 属运营侧另行执行 |

**actual_last_round**：R5 · **early_stop**：no · **residual_risks**：N-R2-1 复测待首个 PG 环境；灰度 ②③ 运营侧

### R0 · 问题框定

默认关 ⇒ 任何不显式配 env 的部署，HITL 批准后 resume 必 503（`resume.py:317`）——审批链「能批不能执行」。R4 裁定 P2 翻转默认，空值回退口保留。

### R1 · 开工闸

三闸 approved：HG-TASK-DRAFT / HG-AUDIT-R1（m00177 覆盖 P0' T1–T7）· HG-GRAPH-MODULES（备注级，签收行回写）。

### R2 · 竖切

单 PR 一次完成：checkpointer 翻转+三 docstring → conftest fixture + 5 站点手术 + 新真值表单测 → 验收脚本两件对齐 → .env.example+三 guides → 图谱备注+签收行 → N3 登记。

### R3 · 失败语义

翻转后 unset=on，所有未显式关的 lg-rag HTTP/SSE 用例会在干净环境真连 PG 建 saver → 全红。解法：conftest autouse fixture 统一 setenv 空值（测试面压回 off），各站点 delenv→setenv 手术（delenv 会吃到新默认）。.sh 恒 export 空值机制已实证语义不变。

### R4 · 可测性

`test_lg_rag_checkpointer.py` 真值表钉死（unset/postgres 形态/空值回退三类）；`test_sse_does_not_open_pg_saver_when_explicitly_off` 改写验回退口；HITL freeze 相关件全绿回归。N-R2-1（真 PG resume）本地不可行（docker 停 · 无本地 PG），记偏差待首个 PG 环境。

### R5 · 交付判定

纯 env 默认值翻转，零 DDL 零新面，范围钉死，可交 30。生产灰度 ②③ 与 N-R2-1 复测列为遗留观察项登记 issue #23。

### 自检结论

（10-task · 2026-11-13）范围 18 文件钉死 · 非范围三条（alembic/models·hitl 行为码·CI workflow）· 验收 8 条可机断 · failure_paths 5 条 · 思考轮 R0–R5 齐全 · 闸表三签（m00177）。

---

## 实现备忘（子 Agent 回填）

（30 实施回填）

---

## 测试策略（Harness）

**test_strategy**: `required`

- 新增 `tests/test_lg_rag_checkpointer.py`：真值表 9 用例（unset→True · postgres×3 形态→True · off 系×5→False）。
- conftest autouse fixture：`LG_RAG_HTTP_CHECKPOINTER` 测试面统一显式空值。
- 手术 5 站点 delenv→setenv；sse_hitl 反向对照语义反转改写。
- 全量 `pytest`（干净环境）+ `ruff check` + graph-compile + freeze 回归。

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-11-13 | 创建 task（issue #23 R4 任务卡 T3 · 裁定 P2；维护者 m00177「签收，开始」） |
