# CLOSE：supervisor-replan-error-feedback（重规划错误反哺：契约闸失败原因 + 可用字段进 prompt）

> 关账日期：2026-10-27 · 关账人：00（delegate-only · 维护者会话签收 HG-AUDIT-R1 + 验收④口径裁决 + produces 覆盖认可）
> 体例承 [close_vector_waterline_local_rerun_20261017.md](close_vector_waterline_local_rerun_20261017.md)

## 一、任务信息

| 项 | 值 |
|---|---|
| task | [task_supervisor_replan_error_feedback.md](../done/task_supervisor_replan_error_feedback.md)（已归档 done/） |
| 性质 | feature · 00 delegate-only 单窗多棒（20 R1 → 30）· 00 本窗零实现码 |
| 由来 | 2026-10-27 实测 run `cb25483697624aafbb1cf864015c3b10`：write 步契约闸拦（`contract_missing_field`：声明 `['title','body','status']`，前驱实际字段 `state`），重规划原样照抄错误声明，两轮 `budget_exhausted`；维护者裁定：第一轮的错误必须反哺第二轮 |
| PR | [#293](https://github.com/Cyning12/ops-desk-api/pull/293) MERGED · squash `be78b5a` · CI 4/4 绿 |
| 审查 | R1 [task_supervisor_replan_error_feedback_audit_R1_20261027.md](../../harness/reviews/task_supervisor_replan_error_feedback_audit_R1_20261027.md) PASS 零阻塞（4 项非阻塞记录）· 随 PR 落址A |
| 闸 | HG-AUDIT-R1 approved（维护者 2026-10-27 会话签收 · 00 转录闸表）· HG-GRAPH-MODULES n/a（不动图谱分层） |

## 二、交付清单

| 产物 | 说明 |
|---|---|
| `app/ops/lg_rag/multi/step_contract.py`（B 层） | `contract_missing_field` 拦截 detail 附前驱实际可用字段清单 `sorted(output.keys())` + 「声明字段不存在，请从实际产出字段中选择」；consumes 与 produces 未兑现两分支同覆盖（R1 P1，维护者认可）；output 非 dict 不校验不替模型猜语义不变 |
| `app/ops/lg_rag/multi/nodes.py`（A 层） | `_format_prefix_block` 新增可选 `failed` 参数：失败步追加「→ 失败：{blocked_by}：{error 截断 400}」+ 切勿照抄提示；无失败步 prompt 逐字节零 diff（preserved_block FP 先例口径） |
| `tests/test_supervisor_replan_error_feedback.py` | TC1-TC4（+259 行），复用 hitl_approval_consumption fixture 体系，_cb2548_rows 场景罐头 |

## 三、验收核验（4 条全 PASS · 维护者裁决口径在案）

| 验收 | 结果 |
|---|---|
| ① 复现 cb2548 → 第二轮 prompt 含失败原因行+字段清单 | PASS · TC1 spy 断言 |
| ② 第二轮 consumes 收敛真实字段名 | PASS · TC2 两轮闭环（端到端实测留评测，符合验收弹性口径） |
| ③ 主路径零 diff | PASS · TC3（failed 缺省逐字节一致）+ TC4（locked 非空无失败步与 master 形态逐字节等）双保险 |
| ④ pytest + ruff 绿 | PASS（裁决口径）· ruff 0.15.21（CI 钉版）全绿；pytest 28 failed/1926 passed 全为既有基线（30 stash 前后清单逐字一致 + 00 独立全量复跑同数复核），维护者按「不引入回归」签收，既有失败另立 task 清理 |

**关键实录**：目标组 45 passed（新 4 + hitl_approved_replan_quality + step_contract）；graph-compile.sh EXIT=0；CI check/import-linter/pytest/lint-wiki-delta 4/4 绿。

## 四、偏差与照登

1. **lint-wiki-delta 首红照登**：task 草案建档漏 Harness 元信息块（`wiki_delta` 缺字段 fail-closed 拦截），`5976ece` 补登 12 字段后转绿。与 2026-10-11 `task_repo_logging_init` 同类卡法，流程拦截正常工作。
2. **既有 28 红照登**：`test_strategy_*`/`capability_*` 等远域模块工作区既有失败，与本改动无关（双口径实证），**本 task 不处置**，建议另立清理 task。
3. **produces 分支覆盖**：B 层字段清单注入覆盖 consumes+produces 两分支（R1 P1 提示 · 同一失败模式 · 维护者裁决认可不回退）。
4. **00 核验误报照登**：00 首验误用 miniconda ruff 0.9.10（UP038×12 假红）与裸 python（缺 asyncpg）；仓 CI 钉 `ruff==0.15.21` + `.venv`，钉版环境复跑全绿。教训：核验必用 `.venv/bin/` 前缀。

## 五、遗留移交

| 项 | 去向 |
|---|---|
| 既有 pytest 28 红清理（strategy/capability/multi_replica 等远域） | 建议另立 task，维护者裁决优先级 |
| manifest 补 output_schema（源头消灭字段名猜测） | task 非范围已声明另立，未建档 |
| 端到端实测（真实 run 复跑 cb2548 场景） | 评测轨另做 |

## 六、维护者 checklist

- [x] 验收 4 条核验完毕（①②③ PASS · ④ 裁决口径 PASS）
- [x] 00 delegate-only 纪律核验（本窗零实现码 · 20/30 全委派）
- [x] 闸真值落闸表（HG-AUDIT-R1 维护者签收 00 转录）
- [x] R1 审查文随 PR 落址A（维护者裁决入库）
- [x] CI 4/4 绿 · PR #293 合并（squash be78b5a）
- [x] 归档 done/ · README 登记 · 50 invoke 落盘
