---
title: task · P4-T4 · RAG 域配置面（fail-closed 域隔离 · collection 按域三级回退 + glossary 按域文件回退 + rag 子任务域闸）
---

# task · P4-T4 · RAG 域配置面（fail-closed 域隔离 · collection 按域三级回退 + glossary 按域文件回退 + rag 子任务域闸）

> **状态**：`active`（2026-11-18 落卡 · 30 待开工）
> **来源**：domain-pack-v1 设计 18 文 §2.3 RAG 域化 + §10 P4-T4 任务行 + §13 失败路径 + 19 契约 §4（钉死口径真源 · commit e453a36）· 授权 issue Cyning12/ops-desk-workspace#23（m03064/m03796 夜间授权 · 委派书 p4-t4-rag-domain-config）

## Harness 元信息

| 键 | 值 |
|----|----|
| **task_slug** | p4-t4-rag-domain-config |
| base | 370a137a |
| 关联 issue | issue Cyning12/ops-desk-workspace#23（授权真源）· 18 设计文 §2.3/§10 P4-T4 行/§13 + 19 契约 §4（需求与口径真源） |
| 关联 PR | feat 本 PR · close chore PR（收口登记） |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 本仓未启用 WikiTrack；本波为 rag 域配置面 G-L1 面 + 图谱登记 |
| graph_change_layer | G-L1（01_modules.md rag/lg_rag 行 p4-t4 备注 + HG-GRAPH-MODULES 签收行） |
| review_hat | 20（R1 审查文落盘 · GO） |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | approved | 30 | approved 2026-11-18 · 授权 issue Cyning12/ops-desk-workspace#23 m03064/m03796（夜间授权）+ 委派书 p4-t4-rag-domain-config 为唯一范围真源 |
| HG-AUDIT-R1 | approved | 30 | approved 2026-11-18 · 同上授权 + R1 审查文 docs/harness/reviews/task_p4_t4_rag_domain_config_audit_R1_20261118.md（GO） |
| HG-GRAPH-MODULES | approved | 30 | approved 2026-11-18 · 同上授权（rag/lg_rag 行 p4-t4 备注属图谱登记义务 · 随 30 交付回填） |

## 背景

domain-pack-v1 的 RAG 面现状是 ops 单域写死：`qdrant_collection()`（app/ops/rag/backend.py:39-40）只读 `QDRANT_COLLECTION` 全局值缺省 `ops_knowledge`；`glossary.py:18` 单路径 `glossary.yaml` 模块级单缓存。oa 等后继域部署同一代码时，若未配置本域 collection，检索会**静默落回 ops_knowledge**——跨域向量泄漏（18 文 LB3 · R-P4-7 钉为红线）。19 契约 §4（commit e453a36 钉死）定稿口径：§4.1 collection 按域 env 三级回退矩阵（ops 含缺省域：`QDRANT_COLLECTION_OPS` → `QDRANT_COLLECTION` → `ops_knowledge` 零 diff；domain≠ops：`QDRANT_COLLECTION_<DOMAIN_UPPER>` 单级，缺省 ⇒ fail-closed 禁用，rag 子任务报「本域未配置检索」**不回落** ops_knowledge）；§4.2 glossary 按域文件回退（`glossary.<domain>.yaml` 存在则读否则 `glossary.yaml` · 按域缓存 · 本波不交付 oa glossary=刻意不交付死配置）；§4.3 ingest/source_type 词表（issue|pr|doc）不泛化（钉死文档）。域解析复用 P4-T2 已合 `app/ops/prompts/domain_context.py` 的 `current_domain()`（勿自建第二真源）。本波依赖 P4-T2（已 merge 370a137a）。

## 范围

1. **collection 域化**（19 §4.1）：`app/ops/rag/backend.py`——`qdrant_collection(domain: str | None = None) -> str | None`：domain=None 解析当前部署域；ops（含缺省域）三级回退 `QDRANT_COLLECTION_OPS` → `QDRANT_COLLECTION` → `ops_knowledge`（QDRANT_COLLECTION_OPS 未设时与 base 逐值一致 · 零 diff）；domain≠ops 单级 `QDRANT_COLLECTION_<DOMAIN_UPPER>`，缺省/空白 ⇒ `None`（本地 RAG 显式禁用）。域解析走 `_current_domain()`：**importlib 运行期解析** `app.ops.prompts.domain_context.current_domain`（守 rag-outbound 静态边界 · 承 lg_rag/continuity.py→session.summary 先例 · 图谱备注级登记 · .importlinter 零改动）；解析异常回落 `ops` + logger.exception（零 diff 面 · 登记）。
2. **glossary 按域回退**（19 §4.2）：`app/ops/rag/glossary.py`——`_glossary_path(domain)`：`glossary.<domain>.yaml` 存在则域件否则回退 `glossary.yaml`（回退判定=文件存在 · 承 T2 目录回退同口径 · 坏 yaml 显式炸不静默）；缓存改按域 `_TABLES: dict[str, dict]`；`expand_query_for_fts(query, domain=None)` 增 domain 形参（None → `backend._current_domain()` 同包复用）；ops 域无 `glossary.ops.yaml` 天然回退默认件（零 diff 双保险 · 承 19 §3.4 同手法）。
3. **rag 子任务域闸**（fail-closed 主防线）：`app/ops/lg_rag/multi/nodes.py` `rag_subtask_node`（:1921-1998）——`emit_subtask_running` 之后、`set_chain_step_hook` 之前插闸：`current_domain()`（静态 import · lg_rag→prompts 同族允许）+ `qdrant_collection(domain)`（**importlib 运行期解析** app.ops.rag.backend · 守 lg-rag-outbound 静态边界 · 同上先例）；None ⇒ `result["output"]="本域未配置检索"` + logger.warning（点名缺失 env 键）直接 `_finish_worker`，**不触** `astream_router_agent`（后端调用零发生）。ops 域闸恒放行（既有行为零 diff）。
4. **影子写写面 fail-closed**：`app/ops/rag/shadow_write.py` `_shadow_upsert_safe`/`_shadow_delete_safe`——collection None ⇒ skip + logger.warning（不进 DLQ 噪声 · 不跨域写；ops 域零 diff）。
5. **ingest/source_type 不泛化**（19 §4.3 钉死 · 文档级）：ingest.py:43/58-89 词表 `issue|pr|doc` 不动一行；本任务档与图谱备注钉死口径。
6. **测试**（新增 `tests/test_rag_domain_config.py`）：回退矩阵全格（ops 三级 × env 有/无/空白 · 非 ops 有/无/空白 · domain=None 经 contextvar 注入与 OPS_DOMAIN env 两通路）；ops 零 diff 对拍（QDRANT_COLLECTION_OPS 未设时与 base 行为逐值等）；域闸（domain=oa 无 env ⇒ output=「本域未配置检索」且 patch astream_router_agent 断言**零调用** · ops 域放行 mock 正常产出）；glossary 回退（oa 无件=与 ops 同表逐字节等 · monkeypatch 域件路径读域件 · 按域缓存隔离）；shadow skip（None ⇒ 零 DLQ 零异常 + warning）。真 PG 绿（postgresql+asyncpg://ops:ops_password@localhost:5432/opsdesk_test · 五键 blank 前缀）· 目标回归（test_rag_qdrant_backend / test_rag_fts_config / test_lg_rag_multi / test_supervisor_parallel_join）零红 · 全量 pytest 绿（环境性红与 base 370a137a 同路径基线逐签对照 · CI 终裁）· `ruff check app tests` 绿。
7. **图谱**：`docs/_tech_graph/l1/01_modules.md` rag 行（:31）+ lg_rag 行（:35）各补 p4-t4 备注 + HG-GRAPH-MODULES 签收行（承 :48 先例）。
8. **落盘**：registry entry（status=active → close 波 closed 钉 wave_tip）· invokes by-task/p4-t4-rag-domain-config/{10,30,40,50} · R1 审查文 · task 档 active→done。

## 非范围

- 不动 ingest 管线（ingest.py · embedder · chunker · 影子写点火面除第 4 条 None-skip 外零改）；source_type 词表 `issue|pr|doc` 不泛化（19 §4.3 钉死）。
- 不动 prompt loader/templates/domain_context.py（P4-T2 已合 · 本波仅消费 `current_domain()` 不自建第二真源）。
- 不做 oa 语料/oa glossary 文件/oa 模板资产（P4-T5）；不交付 `glossary.oa.yaml`（刻意不交付死配置 · 机制面回退天然成立）。
- 不碰 `.importlinter`（importlib 运行期解析守静态边界 · 零新静态边 · 承 continuity.py 先例）；不碰 alembic/ · scripts/；零新依赖。
- 不给 lc_evidence_chain HTTP 旁路/retrieve.py 内部链加域闸（契约 fail-closed 面=rag 子任务闸；qdrant_retriever.py:38 构造得 None 时维持现有异常→fallback 行为 · 限制登记）。
- 不新增矩阵外 env 键（仅 `QDRANT_COLLECTION_OPS` 与 `QDRANT_COLLECTION_<DOMAIN_UPPER>` 族为契约内新键）。

## 失败路径

- 跨域向量泄漏（LB3/R-P4-7 主防线）：非 ops 域缺 `QDRANT_COLLECTION_<DOMAIN>` ⇒ `qdrant_collection` 返回 None（不回落全局/ops）· rag 子任务闸报「本域未配置检索」· 后端调用零发生（patch 断言守）· 影子写 skip 不跨域写。
- importlib 运行期解析失败（domain_context 缺失等进程级破碎）→ `_current_domain()` 回落 `ops` + logger.exception——ops 部署零 diff 面优先（防误伤现网）；「解析失败时非 ops 部署读 ops」风险由「domain_context 为仓内 stdlib-only 模块 · 解析失败=进程级故障」前提承接（登记）。
- env 空白串：`(os.getenv(k) or "").strip()` 空视同未配置（ops 链落 ops_knowledge · 非 ops 域落 None）——与 base `.strip() or "ops_knowledge"` 语义逐值一致。
- glossary 按域缓存串扰：缓存键=domain（`_TABLES` dict）· 测试间 `_TABLES.clear()` 隔离；回退判定=文件存在（坏 yaml safe_load 异常上抛显式炸 · 不静默回退掩盖资产错误 · 承 T2 坏件口径）。
- 静态边界破坏：rag→prompts / lg_rag→rag.backend 禁静态 import（rag-outbound / lg-rag-outbound 均 forbidden）——一律 importlib 运行期解析 + 图谱备注级登记；import-linter CI 闸机判守（12 contracts kept 0 broken）。
- ops 面行为漂移：ops 链三态对拍（无 env / 仅 QDRANT_COLLECTION / QDRANT_COLLECTION_OPS 优先）+ glossary ops 展开与默认件逐字节等 + 目标回归零红。
- 并行 agent 撞 registry.yaml / 01_modules.md 同区冲突（T6 波在飞）→ rebase origin/master 保留双方 entry 手动解，冲突块如实登记。
- 仓根 .env 渗入收集期致全量 pytest 环境性红 → 与 base 370a137a 同路径基线逐签对照登记，CI 终裁；脏树期 wave_gate_registry 红为结构性常态（委派书钉明）。

## 验收标准

- [ ] collection 矩阵全格：ops 三级（QDRANT_COLLECTION_OPS > QDRANT_COLLECTION > ops_knowledge）· 非 ops 单级（QDRANT_COLLECTION_<DOMAIN> 否则 None）· 空白串视同未配置（tests/test_rag_domain_config.py 参数化全格绿）
- [ ] domain=None 解析当前部署域：contextvar 注入 `set_current_domain("oa")` 与 OPS_DOMAIN env 两通路断言绿（importlib 运行期解析 current_domain · 单一真源）
- [ ] ops 零 diff 对拍：QDRANT_COLLECTION_OPS 未设时全矩阵取值与 base `qdrant_collection()` 逐值一致（含空白串边角 · 断言绿）
- [ ] rag 子任务域闸：domain=oa 无 QDRANT_COLLECTION_OA ⇒ output=「本域未配置检索」且 `astream_router_agent` 零调用（patch 计数断言绿）；ops 域闸放行（mock astream 正常产出 output · 既有行为零 diff）
- [ ] glossary 按域回退：glossary.oa.yaml 不存在 ⇒ oa 与 ops 展开逐字节等；monkeypatch 域件路径 ⇒ 读域件生效；按域缓存隔离（清缓存后互不影响 · 断言绿）
- [ ] 影子写 fail-closed：collection None ⇒ upsert/delete skip + warning · 零 DLQ 写入 · 零异常（断言绿）；ops 域影子写路径零 diff
- [ ] ingest/source_type 未动：ingest.py 相对 base 零 diff（git diff 为空 · 19 §4.3 钉死）
- [ ] 目标回归零红（test_rag_qdrant_backend / test_rag_fts_config / test_lg_rag_multi / test_supervisor_parallel_join · 真 PG 五键 blank）；全量 pytest 绿以 CI 终裁；`ruff check app tests` 绿；import-linter 12 contracts kept 0 broken
- [ ] 01_modules.md rag/lg_rag 行 p4-t4 备注 + HG-GRAPH-MODULES 签收行（graph-compile 绿）
- [ ] registry entry active · invokes 四件 · R1 审查文 GO · spec-wave task lint PASS

### 自检结论

（40 波收口回填 · 承 task_p4_t2_prompt_domain_loader 体例：验收逐条绿证 + 回归面台账 + 全量 pytest 以 CI 终裁）

## 必读列表

- 需求真源：`../ops-desk-workspace/docs/01-scope/03-general-agent/18-p4-generalization-design.md` §2.3（RAG 域化）+ §10 P4-T4 任务行（:284）+ §13 失败路径（:313）· `19-p4-contracts.md` §4（commit e453a36 钉死口径 · §4.1 矩阵/§4.2 glossary/§4.3 不泛化/§4.4 配置示例）
- 代码锚：`app/ops/rag/backend.py:39-40`（qdrant_collection 现状）· `app/ops/rag/glossary.py:18-29`（单路径+模块级缓存）· `app/ops/rag/shadow_write.py:111-147`（_shadow_upsert_safe/_shadow_delete_safe）· `app/ops/rag/retrievers/qdrant_retriever.py:38`（构造消费点 · 不改 · 限制登记）· `app/ops/rag/retrieve.py:171-178`（_semantic_search_qdrant 构造链）· `app/ops/prompts/domain_context.py`（T2 已合 · current_domain/set_current_domain/reset_current_domain）· `app/ops/lg_rag/multi/nodes.py:1921-1998`（rag_subtask_node · 闸插点 :1945 后 :1956 前）
- 契约锚：`.importlinter` rag-outbound（:100-125 · rag↛prompts）· lg-rag-outbound（:207-247 · lg_rag↛rag · →prompts 同族允许 :76 既有边实证）· importlib 先例 `app/ops/lg_rag/continuity.py`→session.summary
- 测试锚：`tests/test_rag_qdrant_backend.py`（_reset_env autouse 形态）· `tests/test_rag_fts_config.py:53`（glossary 展开断言）· `tests/test_capability_lookups.py:221`（node 直调先例）
- 体例先例：`docs/tasks/done/task_p4_t2_prompt_domain_loader.md`（同夜同授权 P4 波）· registry `docs/harness/audit_gates/registry.yaml:1264-1305` · 图谱签收 01_modules.md:48

## 思考轮

| 轮 | 结论 | early_stop |
|----|------|-----------|
| R0 | 范围对账（委派书 vs 19 §4 vs 18 §2.3/§10/§13 vs 代码锚）done | false |
| R1 | 失败路径推演（跨域泄漏 · 解析失败回落 · 空白串 · 缓存串扰 · 静态边界 · ops 漂移 · 并行冲突 · 环境性红）done | false |
| R2 | 非范围边界（ingest 不泛化 · T2 面不动 · T5 oa 资产 · .importlinter 零触 · 旁路链不设闸）done | false |
| R3 | 关键决策记录（importlib 双处 · 闸插点 · shadow skip 非 DLQ · glossary 回退=文件存在 · retriever 不加闸）done | false |
| R4 | 体例对账（p4-t2 模板 · registry/invokes/审查文/图谱签收 · 仓规条款一）done | false |
| R5 | 收尾复核（验收 10 条全锚定）done | false |

actual_last_round: R5

### R0 · 范围对账

委派书六条与 19 契约 §4 + 18 §2.3/§10 P4-T4 行/§13 逐条对齐：collection 三级回退矩阵（§4.1 · backend.py:39-40 改造）· glossary 按域文件回退+按域缓存（§4.2 · glossary.py:18 改造）· ingest/source_type 不泛化钉死（§4.3 · ingest.py:43/58-89 零触）· 域解析复用 T2 current_domain（§4.1 前提 · 勿自建第二真源）· 测试五类断言 · 图谱 rag 行备注+签收行。勘察已定位全部锚点（见必读列表）；消费面盘点：qdrant_collection 调用方=shadow_write.py:118/:141 + qdrant_retriever.py:38（经 retrieve.py:176 构造）；expand_query_for_fts 消费=retrieve.py:95（RAG_KW_EXPAND=true 才触达）。

### R1 · 失败路径推演

见「失败路径」节。推演增补：ops 链新键 QDRANT_COLLECTION_OPS 为契约 §4.1 矩阵内新 env——base 无此键读者，「未设时逐值一致」由测试三态对拍机判守；若部署侧未来预设该键则按契约优先语义生效（不属漂移）。rag 子任务闸插点定在 emit_subtask_running 之后：§10.7 running 帧已发（UX 保「子任务起步可见」），随后立即以 output 终态收口（done 帧路径不变）——帧序列零新型。

### R2 · 非范围边界

ingest 管线与 source_type 词表 19 §4.3 钉死不泛化（ingest.py 零 diff 机判）；T2 prompt 面不动仅消费；T5 oa 语料/glossary/模板资产不交付（glossary.oa.yaml 刻意不建=死配置规避 · 机制面「无件回退」天然成立）；.importlinter 零触（importlib 运行期解析 · 承 continuity.py 先例 · 图谱备注级登记）；lc_evidence_chain HTTP 旁路与 retrieve.py 内部链不设闸（契约 fail-closed 面=rag 子任务闸 · qdrant_retriever None 行为维持现状入限制登记）。

### R3 · 关键决策记录

- **importlib 运行期解析双处（守静态边界）**：rag-outbound 禁 rag→prompts、lg-rag-outbound 禁 lg_rag→rag.backend——`backend._current_domain()` 与 `nodes.py` 闸内 `qdrant_collection` 调用均走 importlib 运行期解析（承 lg_rag/continuity.py→session.summary 既定先例 · .importlinter 零改动 · 图谱备注级登记）；nodes.py 的 `current_domain` 用静态 import（lg_rag→prompts 同族允许 · :76 既有边实证）。
- **闸插点**：emit_subtask_running 之后、set_chain_step_hook 之前——running 帧保 §10.7 UX；未装 hook 不触 astream（后端零调用可机判）；output=「本域未配置检索」契约逐字短语进 aggregator，细节（缺失 env 键名）进 logger.warning。
- **影子写 skip 而非 DLQ**：collection None=禁用域预期态非故障——DLQ 留给真故障；skip+warning 保 fail-closed（不跨域写）且无噪声。ops 域 qdrant_collection 恒非 None → 零 diff。
- **glossary 回退判定=文件存在**（承 T2 目录回退同口径）：存在即读（坏 yaml 显式炸不静默）；不存在回退默认件；缓存按域 keyed（`_TABLES`）防跨域串扰；ops 域无 glossary.ops.yaml 天然回退（零 diff 双保险 · 承 19 §3.4 不建 assets/ops/ 同手法）。
- **qdrant_retriever 不加 None 闸**：非子任务路径（lc_evidence_chain HTTP 旁路/direct router）在契约 fail-closed 面之外；构造得 None 时维持现有「qdrant 调用异常→PG fallback」行为（不加新异常面 · 最小改动）；登记为限制。

### R4 · 体例对账

照 task_p4_t2_prompt_domain_loader（同夜同授权 P4 波）：task 档结构/人工闸表三行/registry entry（base=370a137a · allowed_app_files 四件=[rag/{backend,glossary,shadow_write}.py, lg_rag/multi/nodes.py] · banned_prefixes=[alembic/, scripts/]）/invokes by-task 四件 {10,30,40,50}/R1 审查文 GO 机读词/spec-wave@3.5.0 task lint PASS 为闸；图谱签收承 01_modules.md:48（p4-t2）先例。仓规条款一遵守（走 20-R1 审查文非 --allow-no-review）。

### R5 · 收尾复核

验收 10 条逐条锚：矩阵全格/domain 解析两通路/ops 零 diff 对拍/域闸零调用+放行/glossary 回退+缓存隔离/shadow skip/ingest 零 diff（全新断言）+ 回归+全量+ruff+import-linter + 图谱两件 + 过闸四件。回退 = revert 四件 app 文件 + 删 tests/test_rag_domain_config.py（零存量测试迁移面）。

## 实现备忘

### 偏差登记

（30/40 波回填）

### 限制登记

1. qdrant_retriever.py:38 构造消费点不加 None 闸：非子任务路径在契约 fail-closed 面外（R3 裁定 · 维持现有异常→fallback 行为）。
2. oa 语料/oa glossary/oa 模板资产归 P4-T5（委派书钉明 · 本波仅机制面）。
3. 全量 pytest 环境性红与 base 同路径一致（若有）非本波引入；CI 终裁。

## 测试策略

pytest tests（CI 终裁 · 真 PG postgresql+asyncpg://ops:ops_password@localhost:5432/opsdesk_test · 五键 blank 前缀 OPS_HITL_PERSISTENCE= OPS_CAPABILITY_ALLOW_WRITE= OPS_CAPABILITY_ALLOW_WRITE_TAGS= OPS_CAPABILITY_PERSISTENCE= OPS_CAPABILITY_EXTRA_MANIFESTS=）；新增 tests/test_rag_domain_config.py 全绿；目标回归 tests/test_rag_qdrant_backend.py / tests/test_rag_fts_config.py / tests/test_lg_rag_multi.py / tests/test_supervisor_parallel_join.py 全绿；全量回归环境性红与 base 370a137a 同路径基线逐签对照；ruff check app tests 绿；import-linter 12 contracts kept 0 broken；allowed_app_files 四件机判。

## 修订记录

| 日期 | 修订 |
|------|------|
| 2026-11-18 | 落卡（夜间自动执行波 · 授权 issue Cyning12/ops-desk-workspace#23 m03064/m03796 · 来源 18 设计文 §2.3/§10 P4-T4 行/§13 + 19 契约 §4 commit e453a36） |
