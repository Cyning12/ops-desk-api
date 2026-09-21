# SPEC：会话记忆真摘要（可回退原文）（v1）

> **状态**：`signed`（HG-SPEC-SIGNOFF=**approved**（2026-09-22 · 维护者授权 00 本窗签收全部过程文档 · 原话「此spec完成后继续把完成后续spec，一个个进行，每次PR到main通过CI后自动merge」承前令「授权00签收所有过程文档」） · 人签前不出 task / 不改码）
> **track**：`feature`（新 LLM 调用面（摘要档）+ 新 prompt 资产 + **新表 ops_session_summaries（有 alembic 义务）** + 图谱义务按实判见 §2 D5）
> **上游**：`../ops-desk-workspace/docs/08-interview/07_agent-memory-prompt-module-landscape_v1_zh.md`（手册 §1.2.2「明确知道缺的一环」· §1.9 反模式：摘要不可回退）
> **格式基准**：`docs/spec/memory-preference-profile/SPEC-memory-preference-profile_v1.md`（signed · 2026-09-22）
> **下游**：人签 SPEC → 00 出 task → 20-task-audit → HG-AUDIT-R1 → 30 实现
> **Open Folder（实现）**：`ops-desk-api/`

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **spec_slug** | `session-summary-fallback` |
| **invoke_slug** | `session-summary-fallback`（单 task · 波次裁定见 §2） |
| **test_strategy** | `required` |
| **test_strategy_note** | 纯函数对拍（关态与占位逐字节一致）· 缓存 key/命中/降级单测 · 开关非法值回退断言（continuity 先例）· 保真度金样 sentinel 包含/排除断言（evals/ · 热路径零 LLM-as-judge · 参照 evals/memory/preference_redline_v1.yaml 先例）· 变异检验三条（见 §6）· alembic upgrade head + 全量 pytest 绿 |
| **Open Folder（实现）** | `ops-desk-api/` |
| **默认分支** | `task/session-summary-fallback` |
| **graph_change_layer（建议）** | **有图谱义务按实判**：新增表 `ops_session_summaries`（docs/_tech_graph l1 数据面 + HG-GRAPH-MODULES 行）；不新增路由/SSE 事件类型/一级模块（摘要逻辑落既有 `app/ops/session/` 与 `app/ops/lg_rag/continuity.py` 模块内）。若 30 形态偏离（新增路由/事件/一级模块）→ 回 10-spec 修订 |

### 人工闸（SPEC 阶段）

| human_gate_id | status | 说明 |
|---|---|---|
| **HG-SPEC-SIGNOFF** | **approved** | 待人签；签前不出 task / 不改码 |
| **HG-GRAPH-MODULES** | **pending（按实判 · 有义务）** | 新表 `ops_session_summaries` 落 `docs/_tech_graph/l1/01_modules.md` 数据面；30 前须 approved |

---

## 1. 背景与目标

当前窗口压缩 = **截断 + 占位标记**（占位符只有轮数 + 角色，无内容）——保住窗口有界，没保住语义连续（手册 §1.2.2「明确知道缺的一环」）。本 SPEC 引入真摘要，**铁律：摘要必须可回退到原文**（摘错 = 静默造错误前提；回退路径是摘要上线的前提，不是可选项）。

### 现状（2026-10-12 实扫 · 锚点逐个核 · continuity-dedup 波次收敛后形态为准）

| 锚点 | 实扫结论 |
|---|---|
| `app/ops/lg_rag/continuity.py` | `compress_window`（:27-62）**纯函数无 IO**：保留最近 `max_full_turns=6` 轮全量，更早轮次按 `group_size=2` 合并为占位 `[历史摘要 · N 轮 · roles=...]`（:54 · 只有轮数+角色零内容）；压缩失败降级截断（:59-62）。`assemble_graph_messages`（:65-92）纯函数装配；`assemble_graph_messages_with_memory`（:219-283）已是 **async + 可选 IO 注入面**（memory-facts-p0/p1 先例：开关默认关、关闭时与纯函数面逐字节一致、故障降级不拖垮请求、span 计数）——**本 SPEC 摘要面复刻此先例形态** |
| 生产调用面 | `compress_window` 唯一生产入口 = lg_rag `graph.py` `_ainvoke/_astream_with_tracing`（:170/:202 → assemble_graph_messages_with_memory）；history 来自 `thread_store.load_thread_turns`（router.py:203 · **全量无 limit**，压缩在内存收口） |
| `app/ops/session/history.py` | `load_session_turns`（:11-40）从 `ops_runs` 加载最近 20 条 run 的 user/assistant 轮；**实扫 app/ 内无生产调用方**（仅 `session/__init__.py` 导出）——chat 轨历史面，本 SPEC 零改动 |
| 原文保留面 | `ops_runs.query/answer`（models.py:255/:260 · Text 原文）与 `ops_lg_rag_turns`（models.py:305-320 · role/content Text 原文 · thread SoT）**原文均在库、保留现状**；`OpsLgRagTurn` docstring（:306）虽提及「system 摘要」role，但 `persist_thread_turns`（thread_store.py:62-99）只写 user/assistant——**摘要不得写入 turns 表**（污染原文 SoT · 缓存污染静默错，见 §5） |
| LLM 调用面（llm-layer-hardening 已收敛） | 分层路由 `resolve_task_model`（model_catalog.py:140-173）：`TASK_TYPES=("answer","grader","extract","structured")`（:118），`TASK_TIER_MODELS` extract 档默认 None（:122-127 · 不落档沿用现网默认）；env 档覆盖 `OPS_LLM_TIER_<TASK>_MODEL` 且校验已知模型目录（:158-163）。重试（retry.py · `OPS_LLM_RETRY_ENABLED` 默认开）+ provider 级熔断（circuit.py · `OPS_LLM_CB_ENABLED` 默认开）已在 provider 包装层，**新调用面自动继承零改造**。usage 落表 `ops_llm_usage` 经 ContextVar（usage.py · `use_run_context` · task_type 归因）；memory 抽取是 **extract 档 + background 面**的完整先例（extract.py:99-114） |
| prompt 资产化（阶段一后） | 模板落盘 `app/ops/prompts/assets/<template_id>.md`（front-matter `template_id`/`version` · loader.py:56 读取 · 缺文件/缺字段/空 body/版本非法**显式炸不静默降级**）；`render("memory.extract.system")` 无变量、window 经 user 消息传入（extract.py:105-106）——摘要模板复刻此形态；文案变更走 assets README 路径（bump version · 锚点断言非全文快照） |
| 默认关先例（memory-facts-p1 双开关） | `MEMORY_FACTS_ENABLED`（continuity.py:110-120）与 `MEMORY_FACTS_VECTOR_RECALL_ENABLED`（service.py:292-303）均**默认 false · 非法值回退 false + warning · 关闭时与旧路径逐字节一致**——本 SPEC 摘要开关完全复刻此三件套 |

### 一句话目标

在 lg_rag 装配面把占位符升级为**真摘要**：结构仍由纯函数 `compress_window` 定（零改动），内容替换走新 async 摘要面——**请求时懒生成 + DB 缓存**（内容哈希 key），摘要带**版本与来源标记**，原文表零改动可查；**`SESSION_SUMMARY_ENABLED` 默认关、关闭/失败/回退均与占位模式逐字节一致**；保真度金样以 sentinel 结构/对照断言为否决面（热路径零 LLM-as-judge）。

---

## 2. 范围

**波次裁定：单 task（slug `session-summary-fallback`），五块不拆波。** 理由：① 真摘要是一个不可拆的语义单元——只生成不配缓存/版本标记 = 重复付费且不可归因；不配一键回退 = 违反铁律（回退是上线前提）；不配保真度金样 = 违反手册「先把"坏了能发现"装上，再让功能上线」（§1.8）；② 耦合面小（装配面增量 + 一个生成服务 + 一张缓存表 + 一个 prompt 资产 + evals），单 PR 不巨型；③ track 同为 feature，无混 track 问题。

### D1 · 真摘要生成通路（必做 · 请求时懒生成 · 方案 L1 见 §4）

| 项 | 约定 |
|---|---|
| 落点 | 新增 `app/ops/session/summary.py`（既有 session 模块内 · 不新增一级模块）：`async def summarize_placeholders(compressed: list[dict], *, thread_id: str) -> list[dict]`——输入 `compress_window` 产物，把每个占位条（`[历史摘要 · N 轮 · roles=...]`）替换为真摘要条；**结构（轮数切分/条数/顺序/尾部全量轮）由 compress_window 定，零改动**；内容替换才是本面职责 |
| 装配接线 | `assemble_graph_messages_with_memory` 内、记忆注入**之前**：`compress_window` → （开关 on）`summarize_placeholders` → 装配消息。开关 off → 跳过本面，与现网**逐字节一致**（对拍断言钉死） |
| 懒生成 | 每个占位 chunk：按 chunk 源 turns 内容查缓存（D2）→ miss 才调 LLM；chunk 边界由 `max_full_turns/group_size` 决定、内容哈希随窗口滑动自动失效，**无主动失效逻辑** |
| LLM 调用 | 走**新增 `summary` 档**（§4 T2）：`TASK_TYPES` 与 `TASK_TIER_MODELS` 加 `"summary": None`（None = 不落档沿用现网默认 · 与 extract 档同语义）；env 覆盖 `OPS_LLM_TIER_SUMMARY_MODEL`（已知目录校验沿用）；`use_run_context(run_id=…, surface="lg_rag", task_type="summary")` → `ops_llm_usage` 自动归因（llm-layer-hardening D4 机制零改造）；重试/熔断由 provider 包装层自动继承 |
| 超时与降级 | 单次摘要调用包 `asyncio.wait_for`（超时常量 · extract.py EXTRACT_TIMEOUT_S 先例）；**任何失败（LLM/超时/熔断/解析）→ 该 chunk 保留占位符**，log + span `session_summary_degraded=N`（N=降级 chunk 数）；**永不阻塞主答、绝不产出半摘要** |
| prompt 资产 | 新增 `app/ops/prompts/assets/session.summary.system.md`（v1 · front-matter · 无变量，chunk turns 经 user 消息传入 · memory.extract.system 先例）；`render("session.summary.system")`；缺文件/版本非法显式炸（loader 纪律沿用）；模板正文须含「不得新增原文没有的事实」级指令；锚点断言守「摘要」「不得新增」级语义（非全文快照） |
| 摘要条标记 | 真摘要条 content 形如 `[历史摘要 · v1 · N 轮 · 模型:<model> · 有损压缩，细节以最近轮为准]` + 摘要正文——**版本 + 来源 + 有损声明**三标记进上下文（模型可见「这是摘要不是原文」）；占位条格式**零改动** |

### D2 · 原文保留 + 摘要缓存与版本/来源落库（必做）

| 项 | 约定 |
|---|---|
| 原文保留 | `ops_lg_rag_turns` / `ops_runs` **零改动**（不加列、不改写入、不回填）；原文可查 = 现状即满足（thread turns 全量在库）；**摘要行与原文行物理分表** |
| 缓存表 | 新表 `ops_session_summaries`：`id` · `thread_id`（FK → ops_lg_rag_threads · ondelete CASCADE）· `chunk_hash`（sha256(prompt_version + model + chunk turns canonical JSON)）· `summary`（Text）· `prompt_version` · `model` · `turn_count` · `source`（恒 `"llm"` · 预留未来 heuristic）· `created_at`；**唯一约束 (thread_id, chunk_hash)** |
| 缓存 key 铁律 | key **必含内容哈希 + prompt 版本 + 模型**——只用 (thread_id, 序号) 会在窗口滑动后命中旧摘要 = **缓存污染静默错**（§5）；hash 变 = 自然 miss 重生成，无失效逻辑 |
| 写缓存 | 生成成功才写（get-or-create · 唯一约束冲突 = 并发同 key 先写赢，内容同参数语义等价，容忍）；写缓存失败 → log + 本次仍用摘要（缓存是优化不是正确性依赖） |
| 版本归因 | `prompt_version`/`model` 落库 + 进上下文标记（D1）；改 prompt 必须 bump version（assets README 纪律）→ key 变自然重生成 |

### D3 · 可配置一键回退占位模式（必做 · 铁律：回退路径是上线前提）

| 项 | 约定 |
|---|---|
| 主开关 | `SESSION_SUMMARY_ENABLED`：**默认 false**；非法值回退 false + warning（continuity.py:110-120 三件套先例逐字复刻） |
| 回退语义 | **回退 = 关开关**：off（未设/false/非法）→ 装配输出与占位模式**逐字节一致**（对拍断言钉死 · memory-facts-p0 同款纪律）；不发版、不动数据、即时生效（env 重读 · 进程内无状态） |
| 灰度纪律 | 默认关上线 → 灰度环境 env 开 → 观测（span `session_summary_degraded` / `ops_llm_usage` task_type=summary 账 / 摘要条占比）→ 全量；异常即关 env 回退，**回退动作本身零代码零迁移**（缓存表留库无害 · off 态不读不写） |
| 失败降级 ≠ 回退开关 | on 态运行期降级（D1）是**单 chunk 粒度**自动行为（保留该 chunk 占位）；回退开关是**全局粒度**人工/运维行为；两者各自断言不混淆 |
| 上线前提断言 | 验收必须证明：off 对拍逐字节一致 + on 态全链路失败时输出与 off 态逐字节一致（强制 LLM 全失败的变异检验 ③）——**两条都过才允许合入** |

### D4 · 保真度评测金样（必做 · 否决面确定性 · 热路径零 LLM-as-judge）

| 项 | 约定 |
|---|---|
| 判定面裁定 | **优先结构/对照断言，禁用 LLM-as-judge 作否决面**（手册 §1.8 纪律 · 参照 evals/memory/preference_redline_v1.yaml：判定面是「注入上下文」的结构，不是对模型自由文本的语义裁判） |
| 金样形态 | `evals/session/summary_fidelity_v1.yaml`（清单 · 声明=实现 P0 同款）+ `tests/eval/test_session_summary_fidelity.py` 一一对应；金样输入 = **固定 turns 夹具**（内含 sentinel 关键事实：专有编号/实体 token，如 `OD-7391`、`repo:ops-desk-api`） |
| 关键事实不丢（正向） | 对「给定 turns + 候选摘要」的**确定性校验函数**：sentinel 集合 ⊆ 摘要文本（token 包含断言 · 非语义判定）；金样逐条声明 must_keep 集合 |
| 不新增原文没有的内容（反向对照） | 金样含 `must_not_add` 禁忌 sentinel 集合（原文不存在的编号/实体），断言摘要**不含**任一项；只做正向会得到假通过（空摘要天然满足 must_not_add）——**正反双断言缺一不算过**（preference_redline 正反对照先例） |
| 对真模型产出 | 离线 eval 可对真模型跑（sentinel 断言机检 · 打模型归 evals 层纪律）；CI 热路径用**录制/夹具摘要**跑同一校验函数（确定性）；真模型抽检的语义层判断（流畅性/轻微转述）列人工审阅，**不作 CI 否决面** |
| 上下文结构断言 | 摘要模式装配产物：占位条被替换后**零占位格式残留**、每条摘要条含版本/来源/有损三标记；off 态产物与现网逐字节一致（D3 对拍） |

### D5 · 表结构 / alembic / 图谱 / 文档（必做 · 按实判）

- **alembic 义务：有**。迁移建 `ops_session_summaries`（§2 D2 字段 + 唯一约束 + FK CASCADE）；存量零数据迁移；回滚 = drop table（off 态不读不写 · 回滚安全写入迁移注释）。models.py 同步新增 ORM 类。
- **图谱义务：有（按实判）**。新表落 `docs/_tech_graph/l1/01_modules.md` 数据面 + HG-GRAPH-MODULES 行（30 前须 approved）；不新增路由/SSE 事件类型/一级模块。若 30 形态偏离 → 回 10-spec 修订。`./scripts/graph-compile.sh` 绿（回归保险）。
- 文档同步：`app/ops/session/` 模块说明（env 表补 `SESSION_SUMMARY_ENABLED`/`OPS_LLM_TIER_SUMMARY_MODEL` · 故障语义：降级占位 + span 标记）；`app/ops/prompts/assets/README.md` 变量集合表补 `session.summary.system v1 无变量`；不回改 done/归档历史文档。

---

## 3. 非范围

- ❌ **改窗口压缩的轮数策略**（`max_full_turns=6`/`group_size=2` 不变 · 占位草案原文保留）；`compress_window` 纯函数体零改动（continuity-dedup 波次刚收敛此文件 · 改动面压在装配层）
- ❌ 改 SSE / 新增 SSE 事件类型（占位草案原文保留）；摘要过程对用户不可见（span/log 可观测）
- ❌ 对话记忆进长期记忆 / 跨会话摘要（memory 轨的事 · 占位草案原文保留）
- ❌ **离线批量预生成 / 回填历史 thread**（方案对比弃选 · §4 L2/L3；未来另案 SPEC 自带触发面与成本预算义务）
- ❌ chat 轨（`ops_runs`/`load_session_turns`）摘要化——该面实扫无生产调用方，原文保留现状零改动；lg_rag 之外接入另案
- ❌ 摘要写回 `ops_lg_rag_turns`（role=system 摘要行）——污染原文 SoT，物理拒收（缓存独立表是 §4 C1 裁决）
- ❌ 增量/滚动摘要（摘要的摘要 · 摘要链压缩）；多级压缩策略
- ❌ LLM-as-judge 评测面（任何形态）；语义相似度打分作 CI 否决面
- ❌ 多副本缓存共享层（Redis 等）——DB 表即共享面，进程内缓存在非范围（§4 C3 弃选理由）
- ❌ 摘要管理/审计 UI（web/ios 另案）；对外 HTTP 读端点
- ❌ 历史文档回改

---

## 4. 方案对比（R2）

### 摘要生成时机（D1 · 核心裁定）

| 方案 | 做法 | 收益 | 代价 | 裁决 |
|---|---|---|---|---|
| **L1 · 请求时懒生成 + DB 缓存（本 SPEC）** | 装配面发现占位 chunk → 查缓存 → miss 才调 LLM → 写缓存 | **成本按需**：短会话（≤6 轮永不压缩）零调用零账面；缓存命中后延迟摊销为零（chunk 内容哈希不变即命中）；失败降级占位 = 现状形态，回退铁律天然成立；触发面已在请求路径（无新触发器） | 首次压缩的那一次请求多一次 LLM 调用延迟（extract 档级 · 秒级），超时兜底降级 | **推荐** |
| L2 · 离线生成（persist_thread_turns 后 fire-and-forget） | 每轮 done 后异步预算摘要 | 请求路径零新增延迟 | **为不确定的未来付费**：生成时不知道会话会不会超窗，短会话全部白调（ops_llm_usage 账面膨胀 · 与懒生成同量级的调用却大面积浪费）；触发面耦合 persist 失败语义；超窗前生成的摘要因窗口滑动 hash 失效重生成——预付成本打水漂 | 弃 |
| L3 · 混合（懒生成 + 离线预热长会话） | L1 为主 + 对已超窗 thread 离线预热 | 首压延迟消除 | 两套触发面 + 预算逻辑（哪些 thread 值得预热）复杂度；收益只在「长会话首压一次」，不成比例 | 弃（预热留作未来另案入口 · L1 架构不排斥） |

### 摘要调用的模型分档（D1）

| 方案 | 做法 | 收益 | 代价 | 裁决 |
|---|---|---|---|---|
| **T2 · 新增 `summary` 档（本 SPEC）** | `TASK_TYPES`/`TASK_TIER_MODELS` 加 `"summary": None`；`OPS_LLM_TIER_SUMMARY_MODEL` 覆盖；usage `task_type="summary"` | 摘要与抽取**延迟预算不同**（懒生成在请求路径 · extract 是 background 面）——独立档可独立调便宜/快模型不互相误伤；usage 归因干净（ops_llm_usage 可按 task_type 单看摘要账）；扩展面是 model_catalog 既有模式（加一行档默认 + 一档 env） | TASK_TYPES 元组扩一项（小改 · unknown_task 回退纪律覆盖） | **推荐** |
| T1 · 复用 extract 档 | `resolve_task_model("extract")` · `OPS_LLM_TIER_EXTRACT_MODEL` 共用 | 零新档 | extract 档调参（为 background 抽取选强模型）会直接抬请求路径摘要延迟/成本；usage 账上摘要与抽取混记无法归因；两调用面演进互相绑架 | 弃 |

### 摘要缓存面（D2）

| 方案 | 做法 | 收益 | 代价 | 裁决 |
|---|---|---|---|---|
| **C1 · 独立表 ops_session_summaries（本 SPEC）** | 新表 · (thread_id, chunk_hash) 唯一 · 版本/模型/来源落列 | 原文 SoT 零污染（铁律：摘要与原文物理分表）；多副本天然共享；版本归因可查（哪版 prompt 哪个模型产的）；CASCADE 随 thread 清理 | 有 alembic + 图谱义务（按实判已列 D5） | **推荐** |
| C2 · 写回 ops_lg_rag_turns（role=system 摘要行） | 摘要作 turn 落 thread 表 | 零新表 | **污染原文 SoT**：`load_thread_turns` 全量读回 → 摘要行再次进入压缩输入（摘要的摘要 · 失真复利）；原文保留可查纪律被破坏（原文行与衍生行混表）；docstring 提及「system 摘要」是**未实现的旧设想**（persist 只写 user/assistant 实扫为准），不构成立项依据 | 弃 |
| C3 · 进程内缓存（dict） | 进程内存 (thread_id, hash) → summary | 零表零迁移 | 多副本不共享（每副本各付一次首压成本）；重启全失；不可审计（版本归因无从查）；与 ops_llm_usage 账面对不上 | 弃 |

---

## 5. 边界 / 失败路径 / 安全（failure_paths）

| 触发 | 行为 | 可重试 |
|---|---|---|
| **摘错造错误前提**（摘要与原文矛盾 / 丢关键事实，模型基于错误前提回答） | **静默错**；防线三层：① D4 金样 sentinel 正反断言（must_keep/must_not_add）否决面上线前拦；② 摘要条带「有损压缩」标记（模型可见边界）；③ 一键回退（D3）+ 原文全量在库可查可对账；列残余风险（§7 ①——金样覆盖不了全部会话形态） | Y（关开关回退） |
| **缓存污染**（窗口滑动后 chunk 内容变，仍命中旧摘要） | **静默错**；key 必含内容哈希铁律（D2）物理防：内容变 → hash 变 → 自然 miss；单测钉死「同序号不同内容 → miss」；唯一约束 (thread_id, chunk_hash) | Y（修 key） |
| **回退开关失效**（设了 off 仍走摘要 / 非法值被当 on） | **静默错**；off/未设/非法值 → 装配输出与占位模式**逐字节一致**对拍断言钉死（变异检验 ①：临时反转开关解析 → 对拍必挂）；非法值 warning 日志（continuity 先例） | Y（修解析） |
| on 态 LLM 全失败（熔断 open / 超时 / 4xx） | 该 chunk **保留占位符**降级（非整窗失败）；span `session_summary_degraded=N` + log；输出与 off 态逐字节一致（变异检验 ③ 钉死）；**永不阻塞主答、绝无半摘要条** | Y（自动 · 下请求重试） |
| 缓存写失败（DB 故障 / migration 未跑） | log + 本次仍用生成的摘要（缓存是优化不是正确性依赖）；读取失败视同 miss 走生成/降级链；不挡主答（usage.py 落表纪律同款） | Y |
| 缓存读命中但 prompt_version/model 与当前不符 | key 已含 version+model → 结构上不可能（同 key 同参数）；改 prompt 未 bump version 才可能 → assets README 纪律 + CI 锚点断言兜底（改 body 必须 bump version） | — |
| 摘要条格式漂移（丢版本/来源/有损标记） | 锚点断言（摘要条含「历史摘要」+「有损」级锚点 + model 标记）必挂 CI；非全文快照（prompt-asset 先例） | Y（改文案） |
| 摘要成本失控（长会话多 chunk 逐请求生成） | 每 chunk 仅 miss 时一次调用 · 命中零成本；`ops_llm_usage` task_type=summary 可归因对账；span 计数生成/降级；列残余风险（§7 ②——超长会话 chunk 数线性增长的首压成本） | — |
| 并发同 chunk 双生成（两请求同 miss） | 唯一约束先写赢 · 后者冲突即读已写行（同 key 同参数语义等价 · 容忍）；代价 = 偶发一次重复 LLM 调用（账面可查 · 不列验收） | Y |
| 摘要调用泄漏 tenant/user（跨 thread 读缓存） | key 含 thread_id · thread 归属校验在 router 既有面（resolve_thread_for_user · 跨用户 404）；本面不引入新身份语义 | Y |
| prompt 资产缺失/版本非法 | loader **显式炸**（不静默降级为空模板）；但调用面 try 包住 → 降级占位（D1 任何失败降级）——资产事故表现为「摘要面整体降级占位 + log」，不表现为炸请求 | Y（补资产） |

安全：无新凭证面/网络面（复用既有 provider 层）；不新增对外端点/SSE 事件；摘要内容含会话历史 → 缓存表与原文表同库同级别（无新增数据暴露面）；身份（tenant/user/thread）取自请求上下文既有校验链，模型产出不得参与（memory 纪律沿用）。

---

## 6. 验收标准（单 task 直接可用）

### D1 · 生成通路

- [ ] `compress_window` 函数体零 diff（git 级断言 · continuity-dedup 收敛形态保护）；占位条格式逐字节不变
- [ ] on 态：占位 chunk 被真摘要条替换；摘要条含版本（v1）+ 来源（model）+「有损」三标记（锚点断言）
- [ ] LLM 调用走 `summary` 档：`resolve_task_model("summary")` 生效；`OPS_LLM_TIER_SUMMARY_MODEL` 覆盖生效且校验已知目录；`ops_llm_usage` 落行 `task_type="summary"` / `surface="lg_rag"`
- [ ] `session.summary.system.md` v1 资产存在 · front-matter 合法 · 锚点断言（「摘要」「不得新增」级）；loader 缺文件显式炸（单测）
- [ ] 单次调用超时 → 该 chunk 降级占位 + span `session_summary_degraded`；主答零阻塞（时序断言）

### D2 · 缓存与版本归因

- [ ] `ops_session_summaries` 表结构断言（列/唯一约束/FK CASCADE）；生成成功才写；命中后**零 LLM 调用**（mock provider 调用计数断言）
- [ ] key 铁律单测：同 thread 同序号**不同内容** → miss 重新生成（缓存污染防线）；改 prompt_version/model → miss
- [ ] 缓存写失败 → 主流程仍返回摘要 + log；读失败视同 miss
- [ ] `ops_lg_rag_turns`/`ops_runs` 零改动（迁移 diff 断言 · 无 system 摘要行写入 turns 表）

### D3 · 回退开关（上线前提）

- [ ] **off 对拍**：`SESSION_SUMMARY_ENABLED` 未设 / false / 非法值 → 装配输出与现网占位模式**逐字节一致**（三态全断言 · 非法值 warning 日志断言）
- [ ] **on 态全失败对拍**：强制 LLM 调用全失败 → 装配输出与 off 态**逐字节一致** + span 降级标记
- [ ] 开关 env 重读即时生效（进程内无缓存态断言）；off 态**零 LLM 调用、零缓存读写**（mock 计数断言）

### D4 · 保真度金样

- [ ] `evals/session/summary_fidelity_v1.yaml` 与 `tests/eval/test_session_summary_fidelity.py` 一一对应（清单 P0 同款断言）
- [ ] 正向：金样 must_keep sentinel 集合 ⊆ 摘要文本（逐条断言）
- [ ] 反向：must_not_add 禁忌集合逐项不在摘要中；**正反双断言缺一不算过**（空摘要假通过防线：must_keep 非空断言）
- [ ] 热路径零 LLM-as-judge（CI 用夹具/录制摘要跑校验函数；真模型离线抽检归 evals 层 · 不作 CI 否决面）

### D5 · 表结构 / 图谱 / 文档

- [ ] alembic 迁移：`alembic upgrade head` 后摘要通路冒烟过；回滚注释含「off 态不读不写 · drop 安全」
- [ ] `docs/_tech_graph/l1/01_modules.md` 补新表 + HG-GRAPH-MODULES=approved；`./scripts/graph-compile.sh` 绿；无新增路由/SSE 事件/一级模块（偏离 → 本 SPEC 回炉）
- [ ] 文档：session 模块 env 表补两 env + 故障语义；assets README 变量表补 `session.summary.system v1 无变量`

### 变异检验（不验收空真规则）

- [ ] ① 开关可检：临时让开关解析恒 true → off 对拍断言必挂；恢复后全绿
- [ ] ② 缓存可检：临时让 key 去掉内容哈希（只留序号）→ 「同序号不同内容 miss」单测必挂；恢复后全绿
- [ ] ③ 降级可检：on 态强制 LLM 全失败 → 输出与 off 态逐字节一致 + `session_summary_degraded` 标记出现（缺标记不算过——「静默降级」与「根本没走摘要面」必须可区分）

### 工程

- [ ] 全量 `pytest tests` 绿；`ruff check app tests` 绿；生产路径 diff 只含：continuity 装配层/session 新模块/model_catalog 档/prompt 资产/models/alembic/图谱/文档/测试/evals

---

## 7. 思考轮控制（10-spec）

| 轮 | 结论摘要 | 状态 |
|---|---|---|
| R0 | 上游手册 §1.2.2（占位保窗不保语义）+ §1.9（反模式：摘要不可回退）；实扫确认/纠正占位：① `compress_window` 是纯函数（continuity-dedup 波次收敛后形态），生产唯一入口 = lg_rag graph.py；② `session/history.py` app 内**无生产调用方**（chat 轨原文面，零改动）；③ 原文面 `ops_lg_rag_turns`/`ops_runs` 原文在库保留现状；④ llm-layer-hardening 已收敛：分层路由四档（answer/grader/extract/structured · extract 档默认 None）+ 重试/熔断 provider 层自动继承 + usage ContextVar 归因——摘要调用新增 `summary` 档即接全套；⑤ prompt 资产化阶段一形态 = assets/<id>.md + front-matter + loader 显式炸；⑥ `OpsLgRagTurn` docstring 的「system 摘要」是未实现旧设想（persist 只写 user/assistant），不构成立项依据 | done |
| R1 | 范围 = D1 生成通路（懒生成+summary 档+prompt 资产）/ D2 缓存表+版本归因 / D3 一键回退（默认关 · 逐字节对拍）/ D4 保真度金样（sentinel 正反断言）/ D5 alembic+图谱+文档；非范围 = 轮数策略/compress_window 本体 · SSE · 长期记忆 · 离线预生成 · chat 轨 · 摘要写回 turns 表 · 增量摘要 · LLM-as-judge · Redis 缓存 · UI/端点（占位原文全保留并据实扫扩列） | done |
| R2 | 三组对比各 ≥2：生成时机选 **L1 懒生成+缓存**（弃 L2 离线：为不确定的未来付费 + 短会话账面浪费 + hash 失效预付打水漂；弃 L3 混合：双触发面复杂度收益不成比例）；分档选 **T2 新增 summary 档**（弃 T1 复用 extract 档：background/请求路径延迟预算互相绑架 + usage 归因混账）；缓存选 **C1 独立表**（弃 C2 写回 turns：污染原文 SoT + 摘要的摘要失真复利；弃 C3 进程内：多副本不共享不可审计） | done |
| R3 | failure_paths 11 条，三静默错（摘错造错误前提 / 缓存污染 / 回退开关失效）各有断言+变异检验兜底；key 含内容哈希物理防污染；on 态全失败 → 输出与 off 逐字节一致（回退是形态不是口号）；并发双生成唯一约束先写赢容忍；成本失控/金样覆盖盲区列残余风险 | done |
| R4 | 验收全为可执行断言：off/on-失败双对拍逐字节 · key 铁律 miss 单测 · sentinel 正反金样（空摘要假通过防线）· 锚点断言替代全文快照（prompt-asset 先例）· mock 计数断言零调用 · 热路径零 LLM-as-judge；变异检验三条 | done |
| R5 | SPEC draft-complete 可交人签 HG-SPEC-SIGNOFF；签后 00 出单 task（slug `session-summary-fallback` · 波次裁定五块不拆 · failure_paths 沿用 §5 · HG-GRAPH-MODULES 有义务按实判） | done |
| early_stop | no | — |
| residual_risks | ① 金样 sentinel 断言覆盖不了全部会话形态（真实会话摘要质量靠灰度期人工抽检 + 一键回退兜底 · 不构成立项阻塞）；② 超长会话 chunk 数线性增长的首压成本（每 chunk 一次调用 · 命中后摊销为零 · usage 账可观测；真出现再议离线预热另案 · L1 架构不排斥）；③ 摘要质量依赖 extract 级模型能力，summary 档默认 None（沿用现网默认模型）——灰度期若质量不足经 `OPS_LLM_TIER_SUMMARY_MODEL` 调档，无需改码 | 签收时知悉 |

---

## 8. 下一棒

1. **维护者**：审本 SPEC → 签 `HG-SPEC-SIGNOFF=approved`
2. **00**：起草 `docs/tasks/active/task_session_summary_fallback.md`（范围 §2 D1–D5 · failure_paths 沿用 SPEC §5 · 人工闸表：HG-GRAPH-MODULES 有义务（新表）· 变异检验三条入验收 · alembic 义务：建 ops_session_summaries）
3. **20-task-audit**：书面审 → 维护者签 `HG-AUDIT-R1`
4. **30**：`task/session-summary-fallback` 分支实现（D5 迁移+图谱 → D1 档+prompt 资产+生成服务 → D2 缓存 → D3 开关+对拍 → D4 评测 · compress_window 本体零改动）
5. **40**：验收（含双对拍 + 变异检验三条 + alembic upgrade）→ PR（与 memory-facts-p0/p1 · memory-preference-profile 同模式）

### 下一棒可复制 Prompt（20-spec-audit 预审 / 00 起草 task）

```text
你是 ops-desk-api 仓（/Users/cyning/Desktop/Ops-desk/ops-desk-api）的 <20-spec-audit ｜ 00>。
SPEC：docs/spec/session-summary-fallback/SPEC-session-summary-fallback_v1.md（draft-complete · HG-SPEC-SIGNOFF=approved（00 代录 · 维护者授权））。
<20-spec-audit>：书面审范围/非范围/验收/failure_paths 与 R0–R5 思考轮，结论落盘 docs/harness/reviews/，不代签人闸。
<00>：待维护者签 HG-SPEC-SIGNOFF=approved 后，按 SPEC §8 起草 docs/tasks/active/task_session_summary_fallback.md（D1–D5 · failure_paths 沿用 SPEC §5 · HG-GRAPH-MODULES 有义务（新表 ops_session_summaries）· 变异检验三条入验收 · 铁律：SESSION_SUMMARY_ENABLED 默认关、off/on-失败双对拍逐字节一致）。
```

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-09-22 | 占位稿（范围草案 + 锚点 + 验收方向 + 接续指引） |
| 2026-10-12 | 10-spec 补全：锚点逐个实扫（continuity/history/thread_store/models/model_catalog/retry/circuit/usage/prompts assets/extract 先例）——确认 compress_window 纯函数唯一生产入口在 lg_rag、history.py 无生产调用方、原文面保留现状、llm-layer-hardening 四档路由+重试/熔断/usage 全套可继承、prompt 资产化阶段一落盘形态；范围断言化五块；**懒生成+缓存裁定**（§4 L1/L2/L3 对比：成本按需 vs 为不确定未来付费）；**新增 summary 档裁定**（vs 复用 extract 档：延迟预算隔离 + usage 归因）；**缓存独立表裁定**（vs 写回 turns 表污染原文 SoT）；**回退铁律落地**（SESSION_SUMMARY_ENABLED 默认关 · off/on-失败双对拍逐字节一致 · 回退=关开关零代码零迁移）；保真度金样 sentinel 正反断言（热路径零 LLM-as-judge · preference_redline 先例）；track 裁定 `feature`（新 LLM 调用面+新表+alembic+图谱义务）；failure_paths 11 条；R0–R5 回填；HG-SPEC-SIGNOFF 保持 approved（00 代录 · 维护者授权） 待人签 |
