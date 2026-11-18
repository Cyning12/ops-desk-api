# R1 审查文 · task_p4_t7_delegate_child_run

> **审查帽**：20-task-audit（R1）
> **task**：docs/tasks/active/task_p4_t7_delegate_child_run.md
> **日期**：2026-11-18
> **授权链**：issue Cyning12/ops-desk-workspace#23（m03796 夜间预授权）· 需求真源 workspace docs/01-scope/03-general-agent/18-p4-generalization-design.md §3/§7 + 19-p4-contracts.md §8-§13（commit e453a36）· 委派书 p4-t7-delegate-child-run

## 结论

**GO · PASS · 零阻塞** — task 档范围/非范围/验收/failure_paths/思考轮（R0-R5）齐备，与委派书七面（总闸三件套 · 委派执行提升 · 令牌身份映射 · HITL 三段恢复 · 父 join · 真 PG 测试 · 图谱落盘）逐条对齐，修法裁定「执行体提取闸链单真源 · claim+spawn+轮询 join · depth==1 分流恢复 · 帧型零新增」为契约面最小改动组合，可进 30。

## 核对项

| 项 | 结论 | 依据 |
|----|------|------|
| 范围8条 ↔ 委派书 | 一致 | env 三件套（§12）· route 分支+执行体提取+delegate_exec 节点（§8.1/§8.4 · 18 §3.4）· worker/SSE core（18 §3.4/§3.5）· 委派建单（§9/§10）· HITL depth 分流（§10②）· 真 PG 测试（§10 实证两条 + §13）· 图谱签收 + 过闸落盘 |
| 非范围 | 一致 | T6 DDL/claim 本体 · T8 web · T9 验收冒烟 · §14 被否项（DB 租约/多深度/root_run_id/合并流/children 端点）· SSE 帧型词表/cursor · 签发审批面（父侧 dispatch 前既有通路）· 零新依赖 · scripts//alembic/ 禁入 · .importlinter 零改动 |
| 验收标准 | 9 条全机判锚 | env 解析 · route 对拍（off 零 diff / on delegate_exec）· MAX_CHILDREN 超限 · happy path 帧序+归属继承+恰好1次 · HITL 三段（approve 重跑放行至 done · 重复 decide/resume 不重复执行）· rejected 收口 · 回归+全量+ruff · 图谱两件 · 过闸四件 |
| failure_paths | 11 条 | 闸 off 零 diff · MAX_CHILDREN 次序 · 父崩重入 · HITL 重跑幂等 · resumed 撞事件 uq · rejected 收口丢失 · waiting_approval 非终态 · 孤儿补偿 · 并行冲突 · 脏树期 registry 红常态 · PR CONFLICTING 铁律 |
| 思考轮 | R0-R5 齐 · actual_last_round=R5 | 表头 `| 轮 | 结论 | early_stop |` 合规 |
| 人工闸表 | 三行 approved | HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES · issue #23 m03796 授权 |
| 体例 | 照 task_p4_t6_run_tree_ddl done 模板 | registry/invokes/图谱签收承 :49 先例 |
| 仓规条款一 | 遵守 | 本审查文即 20-R1 路径 · 未用 --allow-no-review |

## 关键决策复核

- **执行体提取闸链单真源裁定成立**：18 §3.4 钉「从 tool_exec 提取的委派执行函数（闸链单真源：idempotency/circuit/budget/HITL/delegation 验签原样）」——`_run_tool_capability` 单函数体双调用面（tool_exec_node 图内路径 / execute_delegate_subtask 子 run 路径），W0 写执行审批闸/emit_subtask_running/cap_ctx/capability_ainvoke/降级标记原样保留，双闸链漂移风险结构性消除；budget_run_id 参数承载 §9「cap_ctx 预算键=父根 run_id」（防 9× 配额分裂），emit_running=False 承载「子 run 帧不落父流」（§11 流边界 per-run）。
- **route 分支次序裁定成立**：`run_tree_on and node=="tool_exec"` 先于既有 delegation_on 分支判定，闸 off 时整条新分支短路、既有 Send(tool_exec) 路径逐字节零 diff（§12 铁律）；plan-JSON 零新 type（委派判定在 route 层不在 plan 层 · §8.1）。
- **令牌映射裁定成立（§9 五行表逐行对齐）**：事件/状态行 run_id=子 run_id（子 worker 独立 run_id emit+persist）；token binding=子 run_id/子任务 id（execute_delegate_subtask 内 exec_state run_id=child · claim 先于签发）；子侧每次尝试自发签发 TTL 自尝试起算（§3.9 · 消解批准后 REJECT_EXPIRED 形态）；父令牌仅作授权凭证不直接复用（verify_token 主体四元组比对的结构性结果）；HITL 单据 run_id=子 run_id（acreate_delegate_hitl_request · decide/resume 既有端点零改）。
- **HITL 三段裁定成立（§10 逐字）**：①子执行体 W0 闸未消费 → kind=hitl → 建单+hitl.waiting 帧+done{waiting_approval} 退出（worker task 结束不占 _workers 槽 · waiting_approval 不在 TERMINAL_STATUSES 父轮询继续）；②`_execute_decided_resume`/`_preflight_decided_resume` 按 fetch_run_row depth==1 分流（§10②逐字 · 分流在 _open_event_sink 前 · depth==1 无 checkpoint ResumeEventSink 不适用）；③重跑 _approval_consumed 命中放行（fail-closed · 副作用闸在 capability_ainvoke 前 · 建单 pending 去重防双单）；重复 resume 由 preflight status 闸拒（子终态后 not_interrupted · 19 §10 实证两条钉死）。
- **重跑 seq 续 last_seq 裁定成立**：重跑与首跑共享 (run_id, seq) 唯一键——ResumeEventSink start_seq 纪律同构延续；首版实现从 1 起实测撞 uq_ops_lg_rag_run_events_run_seq（asyncpg UniqueViolationError），修复入 task 档失败路径，属测试先行的正向实证。
- **帧面零新增裁定成立（§11）**：run.start/hitl.waiting/hitl.resumed/answer/done/error 全既有帧型；run.start payload 加 parent_run_id（§11 钉明）+ delegate_spec 加性键（resume 重跑规格重建 · §11.5「消费方须容忍未知键」同口径豁免）；_SUBTASK_NODES 加 "delegate_exec" 走既有 subtask.progress 映射零新帧；cursor 不动。
- **depth 分流查询失败 best-effort 裁定成立**：`_is_delegate_child_run` 查询异常按非委派处理不阻断主链路——depth 列 T6 已合全行有值（DEFAULT 0），异常仅可能为 DB 故障，此时走既有 supervisor resume 路径报错与闸 off 行为一致，fail-closed 语义不破。
- **registry banned_prefixes=[alembic/, scripts/] 裁定成立**：本波不触 alembic（T6 已合 DDL）· 双前缀承 p4-t2 先例；wave gate 对全部 entry（含 closed）前置 banned 面，本 entry 双前缀不会自咬（在途零 alembic 文件）。
- **GUIDE_env_inventory 不登记裁定成立**：承 p4-t2 OPS_DOMAIN 先例（同夜间波 · 图谱行备注承载 env 注记）· 最小改动如实登记偏差。

## 偏差确认

1 条（task 档偏差登记）：GUIDE_env_inventory 不登记 env 三件套（承 p4-t2 先例 · env 注记入图谱行备注）。其余零裁剪。

## 机读通过词

PASS（spec-wave task lint 命令：`npx --yes spec-wave@3.5.0 task lint --file docs/tasks/active/task_p4_t7_delegate_child_run.md`）
