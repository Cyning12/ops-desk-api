# invoke · 30 · memory-embedding-backfill · 实现

| 项 | 内容 |
|----|------|
| **时间** | 2026-09-21 |
| **帽** | 30（实现 · 不签任何 human_gate） |
| **分支** | `task/memory-embedding-backfill`（每次 commit 前 `git branch --show-current` 核验 · 未切 master · 未 push） |
| **task** | `docs/tasks/active/task_memory_embedding_backfill.md`（HG-TASK-DRAFT/HG-AUDIT-R1/HG-GRAPH-MODULES 全 approved · `npx spec-wave verify` PASS 已由 00 核验） |
| **SPEC** | `docs/spec/memory-embedding-backfill/SPEC-memory-embedding-backfill_v1.md`（signed） |

## 落地摘要

- **D1**：`scripts/memory_embedding_backfill.py` —— 扫 `embedding IS NULL AND status='active'`（id ASC keyset）→ `_fact_embed_text` 原样复用 → 每页一次 `embed()` 批调用经 `asyncio.to_thread` 卸载 → 逐行 UPDATE 带 `status='active'` 再核（rowcount=0 记 skipped）· 前置校验 name==`RAG_EMBED_MODEL` + 试嵌维度==1024 + embedding 列探测，不符 exit 2 零写入 · CLI 自建引擎（对齐 rag_ingest 独立引擎先例），session_factory 可注入。
- **D2**：谓词幂等 + keyset 续跑（checkpoint 仅加速，损坏/缺失从头重扫，页内零失败才推进水位）· `MEMORY_BACKFILL_SLEEP_MS` 批间限速 · 回填层零叠加重试，连续 3 页全败终止 status=failed · 报告落 `reports/memory_embedding_backfill/backfill_<UTC>.yaml`（守恒 embedded+skipped+failed==scanned · 实跑后重扫对账剩余==failed 否则 status=failed）· `--dry-run` 零嵌入零写库 · SIGINT/SIGTERM 页边界 partial。
- **D3**：`tests/test_memory_injection.py` 追加四分支 span 单测（capture-list monkeypatch continuity 命名空间，对齐 test_llm_routing.py:176）：N==注入条数 / 0 / degraded 无 injected / 关零调用。**先行提交**（d0b86e5，纯测试零风险面，承 SPEC R5/§8）。
- **D4**：`tests/test_memory_embedding_backfill.py` 15 条集成测（真 PG opsdesk_test）：干跑/实跑 scanned 对账 + 重扫剩余==failed + 对账不等（并发插入）→ status failed；金样轨**实走态② FakeEmbedder 集成夹具轨**（`git ls-files evals/memory/`=0 tracked 复核），含回填前基线（pre top1=project.favorite_editor 确定性行，target 不命中）→ 回填后 top1 命中存量行。
- **D5**：`app/ops/memory/README.md` 增补回填小节 + env 表三行（CLI 用法 / 报告形态 / 口径同源声明）。

## 验证（真跑）

| 项 | 结果 |
|----|------|
| `pytest tests` 全量 | **1174 passed, 3 failed, 1 skipped**；3 红 = 基线环境性红（test_chat_ws×2 + capability proxy×1），`git stash -u` 回基线复跑同 3 红证实与本波无关 |
| 新测 | D3×4 + 回填×15 全绿 |
| `ruff check app tests scripts` | 基线 67 条历史债 == 本波 67 条（**零新增**；新增两文件单查全绿） |
| `./scripts/graph-compile.sh` | 绿（仅存量 warning：10_flow_structured_output triggers 未登记 · 不咬 exit · 与本波无关）· 零图谱变更裁定与实现形态一致（无新路由/表/事件类型） |
| CLI 真跑 | `--dry-run` 对开发库：exit 0 · status=pass · 报告落盘形态核验（embedder_name=BAAI/bge-m3 · 零明文） |
| 变异检验 | 删扫描谓词 `status='active'` → `test_backfill_embeds_only_active_null_rows` **真 fail**（断言 inactive 行零嵌入触发）→ 已还原复跑 15 绿 |

## B1 旧测影响面 11 条逐条处置回填

1. `test_null_embedding_rows_stay_on_deterministic_path` → **回归**：在线路径零改动，全量重跑绿 ✓
2. vector_p1 四条（paraphrase/degrade/write_embed_failure/env fallback）→ **回归**绿 ✓；FakeEmbedder 形态被新测复用（新文件自建 RecordingFakeEmbedder，不改旧文件）
3. `test_memory_injection.py` 既有断言 → **回归**绿 ✓；D3 四条为**追加**（非改编）
4. `test_memory_service_db.py` → **回归**绿 ✓；新测对齐其 skipif/自清先例（独立前缀 `mfb-test-`；因回填全表扫描，fixture 清全表保计数确定性，opsdesk_test 隔离由 conftest 强制）
5. `test_memory_extract_p1.py` → **回归**绿 ✓（回填不触抽取链路）
6. `test_rag_embedder.py` → **回归**绿 ✓（消费 Embedder 不改实现）
7. `test_llm_routing.py:176` capture-list → **回归**绿 ✓（模式被 D3 复用，先例不动）
8. tests/ 全仓 `memory_facts_injected` 零断言 → **新增** D3 四条钉死 ✓
9. `MEMORY_BACKFILL` 全仓零命中 → **新增**三 env + 非法值回退 warning 测全覆盖 ✓
10. `scripts/rag_ingest.py` / qdrant 报告先例 → **回归**（只读参考，未改）✓
11. `evals/memory/` 0 tracked → **新增**态②夹具轨（`test_paraphrase_recall_before_after_backfill`）；态①切换条件不变 ✓

## 钉死契约关键实现注记

- **「幂等第二次零调用」裁定**：前置维度试嵌只在「实跑且候选数 > 0」时执行（干跑/零候选零嵌入调用）——第二次跑 scanned=0 → FakeEmbedder 字面零调用，验收原文成立；试嵌先于任何写库，exit 2 零写入语义不损。
- **name 前置校验口径**：`embedder.name == embed_model_name()`（RAG_EMBED_MODEL）；ApiEmbedder 构造即以该 env 为模型名，默认路径自洽；注入 embedder 的测试显式 setenv 对齐。
- **CLI 引擎隔离**：main 自建 AsyncEngine（finally dispose），不占 app 全局连接池——修复了 in-process 测 CLI 时跨事件循环连接污染（真实防御，非测试便利）。

## commit 列表

1. `d0b86e5` test(memory): span memory_facts_injected 三分支单测（D3 先行）
2. feat(memory): 存量行 embedding 回填 CLI + 集成测试（D1/D2/D4）· task memory-embedding-backfill
3. docs(memory): README 回填小节 + env 表 + 30 invoke（D5）· task memory-embedding-backfill

## 遗留风险（承 SPEC §7 residual）

- 态②夹具轨证据强度弱于 live 金样（residual ①；金样合入后按裁定切态①重跑对照）
- 回填速率（默认 32/页 + 200ms）未经真实存量校准（residual ②；开发库 dry-run scanned=0，无实存量可校）
- 连续失败页 continue 分支同样执行批间 sleep（实现细节，语义无害）

## 闸纪律

本帽未签任何 human_gate；graph_delta 零变更裁定与实现一致（无新端点/表/事件类型），未触发回炉补闸条款。
