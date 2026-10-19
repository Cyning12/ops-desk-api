# Task：api-embedder-internal-batching（ApiEmbedder 内部批切：大体量 ingest 全量单请求超时收口 · 30 落码棒）

> **状态**：done（2026-10-19 CLOSE · PR #278 MERGED squash 056d874 · TC-EB-1~5 全 PASS（红测先行 · F3a 1200 chunks 10 批全 200 OK · 70.9 chunks/s · 8648 零扰动）· 归档 done/）
> **类型**：功能缺口收口（bugfix/robustness 性质 · **有码改 · 30 棒分支 PR 流** · 含图谱闸评估）
> **上游**：[`close_local_rag_knowledge_rebuild_20261018.md`](../close/close_local_rag_knowledge_rebuild_20261018.md) §三.2 偏差照登：ApiEmbedder 无内部批切，ingest.py:225 全量单请求 ~8.6k 文本超时（探测实证 API 单批上限≈500），40 棒靠 `--limit 75` 分批 25 步 248s 绕开；§五 遗留移交「ApiEmbedder 内部批切另立 task」；维护者 2026-10-19（会话「全做」）选定推进
> **分支**：`task/api-embedder-internal-batching`（30 开工时自 master 切出 · 本帽零 git 操作）

---

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `api_embedder_internal_batching` |
| **git_branch** | `task/api-embedder-internal-batching` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | 红测先行：30 先落批切新测（多批请求/跨批保序/配置解析/失败纪律）见红再实现；硬闸 = PR CI pytest 绿 + 本地 `.venv/bin/python -m pytest tests -q` 红集 ⊆ 基线红集零新增（基线须 30 开工亲跑复核留档，参照 2026-10-18 master c956d87 录 19 红） |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `G-L1`（预期 · app/ops/rag 面模块内行为变更，无新模块/路由/表/事件；预期仅 `docs/_tech_graph/l1/01_modules.md` rag 行备注一条，30 实判可降 none 并留理由） |
| **graph_delta** | `docs/_tech_graph/l1/01_modules.md`（rag 行备注：ApiEmbedder 内部批切 + env `RAG_EMBED_API_BATCH_SIZE`） |
| **graph_delta_note** | 改动为 rag 模块内部 embedder 请求形态（单请求→内部多批），拓扑/依赖边/对外契约零变化；按仓内先例（session-summary-fallback 等）落 rag 行备注级，不新增一级模块、不增 implementedBy；若 30 实判行备注亦不必要须改 `graph_delta=none` 并填理由 |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | embedder 内部健壮性收口不涉 WikiTrack 正文真值；裁定与实证留痕于 invoke 与本档修订记录即可 |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,30,40` |
| **invoke_retention_profile** | `default`（10 起草 + 30 落码与逐条裁定 + 40 验收实证；20 按维护者授权取舍） |
| **experience_capture** | `recommended` |
| **kpi_aggregator** | `n/a` |
| **orchestration** | 10 落稿 → 20 R1（按维护者授权）→ 维护者签闸 → 30 分支落码（红测先行 → F1 批切实现 → F2 回归对拍 → 图谱闸评估落备注）→ 40 验收复跑 + F3 大批量实证 → PR → CLOSE |
| **freeze_id** | 无 |
| **related_tasks** | [`task_local_rag_knowledge_rebuild.md`](../done/task_local_rag_knowledge_rebuild.md)（直接上游 · 超时实证母体）· [`close_local_rag_knowledge_rebuild_20261018.md`](../close/close_local_rag_knowledge_rebuild_20261018.md)（§三.2 批切建议原文 · §五 遗留移交）· [`task_ruff_baseline_cleanup.md`](../done/task_ruff_baseline_cleanup.md)（30 落码棒 PR 流与 pytest 红集基线口径先例） |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | approved | 20, 30 | 2026-10-19 维护者「全做」授权 + 授权链（m00238/m01101）00 代录 · R1 task_api_embedder_internal_batching_audit_R1_20261019.md 通过 |
| HG-AUDIT-R1 | approved | 30 | 授权链 00 代录 · 20 R1 通过零阻塞 · **签注三裁定（维护者「全做」采纳推荐默认）**：默认批大小=**128** · 部分批失败纪律=**fail-fast**（skip-and-DLQ 不采纳）· **F3b 端到端写面复跑=不授权**（F3a 只读 ≥1000 取样足证） |
| HG-GRAPH-MODULES | approved | 30 | 授权链 00 代录 · `graph_change_layer=G-L1` 预判 rag 行备注级 · 30 实判随交付签录 · 真值 [`docs/_tech_graph/l1/01_modules.md`](../../_tech_graph/l1/01_modules.md)）；若 30 实判 none 须签注确认降档理由 |

> 关联闸照登：HG-PROD-READONLY-ACCESS 仍 pending（仅阻生产侧）；**本 task 零涉生产**（本地 compose 口径），不受其阻、也不消解之。

---

## 背景与目标

本地 RAG 知识库重建（PR #276 · 2026-10-18 CLOSE）40 实证：`ApiEmbedder.embed()` 把全量 texts 打进**单个** `/embeddings` 请求（embedder.py:87 `payload = {"model": self.name, "input": texts}`），ingest 管线在 `app/ops/rag/ingest.py:225` 一次喂入全量 pending chunks——~8.6k 文本单请求超时，探测实证 API 单批上限≈500 chunks。40 棒靠 `--limit 75` 分批 25 步（248s · 利用 content_hash 水位幂等跳过）零落码绕开，CLOSE 档明记「内部批切改码建议另立 task」。本 task 收口该缺口：ApiEmbedder 内部批切（批量可配 · 默认值钉死 · 失败纪律明确 · 台账留痕），既有小规模行为逐字节等价，大批量单命令不再超时。

### 实证锚点（10 亲跑亲读 2026-10-19 · master `4a5e755` · 30 必读）

| 主题 | 命令 / 路径 · 锚点 | 现状（亲跑实录） |
|------|---------------------|-------------------|
| 全量单请求面 | `app/ops/rag/ingest.py:225`（亲读 :179-304） | `vectors = embedder.embed([p[2] for p in pending])`——变化集全量 chunks 一次调用；前置维度断言 1024 不符即停（:226-230）；消费侧 `zip(pending, vectors, strict=True)`（:236）**保序强依赖** |
| ApiEmbedder 实现 | `app/ops/rag/embedder.py:64-110`（亲读全文 172 行） | `embed()` 单 payload（:87）· httpx.post timeout=60（:92-94）· 响应按 `index` 排序返回（:97 · 已有保序先例）· HTTP 失败重试 3 次指数退避后 raise（:90-110 · **fail-fast 不回落本地 ST**，与缺 key raise :78-81 同哲学）；构造签名 `(model, base_url, api_key, max_retries=3)`（:67-73） |
| env 解析先例 | `app/ops/rag/embedder.py:113-125` | `embed_backend()`：env 读取 strip/lower · 空/未设→默认 · 非法值 warning + 回退默认——**新 env 解析承此先例形态** |
| 超时实证原文 | `docs/tasks/close/close_local_rag_knowledge_rebuild_20261018.md` §三.2 | 「ApiEmbedder 无内部批切：ingest.py:225 全量单请求 ~8.6k 文本超时（探测实证 API 单批上限≈500）→ 分批 --limit 75 步递增（25/25 步 · 248s · 利用 content_hash 水位幂等跳过）。**内部批切改码建议另立 task**。」§三.4：总 17077 chunks ≈ 6.0M tokens · **速率 ~34 chunks/s** |
| safe zone 证据 | `docs/harness/invokes/by-task/local-rag-knowledge-rebuild/evidence/f3_incident_tombstone.md:7` | 「step size 75/source/run (~150 units ~465 chunks < n=500 proven API safe zone)」——单请求 ~465 chunks 实证安全；40 invoke :50 明记「内部批切属改码，FP-8 纪律未落，建议另立 task」 |
| --limit 绕开面 | `scripts/rag_ingest.py`（亲读 88 行） | docstring :12-14 历史全量形态（两 docs-root）；`--limit` :50（每类源最多处理条数 · 40 棒绕开手段）；`--batch-size` :51 **仅传 SentenceTransformerEmbedder**（:63），ApiEmbedder 构造无任何批参数（:65）——批切缺口正在此 |
| 既有测试面 | `tests/test_rag_embedder.py`（亲读 215 行） | **9 测**：embed_backend 默认/非法回退 · model 名默认 · 查询侧工厂硅基路径不构造 ST · **ApiEmbedder 乱序 index 保序 + 维数**（:79-107 · 批切后须仍绿）· 缺 key raise · HTTP 失败重试后 raise 无 ST 回落 · local stub · rag_nodes/lc_evidence 两 wiring（单条查询 embed 调用形态） |
| 水位桩测 | `tests/test_check_vector_waterline.py` | **13 桩测**（grep 实测 def test_×13）；本 task 零触碰水位脚本但列入回归闸 |
| 回归亲跑 | `.venv/bin/python -m pytest tests/test_rag_embedder.py tests/test_check_vector_waterline.py -q` | **22 passed（9+13）· 2026-10-19 master 4a5e755 亲跑**——批切前绿基线 |
| 本地知识库背景 | `docker exec ops-desk-api-db-1 psql -c 'select count(*) from ops_knowledge_chunks'` | **8648**（2026-10-19 亲跑 · 与 CLOSE 三对照一致）——F3 大批量实证的真实语料池（只读取样） |
| pytest 全量基线 | 承 task_ruff_baseline_cleanup 10 invoke（2026-10-18 master c956d87） | 本地 19 failed / 1828 passed / 1 skipped（环境依赖面红集）；**本 task 以零新增红为闸**，30 开工须亲跑复核当前基线留档 |
| 图谱 rag 行 | `docs/_tech_graph/l1/01_modules.md:31`（亲读） | rag 行现状备注含「查询 embed 默认 SiliconFlow HTTP（`RAG_EMBED_BACKEND`）」——本 task 预期同行追加批切备注，形态承 session-summary-fallback 等行内先例 |

### 目标

F1 ApiEmbedder 内部批切（裁切点放 embedder 内部 · Embedder Protocol 与 ingest.py:225 调用面零改动 · 批量 env/参数可配默认值钉死 · 逐批复用既有重试 · 台账留痕）→ F2 回归闸（红测先行 · 既有 9+13 测零改动全绿 · 小规模请求逐字节等价 · pytest 零新增红）→ F3 大批量实证（≥1000 chunks 单 embed 调用链不超时 · 本地 8648 语料为背景只读取样）。终态：大体量 ingest 不再需要 `--limit` 分批绕开。

---

## 范围

- **F1 · ApiEmbedder 内部批切（30 落码 · 唯一改码面 `app/ops/rag/embedder.py` + `tests/test_rag_embedder.py`）**：
  - `embed()` 内部将 texts 切成 ≤batch_size 小批逐批 POST，各批响应按 `index` 排序后**跨批保序拼接**（承 :97 既有保序先例）；`Embedder` Protocol 签名不变，ingest.py:225 与查询侧 `get_query_embedder()` 零改动。
  - **批量可配**：构造参数 `batch_size: int | None = None` → env `RAG_EMBED_API_BATCH_SIZE`（strip/int 解析 · 未设/非法/≤0 回退默认 + warning · 承 embed_backend :113-125 先例）→ **默认值钉死 128**（建议值 · 依据：safe zone ≈500 · 实测 ~34 chunks/s → 128 ≈ 4s/批 << timeout 60s · 15× 余量；维护者签闸可改判 64/256，签注为准）。
  - **失败批纪律（建议 fail-fast · 裁定口留维护者）**：逐批复用既有 max_retries 指数退避；批级重试耗尽即 raise 整单失败——不缓存部分批结果、不重排、不跳过（重跑整体重来幂等安全 · 与缺 key 不回落 ST 同一 fail-fast 哲学）；skip-and-DLQ 形态**不默认采纳**，须维护者签闸显式改判并补配套断言。
  - **台账**：每批 logger.info（批序 i/N · chunks 数 · 批耗时）+ 调用结束汇总（总 chunks · 批数 · 总耗时 · 均速 chunks/s）；token 维度台账由 40 报告以既有 BgeM3TokenCounter 口径估算（embedder 内不引 tokenizer 依赖）。
  - **超时/重试默认不动**：timeout=60（:93）、max_retries=3 保持现状；若 F3 实证须调，回抛维护者裁定，不顺手改。
- **F2 · 回归闸（红测先行）**：
  - 30 先落新测见红再实现：多批切分（>batch_size 输入产生 ceil(N/batch_size) 次 POST · 各批 input 切片正确）· 跨批保序（各批乱序 index 响应拼接后全序正确）· 配置解析（env 生效/非法回退默认+warning · 构造参数优先于 env）· 失败纪律（中间批重试耗尽 → 整单 raise · 已成功批次结果被丢弃不部分返回）。
  - 既有 `tests/test_rag_embedder.py` 9 测 + `tests/test_check_vector_waterline.py` 13 桩测**零改动全绿**；本地全量 pytest 红集 ⊆ 基线红集零新增。
  - **小规模等价断言**：输入 ≤ batch_size（含查询侧单条）时请求次数=1 且 payload 与批切前逐字节等价（`{"model","input":texts}` 原序）· 响应处理同为按 index 排序——默认批切开启下小规模行为不漂移。
- **F3 · 大批量实证（40 棒 · 本地 compose 口径）**：
  - **F3a 只读实证（默认形态）**：一次性 python 片段（全文留档 40 invoke · **不落 scripts/ 新文件**，避免扩散）从 PG `ops_knowledge_chunks` 只读取样 ≥1000 条真实 content 直调 `ApiEmbedder().embed()`：断言全成功 · 返回数==输入数 · 维数全 1024 · 批次数==ceil(N/batch_size)（日志台账佐证）· 保序抽对（同源文本重嵌向量一致/近似）；总耗时/均速台账留档。
  - **F3b 端到端写面复跑（可选 · 须维护者签闸授权）**：若要实证 ingest 全链去 `--limit`，裁定一个受控写面形态（如删小批单元触发重嵌）并**以水位 verdict=match · DLQ=0 收尾**；未授权即不执行，不假绿。
  - F3 仍超时/失败：照登实证回抛维护者裁定调小默认批或拆步，**不凑数不硬闯**。
- **F4 · 图谱闸评估与留档**：30 实判 `docs/_tech_graph/l1/01_modules.md` rag 行备注（建议措辞：「ApiEmbedder 内部批切 `RAG_EMBED_API_BATCH_SIZE` 默认 128 · 失败 fail-fast」）；实判 none 则回填 graph_delta=none + 理由。30/40 invoke 按 required_invoke_hats 落盘。

## 非范围

- **不改 embedding 模型/提供商/维数**：model=BAAI/bge-m3 · SiliconFlow base · dim=1024 全钉死；换模型=重建表+全量重灌（契约 Q3），另 task。
- **不改 ingest 编排语义**：content_hash 水位（ingest.py:186-191）· 清洗/切分/前缀注入（:204-222）· 整组替换逐单元 commit（:240-284）· 墓碑对账删（:292-302）· 影子写/DLQ 面（shadow_write.py）**零 diff**；ingest.py 预期整个零 diff（裁切点在 embedder 内部）。
- **SentenceTransformerEmbedder 不动**（已有 encode batch_size 面 :49-61）；`--embedder st` 路径零变化。
- **生产环境任何访问**（HG-PROD-READONLY-ACCESS 仍 pending · 不消解）。
- **timeout=60 / max_retries=3 默认值变更**（F1 不动；F3 实证要求调即回抛裁定）。
- **查询侧行为语义**：查询为单条 embed，批切不改变其请求形态；`get_query_embedder()` 工厂/缓存面零改动。
- **skip-and-DLQ 部分批失败形态**（非默认 · 须维护者显式签注改判才进范围）。
- `scripts/rag_ingest.py` 改动（`--limit` 面保留作运维工具 · 不删不改）；不新增 scripts/ 文件（F3a 用一次性片段留档）；图谱/Wiki 除 F4 rag 行备注外零改动；alembic/、docker-compose.yml、CI workflow 零改动。

---

## 失败路径

| 触发条件 | 系统行为 | 可重试 | 用户可见 |
|----------|----------|--------|----------|
| FP-1 闸 pending 即 30 改码 | GATE_VERIFY **拒开工**（真值在本档人工闸表；HG-AUDIT-R1 / HG-GRAPH-MODULES pending → 30 拒改码） | 是 | — |
| FP-2 批切引入顺序/去重偏差 | 红测先行钉死：跨批保序拼接断言（各批乱序 index 响应 → 全序正确）· 输入数==返回数 · zip strict 下游零漂移；断言红即修到绿，禁交付带偏差实现 | 是 | 30 invoke |
| FP-3 部分批失败（中间批重试耗尽） | 默认 **fail-fast**：整单 raise · 部分批结果丢弃不部分返回 · 不缓存不重排（重跑整单幂等安全）；ingest 侧已写单元 PG 已 commit 不丢（逐单元提交崩溃可续 · ingest.py:232）；**失败照登不假绿**；欲改 skip-and-DLQ 须维护者签注改判 | 是 | 30/40 invoke + stderr |
| FP-4 env 默认值/向后兼容争议 | `RAG_EMBED_API_BATCH_SIZE` 未设=默认 128 钉死（签闸可改判）；非法/≤0 → warning + 回退默认（承 embed_backend 先例）；向后兼容口径：≤128 条输入请求形态逐字节不变，>128 条由「超时失败」变「分批成功」=修 bug 非破坏——评估写入 30 invoke | 是 | 30 invoke + 图谱备注 |
| FP-5 回归破（既有 9+13 测红 / 小规模 payload 漂移 / pytest 新增红） | 修到等价：既有测零改动全绿 · 小规模逐字节对拍通过 · 全量红集 ⊆ 基线；环境抖动红须与基线逐名对拍留档（承 ruff task FP-6 口径） | 是 | 30/40 invoke |
| FP-6 F3 大批量实证仍超时/失败 | 照登实证（批大小/批数/失败批错误全文）；回抛维护者裁定调小默认批或分步；**不凑数、不硬闯、不私自调 timeout** | 是 | 40 invoke + 报告 |
| FP-7 顺手改 ingest 编排/墓碑/影子写/scripts 冲动 | **STOP**：ingest.py/shadow_write.py/scripts/ 任何 diff 即越界；退回维护者裁定扩范围或另立 task | — | 30 invoke |
| FP-8 台账缺失（无批数/耗时/速率记录即报成功） | 不假绿：F1 台账日志 + F3 台账留档为验收硬项，缺即不勾 TC | 是 | 40 invoke |

---

## 验收标准

- [ ] **TC-EB-1（红测先行 · F2）**：批切新测先于实现落盘见红（30 invoke 留红证）→ 实现后全绿：多批切分（请求次数==ceil(N/batch_size) · 各批 input 切片正确）· 跨批保序 · env/构造参数配置解析（非法回退默认+warning）· 失败批 fail-fast 整单 raise。
- [ ] **TC-EB-2（机断 · 回归零 diff）**：`tests/test_rag_embedder.py` 既有 9 测 + `tests/test_check_vector_waterline.py` 13 桩测**零改动全绿**；本地全量 `pytest tests -q` 红集 ⊆ 基线红集零新增（基线 30 开工亲跑留档）；PR CI pytest 绿。
- [ ] **TC-EB-3（机断 · 小规模等价）**：输入 ≤ batch_size（含单条查询形态）时 POST 次数==1 且 payload 与批切前逐字节等价（自动化断言）；`SentenceTransformerEmbedder` 与 ingest.py、shadow_write.py、scripts/ 零 diff。
- [ ] **TC-EB-4（机断 · 门禁）**：`ruff check app tests` 0 errors · `npx spec-wave task lint --file` 本档 PASS · spec-wave verify EXIT=0 · `git diff --name-only master...HEAD` 白名单（`app/ops/rag/embedder.py` · `tests/test_rag_embedder.py` · `docs/_tech_graph/l1/01_modules.md`（若 F4 实判落备注）· docs/tasks · docs/harness/invokes）。
- [ ] **TC-EB-5（40 实证 · F3）**：≥1000 chunks 单次 `embed()` 调用链不超时全成功（返回数==输入数 · 维数全 1024 · 批次数==ceil(N/batch_size) 台账佐证 · 保序抽对）；总耗时/均速留档；本地 8648 知识库零扰动（实证后水位复跑 verdict=match · DLQ=0）；F3b 若授权执行则以水位 match 收尾，未授权则明记未执行不勾假绿。

## 依赖

- 上游实证：`docs/tasks/close/close_local_rag_knowledge_rebuild_20261018.md` §三.2/§五 · `docs/harness/invokes/by-task/local-rag-knowledge-rebuild/`（40 invoke + evidence/f3_incident_tombstone.md:7 safe zone）。
- 改码面真值：`app/ops/rag/embedder.py:64-110`（ApiEmbedder）· :113-125（env 解析先例）· `app/ops/rag/ingest.py:225`（消费面 · 保序强依赖 :236）。
- 编码规范：`docs/standards/CODING_BACKEND_L2_v1_zh.md`。
- 图谱：`docs/_tech_graph/l1/01_modules.md:31`（rag 行）。
- 闸与流程：`docs/harness/prompts/FRAGMENT_30_gate_verify_v1_zh.md`（GATE_VERIFY 形状 · 本 task 阻塞面 = 30）。
- 30 PR 流与 pytest 红集基线口径先例：`docs/tasks/done/task_ruff_baseline_cleanup.md`。

## 给执行帽的必读列表

1. 本 task 全文（实证锚点表 · 非范围六条 · FP-1~8 · 闸表 · 签注裁定口：默认批大小 / 失败纪律 / F3b 授权）。
2. `app/ops/rag/embedder.py` 全文（172 行 · 重点 :64-125）与 `app/ops/rag/ingest.py:179-304`（:225 消费面 · :236 zip strict 保序依赖）。
3. `tests/test_rag_embedder.py` 全文（9 测 · :79-107 保序/维数测为批切最直接回归面）。
4. `docs/tasks/close/close_local_rag_knowledge_rebuild_20261018.md` §三.2 偏差原文与 §五 移交 · `docs/harness/invokes/by-task/local-rag-knowledge-rebuild/invoke_20261018_40_rebuild.md`（超时与分批绕开实录）。
5. `docs/_tech_graph/l1/01_modules.md:31` rag 行（F4 备注落点 · 行内先例措辞参照）。
6. 10 invoke `docs/harness/invokes/by-task/api-embedder-internal-batching/invoke_20261019_10_task_draft.md`（亲跑实证与参数化建议推导）。

## 思考轮控制

| 轮 | 结论 | early_stop | reason（early_stop） | residual_risks |
|---|------|------------|----------------------|----------------|
| R0 | 框定：ApiEmbedder 无内部批切 → ingest 大体量全量单请求超时（上限≈500）；bugfix/robustness 30 落码棒 PR 流 | false | — | 闸未签 |
| R1 | 证据：embedder.py:87 单 payload · ingest.py:225 全量调用+zip strict 保序依赖 · safe zone ~465<500 · 速率 ~34 chunks/s · 9+13 测 22 passed 亲跑 · PG 8648 亲跑 · env 解析先例 :113-125 全部亲读亲跑 | false | — | pytest 全量基线承 ruff task 19 红（2026-10-18），30 开工须复核当前值 |
| R2 | 方案：裁切点 embedder 内部（Protocol/ingest 零改动 · 消费方自动受益）→ batch_size 构造参数+env 默认 128 → 逐批复用既有重试 fail-fast → 批级台账 → 红测先行 → F3 只读 ≥1000 实证 | false | — | 默认批大小为建议值，签闸可改判 |
| R3 | 反例：顺序/去重偏差（对策：跨批保序红测+zip strict）· 部分批失败部分返回（对策：fail-fast 不缓存）· env 非法值（对策：回退默认+warning 承先例）· 顺手改 ingest/scripts（对策：FP-7 STOP+diff 白名单） | false | — | skip-and-DLQ 形态有运维价值但超既有降级面，留维护者裁定不进默认 |
| R4 | 验收：TC-EB-1..5 全机断或可断言（红测先行红证/既有测零改动/逐字节对拍/diff 白名单/≥1000 实证批数台账） | false | — | F3b 写面复跑未授权时 TC-EB-5 仅以 F3a 只读口径验收 |
| R5 | 收口：实证齐备、方案与反例闭合、验收可机断；草稿交维护者签闸（三闸全 pending） | true | 上游 CLOSE 档已量化缺口与 safe zone，本帽亲跑复核全中，再轮无新信息 | 闸未签；默认批大小/失败纪律/F3b 三裁定口待签注 |

**actual_last_round**：R5（early_stop）

### R0 · 问题框定

ApiEmbedder 全量单请求在大体量 ingest（~8.6k chunks）下超时，实证 API 单批上限≈500；40 棒 `--limit 75` 分批绕开是运维手段非修复。缺口本质 = embedder 内部缺批切，修复裁切点放 embedder 内部则 ingest/查询侧全部消费方零改动受益。

### R1 · 证据收集

2026-10-19 master 4a5e755 亲读亲跑：embedder.py 全文 172 行（单 payload :87 · timeout=60 :93 · index 排序保序 :97 · 重试 3 次 raise :90-110 · 缺 key fail-fast :78-81 · env 解析先例 :113-125）；ingest.py:225 全量调用 + :236 `zip(pending, vectors, strict=True)` 保序强依赖；CLOSE 档 §三.2 超时实录与 §三.4 速率 ~34 chunks/s；f3_incident_tombstone.md:7「~465 chunks < n=500 proven API safe zone」；scripts/rag_ingest.py :51,:63-65 `--batch-size` 仅通 ST 路、ApiEmbedder 无批参数；tests/test_rag_embedder.py 9 测 + waterline 13 桩测亲跑 22 passed；PG ops_knowledge_chunks=8648 亲跑。

### R2 · 方案生成

F1：`embed()` 内部切批 ≤batch_size 逐批 POST、各批按 index 排序后跨批保序拼接；`batch_size` 构造参数 → env `RAG_EMBED_API_BATCH_SIZE` → 默认 128（safe zone 500 的 1/4 · ~4s/批 << 60s timeout）；逐批复用既有重试，批级耗尽 fail-fast raise；批级+汇总 logger.info 台账。F2：红测先行（切批/保序/配置/失败四组）+ 既有 9+13 测零改动 + 小规模逐字节等价 + pytest 零新增红。F3：40 只读取样 ≥1000 真实 chunks 直调 embed 实证不超时 + 台账；F3b 端到端写面复跑留维护者授权。F4：rag 行备注级图谱留痕。

### R3 · 反例与边界

最大风险一是跨批顺序/去重偏差污染下游 zip strict 写入（对策：乱序 index 跨批保序红测钉死）；二是部分批失败后部分返回造成静默缺向量（对策：fail-fast 整单 raise 不缓存部分结果，与缺 key 不回落 ST 同哲学）；三是新 env 引入兼容面漂移（对策：未设=默认钉死 · 非法回退+warning · ≤128 请求形态逐字节不变的兼容评估写进 30 invoke）；四是顺手改 ingest/scripts 扩范围（对策：FP-7 STOP + TC-EB-4 diff 白名单）。skip-and-DLQ 与既有降级面（影子写 DLQ 不回滚不阻塞）哲学不同，不默认采纳，裁定口留维护者。

### R4 · 验收/可测性

五条 TC 全部可机断或可断言：红测先行红证留档、既有测零改动全绿、小规模 payload 逐字节对拍、ruff/lint/verify/diff 白名单、≥1000 实证返回数/维数/批次数/保序抽对+台账。F3b 未授权时 TC-EB-5 以 F3a 只读口径验收并明记，不假绿。

### R5 · 收口

上游 CLOSE 档已量化缺口（上限≈500 · 速率 34/s · 8648 背景），本帽亲跑复核全中；方案（embedder 内部裁切 · 默认 128 · fail-fast · 台账）与反例闭合。三裁定口（默认批大小取值 / 部分批失败纪律 / F3b 写面授权）写明默认建议留维护者签闸改判。HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 全 pending 待签。

### 自检结论（执行者）

30 落码棒回填（2026-10-19 · 分支 task/api-embedder-internal-batching · 详录 invoke_20261019_30_impl.md）：TC-EB-1~5 全勾——红测先行 RED（5 failed TypeError）→ 实现 → GREEN（28 passed · 既有 9+13 测零改动）；全量 pytest 19 failed/1834 passed 红集与基线逐名一致零新增；小规模 payload 逐字节等价自动化断言通过；ruff 0 errors · task lint PASS · verify EXIT=0 · diff 白名单全中；F3a 只读实证 1200 chunks 单 embed() 链 10 批 16.9s 不超时 · 返回数/维数/批数/保序抽对全中 · 水位复跑 verdict=match DLQ=0 零扰动；F3b 签注不授权未执行。图谱闸实判：G-L1 rag 行备注已落（01_modules.md:31）· graph-compile EXIT=0。偏差四条照登 30 invoke §九（venv 复用 · F3a 判据修正 · 代理 env 注记 · 构造参数非法回退语义裁定口）。

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-10-19 | 10 落稿：承 close_local_rag_knowledge_rebuild_20261018 §三.2/§五 批切建议 · 实证锚点亲跑复核（master 4a5e755 · 22 passed · PG 8648）· 三闸 pending 待维护者签 |
| 2026-10-19 | 维护者签闸（授权链 00 代录）：三闸 approved · 签注三裁定（默认批=128 · fail-fast · F3b 不授权）· R1 通过零阻塞 |
| 2026-10-19 | 30 落码回填：红测先行→实现→F3a 实证全绿（TC-EB-1~5 逐项见 自检结论 + invoke_20261019_30_impl.md）· 图谱闸实判 G-L1 rag 行备注已落 · PR 流待并 |
| 2026-10-19 | 50 CLOSE（goal-eb568703 承授权链合并）：PR #278 squash 056d874 已并 · 归档 done/ · 状态行 CLOSED · README 登记 · invoke_20261019_50_close.md（批量目录 close_batch_20261019）· 无遗留开账项 |
