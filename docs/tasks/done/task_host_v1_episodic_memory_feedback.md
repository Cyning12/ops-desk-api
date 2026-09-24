# Task：Agent Host V1-D · 情景记忆 + 失败模式库（ops_memory_episodes + should_write_episode 独立闸 + [相似经验] 分节召回 + 指纹规则聚类 → 建议人工确认）（host-v1-episodic-memory-feedback）

> **状态**：`done`（2026-09-24 · 五棒全通 · PR [#184](https://github.com/Cyning12/ops-desk-api/pull/184) MERGED（CI 三绿 · 669e76a）· 图谱回写 00 代录 HG-GRAPH-MODULES · CLOSE 归档 done/）  
> **类型**：feature（记忆分层扩展 · **有 alembic 义务**（新表 `ops_memory_episodes` · upgrade/downgrade 可逆 · off 态不读不写 drop 安全 · 承 session_summaries 先例）· **有图谱义务**（memory/db 行 + 人签新行 00 代录位 · 不新增一级模块））  
> **上游 SPEC**：`docs/spec/host-v1-episodic-memory-feedback/SPEC-host-v1-episodic-memory-feedback_v0.md`（**signed** · HG-SPEC-SIGNOFF=approved 2026-09-23 · 00 代录 · Q1 run 级 / Q2 指纹规则聚类 / Q3 三闸预算签收锁死）  
> **前置**：V1-A CLOSE（run 归因载体）· V1-B/C 并行在轨（本波文件面=memory/db/scripts · 与 B（strategy/capability）· C（llm）零交叠）  
> **分支**：`task/host-v1-episodic-memory-feedback`（**禁止 master/main 直改 · 30 由 00 委派子 Agent 执行**）  
> **10 注**：2026-09-23 · 本棒由 00 亲起（无初稿时起草第一步 · 承 harness-00-delegate-only 例外条款）；HG-AUDIT-R1 落稿时待签（10 帽不签）

---

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `host-v1-episodic-memory-feedback` |
| **git_branch** | `task/host-v1-episodic-memory-feedback` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | 零互写断言（双向表计数对拍+import 守护）· 独立闸五判据（拒绝=不落库）· 召回分节断言（[相似经验] 独立块 · 三闸预算截断 · off 零 diff）· 跨租户零召回 · 聚类报告确定性可重放+频次阈值 · 建议未确认零生效（redlines/manifest 零 diff）· revoke_by_run · off 态 drop 安全+迁移可逆 |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `G-L1` 行备注（`memory` 行：情景记忆闸/库分离+召回分节+失败模式聚类 · `db` 行：登记新表 `ops_memory_episodes`；**不新增一级模块**（episode 面归属 memory 既有模块）；HG-GRAPH-MODULES 随 30 交付 00 代录） |
| **graph_delta** | `docs/_tech_graph/l1/01_modules.md`（memory 与 db 两行备注 + 人签新行 · 零新一级模块 · 零新跨模块边——memory→db 既有边复用） |
| **graph_delta_note** | **回炉补闸条款**：若 30 实现形态偏离本预判（新增一级模块 · 新增第二张表/改既有表 · 新增 SSE 事件类型 · 新增 HTTP 路由 · 改 freeze 契约 · 改事实记忆闸/状态机/召回既有语义 · 自动回写 redlines/manifest），不得沿用本裁定——退回 10-spec/10-task 补闸 + `docs/_tech_graph/` 如实登记后续做 |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 契约真值在 SPEC `host-v1-episodic-memory-feedback`；memory README/docstring 同步属范围项非 wiki |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,20,30,40` |
| **invoke_retention_profile** | `default` |
| **experience_capture** | `recommended` |
| **kpi_aggregator** | `CLOSE` |
| **orchestration** | 单 task 直通：10 落稿 → 20-task-audit → HG-AUDIT-R1（00 代录）→ 30（00 委派子 Agent · 实现序：D1 表+migration+models → D2 闸+service → D3 召回注入 → D4 聚类脚本 → D5 建议面 → D6 断言收口）→ 40 → PR+CI 绿+merge → 图谱回写（00 代录）→ CLOSE |
| **freeze_id** | 无（不改 lg-rag-sse-v1 / lg-rag-http-v1 / lc-evidence-http-v1 · SSE 零新事件类型 · 零新路由） |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | approved | 20-R1, 30 | 2026-09-23 · 00 代录（维护者令原话：「签收，并生成对此长程任务的00启动Prompt，新窗口执行，授权00签收所有过程文档，完整落地1.0版本内容」+ 本窗令「继续，完成后自行进行下一波，无特殊情况无需停下等待接收命令」） |
| HG-AUDIT-R1 | **approved** | **30** | 2026-09-23 · **00 代录**（维护者令原话：「签收，并生成对此长程任务的00启动Prompt，新窗口执行，授权00签收所有过程文档，完整落地1.0版本内容」+ 本窗令「授权00可以签收所有过程文档」「继续，完成后自行进行下一波，无特殊情况无需停下等待接收命令」）；依据：20-task-audit R1 **PASS-WITH-NITS** 零阻塞（`docs/harness/reviews/task_host_v1_episodic_memory_feedback_audit_R1_20260923.md` · 三专项全过：白名单一致性/alembic 可执行形态/零互写可证伪）；N1–N3 已微修留痕（修订记录） |
| HG-GRAPH-MODULES | approved | **30** | 2026-09-23 真读 `docs/_tech_graph/l1/01_modules.md`：模块表已建置（签录链完整至 2026-09-23 V1-A 回写行）；`memory`/`db` 行在表；图谱新签义务（两行备注 + 人签新行 00 代录位）**随 30 交付落盘**；不新增一级模块 |
| HG-PILOT-OPSDESK-GLAYER | n/a | 物理分层试点改码 | 本 task 不涉物理分层试点改码 |

---

## 背景与目标

现状（SPEC §1 锁死 · 本帽复核一致）：事实/偏好记忆 stable（gate.py 闸 · service.py 状态机 · continuity.py 分节注入默认关）；情景记忆与失败模式库缺失；铁律=与事实记忆闸/库物理分离零互写（U4）。

一句话目标（SPEC 锁死）：`ops_memory_episodes` 新表 + `should_write_episode` 独立闸（零互写）+ 规划期相似成功经验召回 `[相似经验]` 分节（默认关）+ 离线指纹规则聚类 → redlines/manifest 建议（人工确认才生效）。

设计纪律（30 不得违反 · 承 SPEC §1 签收锁死）：

1. **闸/库物理分离（U4）**：不同表/不同闸函数/不同召回路径；零互写断言化（双向表计数对拍 + import 守护）。
2. **默认关双开关**：`MEMORY_EPISODES_WRITE_ENABLED=false`（写入）· `MEMORY_EPISODES_ENABLED=false`（召回）· 非法值回退 false；off 态不读不写 · drop 表读写路径不炸。
3. **审计记动作不记内容**：写/召回/聚类记动作与计数 · plan 摘要/工具序列是结构元数据（截断）· 不记 query 原文。
4. **人工确认闸**：聚类只产建议（报告字段）· 零代码路径自动改 redlines/manifest。
5. **租户隔离**：tenant 谓词承阶段 T（ContextVar · 模型产出不参与身份构造）· 跨租户零召回。
6. **零 freeze 动**：不改 freeze 契约 · SSE 零新事件 · 零新路由；迁移可逆。

---

## 现状锚点（只读 · 30 必读 · 10 已扫）

| 主题 | 路径 · 锚点 | 现状 |
|------|-------------|------|
| 事实记忆闸（**分立对象 · 禁复用**） | `app/ops/memory/gate.py:115-147` | should_write 纯函数（任一不过即拒 · 拒绝=不落库）；episode 闸物理不同文件不同函数 |
| 状态机/revoke 先例 | `app/ops/memory/service.py` | write_fact/revoke_by_source · 逻辑失效不物理删 · 审计 logger 记动作不记内容 |
| 注入分节先例（**D3 落点**） | `app/ops/lg_rag/continuity.py:115-117/:128-136/:212/:236/:369` | `[已知事实]`/`[用户偏好]` 单块双节 · MEMORY_FACTS_ENABLED 默认 false 非法回退 · 召回失败降级不注入 · span 计数 |
| 预算三闸先例 | `app/ops/lg_rag/multi/step_contract.py:23-30` | MAX_FIELDS=16 · MAX_VALUE_CHARS=200 · MAX_CONTEXT_BLOCK_CHARS=800（单值截断挡不住累加 · 整块闸） |
| 模型/迁移面（**D1 落点**） | `app/db/models.py`（OpsMemoryFact）· `alembic/versions/` | 最新 head 20260922_session_summaries；off 态 drop 安全先例（session_summaries） |
| run 归因/聚类输入 | `ops_lg_rag_run_events`（落盘+replay）· V1-A subject_binding（tenant+user+run_id+subtask_id） | episode 归因与离线聚类输入齐备 |
| 报告字段族先例 | `reports/memory_embedding_backfill/` | backfill 报告 yaml 先例（status/counts/记录面） |
| 命名冲突扫 | grep `should_write_episode\|ops_memory_episodes\|MEMORY_EPISODES\|episode_gate\|episode_service\|revoke_by_run\|context_fingerprint\|相似经验` 于 app/tests | **零命中**（2026-09-23 本帽真跑） |
| 测试基线 | `.venv/bin/python -m pytest tests --collect-only -q` | **1420 collected**（2026-09-23 本帽真跑） |
| alembic 义务 | **有** | 新表 `ops_memory_episodes`（upgrade/downgrade 可逆 · off 态不读不写 drop 安全 · 断言化） |

---

## 钉死契约（自 SPEC §2/§4/§5 锁死；30 不得静默改义）

| 项 | 钉死 |
|----|------|
| **表（D1 · Q1 run 级）** | `ops_memory_episodes`：id uuid PK · tenant_id · run_id（索引）· task_domain · context_fingerprint（索引 · 确定性哈希：domain+意图特征+工具序列骨架）· plan_summary（≤200 截断）· tool_sequence jsonb（≤16）· outcome（success\|failure\|partial）· failure_class（词表 nullable · failure 必填）· status（active\|revoked 默认 active）· created_at；索引 (tenant_id,outcome,status)/(context_fingerprint)/(run_id) |
| **独立闸（D2）** | `app/ops/memory/episode_gate.py`：`should_write_episode(candidate) -> Decision` 纯函数五判据（归因齐全/outcome 合法/序列≤16/摘要截断/failure 必 class 且**词表合法**——六值 capability_blocked\|so_failure\|budget_exhausted\|upstream_error\|contract_violation\|other · 非法值同拒 · R1 审查 N3 对齐 SPEC「必填合法」）· 拒绝=不落库 |
| **service（D2）** | `app/ops/memory/episode_service.py`：write_episode（过闸才落）· revoke_by_run（逻辑 revoke · 审计记动作）· **零 import 事实记忆写面** |
| **召回（D3 · Q3 三闸）** | 同 tenant+success+active+fingerprint 匹配 top-N；`MEMORY_EPISODES_MAX_ITEMS` 默认 3 · 单条 ≤200 · 整块 ≤800（尾部截断）；独立分节 `[相似经验]`；`MEMORY_EPISODES_ENABLED=false` 默认关（非法回退 false）；召回失败降级不注入；span `memory_episodes_injected=N` |
| **聚类（D4 · Q2 指纹规则）** | 离线脚本 `scripts/episode_pattern_mine.py`：failure/partial 按 failure_class×fingerprint 分组计数 · 阈值 `EPISODE_PATTERN_MIN_COUNT` 默认 3 · 报告 `reports/episode_patterns/<date>.yaml`（pattern_id/failure_class/fingerprint/count/sample_run_ids≤5/first_seen/last_seen/suggested_rule）· 确定性可重放 |
| **建议（D5）** | 建议只在报告 `suggested_rule` 字段 · **零代码路径自动改 redlines/manifest**（git 守护断言零 diff） |
| **开关（纪律 2）** | `MEMORY_EPISODES_WRITE_ENABLED`/`MEMORY_EPISODES_ENABLED` 双 false 默认 · off 态不读不写 · 表不存在时读写不炸（try/降级 · 承 session_summaries off 态先例） |
| **图谱** | memory/db 行备注 + HG-GRAPH-MODULES 人签新行（**00 代录位**）；`./scripts/graph-compile.sh` 绿；零新一级模块 |

---

## 范围（单 task 直通 · SPEC §2 D1–D6）

- [x] **D1 · 表+迁移+模型（必做 · 本波唯一 alembic）**：`ops_memory_episodes` migration（upgrade/downgrade 可逆）+ models.py 增 OpsMemoryEpisode + off 态 drop 安全
- [x] **D2 · 独立闸+service（必做 · U4 核心）**：episode_gate.py + episode_service.py（零互写 · import 守护）
- [x] **D3 · 召回注入（必做 · 默认关）**：continuity.py 装配面 `[相似经验]` 独立分节 + 三闸预算 + 双开关
- [x] **D4 · 聚类脚本（必做 · 离线）**：scripts/episode_pattern_mine.py + 报告字段族 + 频次阈值
- [x] **D5 · 建议面（必做 · 人工确认闸）**：suggested_rule 报告字段 · 零自动回写守护
- [x] **D6 · 测试与图谱（必做 · 否决面）**：SPEC §2 D6 九组断言全落 + memory/db 行备注 + HG-GRAPH-MODULES 人签新行（00 代录）+ graph-compile 绿

**竖切结论**：D1→D2→D3→D4→D5→D6 同 task 一次提交；episode 不配独立闸 = U4 铁律落空；召回不配分节/预算 = 注入面污染风险；聚类不配人工确认闸 = 全自动回写破口。耦合面可控（一表一迁移 + 两个新文件 + 装配面分节 + 一脚本 + 测试/图谱）。

### 非范围

承 SPEC §3（锁死 · 越任一条即回炉）：D3 跨进程同步 · 自动规则回写 · 实时聚类 · 用户可见记忆管理面/对外端点 · subtask 级 episode · embedding 聚类 · 改事实记忆既有语义（零互写含零改）· 改 freeze/新 SSE 事件/新路由。

---

## failure_paths

| 触发条件 | 系统行为 | 可重试 | 用户可见 |
|----------|----------|--------|----------|
| `HG-AUDIT-R1` 未签即 30 | **拒开工** | 是 | 是 |
| B1 旧测影响面未逐条处置即 30 交付 | **拒收**（闸前置） | 是 | 是 |
| 验收缺零互写/闸判据/分节/跨租户/聚类/建议零生效/revoke/drop 安全/迁移可逆/变异检验任一 | **拒收**（防空真规则） | 是 | 是 |
| **episode 污染放大**（SPEC FP-1 · 错误经验被召回） | 只召回 success + revoke_by_run 纠错 + 召回失败降级不注入三层防线 | 是（revoke） | 否 |
| **聚类噪声**（SPEC FP-2 · 低频偶发被当模式） | 频次阈值默认 ≥3 + 人工确认闸（建议不自动生效）双保险 | 是 | 否 |
| **隐私/租户隔离**（SPEC FP-3） | tenant 谓词承阶段 T · 跨租户零召回断言 · 模型产出不参与身份 | — | 否 |
| **新表 alembic**（SPEC FP-4） | 迁移可逆 · off 态不读不写 · 表不存在读写不炸（断言化） | 是 | 否 |
| **指纹碰撞**（SPEC FP-5 · 不同任务同指纹互染） | 指纹三元（domain+意图特征+工具序列骨架）· 只召回 success+条数上限 · 方向=宁可不召回 | — | 否 |
| **热路径写入放大**（SPEC FP-6） | 写开关默认关 · run 终态异步面触发（承 memory extract 热路径零抽取先例 · 不挡主答） | 是 | 否 |
| **双写漂移**（SPEC FP-7 · 同一经验两表各一份） | 零互写断言 + 来源分立（episode 只从 run 终态结构化产物 · 不经 LLM 抽取） | — | 否 |

---

## 验收标准

- [x] 人工闸：HG-AUDIT-R1 approved 后方可勾选下列码项（图谱新签义务随 30 交付落盘 00 代录；**30 偏离预判 → 回炉补闸条款生效**）

### D1 · 表+迁移（映射 SPEC §6-8 · R1 审查 N1 修正）

- [x] migration upgrade 建表（列/索引齐全断言）· downgrade 可逆断言；off 态（表不存在）读写路径不炸断言

### D2 · 独立闸+service（映射 SPEC §6-1/2/7）

- [x] 零互写断言：write_episode 后 ops_memory_facts 计数零变化 · write_fact 后 episodes 计数零变化；episode_gate/episode_service 不 import 事实记忆写面（import 守护）
- [x] 闸五判据逐条（缺归因/非法 outcome/超长序列/超长摘要/failure 缺 class **或 class 词表非法** 全拒不落库 · R1 审查 N3 对齐 SPEC「必填合法」）
- [x] revoke_by_run：召回零命中 · 表内仍可查 · 审计日志记动作（caplog）

### D3 · 召回注入（映射 SPEC §6-3/4）

- [x] `[相似经验]` 独立分节断言（与 [已知事实]/[用户偏好] 物理分节）；off 零 diff
- [x] 三闸预算断言：条数默认 3 · 单条 ≤200 · 整块 ≤800 尾部截断
- [x] 跨租户零召回断言；召回失败降级不注入断言

### D4 · 聚类（映射 SPEC §6-5）

- [x] 报告产出字段族齐全（pattern_id/failure_class/fingerprint/count/sample_run_ids≤5/first_seen/last_seen/suggested_rule）
- [x] 频次阈值断言（<3 不成模式）；确定性可重放断言（同输入同报告）

### D5 · 建议面（映射 SPEC §6-6）

- [x] 聚类跑完后 redlines yaml 与 manifest 文件零 diff（git 守护断言 · 建议未确认零生效）

### D6 · 图谱 / 工程（映射 SPEC §6-9/10/11）

- [x] memory/db 行备注 + HG-GRAPH-MODULES 人签新行（00 代录）；`./scripts/graph-compile.sh` 绿；迁移 head 入 db 行登记
- [x] 全量 `pytest tests` 绿（基线 **1420 collected** · 无既有用例删除 · 新增数如实入 40）；`ruff check app tests` 净增 0
- [x] 生产路径 diff 白名单：`git diff master -- app/` 只含 memory/episode_gate.py 新增 + memory/episode_service.py 新增 + lg_rag/continuity.py（分节接线）+ db/models.py（OpsMemoryEpisode）+ alembic/versions/ 新迁移 + scripts/episode_pattern_mine.py + 测试/图谱/文档
- 注记（承 SPEC §6-11 · 不计验收计数 · R1 审查 N2）：PR+CI 绿+merge 由 orchestration 流程承载（承「PR 过 CI 自动 merge」先例 · V1-B R2 注记同款）

### 变异检验（不验收空真规则）

- [x] ① **互写可检**：临时让 episode_service 写一行 ops_memory_facts → 零互写断言必挂；恢复后全绿
- [x] ② **闸可检**：临时闸恒放行 → 「拒绝=不落库」断言必挂；恢复后全绿
- [x] ③ **分节可检**：临时把经验注入并入事实块（摘 `[相似经验]` 头）→ 分节断言必挂；恢复后全绿

### 旧测影响面清单（B1 · 2026-09-23 10-task 实扫落盘）

> 扫描口径（真跑）：`ls tests/ | grep -iE 'memory|episode|run_event|continuity|inject|gate'`（命中 13 文件归并 6 组）· 命名冲突扫零命中 · 基线 1420 collected

| # | 锚点 | 本波影响 | 处置 |
|---|------|----------|------|
| 1 | `tests/test_memory_gate.py`（15）· `test_memory_service_db.py`（13）· `test_memory_vector_p1.py`（9）· `test_memory_extract_p1.py`（14）· `test_memory_time_decay_tz.py`（6）· `test_memory_golden_eval.py` | 事实记忆全面守护；episode 物理分离零改动 → 全绿 | 回归（零改动） |
| 2 | `tests/test_memory_injection.py`（23 · off 对拍先例）· `test_lg_rag_session_continuity.py` · `test_session_continuity.py` | 装配注入守护；[相似经验] 默认关零 diff → 全绿 | 回归（零改动） |
| 3 | `tests/test_memory_embedding_backfill.py`（15） | 报告字段族先例守护；聚类报告对齐其先例不改既有 | 回归（零改动） |
| 4 | `tests/test_admin_memory_purge.py` · `test_memory_purge_db.py` | purge 面守护；episode 表不入 purge 面（本波非范围 · admin purge 仅 ops_memory_facts）→ 零改动 | 回归（零改动） |
| 5 | `tests/test_capability_gateway.py` | 闸链守护；本波不触 capability → 零改动 | 回归（零改动） |
| 6 | 新增义务：`tests/test_memory_episode_gate.py`（闸判据/零互写/import 守护/变异检验②）+ `tests/test_memory_episode_recall.py`（分节/预算/跨租户/降级/revoke/drop 安全/变异检验①③）+ `tests/test_episode_pattern_mine.py`（报告/阈值/可重放/建议零生效） | — | 新增（用例数如实入 40 记录） |
| 7 | alembic 链 | 本波**有迁移义务**（新表 · 可逆 · off 态安全 · head 接 20260922_session_summaries 后） | 新增迁移（upgrade/downgrade 断言入 D1） |

---

## 依赖

| 依赖 | 说明 |
|------|------|
| SPEC | `docs/spec/host-v1-episodic-memory-feedback/SPEC-host-v1-episodic-memory-feedback_v0.md`（signed · Q1/Q2/Q3 裁定锁死） |
| 规划/种子 | `docs/spec/agent-infra/07_host_v1_landing_plan_v0.md` · `08_host_v1_wave_spec_outlines_v0.md` §4（双 signed） |
| 事实记忆面 | `docs/spec/memory-facts-p0/SPEC-memory-facts-p0_v1.md`（signed）· `docs/tasks/done/task_memory_preference_profile.md`（分节先例）· `docs/tasks/done/task_session_summary_fallback.md`（off 态 drop 安全先例） |
| 前波 | `docs/tasks/done/task_host_v1_delegation_token.md`（V1-A · run 归因） |
| 编码规范 | `docs/standards/CODING_BACKEND_L2_v1_zh.md` |
| 图谱 | `docs/_tech_graph/l1/01_modules.md`（2026-09-23 真读核验 · memory/db 行 · 签录链至 V1-A 回写行） |
| 改造对象 | `app/ops/memory/episode_gate.py`（新增）· `app/ops/memory/episode_service.py`（新增）· `app/ops/lg_rag/continuity.py`（:212/:236 分节接线）· `app/db/models.py`（OpsMemoryEpisode）· `alembic/versions/`（新迁移）· `scripts/episode_pattern_mine.py`（新增） |
| 先例 · 闸/状态机 | `app/ops/memory/gate.py:115-147` · `app/ops/memory/service.py`（write/revoke/审计） |
| 先例 · 分节注入 | `app/ops/lg_rag/continuity.py:115-117/:128-136/:212/:236/:369` |
| 先例 · 预算三闸 | `app/ops/lg_rag/multi/step_contract.py:23-30` |
| 先例 · 报告字段族 | `reports/memory_embedding_backfill/` |
| 测试锚点 | B1 清单 6 组 |
| 格式基准 | `docs/tasks/done/task_host_v1_delegation_token.md`（V1-A · 五棒全通 · 格式对齐此） |

---

## 给执行帽的必读列表

1. `AGENTS.md`（新会话启动纪律 · 分支纪律 · GATE_VERIFY）
2. 本 task（钉死契约 · 闸 · 非范围 · B1）
3. SPEC `docs/spec/host-v1-episodic-memory-feedback/SPEC-host-v1-episodic-memory-feedback_v0.md`（§2 D1–D6 / §3 非范围 / §4 Q1–Q3 / §5 FP-1~FP-7 / §6 验收）
4. `docs/standards/CODING_BACKEND_L2_v1_zh.md`
5. 代码：`app/ops/memory/gate.py`（:115-147）· `app/ops/memory/service.py`（write/revoke）· `app/ops/lg_rag/continuity.py`（:115-117/:128-136/:212/:236/:369）· `app/ops/lg_rag/multi/step_contract.py`（:23-30）· `app/db/models.py`（OpsMemoryFact 面）
6. 先例：`tests/test_memory_gate.py`（闸断言范式）· `tests/test_memory_injection.py`（off 对拍/分节范式）· `tests/test_memory_service_db.py`（DB 断言范式）
7. `docs/harness/prompts/FRAGMENT_30_gate_verify_v1_zh.md`

---

## 思考轮控制

| 轮 | 结论 | early_stop | reason（early_stop） | residual_risks |
|----|------|------------|----------------------|----------------|
| R0 | SPEC signed（HG-SPEC-SIGNOFF=approved 2026-09-23 00 代录）；范围 D1–D6 承 SPEC §2 不重开；本帽实扫复核：闸 :115-147 · 注入 :115-117/:236 · 三闸 :23-30 · 迁移 head 20260922 · 命名零冲突 · 基线 1420 | no | — | 无 |
| R1 | 开工闸：HG-TASK-DRAFT approved（00 代录 · 双令留痕）· HG-AUDIT-R1 **pending**（blocks 30 → **30 拒开工**）· HG-GRAPH-MODULES=approved（真读核验 · memory/db 行在表 · 图谱新签义务随 30 落盘） | no | — | 无 |
| R2 | 竖切：D1→D2→D3→D4→D5→D6 同 task 一次提交；方案对比继承 SPEC §4 三组裁定（Q1 run 级弃 subtask · Q2 指纹规则弃 embedding · Q3 三闸弃动态百分比），不重演 | no | — | 无 |
| R3 | failure_paths **10 条** = SPEC FP-1~FP-7 翻四列 + 过程三；最锋利边界=污染放大三层防线（只召回 success+revoke+降级不注入）与双写漂移（零互写+来源分立） | no | — | ① 指纹碰撞只能「宁可不召回」（方向正确性已锁）② 聚类建议质量依赖离线报告人工复盘 |
| R4 | 验收 **14 条**全否定性断言化逐块映射 SPEC §6（人工闸 1 / D1×1 / D2×3 / D3×3 / D4×2 / D5×1 / D6×3 = 14 · 变异检验×3 不计入）；B1 实扫 6+1 组三态齐全（回归×5 · 新增×1 · 迁移新增×1） | no | — | 无 |
| R5 | 可交 20-task-audit；与 SPEC 实质差异为零（锚点/B1/基线数/闸行留痕过程化落地）；HG-AUDIT-R1 落稿时待签 | no | — | 见 R3 |

**actual_last_round**：R5 · **early_stop**：no · **residual_risks**：见 R3/R5

### R0 · 问题框定

SPEC 已签收（Q1 run 级 + Q2 指纹规则 + Q3 三闸预算锁死），本 task 只做可执行化拆解：经验≠事实（U4 闸/库物理分离为第一性）；本波是五波中**唯一有 alembic 义务**的波（新表 · off 态 drop 安全承 session_summaries）。当前分支 master——**30 必须切 `task/host-v1-episodic-memory-feedback`**。

### R1 · 开工闸

HG-TASK-DRAFT approved（00 代录 · 双令原话留痕）；HG-AUDIT-R1 **pending**（30 拒开工）；HG-GRAPH-MODULES **真读** `01_modules.md` 核验：模块表已建置 · 签录链完整至 V1-A 回写行 · memory/db 行在表 · 图谱义务=两行备注+人签新行随 30 落盘。

### R2 · 竖切

D1–D6 是不可拆语义单元：episode 不配独立闸 = U4 落空；召回不配分节/预算 = 注入污染；聚类不配人工确认闸 = 全自动回写破口。实现序：D1 表+迁移（底座）→ D2 闸+service（U4 核心）→ D3 召回分节 → D4 聚类脚本 → D5 建议面 → D6 断言收口。

### R3 · 失败语义

SPEC §5 七条全收翻四列加过程三共十条。污染放大三层防线（成败标签只召回 success + revoke_by_run 纠错 + 召回失败降级不注入）；双写漂移由零互写断言+来源分立（episode 不经 LLM 抽取）结构性消除；指纹碰撞方向锁定「宁可不召回」。

### R4 · 可测性

验收 14 条全部可执行：零互写是双向表计数对拍+import 守护（变异检验①直接注入互写→必挂）· 闸五判据逐条（拒绝=不落库非存了不召回）· 分节物理隔离断言 · 聚类确定性可重放（同输入同报告）· off 零 diff 由 1420 基线零改动证明。变异检验三条（互写/闸/分节各配「破坏→必挂→恢复」）。

### R5 · 交付判定

可交 20-task-audit：与 SPEC 实质差异为零；HG-AUDIT-R1 落稿时待签；残余风险两条承 R3 如实携带。

### 自检结论

本稿：范围/非范围/验收/failure_paths 逐块映射 SPEC（§2→D1–D6 · §3→非范围 · §5→failure_paths+过程三 · §6→验收 14 条）；钉死契约自 SPEC §2/§4/§5 锁死；B1 实扫 6+1 组三态齐全；闸表四行诚实；思考轮 R0–R5 回填齐全无跳轮。

---

---

### KPI（kpi_aggregator=CLOSE · 2026-09-24 00 核验）

Task_KPI%: 100 · D1 范围钉死（D1–D6 全交付 · SPEC §2 映射）· D2 闸齐（HG-SPEC-SIGNOFF/HG-TASK-DRAFT/HG-AUDIT-R1/HG-GRAPH-MODULES 全 00 代录 approved）· D3 过程档齐（invoke 10/20/30/30-resume/40 + R1 审查文 PASS-WITH-NITS）· D4 图谱回写随 #184 入 master（不新增一级模块）· D5 关账补登（归档 done/ · Hub 行）

| 指标 | 值 |
|---|---|
| 新增测试 | +84 用例（1503→1587 collected · 零既有删除） |
| 全量测试 | 1574 passed / 0 failed / 1 skipped / 12 errors（12 ERROR 实证为基线环境性 · master+同 .env 同挂 · `ops_sessions.tenant_id`）；CI pytest **pass** |
| lint | ruff 净增 0（57=57）；graph-compile 绿 |
| 变异检验 | 3/3「破坏→必挂→恢复绿」（互写/闸恒放行/分节摘头 · fec4f63） |
| 图谱 | graph-compile 绿 · 不新增一级模块 · HG-GRAPH-MODULES 00 代录 |
| 交付 | PR #184 MERGED（CI 三绿 · 669e76a）· 40 invoke 经 #185 入 master |


## 修订记录

| 日期 | 摘要 |
|------|------|
| 2026-09-23 | 10-task 落稿（SPEC signed 后 · 00 亲起）：锚点逐个复核（gate :115-147 · continuity :115-117/:236 · step_contract :23-30 · 迁移 head 20260922_session_summaries）· 命名冲突扫零命中 · pytest 基线 1420 真跑 · B1 6+1 组落盘 · HG-TASK-DRAFT 00 代录 approved（双令留痕）· HG-AUDIT-R1 pending 待 20-task-audit |
| 2026-09-23 | 20-task-audit R1 **PASS-WITH-NITS**（零阻塞 · 审查文 `docs/harness/reviews/task_host_v1_episodic_memory_feedback_audit_R1_20260923.md`）；N1 D1 映射标注 §6-8/9→§6-8 · N2 SPEC §6-11 映射注记（承 V1-B R2 先例）· N3 闸判据⑤对齐「必填合法」（非法 failure_class 同拒断言）；**00 代录 HG-AUDIT-R1=approved**（维护者令原话+本窗双令留痕）· 30 可委派开工（分支 `task/host-v1-episodic-memory-feedback` · worktree 隔离承 B/C 先例） |
| 2026-09-24 | **00 CLOSE**：PR [#184](https://github.com/Cyning12/ops-desk-api/pull/184) MERGED（CI 三绿 · 669e76a）；图谱人签 00 代录；过程档（SPEC/审查/invokes 10–40）补登；归档 done/ · Hub 补登；**V1-D CLOSE → V1-E 可启** |
