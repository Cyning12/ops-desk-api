# Invoke：10-task 拆分 · hitl-approval-consumption（三 task 串行 · T1→T2 依赖 · T3 可插队）

> **hat_id**：10-task · **日期**：2026-10-10 · **分支**：`task/hitl-approval-consumption`（worktree `task-hitl-approval-consumption` · base `master` 4d905e0=origin/master）  
> **依据**：SPEC v1 `docs/spec/hitl-approval-consumption/SPEC-hitl-approval-consumption_v1.md`（HG-SPEC-SIGNOFF=approved 2026-10-10 · **文档在 spec 分支 · 随首个实现 PR 一并带入 master · task 内已注明**）  
> **skill**：harness-10-task 已加载 · **范式**：`docs/tasks/done/task_testing_write_capability.md` · **规范**：`docs/standards/CODING_BACKEND_L2_v1_zh.md`（P-13/P-14/P-15/P-16）  
> **纪律**：骨架先行增量落盘（三文件 143 行骨架先落盘 → 逐节填充至占位清零）· 禁改实现码（全程仅 docs/）

## 产出清单

| task | 文件 | 承接 | 依赖 |
|------|------|------|------|
| T1 hitl-approval-consumption-loop | `docs/tasks/active/task_hitl_approval_consumption_loop.md` | D1 消费门 + D2 unlock 回填 + D4 台账/测试（A1/A2/A3/A5/A6/A7/A8） | 无（base master） |
| T2 hitl-approval-consumption-auto-resume | `docs/tasks/active/task_hitl_approval_consumption_auto_resume.md` | D5 自动 resume 可配置面（A9/A10 + FP-8~FP-11 断言化 · R2-N1/N2/N3 三钉） | **T1 merge 后方可 30** |
| T3 hitl-approval-consumption-strategy-env | `docs/tasks/active/task_hitl_approval_consumption_strategy_env.md` | D3 strategy env 口（A4 · 最小独立） | 无（可插队先行） |

## 拆分裁定（与建议一致 · 理由补强）

采纳建议三 task 拆法，未调整。**理由**：① T1 是消费成环最小可验收闭环（A1/A2/A3 独立可机断 · D1 与 D2 强耦合——消费门与 unlock 回填互为「批准→放行→resume 可达 done」的两半，拆开任一边都验不出成环）；② T2 的 A9 全链以 T1 为机制前提（无消费门→auto resume 恢复后仍再拦 · 无 D2→resume 409），串行合并是机制依赖非偏好，故 D5 独立成 T2 并钉「T1 merge 后方可 30」；③ T3 单文件小改动 + A4 自足，与消费门/自动 resume 零耦合，独立可插队缩短关键路径。**否 D3 并入 T1**：并入会使 T1 验收面混入 strategy 图谱行与 env 解析面，模糊「消费成环」闭环边界，且 T3 本来就可先行——并入反而拖住它。

## nits 携带落位

| nit | 落位 | 处置 |
|-----|------|------|
| R1-N1（锚点精度） | T1 钉死契约「decided_at 归一」行 + R2 裁定二 | SPEC 表述「Db store 为 datetime」指 SQL 层；消费端经 `_row_to_dict`（store.py:249）实收 **ISO 8601 str**——归一输入类型钉 float\|str · Db 组 TTL 断言必经真读路径 |
| R1-N2（async 波及面） | T1 钉死契约「async 化裁定」行 + B1 + failure_paths 实操-A/E | **扩面实证**：SPEC 估「仅 nodes.py:711 + test 一处」，实测 `_join_subtasks`（sync 节点 · graph.py:94）另有 13 处 sync 直调（test_step_contract ×7 · test_lg_rag_delegation_wiring ×3 · test_capability_testing_write:433 · eval redlines ×1）→ 10 裁定**甲案**（两函数 async 化 + 14 处测试随改 · 否乙=事后状态修补双写面 · 否丙=sync-over-async 违 P-13）· 留 20-task-audit 复核 |
| R2-N1（400/422 形态钉实现路径） | T2 钉死契约 + R2 裁定一 | `_DecidePayload.decision` 既有 Literal/422 形态实证（router.py:113-115）→ `resume_mode` 钉 **str+端点手工白名单=400**（禁 Literal 变 422 · SPEC FP-10/A10）· docstring 注明双形态差异 |
| R2-N2（触发器挂点裁定） | T2 钉死契约 + R2 裁定二 | **挂点=router decide_request 成功分支**（adecide 返回非 None 后）· 否 store 层（违 A7 diff 空 + 无 user/resume_mode 台账面）· 否 OA callback 本波（签名面零 diff · 非范围） |
| R2-N3（行锁锚点与并发断言基建） | T2 钉死契约 + R2 裁定三 | 全仓无 FOR UPDATE 先例（grep 实证）→ `DbHitlStore` 新增 `FOR UPDATE SKIP LOCKED` 认领方法（既有四方法 diff 空）；断言分组钉：Db 组真 PG 并发仅一认领 · **InMemory 禁行锁假断言**（只做状态机幂等）· 承 task_multi_replica_verify 先例 |

## 每 task 必备项核对

- 验收可机断 + SPEC A 条编号映射：T1 TA1–TA7 / T2 TB1–TB8 / T3 TC1–TC3 ✓
- failure_paths 映射 SPEC FP + 实操坑：T1 12 行 / T2 11 行 / T3 7 行 ✓
- 非范围 / 依赖（T2 依赖 T1 merge 写入 T2 依赖表+验收首行+闸行）✓
- R0–R5 思考轮控制表（均 early_stop at R5 · 新增裁定各有实证排除岔路）✓
- graph_change_layer=G-L1 行备注 · review_hat=20 · 人工闸表（HG-TASK-DRAFT/HG-AUDIT-R1/HG-GRAPH-MODULES 全 pending · HG-PILOT-OPSDESK-GLAYER n/a）✓
- required_invoke_hats=10,20,30,40 · invoke_retention_profile=default · wiki_delta=n/a（bulk-split 预填 ✓）

## 给 00 的提醒

1. **派第一棒 30 前跑早检**：`npx --yes spec-wave@3.0.1 task lint-wiki-delta --target . --scope all`（bulk-split 后推荐 all 面）。
2. 三 task 闸全 pending → 20-task-audit R1 → 维护者签（00 代录）后方可 30。
3. 合并顺序建议：T3 可插队先行；T1 → T2 串行；SPEC 文档（`docs/spec/hitl-approval-consumption/`）随首个实现 PR 带入 master。
4. T2 新增裁定四「已批准未恢复」四条件与 run 终态判定真源（event_store 无既有谓词）为 30 裁定留痕点 · 20/40 复核。

## lint 结果

| 检查 | 结果 |
|------|------|
| `spec-wave task lint` T1 task_hitl_approval_consumption_loop.md | **PASS**（EXIT=0 · spec-wave 3.0.1 本地二进制） |
| `spec-wave task lint` T2 task_hitl_approval_consumption_auto_resume.md | **PASS**（EXIT=0） |
| `spec-wave task lint` T3 task_hitl_approval_consumption_strategy_env.md | **PASS**（EXIT=0） |
| `spec-wave task lint-wiki-delta --target . --scope all` | **PASS**（scanned 152 · missing 0 · issues 0 · bulk-split wiki_delta 预填早检） |
