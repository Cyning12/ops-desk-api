# Task 审查：query-coref-rewrite（R1）

> **审查帽**：20-task-audit（书面审 · 不改 task 实质内容 · 不动 app/ · 不代签人工闸）
> **被审文件**：`docs/tasks/active/task_query_coref_rewrite.md`（draft · HG-AUDIT-R1=**pending**）
> **对照真值**：SPEC `docs/spec/query-coref-rewrite/SPEC-query-coref-rewrite_v0.md`（signed · HG-SPEC-SIGNOFF=approved 2026-10-19）· SPEC 审查文 `docs/harness/reviews/spec_query-coref-rewrite_audit_R1_20261019.md`（pass · N1–N3）
> **审查日期**：2026-10-19
> **审查方式**：通读 task/SPEC/SPEC 审查文全文 + read/grep 实测全部新增代码锚点（不接受 task 自述）

## 结论摘要

- **内容审查：pass（通过）** —— 范围/非范围/验收/failure_paths/思考轮/人工闸六维闭合；SPEC R1 审查 N1–N3 三条非阻塞观察均已如实吸收落位，无越范围、无缩水。
- **流程闸：HG-AUDIT-R1=pending（符合预期，必须 pending）** —— 本帽不代签；维护者签闸清单见文末。HG-AUDIT-R1 签为 approved 之前，30 拒改码。
- **阻塞项：无。非阻塞观察 2 条（O1/O2，不构成退回理由）。**

---

## 1. N1–N3 吸收核对（对照 SPEC 审查文 §4 逐条）

| 观察 | SPEC 审查文原要求 | task 落点 | 判定 |
|---|---|---|---|
| N1 · rewrite 档键 | `TASK_TIER_MODELS` 增 `"rewrite": None`（仿 summary 档先例）；缺键走 unknown_task 告警 | D4 **三处同增**：`TASK_TYPES`（:119）+ `TASK_TIER_MODELS`（:123-132）+ `TASK_TIER_FALLBACKS`（:215-223 增 `"rewrite": ()`）；FP-8 + TC7 钉效果断言 | ✅ 如实落位且**超出 N1 最低要求地闭合了同源识别面**（`resolve_fallback_chain` :239 与 `budget.py` :202/:269 均以 `TASK_TYPES` 成员判定，实测确认三处同增必要且充分） |
| N2 · 重写与召回顺序 | SPEC 未钉，留 task 决策并在验收里钉一条 | D1 裁定**先重写后召回**并钉死（impl 入口 :428-441 两分支之前一次性算出 `resolved_query`，召回 `recall_with_vector(..., query, ...)`（:454-457）统一吃改写结果）；FP-9 + TC8 调用序断言；非范围增「禁颠倒」 | ✅ 如实落位，理由成立（召回问句同受指代困扰；召回为瞬时不落盘面，不违 D3 审计口径）；顺序同时进范围与非范围，互锁 |
| N3 · 「明显非问句」确定式化 | 判定规则写成确定式（长度上限数值 + 首行/空白规则），避免 30 自由发挥 | D2 确定式三规则：①strip 后空串 ②含 `
`/``（拒多行，不取首行截断）③strip 后 >512 字符；明示「不以问号结尾作判据」「30 不得另加启发式」；FP-10 + TC9（含恰 512 接受的闭区间边界） | ✅ 如实落位，三条均机器可判 |

**裁定：N1–N3 吸收无失真、无遗漏、无私自扩面。**

## 2. 核对表（对照 SPEC 五维 + 闸表）

| 维度 | 判定 | 依据 |
|---|---|---|
| 范围越/缩 SPEC | ✅ 不越不缩 | D1–D3 承 SPEC §2 原样；D4 为 SPEC D2「走 resolve_task_model('rewrite') 档」蕴含的实现面工作项（SPEC 审查文 N1 原话确认「SPEC 未点名该文件但 D2 已蕴含」），非越范围 |
| 非范围 | ✅ 原样继承 | task :99-104 与 SPEC §3 六条**逐字一致**；task 级补充三条（不扩 CACHEABLE_TASK_TYPES / 禁颠倒 N2 顺序 / 本阶段零 app/ 改码）均为纪律性收口，不改 SPEC 实质 |
| 验收可机器化 | ✅ | TC1–TC12 全部假 LLM 注入/夹具/零 diff 对拍机断，无人工判断项；不打真模型；TC9 边界（恰 512 接受）钉死闭区间口径 |
| 验收↔failure_paths 映射 | ✅ 闭合 | FP-1→TC1 · FP-2→TC4 · FP-3→TC3 · FP-4→TC2 · FP-5→TC6 · FP-6→TC5 · FP-7→TC1/TC11 · FP-8→TC7 · FP-9→TC8 · FP-10→TC9 · FP-11→闸纪律（流程面，无需 TC）；SPEC FP-1~FP-7 原样继承且语义一致（task FP-3 增补 span 细节、FP-5 增补 warning，均与 SPEC D2 自洽） |
| test_strategy/failure_paths 完备性 | ✅ | `test_strategy=required` 承 SPEC 并增补 N1–N3 三条断言；行为变更类 task 的 K7「旧测 grep 影响面」项已含（TC12，枚举 9 个既有测试文件逐文件处置 + 枚举外默认保持绿） |
| 思考轮 R0–R5 | ✅ 闭合 | 控制表齐 + `actual_last_round=R5` + R0–R5 各轮小节回填闭合；early_stop 全 false 合理（草稿未经审不早停）；residual_risks 如实挂账（金样覆盖靠 golden-eval、continue 场景仅一条、HG-AUDIT-R1 pending） |
| 人工闸表 | ✅ | HG-SPEC-SIGNOFF=approved **有依据**（SPEC signed + R1 pass 审查文）；**HG-AUDIT-R1=pending（符合本阶段必须 pending 的要求）**；HG-GRAPH-MODULES=approved 有 `docs/_tech_graph/l1/01_modules.md` 闸登记表在册依据（:63 起，`lg_rag` 行 :65 签收）；graph_change_layer=none 与 freeze 口径（SSE 帧/请求体零变化）表述正确 |
| 元信息齐备 | ✅ | task_slug / git_branch / spec / test_strategy(_note) / code_quality_bar / graph_change_layer / graph_delta(_note) / review_hat=20 / required_invoke_hats=10,20,30,40 / freeze_id / 建议序 1/5 均在表 |

## 3. 锚点抽查（read/grep 实测 · 26 处全部一致，0 漂移）

task 依赖节锚点（承 R1 审查 14/14）之外，本帽对 task **新增引用面**全部实测：

| # | task 引用 | 实测结果 |
|---|---|---|
| 1 | `app/llm/model_catalog.py:119` `TASK_TYPES` tuple | ✅ 一致（:119 原样命中，现有 5 键 answer/grader/extract/structured/summary） |
| 2 | `model_catalog.py:123-132` `TASK_TIER_MODELS` · summary 档先例 :128-131 | ✅ 一致（def :123-132；summary 档三行注释 :128-130 + 键 :131 原样命中） |
| 3 | `model_catalog.py:156-158` unknown_task 告警分支 | ✅ 一致（:157 `"unknown llm task_type=%r; ..."` 字样与 TC7 caplog 断言匹配，:158 返回 `(None, "unknown_task")`） |
| 4 | `model_catalog.py:183-186` 档默认 None → `(None, "default")` | ✅ 一致（:183-186 精确） |
| 5 | `model_catalog.py:215-223` `TASK_TIER_FALLBACKS`（summary 档 :222 先例） | ✅ 一致（def :215-223；`"summary": ()` 正在 :222） |
| 6 | `model_catalog.py:239` `resolve_fallback_chain` 以 `TASK_TYPES` 识别 | ✅ 一致（:239 `if task not in TASK_TYPES` → 空链明确失败） |
| 7 | `app/llm/budget.py:202/:269` 任务级计数键同源（`TASK_TYPES`） | ✅ 一致（:202 `task in TASK_TYPES` 读计数 · :269 `if task in TASK_TYPES` 累加） |
| 8 | `continuity.py:147-162` `session_summary_enabled` 开关先例 | ✅ 一致（def :147-162，strip/lower + `_TRUTHY`/`_FALSY` + 非法值 warning 回退 false，D2 所仿先例成立） |
| 9 | `continuity.py:401-514` impl · :428-441 两条装配分支 | ✅ 一致（def :401，body 至 :514；:428 `if session_summary_enabled()` / :436 `else` 两分支精确） |
| 10 | `continuity.py:454-457` `recall_with_vector(..., query, ...)` | ✅ 一致（:454 调用起，:457 第三实参确为 `query` 变量——N2 钉死对象属实） |
| 11 | `continuity.py:82-98` `_assemble_messages_from_compressed` 末位 :97 追加 | ✅ 一致（:97 `messages.append(HumanMessage(content=query))`） |
| 12 | `continuity.py:546-602` `assemble_graph_messages_with_memory` 包装面 | ✅ 一致（def :546，文件终于 :602） |
| 13 | `continuity.py:44-79` `compress_window`（6/2 常量 :40-41） | ✅ 一致 |
| 14 | `graph.py:199-205` `_astream_with_tracing` 统一经装配 | ✅ 一致（:199-205 `assemble_graph_messages_with_memory(query, history_turns, ...)`） |
| 15 | `multi/nodes.py:1106` planner 取词 | ✅ 一致（`query = _last_user_text(state["messages"])`） |
| 16 | `multi/nodes.py:1163-1170` planner prompt 两条无历史 | ✅ 一致（system(catalog)+user(query) 两条） |
| 17 | `multi/nodes.py:1432-1435` rag 工人不传 history | ✅ 一致（仅 `result["input"]` + thread_id） |
| 18 | `multi/nodes.py:2035-2043` / :2107 aggregator | ✅ 一致（`_aggregator_plain_messages` :2035-2043；aggregator_node :2107 取原文） |
| 19 | `app/ops/lg_rag/nodes.py:203-240` `rewrite_node`（非范围对象） | ✅ 一致（router 子图内部回环，写 `state.current_query`，与装配层重写各司其职） |
| 20 | `thread_store.py:63-90` `persist_thread_turns` 记原文 :82 | ✅ 一致（:82 `content=query`） |
| 21 | `sse_stream.py:334-341` `run.start` payload.query :340 | ✅ 一致（:340 `"query": query`） |
| 22 | `router.py:339-342` continue 草稿拼接 | ✅ 一致（:342 `query = f"{body.query}\n\n[继续回复·既有草稿]\n{partial}"`） |
| 23 | `docs/_tech_graph/l1/01_modules.md` 闸登记表 :63 起 · `lg_rag` :65 在册 | ✅ 一致（:63 起 HG-GRAPH-MODULES 登记连续；:65「新增 `lg_rag` 一级模块」approved） |
| 24 | TC8 引用 `memory_facts_vector_recall_enabled` / `recall_with_vector` | ✅ 存在（`app/ops/memory/service.py:384` / :593） |
| 25 | TC12 枚举 9 个既有测试文件 + eval 1 个 | ✅ 全部存在（`tests/test_lg_rag_session_continuity.py` / `test_session_summary.py` / `test_memory_injection.py` / `test_memory_episode_recall.py` / `test_memory_vector_p1.py` / `test_memory_service_db.py` / `test_input_isolation_wiring.py` / `test_memory_extract_p1.py` / `tests/eval/test_input_isolation.py`） |
| 26 | 必读 6 `docs/tasks/done/task_session_summary_fallback.md` 先例 | ✅ 存在 |

另实测：task 自述当前分支 `docs/spec-followups-2026-10-19`（30 开工前自 master 切 `task/query-coref-rewrite`）与 `git branch --show-current` 一致。

**统计：一致 26 / 漂移 0。**

## 4. 阻塞项

无。

## 5. 非阻塞观察（供 30 参考，不构成退回理由）

1. **O1 · TC12 内 `tests/test_session_summary.py` 行号标注**：task 注「:492-695 对拍簇」——实测 off 态逐字节对拍主簇在 :89-229（未设/非法值/on 态全失败三段），:492-695 属 on 态缓存/库行对拍区（:500 `_shape(out2) == _shape(out1)`）。task 已自述「行号 30 按实校正」，30 红测先行前按实校正即可。
2. **O2 · TC7 source 枚举口径**：TC7 断言 `resolve_task_model('rewrite')` source ∈ {default, env_tier, strategy_pack}。实测 :149-151 source 全词表另含 explicit/rag_grader_model/tier_default——explicit 无调用面、rag_grader_model 为 grader 专属兼容链、tier_default 仅在配档后出现，TC7 枚举对 rewrite 档未配/灰度两态已精确，无歧义。仅供 30 知悉全词表。

## 6. 审查边界声明

本帽未改 task/SPEC 实质内容，未改 `app/` / `tests/`，未执行 git 分支操作，未代签任何人工闸；唯一写入面为本审查文。

## 维护者签闸（20 后 · 30 前）

- [ ] 已读 R1 审查结论
- [ ] 在 task 人工闸表将 HG-AUDIT-R1 改为 approved（维护者 · 日期）
- [ ] commit task 文档或确认已签
- [ ] 再下发 Harness 30 Prompt

30 Agent 将以 task 表为准；pending 时必须拒开工（见 TEMPLATE_30_gate_stop.md）。

---

## 修订记录

| 日期 | 说明 |
|---|---|
| 2026-10-19 | R1：对照 SPEC（signed）+ SPEC R1 审查文六维核对闭合；N1–N3 吸收逐条核实无失真；锚点 26 处实测全一致（0 漂移）；判定 **pass**；HG-AUDIT-R1=pending 待维护者签 |
