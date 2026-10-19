---
hat: 20-task-audit
task_slug: api_embedder_internal_batching
date: 2026-10-19
---

# invoke · 20-task-audit R1 · api_embedder_internal_batching（ApiEmbedder 内部批切 · 30 落码棒 · 含 HG-GRAPH-MODULES 闸）

## 审查行为实录

- 审查帽：20-task-audit（书面审查 · 不落实质改动 · 不代签闸 · 零 git）。
- 被审对象：`docs/tasks/active/task_api_embedder_internal_batching.md`（192 行 · 2026-10-19 10 落稿）。
- 审查文落盘：`docs/harness/reviews/task_api_embedder_internal_batching_audit_R1_20261019.md`。

## 锚点亲核实录（14/14 命中）

- 全量单请求面亲读：`app/ops/rag/ingest.py:225` `vectors = embedder.embed([p[2] for p in pending])` 逐字一致；:236 `zip(pending, vectors, strict=True)` 保序强依赖在案。
- embedder 实现亲读（全文 172 行）：:87 单 payload `{"model","input":texts}` · :92-94 httpx.post timeout=60 · :97 按 index 排序保序先例 · :113-125 `embed_backend()` env 解析先例（strip/lower · 空/未设→默认 · 非法 warning+回退）——逐字一致。
- 上游引用逐字亲核：close_local_rag_knowledge_rebuild_20261018.md §三.2（:30 · 上限≈500 · --limit 75 · 25/25 步 · 248s · 另立 task）· §三.4（:32 · 17077 chunks ≈ 6.0M tokens · ~34 chunks/s）· §五（:43 移交）；f3_incident_tombstone.md:7「~465 chunks < n=500 proven API safe zone」；invoke_20261018_40_rebuild.md:50「内部批切属改码…建议另立 task」——全部在案。
- scripts/rag_ingest.py 亲读（88 行）：:50 --limit · :51 --batch-size 仅传 SentenceTransformerEmbedder（:63）· ApiEmbedder 构造无批参数（:65）——批切缺口定位属实。
- 测试面亲跑复核：test_rag_embedder.py 9 测 + test_check_vector_waterline.py 13 桩测；`.venv/bin/python -m pytest tests/test_rag_embedder.py tests/test_check_vector_waterline.py -q` → **22 passed in 3.62s**（批切前绿基线复现）。
- PG ops_knowledge_chunks=**8648** 亲跑（ops/opsdesk · F3 语料池背景）。
- 图谱 rag 行 `docs/_tech_graph/l1/01_modules.md:31` 亲读：现状备注含「查询 embed 默认 SiliconFlow HTTP（`RAG_EMBED_BACKEND`）」，F4 行内备注落点真实。
- 10 invoke `invoke_20261019_10_task_draft.md` 在案。
- 闸表亲读：HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 三闸全 pending 如实，未代签。

## 结论

**通过（R1 签收）**：内容面零阻塞项。裁切点 embedder 内部（Protocol/ingest/查询侧零改动）· 默认 128 推导链闭合（safe zone 500 的 1/4 · ~4s/批 << 60s）· fail-fast 建议与既有降级哲学一致（skip-and-DLQ 留签注改判）· 小规模逐字节等价断言可机断 · required_invoke_hats=10,30,40 必要性成立。nit 三条（签注三裁定口提醒 · pytest 全量基线 30 开工复核已闭合 · F3a 片段全文留档知悉）。维护者签闸清单（含三签注裁定口）已附审查文末节；三闸 pending 期间 30 拒开工。

## 边界声明

本帽零文件实质改动（仅新增审查文 + 本 invoke）· 零 git · 未代签任何人工闸 · 未改 app/ 任何代码 · pytest 仅复跑只读验证。
