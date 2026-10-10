---
hat: 10
task_slug: hitl-auto-resume-claim-race
date: 2026-10-10
---

# Invoke：10 起草 hitl-auto-resume-claim-race（auto_resume 认领竞态 · decide 同秒首跑连续 stranded_checkpoint）

> **帽**：Harness 10-task（起草） · **task**：`docs/tasks/active/task_hitl_auto_resume_claim_race.md`
> **分支**：`task/hitl-auto-resume-claim-race`（base = master `1117286` · T4 PR #221 已 merge）
> **纪律**：骨架先行增量落盘 · 禁改实现码 · 三人工闸 pending 不代签 · 方案开放不锁死（留 30 实证裁定）

## 过程留痕

- 2026-10-10 10 骨架先行落盘（本文件 + task 全文）→ 逐节增量填充（元信息/人工闸/背景与实证锚点/现状锚点/钉死契约/范围+非范围/failure_paths/B1/验收 TC1–TC5/依赖/必读/R0–R5/修订）。
- lint 首跑 FAIL（E1 元信息表形态不识 task_slug + E8 缺 wiki_delta 行——表头/键名形态未对齐 T2 模板）→ 按 `docs/tasks/done/task_hitl_approval_consumption_auto_resume.md` 形态改写（`| 字段 | 值 |` + `**task_slug**` 粗体键 + 反引号值）→ 复跑 **LINT: PASS · exit 0**（`npx --yes spec-wave task lint --file docs/tasks/active/task_hitl_auto_resume_claim_race.md` · 余 W3 自检结论占位符 draft 期合法 · close 前 40 回填）。

## 依据输入（10 已逐行实读 · 实证锚点）

- **验收实证真值**：`docs/acceptance/20261010_hitl-consumption-loop_local_acceptance.md` D1 偏差表 + 项6 auto 链段——**现于分支 `acceptance/20261010-hitl-consumption-loop` @ `f57b4ae` · 未 merge master**（task 引用已注明分支/commit）。D1 逐字要点：decide 与 `hitl_auto_resume_triggered` 同秒 17:00:51 · 首次认领起连续 6 次 `ResumeError: stranded_checkpoint`（resume.py:244）· 补偿扫描 5s 周期 · 约 17:01:23（≈30s）恢复成功 · 手动 resume 分钟级从未触发 · 项6 其余全通（triggered→claimed→consumed→token→echo）。
- **T2 交付原文**：`docs/tasks/done/task_hitl_approval_consumption_auto_resume.md`（256 行 · 命名/结构/验收勾选/思考轮表头模板）+ `app/ops/hitl/auto_resume.py` 全文（:128-148 触发派发 · :151-182 认领-执行「异常只落日志等下轮」兜底 · :185-222 扫描 · :225-247 scanner）。
- **stranded 判定源**：`app/ops/hitl/resume.py` :41-51（code→HTTP 映射注释 · stranded_checkpoint→409 钉「旧版本格式残留 · 永远恢复不了」）+ :211-282 `_resume_with`（aget_state → 无 tasks 抛 not_interrupted :230-235 → tasks 有但 interrupts 全空抛 stranded_checkpoint :236-248 · 原设计意图=拦 langgraph 0.2→1.2 升级残留防 TypeError 500）。
- **竞态机制链**：`app/ops/lg_rag/multi/nodes.py` :1820-1822 注释明示「**落库先于挂起**」——`_persist_hitl`（:1610-1706）先写 pending 行，`interrupt()`（:1831）才抛 GraphInterrupt · LangGraph checkpoint（含 interrupt 元数据）落库在其后 ⇒ pending 行可见 ⇏ interrupt 元数据可见 = 竞态窗口根源。
- **触发器挂点**：`app/ops/hitl/router.py` :242-254（decide 成功分支 approved∧auto → `schedule_auto_resume` · OA callback 不挂）。
- **SPEC**：`docs/spec/hitl-approval-consumption/SPEC-hitl-approval-consumption_v1.md` §2 D5（:102-111 · Q6 进程内后台任务+行锁认领+补偿扫描 · Q7 env+resume_mode · 设计纪律 6 无状态恢复/禁 HTTP 自调 · FP-8~FP-11 · A9/A10）——本 task 为 T2 交付物的验收偏差收口（bugfix 性质 · 无需新 SPEC）。
- **B1 冲突面清点**：tests/test_hitl_auto_resume.py（T2 39 枚 · :526/:583/:688）· tests/test_hitl_resume.py:230-259（stranded→409 永久语义断言 · 与竞态复现构造同形态须区分）· tests/test_hitl_resume_events.py / test_hitl_pending_decide.py / test_hitl.py / test_lg_rag_sse_hitl.py / test_hitl_approval_consumption.py。
- **图谱**：`docs/_tech_graph/l1/01_modules.md` hitl 行（:39）/lg_rag 行（:35）已含 T2 机制备注 ⇒ 预判无图谱变更照实写。
- **基线钉案**：pytest 4 failed=环境性基线（capability_lookups×3+lg_rag_multi×1 · 零新增红口径）· 仓级 verify EXIT=2（done/ 遗留 92 缺口 · 非本 task 归因）。

## 裁定摘要

- **竞态根因初步研判（开放 · 不锁死）**：机制链=nodes.py「落库先于挂起」使 pending 行可见早于 checkpoint interrupt 元数据落库；手动流人批分钟级延迟天然掩盖窗口，auto 流 decide 同秒认领直读快照（tasks 有 · interrupts 空）→ 命中 stranded_checkpoint。窗口 ≈30s 远超单次 DB 提交，疑似绑 SSE 连接/astream 生成器收尾生命周期（验收脚本 curl 持连期间 checkpoint 终写未提交？）——**仅假设，待 30 实证定位**。
- **候选修复面（开放给 30 实证后定 · 起草不锁死）**：A 认领后执行前只读就绪校验（竞态化为「等下轮」· 消错误日志与 409 误伤）· B decide 触发侧 grace delay（最简治标 · 若窗口绑连接生命周期则不可靠）· C 执行体内对 stranded_checkpoint 有界退避重试（~30s→秒级 · 须区分 transient/永久 · FP-3 防失控）· D 根因侧 interrupt 元数据落库时序（预判超最小面 · 原则上不动 LangGraph）。
- **transient/永久语义裁定**：resume.py:41-51 把 stranded_checkpoint 钉「永远恢复不了」——竞态证明存在 transient 形态；但手动 resume 409 对外语义钉死不动（test_hitl_resume.py:230 断言存续 · 若 30 裁定重分类须动此断言 → 先过 20/维护者裁定 · 钉死契约 2）。
- **最小面**：改动收敛 `app/ops/hitl/auto_resume.py` 认领-执行路径（± resume.py 内部注释/分类 · ± 测试）；nodes.py/store.py/router.py/T1/T4 面 diff 空，实证须动则 GATE_STOP 回 10/维护者。
- **验收口径 TC1–TC5**：TC1 注入式竞态窗口复现（禁赌真竞态 · FP-1）· TC2 修复后零 stranded_checkpoint（caplog 断言）· TC3 live 实证 auto 首跑无重试直达 · TC4 反回归（真·永久 stranded 409 存续 + manual 零 diff + 39 枚原样绿）· TC5 工程面（pytest/ruff/graph-compile/lint/闸序）。
- **图谱判定**：照实预判 n/a——候选修复面全部落在 hitl 行备注既有「触发器/SKIP LOCKED 认领/补偿扫描」覆盖面；若 30 引入新 env 旋钮或新机制面 → hitl 行备注回写 + HG-GRAPH-MODULES 00 代录。
- **人工闸**：HG-TASK-DRAFT/HG-AUDIT-R1/HG-GRAPH-MODULES 全 pending · 10 未代签。

## 留给 20 审查要点

1. **竞态根因研判充分性**：「落库先于挂起 ⇒ pending 可见 ⇏ interrupt 元数据可见」链条是否钉严；窗口 ~30s 与 SSE/astream 生命周期绑定仅假设 —— 30 实证义务（TC1 先行红测或实证日志）是否足够强。
2. **方案开放性**：候选 A/B/C/D 不锁死是否符合委派「开放给 30 实证后定」；钉死契约 5「30 须先复现再定方案」是否足以防直接拍脑袋实现。
3. **钉死契约 2（手动 409 语义）**：stranded_checkpoint transient/永久区分与 test_hitl_resume.py:230 断言存续的张力 —— 重分类若发生，「先过 20/维护者裁定」门槛是否合适。
4. **TC1 注入式复现可构造性**：「checkpoint 有 pending tasks 无 interrupt 元数据 → 随后可见」在内存 saver/mock aget_state 下可否确定性构造（T2 39 枚中 :583 store-rebuild 补偿组为最近先例）。
5. **最小面与 GATE_STOP**：nodes.py interrupt/persist 时序 diff 空是否过强（若实证根因确在落库时序侧，方向 D 被钉死契约 4 挡回 10/维护者 —— 此为刻意设计，请 20 确认裁定权归属表述准确）。
6. **图谱预判 n/a**：若 30 实证新增机制面（新 env/新台账键），HG-GRAPH-MODULES 代录义务触发条件是否钉清。
7. **验收文档分支引用**：实证真值未 merge master（acceptance/20261010-hitl-consumption-loop @ f57b4ae）· task 以分支/commit 引用是否足够（或须推动验收文档先行 merge · 裁定权在维护者）。

## 修订

| 日期 | 说明 |
|------|------|
| 2026-10-10 | 10 骨架先行落盘 → 增量填充完成 · lint 首跑 FAIL（E1/E8 表形态）按 T2 模板改写 → 复跑 PASS exit 0（余 W3 占位符 draft 期合法）· 裁定摘要与 20 审查要点回填 · 三闸 pending 未代签 |
