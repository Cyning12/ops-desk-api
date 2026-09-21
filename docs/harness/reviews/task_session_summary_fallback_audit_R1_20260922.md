# Task 审查（R1）：session-summary-fallback · 20-task-audit

## 元信息

| 项 | 内容 |
|----|------|
| **帽** | 20-task-audit（书面审 · 不实现代码 · 不代签人闸） |
| **日期** | 2026-09-22 |
| **轮次** | R1 |
| **被审对象** | `docs/tasks/active/task_session_summary_fallback.md`（10-task 落稿 · commit aa29b31） |
| **对照基准** | `docs/spec/session-summary-fallback/SPEC-session-summary-fallback_v1.md`（signed · HG-SPEC-SIGNOFF=approved 2026-09-22 · commit 48ce63e） |
| **分支核验** | `git branch --show-current` = `task/session-summary-fallback` ✓（真跑） |
| **工作目录** | `/Users/cyning/Desktop/Ops-desk/ops-desk-api` |

## 结论摘要

- **内容审查结论：通过**（内容零阻塞 · 验收 26 条全可执行断言化 · 与 SPEC 实质零差异）
- **流程闸状态**：HG-AUDIT-R1 = **pending**（blocks 30 · 维护者签闸后方可 30 · 本帽不签）
- **图谱闸状态**：HG-GRAPH-MODULES = approved（模块表已建置 · 本帽亲读复核成立）+ 本 task 新签义务（db 行新表登记 + lg_rag/chat/llm 行备注 + 人签记录新行留 00 代录位）条款在案 · 偏离回炉补闸条款在案

## 对照 SPEC 逐项核对

### 范围 D1–D5（SPEC §2 → task 范围节）

| 块 | SPEC §2 | task 范围节 | 核对 |
|----|---------|-------------|------|
| D1 生成通路 | 懒生成 L1 · summary 档 T2 · prompt 资产 · 三标记 · 超时单 chunk 降级 | 同左逐字承接 | 一致 ✓ |
| D2 缓存与版本归因 | C1 独立表 `ops_session_summaries` · key=内容哈希+prompt_version+model · 唯一约束 (thread_id, chunk_hash) · FK CASCADE | 同左逐字承接 | 一致 ✓ |
| D3 一键回退 | 默认关 · 非法值回退 warning · off/on-全失败双对拍逐字节 · 灰度纪律 | 同左逐字承接 | 一致 ✓ |
| D4 保真度金样 | sentinel must_keep/must_not_add 正反双断言 + 空摘要假通过防线 · 热路径零 LLM-as-judge | 同左逐字承接 | 一致 ✓ |
| D5 表结构/图谱/文档 | alembic 建表可逆 · 图谱按实判 · session 模块说明 + assets README 同步 | 同左 + 可逆往返断言（严于 SPEC · 见观察项 2） | 一致 ✓ |

竖切裁定（五块不拆波）与实现序（D5→D1→D2→D3→D4）均承 SPEC §2/§8 不重开辩论 ✓。

### 非范围

task 非范围 11 条 = SPEC §3 11 条逐条对应（轮数策略/compress_window 本体 · SSE · 长期记忆 · 离线预生成 · chat 轨 · 摘要写回 turns 表 · 增量摘要 · LLM-as-judge · Redis 缓存 · UI/端点 · 历史文档回改）✓。

### failure_paths

task 14 条 = SPEC §5 11 条翻四列（可重试/用户可见列补齐）+ 过程 3 条（闸未签拒开工 · B1 闸前置拒收 · 无双对拍/变异检验拒收）✓；三静默错（摘错造错误前提 / 缓存污染 / 回退开关失效）各有断言 + 变异检验兜底 ✓。

### 验收标准

26 条 = 人工闸 1 + D1×5 + D2×4 + D3×3 + D4×4 + D5×3 + 变异检验×3 + 工程×3，逐块映射 SPEC §6 ✓；行为变更类 task 之「旧测 grep 影响面」义务以 B1 清单 12 行落盘 ✓（回归×10 · 改编×0 · 新增×1 · 迁移×1 · 删除×0）。

### R0–R5 思考轮

控制表回填闭合 · actual_last_round=R5 · early_stop=no · 残余风险 3 条全承 SPEC §7（金样覆盖盲区 / 首压成本线性 / summary 档默认 None 调档路径）✓；R0 锚点复核声明经本帽抽查属实（见下）。

### 闸表

- **HG-AUDIT-R1 = pending** ✓（与 SPEC §8 流程一致 · 20 审后人签 · 本帽不签）
- **HG-TASK-DRAFT = pending** ✓（待 00 验收 · 本帽不签）
- **HG-GRAPH-MODULES 亲读复核**：本帽真读 `docs/_tech_graph/l1/01_modules.md`——`db` 行 :33（`app/db/**`, `alembic/**` · 新表登记先例 ops_llm_usage 在备注）· `lg_rag` 行 :27（`app/ops/lg_rag/**` 覆盖 continuity 装配面）· `chat` 行 :22（glob 实含 `app/ops/session/**` 覆盖新增 `session/summary.py`）· `llm` 行 :32（`app/llm/**` 覆盖 model_catalog 档扩展）均在表；签录链自 bootstrap 2026-07-16（:55）完整至 memory-preference-profile 行（:90 · 2026-09-22）；llm-layer-hardening「00 代录 · 30 交付核验后」先例在 :89。task 闸表陈述全部属实 ✓。
- **新签义务留 00 代录位条款**：闸表 HG-GRAPH-MODULES 行（task :40）+ graph_delta_note（:23）+ R1 节（:274）三处钉死 ✓；偏离回炉补闸条款（新增一级模块/路由/SSE 事件/摘要写回 turns 表 → 退 10-spec + 补闸 + 图谱如实登记）在案 ✓。
- HG-PILOT-OPSDESK-GLAYER = n/a ✓。

## 重点抽查（本帽真跑 / 真读）

1. **pytest 基线复跑**：`python -m pytest tests --collect-only -q` = **1239 tests collected**（2026-09-22 真跑）与 task 声称一致 ✓。
2. **alembic head 实查**：`alembic heads` = `20260922_memory_kind_preference (head)` ✓。
3. **B1 12 行抽 7 行实核**：
   - #1 `test_lg_rag_session_continuity.py:65-84` 三用例属实（:72 `历史摘要` 断言 · :76-78 短窗 noop · :81-85 失败降级截断）✓
   - #3 `test_memory_injection.py` 23 用例属实；:34-54 off 逐字节对拍（`_shape` 比较 · 未设/false/非法值参数化）· :57-63 非法值 warning 范式属实 ✓
   - #5 `test_llm_routing.py:68-74` unknown-task 用例实测对象为 `resolve_task_model("summarize")` → `unknown_task` + warning ✓
   - #6 :82-89 参数化档集合 = answer/extract/structured 三档（不含新档）· 既有档行为守护成立 ✓
   - #8 `test_llm_usage.py:104-120` answer/grader 聚合先例属实 · task_type 自由 str 无枚举 ✓
   - #10 tests/eval/ 9 文件属实（除 `__init__.py` 计 9 个 .py）· `evals/session/` 目录不存在（新增义务成立）✓
   - #11/#12 口径复核：`grep TASK_TYPES|TASK_TIER_MODELS tests/` 仅 docstring 一处提及（无枚举档集合内容断言）✓；`grep load_session_turns app/` 仅定义 + `__init__` 导出（无生产调用方）✓；`grep session.summary|SESSION_SUMMARY app/ tests/ evals/` 零命中 ✓
   - 用例计数全对：15 / 2 / 23 / 17 / 3 / 6 / 9 / 9 ✓
4. **「summarize ≠ summary」语义不反转核验**：现有 unknown-task 用例用词 `"summarize"` 与新增档 `"summary"` 不同词——TASK_TYPES 扩 summary 后该用例仍走 unknown_task 分支，断言零改动全绿，语义不反转成立 ✓。
5. **双对拍断言可测性核验**：
   - **off 三态对拍**：`test_memory_injection.py:34-54` 已提供可复刻范式（`_shape` 逐字节比较 · env 三态参数化）——摘要面插入点在记忆注入之前且 off 态跳过，基线 = 现有 `assemble_graph_messages_with_memory` 输出，断言可落地 ✓
   - **on 态全失败对拍**：monkeypatch 摘要 LLM 调用面抛错 → 每 chunk 保留占位符 → 断言输出与 off 基线逐字节一致 + caplog/span 断言 `session_summary_degraded=N`——「静默降级」与「未走摘要面」经标记可区分（变异检验③ oracle 明确）✓
   - **变异检验①/②**：均有「临时反转 → 对拍/单测必挂 → 恢复全绿」的机械 oracle，40 可执行 ✓
6. **代码锚点抽查（真读）**：`continuity.py:27` def compress_window · :54 占位条 `[历史摘要 · N 轮 · roles=...]` · :59-62 降级截断 · :110-120 memory_facts_enabled 三件套 · :219/:283 装配面；`model_catalog.py:118` 四档 · :122-127 extract=None · :140/:158-163 解析与 env 已知目录校验；`loader.py:52-62` 显式炸；`extract.py:43` EXTRACT_TIMEOUT_S=60.0 · :99/:114 分层路由+wait_for 先例；`usage.py:80-87` use_run_context；assets README :20-34 变量表含 `memory.extract.system v1 无变量` 行——全部属实 ✓。

## 非阻塞观察项（2 条 · 不构成内容阻塞）

1. **日志形态引述字面小疵**：task :68 写作 `invalid MEMORY_SUMMARY_ENABLED=%r`；实测先例日志为 `invalid MEMORY_FACTS_ENABLED=%r; fallback to false`（continuity.py:119 真读）。复刻对象与纪律意图明确，属引述笔误；建议 10-task 顺手修订字面，或由 30 以代码真值为准逐字复刻（本审查文留痕即可）。
2. **D5 口径严于 SPEC**：task D5 验收在 SPEC §6-D5（冒烟 + 回滚注释）之上新增「可逆往返（upgrade → downgrade → upgrade）」断言——属加强而非偏离，30/40 按 task 口径执行，记录备查。

## 回填清单

- 内容阻塞项：零
- 非阻塞观察 2 条见上（字面修订建议 · 口径加强记录）——均不阻塞维护者签 HG-AUDIT-R1

## 维护者签闸（20 后 · 30 前）

- [ ] 已读 R1 审查结论
- [ ] 在 task 人工闸表将 HG-AUDIT-R1 改为 approved（维护者 · 日期）
- [ ] commit task 文档或确认已签
- [ ] 再下发 Harness 30 Prompt

30 Agent 将以 task 表为准；pending 时必须拒开工（见 TEMPLATE_30_gate_stop.md）。

## 签收

R1 书面审查完成 · 内容审查结论：**通过** · 流程闸 HG-AUDIT-R1 待维护者签 · 审查文与 invoke 快照已落盘 · task 实质内容零改动。
