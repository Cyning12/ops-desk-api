# CLOSE：stage-w-write-expand（阶段 W 扩写能力 · 受控写闸链接入第二条真实窄写能力 · Q1=S1 仓内落笔型写）

> 关账日期：2026-11-05 · 关账人：bot 全棒链执行（00 → 20 → 30 → 40 → 50 CLOSE）· 维护者令 issue #323 comment `6657553318`（PR #328 合入后按档 CLOSE）
> 体例承 [close_supervisor_replan_error_feedback_20261027.md](close_supervisor_replan_error_feedback_20261027.md)

## 一、任务信息

| 项 | 值 |
|---|---|
| task | [`task_stage_w_write_expand.md`](../done/task_stage_w_write_expand.md)（已归档 done/） |
| 性质 | feature / 受控写扩切片 · SPEC v0.1 承接（HG-SPEC-SIGNOFF approved） |
| 由来 | issue #323 签收链：阶段 W 闸链（PR #303 + fix #307/#313/#319）上只有语义 mock 写能力 `testing.write.echo`——本 task 把第二条**真实**窄写能力 `ops.write.run_note` 端到端接入既有受控写闸链 |
| PR | [#325](https://github.com/Cyning12/ops-desk-api/pull/325)（00 拆 task）· [#326](https://github.com/Cyning12/ops-desk-api/pull/326)（20-task-audit R1 + 三闸代录）· [#327](https://github.com/Cyning12/ops-desk-api/pull/327)（30 实现 · squash `51030a4` · CI 4/4 绿 · lead 终审 APPROVED）· [#328](https://github.com/Cyning12/ops-desk-api/pull/328)（40 复跑销项 · squash `3d08529` · CI 4/4 绿 · lead 终审 APPROVED） |
| 闸 | HG-STAGE-W-EXPAND-DESIGN（Q1=S1 · 维护者签）· HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES（lead 代录 · 依据 issue #323 comment `6652283580` 预授权 + PR #326 R1 审查文 PASS） |

## 二、交付清单

| 产物 | 说明 |
|---|---|
| `app/ops/capability/manifests/ops.write.v1.yaml` | 第二条真实窄写能力 `ops.write.run_note`（run 备注/审计便签）· tenant_scoped=true · hitl.required+snapshot_fields · 顶层 idempotency_key · **三层显式打开**（不进默认加载面 + `OPS_CAPABILITY_ALLOW_WRITE_TAGS=run_note` 独立写 tag · 不复用 testing tag） |
| `app/ops/capability/defaults.py::ops_write_run_note` + `note_store.py` | 真落笔 adapter（async local_fn · tenant 只取 ctx fail-closed 二道 · approval_id 落便签行 · 幂等 store claim + DB 唯一约束双保险 · DB IO 延迟 import 对齐 idempotency/receipts 先例 · import-linter 白名单同例登记） |
| loader **V13**（`manifest.py`） | SPEC v0.1 Q4 / A2+ 加载期断言：write 级能力 `tenant_scoped: true` 强制 · mock 特例清单不扩容（仅 `testing.write.echo` · testing/mock tag 谓词 · 冒充 id 无谓词 tag 亦拦）· 口径仅 side_effect=write 承「不碰 irreversible」 |
| `ops_capability_notes`（`models.py` + alembic `20261105_capability_notes`） | Q3 新表（随签义务履行）：唯一约束 `(tenant_id, idempotency_key)` = FP-4 重放不双写 DB 级兜底 · `approval_id` 串链列 · 索引 `(run_id)`/`(approval_id)` · 迁移可逆 |
| `tests/test_stage_w_write_expand.py` | 16 枚（红测先行红→绿可见）：A1 机制全链 / V13 四断言 / FP-4 双形态（store 命中 + DB 唯一约束兜底 · store 丢失模拟）/ A3 三处 tenant 一致 + 租户内键隔离 / A2 负样本组 / A4 四照串链 / A5 grep |
| D4 图谱回写 | `l1/01_modules.md` capability 行 + db 行登记 + HG-GRAPH-MODULES 30 回写回签行（G-L1 · 不新增一级模块 · 不增 implementedBy） |

## 三、验收核验（A1–A8 全 PASS）

| 验收 | 结果 |
|---|---|
| A1 端到端竖切 | **机制段** 16 测全绿（闸拦→pending→decide→resume→消费→真落笔）· **live 八段**实录（40 复核）：catalog 可见 → hitl.waiting → pending → decide（重复 409 live）→ resume（写窗 409 live）→ replan 保号 → 消费命中真落笔 → done{status:resumed} 契约帧——段⑦⑧经测试等价 shim 补位（见偏差①） |
| A2 负样本组 | 全绿：无审批 fail-closed / rejected 零落笔 / tenant_scope_missing / write_not_confirmed / env 未开启不可见 / 放行 testing tag 不可见 / 幂等重放不双写双形态；跨租户 404·头 403 由 F1–F6 既有测试承接 |
| A2+ 加载期断言 | V13 四断言全绿（强制/放行/mock 例外/谓词钉死） |
| A3 租户下推 | intent/审批/便签三处 tenant 一致 + 同键跨租户隔离（A1/A3 断言 + live 便签行 `ops-desk-pilot`） |
| A4 审计串链 | span approval_id + 消费台账 + 回执（write_confirmed）+ 便签行 approval_id 四照同单（live `hitl_bf2cc75d…` 串链实证） |
| A5 反回归 | registry/policy/lg_rag/gateway/hitl/SSE 对 merge-base **零 diff**（git 对拍）· resume 单路径 grep 绿 · 判序零 diff 全组钉死 |
| A6 freeze 零破 | SSE 事件表零 diff · `hitl-browser-decide-v1` 语义回归绿（既有 test_hitl_pending_decide 全组） |
| A7 工程面 | 全量 pytest 2057 passed（4 failed 均 master 既有本地红 · 干净树复证零新增）· ruff 零新增 · graph-compile EXIT=0 · G-L1 回写 |
| A8 lint | `spec-wave task lint` PASS（30/40/CLOSE 各时点） |

## 四、偏差与照登

1. **`_worker_state` Send 载荷丢 `run_id`（既有缺陷 · 40 live 实证 · 非本 task 回归）**：`lg_rag/multi/nodes.py:1359` 构造工人 Send 载荷不含 `run_id`（仅 delegation on 附带）→ tool_exec 写审批消费门 `_run_id_of(state)` 空串 fail-closed → **resume 后重下发永远再拦**。潜伏于 PR #303（全部写能力同受影响），单元测试直调 tool_exec（自带全 state）故从未暴露；#327 前后行为一致。修复形态（载荷补键）已 shim 验证 → **另立 fix task**（建议一并补「Send 载荷回归测试：工人可见 state 键集」），维护者裁定。
2. **supervisor system prompt 未文档化 `args` 字段**：写工具结构化入参靠提示词即兴（live 三轮才稳定产出结构化 args）——纳入后续 prompt 资产波次视野，非阻塞。
3. **live 环境噪点**：siliconflow 偶发单调用挂起数分钟（40 invoke 偏差②）；worktree 承主 checkout `.env` 的本地套件污染纪律（40 invoke 偏差③）——均环境性，如实登记。
4. **本地产能 4 枚既有红**：diff-whitelist 锚点漂移 ×2 + env 依赖 ×2（CI 无 PG skip 面）——master 既有，与本 task 无关，双口径复证零新增。

## 五、遗留移交

| 项 | 去向 |
|---|---|
| `_worker_state` Send 载荷补 `run_id`（+ 工人 state 键集回归测试） | **另立 fix task** · 修复形态已 shim 验证 · 维护者裁定优先级 |
| supervisor prompt `args` 字段文档化 | 后续 prompt 资产波次视野 |
| 既有本地产能红 4 枚（锚点漂移/env 依赖 · CI skip 面） | 建议另立清理 task |

## 六、维护者 checklist

- [x] 验收 A1–A8 核验完毕（30 自报 + 40 独立复跑 + lead 双棒终审）
- [x] 闸真值落闸表（四闸 approved · HG-STAGE-W-EXPAND-DESIGN 维护者签 · 余三闸预授权代录留痕）
- [x] R1 审查文随 PR #326 落库 · 30/40 invoke 全棒留痕
- [x] CI 4/4 绿 ×2（#327 · #328）· squash 合入（`51030a4` / `3d08529`）
- [x] 归档 done/ · active README 登记 · Hub done/README 补登 · 50 invoke 落盘
- [x] issue #323 关账声明（全棒链：SPEC 审查签 → 拆 task+设计闸签 → 20-task-audit → 30 实现 → 40 复跑）
