# CLOSE：fix-hitl-observe-node-config-injection（observe_node config 注解形态致 HITL 审批单 thread_id 空 → resume 409 根治）

> 关账日期：2026-10-28 · 关账人：00（delegate-only · 维护者 m00603「同意，开始fix task」授权 + m00627「签收」+ m00729「后端签收归档」）
> 体例承 [close_supervisor_replan_error_feedback_20261027.md](close_supervisor_replan_error_feedback_20261027.md)

## 一、任务信息

| 项 | 值 |
|---|---|
| task | [task_fix_hitl_observe_node_config_injection.md](../done/task_fix_hitl_observe_node_config_injection.md)（已归档 done/） |
| 性质 | bugfix · 00 delegate-only（10 起草 → 30 实现）· 00 本窗零实现码 |
| 由来 | run 0ebcbf86：批准后不继续——单据 hitl_fb4d74b2 decide 成功但直调 resume 409「申请里没有 thread_id」，DB 实证 thread_id=''。**PR #274（b73bb8a ruff 批量改写）把 observe_node 签名从 `Optional[RunnableConfig]` 改成 `RunnableConfig | None`**；本模块带 `from __future__ import annotations`（nodes.py:14），langgraph 1.x 只认两种字面形态（nodes.py:27-32 早已钉案）→ config 不注入 → 落库空。**影响面：#274 以来所有 supervisor HITL 审批单 resume 全灭。** |
| PR | [#296](https://github.com/Cyning12/ops-desk-api/pull/296) MERGED · squash `27fd930` · CI 4/4 绿 |
| 审查 | 无独立 R 审查（required_invoke_hats=10,30 · bugfix 轨） |
| 闸 | HG-AUDIT-R1 approved（维护者 m00627 · 00 转录）· HG-GRAPH-MODULES n/a |

## 二、交付清单

| 产物 | 说明 |
|---|---|
| `app/ops/lg_rag/multi/nodes.py:2126` | 签名回 `Optional[RunnableConfig]` + `# noqa: UP045` 同栓 + 原因注释（:22 Optional import 补回）——noqa 实证必需：无则 ruff check 即红、--fix 会再咬回（UP045 反咬实证 exit 1） |
| `tests/test_hitl_observe_config_injection.py` | 143 行双钉：形态钉（源码断言签名+noqa 同栓）· 行为钉（state 故意不带 thread_id 防直取短路，真 observe_node+InMemorySaver+InMemoryHitlStore 跑至 interrupt，断言落库 thread_id==run thread_id；先红证据 `''=='t-cfg-injection'`+UserWarning 当场复现） |

## 三、验收核验（4 条全 PASS）

| 验收 | 结果 |
|---|---|
| ① 形态钉测绿 | PASS（0.07s） |
| ② 行为钉测绿（先红后绿钉） | PASS |
| ③ ruff 钉版绿 + 全量零新红 | PASS · 28F/1948P/3s（基线+2 钉 · 邻域 11 红取证为修复前既有环境红） |
| ④ 40 live 复跑 #2140 query | PASS · run 1039c1a9：单据 hitl_c4994ba3 **thread_id=9301935e…非空** → 批准 resume 200（13:26:13）→ seq14 t2 执行 done → seq19 done{resumed}；同场补完 task A 验收 5 与 NO_PROXY fix live 验收 |

## 四、偏差与照登

1. **探针残留事故照登**：m00619 UP045 实证探针 `set -e` 在 ruff exit 1 中断，nodes.py 探针改动残留工作区 → 已 git checkout 还原（00 零实现纪律）；教训：探针脚本不用 set -e 拦预期非零退出。
2. **合并 rebase 冲突**：squash 27fd930 与本地 master 旧草案 commit（e04c4cf）撞 AA 冲突 → 以合并版（含 approved 闸转录 8648093）为准，本地旧草案自动丢弃。
3. **显示层曾掩盖落库为空**：sse_stream.py:455 兜底填 thread_id 使 SSE 载荷看似正常——排障教训：事件载荷 ≠ 落库真值，须 DB 实证。
4. **存量损耗不回填**：#274 期空 thread_id 单据（如 hitl_fb4d74b2）永不可 resume（409 fail-closed 防呆正确），task 非范围已声明。

## 五、遗留移交

| 项 | 去向 |
|---|---|
| 前端 HitlApprovalCard decide→resume 链断 | `docs/tasks/active/task_fix_hitl_card_resume_reentry.md` 草案（归属 web 仓 · pending；今日复跑 resume 正常发出，原症状未复现，剩余幂等/错误分类项待维护者裁决收窄或归档） |
| replay 追帧观感（68s/14 次轮询似卡死） | 维护者 m00729 令：web 仓新增 task 对应性修复（00 起草中） |
| `state["hitl_checkpoint_id"]` 恒 None | task 非范围已声明，另议另立 |
| 既有 pytest 28 红清理 | 仍待另立 task（承 PR #293 裁决口径） |

## 六、维护者 checklist

- [x] 验收 4 条核验完毕（①②钉测 · ③对账 · ④ live 维护者签收）
- [x] 00 delegate-only 纪律核验（本窗零实现码 · 30 委派 d58d368f）
- [x] 闸真值落闸表（维护者签收 00 转录）
- [x] CI 4/4 绿 · PR #296 合并（squash 27fd930）
- [x] 归档 done/ · README 登记 · 50 invoke 落盘
