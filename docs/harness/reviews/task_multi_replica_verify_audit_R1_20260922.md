# Task Audit R1：multi-replica-verify · 内容审查通过 · 待维护者签闸

> **hat_id**：20-task-audit  
> **task**：`docs/tasks/active/task_multi_replica_verify.md`（R1 · 2026-09-22 10-task 落稿 · 68550cc）  
> **对照 SPEC**：`docs/spec/multi-replica-verify/SPEC-multi-replica-verify_v1.md`（**signed** · HG-SPEC-SIGNOFF=approved 2026-09-22 · 8236747）  
> **日期**：2026-09-22 · 审查人：20-task-audit  
> **分支**：`task/multi-replica-verify`（本帽 `git branch --show-current` 核实）  
> **task lint**：复跑 `npx spec-wave task lint --file docs/tasks/active/task_multi_replica_verify.md` → **LINT: PASS**（exit 0）  
> **required_invoke_hats**：`10,20,30,40`（含 20）· 20 invoke 快照已落盘 `docs/harness/invokes/by-task/multi-replica-verify/`  
> **本帽未改** task 实质内容 / 人工闸表 / `app/` / `tests/`；仅落盘本审查文 + 20 invoke 快照

## 结论摘要

| 维度 | 结论 |
|------|------|
| **内容** | **PASS** · 零内容阻塞 · SPEC 逐项映射一致 · 重点抽查全部复现或如实记录 |
| **流程闸** | `HG-TASK-DRAFT` pending · `HG-AUDIT-R1` pending（blocks 30）· `HG-GRAPH-MODULES` approved（本帽亲读复核成立）· 本帽按纪律如实记录，签闸权属维护者 |
| **30 授权** | 真值在 task 人工闸表；pending → 30 拒开工；本审查文按纪律附维护者签闸清单，30 Prompt 待签闸后由维护者下发 |

**总评**：task 与 signed SPEC 实质差异为零；范围 D1–D5、非范围 9 条、failure_paths 14 条、验收 26 条、R0–R5 逐块映射核对一致；重点抽查（B1 抽样 · pytest 基线 · uvicorn grep · 图谱亲读 · 两条否定性断言可测性 · 变异检验相容性）均成立；非阻塞观察 2 条（见末节）。

---

## 一、对照 SPEC 逐项核对

### 范围（SPEC §2 → task 范围 D1–D5）

| SPEC | task | 核对 |
|------|------|------|
| D1 部署验证（runbook+报告 · 网关如实标注 · 亲和对照 · 断言面四项 · 报告字段族） | D1 同形 | **一致**（含「Eureka 条目标未覆盖待补 · 降级形态写成网关验证通过 = 撒谎」钉死） |
| D2 状态外置（双进程 pytest · 归属先断言 FAIL 非 skip · A 起 B replay/404/续写 seq · 前置配置断言） | D2 同形 + 并发 setup 不死锁启动竞态实证 | **一致**（task 增补项承 SPEC §5 并发 setup 行，属过程化落地） |
| D3 边界清单（≥8 条目 file:line · 失真形态 · 处置建议 · budget 放大实证 · /runtime · /catalog 对拍 · 扫描基线兜底） | D3 同形 | **一致** |
| D4 HITL 跨实例（A 挂起 B resume 图真的续跑 · 409/503 负路径 · runbook 轨复走） | D4 同形 | **一致** |
| D5 图谱/文档/alembic（零迁移 · 零新路由/模块/事件 · graph-compile 绿 · app/ 零 diff · bug 另开 fix task） | D5 同形 + spec README 移行注记 | **一致** |

### 非范围（SPEC §3 九条 → task 非范围九条）

真投产 / 选型变更 / 容量灾备 / 进程内状态外置改造 / Java 网关改动 / k8s 新建 / 生产码修复 / SSE 无缝迁移 / 前端+历史文档——**九条全收 · 零语义偏移**；「验证≠投产」在 task 头部状态行、背景设计纪律 1、钉死契约、非范围首条四处一致锁死。

### failure_paths（SPEC §5 十条 → task 14 条）

- SPEC 十条（假阳性没真跨实例 · 进程内状态失真 · 配置漂移 · 版本漂移 · HITL 批了没发生 · 并发 setup · 验证污染 · 网关不可用 · 报告无法复核 · 发现阻断性 bug）**逐条全收**，四列翻译完整（触发条件/系统行为/可重试/用户可见）。
- task 增补第 11 条内容行「**双进程 fixture 起停不稳**」（仓内零先例基建风险 · 对策：动态端口 + 就绪轮询 + finally 杀进程树 + 用例级超时）——承 SPEC §7 residual ① 的过程化落地，**有据**。
- 过程三行（HG-AUDIT-R1 未签即 30 拒开工 · B1 未落盘拒收 · 缺断言/变异检验拒收）为 Harness 过程闸常规行。
- 计数核对：10 + 1 + 3 = **14 条**，与 task R3/自检声称一致。

### 验收（SPEC §6 → task 26 条）

计数核对：人工闸 1 / D1×5 / D2×5 / D3×3 / D4×3 / D5×3 / 变异检验×3 / 工程×3 = **26 条**，与 R4 声称一致；SPEC §6 本体 23 条（工程×1）→ task 工程扩为 3 条（闸前置 B1 · pytest/ruff · diff 白名单）+ 人工闸 1 条，每节标题注明映射来源，**属过程化落地非语义偏移**。逐条比对 D1–D5 与变异检验三条措辞，与 SPEC §6 同义。

### 钉死契约

F1 双轨 · P1 subprocess 双进程（P2 弃选钉死）· 归属先断言 FAIL 非 skip · 验证≠投产 · app/ 零改动 · HITL 图真的续跑 · 报告环境指纹 · 网关形态如实标注 · 变异检验三条 · 验证卫生——承 SPEC §2/§4 签收锁死，task 未重开辩论，**一致**。

### R0–R5 思考轮

| 轮 | 核对 |
|----|------|
| R0 | 实扫复核留痕（锚点行号 · uvicorn grep · 基线 1349）本帽抽核可复现（见下节）；SPEC signed 在链 ✓ |
| R1 | 闸态如实（两闸待签 · GRAPH 亲读）✓ |
| R2 | 竖切继承 SPEC §4 F1/P1 裁决不重演 · 实现序承 SPEC §8 ✓ |
| R3 | 14 条构成核对一致（见上）✓ |
| R4 | 验收 26 条计数核对一致；B1 10 行处置三态齐全（回归×5 · 改编×0 预期 · 新增×3 · 风险对策×1 · 迁移无×1 · 删除×0）✓ |
| R5 | 交付判定与 SPEC §7 残余风险四条逐条对应（双进程基建零先例 · 外部网关可用性 · 处置建议是建议 · runbook 结论时效）✓ |

全轮 early_stop=no · actual_last_round=R5 · 回填闭合。

---

## 二、HG-GRAPH-MODULES 亲读复核（本帽真读 `docs/_tech_graph/l1/01_modules.md`）

| task 声称 | 本帽复核 |
|-----------|----------|
| `api` 行 :20 | **属实**（grep -n 实证 :20） |
| `capability` 行 :26 · 进程内注册表明示「非跨进程注册中心」 | **属实**（:26 原文「能力**进程内注册表**…**非**跨进程注册中心」） |
| `lg_rag` 行 :27 · checkpointer/事件表/replay 在案 | **属实**（:27 含 T4 事件落盘 `ops_lg_rag_run_events` + replay · PG checkpointer AsyncPostgresSaver） |
| `hitl` 行 :31 · resume 驱动 + 申请落库 | **属实**（:31 含 `resume.py` thread_id → checkpoint 驱动恢复 + `ops_hitl_requests` 落库） |
| `db` 行 :33 · checkpoint 表 checkpoints/checkpoint_writes 同库不同表在案 | **属实**（:33 原文在案） |
| bootstrap 签 2026-07-16 | **属实**（签录表 :55 `task_graph_bootstrap` 行） |
| 签录链完整至 :93 memory-compliance-delete 行 | **属实**（sed :93 实证该行即 memory-compliance-delete 签录） |

**预期无新签义务裁定复核**：task 产物面为 tests/ + scripts/acceptance/ + reports/ + docs/，零新路由/零新一级模块/零新表/零新 SSE 事件，与模块表现状比对无冲突；偏离回炉补闸条款（graph_delta_note）写明触发面（新观测端点/新路由/新表列/新 SSE 事件/改被验证对象语义）。**裁定成立 · 本帽认可按实判口径**。

---

## 三、重点抽查（本帽真跑）

### B1 10 行抽 5 组实核

| 抽核项 | task 声称 | 本帽真跑 | 结论 |
|--------|-----------|----------|------|
| #1/#2/#3 用例计数（11 文件） | lg_rag_http 11 / sse_resume 10 / sse_hitl 10 / sse_stream 8 / hitl 20 / hitl_resume 19 / hitl_resume_events 13 / capability_gateway 32 / idempotency 17 / persistence_db 15 / admin_observability 12 | `grep -c 'def test_'` 逐文件真跑：**11 文件全部吻合** | **成立** |
| #4 conftest budget fixture | conftest.py budget 命中 · 新增独立 fixture 不改既有语义 | `tests/conftest.py` :202-220 `_reset_capability_budget` + `budget_reset()` 在案 | **成立** |
| #5 runbook 先例 | hitl_persistence_smoke.py/.sh · hitl_approval_loop.py/.sh 在案 · `ls scripts/acceptance/` = 15 脚本 | 先例 4 文件**在案**；目录实际 **16 个文件**（详见非阻塞观察 1） | 先例成立 · 总数计数小差异 |
| #7 双进程零先例 | tests/ uvicorn grep 零命中 · subprocess 仅 harness_cli 非服务进程 | `grep -rnE 'uvicorn' tests/ --include='*.py'` = **零命中**；`grep -rln 'subprocess' tests/ --include='*.py'` = 仅 `test_capability_harness_cli.py` | **成立**（双进程基建零先例实证复现） |
| 附 · B1 扫描口径 | ls tests grep 命中 31 文件 · checkpointer 关联 15 文件 | 31 **吻合**；`grep -rlE 'checkpointer\|CHECKPOINTER' tests/ --include='*.py'` = **15 吻合** | **成立** |

### pytest 基线复跑

`python -m pytest tests --collect-only -q` = **1349 collected**（本帽真跑 · 与 task「1349 = 1333 基线 + memory-compliance-delete 16」一致）。

### 命名冲突扫

`grep -rn 'multi_replica\|multi-replica' app/ tests/ scripts/ docs/_tech_graph/` = **零命中**（本帽真跑 · 与 task 锚点表「预期零命中 · 落稿时真跑复核」一致）。

### 否定性断言可测性核验（一）：「归属先断言 FAIL 非 skip」

**可测 · 成立**。理由：① 归属断言有具体载体（pid/端口注入响应头或启动 banner 对拍 · SPEC §2 D2 与 task 钉死契约同文）；② 失败语义显式钉死「FAIL 非 skip」（pytest 层即 assert 非 skip 机制，可执行）；③ 有反向验证路径——变异检验①「同进程跑 → 归属断言必挂」证明该断言非空真；④ failure_paths 假阳性行三层防线（禁同进程形态 + 归属先断言 + runbook 混合负载两实例均有命中）交叉覆盖。断言不空真有机制兜底。

### 否定性断言可测性核验（二）：「图真的续跑非只断 200」

**可测 · 成立**。理由：① 断言链三要素均可机检——state 推进（checkpoint 读回比对）· answer 非空（帧内容断言）· hitl.resumed/done 帧续写同 run_id（事件表 seq 断言接 last_seq）；② 验收条与 failure_paths 双处钉死「只断 200 = 用例不合格」，给 40 留明确拒收口径；③ 负路径 409（错 thread_id）/503（未开 checkpointer）既有单进程断言形态在 `test_hitl_resume.py` 在案可直接复用（B1 #2 已指认先例文件）。「看起来批了但什么都没发生」这一最坏形态有显式断言链对着打。

### 变异检验三条 ×「预期零生产码」相容性核验（父任务指定重点）

**核验问题**：verify 类 task 预期零生产码，无生产码可变异时，变异检验三条变异的是什么？task 写法是否成立？

**核验结论：相容 · 写法成立**。逐条核：

| 变异 | task 原文变异对象 | 落面 | 与 app/ 零改动关系 |
|------|-------------------|------|---------------------|
| ① 归属可检 | 「D2 用例临时改为同进程双 app（或单进程打两次）」 | **测试形态**（tests/ 内临时改） | 过程动作 · 不产生交付 diff · 「恢复后全绿」钉死临时性 |
| ② 外置可检 | 「B 进程临时换 InMemorySaver（**或关 checkpointer 开关**）」 | **进程 env/配置面**（括号内给出纯 env 合规路径：子进程 env 关开关零代码改动） | 「或」字保证存在零 app/ 改动执行路径；选 env 面路径即与 diff 白名单完全相容 |
| ③ 失真可检 | 「budget 放大实证临时收回单实例」 | **实证拓扑**（单实例 vs 双实例 · runbook/部署面） | 与生产码无关 |

相容性机理：变异检验检验的是「断言本身不空真」（防空真规则），其变异对象天然落在**测试夹具 / 进程环境 / 实证拓扑**三面，本就无需生产码变异；task 三条写法各自自洽（均带「恢复后全绿」），工程验收 diff 白名单（`git diff master` 只含 tests/scripts/reports/docs · app/ 零改动）是**交付态**断言，变异是**过程态**动作，两者时态分离无冲突。**task 写法成立，零生产码预期与变异检验三条无矛盾。**

---

## 四、阻塞

无内容阻塞。

---

## 五、非阻塞观察（不影响本轮回合 · 30 知情即可）

1. **acceptance 目录文件总数**：task B1 口径/R0/修订记录多处写「ls 实证 15 脚本」，本帽 2026-09-22 真跑 `ls scripts/acceptance/` = **16 个文件**（含 dump_agent_graph.py / mermaid_util.py 等工具脚本）；先例本体（hitl_persistence_smoke/hitl_approval_loop 四文件）在案不受影响，计数差异属事实性小出入（git 历史显示目录最新变化早于 task 落稿），可在后续棒次顺手订正计数或注明口径（如「15 acceptance 冒烟 + 1 工具」）。
2. **变异检验②执行路径提示**：task「B 进程临时换 InMemorySaver（或关 checkpointer 开关）」括号内已给合规路径，30 执行时优先走**子进程 env 关开关**路径（零代码改动），避免字面「换 InMemorySaver」被误读为改生产码；此点 task 写法已自洽，仅为 30 执行提示。

---

## 维护者签闸（20 后 · 30 前）

- [ ] 已读 R1 审查结论
- [ ] 在 task 人工闸表将 HG-TASK-DRAFT 改为 approved（维护者 · 日期 · 落稿验收）
- [ ] 在 task 人工闸表将 HG-AUDIT-R1 改为 approved（维护者 · 日期）
- [ ] commit task 文档或确认已签
- [ ] 再下发 Harness 30 Prompt

30 Agent 将以 task 表为准；pending 时必须拒开工（见 TEMPLATE_30_gate_stop.md）。
