# task（fix · active）：observe_node config 注解形态致 HITL 审批单 thread_id 空 → resume 409 根治

> **状态**：active（2026-10-28 维护者签收 m00627「签收」，00 转录闸表；修复落地后其验收 4 与 task A/NO_PROXY fix 验收 5 同场复跑补完）。
> **由来**：2026-10-28 task A（capability output_fields · PR #294）+ NO_PROXY fix（PR #295）合并验收 5 复跑「#2140 这个 issue 在说什么？调用write本地落盘结论」，run `0ebcbf86938c47b4a9cdc51d762fb953` seq8 hitl.waiting、seq9 done{waiting_approval}；维护者点击批准后 run 不继续。
> **分支**：fix/hitl-observe-node-config-injection（fix，非紧急，仍走 task 流程）。

## 根因（已钉案，2026-10-28 实证）

1. 审批单 `hitl_fb4d74b23cca448aa120` decide 成功（status=approved · decision_by=admin · decided_at 2026-10-28 02:05:52Z），但绕开前端直调 `POST /api/ops/hitl/requests/{id}/resume` 返回 **409「申请里没有 thread_id —— 定位不到挂起的 checkpoint，无法恢复」**；DB 实证该行 `thread_id=''`、`checkpoint_id=NULL`。
2. 机制：`app/ops/lg_rag/multi/nodes.py:2125` `observe_node(state, config: RunnableConfig | None = None)` 使用了**禁用注解形态**。本文件 `nodes.py:14` 带 `from __future__ import annotations`（注解字符串化），而 langgraph 1.x 只认 `RunnableConfig` / `Optional[RunnableConfig]` 两种字面写法——`RunnableConfig | None` 字符串不被识别 → **config 不注入** → `_thread_id_of`（`nodes.py:1884-1898`）config 兜底落空返回 `""` → `_persist_hitl`（`nodes.py:2146` 调用、`:2019` 落库键）把空串写进审批单。SSE 事件里的 thread_id 是 `app/ops/lg_rag/sse_stream.py:455` 显示层兜底补的，掩盖了落库为空。
3. 本文件 `nodes.py:27-32` 注释**早已写明此陷阱**（langgraph 0.2→1.2 升级 fd8c9b1 时踩坑所留），但 **PR #274（b73bb8a · ruff 存量收口）的批量现代化改写把签名从 `Optional[RunnableConfig]` 改成 `RunnableConfig | None`** → 回归自此引入。实证：2026-10-28 探针复现 langgraph 对该形态抛 `UserWarning: The 'config' parameter should be typed as...` 且不注入；同条件 `Optional[RunnableConfig]` 正常注入。
4. **ruff 反咬实证**：改回 `Optional[RunnableConfig]` 后 `.venv/bin/ruff check` 立即 UP045 红（exit 1，pyproject.toml:69 select 含 UP）——#274 正是这样被 `ruff --fix` 喂出来的，修复必须同栓 noqa。
5. 影响面：**#274 合并以来所有 supervisor run 的 HITL 审批单 thread_id 全为空 → resume 全灭**（409 fail-closed 按设计正确拦下）。图侧无损伤：该 run 的 thread `1539acea41414b468a94a7f13d1f09b3` 在 checkpoints 表有 7 条，单据补上 thread_id 即可恢复。全仓扫描 `config: RunnableConfig | None` 仅 2 处：`nodes.py:1884` `_thread_id_of`（helper 非节点，不受注入影响）与 `nodes.py:2125` observe_node（唯一受害节点）。

## 修复设计（最小面）

`app/ops/lg_rag/multi/nodes.py`：

1. `observe_node` 签名改回 `config: Optional[RunnableConfig] = None`（承 nodes.py:27-32 钉案形态；`Optional` import 按现状补回）；
2. 该行附 `# noqa: UP045` + 一行原因注释（指回 :27-32 警告块）——**实证必需**：无 noqa 则 ruff check 红、`--fix` 会再改写（UP045 反咬实证见根因 4）；
3. 回归钉测两层：
   a. **形态钉**：断言 nodes.py 源码中 observe_node 签名不含 `RunnableConfig | None`（防任何 lint/现代化工具再次改写）；
   b. **行为钉**：带 `configurable.thread_id` 跑 supervisor 图至 HITL interrupt（mock LLM，承既有 test_hitl*/test_lg_rag_multi 夹具），断言落库审批单 `thread_id` 非空且等于 run 的 thread_id。

## 非范围

- 不动 `_thread_id_of` 判定逻辑、`_persist_hitl` 幂等/去重、resume 409 fail-closed 语义（空 thread_id 仍应 409——防呆正确）。
- 不动 ruff 配置（不加 per-file-ignores、不动 UP select）——用行级 noqa + 钉测，不改 lint 基线。
- 不回填/迁移存量空 thread_id 审批单（如 `hitl_fb4d74b23cca448aa120` 永不可 resume，属 #274 期损耗）；验收走新 run。
- `state["hitl_checkpoint_id"]` 从未被写入、落库 checkpoint_id 恒 NULL——resume 仅凭 thread_id 定位（`app/ops/hitl/router.py:436` 只查 thread_id），不阻塞本修复，另议另立。
- 前端 HitlApprovalCard decide→resume 链断（`docs/tasks/active/task_fix_hitl_card_resume_reentry.md` · 归属 ops-desk-web）是**独立第二断点**，不在本 task。
- 不改 `app/ops/lg_rag/` 其他节点签名与图谱分层。

## 验收标准

- [ ] 1. 形态钉测绿：源码断言 observe_node 签名为 `Optional[RunnableConfig]` 形态（`RunnableConfig | None` 出现于签名即红）。
- [ ] 2. 行为钉测绿：supervisor 图带 thread_id 跑至 HITL interrupt，落库审批单 `thread_id == run 的 thread_id`（非空）；修复前该测应红（先红后绿钉）。
- [ ] 3. `.venv/bin/ruff check app tests` 绿（钉版 ruff 0.15.21 · 禁用系统 ruff，承 PR #293 教训）；`.venv/bin/pytest tests` 全量不引入新红（基线 28 红口径承 task_supervisor_replan_error_feedback 维护者裁决，目标计数 1946+新增钉测）。
- [ ] 4.（40 live · 签收后执行）重跑「#2140 这个 issue 在说什么？调用write本地落盘结论」：新审批单 thread_id 非空 → 批准后 POST /resume 200 → t2 testing.write.echo 实际执行 → done{resumed}。本项同时补完 task A + NO_PROXY fix 合并验收 5 被本 bug 阻塞的「t2 执行 + 终态 done」两项。

## failure_paths

- UP045 反咬：无 noqa 的 `Optional[RunnableConfig]` 必被 ruff check 判红（2026-10-28 实证 exit 1）→ noqa 与签名同 commit，缺一即 CI 红。
- `ruff --fix` 会无视文件内警告注释自动改写 → noqa 条目 --fix 不动（钉测双保险）。
- 修复前行为钉测必须先红（证明钉的是真机制而非恒绿摆设）；若恒绿须返工检查 mock 是否绕过注入路径。
- 若 30 发现其他图节点也声明 config 且形态受害（全仓扫描结论之外），同形态同栓修复并在交付说明列出。
- 存量 approved 空 thread_id 单据 resume 仍 409（设计内防呆，非回归）——复跑新 run 验收，不追旧单。

## 给执行帽（30）必读

- `app/ops/lg_rag/multi/nodes.py:14`（future annotations）· `:27-32`（陷阱警告）· `:1884-1898` `_thread_id_of` · `:2019` 落库键 · `:2125` observe_node 签名 · `:2143-2155` 调用点。
- `app/ops/hitl/router.py:436`（resume 只查 thread_id 的 409 判定点）。
- 先例约束：.venv/bin/ruff 钉版 0.15.21（系统 ruff 0.9.10 UP038 假红教训）· .venv/bin/pytest（裸 python 缺 asyncpg）· 28 红基线（test_strategy_*/capability_* 等远域既有红）· 勿碰 `docs/arch-browser/dist/site-data.json`(M) 与 `docs/tasks/active/task_fix_hitl_card_resume_reentry.md`、`task_fix_observe_config_injection.md` 两个前会话草稿。
- 编码规范 `docs/standards/CODING_BACKEND_L2_v1_zh.md`。

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `fix-hitl-observe-node-config-injection` |
| **git_branch** | `fix/hitl-observe-node-config-injection` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | 形态钉（源码断言）+ 行为钉（HITL 落库 thread_id 非空 · 先红后绿）；不连真网 |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `none` |
| **graph_delta** | `n/a` |
| **wiki_delta** | `n/a` |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,30` |
| **invoke_retention_profile** | `minimal` |
| **close_pr_policy** | `required` |

### 自检结论

结构对齐本仓已合并 fix 先例（task_fix_no_proxy_bracket_ipv6_sanitize · PR #295）；元信息块预填含 wiki_delta（承 K4/lint-wiki-delta 首红教训）。dsh-coding-kit task lint PASS 零余项（仅 W2/W4 轻量提醒，bugfix 轨合法豁免）。

## 人工闸表

| 闸 | 状态 | 备注 |
|---|---|---|
| HG-AUDIT-R1 | approved | 2026-10-28 维护者签收（m00627「签收」；草案授权 m00603），00 转录 |
| HG-GRAPH-MODULES | n/a | 不动图谱分层 |
