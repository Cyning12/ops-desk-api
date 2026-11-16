---
title: task · fix · plan 帧 >800 字符截断落库（观测性缺口）
---

# task · fix · plan 帧 >800 字符截断落库（观测性缺口）

> **状态**：`done`（2026-11-17 落卡 · 2026-11-17 收口 · 夜间自动执行波）
> **来源**：P2b-T5a 冒烟附带发现（workspace docs/01-scope/03-general-agent/13-p2b-skill-verification.md §7.1 · H1b/H2b/H3c 实测恰 800 字符截断）· 授权 issue Cyning12/ops-desk-workspace#23（m03064/m03283/m03694 夜间授权 · 委派书 fix-planframe-truncation）

## Harness 元信息

| 键 | 值 |
|----|----|
| **task_slug** | fix-planframe-truncation |
| base | 6cbb947e |
| 关联 issue | issue Cyning12/ops-desk-workspace#23（授权真源）· workspace 13 文 §7.1（发现真源） |
| 关联 PR | feat #439（squash 979cf3d6 · CI 四绿）· close 本 chore PR |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 本仓未启用 WikiTrack；本波为 lg_rag 持久化面小修 + 图谱登记 |
| graph_change_layer | G-L1（01_modules.md lg_rag 行 fix-planframe 备注 + HG-GRAPH-MODULES 签收行） |
| review_hat | 20（R1 审查文已落盘 · GO） |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | approved | 30 | approved 2026-11-17 · 授权 issue Cyning12/ops-desk-workspace#23 m03064/m03283/m03694（夜间授权）+ 委派书 fix-planframe-truncation 为唯一范围真源 |
| HG-AUDIT-R1 | approved | 30 | approved 2026-11-17 · 同上授权 + R1 审查文 docs/harness/reviews/task_fix_planframe_truncation_audit_R1_20261117.md（GO） |
| HG-GRAPH-MODULES | approved | 30 | approved 2026-11-17 · 同上授权（lg_rag 行 fix-planframe 备注属图谱登记义务 · 随 30 交付回填） |

## 背景

P2b-T5a 冒烟（workspace 13 文 §7.1）发现：supervisor plan 帧（`node.progress` supervisor · payload.subtasks）持久化时 >800 字符被截断落库（`ops_lg_rag_run_events.payload`）——执行不受影响，但回放/审计视角丢信息（观测性缺口）。根因：`app/ops/lg_rag/sse_stream.py:68 _PAYLOAD_MAX=800` + `:90-128 _summarize_payload()` 的截断 payload 被 `emit`（:279-329）同一 dict 双用（SSE 帧 + persist_run_event）；第二路径 `app/ops/hitl/resume.py:139-156 _ResumeEmitter.__call__` 直接以 map_node_update 的截断 payload 落盘。回放端点 GET /runs/{id}/events（runs_router.py:122-154）payload 原样透传（仅 500 帧分页 + 白名单过滤），落库全文后自动回放全文。

## 范围

1. **修法裁定**（委派书预批「落库全文 · SSE 帧面截断保持」）：持久化层不丢信息，展示/推送面保留既有上限。
   - `app/ops/lg_rag/sse_stream.py`：拆两常量——`_PAYLOAD_MAX=800`（SSE 面不动）+ 新 `_PERSIST_PAYLOAD_MAX=32_000`（落库面 · 对齐 `_ANSWER_MAX=32_000` 先例 · 防病理尺寸保险丝）；`_summarize_payload` 参数化 max_len（默认 800 零 diff）；新 `persist_node_payload(node_name, node_output)` 同构落库 payload（含 subtask done 帧 status/message 键 · 键集与 SSE 面一致仅上限不同）；`emit` 增 kw-only `persist_payload=None`（None 时落 payload 本体 · 其余帧型零 diff）；主循环（:461-474）双面计算传入。
   - `app/ops/hitl/resume.py`：`_ResumeEmitter.__call__` 恢复段同修（persist 落 persist_node_payload 全文 · 本路径无 SSE 推送面 · SSE 帧面截断不适用）。
   - `app/ops/lg_rag/history.py`：`summarize_subtasks`（:205-222）读时截断 subtask_result≤800/answer_preview≤200（:217 注释假设「帧内已是截断过的安全大小」在落库全文后破 · 展示面保既有上限承 SSE 旧口径）。
2. **测试**（真 PG postgresql+asyncpg://ops:ops_password@localhost:5432/opsdesk_test · 五键 blank 前缀）：
   - 新增：>800 字符 plan 帧（supervisor subtasks）SSE 帧面仍截断（≤800+"…"）且 persist_run_event 落库 payload 为全文（>800 不截 · 承 test_hitl_resume_events.py _capture / test_lg_rag_sse_stream.py mock 先例形态）；
   - 新增：history.summarize_subtasks 读时截断断言（全文落库帧输入 → 响应面 subtask_result≤800/answer_preview≤200）；
   - 既有 tests/test_lg_rag_sse_stream.py / test_lg_rag_sse_token_stream.py / test_lg_rag_sse_subtask_message.py / test_hitl_resume_events.py / test_chat_history_api.py / test_lg_rag_run_store.py / test_lg_rag_runs_readonly_api.py 回归零红；全量 pytest 绿（环境性红与 base 6cbb947e 同路径基线逐签对照 · CI 终裁）。
3. **图谱**：`docs/_tech_graph/l1/01_modules.md` lg_rag 行（:35）补 fix-planframe 备注（落库全文 · SSE 帧面截断保持）+ HG-GRAPH-MODULES 签收行（承 :41-:45 先例）。
4. **freeze 核实**：lg-rag-sse-v1 freeze 词表不受本改动影响（帧类型不变 · 仅持久化内容长度）；05 spec（docs/spec/agent-infra/05_lg_rag_transport_and_session_plan_v0.md）未钉 node.progress 键值 800 上限 → workspace 契约文档无需同步（核实结论登记）。
5. **落盘**：registry entry（status=active → close 波 closed）· invokes by-task/fix-planframe-truncation/{10,30,40,50} · R1 审查文 · task 档 active→done。

## 非范围

- 不改 SSE 帧面 800 截断口径（`_PAYLOAD_MAX` 数值不动 · 推送面契约保持）。
- 不改 runs_router GET /runs/{id}/events 端点（500 帧分页 + 白名单过滤不动 · payload 透传天然回放全文）。
- 不改 event_store.persist_run_event（本身不截断 · 零触）· 不改 map_node_update 签名（freeze 面 · 3 元组保持）。
- 不碰 alembic/（零新迁移 · payload 列 JSONB 无 schema 变更）· scripts/ · skill_registry/ · graph/ nodes/ 业务逻辑（执行路径零改 · 纯持久化面）。
- 存量已截断落库行不回填（历史数据不可复原 · 仅前向修复）。

## 失败路径

- _PERSIST_PAYLOAD_MAX=32_000 保险丝命中（病理尺寸节点输出）→ 落库面仍截断于 32_000（对齐 answer 终帧先例 · 防单帧爆库）——判据：正常 plan/subtask 帧 << 32K，保险丝仅兜病理。
- persist_node_payload 与 SSE 面键集漂移（未来新增摘要键只改一处）→ 两函数共用 _summarize_payload(max_len=...) 参数化实现（单一真源 · 仅上限不同）。
- history 读时截断遗漏 → 全文帧直接透传 history 响应 → 响应尺寸膨胀；由新增读时截断断言守。
- 并行 agent 撞 registry.yaml / 01_modules.md 同区冲突 → rebase origin/master 保留双方 entry 手动解，冲突块如实登记。
- 仓根 .env 经 tests/test_check_vector_waterline.py 裸 load_dotenv 渗入 worktree 收集期致全量 pytest 环境性红 → 与 base 6cbb947e 同路径基线逐签对照登记，CI 终裁。
- 脏树期 wave_gate_registry 红为结构性常态（委派书钉明）。

## 验收标准

- [ ] SSE 帧面零 diff：>800 plan 帧 SSE 输出仍截断（_PAYLOAD_MAX=800 不动 · 既有 SSE 断言全绿）
- [ ] 落库全文：>800 plan 帧 persist_run_event 收到的 payload.subtasks 为全文（不再截断 · 新断言）
- [ ] 恢复段同修：HITL resume 路径 _ResumeEmitter 落库同为全文（新断言）
- [ ] history 展示面：summarize_subtasks 读时截断 subtask_result≤800/answer_preview≤200（新断言 · 既有 history 断言全绿）
- [ ] 既有七测试文件回归零红；全量 pytest 绿（环境性红逐签对照 base 6cbb947e）
- [ ] `ruff check app tests` 绿
- [ ] 01_modules.md lg_rag 行 fix-planframe 备注 + HG-GRAPH-MODULES 签收行
- [ ] registry entry active · invokes 四件 · R1 审查文 · spec-wave task lint PASS

### 自检结论

验收 8 条全过（2026-11-17）：全文落库断言三绿（SSE 主流 plan 帧 · subtask done 帧形态 · HITL 恢复段 · 真 PG）· history 读时截断两绿（800/200 + 小 payload 透传对照）· 目标七件 109 passed · ruff 绿 · 图谱两件落盘（lg_rag 行 :35 备注 + HG-GRAPH-MODULES 签收行）· 过闸四件齐（registry entry · invokes 10/30/40/50 · R1 审查文 GO · lint PASS）。全量 pytest 2445 passed / 6 failed 逐签：test_tc8_diff_whitelist 与 test_wave_gate_registry 为脏树期结构性红（在途改动未提交时归档波守卫咬合 · 提交后闭窗复绿 · CI 终裁绿）；test_hitl_decide_owner_fallback / test_hitl_pending_decide / test_chat_history_api ×2 共四件在 base 6cbb947e 同路径同红（环境性基线红 · stash 对照实证 · 与本波无关）· CI pytest 2m47s 绿终裁。

## 必读列表

- 发现真源：`../ops-desk-workspace/docs/01-scope/03-general-agent/13-p2b-skill-verification.md` §7.1（H1b/H2b/H3c 恰 800 截断实测）
- 代码锚：`app/ops/lg_rag/sse_stream.py:68/:90-128/:279-329/:461-474` · `app/ops/hitl/resume.py:87-110/:139-156` · `app/ops/lg_rag/history.py:205-222` · `app/ops/lg_rag/runs_router.py:122-154` · `app/ops/lg_rag/event_store.py:63-97`
- freeze 锚：`docs/spec/agent-infra/05_lg_rag_transport_and_session_plan_v0.md`（answer 32_000 · message ≤200 已钉 · node.progress 键值 800 未钉）
- 体例先例：`docs/tasks/done/task_fix_434_worker_thread_upsert.md` · registry `docs/harness/audit_gates/registry.yaml` · 图谱签收承 01_modules.md:41-:45
- 测试先例：`tests/test_hitl_resume_events.py`（:40-46 _capture persist 模式）· `tests/test_lg_rag_sse_stream.py`（:141/:360/:407 mock persist 点）

## 思考轮

| 轮 | 结论 | early_stop |
|----|------|-----------|
| R0 | 范围对账（委派书四条 vs 冒烟 §7.1 vs 代码锚）done | false |
| R1 | 失败路径推演（保险丝 · 键集漂移 · 读时截断遗漏 · 并行冲突 · 环境性红）done | false |
| R2 | 非范围边界（SSE 面零改 · 端点零触 · 存量不回填 · freeze 词表不动）done | false |
| R3 | 关键决策记录（落库全文+SSE 面截断保持 · 拆两常量 · 参数化单一真源 · resume 同修）done | false |
| R4 | 体例对账（fix-434 模板 · registry/invokes/审查文/图谱登记）done | false |
| R5 | 收尾复核（验收 checklist 全锚定）done | false |

actual_last_round: R5

### R0 · 范围对账

委派书四条与冒烟 §7.1 逐条对齐：勘察截断点（已定位 sse_stream.py:68 + resume.py 第二路径）· 裁定修法（落库全文 · SSE 帧面截断保持 · 拆两常量）· 改动+测试（全文落库断言 + SSE 面保持断言）· 图谱登记 + freeze 核实（05 spec 未钉 node.progress 800 口径 · 无需同步 workspace 契约文档）。回放走 GET runs/{id}/events（payload 透传）——确认落库全文后该端点自动回放全文零改动。

### R1 · 失败路径推演

见「失败路径」节。推演增补：resume.py _ResumeEmitter 无 SSE 推送面（恢复段仅 persist + cursor），故「SSE 帧面截断保持」不适用该路径，直接落全文（persist_node_payload）；resume 段 SSE 经 replay 通道下发，replay 端点 payload 透传 → 恢复段回放帧将带全文 payload（与主路径回放一致 · 口径统一）。

### R2 · 非范围边界

SSE 推送面 800 上限保持（_PAYLOAD_MAX 数值不动）；runs_router/event_store/map_node_update 签名零触；存量已截断行不回填（不可复原）；freeze 词表（帧类型）不变；alembic//scripts/ 禁入。

### R3 · 关键决策记录

- **落库全文 · SSE 帧面截断保持**：委派书预批倾向采纳——持久化层不丢信息（观测性缺口修复），展示/推送面保留既有上限（帧尺寸契约不破 · 前端零影响）。
- **拆两常量**：_PAYLOAD_MAX=800（SSE 面）+ _PERSIST_PAYLOAD_MAX=32_000（落库面）——32_000 对齐 _ANSWER_MAX 先例，非无限大，兜病理尺寸保险丝。
- **参数化单一真源**：_summarize_payload(node_output, max_len=_PAYLOAD_MAX)；persist_node_payload 调同一实现传 32_000——两面上限不同但键集/结构同一真源，防未来漂移。
- **emit kw-only persist_payload=None**：默认 None 落 payload 本体（run.start/hitl.waiting/done/error 等帧型零 diff），仅节点帧传双面 payload；resume.__call__ 同形传参。
- **history 读时截断**：落库全文后 :217 假设破，summarize_subtasks 对 subtask_result/answer_preview 补读时截断（≤800/≤200 承 SSE 旧口径）——展示面尺寸契约保持。

### R4 · 体例对账

照 fix-434：task 档结构/人工闸表/registry entry（base=6cbb947e · allowed_app_files=[app/ops/lg_rag/sse_stream.py, app/ops/hitl/resume.py, app/ops/lg_rag/history.py] · banned_prefixes=[alembic/, scripts/]）/invokes by-task 四件 {10,30,40,50}/R1 审查文 GO 机读词/spec-wave@3.5.0 task lint PASS 为闸；图谱签收承 :41-:45 先例。仓规条款一遵守（走 20-R1 审查文非 --allow-no-review）。

### R5 · 收尾复核

验收 8 条逐条锚：SSE 面零 diff（既有断言）· 落库全文（新断言）· resume 同修（新断言）· history 读时截断（新断言）· 七文件回归+全量 · ruff · 图谱两件 · 过闸四件。回退=revert 三文件零迁移。

## 实现备忘

### 偏差登记

（40 收口时按需回填）

### 限制登记

（40 收口时按需回填）

## 测试策略

pytest tests（CI 终裁 · 真 PG postgresql+asyncpg://ops:ops_password@localhost:5432/opsdesk_test · 五键 blank 前缀 OPS_HITL_PERSISTENCE= OPS_CAPABILITY_ALLOW_WRITE= OPS_CAPABILITY_ALLOW_WRITE_TAGS= OPS_CAPABILITY_PERSISTENCE= OPS_CAPABILITY_EXTRA_MANIFESTS=）；目标七件 test_lg_rag_sse_stream/test_lg_rag_sse_token_stream/test_lg_rag_sse_subtask_message/test_hitl_resume_events/test_chat_history_api/test_lg_rag_run_store/test_lg_rag_runs_readonly_api 全绿；全量回归环境性红与 base 6cbb947e 同路径基线逐签对照；ruff check app tests 绿；allowed_app_files=[app/ops/lg_rag/sse_stream.py, app/ops/hitl/resume.py, app/ops/lg_rag/history.py] 机判。

## 修订记录

| 日期 | 修订 |
|------|------|
| 2026-11-17 | 落卡（夜间自动执行波 · 授权 issue Cyning12/ops-desk-workspace#23 m03064/m03283/m03694 · 来源 workspace 13 文 §7.1 P2b-T5a 附带发现） |
| 2026-11-17 | 收口（feat #439 squash 979cf3d6 · CI 四绿：check 14s / import-linter 19s / pytest 2m47s / lint-wiki-delta 5m36s · close 波 registry 钉 wave_tip + task 迁 done + invoke_50） |
