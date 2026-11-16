---
title: RUNBOOK · 会话折叠摘要放量（SESSION_SUMMARY_ENABLED 三步灰度）
version: v1
date: 2026-11-16
status: active
owners: [ops]
related:
  - app/ops/session/README.md
  - docs/_tech_graph/l1/01_modules.md
  - docs/spec/session-summary-fallback/SPEC-session-summary-fallback_v1.md
  - docs/guides/RUNBOOK_goal_rollout_v1_zh.md
design: ops-desk-workspace docs/01-scope/03-general-agent/14-p3-schedule-taskcard-design.md（§5 D-E · §10 任务切分 T7 行）
---

# RUNBOOK · 会话折叠摘要放量（SESSION_SUMMARY_ENABLED 三步灰度）

## 0. 功能面速览

| 件 | 位置 | 交付波 |
|----|------|--------|
| ops_session_summaries 缓存表 | app/db/models.py:348 OpsSessionSummary · migration 20260922_session_summaries | session-summary-fallback（2026-09-22） |
| 占位折叠（窗口压缩） | app/ops/lg_rag/continuity.py:54 compress_window（max_full_turns=6 · group_size=2 · head 折占位条） | lg_rag T3 |
| 真摘要懒生成 + 缓存读写 | app/ops/session/summary.py（:218 _write_cached_summary · :263 summarize_placeholders · chunk_hash=sha256(prompt_version+model+canonical JSON)） | session-summary-fallback |
| 装配接线 + 降级 | app/ops/lg_rag/continuity.py:367 _assemble_with_session_summary · :387 thread_id 缺失降级 | session-summary-fallback |
| env 解析 | app/ops/lg_rag/continuity.py:157 session_summary_enabled（默认 false · 非法值回退 false+warning） | session-summary-fallback |

**总闸**：`SESSION_SUMMARY_ENABLED`（env · 默认 off）。闸 off = 装配面与占位模式**逐字节一致**（零 LLM 调用 · 零缓存表读写 · 摘要面零触达）。闸 on = 窗口外历史占位条替换为真摘要（逐 chunk 懒生成 · 缓存命中零 LLM · 单 chunk 失败降级保留该占位不挡主答）。

**限制（L1）**：本闸为**进程级全局开关**，无 per-tenant 门控。「pilot 灰度」的落地形态 = 灰度环境/内部实例先开（承 GOAL_INJECT 第②步体例）；生产多租户混部面须以环境隔离实现 pilot。

## 1. 三步放量

### 第①步：默认 off（交付态）

- 配置：不设置 `SESSION_SUMMARY_ENABLED`（或显式置 `=0`）。
- 预期：ops_session_summaries 零行增长；装配 off 态与占位模式逐字节一致（tests/test_session_summary.py off 三态逐字节用例守护 · 基线 47 passed）。
- 适用：上线初期 / 观察期（本波交付态即此步）。

### 第②步：灰度（单环境/内部实例开闸）

- 配置：灰度环境 `SESSION_SUMMARY_ENABLED=1`（可选 `OPS_LLM_TIER_SUMMARY_MODEL` 钉摘要档模型；留空跟随策略包/目录默认）。
- 动作：内部会话累积 ≥8 轮（超过 max_full_turns=6 窗口 + 至少 1 个 group_size=2 chunk）后追问，触发首次摘要生成；同 thread 窗口稳定期再追问，验证缓存命中。
- 观测点：
  1. span 三键 `session_summary_generated / session_summary_cache_hits / session_summary_degraded`（经 Langfuse；本地不可用时由对拍脚本录制替代 —— 偏差 D1）——首次装配 generated>0，**窗口稳定二次装配应 generated=0 且 cache_hits>0**；degraded 出现率应 ≈0，持续出现先回退再排查；
  2. usage 账 `ops_llm_usage` `task_type=summary` 行（summary 档模型调用归因 · run_id 可为空属预期——摘要懒生成在装配路径非 run 上下文）；
  3. `ops_session_summaries` 行增速（每新窗口外 chunk 至多 1 行 · 窗口稳定 0 增长；暴涨 = hash 漂移，查摘要档模型/prompt_version 是否变动）；
  4. 压缩率抽查：同 thread on 态装配总字符 vs 原文基线应降 ≥50%（对拍判据见本波 invoke_40 数据表；生产轮长分布不同会漂移，以长期 span/usage 趋势为准 —— 限制 L2）；
  5. 原文零污染：`ops_lg_rag_turns` **不应**出现 `[历史摘要` 字样（摘要是装配层替换，不落盘）。
- 通过标准：灰度 ≥3 天 · degraded ≈0 · 二次装配缓存命中 · 压缩率达标 · turns 表零摘要条污染。

### 第③步：全开

- 配置：生产 `SESSION_SUMMARY_ENABLED=1`。
- 观测点同第②步，加：摘要档成本趋势（ops_llm_usage task_type=summary 每日 token/成本增量 vs 主答装配节省）；degraded 长期趋势（摘要档 LLM 稳定性）。

## 2. 回退

任意阶段回退 = 移除/置空 `SESSION_SUMMARY_ENABLED` 并重启进程（或滚动发布）。

- **秒级生效**：闸判定在装配路径运行时读取（continuity.py:157 session_summary_enabled()），无缓存。
- **零代码零迁移**：ops_session_summaries 存量行保留无害（闸 off 后不读不写）；如需彻底清理可 DELETE，不影响任何链路。
- **回退铁律**（模块上线前提 · app/ops/session/README.md 钉死）：关 env 后装配输出与「从未开过」逐字节一致，有测试守护。

## 3. P3-T7 验收口径对照（14 §5）

| # | 验收口径 | 实证位置 |
|---|----------|----------|
| 1 | ≥30 turn on/off 双跑 token 对拍（窗口外折叠后降 ≥50%） | 本波 invoke_40 对拍数据表（三态：原文基线 / off 占位 / on 真摘要 · chars 主判据 + token 估算附注） |
| 2 | 3 条对照会话抽检（关键实体保留 · 无信息断裂） | 本波 invoke_40 抽检记录 |
| 3 | chunk_hash 缓存命中观测（窗口稳定二次装配零 LLM 调用） | 本波 invoke_40：cache_hits=12 · generated=0 · 库存 hash 重算逐条一致 |
| 4 | thread_id 缺失降级（continuity.py:387）回归 | 本波 invoke_40：on 态 thread_id=None → 与 off 逐字节一致 + warning |

## 4. 故障排查

| 症状 | 排查 |
|------|------|
| session_summary_degraded 持续 >0 | 摘要档 LLM 超时/错误（SUMMARY_TIMEOUT_S=60 · provider 连通性 · `OPS_LLM_TIER_SUMMARY_MODEL` 指向模型是否可用）；单 chunk 失败只保留该占位不挡主答——但持续 degraded 说明摘要面整体不可用，先回退关闸再排查 |
| ops_session_summaries 行暴涨 | hash 漂移：chunk_hash=sha256(prompt_version+model+canonical JSON)，摘要档模型切换/prompt 版本 bump 会全量重 hash（属预期一次性重建）；非预期暴涨查会话内容是否被非确定性字段污染 |
| on 态装配字符未降 | 会话不足窗口（<8 轮无折叠 · max_full_turns=6 + group_size=2）；或 thread_id 缺失走 :387 降级（查 warning 日志） |
| turns 表出现 `[历史摘要` | 装配面被改动（摘要落盘=污染）——回退关闸并审查 continuity.py/summary.py diff |
| 缓存行 FK 报错 | thread 删除应级联清 summaries（FK ON DELETE CASCADE · models.py:348）；报错说明迁移未应用或外键被绕 |

## 5. 观测指标速查

| 指标 | 来源 | 健康口径 |
|------|------|----------|
| session_summary_generated | span metadata | 首次装配 = 窗口外 chunk 数；窗口稳定后 = 0 |
| session_summary_cache_hits | span metadata | 窗口稳定二次装配 = 窗口外 chunk 数 |
| session_summary_degraded | span metadata | ≈0 |
| 摘要档 token/成本 | ops_llm_usage task_type=summary | 随会话量线性；窗口稳定期零增长 |
| 缓存行增速 | ops_session_summaries count | 每新窗口外 chunk ≤1 行；窗口稳定 0 增长 |
| 压缩率 | 装配总字符 on vs 原文基线 | ≥50%（≥30 turn 会话 · 本波对拍判据） |
