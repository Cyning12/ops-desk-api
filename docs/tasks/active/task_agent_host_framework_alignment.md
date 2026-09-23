# Task：Agent Host 完整框架大纲（复杂 Agent 进化主线裁定）+ _tech_graph 主线/legacy/dormant 标记追平（agent-host-framework-alignment）

> **状态**：`in_progress`（2026-09-23 · 维护者本窗直令开工：「更新当前项目 _tech_graph …结合 mermaid 进行框架分析大纲，针对大模块的思考，后续再考虑落地」）  
> **类型**：docs-only（图谱维护 + 讨论稿 · **零代码改动** · 零新路由/表/SSE 事件类型/列/索引）  
> **变更请求**：维护者本窗原话（即本 task 立项依据 · 承 task_tech_graph_recent_sync 「维护者令」先例）  
> **分支**：`task/agent-host-framework-alignment`（**禁止 master/main 直改**）

---

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `agent-host-framework-alignment` |
| **git_branch** | `task/agent-host-framework-alignment` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `docs-only` |
| **test_strategy_note** | 零代码改动；验证 = `./scripts/graph-compile.sh`（compile + check + normalize guard 全绿）+ 链接人工核读 |
| **code_quality_bar** | `n/a`（docs-only） |
| **graph_change_layer** | `G-L0`（00_main chat 节点 legacy 标注 + 描述主线裁定）+ `G-L1`（01_modules 行备注/人签新行 · 10_flow_chat 标题 legacy 标注）|
| **graph_delta** | 有（主线裁定入图谱 · legacy/dormant 标记 · strategy/skill_registry 路径覆盖补记 · 人签记录新行）|
| **graph_delta_note** | **回炉补闸条款**：若落地阶段偏离本裁定（新增/撤销一级模块 · 删代码 · 改 freeze 契约 · 新增路由/表/SSE 事件类型），不得沿用本裁定——退回 10-task 补闸 + `docs/_tech_graph/` 如实登记后方可续 |
| **wiki_delta** | `n/a` |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,30`（docs-only · 20/40 由 graph-compile check 与人工核读替代） |
| **freeze_id** | 无（不改 lg-rag-sse-v1 / lg-rag-http-v1 / lc-evidence-http-v1） |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | approved | 30 | 2026-09-23 · 维护者本窗直令开工（原话即立项依据 · 承 tech_graph_recent_sync 先例）|
| HG-AUDIT-R1 | approved | **30** | 2026-09-23 · docs-only 无代码面；维护者本窗授权（同令覆盖图谱维护类改动）|
| HG-GRAPH-MODULES | approved | **30** | 2026-09-23 · 00 代签（维护者令「更新当前项目 _tech_graph…标记为废弃」）：chat 行 legacy 标记 · lg_rag 行主线裁定 + strategy/skill_registry 路径补记 · 人签记录新行；**不新增/不撤销一级模块** |
| HG-PILOT-OPSDESK-GLAYER | n/a | 物理分层试点改码 | 本 task 不涉物理分层试点改码 |

---

## 背景与目标

主线裁定（维护者令原话）：「当前主线已经不再是简单的 rag agent，而是在向着一个复杂 agent 进化」。本 task 做三件事：

1. **图谱追平**：`docs/_tech_graph/` 反映主线裁定——chat 流式面 legacy（T6 410 已记 · 本次升模块级标记）、`app/ops/strategy/**` 与 `app/ops/skill_registry/**` 路径覆盖缺口补记（strategy 实扫被 `lg_rag/multi/graph.py` 消费 · skill_registry H5 stub 无运行时消费方仅自测试）。
2. **废弃标记约定**：legacy/dormant 面「只要不是针对性读取不会默认考虑」——读序层（README）+ 模块表层（01_modules）双层标注，代码/节点/边/indexes 一律不删（承 T6 先例）。
3. **框架分析大纲**：结合维护者所给 mermaid（**旧业务与系统报警业务场景先不考虑**）+ Agent Host 完整模块清单（五层 34 模块），产出大模块级对照与差距分析讨论稿；**不落地**，落地另起 SPEC/task。

## 非范围

- 任何 `app/` 代码改动（含删除 skill_registry / chat 历史代码）
- 新增/撤销一级模块；新增路由/表/SSE 事件类型/列/索引
- 大纲内任何模块的实现（委派网关令牌、可见集两阶段、LLM 工厂预算闸等均仅停留在大模块思考）
- 旧业务（admin sync → data 只读面）与系统报警场景的方案设计

## 验收标准

1. `docs/discussions/2026-09-23_agent-host-full-framework-outline_v0.md` 落盘：34 模块对照表（目标 → 本仓落点 → 已有/雏形/缺失/不适用）+ 三道防线映射 + 废弃/休眠清单 + 后续方向（大模块级）。
2. `docs/_tech_graph/l1/01_modules.md`：chat 行 legacy 标记 · lg_rag 行主线裁定与路径补记 · 人签记录新行（00 代签 · 维护者令留痕）。
3. `docs/_tech_graph/README.md` 读序增「legacy 非默认读」约定 + 大纲指针。
4. `docs/_tech_graph/l0/00_main.graph.yaml` 与 `l1/10_flow_chat.graph.yaml` legacy 标注后，`./scripts/graph-compile.sh` 全绿（compile + check + normalize guard）。
5. `docs/discussions/README.md` 归档列表新增行。
6. `git status` 仅含本 task 声明文件；零 `app/` 改动。

## failure_paths

| 路径 | 处置 |
|---|---|
| graph-compile check 失败（锚点/链接失效） | 回退 yaml 改动重跑；check 不过不交付 |
| 维护者对主线裁定有异议 | 大纲为讨论稿非 freeze · 修订讨论稿即可，图谱标记随修订 |
| 落地冲动（顺手改 app/） | STOP · 本 task docs-only · 落地另起 SPEC/task |
