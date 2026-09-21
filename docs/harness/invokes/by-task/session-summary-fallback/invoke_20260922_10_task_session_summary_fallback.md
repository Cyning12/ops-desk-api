# invoke · 10 · session-summary-fallback · task 落稿

| 项 | 内容 |
|----|------|
| **时间** | 2026-09-22 |
| **帽** | 10-task（SPEC signed 后落稿 · 本棒由 00 委派 10-task 帽 Agent 执行） |
| **文件** | `docs/tasks/active/task_session_summary_fallback.md` |
| **上游** | `docs/spec/session-summary-fallback/SPEC-session-summary-fallback_v1.md`（signed · HG-SPEC-SIGNOFF=approved 2026-09-22 · 48ce63e） |
| **格式基准** | `docs/tasks/done/task_memory_preference_profile.md`（真读对齐字段 · PR #157 已合 · CLOSE 归档） |

## 结论

**PASS（落稿）** · 范围 D1 真摘要生成通路（`app/ops/session/summary.py` `summarize_placeholders` 请求时懒生成 · 装配接线在记忆注入之前 · `compress_window` 纯函数零改动 · summary 档 `OPS_LLM_TIER_SUMMARY_MODEL` + usage 归因 · 超时单 chunk 降级 span `session_summary_degraded` · prompt 资产 `session.summary.system.md` v1 · 摘要条版本+来源+有损三标记）/ D2 缓存表 `ops_session_summaries`（唯一约束 (thread_id, chunk_hash) · key 铁律=内容哈希+prompt_version+model · FK CASCADE · 生成成功才写）/ D3 一键回退（`SESSION_SUMMARY_ENABLED` 默认关 · 非法值回退+warning · off 三态 + on 态全失败**双对拍逐字节一致**=上线前提）/ D4 保真度金样（`evals/session/summary_fidelity_v1.yaml` + `tests/eval/test_session_summary_fidelity.py` 一一对应 · sentinel must_keep/must_not_add 正反双断言 + 空摘要假通过防线 · 热路径零 LLM-as-judge）/ D5 alembic 建表（可逆往返 · 回滚注释「off 态不读不写 · drop 安全」）+ 图谱登记（db 行新表 + lg_rag/chat/llm 行备注 + 人签新行 00 代录位）+ 文档同步；非范围沿用 SPEC §3（轮数策略/compress_window 本体 · SSE · 长期记忆 · 离线预生成 · chat 轨 · 摘要写回 turns 表 · 增量摘要 · LLM-as-judge · Redis · UI/端点 11 条）；验收 **26 条**全否定性断言化逐块映射 SPEC §6（人工闸 1 / D1×5 / D2×4 / D3×3 / D4×4 / D5×3 / 变异检验×3 / 工程×3）· 与 SPEC 实质差异**零**；failure_paths **14 条**（SPEC §5 十一条翻四列 + 过程三）；R0–R5 全轮无 early_stop。

## 实扫留痕（本帽真跑）

- `git branch --show-current` = `task/session-summary-fallback` ✓（SPEC 签收 48ce63e 后）
- 压缩/装配：`continuity.py` `compress_window` :27-62（占位条 :54 · 降级截断 :59-62）· `assemble_graph_messages` :65-92 · `assemble_graph_messages_with_memory` :219-283（async 注入面先例 · off 逐字节 docstring 明示）· `memory_facts_enabled` :110-120（默认关三件套逐字复刻源）——与 SPEC §1 一致
- 生产调用面：`graph.py` `_ainvoke_with_tracing` :153（调用 :170）/ `_astream_with_tracing` :187（调用 :202）；history 来源 `load_thread_turns`（thread_store.py:44 · 调用点 `lg_rag/router.py:203` · SPEC 锚点「router.py:203」实址补全）
- chat 轨：`load_session_turns`（session/history.py:11-40）grep 实证 app 内**无生产调用方**（仅 `__init__` 导出）——零改动复核成立
- 原文面：`models.py` `ops_runs.query/answer` :255/:260（Text）· `OpsLgRagTurn` :305-320（docstring :306 提及「system 摘要」= 未实现旧设想，persist 只写 user/assistant 实扫属实）
- LLM 面：`model_catalog.py` `TASK_TYPES` 四档 :118 · `TASK_TIER_MODELS` extract=None :122-127 · env 覆盖校验 :158-163 · `resolve_task_model` :140-173；usage `use_run_context`（usage.py:80-87 · task_type 自由 str 无枚举 → summary 归因零改造）；`EXTRACT_TIMEOUT_S=60.0`（extract.py:43）+ wait_for 先例 :99-114
- prompt 资产：`loader.py:52-62` 显式炸纪律 · assets README 变量表 :20-34（`memory.extract.system v1 无变量` 行先例）；`evals/session/` 目录不存在（新增义务）· 金样先例 `evals/memory/preference_redline_v1.yaml` + `tests/eval/test_memory_preference_redline.py`
- 迁移链：`alembic heads` 真跑 = `20260922_memory_kind_preference`（新迁移挂 head 后）
- 命名冲突扫：`grep -rn 'session.summary\|SESSION_SUMMARY' app/ tests/ evals/` = **零命中**
- pytest 基线真跑：`python -m pytest tests --collect-only -q` = **1239 collected**
- B1 落盘 **12 行**（回归×10 · **改编×0** · 新增×1 · 迁移×1 · 删除×0）；关键实证：tests 全仓**无枚举 TASK_TYPES 内容的断言**；`test_llm_routing.py:69-74` unknown-task 用例用 `"summarize"` ≠ 新档 `"summary"`（语义不反转 · 加档零改编）；档参数化集合（:78 · :85-87）不含新档不受影响
- HG-GRAPH-MODULES 真值核验：**真读** `docs/_tech_graph/l1/01_modules.md`——模块表已建置（bootstrap 签 2026-07-16 · 签录链完整至 :90）· `db` 行 :33 / `lg_rag` 行 :27 / `chat` 行 :22（glob 含 `app/ops/session/**`）/ `llm` 行 :32 四行覆盖全部改动面 → 有图谱义务按实判（db 行新表登记 + 三行备注 + 人签**新行留 00 代录位**随 30 交付落盘 · llm-layer-hardening 先例）+ **偏离回炉补闸条款**钉死
- SPEC §1 锚点复核**零措辞偏差**（「router.py:203」实址补全为 `app/ops/lg_rag/router.py:203` 属锚点精确化非偏差）

## 闸态

- `HG-TASK-DRAFT` = **pending**（00 验收代录/人签 · 本帽不签）
- `HG-AUDIT-R1` = **pending**（blocks 30 · 20 审后人签/授权代录）→ **30 拒开工**
- `HG-GRAPH-MODULES` = **approved（模块表已建置 · 本帽真读）** + 本 task 新签义务（db 行新表 `ops_session_summaries` + lg_rag/chat/llm 行备注 + 人签记录新行 00 代录位 · 随 30 交付落盘）；偏离（新增一级模块/路由/SSE 事件/摘要写回 turns 表）→ 回炉补闸
- `HG-PILOT-OPSDESK-GLAYER` = n/a

## lint

`npx spec-wave task lint --file docs/tasks/active/task_session_summary_fallback.md` = **PASS**（W3 自检结论占位 draft 期合法 · close 前 40 回填）

## 下一棒

20-task-audit 书面审（对照 SPEC）→ HG-TASK-DRAFT + HG-AUDIT-R1 人签 → 30（`task/session-summary-fallback` · 承 SPEC §8 序：D5 迁移+图谱 → D1 summary 档+prompt 资产+生成服务 → D2 缓存 → D3 开关+双对拍 → D4 评测 · `compress_window` 本体零改动）。后续 20/30/40 invoke 由各棒落盘本目录（命名对齐 `invoke_<yyyymmdd>_<hat>_<verb>_session_summary_fallback.md`）。
