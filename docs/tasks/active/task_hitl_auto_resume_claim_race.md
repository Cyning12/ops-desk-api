# Task：hitl-auto-resume-claim-race（auto_resume 认领竞态 · decide 同秒首跑连续 stranded_checkpoint）

> **状态**：draft（10 落稿 · 三人工闸 pending · 未开工）
> **类型**：验收偏差收口（bugfix 性质 · 实证驱动 · T2 交付物的 live 偏差修正）
> **依据**：`docs/acceptance/20261010_hitl-consumption-loop_local_acceptance.md` 偏差表 D1 + 项6 auto 链段（**实证真值 · 现于分支 `acceptance/20261010-hitl-consumption-loop` @ `f57b4ae` · 未 merge master · 引用时以该分支/commit 为准**）
> **分支**：`task/hitl-auto-resume-claim-race`（base = master `1117286` · T4 PR #221 已 merge ✓）

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `hitl-auto-resume-claim-race` |
| **git_branch** | `task/hitl-auto-resume-claim-race` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | TC1 竞态窗口注入式复现单测 + TC2 auto decide-同秒链零 stranded_checkpoint 断言 + TC3 live 实证 auto 首跑无重试直达 + TC4 反回归（真·永久 stranded 409 存续 · manual 零 diff · T2 39 枚原样绿） |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `n/a`（预判无图谱变更 · 30 实证若新增机制面/env 则升级 G-L1 hitl 行备注） |
| **graph_delta** | `n/a`（预判 · 无新一级模块/跨模块边/路由/SSE 事件/表） |
| **graph_delta_note** | 候选修复面全部落在 hitl 模块既有行备注覆盖的「触发器/SKIP LOCKED 认领/补偿扫描」机制内；若 30 引入新 env 旋钮或新机制面 → hitl 行备注回写 + HG-GRAPH-MODULES 00 代录 |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 无文档站变更 |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,20,30,40` |
| **invoke_retention_profile** | `default` |
| **experience_capture** | `required` |
| **kpi_aggregator** | `n/a` |
| **orchestration** | 10 落稿 → 20 R1 → 维护者签 → 30（先实证复现定方案再实现）→ 40 → PR+CI 绿 → CLOSE |
| **freeze_id** | 无（预期零新表/零迁移/零新 SSE 事件/零 payload 新键） |

### 人工闸

| 闸 | 状态 | 说明 |
|---|---|---|
| HG-TASK-DRAFT | approved | 10 落稿 7022e20 · 维护者授权 00 代录（2026-10-10 · 授权在案 m00059/m00255） |
| HG-AUDIT-R1 | approved | 20 R1 PASS-WITH-NITS（b7639ce · N-1~N-3 非阻塞留 30 照登）· 维护者授权 00 代录（2026-10-10） |
| HG-GRAPH-MODULES | approved | 在册 · 预判无图谱变更（照实判定 · 00 代录 2026-10-10）· 若 30 实证新增机制面/env/台账键则 hitl 行备注回写（N-2 在案） |
| HG-PILOT-OPSDESK-GLAYER | n/a | 无外部试点面 |

## 背景与目标

### 实证锚点（验收 D1 · 逐字关键行）

2026-10-10 增量验收 live auto 链（`docs/acceptance/20261010_hitl-consumption-loop_local_acceptance.md` 偏差表 D1 · 项6）：

- decide 成功与台账 `hitl_auto_resume_triggered` **同秒**（17:00:51）；
- auto 首次认领起**连续 6 次** `ResumeError: stranded_checkpoint`（`app/ops/hitl/resume.py:244` 周边：checkpoint 有未完成任务但没有 interrupt 元数据）；
- 补偿扫描（`OPS_HITL_AUTO_RESUME_SCAN_INTERVAL_SECONDS=5`）每 5s 重试，约 **17:01:23（≈30s 后）**恢复成功，后续 consumed → token → echo 执行全通；
- 手动 resume（分钟级人批延迟）**从未触发**该错误；
- 验收其余 8 项全 PASS（D1 作为偏差登记 · 全链最终通但 auto 模式首跑延迟明显）。

### 10 初步研判（开放 · 待 30 实证 · 不锁死）

竞态窗口机制链（10 实读在案）：

1. `app/ops/lg_rag/multi/nodes.py:1820-1822` 注释明示「**落库先于挂起**」——`_persist_hitl`（nodes.py:1610-1706）先把 pending 行写库，`interrupt()` 在 :1831 才抛 GraphInterrupt；LangGraph checkpoint（含 interrupt 元数据）落库在此之后。
2. 故「pending 行可见（GET pending / auto 认领可查）」**⇏**「checkpoint interrupt 元数据可见」——两者之间的时序差即竞态窗口。
3. 手动流人批延迟分钟级，窗口天然不可见；auto 流 decide 同秒触发认领（router.py:242-254 → `schedule_auto_resume` → `_claim_and_execute` → `_execute_decided_resume` → `resume_hitl_run` → `aget_state`），读到的可能是 interrupt 元数据落库前的快照（有 pending tasks、interrupts 全空）→ 命中 `resume.py:236-248` `stranded_checkpoint`。
4. 窗口长度 ≈30s（6 轮 × 5s）远超一次 DB 提交，疑似与 SSE 连接/astream 生成器收尾生命周期绑定（验收脚本 curl 保持连接期间 checkpoint 终写未提交？）——**待 30 实证定位，起草阶段不下结论**。
5. 附带发现：`resume.py:41-51` 把 `stranded_checkpoint` 注释钉为「旧版本格式残留 · 永远恢复不了 → 409」——本竞态证明该 code 存在 **transient 形态**，分类语义须重审（手动 resume 409 对外语义不动 · 见钉死契约 2）。

### 候选修复方向（开放给 30 实证后定 · 起草不锁死）

- **方向 A · 认领后执行前就绪校验**：`_claim_and_execute` 认领后用同源 checkpointer `aget_state` 校验 interrupt 元数据可见；不可见 → 不抛错不执行、留痕、等下轮补偿扫描——把竞态化为正常「等下轮」，消除错误日志噪音与 409 语义误伤。
- **方向 B · 延迟认领/触发**：decide 触发后加秒级 grace delay 再认领——实现最简但治标；若窗口绑 SSE 连接生命周期则不可靠。
- **方向 C · 执行体内有界退避重试**：捕获 `stranded_checkpoint` 时短退避重试（如 1s/2s/4s 封顶）——把 ~30s 降到秒级；须区分「真·永久 stranded」（升级残留）与「竞态 transient」，并防无限重试/多副本叠加。
- **方向 D · 根因侧**：确证 checkpoint interrupt 元数据落库时序（LangGraph 内部）并在挂起路径上保证可见性——预判超出最小面，原则上不动 LangGraph 语义。

**目标**：auto 模式 decide 同秒即时认领路径**零 `stranded_checkpoint`**，auto 首跑无重试直达恢复成功；手动 resume 语义与既有测试面零 diff。

## 现状锚点

| 锚点 | 位置 | 事实 |
|---|---|---|
| 触发器挂点 | app/ops/hitl/router.py:242-254 | decide 成功分支 approved∧auto → `schedule_auto_resume`（OA callback 不挂） |
| 触发派发 | app/ops/hitl/auto_resume.py:128-148 | `schedule_auto_resume` 派发 asyncio 任务 · 台账 hitl_auto_resume_triggered/compensated |
| 认领-执行 | app/ops/hitl/auto_resume.py:151-182 | `_claim_and_execute`：acclaim_approved_for_resume 行锁认领 → run_is_terminal 终态判定 → `_execute_decided_resume` 同源恢复 · **任何异常只 logger.exception「HITL 自动恢复执行失败」等下轮扫描兜底** |
| 补偿扫描 | app/ops/hitl/auto_resume.py:185-222 · :225-247 | `scan_approved_not_resumed_once` 四条件 + `start_compensation_scanner`（启动即扫+周期 · manual 零创建） |
| stranded 判定 | app/ops/hitl/resume.py:228-248 | `_resume_with`：aget_state → 无 tasks 抛 not_interrupted(:230-235) → tasks 有但 interrupts 全空抛 **stranded_checkpoint(:236-248 · 报错行 :244)** · 原设计意图=拦 langgraph 0.2→1.2 升级残留防 TypeError 500 |
| code→HTTP 映射 | app/ops/hitl/resume.py:41-51 | stranded_checkpoint → 409 · 注释钉「旧版本格式残留，永远恢复不了」——竞态证明存在 transient 形态 |
| 落库先于挂起 | app/ops/lg_rag/multi/nodes.py:1820-1822 | 注释明示 _persist_hitl 写 pending 行在先 · interrupt() 在 :1831 才抛 GraphInterrupt · checkpoint interrupt 元数据落库在其后 |
| T2 交付原文 | docs/tasks/done/task_hitl_approval_consumption_auto_resume.md | auto_resume 全设计（Q6/Q7 · 无状态恢复纪律 · FP-8~FP-11） |
| SPEC D5 面 | docs/spec/hitl-approval-consumption/SPEC-hitl-approval-consumption_v1.md §2 D5 | Q6 进程内后台任务+行锁认领+补偿扫描 · Q7 env+resume_mode · 设计纪律 6（无状态恢复 · 禁 HTTP 自调） |
| 实证真值 | docs/acceptance/20261010_hitl-consumption-loop_local_acceptance.md（分支 acceptance/20261010-hitl-consumption-loop @ f57b4ae · 未 merge master） | D1 偏差逐字 + 项6 auto 链台账序列 |

## 钉死契约

1. **无状态恢复纪律存续**（SPEC 设计纪律 6 · T2 钉死）：任何修复不引入进程内存挂起态载体；执行路径仍同源 `_execute_decided_resume`（禁 HTTP 自调 · 禁第二条恢复实现）；就绪校验若采用只许**只读**（FP-4）。
2. **手动 resume 对外语义零 diff**：ResumeError code→HTTP 映射不动（stranded_checkpoint 仍 409 · `tests/test_hitl_resume.py:230-259` `test_stranded_checkpoint_is_refused_not_crashed` 断言存续；若 30 裁定 transient 重分类须动此断言 → 先过 20/维护者裁定）；真·永久 stranded（升级残留）判定能力不丢。
3. **manual/off 零 diff**：`OPS_HITL_AUTO_RESUME` 缺省/非法=manual、`LG_RAG_DELEGATION_TOKEN_MODE=off` 零触达；manual 模式行为逐字节不变。
4. **最小面**：改动收敛于 `app/ops/hitl/auto_resume.py` 认领-执行路径（± `resume.py` 内部注释/分类 · ± 测试）；`nodes.py` interrupt/persist 时序、`store.py`、`router.py` decide 挂点、T1 消费门/T4 guard 面 diff 空——若 30 实证根因必须动其中 → GATE_STOP 回 10/维护者裁定。
5. **方案开放**：候选 A/B/C/D 不锁死 · 30 须先复现竞态窗口（TC1 注入式红测或实证日志）再定方案，并在 30 invoke 留裁定依据。
6. **台账纪律存续**：记动作不记内容；若新增重试/就绪台账键须在 30 invoke 钉名。
7. **零新表/零迁移/零新 SSE 事件/零新 env**（候选方案均不需要；若 30 裁定需要新 env 旋钮 → 图谱回写义务触发 + 钉死契约 4 重审）。

## 范围

- **F1 竞态窗口复现**：注入式单测构造「checkpoint 有 pending tasks 但 interrupt 元数据不可见 → 随后可见」时序（内存 saver 预置快照 / mock aget_state 时序 · **禁赌真竞态**）——修复前红、修复后绿（TC1）。
- **F2 根因实证与方案裁定**：30 实证 checkpoint interrupt 元数据可见性时序（含与 SSE 连接生命周期的关系假设），候选 A/B/C/D 择一或组合，invoke 留痕。
- **F3 最小面修复实现**（钉死契约 4 面内）。
- **F4 测试断言化**（TC1–TC4）。
- **F5 图谱判定回写**：预判 n/a（照实写）；实证升级则 hitl 行备注 + HG-GRAPH-MODULES 代录。
- **F6 invoke 留档**（10/20/30/40 按 required_invoke_hats）。

### 非范围

- 不改 LangGraph interrupt/checkpoint 内部语义（方向 D 原则上不做）。
- 不改手动 resume 端点与 ResumeError→HTTP 对外映射（钉死契约 2）。
- 不改 T1 消费门 / T4 replan 保号+建单 guard / `store.adecide` / interrupt 建单机制。
- 不引入 MQ/外部调度/新部署单元（SPEC Q6 双弃裁定存续）。
- 不改 SSE 事件 / UI。
- 不处理 T4 CLOSE 钉案②（approved 路径 LLM 盲循环 + `_collect_decisions` 恒 replan）——另案裁定权在维护者。

## failure_paths

| 编号 | 失败路径 | 处置 |
|---|---|---|
| — | HG-TASK-DRAFT/HG-AUDIT-R1/HG-GRAPH-MODULES pending 即 30 | 拒开工（闸表 pending 不代签） |
| FP-1 | 竞态窗口单测不可复现（时序敏感） | 注入式构造（内存 saver 预置「tasks 无 interrupts」快照 / mock aget_state 时序）· 禁赌真竞态 |
| FP-2 | 修复误伤真·永久 stranded（升级残留 checkpoint） | 手动 resume 409 语义存续断言（test_hitl_resume.py:230 面）· transient/永久区分判定 30 留痕 |
| FP-3 | 退避重试失控（若选方向 C） | 有界次数+间隔上限 · 单据 TTL 过期自然终止 · 行锁认领防多副本叠加 |
| FP-4 | 就绪校验长成第二条恢复路径（若选方向 A） | 只许只读校验 · 执行仍 `_execute_decided_resume` 同源（T2 钉死存续） |
| FP-5 | grace delay 固化 auto 首跑延迟（若选方向 B） | 上限钉死+默认最小 · 台账可观测 · 记录取舍 |
| FP-6 | B1 旧测断言冲突 | 见 B1 表 · 30 亲跑基线对拍 |
| FP-7 | auto 失败可观测性 | 现有 exception 日志保留；修复后首跑直达使竞态面该日志清零（TC2 断言） |

## B1 · 旧测影响面

| 测试文件 | 关系 | 预期 |
|---|---|---|
| tests/test_hitl_auto_resume.py（T2 · 39 枚） | 直接冲突面：:526 `test_db_auto_chain_terminal_done_frame` · :583 `test_db_scan_compensates_after_store_rebuild` · :688 不循环断言 | 原样绿；若修复动「执行失败只落日志等扫描兜底」行为（方向 A/C），相关断言按需对齐并留痕 |
| tests/test_hitl_resume.py | :230-259 `test_stranded_checkpoint_is_refused_not_crashed`（stranded→409 永久语义断言）· **与竞态复现构造同形态，须区分「随后可见 vs 永久不可见」** | 原样绿（钉死契约 2）；若裁定 transient 重分类须动 → 先过 20/维护者裁定 |
| tests/test_hitl_resume_events.py | resume 事件链 | 原样绿 |
| tests/test_hitl_pending_decide.py | decide 面 | 原样绿 |
| tests/test_hitl.py · tests/test_lg_rag_sse_hitl.py | HITL 基线 + SSE 挂起链 | 原样绿 |
| tests/test_hitl_approval_consumption.py（T1/T4） | 消费门+保号 guard | 原样绿 |

## 验收标准

- [ ] **TC1 竞态窗口复现单测**：注入式构造「checkpoint 有 pending tasks 但 interrupt 元数据不可见 → 随后可见」时序；断言修复前该窗口形态触发 `stranded_checkpoint`、修复后 auto 路径不再抛出且最终恢复成功（对照形态或修复后单测直接钉绿 · 30 裁定并留痕）。
- [ ] **TC2 修复后零 stranded_checkpoint**：auto 全链 pytest（decide 同秒即时认领路径）caplog/台账断言无「HITL 自动恢复执行失败」+ 无 `ResumeError: stranded_checkpoint`；首跑即恢复成功（无需补偿扫描重试轮）。
- [ ] **TC3 live 实证 auto 首跑无重试直达**：六 env 组 + auto + `OPS_HITL_AUTO_RESUME_SCAN_INTERVAL_SECONDS=5` 起 live，decide 同秒 → 首个 claimed 即恢复成功；台账链 triggered→claimed→恢复完成（consumed/token/执行）**无 stranded_checkpoint 重试轮**。
- [ ] **TC4 反回归**：真·永久 stranded（旧格式 checkpoint 形态）手动 resume 仍 409（`tests/test_hitl_resume.py:230` 断言存续或经裁对齐）；manual 模式零 diff；tests/test_hitl_auto_resume.py 39 枚原样绿；B1 表全文件亲跑绿。
- [ ] **TC5 工程面**：pytest 全绿（基线 4 failed=capability_lookups×3+lg_rag_multi×1 环境性钉案照登 · 零新增红）；ruff 触及路径零新增；graph-compile EXIT=0；`npx spec-wave task lint` PASS；三闸 approved 后才 30。

## 依赖

- 实证真值：`docs/acceptance/20261010_hitl-consumption-loop_local_acceptance.md`（分支 `acceptance/20261010-hitl-consumption-loop` @ `f57b4ae` · **未 merge master** · D1+项6）。
- T2 交付：`docs/tasks/done/task_hitl_approval_consumption_auto_resume.md` + `app/ops/hitl/auto_resume.py` 全文。
- SPEC：`docs/spec/hitl-approval-consumption/SPEC-hitl-approval-consumption_v1.md` §2 D5（Q6/Q7 · 设计纪律 6 · FP-8~FP-11 · A9/A10）。
- 编码规范：仓内 coding standards（L2_backend bar）。

## 给执行帽的必读列表

1. 验收文档 D1 段 + 项6 auto 链段（分支/commit 见依赖节 · 逐字实证）。
2. `app/ops/hitl/auto_resume.py` 全文（:128-148 触发 · :151-182 认领执行 · :185-222 扫描 · :225-247 scanner）。
3. `app/ops/hitl/resume.py` :41-51（code→HTTP 映射注释）+ :211-282（`_resume_with` · stranded 判定 :236-248）。
4. `app/ops/lg_rag/multi/nodes.py` :1610-1706（`_persist_hitl`）+ :1820-1833（落库先于挂起 · interrupt 时序）。
5. `app/ops/hitl/router.py` :242-254（触发器挂点）。
6. `docs/tasks/done/task_hitl_approval_consumption_auto_resume.md`（T2 钉死契约 · 无状态恢复纪律）。
7. SPEC v1 §2 D5 段。
8. B1 表列测试文件（尤其 tests/test_hitl_auto_resume.py 与 tests/test_hitl_resume.py:230-259）。

## 思考轮控制

| 轮 | 结论 | early_stop | reason（early_stop） | residual_risks |
|---|---|---|---|---|
| R0 | 问题框定：decide 同秒 auto 认领 → 连续 6 次 stranded_checkpoint → 补偿扫描 ~30s 兜底成功 · 手动从未触发 | false | — | 窗口真实成因未实证 |
| R1 | 证据收集：验收 D1 逐字 + auto_resume/resume/nodes 实读 → 「落库先于挂起」+ pending 可见 ⇏ interrupt 元数据可见 | false | — | 窗口 ~30s 长度与 SSE 生命周期关系仅假设 |
| R2 | 方案生成：候选 A 就绪校验 / B 延迟认领 / C 退避重试 / D 根因侧（预判超面） | false | — | 各方向取舍未实证 |
| R3 | 反例/边界：真·永久 stranded 不可误伤 · transient/永久须区分 · manual/off 零 diff · B1 冲突面（stranded 409 断言 / 扫描兜底断言） | false | — | 复现可注入性 |
| R4 | 收敛：最小面锁 hitl/auto_resume.py 认领-执行路径 · 方案开放给 30 实证后定 · 手动 409 语义钉死 | false | — | 图谱判定为预判 |
| R5 | 收口：TC1–TC5 验收口径 + failure_paths + 三闸 pending 不代签 · 图谱照实判 n/a（预判） | true | 范围/非范围/验收/failure_paths/锚点齐备 · 方案开放性显式留 30 · 再轮无新增信息 | 竞态窗口成因待 30 实证 · 候选方案未锁死（刻意） |

**actual_last_round**：R5（early_stop）

### R0 · 问题框定

auto_resume（T2 交付）live 验收 D1：decide 与 `hitl_auto_resume_triggered` 同秒（17:00:51），auto 首次认领起连续 6 次 `ResumeError: stranded_checkpoint`（resume.py:244），补偿扫描 5s 周期重试 ≈30s 后恢复成功（17:01:23），手动 resume 分钟级从未触发。全链最终通，但 auto 首跑延迟明显、错误日志噪音 6 条。本 task = 该偏差的收口（bugfix 性质 · 无需新 SPEC · SPEC v1 D5 机制裁定存续）。

### R1 · 证据收集

逐字实读：验收文档（分支 acceptance/20261010-hitl-consumption-loop @ f57b4ae · 未 merge master · D1+项6）；auto_resume.py 全文（触发/认领/扫描三件套与「异常只落日志等下轮」兜底）；resume.py :41-51 映射注释 + :211-282 stranded 判定（原设计意图=拦 0.2→1.2 升级残留）；nodes.py :1820-1822「落库先于挂起」注释 + :1831 interrupt()。机制链：_persist_hitl 写 pending 行在前 · LangGraph checkpoint（含 interrupt 元数据）落库在后 · pending 可见 ⇏ interrupt 元数据可见 = 竞态窗口。

### R2 · 方案生成

候选四方向（开放 · 不锁死）：A 认领后执行前只读就绪校验（把竞态化为「等下轮」）；B decide 触发侧 grace delay（最简治标）；C 执行体内对 stranded_checkpoint 有界退避重试（~30s→秒级 · 须区分 transient/永久）；D 根因侧 interrupt 元数据落库时序（预判超最小面 · 原则上不动 LangGraph）。窗口 ~30s 远超单次 DB 提交，疑似绑 SSE/astream 收尾生命周期——30 实证后再裁定。

### R3 · 反例与边界

- 真·永久 stranded（升级残留 checkpoint）判定能力不可丢：手动 resume 409 语义钉死（test_hitl_resume.py:230 断言存续）。
- 竞态复现构造与 stranded 409 测试同形态（tasks 有 · interrupts 空），TC1 必须以「随后可见」区分 transient。
- 方向 C 防失控：有界重试 + TTL 自然终止 + 行锁认领防多副本叠加（FP-3）。
- 方向 A 防长成第二条恢复路径：只读校验 · 执行同源（FP-4 · 设计纪律 6）。
- manual/off 零 diff；T1/T4 面 diff 空；B1 七文件清点。

### R4 · 收敛

最小面锁 `app/ops/hitl/auto_resume.py` 认领-执行路径（± resume.py 内部注释/分类 · ± 测试）；nodes.py/store.py/router.py/T1/T4 面 diff 空，实证须动则 GATE_STOP 回 10/维护者。方案开放性显式写入钉死契约 5。图谱照实预判 n/a（机制落在 hitl 行备注既有覆盖面 · 新增机制面则回写+代录）。验收口径 TC1–TC5 对齐委派要求（竞态复现单测 + 修复后零 stranded + live 首跑直达）。

### R5 · 收口

范围 F1–F6、非范围七条、failure_paths FP-1~FP-7+闸行、B1 表、验收五条勾选、必读八项齐备；三人工闸 pending 不代签；lint 形态对齐 T2/T4 实证教训（验收 - [ ] 清单 · 思考轮控制表表头）。裁定收口，early_stop at R5。

### 自检结论（执行者）

40 核验回填（invoke：docs/harness/invokes/by-task/hitl-auto-resume-claim-race/invoke_20261010_40_verify.md）——七项独立复跑全 PASS，不采信 30 自报：

1. **diff 面**：8 文件最小面实证（auto_resume.py +52 · 测试 +158 · 图谱 :39 · 文档面）；nodes.py/store.py/router.py/resume.py/消费门/guard diff 全空；test_hitl_resume.py diff 0 行（钉死契约 2 存续）。
2. **红测时序**：git log + detached worktree 检出 79b6485 复跑 2 failed（D1 同形签名）→ 51e17ca 实现严格在后，无先修后测。
3. **断言强度**：TC1 窗口内零执行断言（`assert not attempted`）+ 台账链断言 + 零 stranded caplog 断言；TC2 真 HTTP decide + 真挂起 + 四键台账齐——deferred 非假绿。
4. **反回归**：B1 七文件 174 passed；全量 1764 passed + 4 failed = 基线钉案零新增红；ruff / graph-compile EXIT=0；再生噪音还原。
5. **TC3 live**（隔离库 opsdesk_tc3 · :8060 · auto + 5s 扫描）：triggered→claimed→(compensated→claimed→deferred)×5→approval_consumed→token_issued→token_verified→HITL 恢复完成；**零 stranded_checkpoint · 零执行失败 ERROR · 恰好一次执行**。deferred×5 = 恢复在窗期探针挡重复认领（方向 A 机制本体 live 实证）；decide-同秒原始窗口本次未命中（误端点耽搁 44s · 如实登记），首认领直达亦合规。
6. **留转 2-5**：not_interrupted 子窗口未观测（维持窄判定）· 永久 stranded 观测路径（deferred 台账 TTL 递减留痕）实证成立 · 探针成本低频可接受 · PG 闸环境事实照登。
7. **N-1~N-3**：断言窗 :260 / 台账键图谱回写 / 时序证据——照登核验全过。

结论：**可进 PR 队列**。

## 修订

| 日期 | 说明 |
|------|------|
| 2026-10-10 | 10 落稿：验收 D1 实证锚点逐字承接 · 竞态机制链实读在案（落库先于挂起 · pending 可见 ⇏ interrupt 元数据可见）· 候选 A/B/C/D 开放不锁死 · 手动 409 语义钉死 · 图谱预判 n/a 照实写 · 三人工闸 pending（10 未代签） |
