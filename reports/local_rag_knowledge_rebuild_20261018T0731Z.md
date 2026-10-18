# 本地 RAG 知识库重建报告（task_local_rag_knowledge_rebuild · 40 实证执行）

> **disclaimer（钉死）**：本报告全部为**本地 docker compose 开发库口径**（ops-desk-api-db-1 + ops-desk-api-qdrant-1 · 本机 127.0.0.1），**不得外推生产**。生产侧任何动作仍属 HG-PROD-READONLY-ACCESS（pending）管辖（FP-9）。
> 执行时间：2026-10-18 15:00–15:32 (+08:00) · 执行棒：40 单棒 · 零落码（app/** scripts/** alembic/** docker-compose.yml 零 diff，git 实证）。

## 结果速览

| 项 | 值 |
|---|---|
| chunks_written（恢复轮累计） | **8429**（+首轮已含 docs 219） |
| PG ops_knowledge_chunks 终值 | **8648**（issue 2762 · pr 5667 · doc 219） |
| Qdrant ops_knowledge points | **8648** |
| 三对照 | ingest 累计 8429+219 == PG 8648 == Qdrant 8648 ✅ |
| 水位 verdict | **match**（diff=0 · PG独有=0 · Qdrant独有=0 · DLQ=0 · degraded=false）→ reports/vector_waterline_local_20261018T072903Z.yaml |
| 规模裁定 | **8648 ∈ [6000,12000]** ✅（历史常态 8574 · 偏差 +0.9%） |
| 检索抽检 | **命中**（降级纯向量形态 · top-1/top-3 双中 issue#2720 · 显式标注非全链） |
| embedding 失败 | 首轮 2 次环境级失败（见下）· 正式分批轮 **0 失败**（25/25 步 attempt=1） |

## F1 前置核验（全绿）

- 双容器 Up 2 days (healthy)：ops-desk-api-db-1 · ops-desk-api-qdrant-1。
- .env：SILICONFLOW_API_KEY 存在非空（grep 计数=1 · 值零落档）· RAG_QDRANT_SHADOW_WRITE=true（计数=1）。
- Qdrant collection ops_knowledge：status=green · points_count=0 · dim=1024 · Cosine · on_disk。
- PG 零点基线对齐 20261018T005534Z：chunks=0 · dlq=0 · issues=881 · pulls=1855。
- docs-root 路径核实：worktree 下相对路径 ../ops-desk-workspace 不存在；改用绝对路径 /Users/cyning/Desktop/Ops-desk/ops-desk-workspace/docs/{05-plan(11 md), contracts(8 md)}（与任务档 11/8 计数一致）。

## F2 dry-run（规模裁定核验通过）

`uv run python scripts/rag_ingest.py --dry-run --docs-root <05-plan abs> --docs-root <contracts abs>`
→ {scanned: 2755, to_upsert: 2755, unchanged: 0, to_delete: 0}。881+1855+19=2755 精确匹配语料面，空库预期三态成立。

## F3 重建执行（含两次环境级失败与一次编排事故 · 全照登）

### 失败 1（环境 · 已修复）：httpx.InvalidURL "Invalid port: ':1]'"
41s 即败。栈定位 httpx/_client.py:697 mounts 构造——shell NO_PROXY 含 IPv6 条目 `[::1]`，httpx URLPattern 误解析为 port ':1]'。**非 app/scripts 缺陷，零落码修复**：重跑时清洗 NO_PROXY/no_proxy='localhost,127.0.0.1'（http_proxy/https_proxy/all_proxy 保留）。修复前后 httpx.Client() 构造对照实证留档。

### 失败 2（API 批量上限 · 零落码绕过）：httpx.ReadTimeout
清洗后重跑 197s 败：ingest.py:225 `embedder.embed([p[2] for p in pending])` **一次性提交全部变化集**，ApiEmbedder（embedder.py:84-110）无内部批切 → ~8.6k 文本单请求经代理 60s 读超时 ×3 重试耗尽。探测实证：n=32/500 文本 OK（0.9s/5.6s），n=1000/1500 服务端 500/超时——**API 单批安全上限 ≈500 文本**。历史全量成功因默认 --embedder st（rag_ingest.py:52）内部批切 32。

### 编排事故（我的失误 · 已恢复 · 零源数据损失）
首轮分批用 `--only issues/pulls` 递增 --limit 全部成功（28/28 步），但收尾 standalone `--only docs` 触发 ingest.py:291-302 墓碑对账：seen={19 docs} → PG 内 2736 issue/pull 单元判 stale 删除（chunks 8648→219），影子删同步 Qdrant。**ops_issues/ops_pull_requests 源表零损失**，PG chunks 为派生数据可重建；DLQ=0 证明影子删全部成功。事故分析落 evidence/f3_incident_tombstone.md。

### 恢复轮（成功路径）
纠偏编排：递增 `--limit 75..1875`（步长 75/源 · 每步约 150 units ≈465 chunks < 500 安全区）**不带 --only**，docs 经 load_doc_units 恒在 seen 集 → 墓碑安全。25/25 步全 OK（均 attempt=1 · 单步 8–12s · 全程 248s）：issues+pulls 重嵌入重写 8429 chunks，docs 219 hash 未变跳过，终步 scanned=2755 **to_delete=0**。

### 成本/速率实测
- 嵌入总量：首轮 8648 + 恢复轮 8429 = **17077 次 chunk 嵌入**（含事故返工 ~8.4k，照登）。
- 速率：恢复轮 8429 chunks / 248s ≈ **34 chunks/s**（含 tokenizer 加载与 PG 写入开销）；API 单请求 n≈465 文本约 5–10s。
- token 估算：≈17077 chunks × 均值 ~350 tokens ≈ **6.0M tokens**（其中事故返工约 2.9M）；按 SiliconFlow bge-m3 刊例价自行折算，量级元级。

## F4 双侧一致性核验（硬闸 PASS）

`uv run python scripts/check_vector_waterline.py --env local` → reports/vector_waterline_local_20261018T072903Z.yaml：
PG 行数 8648 · Qdrant points 8648 · **diff=0 · verdict=match · DLQ 深度 0 · degraded=false**。三对照成立。影子写全程零 DLQ（含事故轮影子删）。

## F5 检索抽检（降级形态 · 显式标注）

- 首选 `scripts/rag_smoke.py` 全链：**不可用（环境缺 langchain 包，Langfuse 集成 graph 阶段报错）**——非检索缺陷，FP-7 降级路径。
- 降级纯向量检索（/tmp 探针 · 嵌入 G01 query → Qdrant search · 不落仓码）：
  top-5 中 **#1 score=0.7431 issue#2720 chunk0 · #3 score=0.6958 issue#2720 chunk1** 双中锚；#2 contracts/rag-knowledge-contract-v1.md。#4/#5 为 issue#1585/#2427。
  **结论：知识可检（向量层实证）· 形态=DEGRADED_VECTOR_ONLY，未冒充全链**。全链 rag_smoke 待 langchain 环境补齐后另验（非本 task）。

## TC 对照

TC-RK-1 ✅ 前置三面落档 · TC-RK-2 ✅ dry-run 2755 精确匹配 · TC-RK-3 ✅ chunks_written=8429(+219)>0 失败照登 · TC-RK-4 ✅ 水位 match 三对照 DLQ=0 · TC-RK-5 ✅ 降级向量抽检锚双中（形态标注）· TC-RK-6 ✅ 8648∈[6000,12000] 对照历史 8574 · TC-RK-7 ✅ 零 diff · pytest 13 passed · LINT PASS · 证据全落档。

## 偏差与教训（照登）

1. NO_PROXY IPv6 条目触发 httpx 解析 bug——worktree/CI 环境复跑须携带 NO_PROXY 清洗（证据 f3_retry_note.md）。
2. --embedder api 无内部批切，全量单请求必超时——分批 --limit 递增为零落码正解；长期解（ApiEmbedder 内部批切）属改码，**本 task FP-8 纪律下未落**，建议另立 task。
3. `--only` 局部跑作收尾会触发墓碑对账误删他源——编排教训：任何局部 run 之后必须跟全 seen 集终跑，或全程不带 --only。
4. 事故返工多耗 ~2.9M tokens 嵌入量，照登不遮掩。
