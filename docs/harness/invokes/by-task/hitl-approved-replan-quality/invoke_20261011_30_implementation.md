---
hat: 30
task_slug: hitl-approved-replan-quality
date: 2026-10-11
---

# invoke · 30-implementation · hitl-approved-replan-quality（D1=C 混合案落地）

## 实施摘要

- **D1 裁定：C 混合案**（10 倾向承案 · 30 实证复现后维持）——读步去盲靠注入（B 面），写步安全靠结构（护栏面），不动 A 案图路径（改动最小 · 可机断性由护栏+TC 断言兜底）。
- **TC1 红测先行**（commit 9b56343 · 时序证据在 git 历史）：两枚对现码 RED → 本帽实现后转绿。
- **实现 commit ebe2a01**（feat · 5 文件 383+/17-）：
  - **注入去盲（B 面）**：`_build_supervisor_suffix_system` 增 `preserved_block` 槽（模板 lg_rag.supervisor.suffix.system **v1→v2** · README 与 test_prompt_assets :22/:36 同步）；`_format_preserved_block` 渲染保号行名单（空集合返空串零 diff）；`_format_prefix_block` 带 locked 步终态 output 摘要（json 截断 200 防爆）。破 SPEC §9 序1 现象①「LLM 不知晓保号行/已完成步产出」。
  - **write 孪生结构护栏（C 面 · 契约一核心红线）**：`_join_subtasks` 分发层 **先于签发检查**——`_guard_write_key` canonical（tool + sort_keys 规范化入参 · args 优先兼容 input · 仅 WRITE_SIDE_EFFECTS 注册能力 · 序列化失败/未注册返 None 不护栏）命中**异 sid 成功终态** → guard-skip：不派发 · 不消费审批单据 · 不产孤儿 HITL 单，output deepcopy 照抄原终态 + `write_replay_guard_skip`/`replay_of` 台账 + span metadata。同批双胞胎：首发照派、次发本轮挂起（不落任何终态），下一 join pass 见终态后 guard-skip（同轮重入结构前提 graph.py:94-103）。`_delegation_active()` off 模式整段不建索引零触达（承 off 零 diff 先例）。
- **TC2 边界组六枚**（同 commit）：FP-3 反面（批准步无终态可命中·正常消费派发）· 同 tool 异 args 不算孪生 · error 终态不拦（失败重跑系既有语义）· 同批双胞胎两段式 · off 零介入 · canonical 确定性+空保号空串。

## 契约自查（钉死契约五条）

| # | 契约 | 结论 |
|---|---|---|
| 1 | 已终态 write 步零重发（结构性） | ✅ 分发层 guard-skip 先于签发检查，TC1-a/TC2 组机断（不派发不消费+replay_of 台账） |
| 2 | 保号机制零回归（TB1-TB8） | ✅ test_hitl_approval_consumption 48 枚全绿；台账键（delegation_approval_consumed/hitl_persist_guard_skip 等）零字面改动；保号落位 [locked→preserved→新后缀] 契约 TC1-b 断言存续 |
| 3 | 手动/auto resume 双路径同口径 | ✅ 未触 resume.py:131 出口（done{completed} 钉案①非范围照登） |
| 4 | reject 路径零 diff | ✅ 未触 rejected 集合语义 |
| 5 | pytest 全量零新增红 | ✅ 1769 过/7 红/1 跳过——7 红与基线 9b56343 stash 对拍**逐枚一致**（环境性：仓根 .env 软链使 delegation ON + LG_RAG_HTTP_CHECKPOINTER=postgres 全进程 ON；dualproc×2 需跨实例 DB · asyncpg event-loop 系 fixture 环境噪音）；ruff 55 持平 master 基线（新码零新增，TC1 稿 4 枚 F401/F811/C416 一并 noqa/list() 收口） |

## 验收勾选口径

- TC1 ✅（红→绿时序在案）· TC2 ✅（六枚全绿）。
- TC3/TC5 live 实证依赖序2 merge（台账可见前提）→ 40 帽待办；TC4 反回归本帽已自跑全量对拍零新增红，40 终验复核待办。

## 执行环境备注

worktree 无独立 .venv/.env —— 按先例软链主仓（ln -s ../ops-desk-api/.venv · .env 同）；.env 使 LG_RAG_HTTP_CHECKPOINTER=postgres 全进程 ON，环境性红归因以基线对拍为准（契约五口径承先例）。

## 遗留偏差

- TC1-b 断言保号行 sid 入 prompt；注入文案为中文引导句（「切勿为同一目的再规划新步骤或孪生步骤」），LLM 遵守度靠结构护栏兜底（FP-1 口径：注入是优化、护栏是红线）。
- nodes.py import 块 I001 等 55 枚为 master 存量口径，本 task 不扩面整治。
- 40 帽（含 live 实证 TC3/TC5 + PR）本棒不做，待序2 merge 后另行组织。
