# 合并前审查（40 帽）：query-coref-rewrite

> **审查帽**：Harness 40（合并前代码审查 · 书面审 · 不改实现码 / 不改 task/SPEC/闸表 · 唯一写入面=本文）
> **被审 diff**：`d8b787d..task/query-coref-rewrite`（2 提交：`4b36b3b` 实现 9 文件 +694/-6 · `cb80f8f` invoke 实录 +50；合计 10 文件 +744/-6）
> **对照真值**：task `docs/tasks/active/task_query_coref_rewrite.md`（D1–D4 / FP-1~FP-11 / TC1–TC12 / 非范围 / freeze_id）· SPEC `docs/spec/query-coref-rewrite/SPEC-query-coref-rewrite_v0.md`（signed）· R1 审查 `docs/harness/reviews/task_query_coref_rewrite_audit_R1_20261019.md`（pass · O1/O2）
> **审查日期**：2026-10-19
> **审查方式**：逐行读全量 diff（889 行）+ 对照 task/SPEC/R1 审查逐面核验 + 关键锚点 grep 实测 + 本机复跑（CI 等价 park .env 跑法）

## 结论摘要

- **结论：approve（可合并）** —— 阻塞项 0。
- D1–D4 四面与 task 口径逐行一致；禁区（SSE 帧/请求体/event_type/路由/表）零触碰；01_modules.md 仅 lg_rag 行尾追加一段备注（graph_change_layer=none 承诺成立）；38 例新测为真断言，TC↔测试映射闭合；本机复跑新测 38/38 绿、ruff（仓内 venv 0.15.21）全绿、graph-compile EXIT=0、TC12 枚举回归面 188 项绿。
- 非阻塞观察 4 条（O1–O4，均不构成退回理由），residual_risks 4 条逐条裁定**均不阻塞**。

---

## 1. 逐行 diff 核验（D1–D4 + env 非法值路径）

### D1 · 插入位置与「先重写后召回」（task D1 / FP-9 / TC8）——✅ 一致

- `app/ops/lg_rag/continuity.py:440` `resolved_query = await maybe_rewrite_query(query, history_turns)` 位于 impl 入口、`:441` `if session_summary_enabled()` 分支**之前**——确在两条装配分支（on `:443` / off `:451`）之前一次性算出，两分支统一吃 `resolved_query`。
- 记忆向量召回 `:467-470` `recall_with_vector(tenant_id, user_id, resolved_query, ...)` 第三实参已换为 `resolved_query`——N2 钉死顺序「先重写后召回」落实，未颠倒。
- 生效面核验：`graph.py:184` `_astream_with_tracing`（`:199` 调装配）被 basic `:249` / router `:286` / supervisor（`multi/graph.py:146`）三模式共用——三模式统一生效成立（另 invoke 路径 `graph.py:166` `_ainvoke_with_tracing` 同经装配，口径一致）。

### D2 · 三规则边界 / 开关 / 降级（task D2 / FP-3 / FP-5 / FP-10）——✅ 一致

- `query_rewrite.py:76-91` `_validate_rewrite`：strip 后空串 → 非法；含 `\n` 或 `\r` → 整体非法（**不截首行**，与钉死一致）；strip 后 `> 512` → 非法。闭区间边界正确：恰 512 接受（`len(text) > QUERY_REWRITE_MAX_CHARS` 不含等号，TC9 边界测 `"问"*512` 接受 / `*513` 拒双向往返钉死）。未以问号作判据、未另加启发式。
- 开关 `:53-67` `query_rewrite_enabled`：strip/lower + truthy/falsy 集合 + 非法值 warning 回退 False，逐条仿 `session_summary_enabled` 先例；env 每次重读无缓存。非法值路径有 TC6 caplog + 零 diff 双重断言。
- 降级：LLM 异常 / `asyncio.wait_for` 超时（30s，30 自选值已在 invoke 偏离节如实披露）/ 非法输出三路均静默降级原文 + span `query_rewrite_applied=false` + `query_rewrite_fallback=true`；成功路记 bool + src/dst 长度、不记改写全文——与 D3 可观测口径一致。

### D3 · 落盘 / run.start 记原文（task D3 / FP-6 / TC5）——✅ 一致（零触碰式满足）

- diff 全文不含 `thread_store.py` / `sse_stream.py` / `router.py`——双写口径以「装配层以下零感知」方式保持，无双写 veto 风险。
- TC5 经真实 HTTP `POST /api/ops/lg-rag/stream` 全链验证：`run.start` `payload.query` == 原文、`persist_thread_turns` 桩实收原文，同时同请求装配末位 == 改写文（证明重写确生效）——双写口径不漂移断言为真。

### D4 · 档键三处同增（task D4 / FP-8 / TC7）——✅ 齐备

- `app/llm/model_catalog.py`：`TASK_TYPES` +`"rewrite"`（:119）；`TASK_TIER_MODELS` `"rewrite": None`（:132-135，注释仿 summary 档先例）；`TASK_TIER_FALLBACKS` `"rewrite": ()`（:229，背景档注释同步枚举 rewrite）。三处同增齐备，`resolve_fallback_chain`/`budget.py` 同源识别面闭合；TC7 断言无 unknown_task 告警、`(None,"default")`、`OPS_LLM_TIER_REWRITE_MODEL`→`env_tier`、空 tuple 全覆盖。
- 30 自选 `QUERY_REWRITE_TIMEOUT_S=30.0` 与「TC10 不动闸台账表」两项偏离均在 invoke「偏离与自选」节如实落盘，披露纪律合规。

## 2. 禁区核验（freeze_id / graph_change_layer=none）——✅ 全部成立

| 禁区 | 证据 | 判定 |
|---|---|---|
| SSE 帧 / 请求体零变化 | diff 文件清单不含 `sse_stream.py` / `router.py` / `schemas`；TC5 对真实 SSE 响应解析 `run.start` 帧结构未变 | ✅ |
| 零新 event_type / 路由 / 表 | 10 文件无路由注册、无 alembic 迁移、无 db models；`graph.py`/`multi/graph.py` 零改动 | ✅ |
| 01_modules.md 仅一句备注 | word-diff 实测：仅 lg_rag 行尾追加一段 `**query-coref-rewrite（2026-10-19 …）**：…` 备注（含「不新增一级模块/路由/表/SSE 事件类型 · 不增 implementedBy」自述）；无结构变更 | ✅ |
| graph-compile | 本机复跑 EXIT=0（9 graphs OK · mermaid normalize check ok）——freeze 零 diff | ✅ |

## 3. 测试质量与 TC↔映射闭合

`tests/test_lg_rag_query_rewrite.py`（504 行 · 38 例）为**真断言**非走过场：span 字典逐键等值断言、LLM 调用计数 ==0/==1、调用序 `["rewrite","recall"]` 钉死、`_shape` 类型+content 逐字节对拍、真实 HTTP SSE 解析对拍 run.start 原文、512/513 双向往返边界。

| TC | 落点 | 判定 |
|---|---|---|
| TC1 默认关三模式零 diff | `test_tc1_off_three_modes_zero_diff`（3 模式 × 4 env 态 = 12 例 · _FakeGraph 捕获入图 payload 对拍纯装配基线 + 零调用零 span） | ✅ |
| TC2 金样三类 + continue | `test_tc2_golden_coref_rewrite`（7 条金样参数化：指代×2/省略×2/时间锚定×2/continue×1）+ 装配末位 + planner/aggregator 实收两例 | ✅（形态级证明，见 O2/O3） |
| TC3 失败降级 | 异常 / 超时（monkeypatch 缩 timeout 真等 0.5s）/ 降级装配逐字节=off 三例 | ✅ |
| TC4 首轮短路 | None/[] 两例 · 调用计数 0 · 零 span | ✅ |
| TC5 落盘原文 | 真实 HTTP 全链（client fixture + override_auth）· run.start/persist 双原文 + 同请求装配已改写 | ✅ |
| TC6 env 非法值 | caplog 警告文案 + 行为零 diff + 零调用 | ✅ |
| TC7 档键在册 | 三处在册 + 无 unknown_task 告警 + env_tier 覆盖（取目录实模型） | ✅ |
| TC8 先重写后召回 | recall 桩实收 ==resolved_query + order==["rewrite","recall"] | ✅ |
| TC9 三规则 + 边界 | 5 形态参数化（空/strip 空/\n/\r/513）+ 恰 512 接受 + 前后空白 strip 规范化 | ✅ |
| TC10 图谱守护 | 本机复跑 graph-compile EXIT=0；01_modules.md 实测仅一段备注 | ✅ |
| TC11 全量 + ruff | 本机复跑：新测 38/38；ruff 仓内 venv 全绿；invoke 录全量 4 failed/1901 passed（失败集与基线逐名一致） | ✅ |
| TC12 旧测影响面 | 本机复跑枚举 8 文件 188 项全绿；vector/db 两文件 21 passed + 1 failed（环境性，见复跑节） | ✅ |

**红测先行声称**：invoke 录「先写 38 例 → ImportError 红 → 再实现 → 一次全绿」。git 史上测试与实现同处 `4b36b3b` 单提交，无法从历史独立证红；但声称机制可信（测试文件 import `app.ops.lg_rag.query_rewrite`，实现前必然 ImportError），invoke 实录口径自洽。**采信，标注为自证性质**。

**R1 审查 O1/O2 吸收**：invoke 专节实录——O1 按实校正 off 态对拍主簇行号（:89-229）并沿用其手法；O2 知会 source 全词表但未私扩 TC7 三值断言。**吸收合规，无 silent 扩**。

## 4. 本机复跑实录（CI 等价 park .env 跑法）

| 项 | 命令 | 结果 |
|---|---|---|
| 新测 | `.venv/bin/python -m pytest tests/test_lg_rag_query_rewrite.py -q` | **38 passed**（0.24s） |
| ruff | `.venv/bin/ruff check app tests`（仓内 pin 0.15.21） | **All checks passed** |
| graph-compile | `./scripts/graph-compile.sh` | **EXIT=0**（9 graphs OK） |
| TC12 回归面 | session_continuity / session_summary / memory_injection / memory_episode_recall / input_isolation_wiring / memory_extract_p1 / eval/input_isolation / prompt_assets | **188 passed** |
| vector/db 面 | test_memory_vector_p1 + test_memory_service_db | 21 passed / **1 failed**：`test_embedder_failure_degrades_with_marker` 缺 `SILICONFLOW_API_KEY`（park .env 副作用 · 正落在 invoke 预存失败集「embedder flaky」内 · 基线 d8b787d 同法同失败 · 与本 diff 零相关） |

环境说明：系统 `ruff`（miniconda 0.9.10）对未触及的预存文件报 12 项 UP038，属工具链版本差，仓内 venv 与 CI 口径全绿，不计入本 diff。本机 .env 泄入致 16 项 capability/strategy 预存失败一事，30 已在基线同环境实证非本 diff 引入，本帽复跑采 park 跑法规避，结论一致。

## 5. residual_risks 裁定（30 挂账四条）

| # | 挂账 | 裁定 |
|---|---|---|
| 1 | 真连 LLM 重写质量未实证 | **不阻塞**。task/SPEC 口径即「全假 LLM 机断、不打真模型」；默认关 + 失败降级原文 + 金样断言三重保险。建议：灰度开启前做一次金样真连抽查（可并入下游 golden-eval 加强，承 SPEC R4 挂账） |
| 2 | rewrite 档默认 None 走 `ops_llm_model` | **不阻塞**。此即 task D2 钉死的既定语义（档未配 → `(None,"default")` 沿用现网默认），非风险是设计；灰度期 `OPS_LLM_TIER_REWRITE_MODEL` 零改码调档 |
| 3 | 金样仅中文 7 条 | **不阻塞**。SPEC §7 / task R4 已挂账（覆盖率靠 golden-eval 加强）；英文/混合语种属非范围 |
| 4 | .env 泄入 `os.environ` 致 16 项预存失败 | **不阻塞**。基线同环境同失败集已实证；本帽 park 跑法复跑全绿旁证。.env 治理另立任务合理，不挂本 task |

## 6. 非阻塞观察（O1–O4，不构成退回理由）

1. **O1 · 重写输入为原始历史窗而非「压缩后历史」**：SPEC/task D1 措辞为「压缩后历史 turns + 原文 query」；实现 `_build_user_content`（`query_rewrite.py:94-101`）取 `history_turns[-6:]` 原始轮次（`_HISTORY_WINDOW=6` 与默认 max_full_turns 对齐）。impl 入口单点只有原始 turns，取压缩态需二次压缩，实现选择可辩护且重写质量更优；但语义差客观存在：**窗口（默认 6 轮）之前的历史内容虽经压缩摘要进入 planner 视野，重写器看不到**，超窗指代不消解。默认关 + golden-eval 后续加强可覆盖，建议经验沉淀时记录此口径差。
2. **O2 · TC2 planner/aggregator 为形态级证明**：直接对装配输出调 `_last_user_text` / `_aggregator_plain_messages`，非全 supervisor 图执行。planner/aggregator 取词代码属非范围零改动，形态级证明对「消耗面天然覆盖」口径充分；若要端到端坐实，留待真连灰度抽查（与风险 1 合并）。
3. **O3 · 「continue 场景」金样未走草稿拼接链路**：该金样为 4 轮历史 + 指代 query，未实际经 `router.py:339-342` 拼接（本波不改拼接，仅记顺序事实）。满足 task「金样含一条 continue 场景」字面口径；拼接后文本含 `[继续回复·既有草稿]` 标记进重写 prompt 的真实交互未覆盖，留灰度抽查。
4. **O4 · 重写前置 setup 在 try 之外**：`query_rewrite.py:115-117` `get_llm_provider()` / `_resolve_model()` / `render()` 任一抛错会穿过装配层（不在降级 try 内）。实际爆半径为零：provider 工厂若坏主链路必坏（同工厂）；`render` 资产由 `test_prompt_assets.py` 集合等式守护。FP-3 枚举的失败面（LLM 异常/超时/非法输出）全部在 try 内，口径无缺口；可选加固（setup 一并入 try）留后续，不阻塞。

## 7. 审查边界声明

本帽未改 `app/` / `tests/` / task / SPEC / 闸表 / 图谱任何字节；复跑产生的 `.env` park/restore 已复原（跑前后 `ls .env` 核对一致）；唯一写入面为本审查文。

## 合并建议清单（维护者）

- [x] 40 审查结论：**approve**（阻塞 0 · 非阻塞 O1–O4 · residual 4 条均不阻塞）
- [ ] PR 合并前 CI 绿（仓内口径：pytest + ruff + graph-compile）
- [ ] 合并后 CLOSE task 并归档；O1/O3 口径差随经验沉淀落 invoke 补记
- [ ] 下游棒：memory-injection-consumer（建议序 2/5 · 另 SPEC/task）

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-10-19 | 40 合并前审查：逐行 diff（889 行）+ 四面口径核验 + 禁区核验 + 本机复跑（38 新测绿 · ruff 绿 · graph-compile EXIT=0 · 回归面 188 绿）；结论 **approve**；非阻塞 O1–O4；residual_risks 4 条裁定均不阻塞 |
