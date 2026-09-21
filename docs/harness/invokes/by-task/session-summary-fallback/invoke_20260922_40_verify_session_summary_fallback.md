# invoke · 40-verify · session-summary-fallback

| 项 | 内容 |
|----|------|
| **时间** | 2026-09-22 |
| **帽** | 40（核验 · 不签任何人闸 · 不改实现码 · 只写过程文档） |
| **task** | `docs/tasks/active/task_session_summary_fallback.md`（signed） |
| **验收对象** | 30 交付 = `233165d`（feat）+ `6b1601e`（图谱回写+30 invoke）+ `772d0bd`（图谱 ratify 00 代录 approved） |
| **分支** | `task/session-summary-fallback`（核验全程未切 master/main · 未 push · 基线对照走 git worktree） |

## 总判定：**PASS · 验收 26/26 通过**（全部真跑亲核 · 非轻信 30 自称）

## 一、全量 pytest + 基线红对照（真跑）

- 分支全量 `pytest tests`：**1278 collected（基线 1239 + 新增 39 · 与 30 自称一致）→ 1274 passed + 3 failed + 1 skipped**。
- 3 红 = `test_capability_http_adapter::test_urllib_transport_honors_explicit_capability_proxy` · `test_chat_ws::test_ws_message_streams_events` · `test_chat_ws::test_ws_second_message_while_active_rejected`。
- **基线对照**：git worktree @ `95c5279`（origin/master · PR #158 merge）+ 补同 `.env`，同 3 用例**原样复现全红**（3 failed in 0.81s）——环境性既有红，与本波无关。
- 本轮**未复现** `memory_backfill` flaky（30 次轮曾遇 1 条并隔离复跑区分 · 本轮一次通过，无需再区分）。

## 二、双对拍亲核（上线前提两条 · 读实现 + 实跑）

- **读实现**（`tests/test_session_summary.py`）：对拍是真断言非空壳——`_shape()` 取 `(消息类型, content)` 元组序列做**逐字节相等**比较；off 三态（未设 :91 / falsy×4 参数化 :108 / 非法值+warning :122）+ env 重读 :141 + on 态全失败 :167 各断言独立。
- **两路径都走到**：on 全失败用例 `provider.calls == 2`（两占位 chunk 各一次真调用计数）证明**确实进了摘要面**而非没走到；`obs["spans"]` 断言 `session_summary_degraded=2` 区分「走了但全降级」与「根本没走」。
- **实跑**：`-k "off_unset or off_falsy or off_invalid or reread or all_llm_failures or missing_thread_id or prompt_asset_failure"` → **10 passed**；全量 32 passed（该文件）。

## 三、零 diff / 白名单亲核（git 级）

- `compress_window` 函数体：AST 提取 HEAD vs origin/master **逐字节一致 True**（文件级 diff 非空属预期——装配层接线 + 开关 + importlib 面全在白名单内）。
- `assemble_graph_messages` 重构为共用内核抽取（`_assemble_messages_from_compressed`），调用序不变，纯函数面旧测零改动全绿（B1 #1/#2 回归属实）。
- `graph.py` diff = **恰好 +2 行**（`_ainvoke_with_tracing` / `_astream_with_tracing` 透传 `thread_id`），白名单外零越界。
- `git diff origin/master --stat` 26 文件全部落白名单（models / model_catalog / continuity / graph(+2) / prompts / session / alembic / 图谱 / 文档 / tests / evals）。
- **lg_rag↛session AST 边界**：`app/ops/lg_rag/` 内**零静态 import** `app.ops.session`（grep 实证仅 docstring 提及 + `importlib.import_module` 运行期解析）；边界测试在全量中绿。

## 四、alembic 往返亲跑（dev 库 · 终态回 head · 数据零触碰）

- `alembic downgrade -1` → 活库核验 `to_regclass('ops_session_summaries') = None`（真 drop）。
- `alembic upgrade head` → 活库核验：表回建 · 唯一约束 `uq_ops_session_summaries_thread_chunk` 在 · FK `confdeltype='c'`（CASCADE）在 · 9 列齐全。
- 终态 `alembic current` = `20260922_session_summaries (head)`；迁移注释含「off 态不读不写 · drop 安全」✓；`OpsSessionSummary` ORM 与迁移一致（models.py:347+）。

## 五、ruff / graph-compile

- `ruff check app tests` = **57 errors**；基线 worktree 同口径 = **57 errors** → **零新增**。
- `./scripts/graph-compile.sh` exit 0（仅既有 warning 一条不咬 exit）；跑后 `graph.json` 漂移仅 `generated_at` 时间戳，**已还原**，工作树净。

## 六、变异检验复做 ①（开关可检 · 亲做）

- 变异：`session_summary_enabled` 插 `if True: return True`（恒 true）。
- 结果：off 对拍 **恰好 7 failed**（off_unset / off_falsy×4 / off_invalid / reread）——与 30 自称的 7 挂一致，断言确实能抓开关失效。
- 还原（`git checkout`）→ 该文件 **32 passed** → `git status` 净（无 MUTANT 残留）。
- ② 缓存可检 / ③ 降级可检：采用 30 invoke 留痕（2 failed 含假变异重做如实记录 / 3 failed），本帽未重复执行（父指令仅要求复做 1 条）。

## 七、B1 抽核（5 行 · 含偏差回填行）

| # | 抽核 | 实测 |
|---|------|------|
| 1 compress_window 三用例 | `test_lg_rag_session_continuity.py` 含在 113 passed 内 + 函数体逐字节比对 True | 属实 |
| 3 memory_injection 23 用例 | 同批全绿（off 态跳过摘要面） | 属实 |
| 5/6 llm_routing | 17 用例全绿；`"summarize"`≠`"summary"` 语义不反转；summary 档断言新增于 TestSummaryTierRouting（4 条） | 属实 |
| 8 llm_usage | 6 用例全绿 + 归因断言新增（ContextVar + 真 provider 落行 task_type=summary） | 属实 |
| **13（偏差）test_prompt_assets** | **改编属实且口径不变**：`EXPECTED_IDS` 集合等式仍集合等式（+登记 `session.summary.system: v1`）· 用例改名 `test_registry_covers_declared_templates` · 锚点参数化 +「不得新增」· 留痕注释指回 30 invoke | 属实（B1 漏扫如实回填） |

## 八、金样一一对应亲核（D4）

- `evals/session/summary_fidelity_v1.yaml`（F0–F3 规则 + G1–G3 金样）↔ `tests/eval/test_session_summary_fidelity.py`（4 用例 `@rule("F0".."F3")` 装饰器登记）——F0 用例断言 `declared == IMPLEMENTED` 集合等式守一一对应。
- 正反双断言齐全：F1 must_keep ⊆ 摘要 + 删 sentinel 必挂反向对照；F2 must_not_add 逐项不含 + 掺入必挂 + **空摘要必判违规**（假通过防线）；F3 结构断言（零 `roles=` 占位残留 + v1/模型:/有损三标记 + 装配产物过同一 `check_summary_fidelity`）。
- 热路径零 LLM-as-judge：`evals/session/fidelity.py` 确定性 token 断言，CI 用夹具 turns + 录制摘要。

## 九、图谱 ratify 核对（772d0bd）

- `01_modules.md`：db 行登记 `ops_session_summaries`（唯一约束/FK CASCADE/migration head/drop 安全）✓；lg_rag/chat/llm 三行备注各就其位 ✓；HG-GRAPH-MODULES 人签记录新行 = **approved（00 代录 · 30 回写内容 00 ratify 2026-09-22）** ✓；无新增一级模块/路由/SSE 事件（偏离回炉条款未触发）。

## 十、文档核对（D5）

- `app/ops/session/README.md`（新建）：env 表含 `SESSION_SUMMARY_ENABLED`（默认 false/非法值回退）+ `OPS_LLM_TIER_SUMMARY_MODEL`；故障语义表含降级占位 + span `session_summary_degraded` + 灰度纪律 ✓。
- `app/ops/prompts/assets/README.md` 变量表 +`session.summary.system v1 无变量` ✓。

## 闸纪律（40 自检）

- 未签任何人闸 · 未改实现码（唯一临时改动 = 变异检验①，做完即还原并留痕）· 未切 master/main（基线对照走 worktree `/tmp/ops-desk-baseline-95c5279`）· 未 push。
- 本 commit 仅 docs（本 invoke + task 自检结论/修订行）。
