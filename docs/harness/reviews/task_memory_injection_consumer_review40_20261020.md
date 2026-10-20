# 合并前审查（40 帽）：memory-injection-consumer

> **审查帽**：Harness 40（合并前代码审查 · 书面审 · 不改实现码 / 不改 task/SPEC/闸表 · 唯一写入面=本文）
> **被审 diff**：`414270d..task/memory-injection-consumer`（4 提交：`a9fde63` Phase A spy 实证矩阵（零生产码）· `ed2c150`/`29cd456` [00] 文档落签 · `1edd2ab` Phase B ④b 全模式收窄+功能休眠；合计 20 文件 +1070/-313）
> **对照真值**：task `docs/tasks/active/task_memory_injection_consumer.md`（Phase A/B 结构 · ④b 裁定 · FP/TC · 非范围 · freeze）· SPEC `docs/spec/memory-injection-consumer/SPEC-memory-injection-consumer_v0.md`（signed v0.1）· R1 审查 `docs/harness/reviews/task_memory_injection_consumer_audit_R1_20261019.md`（conditional_pass · N1–N3）· 裁定链：HG-PHASE-B-DECISION=approved（④b）· 00 方案甲裁定（redline P1 翻休眠断言）· `docs/harness/invokes/by-task/memory-injection-consumer/invoke_20261020_30_phaseB_4b_dormant.md`
> **审查日期**：2026-10-20
> **审查方式**：逐行读全量 diff（20 文件）+ 对照 task/SPEC/R1/裁定链逐面核验 + 关键锚点 grep 实测 + 本机复跑（CI 等价 park .env 跑法，跑后已复原）

## 结论摘要

- **结论：approve（可合并）** —— 阻塞项 0。
- 切割点确为**单点 funnel**：`assemble_graph_messages_with_memory` 在 `app/` 仅 `graph.py:166`（invoke 壳）/ `graph.py:199`（stream 壳）两调用点，basic/router/supervisor 三模式与 supervisor 内层 rag 工人（`multi/nodes.py:1432` 复走 stream 壳）全部同路；切割完整无残留注入路径；休眠声明四落点齐备且全部指向 DEF-005 对接文档；resolved_query / session_summary / 写入侧 / render helper / 开关函数零改动逐行核实成立。
- 行为等价证据可信：spy 归一化（去尾标后 (role, content) 全量列表等值 = 逐字节对拍）+ run_id 常量隔离 + 自牙测（assertion-has-teeth）三件套设计成立；.env 37 failed 与基线 worktree 逐项 IDENTICAL 对拍有 invoke 实录，本机 park .env 复跑旁证一致（1732 passed / 0 failed / 182 skipped，与 invoke 逐数一致）。
- 枚举外处置三件（redline P1 方案甲 / query_rewrite TC8 翻 dormant / .importlinter 三条移除）逐条核实**合规**，授权链完整（invoke 枚举外披露 + 00 方案甲裁定）。
- 21 红→绿签名经逐行读过全部为真休眠语义（stub 触达即炸 + 逐字节基线 + 零 span/零槽）；DB 变异测以「服务层召回可见污染」保非空真，设计扎实。
- 非阻塞观察 4 条（O1–O4，均不构成退回理由）；残留挂账 5 处注释（白名单外未动）裁定**不阻塞**（§6）；流程挂账 1 条已经 00 裁定路径（§8：方案甲，本文按裁定留工作区，由 30 增补白名单后一并提交）。

---

## 1. 逐行 diff 核验

### 1.1 切割点单点 funnel（task ④b 核心承诺）——✅ 成立

- `app/ops/lg_rag/continuity.py:459-468`：`_assemble_graph_messages_with_memory_impl` 内原注入双分支（facts：开关判定/身份缺失 skip/向量分流/`recall_active`/降级 span/facts·preferences 双计数/注入；episodes：开关/tenant skip/fingerprint/`recall`/降级/零命中 span/注入）**整体删除**，替换为「④b 全模式收窄：记忆注入消费点休眠」注释块 + `return messages`。切割面与 invoke 实录逐字一致。
- funnel 唯一性 grep 实测：`assemble_graph_messages_with_memory` 在 `app/` 内仅 `graph.py:166`（`_ainvoke_with_tracing`）与 `graph.py:199`（`_astream_with_tracing`）两处调用。三模式同路：basic/router 入口与 supervisor（`multi/graph.py:36` 复用两壳，`:122`/ `:146`）共走这两条装配壳；supervisor 内层 rag 工人经 `astream_router_agent`（`multi/nodes.py:1432`）复走 `_astream_with_tracing` → 同 funnel。hitl/resume 路径用 `build_supervisor_agent` + `Command(resume)`，不重新装配——无第四路径。
- 残留注入路径 grep 实测：`inject_memory_facts_block` / `recall_active` / `recall_with_vector` / episode `recall` 在 `app/` 生产调用面零残留（`memory/service.py` / `episode_service.py` 保留的是写入侧/服务层 API，属 task 既定保留面）。

### 1.2 保留面零改动（task「helper 保留供 ④a 复活」口径）——✅ 逐行核实

| 保留面 | 位置 | 判定 |
|---|---|---|
| `resolved_query`（先重写后召回的重写侧） | `continuity.py:443` `maybe_rewrite_query` | ✅ 零改动 |
| session_summary 双分支 | `continuity.py:444-458` | ✅ 零改动 |
| wrapper 签名（tenant_id/user_id/task_domain/intent_features/tool_sequence） | `continuity.py:516-518` 起 | ✅ 形参全保留（现不被使用，签名稳定，④a 复活零签名迁移成本） |
| 开关函数（默认关 · 非法回退关） | `memory_facts_enabled:142-152` / `memory_episodes_enabled:208-223` | ✅ 零改动 |
| render / inject helper | `render_memory_facts_block:279` / `render_memory_episodes_block:316` / `inject_memory_facts_block:349` | ✅ 零改动 |
| 写入侧（extract / service / episode_service / episode_gate） | `app/ops/memory/` | ✅ diff 零触碰（仅 README:14 / `__init__.py` docstring 文档面） |

### 1.3 休眠声明四落点 + 图谱/文档面——✅ 齐备且指向 DEF-005 对接文档

1. 切割处注释块（`:459-468`）✅；2. 模块 docstring（`:4-13`）✅；3. impl/wrapper docstring（`:433-437` / `:516-518`）✅；4. `:125` 节首「记忆 facts helper（④b 休眠…保留供 ④a 复活）」✅——四落点全部指向 `docs/tasks/deferred/task_memory_facts_build_4a.md`。
- `docs/_tech_graph/l1/01_modules.md` memory 行末追加备注：「memory-injection-consumer ④b（2026-10-20）…当前无任何消费点，功能休眠…复活对接 task_memory_facts_build_4a.md…不新增一级模块 · 零新跨模块边 · 零新路由/表/SSE · 不增 implementedBy」——task TC10 图谱回写口径逐字落实。
- `.importlinter`：移除 `continuity -> memory.{service,episode_gate,episode_service}` 三条 ignore（保留 router/sse_stream `-> memory.extract` 写入侧两条），注释注明 ④a 复活时接回——移除必要性成立：切割后 continuity 不再 import 这些模块，import-linter 对无匹配 ignore 会挂（本机复跑 12 kept / 0 broken 实证）。
- `docs/standards/PRIORITY_DEFERRED.md` 登记 DEF-005 ✅；`docs/tasks/deferred/task_memory_facts_build_4a.md` 新建 30 行（触发条件 / Phase A 基线 / 8 条遗留问题清单 / 非范围）✅；task 闸表 HG-PHASE-B-DECISION 翻 approved 由 [00] 落签提交（`ed2c150`/`29cd456`）完成，30 未碰闸表 ✅。

## 2. 行为等价证据复核——✅ 可信

- **spy 归一化手法**：`SpyProvider` 以 `RecordCall` 快照 complete/complete_stream 实收消息清单；`_assert_on_off_parity` 先经 `_norm` 剥 spy 名 `.on`/ `.off` 尾标，再对 messages 做 (role, content) 全量列表等值比较——等价于逐字节对拍，且覆盖**全部** LLM 消费点（chain/router/planner/内层工人/aggregator），比抽样强。
- **run_id / thread_id 隔离**：supervisor 场景 `run_id="phaseb-run"` 常量（子任务 id 嵌入 run_id，on/off 需同值才能逐字节等）；thread_id 带 tag 隔离（thread_id 不进 prompt——session_summary 默认关，实测不影响消息面）。设计正确，见 O2 提示。
- **自牙测**：`test_spy_assertion_has_teeth`（开开关但**不**放 stub → 哨兵真发 → dormant 断言必失败）证明断言不是恒真走过场；`test_markers_match_render_truth` 把测试 marker 对 `render_memory_facts_block`/`render_memory_episodes_block` 真值钉死，防「marker 写错导致零命中恒真」。
- **注入开/关零 diff 对拍**：4 场景（basic-rag / router-rag-rewrite 回环 / router-direct / supervisor 含内层工人）× on/off 双拍 + `test_switches_default_off_zero_recall_zero_injection`（TC2 默认关面）——场景覆盖与 task 三模式+内层工人承诺一致。
- **.env 37 failed 对拍实录**：invoke 录「.env 在场 37 failed 与基线 `a9fde63` worktree 逐项 IDENTICAL」——手法正确（同 .env 双跑逐名对拍），证明 37 失败全为宿主 .env 环境性（非本 diff 引入）。本机 park .env 复跑 1732 passed / 0 failed（§5）为其旁证：CI 等价面零失败。

## 3. 枚举外处置合规——✅ 三件全合规

1. **redline P1 方案甲落实**（`tests/test_memory_preference_redline.py::test_no_preference_memory_no_preference_section_dormant`）：`MEMORY_FACTS_ENABLED=true` + recall stub 零调用（触达即炸 + `assert_not_awaited`）+ 金样 ≥3 逐案例逐字节基线 + 零偏好节断言；改名 `*_dormant`；docstring 注明 ④a 恢复时按 deferred task 清单恢复原反向对照。方案甲四要件（stub 零调用 / 逐字节基线 / 改名 / 恢复指引）逐条在码。
2. **query_rewrite TC8 翻 dormant**（`tests/test_lg_rag_query_rewrite.py::test_tc8_rewrite_applied_recall_never_called_dormant`）：#1 已合并任务的测试被翻——核实新断言 `order == ["rewrite"]` + `out[-1]` 实收 rewritten + `recall_with_vector` stub 触达即炸：「先重写后召回」的**重写侧**仍被守护（重写确发生且实收改写文），召回侧在 ④b 下零触达**属实**（装配面已不召回，旧断言`order==["rewrite","recall"]`必红，翻断言是唯一正解）。改动经 invoke 枚举外披露 + 00 方案甲授权链，非 30 私改。
3. **.importlinter 三条 ignore 移除**：必要性实证（§1.3），保留写入侧两条未动，注释留 ④a 接回指引。

## 4. 测试质量——✅ 真休眠语义 · 非空真 · 登记如实

- **21 红→绿签名**：invoke 录「生产码未动首跑 21 failed/74 passed」。现树 `*_dormant` 签名 22 个 = 旧文件改名 18（injection 8 / episode_recall 6 / extract_p1 1 / input_isolation 1 / redline 1 / query_rewrite 1）+ 新文件 parity 4；invoke 的 21 = 改名 18 + 未改名但断言面翻转 3（`test_memory_service_db.py` 两 mutation 测 + `test_memory_vector_p1.py` 一测）——口径自洽（O4）。逐行读过全部 22 个 dormant 断言：均为「stub 触达 AssertionError + 零 span/零槽/零 marker + off 基线逐字节」真休眠语义，无一走过场。
- **非空真设计**（亮点）：DB 变异测先断言**服务层** `recall_active`/`recall_with_vector` 可见污染（通路是通的），再断言装配面恒零注入块，revoke 后服务层痊愈——「装配面零注入」不是空真（库内确实有污染、服务层确实能召回，只是装配面不消费）。
- **TC5 白名单登记**：`test_phase_b_diff_whitelist` 白名单 `_APP_ALLOWED`={continuity.py, memory README/`__init__`, .importlinter} + 前缀 tests/、invoke 目录、01_modules.md + `_UPSTREAM_SIGN_PATHS`（docs/tasks 两件 + PRIORITY_DEFERRED = 00 落签面）+ 黑名单 scripts//alembic//其余 app/（含 untracked 面）——对照实际 diff 逐路径核账**如实**（R1 N2 白名单化吸收落实）。白名单未含 `docs/harness/reviews/` 的交互问题见 §8（已经 00 裁定）。
- **TC↔映射**：TC1 Phase A 矩阵（`a9fde63` invoke 实录 9 消费点零收到）✅；TC2 ✅；TC3/TC4（4 场景 dormant+parity 覆盖 supervisor 三消费点与 router/basic 四点）✅；TC5 ✅；TC6（task 闸表 approved + `invoke_20261020_phase_b_decision_4b.md` 记录位）✅；TC8（收窄案注入查询跳过 · spy DB 零命中）✅；TC7/TC9 为接线案/疑点推翻案验收，④b 结局不取用（task :220「TC7–TC9 按结局取用」明裁）——不适用，非缺失；TC10（graph-compile 绿 + 图谱回写）✅；TC11（全量绿 + ruff）✅；TC12（九旧测文件逐文件处置）✅。

## 5. 本机复跑实录（CI 等价 park .env 跑法 · 跑后已复原）

| 项 | 命令（与 `.github/workflows/` 一致） | 结果 |
|---|---|---|
| pytest 全量 | `.venv/bin/python -m pytest tests -q`（CI: pytest.yml:48） | **1732 passed / 0 failed / 182 skipped**（24.98s · 52 warnings 全为既有环境告警）——与 invoke 逐数一致 |
| ruff | `.venv/bin/ruff check app tests`（仓内 pin 0.15.21，CI: pytest.yml:53） | **All checks passed**（exit 0） |
| graph-compile | `./scripts/graph-compile.sh`（CI: tech-graph.yml:33） | **EXIT=0**（flow 图谱全 OK · mermaid normalize check 9 md ok） |
| lint-imports | `.venv/bin/lint-imports`（CI: import-linter.yml:31 `--config .importlinter`） | **Contracts: 12 kept, 0 broken**（exit 0） |

跑法：`mv .env /tmp` park → 四项全跑 → 复原（`ls -la .env` 核实 3629B Oct 16 原件回位）。注：系统 PATH 的 ruff 与仓内 pin 版本不一致（报 12 条 UP007 风格项），以仓内 venv 0.15.21 为准（与 CI 同源钉版）——非本 diff 问题。

## 6. 残留挂账评估——✅ 不阻塞

invoke 登记 5 处注释残留，逐处 grep 实证在册：`graph.py:161` / `graph.py:195`（user_id「仅供记忆注入…默认关零 diff」）、`router.py:176-177`（「仅供图内记忆注入」）、`sse_stream.py:401`（「记忆注入身份…默认关零 diff」）、`app/ops/session/README.md:16`（「记忆注入**之前**」）。
- **未动合规**：五处均不在 TC5 白名单 `_APP_ALLOWED` 内，30 禁动属实（动即破白名单）。
- **阻塞裁定**：注释描述的是参数的历史设计意图（身份链路为注入而铺），④b 下语义已过时但**不误导运行行为**（开关默认关 + 装配面休眠双保险）；且 DEF-005 已登记、④a 复活时这些注释反而恢复准确。挂账口径**可接受**，不阻塞合并。建议（O3）：把「④a 复活或独立清理 task 时同步刷新五处注释措辞」补入 `task_memory_facts_build_4a.md` 遗留问题清单（文档面建议，非退回项）。

## 7. R1 审查 N1–N3 吸收核实——✅ 全落实

| N | 内容 | 吸收实证 |
|---|---|---|
| N1（低） | 结局空间漏洞（supervisor 有 ∧ router/basic 零 无触发结局） | 未走漏洞径：Phase A 实证三模式 9 消费点全零收到 → 结局④前提干净命中，FP-9 处置预案无需触发 ✅ |
| N2（低） | TC5 黑名单收紧为白名单 | Phase A `test_phase_a_diff_whitelist` 与 Phase B `test_phase_b_diff_whitelist` 双白名单+黑名单在测试内强制 ✅ |
| N3（低） | 开关锚点行区间差尾行 `return False`（:152/:223） | 现 task 文本已不再含 `:142-151`/`:208-222` 区间（:73/:161 锚点改写为注入面 `:349-362`/`:316`/`:527`），错误区间标记失效——按「不再出现错误锚点」裁定吸收属实 ✅ |

## 8. 流程挂账与裁定链记录（40 写入面纪律）

- **发现**：`test_phase_b_diff_whitelist` 白名单不含 `docs/harness/reviews/`——若按原指示把本审查文提交进分支，`git diff 414270d HEAD` 将多出本文 → TC5 转红（PR CI 必跑此测，合并闸破）。先例：`task_query_coref_rewrite_review40_20261019.md` 留工作区 untracked 未入 git。
- **处置链**：40 中途 send_message 上报 00 → **00 裁定方案甲**：本文落盘留工作区**不 commit/push**；30 在 `_UPSTREAM_SIGN_PATHS` 增补本文路径一行 + 复跑 `test_phase_b_diff_whitelist` 绿后，由 30 将（审查文 + 测试一行）一并提交 push。40 写入面仅本文，未碰测试。
- 本节为裁定链如实记录；该挂账不影响 §1–§7 对 30 交付本身的 approve 结论。

## 9. 非阻塞观察（O1–O4）

| # | 级 | 内容 | 裁定 |
|---|---|---|---|
| O1 | 低 | `_assembled_text` 对 state.messages 仅比 content 拼接不比 role 序列 | LLM 请求面对拍已是 (role, content) 全等；state 面 role 由同代码路径产出——风险极低，不阻塞 |
| O2 | 低 | supervisor parity 依赖 `run_id` 常量使子任务 id 嵌入位一致 | 现设计正确；若未来 run_id 生成逻辑变更需同步归一化——提示性 |
| O3 | 低 | 5 处注释残留措辞过时（§6） | 建议补入 ④a 遗留问题清单，不阻塞 |
| O4 | 提示 | invoke 红测计数 21 = 改名 18 + 未改名翻转 3；现树 `*_dormant` 签名 22（含新文件 4 parity） | 口径自洽无矛盾，仅备查 |

## 10. 结论

**approve（可合并）**。切割单点 funnel 与完整性、休眠声明四落点、行为等价证据、枚举外授权链、测试真休眠语义、复跑四闸全绿、残留挂账口径——七面全部核实成立，阻塞项 0。唯一流程事项（审查文入库路径）已经 00 裁定方案甲，按裁定执行不影响本结论。

---

> 审查人：Harness 40（合并前代码审查帽） · 2026-10-20
> 本文落盘即真值；按 00 裁定，本文提交动作由 30 随白名单增补一并完成。
