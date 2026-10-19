# Invoke：api-embedder-internal-batching · 10 任务起草（2026-10-19）

- **hat**：10-task · **task**：docs/tasks/active/task_api_embedder_internal_batching.md（draft · 三闸 pending）
- **上游**：close_local_rag_knowledge_rebuild_20261018.md §三.2 批切建议 + §五 遗留移交 · 维护者 2026-10-19（会话「全做」）选定推进
- **base**：master 4a5e755（只读 git 查询 · 本帽零 git 操作 · 工作树既有 M docs/arch-browser/dist/site-data.json + ?? backups/ 非本帽产物）

## 一、亲读亲跑实录（起草前真读复核）

| 锚点 | 实录 |
|------|------|
| close 档偏差节 | §三.2 原文：「ApiEmbedder 无内部批切：ingest.py:225 全量单请求 ~8.6k 文本超时（探测实证 API 单批上限≈500）→ 分批 --limit 75 步递增（25/25 步 · 248s · 利用 content_hash 水位幂等跳过）。内部批切改码建议另立 task。」§三.4：17077 chunks ≈ 6.0M tokens · 速率 ~34 chunks/s |
| ingest.py:225 附近 | 亲读 :179-304：:225 `vectors = embedder.embed([p[2] for p in pending])` 全量单调用；:236 `zip(pending, vectors, strict=True)` 保序强依赖；:226-230 维数 1024 断言；:240-284 整组替换逐单元 commit；:292-302 墓碑对账 |
| embedder.py 全文 172 行 | ApiEmbedder :64-110：:87 单 payload `{"model","input":texts}` · :92-94 httpx timeout=60 · :97 响应按 index 排序（保序先例）· :90-110 重试 3 次指数退避后 raise（fail-fast 不回落 ST · 同 :78-81 缺 key raise 哲学）；env 解析先例 embed_backend :113-125（strip/lower · 非法 warning+回退默认）；构造 :67-73 无批参数 |
| scripts/rag_ingest.py 全文 88 行 | :50 `--limit`（40 绕开手段）· :51 `--batch-size` 仅传 SentenceTransformerEmbedder（:63）· :65 `ApiEmbedder()` 无批参数——缺口坐标钉死 |
| PR #276 40 invoke | invoke_20261018_40_rebuild.md :11（两次环境级失败实录）· :50「--embedder api 无内部批切为既存管线特性；内部批切属改码，FP-8 纪律未落，建议另立 task」；evidence/f3_incident_tombstone.md:7「~465 chunks < n=500 proven API safe zone」 |
| tests 亲跑 | `.venv/bin/python -m pytest tests/test_rag_embedder.py tests/test_check_vector_waterline.py -q` → **22 passed in 5.61s**（9 embedder + 13 waterline 桩测 · 批切前绿基线） |
| PG 背景亲跑 | `docker exec ops-desk-api-db-1 psql -t -c 'select count(*) from ops_knowledge_chunks'` → **8648**（与 CLOSE 三对照一致 · F3 语料池） |
| 图谱 | docs/_tech_graph/l1/01_modules.md:31 rag 行亲读（行内备注先例形态确认 · F4 落点） |
| pytest 全量基线 | 承 task_ruff_baseline_cleanup 10 invoke（2026-10-18 master c956d87：19 failed/1828 passed/1 skipped 环境面红集）；本 task 以零新增红为闸，30 开工须复核当前基线 |

## 二、批切参数化建议形态（10 推导 · 签闸裁定口）

1. **裁切点**：ApiEmbedder.embed() 内部（非 ingest 调用面）——Embedder Protocol 签名不变 → ingest.py:225 / 查询侧 get_query_embedder() / memory 等全部消费方零改动自动受益；ingest.py 预期整个零 diff。
2. **参数形态**：`batch_size: int | None = None` 构造参数 → env `RAG_EMBED_API_BATCH_SIZE`（未设/非法/≤0 → warning + 回退默认 · 承 :113-125 先例）→ **默认值钉死 128**。推导：safe zone ≈500（465 实证安全）· 速率 ~34 chunks/s → 128 ≈ 3.8s/批 << timeout 60s（15× 余量）· 比 500 留 4× 防 API 侧漂移；签闸可改判 64/256。
3. **失败纪律**：逐批复用既有 max_retries=3 指数退避；批级耗尽 **fail-fast 整单 raise**（不缓存部分批、不部分返回、重跑整单幂等安全 · 与缺 key 不回落 ST 同哲学）；skip-and-DLQ 形态与既有降级面（影子写 DLQ 不回滚不阻塞）哲学不同，不默认采纳，裁定口留维护者签注。
4. **台账**：批级 logger.info（i/N · chunks · 批耗时）+ 汇总（总 chunks/批数/总耗时/均速）；token 维度由 40 报告以 BgeM3TokenCounter 口径估算（embedder 不引 tokenizer 依赖）。
5. **向后兼容评估**：env 未设=默认 128 钉死；≤128 条输入 POST 次数=1 且 payload 逐字节不变（含查询侧单条形态）；>128 条由「超时失败」变「分批成功」=修 bug 非破坏。timeout=60/max_retries=3 默认不动。

## 三、产出

- task 草稿：docs/tasks/active/task_api_embedder_internal_batching.md（F1 批切 / F2 红测先行回归 / F3 ≥1000 实证 / F4 图谱闸评估 · 非范围六条 · FP-1~8 · TC-EB-1~5 · R0–R5 思考轮 R5 early_stop）
- lint：`npx spec-wave task lint --file docs/tasks/active/task_api_embedder_internal_batching.md` → **LINT: PASS**（exit 0 · 2026-10-19）
- 闸：HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 全 **pending**（未代签 · 签注裁定口=默认批大小 / 失败纪律 / F3b 写面授权）
- git：零操作（只读 rev-parse/status）；新增仅本 task 档 + 本 invoke（untracked）

## 四、三裁定口（维护者签闸时）

| 口 | 10 建议 | 备选 |
|----|---------|------|
| 默认批大小 | 128（500 safe zone 1/4 · 3.8s/批） | 64 / 256 |
| 部分批失败 | fail-fast 整单 raise（承既有哲学） | skip-and-DLQ（须补配套断言 · 与降级面对齐评估） |
| F3b 端到端写面复跑 | 不默认授权（F3a 只读 ≥1000 已足证批切） | 授权受控写面 + 水位 match 收尾 |
