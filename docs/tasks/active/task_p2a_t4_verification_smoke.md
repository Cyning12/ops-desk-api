---
title: P2a-T4 冒烟验证与验收落盘
---

# task_p2a_t4_verification_smoke

> **状态**：`active`（2026-11-16 落卡）

- 关联：issue Cyning12/ops-desk-workspace#23（m03064 夜间授权窗口）· 设计真源 08-p2a-tools-design.md（§3 / §6 / §7 T4 行 / §8）

## Harness 元信息

| 键 | 值 |
|---|---|
| **task_slug** | p2a-t4-verification-smoke |
| **wiki_delta** | 无（WikiTrack 零改动） |
| graph_change_layer | G-L0（零图谱改动 · 纯测试 + 文档波 · capability 行无新增） |
| review_hat | 20 |
| base | 96ccf902（T2 CLOSE merge sha） |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| HG-AUDIT-R1 | approved | 30 | 维护者夜间授权窗口（issue Cyning12/ops-desk-workspace#23 m03064）+ 08 设计终稿 §7 T4 行；R1 审查文 docs/harness/reviews/task_p2a_t4_verification_smoke_audit_R1_20261116.md 结论 GO |
| HG-GRAPH-MODULES | approved | 30 | 同上授权；零图谱改动（不新增一级模块 · 不增 implementedBy · 01_modules.md 零回写） |
| HG-PILOT-OPSDESK-GLAYER | approved | 30 | 同上授权；本单不触物理分层试点面 |

## 背景

P2a（面板工具化）第四波·关账波。T1 落列表双工具、T2 落聚合双工具、T3 落 MCP 映射设计（回灌三点 · 纯文档）。T4 验证总假设「Agent 读面板数据出结论」：CI 结构断言（plan-JSON 对 supervisor 面九枚 capability 的可选中性 + 四设计样例预期对照）+ 四样例真 LLM 冒烟（真 PG seed · 真 SSE · Langfuse/span 证据链）一次跑完，验收记录落 workspace 仓。

## 范围

1. tests/test_capability_supervisor_smoke_assertions.py（新文件 · **零 app/ 改动**）：
   - supervisor allowlist 恰好九枚钉死（strategy/config.py CAPABILITY_ALLOWLIST_BY_KEY["supervisor"] 逐名对照）；
   - 九枚逐枚 plan-JSON 可选中：mock LLM 返回合法 plan（subtasks[0].tool=<cid>）→ supervisor_node 保留 plan 不 fallback（表达力覆盖全 supervisor 面）；
   - 四设计样例 query → 预期 capability id 对照表钉死：「最近 issue 吞吐怎么样？」→ get_overview ·「open 的 PR 里哪些 CI 挂了？」→ query_pull_requests ·「模块 X 依赖哪些模块？」→ graph_snapshot ·「现在有哪些 open 的 bug？」→ query_issues；预期集 ∩ mock_* = ∅（§6 (f) 结构面）；
   - catalog 片段含全部九枚 id（plan-JSON 选择面可见性）。
2. 四样例真 LLM 冒烟（人工 · 30 帽执行 · 40 落证）：dev 库 seed（ops_repos/issues/pull_requests/sync_runs/scan_snapshots/graph_snapshots · tenant ops-desk-pilot）→ POST /api/ops/lg-rag/stream（mode=supervisor · 真 .env siliconflow）逐样例采 SSE 帧 + 面板 REST 端点同题对照 + Langfuse API 拉 tool_exec span（不可达则以 SSE 帧+span metadata 测试证据替代并登记偏差）→ §6 (a)-(f) 逐项判定 + 三级裁定。
3. 验收记录落 workspace 仓 docs/01-scope/03-general-agent/10-p2a-verification.md（四样例证据 + (a)-(f) 判定表 + 三级裁定 + 偏差清单）。

## 非范围

承 08 §8 与本波性质：app/ 任何改动（含 lg_rag 图/nodes.py · lookups.py · manifest/builtin.v1.yaml · strategy/config.py）· 图谱改动 · SSE 新帧 · 新依赖 · 新 DDL/索引 · 前端 · mock 退役 · description 修订与 mock description 收窄（失败处置触发时另波进行 · 不在本波）。T3 回灌三点：①已由本波钉死（plan-JSON 原 capability_id 选择）；②③ 属 P2b 面 · 本波不承载。

## 失败路径

| 场景 | 行为 |
|---|---|
| LLM 选错 capability | 唯一真实杠杆 = 修 description（另波 · 登记裁定依据） |
| mock_* 误选 | 收窄 mock description（另波） |
| plan-JSON 表达力归因失败 ≥1/4 | 触发 08 §3 FC 重估（重开关闭态条目） |
| 数据错（capability 与面板端点不同数） | 退回 T1/T2 查 adapter 口径 |
| Langfuse 本地不可达 | 以 SSE 帧序列 + span metadata 既有测试证据替代 (a) · 登记偏差 |
| 无浏览器/GUI | (b) 以面板 REST 端点（/api/ops/issues|pulls|overview|graph）同题对照替代 UI 截图 · 登记偏差 |

## 验收标准

- [ ] 结构断言新文件绿：allowlist 九枚钉死 · 九枚逐枚可选中 · 四样例预期对照钉死（预期集 ∩ mock_* = ∅）· catalog 九枚可见
- [ ] capability 电池十一件（T2 十件 + 本波新文件）全绿（五键 blank）
- [ ] 全量套件对拍：失败集与 base 96ccf902 同子集恒等（既有 .env 污染红 · CI 无 .env 为终裁）
- [ ] 四样例冒烟一次跑完 · (a)-(f) 逐项判定落盘 · 三级裁定明确（成立/部分成立/不成立）
- [ ] ruff check app tests 绿 · CI 四绿 · 零 app/ 改动 · 零新依赖/DDL/SSE 帧/图谱改动
- [ ] 验收记录落 workspace 10-p2a-verification.md（含偏差清单）

### 自检结论

（40 验收时回填）

## 必读

- ../ops-desk-workspace/docs/01-scope/03-general-agent/08-p2a-tools-design.md（§3/§6/§7 T4 行/§8）
- tests/test_lg_rag_supervisor_capability_catalog.py（mock LLM 范式真源）
- app/ops/lg_rag/multi/nodes.py（supervisor_node · _SUPERVISOR_CAP_FILTER）· app/ops/strategy/config.py（allowlist 九枚）
- docs/tasks/done/task_p2a_t2_panel_aggregate_tools.md（T2 模板与偏差先例）

## 思考轮控制

| 轮 | 结论 | early_stop |
|---|---|---|
| R0 勘察 | 见 invoke_20261116_10_draft.md 勘察定论 | false |
| R1 契约审查 | plan-JSON 形态 {subtasks:[{id,type:"tool",input,tool}]}（catalog 测试 :240-251 在案）· 合法 id 保留/非法 fail-closed 既有覆盖 · 本波零 app/ 改动 → 零契约变更 | false |
| R2 租户 | seed tenant=ops-desk-pilot（TENANT_A）· 冒烟会话默认 tenant 一致 · 结构断言无 ctx 面 | false |
| R3 图谱 | 零图谱改动（纯测试 + 文档波）· graph_change_layer G-L0 | false |
| R4 冒烟路径 | 端点现实 /api/ops/lg-rag/stream mode=supervisor（设计写 /api/ops/chat/stream 已 410 下线 · 偏差登记）· ci_status 已知值 success\|failure\|pending（设计样例写 failing · seed 用 failure） | false |
| R5 早停 | 设计终稿 §6/§7 即审计真源 · 结构断言全机断 · early_stop 成立 | true |

actual_last_round: R5

### R0

勘察定论见 invoke_20261116_10_draft.md：端点/模型/seed 面/帧词汇/Langfuse 配置/测试范式清点完毕；master 尖基线 2150 passed/16 failed（既有 .env 污染红 · 抽查三枚 blank LG_RAG 键后复绿证实因果）。

### R1

契约审查：plan-JSON 形态与 fail-closed 语义由既有 catalog 测试钉死；本波只新增断言不改契约；mock LLM 范式（SimpleNamespace(complete=async fn) + patch get_llm_provider/_record_span_metadata/trace_span）逐行复用。

### R2

租户裁定：seed 与冒烟会话同 tenant ops-desk-pilot；面板端点 tenant 强制（issues.py:47-51）与 capability tenant_scoped 三枚口径一致 · 对照有效。

### R3

图谱裁定：零新模块/边/implementedBy/capability 行；01_modules.md 零回写（承 G-L0 裁定）。

### R4

冒烟路径裁定：/api/ops/chat/stream 已 410（router.py:56 迁移指针）→ 现实路径 /api/ops/lg-rag/stream mode=supervisor；seed ci_status 用 failure（GitHub 惯例词 · manifest description 在案）；as_of 由 get_overview 必带。

### R5

早停裁定：设计终稿（08）即审计真源，结构断言全部可机断，R5 early_stop 成立。

## 实现备忘

（30 实施时回填）

## 测试策略

- InMemory 恒跑（CI）：结构断言全量（mock LLM 不连真外网）
- capability 套件先 blank 五键（OPS_HITL_PERSISTENCE= OPS_CAPABILITY_ALLOW_WRITE= OPS_CAPABILITY_ALLOW_WRITE_TAGS= OPS_CAPABILITY_PERSISTENCE= OPS_CAPABILITY_EXTRA_MANIFESTS=）
- 冒烟波另 blank LG_RAG_SUPERVISOR_PLAN_ON_FAIL=/LG_RAG_DELEGATION_TOKEN_MODE=/OPS_STRATEGY_EXTRA_CANDIDATE_CAPABILITY_IDS= 之外的键不动（真 .env 冒烟 · 但 LG_RAG_SUPERVISOR_PLAN_ON_FAIL=single_rag 会掩盖 plan fallback → (d) 判定读 span/帧证据）
- ruff check app tests

## 修订记录

- 2026-11-16 · 落卡（夜间授权窗口 · issue #23 m03064 + 08 §7 T4 行）
