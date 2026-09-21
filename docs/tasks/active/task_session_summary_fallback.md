# Task：会话记忆真摘要（可回退原文）· 请求时懒生成 + DB 缓存 · `SESSION_SUMMARY_ENABLED` 默认关 · off/on-态全失败双对拍逐字节一致（session-summary-fallback）

> **状态**：`signed`（2026-09-22 · R1 PASS 零阻塞 · HG-TASK-DRAFT/HG-AUDIT-R1=approved（维护者授权 00 代录）· 可 30）  
> **类型**：feature（新 LLM 调用面（summary 档）+ 新 prompt 资产 + **新表 ops_session_summaries（有 alembic 义务 · 建表可逆）** + **有图谱义务按实判**（db 行新表登记 + lg_rag/chat/llm 行备注 · 不新增一级模块/路由/SSE 事件 · 偏离回炉条款见闸表与 graph_delta_note））  
> **上游 SPEC**：`docs/spec/session-summary-fallback/SPEC-session-summary-fallback_v1.md`（**signed** · HG-SPEC-SIGNOFF=approved 2026-09-22 · commit 48ce63e）  
> **分支**：`task/session-summary-fallback`（**禁止 master/main 直改 · 禁止 push**）  
> **10 注**：2026-09-22 · 本棒由 00 委派 10-task 帽 Agent 执行；HG-TASK-DRAFT / HG-AUDIT-R1 均 **approved**（2026-09-22 · R1 PASS 零阻塞 · 维护者授权 00 代录；10 帽不签）

---

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `session-summary-fallback` |
| **git_branch** | `task/session-summary-fallback` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | 纯函数对拍（`compress_window` 零 diff git 级断言 · off 态与占位模式逐字节一致 · on 态全链路失败与 off 态逐字节一致 · 双对拍=上线前提）；缓存 key/命中/降级单测（同序号不同内容 → miss · 命中零 LLM 调用 mock 计数）；开关三态断言（未设/false/非法值 · 非法值回退 false + warning · continuity.py:110-120 先例逐字复刻）；保真度金样 sentinel 正反断言（`evals/session/summary_fidelity_v1.yaml` + `tests/eval/test_session_summary_fidelity.py` 一一对应 · 热路径零 LLM-as-judge · `evals/memory/preference_redline_v1.yaml` 先例）；摘要条三标记锚点断言（版本 v1 + 来源 model + 「有损」· 非全文快照）；**变异检验三条**（开关可检 / 缓存可检 / 降级可检 · 见验收「变异检验」）；alembic 建表**可逆往返**（upgrade head + downgrade = drop table · 回滚注释含「off 态不读不写 · drop 安全」）；全量 pytest 绿（基线 **1239 collected** 真跑）+ ruff 零新增 |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | **有图谱义务按实判**（SPEC §2 D5）：新表 `ops_session_summaries` 落 `docs/_tech_graph/l1/01_modules.md` db 行数据面；`lg_rag` 行（continuity 装配面）· `chat` 行（glob 含 `app/ops/session/**` · 新增 `session/summary.py`）· `llm` 行（`model_catalog.py` TASK_TYPES 扩 `summary` 档）备注更新；人签记录新行**留 00 代录位**（30 交付后落盘 · llm-layer-hardening 先例）；**不新增一级模块/路由/SSE 事件类型**（**本帽真读复核**见闸表 HG-GRAPH-MODULES 行与 R1） |
| **graph_delta** | 有（db 行新表登记 + lg_rag/chat/llm 行备注 · 备注级非新模块） |
| **graph_delta_note** | **回炉补闸条款**：若 30 阶段实现形态偏离预判（新增一级模块 · 新增任何路由/SSE 事件类型 · 摘要写回 `ops_lg_rag_turns` 等 SPEC §3 非范围项），**不得沿用本裁定**——退回 10-spec 修订 SPEC + 10-task 补闸 + `docs/_tech_graph/` 如实登记后方可续 30 |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 契约真值在 SPEC `session-summary-fallback`；`app/ops/session/` 模块说明与 `app/ops/prompts/assets/README.md` 同步属 D5 范围项非 wiki |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,20,30,40` |
| **invoke_retention_profile** | `default` |
| **experience_capture** | `recommended` |
| **kpi_aggregator** | `CLOSE` |
| **orchestration** | **单 task 五块不拆波**（SPEC §2 波次裁定：真摘要是一个不可拆语义单元——只生成不配缓存/版本标记 = 重复付费且不可归因；不配一键回退 = 违反铁律（回退是上线前提）；不配保真度金样 = 违反手册 §1.8）；本 task：10 落稿 → 20-task-audit → HG-AUDIT-R1 人签 → 30（承 SPEC §8 序：D5 迁移+图谱 → D1 summary 档+prompt 资产+生成服务 → D2 缓存 → D3 开关+双对拍 → D4 评测 · `compress_window` 本体零改动）→ 40（双对拍 + 变异检验三条 + alembic 往返）→ CLOSE |
| **freeze_id** | 无（不改 `lg-rag-sse-v1` / `lg-rag-http-v1` / `lc-evidence-http-v1`；SSE 零新事件类型 · 摘要过程对用户不可见） |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | **approved** | 20-R1, 30 | 2026-09-22 · 00 验收 10-task 稿通过（维护者本窗授权 00 签收过程文档 · 原话留痕 SPEC 状态行） |
| HG-AUDIT-R1 | **approved** | **30** | 2026-09-22 · 20-task-audit R1 PASS 零阻塞零退回（`docs/harness/reviews/task_session_summary_fallback_audit_R1_20260922.md` · B1 抽 7 亲跑属实 · 双对拍可测性成立）· 维护者本窗授权 00 代录签收 |
| HG-GRAPH-MODULES | **approved** | **30** | 2026-09-22 本帽**真读** `docs/_tech_graph/l1/01_modules.md`：模块表已建置（bootstrap 签 2026-07-16 · 签录链完整至 memory-preference-profile 行 :90）；`db` 行 :33（`app/db/**`, `alembic/**` · 新表登记先例 ops_llm_usage）· `lg_rag` 行 :27（`app/ops/lg_rag/**` 覆盖 continuity 装配面）· `chat` 行 :22（glob 含 `app/ops/session/**` 覆盖新文件 `session/summary.py`）· `llm` 行 :32（`app/llm/**` 覆盖 model_catalog 档扩展）均在表。SPEC §2 D5 判**有图谱义务按实判**：新表 `ops_session_summaries` 登记 db 行 + 上述三行备注 + 人签记录**新行留 00 代录位**（随 30 交付落盘 · llm-layer-hardening「00 代录 · 30 交付核验后」先例）——义务钉在 D5 验收，**不新增一级模块/路由/SSE 事件**故不阻塞 30 开工形态预判。**若 30 形态偏离 → 回炉补闸**（见 graph_delta_note，不得沿用本裁定） |
| HG-PILOT-OPSDESK-GLAYER | n/a | 物理分层试点改码 | 本 task 不涉物理分层试点 |

---

## 背景与目标

现状（SPEC §1 实扫锁死 · 2026-09-22 本帽复核一致）：当前窗口压缩 = **截断 + 占位标记**——`compress_window`（continuity.py:27-62 纯函数零 IO）保留最近 `max_full_turns=6` 轮全量，更早轮次按 `group_size=2` 合并为占位 `[历史摘要 · N 轮 · roles=...]`（:54 · 只有轮数+角色零内容）——保住窗口有界，没保住语义连续（手册 §1.2.2「明确知道缺的一环」）。

一句话目标（SPEC 锁死）：在 lg_rag 装配面把占位符升级为**真摘要**——结构仍由纯函数 `compress_window` 定（**零改动**），内容替换走新 async 摘要面 `app/ops/session/summary.py`：**请求时懒生成 + DB 缓存**（key = 内容哈希 + prompt_version + model），摘要条带**版本 + 来源 + 有损声明**三标记，原文表零改动可查；**`SESSION_SUMMARY_ENABLED` 默认关、非法值回退 false + warning、关闭/失败/回退均与占位模式逐字节一致**（off 与 on-态全失败双对拍 = 上线前提）；保真度金样以 sentinel 正反断言为否决面（热路径零 LLM-as-judge）。

设计纪律（30 不得违反 · 承 SPEC §1/§2 签收锁死）：

1. **`compress_window` 纯函数体零改动**：结构（轮数切分/条数/顺序/尾部全量轮）由它定；本面只做内容替换（continuity-dedup 波次刚收敛此文件 · 改动面压在装配层）。
2. **回退铁律**：回退 = 关开关（零代码零迁移 · env 重读即时生效 · 进程内无状态）；off（未设/false/非法值）→ 装配输出与占位模式**逐字节一致**；on 态任何失败 → 该 chunk 保留占位符降级，**永不阻塞主答、绝不产出半摘要**。
3. **缓存 key 铁律**：key 必含**内容哈希 + prompt_version + model**——只用 (thread_id, 序号) 会在窗口滑动后命中旧摘要 = 缓存污染静默错；hash 变 = 自然 miss，**无主动失效逻辑**。
4. **原文 SoT 零污染**：摘要**不得写入** `ops_lg_rag_turns`（docstring 的「system 摘要」是未实现旧设想，不构成立项依据）；摘要与原文**物理分表**（`ops_session_summaries` 独立表）。
5. **锚点断言替代全文快照**：摘要条/prompt 资产断言守语义锚点（「历史摘要」「有损」「不得新增」级），改文案不挂 CI、改语义必挂。
6. **金样正反双断言缺一不算过**：must_keep（sentinel ⊆ 摘要）+ must_not_add（禁忌 sentinel 不在摘要）——只做反向会得到假通过（空摘要天然满足 must_not_add）；must_keep 非空断言作空摘要假通过防线。

---

## 现状锚点（只读 · 30 必读 · 10 已扫 · 承 SPEC §1 并复核）

| 主题 | 路径 · 锚点 | 现状 |
|------|-------------|------|
| 压缩纯函数（**零改动对象**） | `app/ops/lg_rag/continuity.py` | `compress_window`（:27-62 纯函数无 IO）：`max_full_turns=6`/`group_size=2`，占位条 `[历史摘要 · N 轮 · roles=...]`（:54）；压缩失败降级截断（:59-62）。`assemble_graph_messages`（:65-92）纯函数装配 |
| 装配接线点（改造对象 D1） | `app/ops/lg_rag/continuity.py:219-283` | `assemble_graph_messages_with_memory` 已是 **async + 可选 IO 注入面**（memory-facts 先例：开关默认关 · 关闭时与纯函数面逐字节一致 · 故障降级不拖垮请求 · span 计数）——摘要面复刻此形态，插入点在**记忆注入之前** |
| 默认关三件套先例（复刻对象 D3） | `app/ops/lg_rag/continuity.py:110-120` | `memory_facts_enabled()`：默认 false · `_TRUTHY/_FALSY` 集合 · 非法值回退 false + warning（`invalid MEMORY_SUMMARY_ENABLED=%r` 同款日志形态）——`SESSION_SUMMARY_ENABLED` 逐字复刻 |
| 生产调用面 | `app/ops/lg_rag/graph.py:153/:187` | `compress_window` 唯一生产入口 = `_ainvoke_with_tracing`/:170 与 `_astream_with_tracing`/:202 → `assemble_graph_messages_with_memory`；history 来自 `thread_store.load_thread_turns`（`lg_rag/router.py:203` · 全量无 limit · 压缩在内存收口） |
| chat 轨历史面（零改动） | `app/ops/session/history.py` | `load_session_turns`（:11-40）实扫 app/ 内**无生产调用方**（仅 `session/__init__.py` 导出）——本 task 零改动 |
| 原文保留面（零改动） | `app/db/models.py:255/:260/:305-320` | `ops_runs.query/answer`（Text 原文）与 `ops_lg_rag_turns`（role/content Text · thread SoT）原文均在库保留现状；`OpsLgRagTurn` docstring（:306）提及「system 摘要」但 `persist_thread_turns` 只写 user/assistant |
| LLM 分层路由（改造对象 D1 · summary 档） | `app/llm/model_catalog.py` | `TASK_TYPES=("answer","grader","extract","structured")`（:118）；`TASK_TIER_MODELS` extract 档默认 None（:122-127 · 不落档沿用现网默认）；env 覆盖 `OPS_LLM_TIER_<TASK>_MODEL` + 已知目录校验（:158-163）；`resolve_task_model`（:140-173 · unknown_task 回退 + warning） |
| 重试/熔断/usage（零改造继承面） | `app/llm/retry.py` · `circuit.py` · `usage.py` | 重试（`OPS_LLM_RETRY_ENABLED` 默认开）+ provider 级熔断（`OPS_LLM_CB_ENABLED` 默认开）在 provider 包装层**自动继承**；usage 经 ContextVar `use_run_context`（usage.py:80-87 · task_type 自由 str 无枚举）落 `ops_llm_usage` 归因；extract 档 + background 面完整先例（extract.py:99-114） |
| prompt 资产化（复刻对象 D1） | `app/ops/prompts/` | 模板落盘 `assets/<template_id>.md`（front-matter `template_id`/`version` · loader.py:52-62 读取 · 缺文件/缺字段/空 body/版本非法**显式炸不静默降级**）；`render("memory.extract.system")` 无变量、window 经 user 消息传入（extract.py:105-106）；assets README 变量集合表（:20-34 · `memory.extract.system v1 无变量` 行先例） |
| 超时先例 | `app/ops/memory/extract.py:43` | `EXTRACT_TIMEOUT_S = 60.0` + `asyncio.wait_for`（:103-114）——摘要单次调用超时常量复刻此形态 |
| alembic 链 | `alembic heads` 真跑 | head = `20260922_memory_kind_preference`；新迁移挂 head 后（建 `ops_session_summaries` · 可逆） |
| evals 金样先例 | `evals/memory/preference_redline_v1.yaml` + `tests/eval/test_memory_preference_redline.py` | 清单=实现一一对应（P0 同款）· 正反双断言 · 热路径零 LLM-as-judge · 金样形态直接对齐；`evals/session/` 目录**不存在**（新增义务） |
| 命名冲突扫 | `grep -rn 'session.summary\|SESSION_SUMMARY' app/ tests/ evals/` | **零命中**（2026-09-22 真跑 · 新文件名/env 名无冲突） |
| 测试基线 | `python -m pytest tests --collect-only -q` | **1239 collected**（2026-09-22 本帽真跑）；相关面用例计数见 B1 清单 |

---

## 钉死契约（自 SPEC §2/§4 锁死；30 不得静默改义）

| 项 | 钉死 |
|----|------|
| **生成通路（方案 L1）** | 新增 `app/ops/session/summary.py`：`async def summarize_placeholders(compressed: list[dict], *, thread_id: str) -> list[dict]`——输入 `compress_window` 产物，逐占位 chunk 查缓存（D2）→ miss 才调 LLM → 替换为真摘要条；**结构零改动**（轮数切分/条数/顺序/尾部全量轮由 compress_window 定）；chunk 边界随窗口滑动 hash 自动失效，**无主动失效逻辑** |
| **装配接线** | `assemble_graph_messages_with_memory` 内、记忆注入**之前**：`compress_window` →（开关 on）`summarize_placeholders` → 装配；开关 off → 跳过本面，与现网**逐字节一致**（对拍断言钉死） |
| **summary 档（方案 T2）** | `TASK_TYPES`/`TASK_TIER_MODELS` 加 `"summary": None`（None = 不落档沿用现网默认 · extract 档同语义）；env 覆盖 `OPS_LLM_TIER_SUMMARY_MODEL`（已知目录校验沿用）；`use_run_context(run_id=…, surface="lg_rag", task_type="summary")` → `ops_llm_usage` 自动归因；重试/熔断 provider 包装层自动继承零改造 |
| **超时与降级** | 单次摘要调用包 `asyncio.wait_for`（超时常量 · EXTRACT_TIMEOUT_S 先例）；**任何失败（LLM/超时/熔断/解析/资产缺失）→ 该 chunk 保留占位符**，log + span `session_summary_degraded=N`（N=降级 chunk 数）；单 chunk 粒度降级 ≠ 全局回退开关，两者各自断言不混淆 |
| **prompt 资产** | 新增 `app/ops/prompts/assets/session.summary.system.md`（v1 · front-matter · 无变量 · chunk turns 经 user 消息传入）；`render("session.summary.system")`；缺文件/版本非法显式炸（loader 纪律沿用 · 调用面 try 包住 → 降级占位）；模板正文须含「不得新增原文没有的事实」级指令；锚点断言守「摘要」「不得新增」级语义 |
| **摘要条三标记** | 真摘要条 content 形如 `[历史摘要 · v1 · N 轮 · 模型:<model> · 有损压缩，细节以最近轮为准]` + 摘要正文——**版本 + 来源 + 有损声明**进上下文（模型可见「这是摘要不是原文」）；占位条格式**零改动** |
| **缓存表（方案 C1）** | 新表 `ops_session_summaries`：`id` · `thread_id`（FK → ops_lg_rag_threads · ondelete CASCADE）· `chunk_hash`（sha256(prompt_version + model + chunk turns canonical JSON)）· `summary`（Text）· `prompt_version` · `model` · `turn_count` · `source`（恒 `"llm"`）· `created_at`；**唯一约束 (thread_id, chunk_hash)** |
| **缓存读写纪律** | 生成成功才写（get-or-create · 唯一约束冲突 = 并发同 key 先写赢，容忍）；写缓存失败 → log + 本次仍用摘要（缓存是优化不是正确性依赖）；读失败视同 miss；off 态**零读零写** |
| **开关（D3 铁律）** | `SESSION_SUMMARY_ENABLED`：**默认 false**；非法值回退 false + warning（continuity.py:110-120 三件套逐字复刻）；env 重读即时生效（进程内无缓存态）；off 态零 LLM 调用、零缓存读写 |
| **上线前提双对拍** | 验收必须证明：① off 对拍逐字节一致（三态：未设/false/非法值）；② on 态强制 LLM 全失败 → 输出与 off 态**逐字节一致** + span 降级标记——**两条都过才允许合入** |
| **金样（D4）** | `evals/session/summary_fidelity_v1.yaml`（清单）+ `tests/eval/test_session_summary_fidelity.py`（实现）一一对应；固定 turns 夹具含 sentinel（专有编号/实体 token 如 `OD-7391`、`repo:ops-desk-api`）；must_keep ⊆ 摘要文本（正向）+ must_not_add 逐项不含（反向）+ must_keep 非空（空摘要假通过防线）；热路径用夹具/录制摘要跑同一校验函数（确定性），真模型离线抽检不作 CI 否决面 |
| **alembic** | 迁移建 `ops_session_summaries`（字段 + 唯一约束 + FK CASCADE）；存量零数据迁移；**可逆往返**（upgrade → downgrade → upgrade）；回滚 = drop table，迁移注释含「off 态不读不写 · drop 安全」；models.py 同步新增 ORM 类 |
| **图谱** | db 行登记新表 + lg_rag/chat/llm 行备注 + HG-GRAPH-MODULES 人签记录新行（**00 代录位** · 随 30 交付落盘）；`./scripts/graph-compile.sh` 绿；偏离预判 → 回炉补闸（graph_delta_note） |
| **文档** | `app/ops/session/` 模块说明（无 README 则建 · memory README 先例）：env 表补 `SESSION_SUMMARY_ENABLED`/`OPS_LLM_TIER_SUMMARY_MODEL` + 故障语义（降级占位 + span 标记）；`app/ops/prompts/assets/README.md` 变量表补 `session.summary.system v1 无变量`；不回改 done/归档历史文档 |
| **安全** | 无新凭证面/网络面（复用既有 provider 层）；不新增对外端点/SSE 事件；缓存表与原文表同库同级别；身份（tenant/user/thread）取自请求上下文既有校验链（resolve_thread_for_user 跨用户 404），模型产出不得参与 |

---

## 范围（同 task 竖切 · 五块不拆波 · SPEC §2 波次裁定）

- [ ] **D1 · 真摘要生成通路（必做 · 请求时懒生成 L1）**：`app/ops/session/summary.py` `summarize_placeholders`；装配接线（记忆注入之前 · off 跳过逐字节一致）；summary 档（`TASK_TYPES`/`TASK_TIER_MODELS`/`OPS_LLM_TIER_SUMMARY_MODEL` + usage 归因）；超时 + 单 chunk 降级（span `session_summary_degraded`）；prompt 资产 `session.summary.system.md` v1；摘要条三标记
- [ ] **D2 · 原文保留 + 摘要缓存与版本/来源落库（必做）**：`ops_session_summaries` 新表（唯一约束 (thread_id, chunk_hash) · FK CASCADE）；key 铁律（内容哈希+prompt_version+model）；生成成功才写 · 写失败不挡主流程；`ops_lg_rag_turns`/`ops_runs` 零改动
- [ ] **D3 · 可配置一键回退占位模式（必做 · 铁律）**：`SESSION_SUMMARY_ENABLED` 默认关 + 非法值回退 warning；off 三态对拍逐字节一致；on 态全失败对拍逐字节一致；灰度纪律（默认关上线 → env 开 → 观测 → 异常即关 · 回退零代码零迁移）
- [ ] **D4 · 保真度评测金样（必做 · 否决面确定性）**：`evals/session/summary_fidelity_v1.yaml` + `tests/eval/test_session_summary_fidelity.py` 一一对应；sentinel must_keep/must_not_add 正反双断言 + 空摘要假通过防线；上下文结构断言（零占位残留 · 三标记在条）；热路径零 LLM-as-judge
- [ ] **D5 · 表结构 / alembic / 图谱 / 文档（必做 · 按实判）**：alembic 建表迁移（可逆往返 · 回滚注释）+ models.py ORM 类；图谱登记（db 行 + 三行备注 + 人签新行 00 代录位）+ graph-compile 绿；session 模块说明 + assets README 同步

**竖切结论**：D1–D5 同 task 一次提交（SPEC §2：只生成不配缓存/回退/金样 = 重复付费不可归因 / 违反回退铁律 / 违反手册 §1.8；耦合面小单 PR 不巨型）；承 SPEC §8 实现序 D5 迁移+图谱 → D1 档+prompt 资产+生成服务 → D2 缓存 → D3 开关+对拍 → D4 评测。

### 非范围

- ❌ **改窗口压缩的轮数策略**（`max_full_turns=6`/`group_size=2` 不变）；`compress_window` 纯函数体零改动
- ❌ 改 SSE / 新增 SSE 事件类型；摘要过程对用户不可见（span/log 可观测）
- ❌ 对话记忆进长期记忆 / 跨会话摘要（memory 轨的事）
- ❌ **离线批量预生成 / 回填历史 thread**（§4 L2/L3 弃选 · 未来另案 SPEC 自带触发面与成本预算义务）
- ❌ chat 轨（`ops_runs`/`load_session_turns`）摘要化——实扫无生产调用方，原文保留现状零改动
- ❌ 摘要写回 `ops_lg_rag_turns`（role=system 摘要行）——污染原文 SoT，物理拒收
- ❌ 增量/滚动摘要（摘要的摘要 · 摘要链压缩）；多级压缩策略
- ❌ LLM-as-judge 评测面（任何形态）；语义相似度打分作 CI 否决面
- ❌ 多副本缓存共享层（Redis 等）——DB 表即共享面；进程内缓存
- ❌ 摘要管理/审计 UI（web/ios 另案）；对外 HTTP 读端点
- ❌ 历史文档回改

---

## failure_paths

| 触发条件 | 系统行为 | 可重试 | 用户可见 |
|----------|----------|--------|----------|
| `HG-AUDIT-R1` pending 即 30 | **拒开工** | 是 | 是 |
| **摘错造错误前提**（摘要与原文矛盾 / 丢关键事实，模型基于错误前提回答） | **静默错**；防线三层：① D4 金样 sentinel 正反断言上线前拦；② 摘要条带「有损压缩」标记（模型可见边界）；③ 一键回退 + 原文全量在库可查可对账；列残余风险（SPEC §7 ① 金样覆盖不了全部会话形态） | Y（关开关回退） | 否 |
| **缓存污染**（窗口滑动后 chunk 内容变，仍命中旧摘要） | **静默错**；key 必含内容哈希铁律物理防（内容变 → hash 变 → 自然 miss）；单测钉死「同序号不同内容 → miss」；唯一约束 (thread_id, chunk_hash) | Y（修 key） | 否 |
| **回退开关失效**（设了 off 仍走摘要 / 非法值被当 on） | **静默错**；off/未设/非法值 → 装配输出与占位模式**逐字节一致**对拍断言钉死（变异检验 ①：临时反转开关解析 → 对拍必挂）；非法值 warning 日志（continuity 先例） | Y（修解析） | 否 |
| on 态 LLM 全失败（熔断 open / 超时 / 4xx） | 该 chunk **保留占位符**降级（非整窗失败）；span `session_summary_degraded=N` + log；输出与 off 态逐字节一致（变异检验 ③ 钉死）；**永不阻塞主答、绝无半摘要条** | Y（自动 · 下请求重试） | 否 |
| 缓存写失败（DB 故障 / migration 未跑） | log + 本次仍用生成的摘要（缓存是优化不是正确性依赖）；读取失败视同 miss 走生成/降级链；不挡主答 | Y | 否 |
| 缓存读命中但 prompt_version/model 与当前不符 | key 已含 version+model → 结构上不可能（同 key 同参数）；改 prompt 未 bump version 才可能 → assets README 纪律 + CI 锚点断言兜底（改 body 必须 bump version） | — | 否 |
| 摘要条格式漂移（丢版本/来源/有损标记） | 锚点断言（摘要条含「历史摘要」+「有损」级锚点 + model 标记）必挂 CI；非全文快照（prompt-asset 先例） | Y（改文案） | 否 |
| 摘要成本失控（长会话多 chunk 逐请求生成） | 每 chunk 仅 miss 时一次调用 · 命中零成本；`ops_llm_usage` task_type=summary 可归因对账；span 计数生成/降级；列残余风险（SPEC §7 ② 超长会话首压成本线性增长） | — | 否 |
| 并发同 chunk 双生成（两请求同 miss） | 唯一约束先写赢 · 后者冲突即读已写行（同 key 同参数语义等价 · 容忍）；代价 = 偶发一次重复 LLM 调用（账面可查 · 不列验收） | Y | 否 |
| 摘要调用泄漏 tenant/user（跨 thread 读缓存） | key 含 thread_id · thread 归属校验在 router 既有面（resolve_thread_for_user · 跨用户 404）；本面不引入新身份语义 | Y | 否 |
| prompt 资产缺失/版本非法 | loader **显式炸**（不静默降级为空模板）；但调用面 try 包住 → 降级占位——资产事故表现为「摘要面整体降级占位 + log」，不表现为炸请求 | Y（补资产） | 否 |
| 30 开工前旧测影响面清单未落盘或逐条无处置 | 验收「工程 · 闸前置」项不满足 → **拒收**（B1） | 是 | 否 |
| 无双对拍 / 无变异检验三条却宣称回退铁律成立 | 40/verify **拒收**（不验收空真规则） | 是 | 否 |

---

## 验收标准

- [ ] 人工闸：`HG-AUDIT-R1` approved 后方可勾选下列码项（HG-GRAPH-MODULES 模块表已建置 approved · 本 task 图谱新签义务（db 行新表 + 三行备注 + 人签新行 00 代录位）随 30 交付落盘；**若 30 偏离预判（新增一级模块 / 新增路由/SSE 事件类型 / 摘要写回 turns 表）→ 回炉补闸**，见闸表与 graph_delta_note）

### D1 · 生成通路（映射 SPEC §6-D1）

- [ ] `compress_window` 函数体零 diff（git 级断言 · continuity-dedup 收敛形态保护）；占位条格式逐字节不变
- [ ] on 态：占位 chunk 被真摘要条替换；摘要条含版本（v1）+ 来源（model）+「有损」三标记（锚点断言 · 非全文快照）
- [ ] LLM 调用走 `summary` 档：`resolve_task_model("summary")` 生效；`OPS_LLM_TIER_SUMMARY_MODEL` 覆盖生效且校验已知目录；`ops_llm_usage` 落行 `task_type="summary"` / `surface="lg_rag"`
- [ ] `session.summary.system.md` v1 资产存在 · front-matter 合法 · 锚点断言（「摘要」「不得新增」级）；loader 缺文件显式炸（单测）
- [ ] 单次调用超时 → 该 chunk 降级占位 + span `session_summary_degraded`；主答零阻塞（时序断言）

### D2 · 缓存与版本归因（映射 SPEC §6-D2）

- [ ] `ops_session_summaries` 表结构断言（列/唯一约束 (thread_id, chunk_hash)/FK CASCADE）；生成成功才写；命中后**零 LLM 调用**（mock provider 调用计数断言）
- [ ] key 铁律单测：同 thread 同序号**不同内容** → miss 重新生成（缓存污染防线）；改 prompt_version/model → miss
- [ ] 缓存写失败 → 主流程仍返回摘要 + log；读失败视同 miss
- [ ] `ops_lg_rag_turns`/`ops_runs` 零改动（迁移 diff 断言 · 无 system 摘要行写入 turns 表）

### D3 · 回退开关（上线前提 · 映射 SPEC §6-D3）

- [ ] **off 对拍**：`SESSION_SUMMARY_ENABLED` 未设 / false / 非法值 → 装配输出与现网占位模式**逐字节一致**（三态全断言 · 非法值 warning 日志断言）
- [ ] **on 态全失败对拍**：强制 LLM 调用全失败 → 装配输出与 off 态**逐字节一致** + span 降级标记
- [ ] 开关 env 重读即时生效（进程内无缓存态断言）；off 态**零 LLM 调用、零缓存读写**（mock 计数断言）

### D4 · 保真度金样（映射 SPEC §6-D4）

- [ ] `evals/session/summary_fidelity_v1.yaml` 与 `tests/eval/test_session_summary_fidelity.py` 一一对应（清单 P0 同款断言）
- [ ] 正向：金样 must_keep sentinel 集合 ⊆ 摘要文本（逐条断言）
- [ ] 反向：must_not_add 禁忌集合逐项不在摘要中；**正反双断言缺一不算过**（空摘要假通过防线：must_keep 非空断言）
- [ ] 热路径零 LLM-as-judge（CI 用夹具/录制摘要跑校验函数；真模型离线抽检归 evals 层 · 不作 CI 否决面）

### D5 · 表结构 / 图谱 / 文档（映射 SPEC §6-D5）

- [ ] alembic 迁移：`alembic upgrade head` 后摘要通路冒烟过；**可逆往返**（upgrade → downgrade → upgrade）；回滚注释含「off 态不读不写 · drop 安全」
- [ ] `docs/_tech_graph/l1/01_modules.md`：db 行登记 `ops_session_summaries` + lg_rag/chat/llm 行备注 + HG-GRAPH-MODULES 人签记录新行（00 代录 approved）；`./scripts/graph-compile.sh` 绿；无新增路由/SSE 事件/一级模块（偏离 → 回炉补闸 + SPEC 回炉）
- [ ] 文档：`app/ops/session/` 模块说明 env 表补两 env + 故障语义（降级占位 + span 标记）；`app/ops/prompts/assets/README.md` 变量表补 `session.summary.system v1 无变量`

### 变异检验（不验收空真规则 · 映射 SPEC §6-变异检验）

- [ ] ① **开关可检**：临时让开关解析恒 true → off 对拍断言必挂；恢复后全绿
- [ ] ② **缓存可检**：临时让 key 去掉内容哈希（只留序号）→ 「同序号不同内容 miss」单测必挂；恢复后全绿
- [ ] ③ **降级可检**：on 态强制 LLM 全失败 → 输出与 off 态逐字节一致 + `session_summary_degraded` 标记出现（缺标记不算过——「静默降级」与「根本没走摘要面」必须可区分）

### 工程（映射 SPEC §6-工程）

- [ ] **闸前置**：30 开工前旧测影响面清单已落盘且逐条有处置（回归/改编理由）——清单见下「旧测影响面清单（B1）」，30 逐条执行处置并在提交说明逐条回填
- [ ] 全量 `pytest tests` 绿（基线 **1239 collected** · 2026-09-22 本帽真跑；**无既有用例删除**，新增守护用例数如实入 40 记录）；`ruff check app tests` 绿（零新增告警口径）
- [ ] 生产路径 diff 白名单：`git diff master -- app/ alembic/` 只含 continuity 装配层 / session 新模块 / model_catalog 档 / prompt 资产 / models / alembic 迁移 / 图谱 / 文档 + 测试 + evals

### 旧测影响面清单（B1 · 2026-09-22 10-task 实扫落盘）

> 扫描口径（真跑）：`ls tests/ | grep -iE 'continuity|session|lg_rag|summary|model_catalog|llm'`（命中 21 文件）· `grep -rln 'compress_window\|assemble_graph_messages\|load_session_turns\|MEMORY_FACTS_ENABLED\|resolve_task_model\|TASK_TYPES\|OPS_LLM_TIER\|历史摘要' tests/ evals/`（命中 5 测试文件：test_lg_rag_session_continuity / test_memory_injection / test_llm_routing + memory 面 3 文件与 eval 面与本波正交）· 各文件 `def test_` 计数（lg_rag_session_continuity 15 / session_continuity 2 / memory_injection 23 / llm_routing 17 / model_catalog 3 / llm_usage 6 / llm_retry 9 / llm_circuit 9）· `grep -rn 'TASK_TYPES\|TASK_TIER_MODELS' tests/`（**无枚举档集合内容的断言** · 仅 docstring 提及）· `grep -rn 'load_session_turns' app/`（仅定义 + `__init__` 导出 · 无生产调用方复核成立）· `grep -rn 'session.summary\|SESSION_SUMMARY' app/ tests/ evals/`（**零命中** · 无命名冲突）· `python -m pytest tests --collect-only -q`（=**1239**）· `alembic heads`（=`20260922_memory_kind_preference`）。本波行为变更源裁定：**装配层插入摘要面（off 逐字节一致）+ TASK_TYPES 扩 summary 档 + 新表迁移 + prompt 新资产**；`compress_window` 零改动 · 既有四档行为不变 · 既有开关语义不变，故影响面以**回归**为主、**改编为零**（实扫未发现依赖「档集合恰好四元」或「无 summary 档」的断言），**无测试删除**。处置三态：**回归**（不受影响，全波次重跑确认）/ **改编**（本清单无）/ **删除**（本清单无）。

| # | 锚点 | 旧测/调用点现状 | 本波影响 | 处置 |
|---|------|----------------|----------|------|
| 1 | `tests/test_lg_rag_session_continuity.py:65-84` compress_window 三用例 | 占位格式断言（`历史摘要` in content :72）· 短窗 noop（:76-78）· 失败降级截断（:81-84） | `compress_window` 零改动（钉死契约）→ 零改动全绿 | 回归（零改动 · off 态对拍钉死） |
| 2 | `tests/test_lg_rag_session_continuity.py` 其余 12 用例（装配 :90-109 · graph 集成 :247 等） | `assemble_graph_messages` 纯函数装配守护 | 纯函数面零改动 → 零改动全绿 | 回归（零改动） |
| 3 | `tests/test_memory_injection.py` 23 用例（off 对拍 :32-57 · 非法值 warning :60-63 · 注入位置 :99-126 · span :155+） | `assemble_graph_messages_with_memory` off 态与纯函数面逐字节一致守护 | 摘要面插入点在记忆注入**之前**且 off 态跳过 → 既有用例零改动全绿；on 态/全失败对拍为新增断言（见 #11） | 回归（零改动守护）+ 新增双对拍断言（新增义务 · 见 #11） |
| 4 | `tests/test_session_continuity.py` 2 用例 | sse_replay 纯函数（replay_events / cursor / payload） | 与本面正交（chat 轨零改动）→ 零改动 | 回归（零改动） |
| 5 | `tests/test_llm_routing.py:69-74` unknown-task 断言 | `resolve_task_model("summarize")` → `unknown_task` + warning | `"summarize"` ≠ `"summary"`：加档后仍 unknown → 语义不反转零改动全绿 | 回归（零改动 · 语义钉死） |
| 6 | `tests/test_llm_routing.py` 其余 16 用例（档解析序 · env 覆盖 :85-96 参数化 answer/extract/structured · answer 节点对拍） | 既有四档行为守护 | 参数化档集合不含新档、既有档行为不变 → 零改动；summary 档解析/env 覆盖/未知模型回退断言为新增（见 #11） | 回归（零改动）+ 新增 summary 档断言（新增义务 · 见 #11） |
| 7 | `tests/test_model_catalog.py` 3 用例 | SILICONFLOW_MODELS env / 默认兜底 | 与档路由正交 → 零改动 | 回归（零改动） |
| 8 | `tests/test_llm_usage.py` 6 用例 | task_type 自由 str 无枚举校验（:104-120 answer/grader 聚合先例） | usage 机制零改造自动继承 → 零改动；summary 归因落行断言为新增（见 #11） | 回归（零改动）+ 新增归因断言（新增义务 · 见 #11） |
| 9 | `tests/test_llm_retry.py`（9）· `tests/test_llm_circuit.py`（9）· `tests/test_llm_providers.py` | provider 包装层重试/熔断守护 | 新调用面自动继承零改造 → 零改动 | 回归（零改动） |
| 10 | `tests/eval/` 9 文件 + `evals/` 既有金样（memory redline / agent redlines 等） | evals 层守护 | 不触既有清单/实现 → 零改动；新金样为新增目录 `evals/session/`（见 #11） | 回归（零改动） |
| 11 | 新增义务：summary.py 单测（缓存 key/miss/写失败/超时降级/并发唯一约束）· off 三态 + on 全失败双对拍 · summary 档路由断言 · usage 归因断言 · 表结构断言 · prompt 资产锚点 + loader 显式炸 · 金样（`evals/session/summary_fidelity_v1.yaml` + `tests/eval/test_session_summary_fidelity.py`）· 变异检验三条 | 当前不存在 | 本波新增守护测试 + evals 金样（工程验收项）；collected 自 1239 增加，新增数入 40 记录 | 新增（30 实现 · 40 核验） |
| 12 | alembic 链 | head=`20260922_memory_kind_preference`（真跑 `alembic heads`） | 新迁移挂 head 后（建 `ops_session_summaries`）；既有迁移零改动 | 新增迁移文件（D5 · 可逆往返钉死） |

---

## 依赖

| 依赖 | 说明 |
|------|------|
| SPEC | `docs/spec/session-summary-fallback/SPEC-session-summary-fallback_v1.md`（signed · HG-SPEC-SIGNOFF=approved 2026-09-22 · 48ce63e） |
| 上游手册 | `../ops-desk-workspace/docs/08-interview/07_agent-memory-prompt-module-landscape_v1_zh.md`（§1.2.2 缺的一环 · §1.8 先把「坏了能发现」装上 · §1.9 反模式：摘要不可回退） |
| 编码规范 | `docs/standards/CODING_BACKEND_L2_v1_zh.md` |
| 图谱 | `docs/_tech_graph/l1/01_modules.md`（HG-GRAPH-MODULES 真值 · 2026-09-22 真读核验 · db 行 :33 / lg_rag 行 :27 / chat 行 :22 / llm 行 :32） |
| 改造对象 | `app/ops/lg_rag/continuity.py`（:27-62 压缩零改动 · :110-120 开关先例 · :219-283 装配接线点）· `app/ops/session/summary.py`（新增）· `app/llm/model_catalog.py`（:118/:122-127/:158-163 档扩展）· `app/db/models.py`（新 ORM 类）· `alembic/versions/`（新迁移挂 head `20260922_memory_kind_preference` 后） |
| prompt 资产 | `app/ops/prompts/assets/session.summary.system.md`（新增 v1）· `app/ops/prompts/loader.py:52-62`（显式炸纪律）· `app/ops/prompts/assets/README.md`（变量表同步） |
| 先例 · 默认关三件套 | `app/ops/lg_rag/continuity.py:110-120`（memory_facts_enabled）· `app/ops/memory/service.py`（vector recall 开关同款） |
| 先例 · extract 档 | `app/ops/memory/extract.py:43`（EXTRACT_TIMEOUT_S）· :99-114（分层路由 + use_run_context + wait_for 完整先例） |
| 先例 · 金样 | `evals/memory/preference_redline_v1.yaml` + `tests/eval/test_memory_preference_redline.py`（清单=实现一一对应 · 正反双断言 · 热路径零 LLM-as-judge）· `evals/agent/redlines/capability_v1.yaml` |
| 先例 · 新表图谱签录 | `docs/tasks/done/task_llm_layer_hardening.md`（ops_llm_usage 新表 · db 行登记 · HG-GRAPH-MODULES 00 代录「30 交付核验后」先例） |
| 测试锚点 | `tests/test_lg_rag_session_continuity.py` · `tests/test_memory_injection.py` · `tests/test_llm_routing.py` · `tests/test_llm_usage.py` |
| 格式基准 | `docs/tasks/done/task_memory_preference_profile.md`（signed → done 五棒全通 · PR #157） |

---

## 给执行帽的必读列表

1. `AGENTS.md`
2. 本 task（钉死契约 · 闸 · 非范围 · B1）
3. SPEC `docs/spec/session-summary-fallback/SPEC-session-summary-fallback_v1.md`（§1 锚点 / §2 D1–D5 / §4 方案裁决 L1+T2+C1 / §5 failure_paths / §6 验收 / §7 residual）
4. `docs/standards/CODING_BACKEND_L2_v1_zh.md`
5. 代码：`app/ops/lg_rag/continuity.py`（:27-62 · :98-120 · :219-283）· `app/ops/lg_rag/graph.py`（:153-215）· `app/llm/model_catalog.py`（:113-173）· `app/llm/usage.py`（:80-104）· `app/ops/prompts/loader.py`（:52-62）· `app/ops/memory/extract.py`（:43 · :99-114）· `app/db/models.py`（:250-320）
6. 先例：`tests/test_memory_injection.py:32-74`（off 对拍 + 非法值 warning 范式）· `tests/test_llm_routing.py:69-96`（unknown_task / 档参数化范式）· `evals/memory/preference_redline_v1.yaml` + `tests/eval/test_memory_preference_redline.py`（金样正反断言范式）
7. 测试：`tests/test_lg_rag_session_continuity.py` · `tests/test_memory_injection.py` · `tests/test_llm_routing.py` · `tests/test_llm_usage.py` · `tests/test_model_catalog.py`
8. `docs/harness/prompts/FRAGMENT_30_gate_verify_v1_zh.md`

---

## 思考轮控制

| 轮 | 结论 | early_stop | reason（early_stop） | residual_risks |
|----|------|------------|----------------------|----------------|
| R0 | SPEC signed（HG-SPEC-SIGNOFF=approved 2026-09-22 · 48ce63e）；范围 D1–D5 承 SPEC §2 不重开辩论；本帽实扫复核：分支正确（`task/session-summary-fallback`）· continuity compress_window :27-62 / 开关 :110-120 / 装配 :219-283 · graph.py :153/:187 调用 :170/:202 · load_thread_turns 于 lg_rag/router.py:203（SPEC 锚点「router.py:203」实址 = `app/ops/lg_rag/router.py`）· history.py 无生产调用方 · models.py :255/:260/:305-320 · model_catalog :118/:122-127/:158-163 · loader.py:52-62 · extract.py:43/:99-114 · assets README 变量表 :20-34 · usage.py task_type 自由 str · pytest 基线 **1239 collected**（真跑）· alembic head `20260922_memory_kind_preference`（真跑）· `session.summary`/`SESSION_SUMMARY` 零命名冲突——SPEC §1 锚点全部复核一致 | no | — | none |
| R1 | 开工闸：HG-TASK-DRAFT=approved · HG-AUDIT-R1=approved（2026-09-22 00 代录 · blocks 30 已放行）· HG-GRAPH-MODULES=approved（模块表已建置 · **真读** `01_modules.md`：db/lg_rag/chat/llm 四行覆盖全部改动面）+ **新签义务**（db 行新表登记 + 三行备注 + 人签新行 00 代录位随 30 交付落盘 · llm-layer-hardening 先例）+ 偏离回炉补闸条款 · HG-PILOT-OPSDESK-GLAYER=n/a | no | — | 无 |
| R2 | 竖切：D1–D5 同 task 一次提交（承 SPEC §2 波次裁定 · 五块不可拆语义单元）；实现序承 SPEC §8（D5 迁移+图谱 → D1 档+prompt 资产+生成服务 → D2 缓存 → D3 开关+对拍 → D4 评测）；方案对比继承 SPEC §4 三组裁决（L1 懒生成+缓存弃 L2/L3 · T2 新增 summary 档弃 T1 · C1 独立表弃 C2/C3），不重演 | no | — | 无 |
| R3 | failure_paths **14 条** = SPEC §5 十一条翻四列 + 过程三（闸未签拒开工 · B1 闸前置拒收 · 无双对拍/变异检验拒收）；三静默错（摘错造错误前提 / 缓存污染 / 回退开关失效）各有断言+变异检验兜底 | no | — | 无 |
| R4 | 验收 **26 条**全否定性断言化逐块映射 SPEC §6（人工闸 1 / D1×5 / D2×4 / D3×3 / D4×4 / D5×3 / 变异检验×3 / 工程×3）；B1 实扫 **12 行**落盘（回归×10 · 改编×0 · 新增×1 · 迁移×1 · 删除×0）；实扫确认无「档集合恰好四元」断言（unknown-task 用例用 `"summarize"` ≠ `"summary"` 语义不反转）——改编面为零钉死 | no | — | 超长会话 chunk 数线性增长的首压成本（承 SPEC §7 ② · usage 账可观测） |
| R5 | 可交 20-task-audit；与 SPEC 实质差异为零（B1 / 闸行留痕 / 基线数 / 扫描口径细化均为过程化落地）；HG-AUDIT-R1 待人签 | no | — | ① 金样 sentinel 覆盖不了全部会话形态（承 SPEC §7 ① · 灰度期人工抽检 + 一键回退兜底）；② 超长会话首压成本（承 SPEC §7 ②）；③ summary 档默认 None 沿用现网默认模型，灰度期质量不足经 `OPS_LLM_TIER_SUMMARY_MODEL` 调档无需改码（承 SPEC §7 ③） |

**actual_last_round**：R5 · **early_stop**：no · **residual_risks**：见 R4/R5

### R0 · 问题框定

SPEC 已签收，本 task 只做可执行化拆解：窗口压缩占位保窗不保语义（手册 §1.2.2）· 摘要必须可回退（§1.9 反模式）。本帽实扫复核：分支 `task/session-summary-fallback` 正确；`compress_window`（continuity.py:27-62）纯函数、占位条 :54、降级截断 :59-62（与 SPEC 一致 · **零改动对象**）；`assemble_graph_messages_with_memory`（:219-283）async 注入面先例在位（off 逐字节 docstring 明示）；`memory_facts_enabled`（:110-120）默认关三件套逐字可复刻；生产唯一入口 graph.py `_ainvoke_with_tracing`:153（调用 :170）/ `_astream_with_tracing`:187（调用 :202）；history 来源 `load_thread_turns`（thread_store.py:44 · 调用点 lg_rag/router.py:203 · SPEC 锚点实址复核一致）；`load_session_turns`（session/history.py:11-40）app 内无生产调用方（grep 实证仅 `__init__` 导出）；`ops_runs.query/answer`（models.py:255/:260 Text）与 `ops_lg_rag_turns`（:305-320 · docstring :306 提及「system 摘要」实扫属实 = 未实现旧设想）；`TASK_TYPES` 四档（model_catalog.py:118）· extract 档默认 None（:122-127）· env 覆盖校验（:158-163）· `resolve_task_model`（:140-173）；usage `use_run_context`（usage.py:80-87 · task_type 自由 str 无枚举）；prompt loader 显式炸（loader.py:52-62）；`EXTRACT_TIMEOUT_S=60.0`（extract.py:43）；assets README 变量表（:20-34 · `memory.extract.system v1 无变量` 行先例）；pytest 基线 **1239 collected**（真跑）；`alembic heads` = `20260922_memory_kind_preference`（真跑）；`session.summary`/`SESSION_SUMMARY` 全仓零命中（无命名冲突）。SPEC §1 锚点全部复核一致，**零措辞偏差**。

### R1 · 开工闸

HG-TASK-DRAFT / HG-AUDIT-R1 均 approved（2026-09-22 · R1 零阻塞 · 维护者授权 00 代录）；HG-GRAPH-MODULES **真读** `docs/_tech_graph/l1/01_modules.md` 核验：模块表已建置（bootstrap 签 2026-07-16 · 签录链完整至 :90 memory-preference-profile 行）；`db` 行（:33 · `app/db/**`, `alembic/**` · 新表登记先例 ops_llm_usage）· `lg_rag` 行（:27 · 覆盖 continuity 装配面）· `chat` 行（:22 · glob 含 `app/ops/session/**` 覆盖新增 `session/summary.py`）· `llm` 行（:32 · 覆盖 model_catalog 档扩展）均在表。SPEC §2 D5 判**有图谱义务按实判**：新表 `ops_session_summaries` 登记 db 行 + 三行备注 + 人签记录**新行留 00 代录位**（随 30 交付落盘 · llm-layer-hardening「00 代录 · 30 交付核验后」先例）——不新增一级模块/路由/SSE 事件，义务钉 D5 验收不阻塞 30 开工形态预判；**回炉补闸条款**钉死（偏离 → 退 10-spec + 补闸 + 图谱如实登记）。HG-PILOT-OPSDESK-GLAYER=n/a。

### R2 · 竖切

承 SPEC §2 波次裁定：五块（生成通路 / 缓存与版本归因 / 一键回退 / 保真度金样 / 表结构图谱文档）是一个不可拆语义单元——只生成不配缓存/版本标记 = 重复付费且不可归因；不配一键回退 = 违反铁律（回退是上线前提）；不配保真度金样 = 违反手册 §1.8「先把坏了能发现装上再让功能上线」；耦合面小（装配面增量 + 一个生成服务 + 一张缓存表 + 一个 prompt 资产 + evals），单 PR 不巨型。实现序承 SPEC §8：D5 迁移+图谱（建表先行 · off 态不读不写故迁移与开关解耦）→ D1 summary 档+prompt 资产+生成服务 → D2 缓存 → D3 开关+双对拍 → D4 评测收口。方案对比不重演，直接继承 SPEC §4 三组裁决（L1 懒生成+DB 缓存弃 L2 离线/L3 混合 · T2 新增 summary 档弃 T1 复用 extract · C1 独立表弃 C2 写回 turns/C3 进程内）。

### R3 · 失败语义

SPEC §5 十一条失败面全收并翻四列：三静默错（摘错造错误前提 / 缓存污染 / 回退开关失效）各有断言 + 变异检验兜底；on 态全失败单 chunk 降级占位（≠ 全局回退开关 · 双对拍钉死两者各自语义）；缓存写失败不挡主流程；version/model 不符结构上不可能（key 含二者）；格式漂移锚点断言；成本失控/并发双生成列残余或容忍；跨 thread 泄漏由 key 含 thread_id + 既有归属校验兜；prompt 资产事故 = 整体降级占位不炸请求。补过程三行：闸未签拒开工 · B1 未落盘拒收 · 无双对拍/无变异检验三条拒收（防空真规则）。

### R4 · 可测性

验收 **26 条**全部可执行断言：`compress_window` git 级零 diff · 三标记锚点断言 · summary 档路由/env 覆盖/usage 归因断言 · prompt 资产锚点 + loader 显式炸 · 超时降级时序断言 · 表结构/唯一约束/FK CASCADE 断言 · 命中零 LLM 调用 mock 计数 · key 铁律 miss 单测 · off 三态对拍 + on 全失败对拍逐字节 · env 重读即时生效 + off 零 LLM 零缓存读写 mock 计数 · 金样清单一一对应 + sentinel 正反双断言 + 空摘要假通过防线 · 热路径零 LLM-as-judge · alembic 可逆往返 + 回滚注释 · 图谱登记 + graph-compile 绿 · 文档同步 · ruff 零新增 + diff 白名单。B1 实扫落盘 **12 行**：回归×10 · **改编×0**（实扫确认：tests 全仓无枚举 TASK_TYPES 内容的断言；unknown-task 用例用 `"summarize"` 与新档 `"summary"` 不同词，语义不反转；既有四档参数化集合不含新档不受影响）· 新增×1（守护测试 + evals 金样义务 #11）· 迁移×1（#12）· **删除×0**。

### 自检结论

（40 核验回填位 · 10-task 落稿阶段为空 · 40 验收后按实测回填）

### R5 · 交接就绪

思考充分可交 20-task-audit；与 SPEC 逐条核对**实质差异为零**（验收 26 条 = SPEC §6 各块 + 人工闸行 + 闸前置 B1，均过程化落地；SPEC §1 锚点复核零偏差 · 「router.py:203」实址补全为 `app/ops/lg_rag/router.py:203` 属锚点精确化非偏差）。残余风险三条全承 SPEC §7：金样 sentinel 覆盖盲区（灰度人工抽检 + 一键回退兜底）；超长会话首压成本线性（usage 账可观测 · 真出现再议离线预热另案）；summary 档默认 None 沿用现网默认模型（灰度期经 env 调档无需改码）。

---

## 修订

| 日期 | 说明 |
|------|------|
| 2026-09-22 | 10-task 落稿 · R0–R5 全轮无 early_stop · 验收 **26 条**逐块映射 SPEC §6 实质零差异（人工闸 1 / D1×5 / D2×4 / D3×3 / D4×4 / D5×3 / 变异检验×3 / 工程×3）· B1 旧测影响面 **12 行**实扫落盘（口径：tests grep 命中 5 文件 · 无枚举档集合断言 · unknown-task 用例 `"summarize"`≠`"summary"` 语义不反转 · 用例计数 8 文件 · pytest 基线 **1239 collected** 真跑 · `alembic heads`=`20260922_memory_kind_preference` 真跑 · `session.summary` 零命名冲突）· SPEC §1 锚点复核零偏差 · HG-TASK-DRAFT/HG-AUDIT-R1 落稿时待签 → 2026-09-22 00 代录 approved（R1 零阻塞）· HG-GRAPH-MODULES=approved（模块表已建置真读核验）+ 新签义务（db 行新表 + lg_rag/chat/llm 行备注 + 人签新行 00 代录位 · 偏离回炉补闸）· HG-PILOT-OPSDESK-GLAYER=n/a |
