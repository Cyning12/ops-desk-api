# CLOSE：fix-worker-state-send-run-id（`_worker_state` Send 载荷补 run_id · HITL resume 后写消费闭环修复）

> 关账日期：2026-11-05 · 关账人：bot 全棒链执行（10 → 20 → 30 → 40 → 50 CLOSE · 同日闭环）· 维护者令 issue #329 comment `6660516133`（40 复跑销项）+ 裁定 comment `6661645452`（(a) 按机制面 PASS 关账 · planner args 另波 #339）
> 体例承 [close_stage_w_write_expand_20261105.md](close_stage_w_write_expand_20261105.md)

## 一、任务信息

| 项 | 值 |
|---|---|
| task | [`task_fix_worker_state_send_run_id.md`](../done/task_fix_worker_state_send_run_id.md)（已归档 done/） |
| 性质 | fix / 缺陷修复（Send 载荷丢键 · 消费门 fail-closed 静默失效 · PR #303 时期潜伏非近期回归） |
| 由来 | issue #329（40 live 全链实测偏差登记①实锤：`_worker_state` 载荷无 `run_id` → 写审批消费门取空串 fail-closed → resume 后重下发永久再拦 · shim 补位八段全通）· 上游 task_stage_w_write_expand（同日 CLOSE · 偏差#1 移交本单） |
| PR | [#331](https://github.com/Cyning12/ops-desk-api/pull/331)（10 起草 · squash `5bec9d6` · CI 4/4 绿 · lead review APPROVED 签认四闸）· [#332](https://github.com/Cyning12/ops-desk-api/pull/332)（30 实现 · squash `ba03800` · CI 4/4 绿 · lead 验收六条件全过） |
| 闸 | HG-WORKER-STATE-RUN-ID-DESIGN（两决策点裁决 = 案 A `_worker_state` 补键 + 回归影响面签收 · lead 签）· HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES（lead 签认 · 依据 PR #331 review `5785422963` + issue #329 `6658235851`/`6658823187`） |

## 二、交付清单

| 产物 | 说明 |
|---|---|
| `app/ops/lg_rag/multi/nodes.py::_worker_state` | Send 载荷补 `run_id` 键（**案 A** · 非空才写镜像 supervisor_started_at 可选键先例 · FP-7 空串不写入 · 注释留痕缺陷机制）；改码面唯一 +8 行；delegation 分支 :1666 重复赋值行保留（同值幂等） |
| `tests/test_fix_worker_state_send_run_id.py` | 6 枚红测先行（先红 3 后绿）：负样本走真派发路径（route_next_subtask → _worker_state → tool_exec_node · 补 40 live 才暴露的单测盲区）预置 approved 单据 → 消费命中 + 真落笔三照（便签行/回执/消费台账 span · approval_id 串链）+ 键集钉双形态（有值含 run_id · 空值不写入）+ delegation on 对拍 + FP-9 防误读（无审批仍拦死） |
| 旧测适配 1 枚（适配不放宽） | `test_lg_rag_delegation_wiring.py::test_off_mode_dispatch_zero_diff`——off 模式零 diff 契约收窄为「不注入委派 artifact」，载荷身份键 run_id 随案 A 裁决全派发路径下发（断言对象改写 · 依据留痕） |
| 过程文档 | task 档（四闸签认 + 全棒自检）· 20-R1 审查文（lead 人审转录）· 10/20/30/40/50 invoke 全落盘 |

## 三、验收核验（全 PASS · 维护者裁定 (a) 机制面关账）

| 验收 | 结果 |
|---|---|
| 红测负样本（维护者红线） | ✅ 6 枚先红 3（KeyError: run_id → 消费门再拦 = 40 偏差#1 单测形态）后绿；40 live 免 shim **消费闭环 ×2 实证**（`capability_write_approval_consumed` → 执行放行 · pre-fix 永久再拦面） |
| 键集回归钉 | ✅ 有值含 run_id（键集精确钉死）· 空 run_id 不写入（FP-7） |
| delegation on 对拍 | ✅ payload run_id 值不变（决策点②签收面） |
| 消费门 fail-closed 零变化 | ✅ 未命中/读失败/过期/类型/租户负样本全绿 + FP-9 新测仍拦（`test_write_approval_gate` 全组） |
| 红线对拍 | ✅ registry/policy/event_store/hitl/SSE 零 diff · web `hitl.ts` freeze 未碰 · resume 单路径 grep 绿（30 自检 + 40 独立双证 · delta 恰 3 码文件） |
| 旧测 grep 影响面 | ✅ step_contract 三测 / redlines R14 段零影响（183 passed 实跑）· stage_w 16 枚全绿 · 适配 1 枚不放宽 |
| 工程面 | ✅ 全量 pytest 2063 passed · 4 failed = 既有本地产能红（diff-whitelist ×2 / env ×2 · 零新增）· ruff 零新增 · graph-compile EXIT=0 · task lint PASS |
| 40 复跑销项（条件触发） | ✅ 机制面 PASS——stage-w 40 偏差登记①**实质销项**；偏差②（真落笔 · planner string-args）维护者裁定另波跟踪（issue #339 · 同源 stage-w 观察③ · 预存在非本链） |

## 四、偏差与裁定留痕

- **偏差②（真落笔未达成 · 另波 #339）**：live 八段①-⑦达成（消费闭环 ×2 实证），⑧真落笔两轮采样均被 `args_schema_invalid` 拦（planner 产出 string-args）——归因 stage-w 40 观察③同源（supervisor prompt 未文档化 args 字段）· 预存在 · 非本 task 缺陷 · 非 #332 引入。维护者裁定 (a)：按机制面 PASS 关账，planner args 另波 #339 跟踪。
- **偏差①（环境噪点）**：本机 siliconflow 间歇挂起/空响应（bounded retry 内 4-9 分钟两轮），前两轮规划失败走 .env `single_rag` 降级；环境性非仓码语义，如实登记。
- **偏差③（口径登记）**：主 .env delegation enforce → 40 专以 off 模式实测被修路径（W0 写闸 · 与 stage-w 40 live 同口径）；enforce 路径同结构由单测承接。

## 五、关账动作

- 档迁：`docs/tasks/active/` → `docs/tasks/done/`（本 CLOSE 档 + done/README + active/README 同步 + 50 invoke）；
- issue #329：维护者执行关 issue（bot 不 close issue · 已声明）；
- 后续跟踪：planner args 文档化 → issue #339（另波立项）。

## 六、棒链留痕

| 棒 | 交付 | 证据 |
|---|---|---|
| 10 | task 档起草 + 10 invoke（PR #331） | `invoke_20261105_10_task_draft.md` |
| 20 | R1 审查（lead 人审转录 · 两决策点裁决） | `task_fix_worker_state_send_run_id_audit_R1_20261105.md` + `invoke_20261105_20_r1_audit.md` |
| 30 | 案 A 实现 + 红测 6 枚 + 旧测适配 1 枚（PR #332） | `invoke_20261105_30_implement.md` |
| 40 | 独立复跑 + live 免 shim 八段（机制面 PASS · 偏差②停下报） | `invoke_20261105_40_verify.md` |
| 50 | CLOSE 收口（本档 + 归档 + 双 README + invoke 终条） | `invoke_20261105_50_close.md` |
