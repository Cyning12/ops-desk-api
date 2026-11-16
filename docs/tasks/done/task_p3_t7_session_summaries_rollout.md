---
title: task · feat · P3-T7 ops_session_summaries 折叠摘要放量对拍
---

# task · feat · P3-T7 ops_session_summaries 折叠摘要放量对拍

> **状态**：`done`（2026-11-16 落卡 · 2026-11-16 收口 · 夜间自动执行波）
> **来源**：issue Cyning12/ops-desk-workspace#23（m03064/m03283/m03498/m03551 夜间授权 · 设计真源 workspace 14-p3-schedule-taskcard-design.md 终稿 R1-R23 §5/§10 · 契约真源 15-p3-contracts.md · 操作真源 lead 委派书）

## Harness 元信息

| 键 | 值 |
|----|----|
| **task_slug** | p3-t7-session-summaries-rollout |
| base | 87fd1ddf |
| 关联 issue | Cyning12/ops-desk-workspace#23 |
| 关联 PR | #430（squash merge 8569fa0e · CI 四绿）+ close wave PR（本 commit） |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 本仓未启用 WikiTrack；本波为纯 env 放量 + 文档/对拍，零代码改动 |
| graph_change_layer | G-L1（01_modules.md chat 行 P3-T7 放量备注 + HG-GRAPH-MODULES 签收行） |
| review_hat | 20（R1 审查文已落盘 · GO） |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | approved | 30 | approved 2026-11-16 · 授权 issue #23 m03064/m03283/m03498/m03551（夜间授权）+ 14 设计终稿 §5/§10 为唯一范围真源 |
| HG-AUDIT-R1 | approved | 30 | approved 2026-11-16 · 同上授权（14 终稿 + 15 契约即审计真源）+ R1 审查文 docs/harness/reviews/task_p3_t7_session_summaries_rollout_audit_R1_20261116.md（GO） |
| HG-GRAPH-MODULES | approved | 30 | approved 2026-11-16 · 同上授权（chat 行放量备注属图谱登记义务 · 随 30 交付回填） |

## 背景

P3（Schedule/TaskCard 面）治理线第 3 单。14 §5 裁定：session_summaries 本波只做「放量 + 验收对拍」，**零代码改动**——数据面早已齐备（表 models.py:348 OpsSessionSummary · 迁移 20260922_session_summaries · 写 summary.py:218 _write_cached_summary · 读 continuity.py:367 _assemble_with_session_summary · 降级 :387），`SESSION_SUMMARY_ENABLED` 默认关。叙事定位 R19：本项属治理/成本面，验收数据进 T11「治理放量结果」表。前置债 R-P3-6：Langfuse OTLP 403（dev 密钥失效）→ 对拍证据走录制替代路径（span metadata 由对拍脚本直接录制，不经 Langfuse）。

## 范围

1. **放量准备核实**：`SESSION_SUMMARY_ENABLED` 现状逐行核对（continuity.py:157-172 解析三态 · 默认 false · 非法回退 false+warning；summary.py 开关判定在装配侧 · 本面不读 env）；放量节奏按 14 §5 钉值 = off → pilot（灰度环境/内部 tenant）→ 全开，每步独立回退 = 关 env（承 P1-T5 RUNBOOK_goal_rollout_v1_zh.md 体例）。
2. **验收对拍**（本地真 PG localhost:5432 + dev 库 opsdesk · 合成标记 thread ≥30 turn · 用后删除级联清理）：同 thread on/off 双跑 `assemble_graph_messages_with_memory`——
   - ① token 预算对拍：三态（无折叠原文基线 / off 占位 / on 真摘要）装配 messages 条数 + 总字符数 + token 估算（仓内无 tiktoken · chars 为主判据 · 估算口径写入报告），压缩率判据 = on 态 vs 原文基线降 ≥50%（14 §5 判据进验收单）；
   - ② 答案质量对照：on 态摘要条人工抽检 3 条（关键实体保留 · 无信息断裂 · 三标记齐），记录落 invoke_40；
   - ③ chunk_hash 缓存命中观测：窗口稳定二次装配应命中缓存零 LLM 调用（provider 调用计数器 + span session_summary_cache_hits/generated 录制 + ops_session_summaries 行数不变 + 库存 chunk_hash == 重算值）；
   - ④ thread_id 缺失告警降级路径（continuity.py:387）实证回归（保留占位 + warning）。
3. **落盘**：
   - 放量 runbook `docs/guides/RUNBOOK_session_summary_rollout_v1_zh.md`（承 RUNBOOK_goal_rollout 三步体例：env 开法 / 回退=关 env 即时生效零迁移 / 观测指标 = span 三键 session_summary_generated|cache_hits|degraded + ops_llm_usage task_type=summary 账 + ops_session_summaries 行增速 + 降级率阈值）；
   - `.env.example` 注记 SESSION_SUMMARY_ENABLED + OPS_LLM_TIER_SUMMARY_MODEL 两键；
   - `docs/guides/GUIDE_env_inventory_v1.md` SESSION_SUMMARY_ENABLED 空备注回填 + OPS_LLM_TIER_SUMMARY_MODEL 备注补放量口径（86 键不变 · 仅回填备注）；
   - 图谱 `docs/_tech_graph/l1/01_modules.md` chat 行 P3-T7 放量备注 + HG-GRAPH-MODULES 签收行（承 :41/:42 先例）；
   - 验收对拍数据表进 invoke_40。
4. **测试**：开关行为测试缺口核对（既有 tests/test_session_summary.py 30+ 用例已覆盖 off 三态逐字节/on 三标记替换/全失败降级逐字节/thread_id 缺失/缓存命中零 LLM/hash 纪律/原文表零写入——核对结论落 invoke_30；有缺口才补）；全量回归（真 PG opsdesk_test · 五键 blank 前缀 · 环境性红与 base 87fd1ddf 基线逐签对照 · CI 终裁）。

## 非范围

- 不改折叠算法与摘要面本体：compress_window / summary.py / continuity.py 零改动（发现缺陷只登记）。
- 不做 L2 记忆三开关放量（MEMORY_FACTS_ENABLED / MEMORY_FACTS_EXTRACT_ENABLED / MEMORY_FACTS_VECTOR_RECALL_ENABLED——§4.3 节奏不在本波；T5 只交付端点，放量决策在维护者）。
- 不换 Langfuse 密钥（R-P3-6 维护者前置债 · 本波走录制替代路径）。
- 不碰 app/ 任何代码 · alembic/ · scripts/ · skill_registry/ · SSE/契约面。

## 失败路径

- 对拍脚本 LLM 调用失败/超时 → 该 chunk 降级占位（summary.py:316-330 既有语义）· 对拍数据如实记 degraded 数。
- 缓存读失败视同 miss 走生成链；缓存写失败 log + 本次仍用摘要（不挡主答）。
- on 态 thread_id 缺失 → 保留占位 + warning（continuity.py:387）。
- SESSION_SUMMARY_ENABLED 非法值 → 回退 off + warning（continuity.py:171）。
- 回退 = 关 env（零代码零迁移 · env 重读即时生效 · 进程内无状态 · 缓存表留库无害 off 态不读不写）。
- 并行 agent 撞 registry.yaml / 01_modules.md 同区冲突 → rebase origin/master 保留双方 entry 手动解，冲突块如实登记。
- 仓根 .env 经 tests/test_check_vector_waterline.py 裸 load_dotenv 渗入 worktree 收集期致全量 pytest 环境性红 → 与 base 87fd1ddf 同路径基线逐签对照登记，CI 终裁。

## 验收标准

- [x] 对拍数据表落 invoke_40：同 thread ≥30 turn 三态（原文基线/off 占位/on 真摘要）装配 messages 条数 + 总字符数 + token 估算；on 态 vs 原文基线字符降 ≥50%
- [x] 缓存命中实证：on 态二次装配 span 录制 session_summary_cache_hits=12 · session_summary_generated=0 · provider 零调用 · ops_session_summaries 行数不变；库存 chunk_hash 与重算 sha256 逐条一致
- [x] 3 条 on 态摘要条人工抽检记录落 invoke_40（关键实体保留 · 三标记 `[历史摘要 · v1 · N 轮 · 模型:... · 有损压缩...]` 齐 · 无信息断裂）
- [x] thread_id 缺失降级实证：on 态 thread_id=None → 输出与 off 逐字节一致 + warning 日志（continuity.py:387）
- [x] RUNBOOK_session_summary_rollout_v1_zh.md 落盘：三步放量（off→pilot→全开）+ env 开法 + 回退命令 + 观测指标四面（span 三键/usage 账/缓存行增速/降级率）
- [x] .env.example 两键注记 + GUIDE_env_inventory SESSION_SUMMARY_ENABLED/OPS_LLM_TIER_SUMMARY_MODEL 备注回填
- [x] 01_modules.md chat 行 P3-T7 放量备注 + HG-GRAPH-MODULES 签收行
- [x] `pytest tests/test_session_summary.py tests/test_lg_rag_session_continuity.py tests/eval/test_session_summary_fidelity.py` 目标测试绿；全量回归环境性红与 base 基线逐签对照登记
- [x] `ruff check app tests` 绿（零代码改动仍跑）

### 自检结论

**PASS（2026-11-16 · 40 收口）**：九条验收全过——真源对拍（dev 库 40 轮拟真 thread · 真模型 DeepSeek-V4-Flash）on vs 原文基线 chars −51.1% / est_tokens −51.3%（≥50% ✅ · L2 漂移已登记）；缓存二跑 16/17 命中零 LLM 逐字节一致（1 chunk 连续两次 >60s 超时维持占位 · 降级语义正确 · run1 12/12 全等 hash 对账证函数级一致）；3 条抽检实体全保留；thread_id 缺失与 off 逐字节一致 + warning；RUNBOOK/.env.example/GUIDE/01_modules 四面齐；目标测试 17+全量 2436 绿；ruff 绿。偏差 D1（Langfuse 403 录制替代 · span 键名以 summary.py:346-352 为准）· D2（chars 主判据）· D3（base 说明）终态登记。数据详表见 invoke_20261116_40_verify.md · 收口见 invoke_20261116_50_close.md。

## 必读列表

- 设计真源：`../ops-desk-workspace/docs/01-scope/03-general-agent/14-p3-schedule-taskcard-design.md` 终稿（R1-R23 · §5 D-E · §10 任务切分 T7 行 · §11 失败路径）
- 契约真源：`../ops-desk-workspace/docs/01-scope/03-general-agent/15-p3-contracts.md`（commit 62af6ea · 本波无契约修订）
- 模块真值：`app/ops/session/README.md`（env 表/缓存 key 铁律/故障语义/灰度纪律）· SPEC `docs/spec/session-summary-fallback/SPEC-session-summary-fallback_v1.md`（signed 2026-09-22）
- 体例先例：`docs/guides/RUNBOOK_goal_rollout_v1_zh.md`（P1-T5 三步放量）· `docs/tasks/done/task_p3_t2_schedule_ddl_rest.md` · registry `docs/harness/audit_gates/registry.yaml`
- 代码锚：`app/ops/lg_rag/continuity.py:54 compress_window · :157 session_summary_enabled · :367 _assemble_with_session_summary · :387 降级` · `app/ops/session/summary.py:218 _write_cached_summary · :263 summarize_placeholders` · `app/db/models.py:348 OpsSessionSummary`

## 思考轮

| 轮 | 结论 | early_stop |
|----|------|-----------|
| R0 | 范围对账（委派书 vs 14 终稿 §5/§10 T7 行）done | false |
| R1 | 失败路径推演（降级链/缓存故障/回退/env 非法值）done | false |
| R2 | 非范围边界（折叠算法零触 · L2 三开关 · Langfuse 密钥）done | false |
| R3 | 关键决策记录（对拍三态口径 · 录制替代路径 · chars 主判据 · 合成 thread 清理）done | false |
| R4 | 体例对账（T2/T3 模板 · registry/invokes/审查文/图谱登记）done | false |
| R5 | 收尾复核（验收 checklist 全锚定）done | false |

actual_last_round: R5

### R0 · 范围对账

委派书四条范围与 14 §5 验收口径四条（token 对拍/对照会话/缓存命中/:387 降级回归）+ §10 T7 行（token 对拍脚本+对照会话+缓存命中观测 · 放量 runbook · 压缩率报告+3 条对照会话记录）逐条对齐；T7 依赖=T1（契约文档已交付）+ 前置 Langfuse 密钥（R-P3-6 未偿 → 录制替代路径登记偏差）。非范围「不改折叠算法 · 不做 L2 开关放量」与委派书一致。

### R1 · 失败路径推演

见「失败路径」节。推演增补：对拍合成 thread 中途失败 → 脚本 finally 删除 thread（FK CASCADE 清 turns/summaries）；on 态 12 chunk 部分 LLM 失败 → degraded 记数不阻塞，压缩率按实际摘要条计；dev 库 ops_llm_usage 写入失败 → record_llm_usage 不挡主答（usage.py:140 计数）仅影响usage 账观测，改用 provider 计数器兜底。

### R2 · 非范围边界

折叠算法/compress_window/summary.py/continuity.py 零触（allowed_app_files=[] 机判守）；MEMORY_FACTS 三开关不动（§4.3 为后续波）；Langfuse 密钥更换属维护者；web/iOS 面无涉；scripts/ alembic/ 禁入。

### R3 · 关键决策记录

- **三态对拍口径**：off 占位与 on 真摘要双跑外，加「无折叠原文基线」（max_full_turns 调到 ≥ 轮数直取原文）作分母——14 §5「窗口外 turn 折叠后 token 降 ≥50%」的压缩率分母只能是原文基线（off 占位本身已折叠，off vs on 差异是摘要信息量开销非压缩率）。
- **录制替代路径**：Langfuse 403 未偿 → span metadata（session_summary_generated/cache_hits/degraded）由对拍脚本包装 update_current_span_metadata 直接录制（只录不改行为），usage 账查 ops_llm_usage task_type=summary 行。
- **chars 主判据**：仓内无 tiktoken/requirements 不引新依赖 → 总字符数为精确主判据，token 估算（chars/4 英文 · 中文按字近 1 token 混合口径）为辅并标注口径；判据 ≥50% 用 chars 判。
- **合成 thread 内容**：32 轮拟真运维排障对话（user/assistant 交替 · 含实体：服务名/版本号/错误码/时间戳），供抽检「关键实体保留」有判据；用后 DELETE thread 级联清三表。
- **registry allowed_app_files=[]**：纯 env 放量零代码机判守（app/ 任何改动即 banned）。

### R4 · 体例对账

照 T2/T3：task 档结构/人工闸表/registry entry（base=87fd1ddf · allowed_app_files=[] · banned_prefixes=[alembic/, scripts/]）/invokes by-task 四件 {10,30,40,50}/R1 审查文 GO 机读词/spec-wave task lint PASS 为闸；runbook 承 RUNBOOK_goal_rollout_v1_zh.md 三步体例；图谱签收承 :41/:42 先例。仓规条款一遵守（走 20-R1 审查文非 --allow-no-review）。

### R5 · 收尾复核

验收 9 条逐条锚到 invoke_40 数据表/文件证据/测试锚；回退路径=关 env（回退铁律是模块上线前提 · README 钉死）。

## 实现备忘

### 偏差登记

- **D1（Langfuse 前置债 · R-P3-6）**：Langfuse OTLP 403（dev 密钥失效 · traces 止 2026-10-29）未偿 → 对拍 span 证据走录制替代路径（脚本包装 update_current_span_metadata 录制三键 · 不经 Langfuse）；密钥更换留维护者。
- **D2（token 计数口径）**：仓内无 tiktoken · 不引新依赖 → 压缩率主判据=总字符数（精确可复算），token 估算为附注口径（混合文本 chars≈tokens 量级估计）；与 14 §5「ops_llm_usage/span 导出」口径的偏差：usage 账只含摘要生成调用本身的 prompt/completion tokens，主答装配 budget 以 chars 对拍代之。
- **D3（base 说明）**：委派书钉 base=87fd1ddf · 与 origin/master 尖一致（本地 master 滞后 origin 两提交 · 以 origin 为真源）。

### 限制登记

- **L1（单 env 全局开关）**：SESSION_SUMMARY_ENABLED 为进程级全局开关，无 per-tenant 门控——「pilot tenant 灰度」落地形态=灰度环境/内部实例先开（承 GOAL_INJECT 第②步体例），生产多租户混部面需以环境隔离实现 pilot。
- **L2（压缩率判据环境性）**：≥50% 判据在合成 32 轮运维对话上实测；生产会话轮长分布不同压缩率会漂移，runbook 观测口径以 span/usage 长期趋势为准。

## 测试策略

pytest tests（CI 终裁 · 真 PG postgresql+asyncpg://ops:ops_password@localhost:5432/opsdesk_test · 五键 blank 前缀）；目标三件 tests/test_session_summary.py + tests/test_lg_rag_session_continuity.py + tests/eval/test_session_summary_fidelity.py 全绿；全量回归环境性红（仓根 .env 经 test_check_vector_waterline.py 裸 load_dotenv 渗入 · 委派书已预警）与 base 87fd1ddf 同路径基线逐签对照；ruff check app tests 绿；零代码改动（allowed_app_files=[] 机判）。

## 修订记录

| 日期 | 修订 |
|------|------|
| 2026-11-16 | 落卡（夜间自动执行波 · 授权 issue #23 m03064/m03283/m03498/m03551） |
| 2026-11-16 | 收口：验收 9/9 过 · PR #430 squash merge 8569fa0e（CI 四绿）· 转 done · registry closed |
