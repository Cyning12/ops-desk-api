---
hat: 20-task-audit
task_slug: api_embedder_internal_batching
review_round: R1
date: 2026-10-19
reviewed_file: docs/tasks/active/task_api_embedder_internal_batching.md
---

# R1 书面审查 · task_api_embedder_internal_batching（ApiEmbedder 内部批切 · 30 落码棒 · 含 HG-GRAPH-MODULES 闸）

## 元信息

| 项 | 值 |
|---|---|
| 审查帽 | 20-task-audit（书面审查 · 不落实质改动 · 不代签任何人工闸 · 零 git） |
| 被审对象 | `docs/tasks/active/task_api_embedder_internal_batching.md`（192 行 · 2026-10-19 10 落稿 · draft） |
| 审查轮次 | R1 |
| 审查方式 | 全文亲读 + 锚点逐条亲跑亲读核真（14 项 · 含 22 测基线亲跑复跑） |

## 结论摘要

**结论：通过（R1 签收）**。本帽已于 2026-10-19 对 `docs/tasks/active/task_api_embedder_internal_batching.md` 完成 R1 书面审查：改码面（`app/ops/rag/embedder.py` + `tests/test_rag_embedder.py` 两件）与非范围六条边界清晰，ingest.py:225 全量单请求面与 embedder 实现锚点逐行亲核命中，上游 CLOSE 档批切移交引用逐字真实，失败纪律裁定口（fail-fast 默认 · skip-and-DLQ 留签注改判）与既有降级面哲学一致，HG-GRAPH-MODULES 闸列入与 graph_change_layer=G-L1 预判合规，required_invoke_hats=10,30,40 与 30 棒必要性成立，R0–R5 齐套，锚点 14/14 亲核命中，内容面零阻塞项。

流程闸面（与内容面分列）：`HG-TASK-DRAFT` / `HG-AUDIT-R1` / `HG-GRAPH-MODULES` 三闸在 task 人工闸表均如实记为 **pending**，本帽不代签；维护者签闸清单见末节（含三签注裁定口）。

## 锚点核验记录（20 亲跑亲读 2026-10-19 · 14/14 命中）

| # | 档内声称 | 复核手段 | 结果 |
|---|----------|----------|------|
| 1 | ingest.py:225 `vectors = embedder.embed([p[2] for p in pending])` 全量单请求面 | 亲读 :223-227 | ✅ 逐字一致（:225）；前置维度断言 :226-230 在案 |
| 2 | ingest.py:236 `zip(pending, vectors, strict=True)` 保序强依赖 | 亲读 :236 | ✅ 逐字一致 |
| 3 | embedder.py:87 单 payload `{"model","input":texts}` | 亲读 :85-98 | ✅ 逐字一致 |
| 4 | embedder.py httpx.post timeout=60（:92-94）· 响应按 index 排序（:97） | 亲读 | ✅ 逐字一致（保序先例成立，批切跨批拼接有据） |
| 5 | embedder.py 全文 172 行 · env 解析先例 :113-125 | `wc -l` + 亲读 | ✅ 172 行；`embed_backend()` strip/lower · 空/未设→默认 · 非法 warning+回退 形态在案 |
| 6 | 上游 CLOSE §三.2 引文（无批切 · 上限≈500 · --limit 75 · 25/25 步 248s · 另立 task） | 亲读 `close_local_rag_knowledge_rebuild_20261018.md` :30 | ✅ 逐字在案；§三.4「17077 chunks ≈ 6.0M tokens · ~34 chunks/s」:32 在案；§五 移交 :43 在案 |
| 7 | safe zone 证据 f3_incident_tombstone.md:7 | 亲读 | ✅ 「step size 75/source/run (~150 units ~465 chunks < n=500 proven API safe zone)」逐字在案 |
| 8 | 40 invoke :50「内部批切属改码，FP-8 纪律未落，建议另立 task」 | 亲读 `invoke_20261018_40_rebuild.md` :48-52 | ✅ 逐字在案（:50） |
| 9 | scripts/rag_ingest.py :50 --limit · :51 --batch-size 仅传 ST（:63）· ApiEmbedder 无批参数（:65）· 88 行 | 亲读 :50-51/:60-66 + `wc -l` | ✅ 逐字一致——批切缺口定位属实 |
| 10 | tests/test_rag_embedder.py 9 测 + test_check_vector_waterline.py 13 桩测 | `grep -c 'def test_'` | ✅ 9 + 13 |
| 11 | 批切前绿基线 22 passed（9+13 · master 4a5e755） | 亲跑 `.venv/bin/python -m pytest tests/test_rag_embedder.py tests/test_check_vector_waterline.py -q` | ✅ **22 passed in 3.62s**（本帽复跑复现） |
| 12 | PG ops_knowledge_chunks=8648（F3 语料池背景） | 亲跑 docker exec psql（ops/opsdesk） | ✅ 8648 |
| 13 | 图谱 rag 行 `01_modules.md:31` 现状备注含「查询 embed 默认 SiliconFlow HTTP（`RAG_EMBED_BACKEND`）」 | 亲读 :31 | ✅ 逐字在案，F4 行内追加备注落点真实 |
| 14 | 10 invoke `invoke_20261019_10_task_draft.md` 已落盘 | `ls` | ✅ 在案（by-task/api-embedder-internal-batching/） |

**锚点核验命中率：14/14 = 100%**。

## 审查要点裁定

- **裁切点与批切参数化建议合理**：裁切点放 embedder 内部（Protocol 签名不变 · ingest.py:225 与查询侧零改动），所有消费方自动受益；默认值 128 推导链闭合（safe zone ≈500 的 1/4 · 实测 ~34 chunks/s → 128 ≈ 4s/批 << timeout 60s · 15× 余量），且明示「建议值 · 签闸可改判 64/256」——参数化但未越权钉死。
- **部分批失败纪律裁定口合规**：建议 fail-fast（批级重试耗尽整单 raise · 不缓存部分批 · 重跑幂等安全）与既有哲学（缺 key raise :78-81 · HTTP 重试耗尽 raise 不回落 ST）一致；skip-and-DLQ 与影子写 DLQ 降级面哲学不同，不默认采纳、留维护者签注显式改判——裁定口设计得当。
- **小规模兼容断言可机断**：「输入 ≤ batch_size 时 POST 次数==1 且 payload 逐字节等价」为自动化断言形态，FP-4 向后兼容口径（≤128 逐字节不变 · >128 由超时失败变分批成功=修 bug 非破坏）成立。
- **HG-GRAPH-MODULES 闸列入与 graph_change_layer 预判合规**：G-L1 预期 rag 行备注级（承 session-summary-fallback 行内先例），并留「30 实判可降 none 须填理由」的降级口；闸表 blocks=30 与本 task 30 落码棒性质匹配。
- **required_invoke_hats=10,30,40 必要性成立**：有码改 · 红测先行 · PR 流，30 棒不可缺；10/40 已分别落盘/规划。
- **PR #276 超时实录引用真实**：探测上限≈500 · --limit 75 分批 248s · safe zone ~465<500 三处引文全部逐字亲核（核验 #6/#7/#8）。
- **红测先行与回归闸闭合**：F2 四组新测（切批/保序/配置/失败纪律）先见红再实现；既有 9+13 测零改动全绿 + 全量 pytest 红集⊆基线（基线须 30 开工亲跑复核留档，承 ruff task 口径）；TC-EB-4 diff 白名单与 F1「唯一改码面两件」自洽。

## 阻塞级问题与 nit 清单

- 阻塞级问题：**无**。
- nit（不阻签收 · 可选回填）：
  1. HG-AUDIT-R1 闸说明内含三签注裁定口（默认批大小 128 / 部分批失败纪律 fail-fast / F3b 写面复跑授权）——维护者签闸时须逐条签注，提醒级。
  2. pytest 全量基线承 2026-10-18 ruff task（master c956d87 · 19 红）为转引值；档内已要求 30 开工亲跑复核当前基线留档，闭合，无需改档。
  3. F3a「不落 scripts/ 新文件 · 一次性片段全文留档 40 invoke」为防扩散纪律，执行帽须注意片段全文入 invoke 附件，知悉级。

## 回填清单

无强制回填项（三条 nit 均为知悉/提醒级，不要求改档）。

## 维护者签闸（20 后 · 30 前）

- [ ] 已读 R1 审查结论（本文）
- [ ] 在 task 人工闸表将 HG-TASK-DRAFT 改为 approved（维护者 · 日期）
- [ ] 在 task 人工闸表将 HG-AUDIT-R1 改为 approved（维护者 · 日期）——**签注三裁定口**：默认批大小取值（建议 128 · 可改判 64/256）· 部分批失败纪律（建议 fail-fast · skip-and-DLQ 须显式改判）· F3b 写面复跑是否授权
- [ ] 在 task 人工闸表将 HG-GRAPH-MODULES 改为 approved（维护者 · 日期 · G-L1 rag 行备注级预判确认；30 实判降 none 须签注理由）
- [ ] commit task 文档或确认已签
- [ ] 再下发 Harness 30 Prompt（前提：task 表已 approved，非「计划签」）

30 Agent 将以 task 表为准；pending 时必须拒开工（见 TEMPLATE_30_gate_stop.md）。
