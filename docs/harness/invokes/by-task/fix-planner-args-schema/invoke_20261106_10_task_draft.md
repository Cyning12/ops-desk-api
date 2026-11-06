# invoke · 10 起草 · fix-planner-args-schema（2026-11-06）

| 项 | 值 |
|----|----|
| hat | `10`（task 起草 · 承 issue #339 维护者令） |
| task_slug | `fix-planner-args-schema` |
| task 文件 | `docs/tasks/active/task_fix_planner_args_schema.md` |
| 分支 | 落稿 `agent/planner-args-fix-task-0796db4a2434`；30 执行分支预登记 `fix/planner-args-schema`（base `master` · 待闸签收后另行授权） |
| 指令来源 | issue #339 维护者 comment `6673790438`（2026-11-06 01:02）：「请按 Harness 流程起草 fix task 文档（10 帽活：只产 docs/tasks/active/ task 档 + npx spec-wave task lint PASS + PR；不要实现业务码）」+ comment `6674337004` 补发触发（受理要求同前）· 受理依据 = 维护者 2026-11-06 08:48 授权（lead 全程代行签收与验收） |

## 输入真值（已读）

- issue #339 正文（backlog：planner string-args → args_schema_invalid · 两轮一致 · 阻断全部写能力真落笔 · 建议 fix task 流程先诊断 prompt 资产根因再定修复面 · 红线 = SSE 零 diff / 写消费语义 freeze / resume 单路径 / 改码面收敛 / 红测先行 · 负样本 = planner 输出 args 通过 schema 校验 · 处置形态决策点留设计闸）+ comment `6673790438` 五要求（先诊断根因 / task 档六要素 / 红测先行 / 红线入 failure_paths / lint PASS 出货）。
- 同源四单偏差链：#329 40 invoke（`invoke_20261105_40_verify.md` 偏差② · run `5bc63c8b…`/`f193a5b9…` 两轮一致）· #334 40 invoke（`invoke_20261106_40_verify.md` 偏差② · 维护者 item 3 口径）· #335 偏差② · stage-w 40 观察③（prompt 未文档化 args 字段 · 非阻塞登记）。
- 10 档只读诊断（机制链五环 · file:line 全锚入 task 背景节）：prompt 资产 `lg_rag.supervisor.system.md:10` / `lg_rag.supervisor.suffix.system.md:14`（v2 均未文档化 args）→ schema `subtasks.py:21,23`（input:str 合法 · args:dict 存在但 prompt 未提）→ `_parse_subtasks`（nodes.py:186-231）零识别 → `_format_capability_catalog`（nodes.py:104-121）目录块不含 args_schema → `tool_exec_node`（nodes.py:1970-1974）兼容回退 input → gateway `_prepare_call`（gateway.py:446）fail-closed 拦截。
- 同链先例：task_fix_seen_surface_idempotency（设计闸 + 四红线 + 红测端到端 + 10 档实扫声明）· task_supervisor_replan_error_feedback（拒收反哺面）。

## R 轮结论摘要

| 轮 | 结论 |
|----|------|
| R0 | 缺陷 = prompt 资产面预存在问题（非回归非 #332 引入）；10 档只读诊断五环机制链已锚（根因环 = 两份 supervisor 资产 v2 未文档化 args 字段）——「约束在哪一层失效」实锤至资产层 |
| R1 | 范围 = 处置形态落地（闸签为准）+ 红测负样本 + 常规对拍 + 条件旧测适配；非范围十一条（fail-closed 永不放宽 / SSE / HITL 消费 freeze / resume 单路径 / 改码面收敛 / 结构化网关级改造不自作主张 / web 面） |
| R2 | 设计闸 HG-PLANNER-ARGS-DESIGN 处置形态三案：①拒收并约束输入（解析层识别 + 统一口径 + 反哺重规划）②修复资产（prompt 文档化 args ± 目录块注入 args_schema）③转独立设计任务（修复面溢出时诊断销项另立）；影响面 = 全部写能力 40 验证等待 · 签认须带 30 探针证据 |
| R3 | FP-1~FP-11（四闸拒开工 / SSE 零 diff / HITL 消费 freeze / resume 第二实现 / 改码面外溢 / fail-closed 放宽伪修复 / 负样本未绿 / 30 越权自裁 / 修资产只改字面 / 拒收静默吞单 / 解析兜底波及） |
| R4 | 负样本经真规划→派发→执行路径驱动（禁直造 state）；先红（复现两轮一致拦截形态）后绿（schema 校验通过 + 真落笔断言）；常规对拍防过紧；live 全写能力解锁留 40 |
| R5 | 落稿 · 四闸 pending · NO-GO 20/30 · lint PASS 出货待审 · 30 待闸签收后另行授权 |

**actual_last_round**：R5 · **early_stop**：no · **residual_risks**：处置形态取舍待设计闸签认（影响面 = 全部写能力 40 验证等待 · 不轻裁）

## task_slug 说明

`fix-planner-args-schema`（fix 类 · 承载面 = planner args 形态 vs schema 校验冲突）；task 文件 / 30 分支 `fix/planner-args-schema` / invoke 目录同名一致。

## 闸表（全部 pending）

| 闸 | blocks | 说明 |
|----|--------|------|
| HG-TASK-DRAFT | 20-R1, 30 | 初稿未经 20-task-audit 审查与维护者签收 |
| HG-AUDIT-R1 | 30 | 20-task-audit R1 审查文未落盘 |
| HG-GRAPH-MODULES | 30 | `none` 口径待签（无图谱面 · 承 seen-surface 先例；30 实扫出图谱面须回签） |
| HG-PLANNER-ARGS-DESIGN | 30 | **设计闸** · 处置形态裁决三案（拒收并约束输入 / 修复资产 / 转独立设计任务）+ 影响面签认（全部写能力 40 验证等待） |

## 自检

| 命令 | 结果 |
|------|------|
| `npx --yes spec-wave@3.5.0 task lint --file docs/tasks/active/task_fix_planner_args_schema.md` | **PASS**（2026-11-06 · 零 warn） |
| `npx --yes spec-wave@3.5.0 task lint-wiki-delta --target .` | **PASS**（scope all · 本档 wiki_delta 预填） |

## 禁区复核

- 未改 `app/` / `alembic/` / `tests/`（仅 `docs/tasks/active/` + 本 invoke）。
- 未签任何 human_gate（四闸 pending 待维护者/lead 签收；处置形态留 HG-PLANNER-ARGS-DESIGN 随档裁决）。
- 10 档诊断只读（grep/sed 实扫 · 零仓内状态变更）。
