# Task：Capability · 本库 Issue/PR 只读 lookup（真实 local_fn）

> **状态**：completed（2026-08-28 · 00 机械验收 PASS）  
> **类型**：feature / capability  
> **前置**：H2 Policy · S3 manifest · 现有 `OpsIssue` / `OpsPullRequest`  
> **并行**：`ops-sync-sender-migration` **勿混改**（数据新鲜度另轨；本波读库即可，可为空/过期）  
> **后置**：本 task 与 sync **均 CLOSE** 后再开 Eval E0/E1  
> **分支**：`task/ops-pg-lookup-capabilities`  
> **无关**：勿拉回 `docs/tasks/deferred/` 两条 RAG；禁止 MCP；禁止 GitHub 热路径 API；禁止改 `chat/graph.py` 拓扑。

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `ops-pg-lookup-capabilities` |
| **git_branch** | `task/ops-pg-lookup-capabilities` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | 夹具插入 OpsIssue/OpsPR；ainvoke 命中/未命中；tool_exec 走 Gateway；无外网 |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `G-L1` |
| **graph_delta** | `docs/_tech_graph/l1/01_modules.md` · `docs/_tech_graph/l1/10_flow_capability.graph.yaml` |
| **graph_delta_note** | `capability` 行备注：本库 issue/PR 只读 lookup；不新增一级模块；**不**改 lg_rag 图拓扑 |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 契约在 spec/capability；无 coding_wiki 条文变更 |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,30` |
| **invoke_retention_profile** | `default` |
| **freeze_id** | 无 |
| **orchestration** | 真实 capability 第一棒；sync 另 task |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| HG-TASK-DRAFT | approved | 22-R1 | 2026-08-28 · **00 代签 · 维护者令新增能力并统筹**（R1 pass） |
| HG-AUDIT-R1 | approved | 30 | 2026-08-28 · **00 代签** · 见 `docs/harness/reviews/task_ops_pg_lookup_capabilities_audit_R1_20260828.md` |
| HG-GRAPH-MODULES | approved | 30 | 仅 G-L1 `capability` 备注 + flow；不新增一级模块 · **00 代签** |

---

## 背景与目标

默认目录三枚：`utc_now_iso` **已是真时间**；`mock_get_*` 为罐头。Supervisor 需要能查 **本仓 PG** 的 Issue/PR（HTTP data 层已有表），不经三方 MCP、不经 GitHub 热路径。

---

## 范围 / 非范围

**范围**：

- 新增 `get_issue_by_number` · `get_pr_by_number`（`kind=local_fn` · `risk_level=low`）
- 写入 `builtin.v1.yaml` + `_DEFAULT_SPECS`；**保留**两枚 mock 与 `utc_now_iso`（测试与回退）
- payload：从字符串解析 **第一个整数**（`#128` / `128` / 含数字的短句）；解析失败或未命中 → `ok=False`，不抛垮 tool_exec
- 返回：number / title / state / html_url / updated_at / labels 或 ci_status 等摘要；**不**返回 `raw_payload`；body 最多 500 字
- 多 repo 同号：取 `updated_at` 最新一条
- Gateway **`ainvoke`**：adapter 若为 coroutine 则 await；否则兼容现有 sync `invoke`；`tool_exec_node` 改走 `ainvoke`（P-13，禁止在 async 节点里同步打 PG）
- 单测夹具 + G-L1 备注 + graph-compile + ruff

**非范围**：

- MCP / sandbox / cli / skill / GitHub API  
- 改 mock 语义；改 Builder Policy；改 chat/router/basic/supervisor **拓扑**  
- sync sender、Eval E0/E1、两条 deferred RAG  
- 部署/环境真实 tool（仍无数据源）

### 00 定夺

| 项 | 值 |
|---|---|
| 落点 | `app/ops/capability/lookups.py`；manifest adapter 前缀扩到 `local_fn:app.ops.capability.lookups:<attr>`（**仍仅此二前缀**，defaults 保留） |
| 会话 | `AsyncSessionLocal`；只读 select |
| 空库 | `ok=False` + 明确 error（如 `issue_not_found`） |
| 新鲜度 | 本波不保证日更；依赖并行 sync task |

---

## 验收标准

- [x] 夹具写入后 `ainvoke("get_issue_by_number", "#N")` 命中摘要字段
- [x] 不存在的 number → `ok=False`，tool_exec 记 error 不中断图
- [x] `get_pr_by_number` 对称
- [x] `utc_now_iso` / mock 回归不破
- [x] `tool_exec_node` 对 lookup 走 async，不在事件循环同步连 PG
- [x] builtin YAML 含新 id；非法 adapter 前缀仍整文件失败
- [x] G-L1 `capability` 备注 + graph-compile；`chat/graph.py` 与 `lg_rag/multi/graph.py` 拓扑 0 diff（允许 tool_exec **调用**改 ainvoke，禁止改边）
- [x] ruff / pytest 触及路径绿

---

## failure_paths

| 触发 | 行为 | 可重试 |
|---|---|---|
| payload 无整数 | `ok=False` · error 说明需 issue/PR 号 | N |
| 库中无该 number | `ok=False` · `not_found` | N |
| DB 连接失败 | `ok=False` · error 截断进 span | 上层可记子任务 error |
| 同号多 repo | 最新 `updated_at` | N |

---

## test_strategy

```text
required · 夹具 PG · 不连外网
pytest：lookups ainvoke / 未命中 / manifest / tool_exec 与 mock 回归
ruff 触及路径
./scripts/graph-compile.sh
chat/graph.py 与 multi/graph.py 拓扑 0 diff
```

---

## 自检结论

> 2026-08-28 · 00 机械复检 · **PASS**

- [x] pytest 绿集 63 passed（1 skipped · langchain.debug smoke 非本棒）
- [x] ruff 0 · `chat/graph.py` 与 `multi/graph.py` 拓扑 0 diff
- [x] 验收勾选 lookup / ainvoke / mock 回归

**50 结论**：PASS · 下一棒仍为 `ops-sync-sender-migration`（须人拍板 sender 方案）；**勿**开 Eval

---

## CLOSE

| 项 | 内容 |
|---|---|
| 日期 | 2026-08-28 |
| 定稿 | 本库 get_issue_by_number / get_pr_by_number；Gateway ainvoke；保留 mock |
| 归档 | `docs/tasks/done/task_ops_pg_lookup_capabilities.md` |
| PR | 待开 |

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-08-28 | 00 拆 task · R1 pass · HG 代签 · 本波只做 lookup 不加 MCP |
