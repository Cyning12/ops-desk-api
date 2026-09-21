# invoke · 30-implement · session-summary-fallback

| 项 | 内容 |
|----|------|
| **时间** | 2026-09-22 |
| **帽** | 30（实现 · 不签任何人闸 · 图谱新签行留 00 代录位） |
| **task** | `docs/tasks/active/task_session_summary_fallback.md`（signed · HG-TASK-DRAFT/HG-AUDIT-R1=approved） |
| **SPEC** | `docs/spec/session-summary-fallback/SPEC-session-summary-fallback_v1.md`（signed · 48ce63e） |
| **分支** | `task/session-summary-fallback`（每次 commit 前 `git branch --show-current` 核验 · 禁止 master/main 直改 · 禁止 push） |

## 人工闸扫描（GATE_VERIFY · 首输出）

| human_gate_id | task表status | 用户/invoke声称 | 一致？ | blocks_30 | 30可开工？ |
|---------------|--------------|-----------------|--------|-----------|------------|
| HG-TASK-DRAFT | approved | approved | Y | 20-R1, 30 | ✅ |
| HG-AUDIT-R1 | approved | approved | Y | Y | ✅ |
| HG-GRAPH-MODULES | approved | approved | Y | —（新签义务随 30 落盘 · 留 00 代录位） | ✅ |
| HG-PILOT-OPSDESK-GLAYER | n/a | — | — | N | — |

reviews：`docs/harness/reviews/task_session_summary_fallback_audit_R1_20260922.md` 存在且 R1 通过 ✓
pre-30 invoke：{10, 20} 齐全 ✓（`invoke_20260922_10_*` / `invoke_20260922_20_*`）
机械辅助：`npx spec-wave verify --target . --task docs/tasks/active/task_session_summary_fallback.md` = **VERIFY: PASS**（真跑）

结论：**可进入读码/改码**。

## 实现纪要（D1–D5 · 实现序承 SPEC §8）

- **D5a 迁移先行**：`alembic/versions/20260922_session_summaries.py` 建 `ops_session_summaries`（字段 + 唯一约束 `(thread_id, chunk_hash)` + FK CASCADE `ops_lg_rag_threads` · 回滚注释含「off 态不读不写 · drop 安全」）；`app/db/models.py` 新增 `OpsSessionSummary` ORM 类。**可逆往返真跑**：upgrade → downgrade → re-upgrade 全绿。
- **D1 生成通路**：`app/ops/session/summary.py` `summarize_placeholders`（结构零改动 · 占位条内容替换 · `SUMMARY_TIMEOUT_S=60.0` extract 先例 · 单 chunk 降级 span `session_summary_degraded=N`）；summary 档（`TASK_TYPES`/`TASK_TIER_MODELS` + `"summary": None` · `OPS_LLM_TIER_SUMMARY_MODEL` 覆盖 · `use_run_context(task_type="summary", surface="lg_rag")` 归因继承）；prompt 资产 `session.summary.system.md` v1（无变量 · 「不得新增原文没有的事实」级指令）；摘要条三标记（`[历史摘要 · v1 · N 轮 · 模型:<model> · 有损压缩，细节以最近轮为准]`）。
- **D2 缓存**：key 铁律 `sha256(prompt_version + model + chunk turns canonical JSON)`；生成成功才写（唯一约束冲突 = 并发先写赢容忍）；写失败 log + 本次仍用摘要；读失败视同 miss；off 态零读零写；`ops_lg_rag_turns`/`ops_runs` 零改动（DB 行数断言钉死）。
- **D3 回退铁律**：`session_summary_enabled()` 逐字复刻 continuity.py:110-120 三件套（默认 false · 非法值回退 false + warning · env 重读即时生效）；off 三态对拍 + on 态全失败对拍**逐字节一致**双断言落 `tests/test_session_summary.py`。
- **D4 金样**：`evals/session/summary_fidelity_v1.yaml`（F0–F3 规则 + 3 金样夹具）↔ `tests/eval/test_session_summary_fidelity.py` 一一对应（F0 断言）；`evals/session/fidelity.py::check_summary_fidelity` 确定性校验函数（must_keep ⊆ 摘要 + must_not_add 逐项不含 + 空摘要假通过防线）；热路径零 LLM-as-judge。
- **D5b 图谱/文档**：`01_modules.md` db 行登记新表 + lg_rag/chat/llm 行备注 + 人签记录新行 **pending（留 00 代录位 · 30 不签闸）**；`./scripts/graph-compile.sh` 绿；`app/ops/session/README.md` 新建（env 表 + 故障语义）；assets README 变量表补 `session.summary.system v1 无变量`。

## 关键实现裁定（30 如实记录 · 非偏离）

1. **lg_rag↛session 边界 vs 钉死接线点的张力**：`tests/test_lg_rag_session_continuity.py:22-38` AST 边界测试禁止 lg_rag 包静态 import `app.ops.session`，而钉死契约要求摘要面接线在 `assemble_graph_messages_with_memory` 内、且新模块落 `app/ops/session/summary.py`。裁定：continuity 侧经 **importlib 运行期解析**（仅开关 on 时触达；off 态静态加载链零变化 · 边界测试全绿不动）；capability/manifest.py 已有 importlib 先例。SPEC 钉死的两个事实（模块位置 + 接线点）均保全。
2. **`assemble_graph_messages` 抽取共用内核**（`_assemble_messages_from_compressed`）：on 态路径复用同一转换循环，行为逐字节不变（纯函数面测试零改动全绿）；**`compress_window` 函数体 git 级零 diff**（与 master 逐字节比对 True）。
3. **graph.py +2 行**：两入口透传 `thread_id` 给装配面（缓存 key 唯一约束必需 · 属装配接线一部分）；生产 diff 白名单其余项全部吻合，无其它越界文件。
4. **`summarize_placeholders` 增补可选 kwargs**（`source_turns`/`max_full_turns`/`group_size`/`_provider`）：钉死签名 `(compressed, *, thread_id)` 原样成立可独立调用（source_turns 缺省直读 `ops_lg_rag_turns` · session→db 既有边 · 不 import lg_rag）；生产路径由装配面传入已加载历史避免二次读库。

## B1 旧测影响面处置回填（12 行 + 1 偏差行）

| # | 处置 | 实测 |
|---|------|------|
| 1 compress_window 三用例 | 回归 | 全绿（函数体零 diff 逐字节比对 True） |
| 2 装配/graph 集成 12 用例 | 回归 | 全绿（边界 AST 测试含在内 · importlib 方案不动它） |
| 3 memory_injection 23 用例 | 回归 | 全绿（摘要面 off 态跳过 · 插入点在记忆注入之前） |
| 4 session_continuity 2 用例 | 回归 | 全绿（chat 轨零改动） |
| 5 llm_routing unknown-task | 回归 | 全绿（`"summarize"` ≠ `"summary"` 语义不反转成立） |
| 6 llm_routing 其余 16 用例 | 回归+新增 | 全绿；summary 档断言新增于 `test_session_summary.py::TestSummaryTierRouting`（3 条） |
| 7 model_catalog 3 用例 | 回归 | 全绿 |
| 8 llm_usage 6 用例 | 回归+新增 | 全绿；归因断言新增（ContextVar 捕获 + 真 provider 落行 `task_type=summary` 双轨） |
| 9 llm_retry/circuit/providers | 回归 | 全绿（provider 包装层自动继承零改造） |
| 10 tests/eval 既有 9 文件 | 回归 | 全绿；新增 `evals/session/` 目录 + 实现文件 |
| 11 新增守护 | 新增 | `tests/test_session_summary.py`（32）+ `tests/eval/test_session_summary_fidelity.py`（4）+ prompt 资产锚点（入 `test_prompt_assets.py` 参数化） |
| 12 alembic 链 | 新增迁移 | `20260922_session_summaries` 挂 `20260922_memory_kind_preference` 后；既有迁移零改动 |
| **13（偏差）** `tests/test_prompt_assets.py` | **改编** | **B1 漏扫**：该文件 `EXPECTED_IDS` 集合等式断言（`test_registry_covers_nine_templates`）钉死模板恰 9 个——新增资产必然触发。处置：集合登记 +`session.summary.system: v1` · 用例改名 `test_registry_covers_declared_templates`（口径不变仍为集合等式）· 锚点参数化 +`("session.summary.system", "不得新增")`。改编理由：断言意图=「registry 与声明一致」，非「永为 9 个」；D1 钉死义务要求新资产进白名单 |

## 验证结果（全部真跑）

- `pytest tests` 全量：**1278 collected（基线 1239 + 新增 39）**；首轮 1274 passed + 基线环境性 3 红同款（`test_capability_http_adapter::test_urllib_transport_honors_explicit_capability_proxy` · `test_chat_ws` 两条）；次轮同 3 红 + `test_memory_embedding_backfill::test_reconcile_mismatch_marks_failed` 1 条——即父指令预判的偶发随机序 flaky，**隔离复跑 15 全绿 · 邻面切片复跑 28 全绿**（与本波改动面无交 · 复跑区分口径执行）
- `ruff check app tests`：**57 errors = 基线 57 零新增**（新增 4 处已修：B023×2/F401/C408/I001）
- alembic 可逆往返：upgrade head → downgrade -1 → upgrade head 全绿（真跑 · head=`20260922_session_summaries`）
- `./scripts/graph-compile.sh`：绿（done · 仅既有 warning 一条不咬 exit）
- `compress_window` git 级零 diff：与 master 函数体逐字节比对 **True**
- 生产 diff 白名单：`git diff master --stat` = models/model_catalog/continuity/graph(+2)/prompts/session/alembic/图谱/文档/测试/evals · 无越界文件

## 变异检验 ×3（做完即还原 · 还原后复绿）

| # | 变异 | 预期 | 实测 |
|---|------|------|------|
| ① 开关可检 | `session_summary_enabled` 恒 true | off 对拍必挂 | **7 failed**（off 三态+reread 全挂）→ 还原全绿 ✓ |
| ② 缓存可检 | `chunk_content_hash` 去掉内容哈希（只留 version+model） | 「同序号不同内容 miss」必挂 | **2 failed**（miss 单测 + hash 纪律单测全挂）→ 还原全绿 ✓（注：首跑变异只改 JSON 键名未真去内容 = 假变异未挂，重做真变异后挂 · 如实留痕） |
| ③ 降级可检 | 摘掉 span `session_summary_degraded` 标记 | 降级标记断言必挂 | **3 failed**（全失败对拍 + 部分降级 + 超时降级全挂——输出逐字节一致但缺标记仍被抓）→ 还原全绿 ✓ |

## 闸纪律

- 未签任何人闸：图谱人签记录新行写为 **pending（留 00 代录位 · 30 回写内容待 00 ratify）**。
- 未切 master/main · 未 push；commit 前逐次 `git branch --show-current` = `task/session-summary-fallback`。
- commit 分工：feat（app/alembic/tests/evals）与 docs（图谱 + 本 invoke）分开。
