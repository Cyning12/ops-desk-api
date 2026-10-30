# CLOSE：lg-rag-gate-produces-unfulfilled（契约闸判定3收窄为观察留痕 + 重发前驱步逃生口指引）

> 关账日期：2026-10-30 · 关账人：00（文档健康度整理窗口补关账：PR 已于 2026-10-28 合并，active 残留为簿记滞后）
> 体例承 [close_supervisor_replan_error_feedback_20261027.md](close_supervisor_replan_error_feedback_20261027.md)

## 一、任务信息

| 项 | 值 |
|---|---|
| task | [task_lg_rag_gate_produces_unfulfilled.md](../done/task_lg_rag_gate_produces_unfulfilled.md)（已归档 done/） |
| 性质 | fix · d3a49 死锁根治（契约闸 produces 未兑现收窄 + 前缀锁定死锁带内逃生口） |
| 由来 | 2026-10-27 复跑实证 run `d3a49527929248cc953b7a5327cae2d0`（635 事件 · 400s · budget_exhausted）：t1 声明 produces `['title','body','status']` 未兑现 `status`，t2 只需 `title/body` 仍被闸判定3拦死；重规划两轮照抄同一计划，write 从未执行 |
| PR | [#297](https://github.com/Cyning12/ops-desk-api/pull/297) MERGED · squash `0a5d6109` · 2026-10-28T06:39:33Z |
| 闸 | HG-AUDIT-R1 approved（维护者 2026-10-28 签收 · m00811「签收，删除草稿」）· HG-GRAPH-MODULES n/a（`graph_change_layer=none`） |
| 姊妹 task | `task_lg_rag_capability_output_schema`（task A · PR [#294](https://github.com/Cyning12/ops-desk-api/pull/294) MERGED 2026-10-28 · 互指非范围、独立可合，A 源头消猜 / B 救得回） |

## 二、交付清单

| 产物 | 说明 |
|---|---|
| `app/ops/lg_rag/multi/step_contract.py`（B1 判定3收窄） | produces 未兑现且缺失字段未被本步 consumes 引用 → 不再 `return BLOCKED`，降级观察留痕放行；新增纯函数 `unfulfilled_produces` 供编排层写 span `step_contract_produces_unfulfilled`（复用 `_record_span_metadata` 通道 · 不新增事件类型）；consumes 引用缺失字段仍由判定2拦截（语义零回归）；判定1/2 零改动；纯序依赖（depends_on 无 consumes）同样放行 |
| `app/ops/lg_rag/multi/nodes.py`（B2 逃生口指引） | `_format_prefix_block` 失败摘要段：任一失败行 blocked_by∈{contract_missing_field, prefix_touch_required} 即附指引——已终态前驱锁定不可改写，以修正后 produces 重发新步或只消费实际产出字段；勿照抄原声明 |

## 三、验收核验（5 条全 PASS · ⑤ 于 2026-10-30 live 核销）

| 验收 | 结果 |
|---|---|
| ① 单测复刻 d3a49 闸场景（前驱缺声明字段、本步 consumes 全命中 → 放行 + 观察留痕断言） | PASS · 红测先行实现前 9 failed、实现后全绿（PR #297 验证节在案） |
| ② 零回归（consumes 引用缺失字段仍拦 / dep 在 prefix 分类不变 / 判定1 不动） | PASS · 目标组 57 passed |
| ③ 失败摘要段含「重发前驱步」指引 + 无失败步主路径 prompt 逐字节零 diff | PASS · TC4 钉死（承 PR #293 FP 口径） |
| ④ ruff（钉 0.15.21）绿 + pytest 不引入新红 | PASS · 全量 28F/1958P/3s = master 基线 28F/1948P + 10 新测，零新红 |
| ⑤ 40 live：复跑 #2140 query，t2 write 实际执行成功 | **PASS**（2026-10-30 核销）· run `25abecd64908416ba28100cecaf300a5`：t1 produces=[title,body] 全真实（闸未触发）→ t2 HITL 批准 resume → testing.write.echo 执行 done → done{resumed}@19 · 全程 19 事件零 budget_exhausted（对照 d3a49 635 事件死锁）· 实证链 [invoke_20261030_40_acceptance.md](../../harness/invokes/by-task/lg-rag-gate-produces-unfulfilled/invoke_20261030_40_acceptance.md) |

## 四、偏差与照登

1. **簿记滞后照登**：PR #297 于 2026-10-28 合并，task 档滞留 active/ 两日；本 CLOSE 为文档健康度整理窗口补簿记，代码真值以 squash `0a5d6109` 为准。
2. **验收⑤ 缺口照登（已闭合）**：40 live 复跑未随 PR 落地，合并时诚实标 OPEN；2026-10-30 维护者令「开始40」执行复跑，run `25abecd64908416ba28100cecaf300a5` 全链实证 PASS（见验收表⑤与 40 invoke），本缺口闭合。
3. **既有 28 红基线照登**：`test_strategy_*`/`capability_*` 等远域既有失败与本 task 无关，清理去向承 close_supervisor_replan_error_feedback 遗留移交（建议另立 task）。

## 五、遗留移交

| 项 | 去向 |
|---|---|
| ~~验收⑤ 40 live 复跑 #2140 query~~ | 已闭合（2026-10-30 · run `25abecd6…` PASS · 40 invoke 在案） |
| 既有 pytest 28 红清理 | 另立 task（维护者裁决优先级） |

## 六、维护者 checklist

- [x] 验收 ①–④ 核验（PR #297 验证节在案）
- [x] **验收⑤ 40 live 复跑**（2026-10-30 核销）：run `25abecd64908416ba28100cecaf300a5` · t2 testing.write.echo 批准链路后实际执行 done · 全程 19 事件零 budget_exhausted · done{resumed}@19 · 事件链与对照表见 [invoke_20261030_40_acceptance.md](../../harness/invokes/by-task/lg-rag-gate-produces-unfulfilled/invoke_20261030_40_acceptance.md)
- [x] 闸真值落闸表（HG-AUDIT-R1 维护者 2026-10-28 签收）
- [x] PR #297 合并（squash `0a5d6109`）
- [x] 归档 done/ · README 登记 · CLOSE 档落盘

## 七、修订记录

| 日期 | 说明 |
|------|------|
| 2026-10-30 | CLOSE 落稿（文档健康度整理窗口补关账）：PR #297 MERGED 事实录 · 验收⑤ 诚实 OPEN 移交维护者 checklist · 分支 `task/lg-rag-gate-produces-unfulfilled` 移交清理 |
| 2026-10-30 | 验收⑤ 核销：维护者令「开始40」→ live 复跑 #2140 query PASS（run `25abecd6…` · t2 write 执行 · 零 budget_exhausted）· 40 invoke 落盘 · 维护者 checklist 全清 |
