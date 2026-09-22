# invoke · 40 · memory-embedding-backfill · 核验

| 项 | 内容 |
|----|------|
| **时间** | 2026-09-21 |
| **帽** | 40（核验 · 不改实现码 · 不签任何 human_gate） |
| **分支** | `task/memory-embedding-backfill`（每次 commit 前 `git branch --show-current` 核验 · 未切 master · 未 push；基线对照用 `git worktree` @ origin/master 1bb24a8，不动工作树） |
| **task** | `docs/tasks/active/task_memory_embedding_backfill.md`（验收 21 条） |
| **SPEC** | `docs/spec/memory-embedding-backfill/SPEC-memory-embedding-backfill_v1.md`（signed） |
| **被验对象** | 30 invoke `invoke_20260921_30_implement_memory_embedding_backfill.md`（commits d0b86e5 / 79b9cd0 / adb758b） |
| **金样轨实际走轨** | **态② · FakeEmbedder 集成夹具轨**（40 复核 `git ls-files evals/memory/` = 0 tracked，态①切换条件未触发）· **含回填前基线**（`test_paraphrase_recall_before_after_backfill`：pre top1=`project.favorite_editor` 确定性行、target 不命中 → 回填后 top1 命中存量行） |
| **证据强度判定** | 态②夹具轨证据强度**弱于** live 金样（承 SPEC §7 residual ①，维护者签收时已知悉）；谓词正确性由变异检验补强（40 亲自复做，见下） |

## 总判定：**PASS（验收 21/21 通过 · 0 FAIL · 2 WARN）**

## 核验动作（40 真跑留证据 · 全程未轻信 30 自称）

| # | 动作 | 证据 | 结论 |
|---|------|------|------|
| 1 | `pytest tests` 全量（分支） | **1174 passed, 3 failed, 1 skipped**；3 红 = `test_chat_ws::test_ws_message_streams_events` / `test_ws_second_message_while_active_rejected` / `test_capability_http_adapter::test_urllib_transport_honors_explicit_capability_proxy` | 与 30 自称一致 |
| 2 | 基线对照（`git worktree` @ origin/master 1bb24a8 · 补齐同 `.env` 后复跑） | 基线 **1155 passed, 3 failed, 1 skipped**，3 红与分支**完全同三条** → 基线环境红与本波无关坐实；总数差 1178−1159=**19 = 新测 19（D3×4+回填×15）全绿** | PASS（比 30 的 stash 对照更严：worktree 不动工作树） |
| 3 | `ruff check app tests scripts` | 分支 67 errors == 基线 worktree 67 errors（**零新增**） | PASS |
| 4 | `./scripts/graph-compile.sh` | exit 0 绿（仅存量 warning：10_flow_structured_output triggers 等未登记 · 不咬 exit · 与本波无关）；`graph.json` 仅 `generated_at` 时间戳漂移，已 `git checkout --` 还原不混入提交；`git diff origin/master HEAD --stat` 确认**零图谱 yaml 变更**，与零变更裁定一致（无新路由/表/事件类型） | PASS |
| 5 | 断言真实非空抽查（逐行读 `scripts/memory_embedding_backfill.py` 511 行 + `tests/test_memory_embedding_backfill.py` 608 行 + D3 diff 93 行） | 幂等：`r2=(0,0,0,0)` 且 `fake2.calls==[]`（含前置试嵌零调用）· dry-run：`fake.calls==[]` + 行保持 NULL + 报告 `dry_run: true` · 断点续跑：`rerun_texts.isdisjoint(page1_texts)` · 报告守恒：`embedded+skipped+failed==scanned` 双断言（report 对象 + yaml 落盘件）· 前置校验 exit 2：CLI 层 `rc==2` 三态（name/维度/缺 SILICONFLOW_API_KEY）+ 零写入断言 · span 四分支：`captured==[{"memory_facts_injected":2}]` / `==[{"memory_facts_injected":0}]` / `==[{"memory_degraded":True}]` 且无 injected / `==[]` | PASS（全为否定性实断言，非空真规则） |
| 6 | **变异检验 40 亲自复做**：删 `_fetch_page` 扫描谓词 `status='active'` | `test_backfill_embeds_only_active_null_rows` **真 FAIL**（`At index 0 diff: 6 != 3`，inactive 行被误扫嵌入触发计数断言）→ `git checkout --` 还原 → `pytest tests/test_memory_embedding_backfill.py tests/test_memory_injection.py` **34 passed** → 工作树净 | PASS（防空真规则成立） |

## 验收 21 条逐条

### 人工闸（1 条）
1. HG-AUDIT-R1 approved 后方勾选码项 → 闸表 approved（00 代录 · commit 1b1b3fe · 先于 30 三 commit）· HG-GRAPH-MODULES approved 且零图谱变更裁定与实现形态一致，未触发回炉补闸 → **PASS**

### D1 · 回填主体（4 条）
2. 扫描谓词只命中 active-NULL（3 active-NULL 嵌入 · superseded/revoked/expired 零嵌入 · 已嵌行不触碰 · embed() 文本 == `_fact_embed_text(key,value)` 逐条一致 · to_thread 线程卸载断言）→ `test_backfill_embeds_only_active_null_rows` 绿 + 变异检验咬住 → **PASS**
3. 回写再核竞态：embed 后回写前置 superseded → skipped 且保持 NULL → `test_write_recheck_race_marks_skipped`（`(2,1,1,0)`）→ **PASS**
4. 前置校验维度/name 不符 → exit 2 零写入 → `test_preflight_bad_dimension_exit_2` / `test_preflight_name_mismatch_exit_2` / `test_cli_preflight_failures_exit_2`（CLI 层 `rc==2` ×3 态）→ **PASS**
5. keyset 分页 batch=2 造 5 行 → 3 页 `[2,2,1]` · id 严格递增无重复 → `test_keyset_pagination_strictly_increasing` → **PASS**

### D2 · 幂等/续跑/报告（5 条）
6. 幂等：第二次 `scanned=0 embedded=0` · FakeEmbedder 字面零调用（`fake2.calls==[]`）→ **PASS**
7. 断点续跑：页 1 成功 + 连续 3 页全败终止（`status=failed` · `(8,2,6)`）→ 重跑补齐 `(6,6,0)` 且 `rerun_texts.isdisjoint(page1_texts)` → **PASS**（验收原文「第 2 页抛错终止」以实现态「连续 3 页全败终止」覆盖，更强）
8. 部分失败：第 2 页 `httpx.HTTPError` → `embedded=2 failed=2` · `failed_ids` == 第 2 页 id 集 · 重跑清零 → **PASS**
9. 报告形态：yaml 含 status/scanned/embedded/skipped/failed/failed_ids/embedder_name/dry_run/elapsed_s/recorded_at 等 13 键（`required <= set(data)`）+ 守恒双断言 → **PASS**
10. env 非法值回退 + warning 三 env 全覆盖（含 checkpoint 指目录/文件损坏）· `--dry-run` 零写零调用 + 报告 `dry_run: true` → **PASS**

### D3 · span 单测（4 条）
11. 有 facts：`captured==[{"memory_facts_injected":2}]` 且注入块真含两条 → **PASS**
12. 零 facts：`==[{"memory_facts_injected":0}]` 且无注入块 → **PASS**
13. 召回故障：`==[{"memory_degraded":True}]` 且全程无 injected + 形状对齐 baseline → **PASS**
14. 开关关闭：`captured==[]` 且逐字节形状一致 → **PASS**

### D4 · 对账与金样对照（3 条）
15. 干跑/实跑对账：`dry.scanned==real.scanned==4` · 重扫剩余==failed（含对账不等 → status=failed 反向测 `test_reconcile_mismatch_marks_failed`）→ **PASS**
16. 复述召回对照：**态②**（前置条件 40 复核成立）· 含回填前基线（pre top1 不命中 target）→ 回填后 top1 命中 → **PASS**
17. 变异检验：40 亲自复做真 fail → 还原复跑绿 → 工作树净 → **PASS**

### 工程（4 条）
18. B1 闸前置：旧测影响面 11 条 30 invoke 逐条处置回填（回归×8 / 新增×3 · 无删除无改编）· 40 抽查：#8 `memory_facts_injected` 已有 D3 断言钉死 · #11 `evals/memory/` 0 tracked 复核成立 → **PASS**
19. ruff 67==67 零新增 · pytest 新测 19 绿 + `test_memory_*` 回归绿（3 红基线坐实）→ **PASS**
20. graph-compile 绿 · 零图谱变更裁定与实现形态一致（diff stat 无 graph yaml）→ **PASS**
21. `app/ops/memory/README.md` 回填小节 + env 表三行（CLI 用法 / 报告形态 / 口径同源声明）→ **PASS**

## WARN（不阻塞 · 记录）

- **W1**：态②夹具轨召回提升证据强度弱于 live 金样（承 SPEC §7 residual ① · 签收知悉项）；`evals/memory/` 合入后按裁定切态①重跑对照。
- **W2**：基线 worktree 首次对照因 `.env` 缺 `SILICONFLOW_API_KEY` 多出第 4 条红（`test_memory_vector_p1.py::test_embedder_failure_degrades_with_marker` · 环境噪音非本波引入）；40 补齐同 `.env` 复跑后基线恰为 3 红，与分支完全对齐。提示：后续 worktree 对照须注意未跟踪 `.env` 不随 worktree 分发。

## 30 自称核验小结

| 30 自称 | 40 核验 |
|---------|---------|
| pytest 1174/3failed/1skipped · 3 红基线 | ✅ 复跑一致；worktree 对照坐实（比 stash 更严） |
| 新测 19 绿 | ✅ 总数差 19 交叉印证 + 单跑 34 绿（含 injection 既有） |
| ruff 67=基线零新增 | ✅ 双树各 67 |
| graph-compile 绿零图谱变更 | ✅ exit 0 · diff stat 零 graph yaml |
| 变异检验已做并还原 | ✅ 40 独立复做真 fail → 还原绿 |
| 态②夹具轨含回填前基线 | ✅ 前置 0 tracked 复核 · 测试内 pre 断言在 |
| B1 11 条处置完成 | ✅ 逐条在档，抽查成立 |

## 闸纪律

本帽未签任何 human_gate、未改实现码、未 push、未切 master；工作树唯一改动 = 本 invoke + task 自检结论/修订行（docs）。
