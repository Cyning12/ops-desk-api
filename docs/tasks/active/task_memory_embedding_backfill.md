# Task：记忆既有行 embedding 回填批处理 + span 专门单测（memory-embedding-backfill）

> **状态**：`signed`（2026-09-21 · 20-task-audit R1 PASS 零阻塞 · HG-TASK-DRAFT/HG-AUDIT-R1=approved（维护者授权 00 代录）· 可 30）  
> **类型**：feature / 运维批处理（**不改表结构 → 无 alembic 义务**；图谱零变更按实判，偏离回炉条款见闸表与 D5）  
> **上游 SPEC**：`docs/spec/memory-embedding-backfill/SPEC-memory-embedding-backfill_v1.md`（**signed** · HG-SPEC-SIGNOFF=approved 2026-09-21）  
> **分支**：`task/memory-embedding-backfill`（**禁止 master 直改**）  
> **10 注**：2026-09-21 · 维护者授权 00 本窗签收全部过程文档（原话「此spec完成后继续把完成后续spec，一个个进行，每次PR到main通过CI后自动merge」承前令「授权00签收所有过程文档」，留痕于 SPEC 状态行）· HG-TASK-DRAFT / HG-AUDIT-R1 由 00 在该授权下于 20 审后代录，**本帽不签**

---

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `memory-embedding-backfill` |
| **git_branch** | `task/memory-embedding-backfill` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | DB 集成测试（对齐 `tests/test_memory_service_db.py` 先例）：扫描谓词只命中 `embedding IS NULL AND status='active'`、幂等重跑零重复嵌入、回写再核 active（竞态行记 skipped 不误嵌）、部分批失败计数与续跑；FakeEmbedder 注入（`_embed_one` 同款线程卸载断言）；span 单测 patch `continuity.update_current_span_metadata` 断言 `memory_facts_injected=N/0` 与 `memory_degraded`（capture-list 模式对齐 `tests/test_llm_routing.py:176`）；CLI dry-run/实跑计数对账；新 env 非法值回退 + warning；回归 `tests/test_memory_*.py` 全绿 |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | 无（**零图谱变更按实判** · SPEC §2 D5 裁定；不新增路由/表/事件类型，`scripts/` CLI 不触发仓规三类同步义务） |
| **graph_delta** | 无 |
| **graph_delta_note** | **回炉补闸条款**：若 30 阶段实现形态偏离零变更预判（如改加管理端点 / checkpoint 表 / 新事件类型），**不得沿用本裁定**——退回 10-task 补 HG-GRAPH-MODULES 新行义务 + `docs/_tech_graph/` 如实登记后方可续 30 |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 契约真值在 SPEC `memory-embedding-backfill` |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,20,30,40` |
| **invoke_retention_profile** | `default` |
| **experience_capture** | `recommended` |
| **kpi_aggregator** | `CLOSE` |
| **orchestration** | 10 落稿 → 20-task-audit → 维护者授权 00 代录闸 → 30（建议 **D3 span 单测先行提交**，D1/D2/D4 回填主体随后 · 承 SPEC R5/§8）→ 40 → CLOSE |
| **freeze_id** | 无（不改 `lg-rag-sse-v1` / `lg-rag-http-v1` / `lc-evidence-http-v1`） |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | **approved** | 20-R1, 30 | 2026-09-21 · 00 验收 10-task 稿通过（维护者本窗授权 00 签收过程文档 · 原话留痕 SPEC 状态行） |
| HG-AUDIT-R1 | **approved** | **30** | 2026-09-21 · 20-task-audit R1 PASS 零阻塞零退回（`docs/harness/reviews/task_memory_embedding_backfill_audit_R1_20260921.md`）· 维护者本窗授权 00 代录签收 |
| HG-GRAPH-MODULES | **approved** | **30** | 2026-09-21 真读核验 `docs/_tech_graph/l1/01_modules.md`：模块表已建置（bootstrap 签 2026-07-16 · `memory` 行在表 · 签录链完整含当日 memory_facts_p0/p1 等四行）。SPEC §2 D5 判本 task **零图谱变更**（不新增路由/表/事件类型 · `scripts/` 新增 CLI 不在登记义务内）→ **无新签义务**；**若 30 偏离零变更预判则回炉补闸**（见 graph_delta_note，不得沿用本裁定） |
| HG-PILOT-OPSDESK-GLAYER | n/a | 物理分层试点改码 | 本 task 不涉物理分层试点 |

---

## 背景与目标

现状（SPEC §1 实扫锁死）：`embedding` 列已就位（nullable · deferred · bge-m3@1024）；写入时嵌入（P1 `_maybe_embed_fact`）默认关且只嵌新写行；向量召回 SQL 带 `embedding IS NOT NULL`——**P0 时期存量 active 行终身进不了向量 top-M**，只能靠确定性 top-N 兜底，复述/语义相近查询对存量行命中率低，且缺口**无自愈、无报错面**（静默覆盖缺口）。另 `memory_facts_injected` span 发射在 `continuity.py:240,243` 但 tests/ 全仓零断言（P0 遗留未测项 ①）。

一句话目标（SPEC 锁死）：在 **召回融合算法 / 写入闸 / 嵌入文本口径 / 表结构一行不改** 的前提下，交付 **幂等可断点续跑的存量行 embedding 回填批处理**（扫 NULL → Embedder → 回写 · 限速重试 · 跑批报告 · 干跑/实跑对账），并补上 **span `memory_facts_injected` 专门单测**，回填后复述召回有对照提升证据。

设计纪律（30 不得违反 · 承 SPEC §1 签收锁死五条）：

1. **嵌入文本口径唯一**：回填嵌入文本 = `service.py::_fact_embed_text(key, value)` 原样复用，禁止另造序列化（否则在线写入与回填向量空间不一致，静默腐烂）。
2. **幂等靠谓词不靠记忆**：断点续跑正确性只依赖 `embedding IS NULL AND status='active'` 谓词 + 稳定序分页；checkpoint 若存在仅为加速，**不作为正确性依据**。
3. **回写再核状态**：UPDATE 谓词必带 `id + status='active'`，rowcount=0 → 记 skipped（回填期间被 supersede/revoke 的行**不误嵌**）。
4. **失败不静默不放大**：批级失败不重试叠加（`ApiEmbedder` 内部已 3 次退避，回填层再退避 = 双重放大）；失败行进报告 `failed_ids`，靠重跑自愈；报告计数与 DB 实况可对账。
5. **模型 fingerprint 防混库**：回填前校验 `embedder.name` 与维度 = `MEMORY_FACT_EMBEDDING_DIM`（1024），不符 → 显式失败 exit ≠ 0，**不嵌半库异构向量**。

---

## 现状锚点（只读 · 30 必读 · 10 已扫 · 承 SPEC §1）

| 主题 | 路径 · 锚点 | 现状 |
|------|-------------|------|
| embedding 列 | `app/db/models.py:519-521` `Vector(MEMORY_FACT_EMBEDDING_DIM)`（1024 · `models.py:22`）；migration `alembic/versions/20260921_memory_facts_embedding.py` | 已建 · nullable · deferred；注释钉死「既有行不回填 = 只走确定性通路即正确」（`models.py:515-518`）——本 task 正是补上回填 |
| 写入时嵌入 | `app/ops/memory/service.py:314-337` `_maybe_embed_fact` · `:280-293` `_embed_one`（`asyncio.to_thread` 卸载 · 失败返回 None 不抛）· `:296-311` `_set_embedding`（SAVEPOINT 隔离） | 默认关（`MEMORY_FACTS_VECTOR_RECALL_ENABLED` 开才嵌）；失败不阻断写入、行留 NULL |
| 嵌入文本口径 | `service.py:263-268` `_fact_embed_text`：`key=value` 同形 | **回填必须复用本函数**，另造口径 = 静默语义漂移 |
| Embedder 协议 | `app/ops/rag/embedder.py:27-30` `Embedder(Protocol)` 同步 `embed(texts)` + `name` fingerprint；`ApiEmbedder`（`:64-110`）内置 max_retries=3 指数退避 · timeout=60s；`get_query_embedder` 单例工厂（`:147-172`） | 协议原生批；回填层**零行级重试**（内置退避已足） |
| 向量召回对 NULL 行 | `service.py:237-245` `_VECTOR_RECALL_SQL` 带 `embedding IS NOT NULL` | 存量行永远进不了向量 top-M（本 task 消除此覆盖缺口） |
| 影子写/迁移对账先例 | `app/ops/rag/shadow_write.py`（DLQ 不阻塞主链路）；`reports/qdrant_migrate/reconcile_p1_20260813.yaml`（status / 双侧计数 / count_diff / thresholds / recorded_at） | 报告形态先例可直接复用 |
| span `memory_facts_injected` | `app/ops/lg_rag/continuity.py:240,243` `update_current_span_metadata`；degraded 分支 `:237` | 发射在 · **tests/ 全仓 grep 零断言**（2026-09-21 本帽实扫确认）；capture-list 先例 `tests/test_llm_routing.py:176` |
| CLI 先例 | `scripts/rag_ingest.py`（独立可执行 · argparse · 退出码语义） | 回填 CLI 对齐此形态 |
| 记忆金样资产 | `evals/memory/golden_v1.yaml`（50 条 · 复述 12）+ `run_eval.py`（fake/live 双模式）在 `task/memory-golden-eval`（commit a54b8ed · **未合 master**） | 2026-09-21 本帽实扫：`git ls-files evals/memory/` = **0 tracked**（工作区仅剩空 `__pycache__`）→ D4 验收两态化 |
| DB 集成测试先例 | `tests/test_memory_service_db.py`（真 PG opsdesk_test · skipif DB_AVAILABLE）；`tests/conftest.py:166-172` 已保 `embedding vector(1024)` 列 | 回填新测直接对齐此先例，夹具零新增义务 |
| 回归底线 | `tests/test_memory_*.py`（injection / service_db / vector_p1 / extract_p1）· `tests/test_rag_embedder.py` | **全绿是本波回归底线** |

---

## 钉死契约（自 SPEC §1/§2 锁死；30 不得静默改义）

| 项 | 钉死 |
|----|------|
| **入口形态** | `scripts/memory_embedding_backfill.py` CLI（argparse + 退出码语义 · 对齐 `scripts/rag_ingest.py`）；**非** alembic data migration、**非**对外管理端点 |
| **扫描谓词** | `WHERE embedding IS NULL AND status='active' ORDER BY id ASC` keyset 分页（`id > :last_id`）；扫描与回写**双处**带 `status='active'` |
| **页大小 env** | `MEMORY_BACKFILL_BATCH_SIZE`（默认 32 · 对齐 Embedder 批形态）；非法值回退默认 + warning（对齐 `service.py:248-260` 模式） |
| **嵌入文本** | `_fact_embed_text(key, value)` 原样复用（禁止另造序列化） |
| **嵌入执行** | 每页一次 `embedder.embed(texts)` 批调用；同步 Embedder 经 `asyncio.to_thread` 卸载（对齐 `service.py:280-293`）；embedder 显式注入可测，默认 `get_query_embedder()` |
| **回写** | 逐行 `UPDATE … SET embedding=:vec WHERE id=:id AND status='active'`；rowcount=1 → success · 0 → skipped；单行回写失败 → failed（不连坐同页其他行） |
| **前置校验** | 启动即查 `embedder.name` + 试嵌一条断维度 == 1024；不符 → 报错 **exit 2**（不嵌一行）；`SILICONFLOW_API_KEY` 缺失等同 exit 2（`ApiEmbedder` 构造即抛，CLI 翻译）；向量列不存在（migration 未跑）→ 前置探测 → exit 2 |
| **开关** | 回填是显式运维动作，**不挂** `MEMORY_FACTS_VECTOR_RECALL_ENABLED`（该开关管在线路径）；CLI 本身即开关 |
| **幂等/续跑** | 谓词幂等 + keyset 重扫 = 零状态即正确；可选 `MEMORY_BACKFILL_CHECKPOINT` 文件记 `last_id` 仅作跳过加速，损坏/缺失 → 从头重扫（正确性不受影响） |
| **限速** | 批间 `MEMORY_BACKFILL_SLEEP_MS`（默认 200ms）+ 单批超时沿 `ApiEmbedder` timeout=60s；非法值回退默认 + warning |
| **重试** | **回填层零行级重试**（`ApiEmbedder` 内置 3 次指数退避已足；叠加 = 双重放大）；批失败 → 整页记 failed 落 `failed_ids`，重跑自愈；连续 3 页全败 → 判下游不可用提前终止，报告 `status: failed` exit 1 |
| **报告形态** | `reports/memory_embedding_backfill/backfill_<UTC 时间戳>.yaml`：`status`（pass/failed/partial）· `scanned`/`embedded`/`skipped`/`failed` · `failed_ids`（截断上限）· `embedder_name` · `batch_size`/`sleep_ms` · `dry_run` · `elapsed_s` · `recorded_at`；stdout 同步摘要；**计数守恒 `embedded+skipped+failed==scanned`** |
| **干跑** | `--dry-run`：只扫描计数 + 前置校验，**零嵌入零写库**；报告 `dry_run: true` |
| **中断** | 页边界响应 SIGINT/SIGTERM：当前页完成后落部分报告（`status: partial`）再退出；谓词幂等保证续跑正确 |
| **安全** | 复用既有 `SILICONFLOW_API_KEY`（无新凭证面）；报告只记 id/计数/模型名，**不存** fact 明文 value；CLI 无网络监听面 |
| **在线路径** | `_maybe_embed_fact` / `recall_with_vector` / `_fuse_recall` / `continuity.py` 行为**零改动**（D3 只加测试不改实现） |

---

## 范围（同 task 竖切）

- [ ] **D1 · 回填批处理主体**：`scripts/memory_embedding_backfill.py` CLI（扫描 keyset 分页 · `_fact_embed_text` 复用 · 批嵌入线程卸载 · 逐行回写再核 active · 前置校验 exit 2 · `MEMORY_BACKFILL_BATCH_SIZE`）
- [ ] **D2 · 幂等断点续跑 · 限速重试 · 跑批报告**：谓词幂等 · 可选 checkpoint 仅加速 · `MEMORY_BACKFILL_SLEEP_MS` 限速 · 回填层零行级重试 · 连续 3 页全败终止 · yaml 报告 + stdout 摘要 + `--dry-run`
- [ ] **D3 · span `memory_facts_injected` 专门单测**：`tests/test_memory_injection.py` 追加（或同义新文件）· capture-list monkeypatch `continuity.update_current_span_metadata`（对齐 `tests/test_llm_routing.py:176`）· 四分支断言（N / 0 / degraded / 开关关闭零调用）
- [ ] **D4 · 干跑/实跑对账 + 金样两态对照**：同库序 dry-run == 实跑 `scanned` · 实跑后重扫剩余 == `failed` · 复述召回对照走轨见下「金样轨两态裁定」· 变异检验一条
- [ ] **D5 · 文档**：`app/ops/memory/README.md` 增补回填小节（CLI 用法 / env 表 / 报告形态 / 与 `_maybe_embed_fact` 口径同源声明）· `./scripts/graph-compile.sh` 绿（回归保险）

**竖切结论**：D1–D5 同 task 必交；建议 **D3 先行提交**（纯测试、零风险面先落），D1/D2/D4 回填主体随后（承 SPEC R5/§8）；D5 随 30 一并。

### 金样轨两态裁定（D4 验收轨 · 10 落稿定 · SPEC §2 D4 / §7 residual ①③）

| 项 | 裁定 |
|---|---|
| **默认轨** | **态② · FakeEmbedder 集成夹具轨**（CI 可跑）：写入 facts 强制 `embedding=NULL` 模拟存量 → paraphrase 查询回填前 `recall_with_vector` top1 不命中该存量行 / 回填后命中 top1（FakeEmbedder 确定性向量） |
| **默认轨依据** | 2026-09-21 本帽实扫：`git ls-files evals/memory/` = **0 tracked**，金样资产 `evals/memory/golden_v1.yaml` + `run_eval.py` 在未合并分支 `task/memory-golden-eval`（a54b8ed）→ live 金样轨当前不可走 |
| **切换条件** | 若 30 开工前/实施期间 `evals/memory/` 金样资产合入本分支（`git ls-files evals/memory/` 非空且 `run_eval.py` live 模式可用）→ 改走 **态① · live 金样轨**：回填前/后各跑一次 live 金样，复述 top1/top3 不降且报告留档 `reports/memory_embedding_backfill/`（含回填前基线） |
| **写明义务** | 40 验收必须在 invoke 中**写明实际走了哪条轨**；两态都**必须含回填前基线数据**（防假绿 · SPEC §2 D4），禁止只贴回填后结果 |
| **知悉** | 态② 召回提升证据强度弱于真 live 金样（SPEC residual ①），维护者签收 SPEC 时已知悉；本 task **不**承担 `evals/memory/` 建设/合并（SPEC §3 非范围） |

### 非范围

- ❌ 改召回融合算法 / 权重（`_fuse_recall` / `SIM_FLOOR` / `HALF_LIFE_DAYS` / 来源权重不动；调参归 `memory-fusion-weight-tuning` 轨）
- ❌ 改写入闸 / 状态机 / 嵌入文本口径（`should_write` / `_fact_embed_text` / `_maybe_embed_fact` 行为不变）
- ❌ 对外端点 / 管理 API（CLI-only 是 SPEC §4 的显式裁决）
- ❌ 画像 / preference 记忆（`kind='fact'` 以外）
- ❌ 表结构变更（无 alembic 义务；`embedding` 列已 nullable 就位。**若 30 发现必须改表 → 回 10-spec 修订 SPEC**，不得在 task 阶段静默加 migration）
- ❌ checkpoint DB 表 / DLQ 表（一次性运维量级不符；报告 `failed_ids` + 重跑足够）
- ❌ 在线写入路径并发改造（`_maybe_embed_fact` 逐行嵌入保持现状；回填批嵌入不反哺在线路径）
- ❌ `evals/memory/` 金样资产本身的建设/合并（属 `memory-golden-eval` 轨；本 task 只消费，两态验收见上）
- ❌ web / ios

---

## failure_paths

| 触发条件 | 系统行为 | 可重试 | 用户可见 |
|----------|----------|--------|----------|
| `HG-AUDIT-R1` pending 即 30 | **拒开工** | 是 | 是 |
| 嵌入 API 429/5xx/超时 | `ApiEmbedder` 内置指数退避 ≤3 次（`embedder.py:90-110`）；耗尽 → 该页整页记 failed（`failed_ids` 落报告），**回填层不叠加重试**；继续下一页不中断跑批 | Y（重跑自愈） | 是（报告/stdout） |
| 嵌入 API 持续故障（页失败率 100% × N 页） | 连续 3 页全败 → 判下游不可用，提前终止，报告 `status: failed` exit 1（不连打挣扎下游） | Y（人工重跑） | 是（报告 + exit 1） |
| 部分批失败（页内单行回写 DB 错） | 单行独立 UPDATE：失败行记 failed，同页其他行不受影响；计数守恒 `embedded+skipped+failed==scanned` | Y（重跑） | 是（报告） |
| 重复回写（重跑 / 误双跑） | 谓词幂等：已嵌行不再命中扫描；极端竞态（两实例同扫一页）= 同 `embedder.name` 同文本同值覆盖，语义无害；报告观测可发现 | — | 否 |
| 回填期间行被 supersede/revoke/expire | 回写 UPDATE 带 `status='active'` 再核，rowcount=0 → 记 skipped，**不误嵌失效行** | — | 是（报告 skipped 计数） |
| 误嵌 inactive 行（谓词漏 status） | 扫描与回写**双处**带 `status='active'`；单测断言 superseded/revoked/expired 行零嵌入；变异检验删谓词须真 fail | — | 否 |
| 嵌入模型/维度漂移（`RAG_EMBED_MODEL` 被改） | 前置校验 `embedder.name` + 试嵌维度 == 1024，不符 exit 2 零写入（防半库异构向量混库） | — | 是（exit 2 + 报错） |
| `SILICONFLOW_API_KEY` 缺失 | `ApiEmbedder` 构造即抛（`embedder.py:79-81`）→ CLI 翻 exit 2 显式报错，不静默退 local ST | — | 是（exit 2 + 报错） |
| DB 故障（扫描/回写连接断） | 当前页失败记 failed；连接级故障 → 终止跑批 exit 1 + 报告留档；**不伪装成功** | Y（重跑） | 是（报告 + exit 1） |
| 中断（SIGINT/SIGTERM） | 页边界响应中断：当前页完成后落 checkpoint（若启用）+ 部分报告（`status: partial`）再退出；谓词幂等保证续跑正确 | Y | 是（partial 报告） |
| 干跑误当实跑 | `--dry-run` 零写库零嵌入（仅扫描计数 + 前置校验），报告 `dry_run: true` 永不混淆 | — | 是（报告标记） |
| 新 env 非法值 | 回退默认 + warning（`MEMORY_BACKFILL_BATCH_SIZE` / `MEMORY_BACKFILL_SLEEP_MS` / `MEMORY_BACKFILL_CHECKPOINT`，对齐 `service.py:248-260` 模式） | — | 是（warning 日志） |
| 向量列不存在（migration 未跑） | 启动前置探测 `embedding` 列（轻量 SELECT），缺失 → exit 2 显式报错，不静默零回填 | — | 是（exit 2 + 报错） |
| 金样轨未写明 / 对照缺回填前基线 | 40/verify **拒收**（防假绿 · 防两态模糊） | 是 | 否 |
| 无变异检验却宣称谓词有效 | 40/verify **拒收**（不验收空真规则） | 是 | 否 |
| 30 开工前旧测影响面清单未落盘或逐条无处置 | 验收「工程 · 闸前置」项不满足 → **拒收**（B1） | 是 | 否 |

---

## 验收标准

- [ ] 人工闸：`HG-AUDIT-R1` approved 后方可勾选下列码项（HG-GRAPH-MODULES 模块表已建置 approved · 本 task 零图谱变更无新签义务；**若 30 偏离零变更预判 → 回炉补闸**，见闸表）

### D1 · 回填主体（映射 SPEC §6-D1）

- [ ] DB 集成测试：造 active-NULL 行 3 条 + superseded-NULL / revoked-NULL / active-已嵌 各 1 条 → 跑回填 → 断言仅 3 条 active-NULL 被嵌入（FakeEmbedder 注入，`embed()` 收到文本 == `_fact_embed_text(key, value)` 逐条一致），inactive 行 embedding 保持 NULL
- [ ] 回写再核：回填进行中把目标行置 superseded（模拟竞态）→ 该行计 skipped，embedding 保持 NULL
- [ ] 前置校验：FakeEmbedder 维度 ≠ 1024 或 `name` 不符 → exit 2，DB 零写入
- [ ] keyset 分页：batch_size=2 造 5 行 → FakeEmbedder 调用 3 页且每页 id 序严格递增无重复

### D2 · 幂等/续跑/报告（映射 SPEC §6-D2）

- [ ] 幂等：回填跑两次，第二次 `scanned=0 · embedded=0`，FakeEmbedder 零调用
- [ ] 断点续跑：跑至中途模拟中断（第 1 页成功第 2 页抛错终止）→ 重跑 → 全部补齐且第 1 页行不重复嵌入（FakeEmbedder 调用文本不含已嵌行）
- [ ] 部分失败：FakeEmbedder 第 2 页抛 `httpx.HTTPError` → 报告 `embedded=2, failed=2`，`failed_ids` 含第 2 页 id；重跑后 failed 清零
- [ ] 报告形态：yaml 含 status/scanned/embedded/skipped/failed/failed_ids/embedder_name/dry_run/elapsed_s/recorded_at，且 `embedded+skipped+failed==scanned` 守恒断言
- [ ] env 非法值回退 + warning 全覆盖；`--dry-run` 断言 DB 零写、embedder 零调用、报告 `dry_run: true`

### D3 · span 单测（映射 SPEC §6-D3）

- [ ] 有 facts：捕获 `update_current_span_metadata` 收到 `{"memory_facts_injected": N}`，N == 实际注入条数
- [ ] 零 facts：收到 `{"memory_facts_injected": 0}`
- [ ] 召回故障：收到 `{"memory_degraded": True}` 且全程无 `memory_facts_injected`
- [ ] 开关关闭：零 span 调用（与既有逐字节一致断言并存）

### D4 · 对账与金样对照（映射 SPEC §6-D4）

- [ ] 干跑/实跑对账：同库序 dry-run `scanned` == 实跑 `scanned`；实跑后重扫 NULL-active 剩余数 == 报告 `failed`（不等 → status: failed）
- [ ] 复述召回对照：**默认走态② FakeEmbedder 集成夹具轨**（依据与切换条件见「金样轨两态裁定」）——active-NULL 存量行 + FakeEmbedder 确定性向量，paraphrase 查询回填前 `recall_with_vector` top1 不命中该存量行 / 回填后命中 top1；若资产已合入改走态① live 金样（回填前/后复述 top1/top3 不降且报告留档）；**两态都必须含回填前基线**，40 invoke 写明走了哪条
- [ ] 变异检验：把扫描谓词 `status='active'` 删掉一次，确认 D1 的「inactive 行零嵌入」断言**真会 fail**（不验收空真规则）

### 工程（映射 SPEC §6-工程）

- [ ] **闸前置**：30 开工前旧测影响面清单已落盘且逐条有处置（回归/改编/删除理由）——清单见下「旧测影响面清单（B1）」，30 逐条执行处置并在提交说明逐条回填
- [ ] ruff + pytest 绿（本波新测 + `tests/test_memory_*.py` 全量回归）
- [ ] `graph-compile.sh` 绿；图谱零变更裁定与实现形态一致（若实现加了端点/表/事件类型 → 回炉补闸 + 本 SPEC 回炉）
- [ ] `app/ops/memory/README.md` 回填小节 + env 表落盘（CLI 用法 / env 表 / 报告形态 / 与 `_maybe_embed_fact` 口径同源声明）

### 旧测影响面清单（B1 · 2026-09-21 10-task 实扫落盘）

> 扫描口径（真跑）：`grep tests/` `recall_with_vector|_VECTOR_RECALL_SQL` · `update_current_span_metadata|memory_facts_injected|memory_degraded` · `_fact_embed_text|_maybe_embed_fact|_embed_one|_set_embedding|get_query_embedder|FakeEmbedder` · `MEMORY_FACTS_*|MEMORY_BACKFILL*` · `embedding`；全仓 `git ls-files evals/memory/`。本波行为变更源裁定：**在线路径零改动**（service/continuity/embedder/recall 行为不变），变更面 = 新增 `scripts/` CLI + 新增/追加测试 + README；故影响面以**回归**为主，无预期改编。处置三态：**回归**（不受影响，全波次重跑确认）/ **改编**（随本波更新，理由在格内）/ **删除**（须附理由，本清单无）。

| # | 锚点 | 旧测/调用点现状 | 本波影响 | 处置 |
|---|------|----------------|----------|------|
| 1 | `tests/test_memory_vector_p1.py::test_null_embedding_rows_stay_on_deterministic_path`（154-167） | 开关关写入 = NULL 存量行，断言其不进向量 top-M 但确定性 ∪ 带回 | 回填 CLI 不改 `recall_with_vector` 语义；该测夹具行不回填（测试内无人跑 CLI）→ 前提成立 | 回归（若红 = 30 动了在线路径，违约） |
| 2 | `tests/test_memory_vector_p1.py::test_paraphrase_query_recalls_fact_via_vector_path`（119-148）· `test_embedder_failure_degrades_with_marker`（173-186）· `test_write_embed_failure_does_not_block`（189-196）· `test_vector_recall_env_invalid_fallback`（310-319） | P1 向量召回 / 降级标记 / 嵌入失败不阻断写入 / env 非法回退 | 钉死契约保这些行为零改动；FakeEmbedder 类（`:44`）可被本波新测复用注入 | 回归 |
| 3 | `tests/test_memory_injection.py` 全文件（开关关闭逐字节一致 `:32/:43` · 身份缺失跳过 `:64` · 降级不注入 `:148`） | P0 装配注入纯装配测，**无 span 断言** | D3 在本文件（或同义新文件）**追加** span 单测：capture-list 模式对齐 `tests/test_llm_routing.py:176`；既有断言不动 | 回归（既有）+ 新增（D3 四条，非改编） |
| 4 | `tests/test_memory_service_db.py`（DB 集成先例 · `_clean` 夹具清 `mf-test-%` 行） | 状态机/否定性断言真 PG 集成 | 回填 DB 集成新测对齐本文件先例（skipif DB_AVAILABLE · 独立 tenant 前缀自清）；conftest `:166-172` 已保 `embedding vector(1024)` 列，夹具零改编 | 回归（新测复用先例模式，不改本文件） |
| 5 | `tests/test_memory_extract_p1.py`（monkeypatch `recall_with_vector` `:180` · patch `get_query_embedder` `:185` · `test_extract_provider_error_zero_writes` `:384` · 双开关全关逐字节 `:155`） | 抽取链路与装配路径开关语义 | 回填不触抽取链路、不触在线嵌入开关 → 零影响 | 回归 |
| 6 | `tests/test_rag_embedder.py`（`get_query_embedder` 工厂 `:50/:141` · ApiEmbedder 重试/超时） | Embedder 协议与工厂行为 | 回填**消费** Embedder 不改其实现；前置校验只读 `embedder.name` 与维度 | 回归 |
| 7 | `tests/test_llm_routing.py:176` capture-list monkeypatch `update_current_span_metadata` | span 捕获先例 | D3 复用该模式于 continuity 发射点；先例本身不动 | 回归 |
| 8 | tests/ 全仓 grep `memory_facts_injected` | **零断言**（2026-09-21 实扫确认 · P0 遗留未测项①） | D3 首次钉死该 span 三分支断言 | 新增（无旧测可改编） |
| 9 | 全仓 grep `MEMORY_BACKFILL`（tests/ · app/ · scripts/） | **零命中**（2026-09-21 实扫确认） | 三个新 env 无命名冲突；非法值回退 + warning 新测覆盖 | 新增（无旧测可改编） |
| 10 | `scripts/rag_ingest.py` · `reports/qdrant_migrate/reconcile_p1_20260813.yaml` | CLI / 报告形态先例（无 tests/ 直接断言） | 只读参考，不被本波修改 | 回归（参考件不动） |
| 11 | `git ls-files evals/memory/` = 0 tracked（2026-09-21 实扫） | 金样资产在未合并分支 `task/memory-golden-eval`（a54b8ed） | D4 默认走态②夹具轨；切换条件见「金样轨两态裁定」 | 新增（态②夹具）；合入后按裁定切态① |

---

## 依赖

| 依赖 | 说明 |
|------|------|
| SPEC | `docs/spec/memory-embedding-backfill/SPEC-memory-embedding-backfill_v1.md`（signed · HG-SPEC-SIGNOFF=approved 2026-09-21） |
| 上游设计 | `../ops-desk-workspace/docs/08-interview/07_agent-memory-prompt-module-landscape_v1_zh.md`（记忆轨 M2+M6） |
| 编码规范 | `docs/standards/CODING_BACKEND_L2_v1_zh.md` |
| 图谱 | `docs/_tech_graph/l1/01_modules.md`（HG-GRAPH-MODULES 真值 · 2026-09-21 核验） |
| CLI 先例 | `scripts/rag_ingest.py`（独立可执行 · argparse · 退出码语义） |
| 报告形态先例 | `reports/qdrant_migrate/reconcile_p1_20260813.yaml` |
| DB 集成测试先例 | `tests/test_memory_service_db.py` + `tests/conftest.py:166-172`（embedding 列保障） |
| span 捕获先例 | `tests/test_llm_routing.py:176`（capture-list monkeypatch） |
| 同模式闭环先例 | `docs/tasks/done/task_memory_facts_p1.md` · `docs/tasks/done/task_llm_layer_hardening.md`（含 B1 旧测影响面模式） |
| 金样资产（条件依赖） | `evals/memory/golden_v1.yaml` + `run_eval.py` @ `task/memory-golden-eval`（a54b8ed · 未合 master）；合入前走态②夹具轨 |

---

## 给执行帽的必读列表

1. `AGENTS.md`
2. 本 task（钉死契约 · 闸 · 非范围 · B1）
3. SPEC `docs/spec/memory-embedding-backfill/SPEC-memory-embedding-backfill_v1.md`
4. `docs/standards/CODING_BACKEND_L2_v1_zh.md`
5. 代码：`app/ops/memory/service.py`（`_fact_embed_text` / `_embed_one` / `_set_embedding` / `_maybe_embed_fact` / `_VECTOR_RECALL_SQL`）· `app/ops/rag/embedder.py`（协议 + ApiEmbedder 退避）· `app/ops/lg_rag/continuity.py:237-243`（span 发射点）· `app/db/models.py:515-521` · `scripts/rag_ingest.py`
6. 测试：`tests/test_memory_service_db.py` · `tests/test_memory_vector_p1.py` · `tests/test_memory_injection.py` · `tests/test_llm_routing.py:176` · `tests/conftest.py:166-172`
7. `docs/harness/prompts/FRAGMENT_30_gate_verify_v1_zh.md`

---

## 思考轮控制

| 轮 | 结论 | early_stop | reason（early_stop） | residual_risks |
|----|------|------------|----------------------|----------------|
| R0 | SPEC signed（HG-SPEC-SIGNOFF=approved 2026-09-21）；范围 D1–D5 承 SPEC §2 不重开辩论；实扫确认分支正确（`task/memory-embedding-backfill`）与金样资产 0 tracked | no | — | none |
| R1 | 开工闸：HG-TASK-DRAFT=pending（00 代录）· HG-AUDIT-R1=pending（blocks 30 · 本帽不签）· HG-GRAPH-MODULES=approved（2026-09-21 真读 `01_modules.md` 核验模块表已建置）· 零图谱变更 + 回炉补闸条款钉死 · HG-PILOT-OPSDESK-GLAYER=n/a | no | — | 无 |
| R2 | 竖切：D1–D5 同 task；建议 D3 span 单测先行提交（纯测试零风险面），D1/D2/D4 随后，D5 随 30；方案对比继承 SPEC §4 三组裁决（独立 CLI / 小批线程卸载 / 谓词幂等+keyset），不重演 | no | — | 无 |
| R3 | failure_paths 17 条 = SPEC §5 十三 + 过程四（闸 / 金样轨写明 / 变异检验 / B1 闸前置）；核心纪律钉死：回填层零叠加重试 · 回写再核 active · 前置校验防混库 · 谓词幂等 | no | — | 无 |
| R4 | 验收 21 条全否定性断言化逐块映射 SPEC §6（D1×4 / D2×5 / D3×4 / D4×3 / 工程×4 + 人工闸行）；金样两态默认轨=态②夹具（实扫 0 tracked）· 切换条件写明；变异检验「删 `status='active'` 谓词须真 fail」入 D4；B1 实扫 11 条（在线路径零改动 → 回归为主，无预期改编） | no | — | 态②证据强度弱于 live 金样（继承 SPEC residual ①） |
| R5 | 可交 20-task-audit；与 SPEC 差异为零（B1 / 闸行 / 金样轨裁定均为过程化落地，非范围偏差）；HG-AUDIT-R1 待人签（00 依授权代录） | no | — | 回填速率（默认 32/页 + 200ms）未经真实存量校准（继承 SPEC residual ②）；金样合入时序依赖维护者知悉（继承 SPEC residual ③） |

**actual_last_round**：R5 · **early_stop**：no · **residual_risks**：见 R4/R5

### R0 · 问题框定

SPEC 已签收，本 task 只做可执行化拆解：存量行 embedding 覆盖缺口（静默 · 无自愈）+ span 观测断言缺（P0 遗留①）。实扫确认：分支 `task/memory-embedding-backfill` 正确；`evals/memory/` 0 tracked（金样在未合并分支）→ D4 必须两态化且默认夹具轨。

### R1 · 开工闸

HG-TASK-DRAFT / HG-AUDIT-R1 均 pending（00 在维护者「授权00签收所有过程文档」令下于 20 审后代录，本帽不签）；HG-GRAPH-MODULES 真读核验 `01_modules.md`：模块表已建置（bootstrap 2026-07-16 签 · `memory` 行在表 · 签录链完整），本 task 按 SPEC §2 D5 判零图谱变更（不新增路由/表/事件类型 · `scripts/` CLI 无登记义务）→ 无新签义务；**回炉补闸条款**钉死：30 偏离零变更预判（管理端点/checkpoint 表/新事件类型）→ 退回 10-task 补闸 + 图谱如实登记，不得沿用本裁定。

### R2 · 竖切

D1–D5 同 task：回填主体（D1/D2）与对账金样（D4）强耦合（对账即验收回填正确性），拆开会出现半截态；D3 span 单测独立纯测试，建议先行提交降低主体验收噪声（承 SPEC R5/§8）。方案对比不重演，直接继承 SPEC §4 三组裁决。

### R3 · 失败语义

SPEC §5 十三条全收并翻成四列格式；补过程四行：闸未签拒开工 · 金样轨未写明/缺基线拒收（防假绿）· 无变异检验拒收（防空真规则）· B1 未落盘拒收。核心：回填层零叠加重试（ApiEmbedder 已退避 3 次）· 回写再核 active（竞态不误嵌）· 前置校验 exit 2（防异构向量混库）· 谓词幂等保中断/双跑安全 · 报告不存 fact 明文。

### R4 · 可测性

FakeEmbedder 注入消解外网不确定性（CI 可跑）；DB 集成对齐 `test_memory_service_db.py` 先例（真 PG · skipif）；span 三分支用 capture-list monkeypatch（对齐 `test_llm_routing.py:176`）；对账断言计数守恒 + 重扫剩余 == failed；金样两态写明默认轨与切换条件；变异检验一条（删 `status='active'` 谓词 → D1 inactive 零嵌入断言须真 fail）；B1 实扫 11 条落盘（grep 口径在节首），在线路径零改动故全回归/新增、无预期改编。

### R5 · 交接就绪

思考充分可交 20-task-audit；与 SPEC 逐条核对差异为零（验收 21 条 = SPEC §6 十九条 + 闸前置 B1 + 人工闸行，均过程化落地）。残余风险三条继承 SPEC §7 residual 签收知悉项。

---

### 自检结论（40 核验 · 2026-09-21）

**总判定：PASS（验收 21/21 通过 · 0 FAIL · 2 WARN）** · 详见 `docs/harness/invokes/by-task/memory-embedding-backfill/invoke_20260921_40_verify_memory_embedding_backfill.md`。

- **验收逐条计数**：人工闸 1/1 · D1 4/4 · D2 5/5 · D3 4/4 · D4 3/3 · 工程 4/4 = **21/21 PASS**。
- **变异检验 40 亲自复做**：删 `_fetch_page` 扫描谓词 `status='active'` → `test_backfill_embeds_only_active_null_rows` 真 FAIL（scanned 6 != 3，inactive 行被误扫）→ 还原复跑 34 绿 → 工作树净。
- **金样轨实际走轨**：**态② FakeEmbedder 集成夹具轨**（40 复核 `git ls-files evals/memory/` = 0 tracked）· **含回填前基线**（pre top1 确定性行、target 不命中 → 回填后 top1 命中）；证据强度弱于 live 金样（承 SPEC residual ①，签收知悉）。
- **基线红核验**：`git worktree` @ origin/master 1bb24a8（补齐同 `.env`）复跑 = 1155 passed / 3 failed / 1 skipped，3 红与分支完全同三条（chat_ws×2 + capability proxy×1）→ 基线环境红坐实；总数差 19 = 新测 19 全绿。
- **B1 逐条处置回填核验**：30 invoke 11 条在档（回归×8 / 新增×3 · 无删除无改编），40 抽查 #8/#11 成立。
- **WARN×2**：W1 态②证据强度（知悉项）；W2 worktree 对照须注意未跟踪 `.env` 不分发（首次对照曾多出 1 条环境红，补齐后消解）。

---

## 修订

| 日期 | 说明 |
|------|------|
| 2026-09-21 | 40 核验 **PASS（21/21 · 0 FAIL · 2 WARN）**：全量 pytest 1174 passed/3 failed（worktree @ origin/master 对照坐实基线红）· ruff 67=基线零新增 · graph-compile 绿零图谱变更 · 变异检验 40 复做真 fail 还原绿 · 金样走态②夹具轨含回填前基线 · B1 11 条处置核验成立（invoke_20260921_40_verify） |
| 2026-09-21 | 10-task 落稿 · R0–R5 全轮无 early_stop · 验收 21 条逐块映射 SPEC §6 零差异 · B1 旧测影响面 11 条实扫落盘 · 金样两态裁定：默认态② FakeEmbedder 夹具轨（`git ls-files evals/memory/`=0 tracked），资产合入切态① · HG-TASK-DRAFT=pending · HG-AUDIT-R1=pending → 30 拒开工 · HG-GRAPH-MODULES=approved（模块表已建置 · 零图谱变更 + 回炉补闸条款）· HG-PILOT-OPSDESK-GLAYER=n/a |
