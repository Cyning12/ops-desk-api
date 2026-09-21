# SPEC：记忆既有行 embedding 回填批处理 + span 专门单测（v1）

> **状态**：`signed`（HG-SPEC-SIGNOFF=**approved** · 2026-09-21 · 维护者授权 00 本窗签收全部过程文档 · 原话「此spec完成后继续把完成后续spec，一个个进行，每次PR到main通过CI后自动merge」承前令「授权00签收所有过程文档」）
> **track**：`feature`（批处理运维功能 · 双轨必经 10-spec；**不改表结构 → 无 alembic 义务**；图谱零变更按实判见 §2 D5）
> **上游**：`../ops-desk-workspace/docs/08-interview/07_agent-memory-prompt-module-landscape_v1_zh.md`（记忆轨 M2+M6）
> **格式基准**：`docs/spec/llm-layer-hardening/SPEC-llm-layer-hardening_v1.md`（signed · PR #148 已合）
> **下游**：人签 SPEC → 00 出 task → 20-task-audit → HG-AUDIT-R1 → 30 实现
> **Open Folder（实现）**：`ops-desk-api/`

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **spec_slug** | `memory-embedding-backfill` |
| **invoke_slug** | `memory-embedding-backfill`（task 阶段） |
| **test_strategy** | `required` |
| **test_strategy_note** | DB 集成测试（对齐 `tests/test_memory_service_db.py` 先例）：扫描谓词只命中 `embedding IS NULL AND status='active'`、幂等重跑零重复嵌入、回写再核 active（竞态行记 skipped 不误嵌）、部分批失败计数与续跑；FakeEmbedder 注入（`_embed_one` 同款线程卸载断言）；span 单测 patch `continuity.update_current_span_metadata` 断言 `memory_facts_injected=N/0` 与 `memory_degraded`（capture-list 模式对齐 `tests/test_llm_routing.py:176`）；CLI dry-run/实跑计数对账；新 env 非法值回退 + warning；回归 `tests/test_memory_*.py` 全绿 |
| **Open Folder（实现）** | `ops-desk-api/` |
| **默认分支** | `task/memory-embedding-backfill` |
| **graph_change_layer（建议）** | 无（**零图谱变更按实判**：不新增路由/表/事件类型，`scripts/` CLI 不触发仓规三类同步义务；若 30 阶段裁定需登记脚本入口，task 阶段如实补 HG-GRAPH-MODULES 行） |

### 人工闸（SPEC 阶段）

| human_gate_id | status | 说明 |
|---|---|---|
| **HG-SPEC-SIGNOFF** | **pending** | 维护者签收本 SPEC 后方可 00 出 task / 30 改码（人签，不由 10-spec 代签） |

---

## 1. 背景与目标

### 现状（2026-09-21 实扫）

| 能力 | 状态 | 锚点 |
|---|---|---|
| `embedding` 列 | ✅ 已建 · nullable · deferred | `app/db/models.py:519-521` `Vector(MEMORY_FACT_EMBEDDING_DIM)`（bge-m3@1024 · `models.py:22`）；migration `alembic/versions/20260921_memory_facts_embedding.py`；注释钉死「既有行不回填 = 只走确定性通路即正确」（`models.py:515-518`） |
| 写入时嵌入（P1） | ✅ 默认关 | `app/ops/memory/service.py:314-337` `_maybe_embed_fact`：开关 `MEMORY_FACTS_VECTOR_RECALL_ENABLED` 开才嵌；`_embed_one`（`service.py:280-293`）`asyncio.to_thread` 线程卸载同步 Embedder，失败返回 None 不抛；`_set_embedding`（`service.py:296-311`）单列 UPDATE · caller session 走 SAVEPOINT 隔离，**嵌入/列写失败不阻断写入，行留 NULL 走确定性通路** |
| 嵌入文本口径 | ✅ 已定 | `service.py:263-268` `_fact_embed_text`：`key=value` 同形（与注入展示面对齐）——回填**必须复用本函数**，另造口径 = 静默语义漂移 |
| Embedder 协议 | ✅ | `app/ops/rag/embedder.py:27-30` `Embedder(Protocol)`：**同步** `embed(texts: list[str]) -> list[list[float]]` + `name` fingerprint；`ApiEmbedder`（`embedder.py:64-110`）内置 `max_retries=3` 指数退避（`time.sleep(2**attempt)` · timeout=60s）；`get_query_embedder` 单例工厂（`embedder.py:147-172`） |
| 向量召回对 NULL 行行为 | ✅ 正确但覆盖缺 | `service.py:237-245` `_VECTOR_RECALL_SQL` 带 `embedding IS NOT NULL`——存量行**永远进不了向量 top-M**，只能靠确定性 top-N 兜底；paraphrase（复述）查询对存量行命中率低 |
| 影子写/迁移对账先例 | ✅ | `app/ops/rag/shadow_write.py`（DLQ 落 `ops_qdrant_dlq` · 失败绝不阻塞主链路）；`reports/qdrant_migrate/reconcile_p1_20260813.yaml`（报告形态：status / 双侧计数 / count_diff / thresholds / recorded_at） |
| span `memory_facts_injected` | ⚠️ 发射在 · **无专门单测** | 发射点 `app/ops/lg_rag/continuity.py:240,243`（`update_current_span_metadata`）；tests/ 全仓 grep 零断言（仅 `test_llm_routing.py:176` 等 capture-list monkeypatch 先例可复用）；P0 已知未测项 ①（`docs/tasks/done/task_memory_facts_p0.md:219`） |
| 记忆金样资产 | ⚠️ 在未合并分支 | `evals/memory/golden_v1.yaml`（50 条：应记 14 / 负样本 14 / supersede 10 / **复述 12**）+ `run_eval.py`（fake/live 双模式 · live 连真 PG）在 `task/memory-golden-eval`（commit a54b8ed · **未合 master · 本分支不存在**，`git ls-files evals/memory/` 为空） |

### 痛点

1. **存量行召回覆盖缺**：P0 时期（向量召回上线前）写入的 active 行 `embedding IS NULL`，复述/语义相近查询永远走不到它们——向量通路上线越久，新老行召回质量两极分化越明显（静默覆盖缺口，无任何报错面）。
2. **缺口无自愈**：`_maybe_embed_fact` 只嵌新写行；NULL 行除非被 supersede 重写，否则终身确定性通路。
3. **观测断言缺**：`memory_facts_injected` span 是记忆注入唯一线上计数面，无单测钉死 → 重构 continuity 时静默丢失无人发现（P0 遗留 ①）。

### 一句话目标

在 **召回融合算法 / 写入闸 / 嵌入文本口径 / 表结构一行不改** 的前提下，交付 **幂等可断点续跑的存量行 embedding 回填批处理**（扫 NULL → Embedder → 回写 · 限速重试 · 跑批报告 · 干跑/实跑对账），并补上 **span `memory_facts_injected` 专门单测**，回填后复述召回金样对照有提升证据。

设计纪律（签收时锁死）：

1. **嵌入文本口径唯一**：回填嵌入文本 = `service.py::_fact_embed_text(key, value)` 原样复用，禁止另造序列化（否则在线写入与回填向量空间不一致，静默腐烂）。
2. **幂等靠谓词不靠记忆**：断点续跑的正确性只依赖 `embedding IS NULL AND status='active'` 谓词 + 稳定序分页；checkpoint 若存在仅为加速，**不作为正确性依据**。
3. **回写再核状态**：UPDATE 谓词必带 `id + status='active'`，rowcount=0 → 记 skipped（回填期间被 supersede/revoke 的行**不误嵌**）。
4. **失败不静默不放大**：批级失败不重试叠加（`ApiEmbedder` 内部已 3 次退避，回填层再退避 = 双重放大）；失败行进报告 `failed_ids`，靠重跑自愈；报告计数与 DB 实况可对账。
5. **模型 fingerprint 防混库**：回填前校验 `embedder.name` 与维度 = `MEMORY_FACT_EMBEDDING_DIM`（1024），不符 → 显式失败 exit ≠ 0，**不嵌半库异构向量**（对齐 `embedder.py` 序言 fingerprint 纪律）。

---

## 2. 范围

### D1 · 回填批处理主体（必做）

| 项 | 约定 |
|---|---|
| 入口 | `scripts/memory_embedding_backfill.py` CLI（对齐 `scripts/rag_ingest.py` 先例：独立可执行、argparse、退出码语义）；**非** alembic data migration、**非**对外管理端点（裁决见 §4） |
| 扫描 | `SELECT … FROM ops_memory_facts WHERE embedding IS NULL AND status='active' ORDER BY id ASC` keyset 分页（`id > :last_id`），页大小 env `MEMORY_BACKFILL_BATCH_SIZE`（默认 32 · 对齐 `SentenceTransformerEmbedder.batch_size=32` 与 ApiEmbedder 批形态）；稳定序分页保证中断重扫无遗漏无重复 |
| 嵌入 | 每页文本 = `_fact_embed_text(key, value)` 批量 `embedder.embed(texts)`（协议原生批）；同步 Embedder 经 `asyncio.to_thread` 卸载（对齐 `service.py:280-293` 先例）；embedder 显式注入可测，默认 `get_query_embedder()` |
| 回写 | 逐行 `UPDATE … SET embedding=:vec WHERE id=:id AND status='active'`（再核纪律 3）；rowcount=1 → success，0 → skipped；单行回写失败 → failed（不连坐同页其他行） |
| 前置校验 | 启动即查 `embedder.name` + 试嵌一条断维度 == 1024；不符 → 报错 exit 2（不嵌一行）；`SILICONFLOW_API_KEY` 缺失等同处理（`ApiEmbedder` 构造即抛，CLI 翻成 exit 2） |
| 开关 | 回填是显式运维动作，**不挂** `MEMORY_FACTS_VECTOR_RECALL_ENABLED`（该开关管在线路径）；CLI 本身即开关 |

### D2 · 幂等断点续跑 · 限速重试 · 跑批报告（必做）

| 项 | 约定 |
|---|---|
| 幂等 | 谓词幂等：已回写行不再命中扫描；重跑/并发误双跑不产生重复嵌入（重复 = 同值覆盖，无害但计入 skipped-already-done 观测） |
| 断点续跑 | 主机制 = 谓词幂等 + keyset 重扫（零状态即正确）；可选 `MEMORY_BACKFILL_CHECKPOINT` 文件记 `last_id` 仅作跳过加速，文件损坏/缺失 → 从头重扫（正确性不受影响） |
| 限速 | 批间 `MEMORY_BACKFILL_SLEEP_MS`（默认 200ms）+ 单批超时沿 `ApiEmbedder` timeout=60s；非法值回退默认 + warning（全 env 统一纪律，对齐 `service.py:248-260` 模式） |
| 重试 | **回填层零行级重试**（`ApiEmbedder` 内置 3 次指数退避已足；叠加 = 对挣扎下游双重放大）；批失败 → 整页行记 failed，报告落 `failed_ids`，重跑自愈 |
| 报告 | `reports/memory_embedding_backfill/backfill_<UTC 时间戳>.yaml`，形态对齐 `reports/qdrant_migrate/reconcile_p1_20260813.yaml`：`status`（pass/failed/partial）· `scanned` / `embedded` / `skipped` / `failed` 计数 · `failed_ids`（截断上限）· `embedder_name` · `batch_size` / `sleep_ms` · `dry_run` 标记 · `elapsed_s` · `recorded_at`；stdout 同步摘要 |
| 干跑 | `--dry-run`：只扫描计数 + 前置校验，**零嵌入零写库**；报告 `dry_run: true` |

### D3 · 并入小项：span `memory_facts_injected` 专门单测（必做）

| 项 | 约定 |
|---|---|
| 测试位 | `tests/test_memory_injection.py` 追加（或同义新文件）；capture-list monkeypatch `app.ops.lg_rag.continuity.update_current_span_metadata`（对齐 `tests/test_llm_routing.py:176` 模式） |
| 断言 | ① 有 facts 注入 → 捕获 `{"memory_facts_injected": N}` 且 N == 注入条数；② 零 facts → `{"memory_facts_injected": 0}`（`continuity.py:240` 分支）；③ 召回故障 → `{"memory_degraded": True}` 且不出现 `memory_facts_injected`（`continuity.py:237` 分支）；④ 开关关闭 → 零 span 调用且输出逐字节一致（既有断言补强） |

### D4 · 干跑/实跑对账 + 金样对照（必做）

| 项 | 约定 |
|---|---|
| 干跑/实跑对账 | 同一库序先 `--dry-run` 再实跑：断言 dry-run `scanned` == 实跑 `scanned`，实跑 `embedded + skipped + failed == scanned`；实跑后重扫 `embedding IS NULL AND status='active'` 剩余数 == `failed`（对账不等 → 报告 `status: failed`） |
| 金样对照 | **锚点按实扫**：`evals/memory/golden_v1.yaml`（复述 12 条）+ `run_eval.py` live 模式在 `task/memory-golden-eval` 分支（a54b8ed · 未合 master）。验收分两态：① 该资产已合入 → live 金样回填前/后各跑一次，复述 top1/top3 不降且报告留档 `reports/memory_embedding_backfill/`；② 未合入 → 用 DB 集成测试夹具替代：写入 facts 强制 `embedding=NULL` 模拟存量 → paraphrase 查询回填前 `recall_with_vector` 不命中 / 回填后命中 top1（FakeEmbedder 确定性向量，CI 可跑）。两态都必须在 task 验收中写明走了哪条 |
| 防假绿 | 金样/夹具对照必须含「回填前基线」数据，禁止只贴回填后结果 |

### D5 · 图谱与文档（必做 · 按实判零图谱变更）

- **图谱零变更义务 = 无**：本 SPEC 不新增路由/表/事件类型（仓规三类同步义务均不触发）；`scripts/` 新增 CLI 不在 `docs/_tech_graph/` 登记义务内。**若 30 阶段实现形态偏离**（如改加管理端点或 checkpoint 表），task 阶段必须如实补 HG-GRAPH-MODULES 行，不得沿用本裁定
- `app/ops/memory/README.md` 增补回填小节（CLI 用法 / env 表 / 报告形态 / 与 `_maybe_embed_fact` 的口径同源声明）
- `./scripts/graph-compile.sh` 绿（回归保险，非新增义务）

---

## 3. 非范围

- ❌ 改召回融合算法 / 权重（`_fuse_recall` / `SIM_FLOOR` / `HALF_LIFE_DAYS` / 来源权重不动 · 占位草案原文保留；调参归 `memory-fusion-weight-tuning` 轨）
- ❌ 改写入闸 / 状态机 / 嵌入文本口径（`should_write` / `_fact_embed_text` / `_maybe_embed_fact` 行为不变 · 占位草案「改闸」原文保留）
- ❌ 对外端点 / 管理 API（占位草案原文保留；CLI -only 是本 SPEC 的显式裁决）
- ❌ 画像 / preference 记忆（`kind='fact'` 以外 · 占位草案原文保留）
- ❌ 表结构变更（无 alembic 义务；`embedding` 列已 nullable 就位。若 30 阶段发现必须改表，**回 10-spec 修订本 SPEC**，不得在 task 阶段静默加 migration）
- ❌ checkpoint DB 表 / DLQ 表（量级不符：单表 NULL 行回填是一次性运维，报告 `failed_ids` + 重跑足够；`shadow_write.py` 的 DLQ 是持续在线链路的形态，不照抄）
- ❌ 在线写入路径并发改造（`_maybe_embed_fact` 逐行嵌入保持现状；回填批嵌入不反哺在线路径）
- ❌ `evals/memory/` 金样资产本身的建设/合并（属 `memory-golden-eval` 轨；本 SPEC 只消费，两态验收见 §2 D4）
- ❌ web / ios

---

## 4. 方案对比（R2）

### 入口形态

| 方案 | 做法 | 收益 | 代价 | 裁决 |
|---|---|---|---|---|
| **S1 · 独立 CLI 脚本（本 SPEC）** | `scripts/memory_embedding_backfill.py`，argparse + 退出码 + 报告落 `reports/` | 对齐 `scripts/rag_ingest.py` 先例；显式运维动作、可 dry-run、可重复执行；零运行时面新增（无新端点无新依赖）；报告形态直接复用 qdrant_migrate 先例 | 需人工/运维触发（一次性回填正合适） | **推荐** |
| S2 · alembic data migration | 迁移内嵌 Python 循环调 API | 随 deploy 自动跑 | migration 里打外网嵌入 API = 部署被下游故障绑架（超时/429 阻塞 upgrade）；不可 dry-run；失败语义与 schema 迁移耦合；**本 SPEC 连 schema 变更都没有**，为数据回填开 migration 名实不符 | 弃 |
| S3 · 管理端点 | POST /admin/backfill 异步跑 | 可远程触发 | 新鉴权面 + 新路由（触发图谱义务）+ 长任务生命周期管理；单仓试点量级不符；占位草案已列「对外端点」为非范围 | 弃 |

### 嵌入并发模型

| 方案 | 做法 | 收益 | 代价 | 裁决 |
|---|---|---|---|---|
| **S1 · 小批 + 线程卸载（本 SPEC）** | 每页 ≤32 条一次 `embed()` 批调用，`asyncio.to_thread` 卸载同步 Embedder，页间 sleep 限速 | Embedder 协议原生批（一次 HTTP 32 条，QPS 天然低）；完全复用 `service.py:280-293` 已验证先例；失败粒度 = 页，语义简单 | 吞吐上限 = 串行页速（存量回填不要求实时，可接受） | **推荐** |
| S2 · asyncio 高并发批 | `asyncio.gather` 并发多页 embed | 吞吐高 | Embedder 是**同步阻塞** httpx，gather 并发必须全绕 to_thread → 线程池放大下游 QPS，与限速目标直接冲突；`ApiEmbedder` 内置退避在并发下互相叠加，429 风暴风险 | 弃 |
| S3 · 多进程 | multiprocessing 并行 | 真并行 | 单表单次回填量级不符；DB 连接与报告聚合复杂化 | 弃 |

### 断点续跑态

| 方案 | 做法 | 收益 | 代价 | 裁决 |
|---|---|---|---|---|
| **S1 · 谓词幂等 + keyset 重扫（本 SPEC）** | `embedding IS NULL` 即天然进度；`id ASC` keyset 分页；可选 checkpoint 文件仅加速 | **零状态即正确**：中断/SIGKILL/双跑都安全；无新表无新文件格式语义；对账极简（重扫剩余 == failed） | 重跑要重扫全表（扫描是索引可撑的 NULL 过滤，量级小） | **推荐** |
| S2 · checkpoint 表/文件作正确性依据 | 记 last_done_id，重跑从 checkpoint 续 | 免重扫 | 多一个真相源：checkpoint 与库实况可能分叉（手工改库/部分提交），静默跳过未嵌行 = 本 SPEC 最怕的静默错；为加速优化引入正确性风险不值 | 弃（降级为 S1 的可选加速件） |
| S3 · 内存扫序无断点 | 一次跑完，中断从头来 | 最简 | 大存量 + 嵌入 API 故障窗口下重跑成本高；与「失败重试 + 断点续跑」的任务要求直接冲突 | 弃 |

---

## 5. 边界 / 失败路径 / 安全（failure_paths）

| 触发 | 行为 | 可重试 |
|---|---|---|
| 嵌入 API 429/5xx/超时 | `ApiEmbedder` 内置指数退避 ≤3 次（`embedder.py:90-110`）；耗尽 → 该页整页记 failed（`failed_ids` 落报告），**回填层不叠加重试**；继续下一页，不中断跑批 | Y（重跑自愈） |
| 嵌入 API 持续故障（页失败率 100% × N 页） | 连续 3 页全败 → 判定下游不可用，提前终止，报告 `status: failed` exit 1（不做无用功连打挣扎下游） | Y（人工重跑） |
| 部分批失败（页内单行回写 DB 错） | 单行独立 UPDATE：失败行记 failed，同页其他行不受影响；报告计数守恒 `embedded+skipped+failed==scanned` | Y（重跑） |
| 重复回写（重跑 / 误双跑） | 谓词幂等：已嵌行不再命中扫描；极端竞态（两实例同扫一页）= 同 `embedder.name` 同文本同值覆盖，语义无害；报告观测可发现 | — |
| 回填期间行被 supersede/revoke/expire | 回写 UPDATE 带 `status='active'` 再核，rowcount=0 → 记 skipped，**不误嵌失效行**（嵌入失效行虽不进召回——`_VECTOR_RECALL_SQL` 只认 active——但属浪费与审计噪声） | — |
| 误嵌 inactive 行（谓词漏 status） | 扫描与回写**双处**带 `status='active'`（扫描谓词 + 回写再核），单测断言 superseded/revoked/expired 行零嵌入 | — |
| 嵌入模型/维度漂移（`RAG_EMBED_MODEL` 被改） | 前置校验 `embedder.name` + 试嵌维度 == 1024，不符 exit 2 零写入（防半库异构向量混库 · `embedder.py` fingerprint 纪律） | — |
| `SILICONFLOW_API_KEY` 缺失 | `ApiEmbedder` 构造即抛（`embedder.py:79-81`）→ CLI 翻 exit 2 显式报错，不静默退 local ST（冷启动纪律） | — |
| DB 故障（扫描/回写连接断） | 当前页失败记 failed；连接级故障 → 终止跑批 exit 1 + 报告留档；**不伪装成功** | Y（重跑） |
| 中断（SIGINT/SIGTERM） | 页边界响应中断：当前页完成后落 checkpoint（若启用）+ 部分报告（`status: partial`）再退出；谓词幂等保证下次续跑正确 | Y |
| 干跑误当实跑 | `--dry-run` 零写库零嵌入（仅扫描计数 + 前置校验），报告 `dry_run: true` 永不混淆 | — |
| 新 env 非法值 | 回退默认 + warning（`MEMORY_BACKFILL_BATCH_SIZE` / `MEMORY_BACKFILL_SLEEP_MS` / `MEMORY_BACKFILL_CHECKPOINT`，对齐 `service.py:248-260` 模式） | — |
| 向量列不存在（migration 未跑） | 启动前置探测 `embedding` 列（轻量 SELECT），缺失 → exit 2 显式报错（对齐「向量列不存在 → 回退确定性」的显式哲学，不静默零回填） | — |

安全：回填复用既有 `SILICONFLOW_API_KEY`（无新凭证面）；报告只记 id/计数/模型名，**不存** fact 明文 value（对齐 `ops_llm_usage` 不存正文纪律）；CLI 无网络监听面。

---

## 6. 验收标准

### D1 · 回填主体

- [ ] DB 集成测试：造 active-NULL 行 3 条 + superseded-NULL / revoked-NULL / active-已嵌 各 1 条 → 跑回填 → 断言仅 3 条 active-NULL 被嵌入（FakeEmbedder 注入，`embed()` 收到文本 == `_fact_embed_text(key, value)` 逐条一致），inactive 行 embedding 保持 NULL
- [ ] 回写再核：回填进行中把目标行置 superseded（模拟竞态）→ 该行计 skipped，embedding 保持 NULL
- [ ] 前置校验：FakeEmbedder 维度 ≠ 1024 或 `name` 不符 → exit 2，DB 零写入
- [ ] keyset 分页：batch_size=2 造 5 行 → FakeEmbedder 调用 3 页且每页 id 序严格递增无重复

### D2 · 幂等/续跑/报告

- [ ] 幂等：回填跑两次，第二次 `scanned=0 · embedded=0`，FakeEmbedder 零调用
- [ ] 断点续跑：跑至中途模拟中断（第 1 页成功第 2 页抛错终止）→ 重跑 → 全部补齐且第 1 页行不重复嵌入（FakeEmbedder 调用文本不含已嵌行）
- [ ] 部分失败：FakeEmbedder 第 2 页抛 `httpx.HTTPError` → 报告 `embedded=2, failed=2`，`failed_ids` 含第 2 页 id；重跑后 failed 清零
- [ ] 报告形态：yaml 含 status/scanned/embedded/skipped/failed/failed_ids/embedder_name/dry_run/elapsed_s/recorded_at，且 `embedded+skipped+failed==scanned` 守恒断言
- [ ] env 非法值回退 + warning 全覆盖；`--dry-run` 断言 DB 零写、embedder 零调用、报告 `dry_run: true`

### D3 · span 单测

- [ ] 有 facts：捕获 `update_current_span_metadata` 收到 `{"memory_facts_injected": N}`，N == 实际注入条数
- [ ] 零 facts：收到 `{"memory_facts_injected": 0}`
- [ ] 召回故障：收到 `{"memory_degraded": True}` 且全程无 `memory_facts_injected`
- [ ] 开关关闭：零 span 调用（与既有逐字节一致断言并存）

### D4 · 对账与金样对照

- [ ] 干跑/实跑对账：同库序 dry-run `scanned` == 实跑 `scanned`；实跑后重扫 NULL-active 剩余数 == 报告 `failed`（不等 → status: failed）
- [ ] 复述召回对照（二选一，task 验收须写明走了哪条）：① `evals/memory/` 已合入 → live 金样回填前/后复述 top1/top3 不降且报告留档（含回填前基线）；② 未合入 → 集成夹具：active-NULL 存量行 + FakeEmbedder 确定性向量，paraphrase 查询回填前 `recall_with_vector` top1 不命中该存量行 / 回填后命中 top1
- [ ] 变异检验：把扫描谓词 `status='active'` 删掉一次，确认 D1 的「inactive 行零嵌入」断言真会 fail（不验收空真规则）

### 工程

- [ ] ruff + pytest 绿（本波新测 + `tests/test_memory_*.py` 全量回归）
- [ ] `graph-compile.sh` 绿；图谱零变更裁定与实现形态一致（若实现加了端点/表 → 本 SPEC 回炉）
- [ ] `app/ops/memory/README.md` 回填小节 + env 表落盘

---

## 7. 思考轮控制（10-spec）

| 轮 | 结论摘要 | 状态 |
|---|---|---|
| R0 | 上游记忆轨 M2+M6；占位 SPEC 三块范围草案经实扫全部成立；金样锚点实扫发现 `evals/memory/` 在未合并分支（本仓 HEAD 无此目录）→ 验收必须两态化 | done |
| R1 | 范围 = D1 回填主体 / D2 幂等限速报告 / D3 span 单测 / D4 对账金样 / D5 文档；非范围 = 融合算法 / 闸 / 对外端点 / 画像 / 表结构 / checkpoint 表 / 金样建设本身（占位草案非范围全保留并扩 4 条） | done |
| R2 | 三组对比各 ≥2：入口选独立 CLI（弃 alembic data migration：部署被外网 API 绑架且无 schema 变更名实不符；弃管理端点：新鉴权面量级不符）；并发选小批线程卸载（弃 asyncio 并发：同步阻塞 Embedder 并发 = 限速目标自反；弃多进程）；续跑选谓词幂等+keyset（弃 checkpoint 作正确性依据：双真相源分叉 = 静默跳过风险；弃纯内存无断点） | done |
| R3 | failure_paths 13 条，核心四条：嵌入故障回填层零叠加重试（ApiEmbedder 已退避 3 次，叠加 = 双重放大）、回写再核 active（竞态不误嵌失效行）、模型维度前置校验（防异构向量混库）、谓词幂等保中断/双跑安全；report 不存 fact 明文 | done |
| R4 | 验收全为可执行断言：扫描谓词正交夹具（active/inactive/已嵌）、幂等二次跑零调用、中断续跑不重复、计数守恒、span 三分支 N/0/degraded、干跑对账、金样两态 + 变异检验一条 | done |
| R5 | SPEC draft-complete 可交人签 HG-SPEC-SIGNOFF；签后 00 出 task（建议单 task 一波：D3 span 单测先行提交，D1/D2/D4 回填主体随后） | done |
| early_stop | no | — |
| residual_risks | ① 金样对照依赖 `task/memory-golden-eval` 合入时序，未合入则走夹具态（召回提升证据强度弱于真 live 金样）；② 回填速率（默认 32/页 + 200ms）未经真实存量校准，大行数时跑批时长需实测；③ `evals/memory/` 在本分支不存在，task 验收两态选择须维护者知悉 | 签收时知悉 |

---

## 8. 下一棒

1. **维护者**：审本 SPEC → 签 `HG-SPEC-SIGNOFF=approved`
2. **00**：起草 `docs/tasks/active/task_memory_embedding_backfill.md`（范围 D1–D5 · failure_paths 沿用 SPEC §5 · 人工闸表按实判：无 HG-GRAPH-MODULES 义务除非实现形态偏离）
3. **20-task-audit**：书面审 → 维护者签 `HG-AUDIT-R1`
4. **30**：`task/memory-embedding-backfill` 分支实现（D3 先行提交，D1/D2/D4 随后）
5. **40**：验收（含金样两态写明）→ PR（与 memory-facts-p0/p1 同模式）

### 下一棒可复制 Prompt（20-spec-audit 预审 / 00 起草 task）

```text
你是 ops-desk-api 仓（/Users/cyning/Desktop/Ops-desk/ops-desk-api）的 <20-spec-audit ｜ 00>。
SPEC：docs/spec/memory-embedding-backfill/SPEC-memory-embedding-backfill_v1.md（draft-complete · HG-SPEC-SIGNOFF=pending）。
<20-spec-audit>：书面审范围/非范围/验收/failure_paths 与 R0–R5 思考轮，结论落盘 docs/harness/reviews/，不代签人闸。
<00>：待维护者签 HG-SPEC-SIGNOFF=approved 后，按 SPEC §8 起草 docs/tasks/active/task_memory_embedding_backfill.md（D1–D5 · failure_paths 沿用 SPEC §5 · 图谱闸按实判零变更）。
```

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-09-21 | 占位稿（范围草案 + 锚点 + 验收方向 + 接续指引） |
| 2026-09-21 | 10-spec 补全：实扫 `memory/service.py`（_embed_one/_set_embedding/_fact_embed_text）· `rag/embedder.py`（协议 + ApiEmbedder 内置退避）· `rag/shadow_write.py`（DLQ 先例）· `models.py:515-521`（embedding nullable/deferred）· `continuity.py:237-243`（span 发射点）· `reports/qdrant_migrate/`（报告形态）锚点落地；三块范围断言化验收；R0–R5 回填；方案对比三组；failure_paths 13 条；track 裁定 `feature`（无 alembic 义务 · 图谱零变更按实判）；金样锚点实扫裁定两态验收；HG-SPEC-SIGNOFF 保持 pending 待人签 |
