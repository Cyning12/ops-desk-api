# R1 审查文 · task_p4_t6_run_tree_ddl

> **审查帽**：20-task-audit（R1）
> **task**：docs/tasks/active/task_p4_t6_run_tree_ddl.md
> **日期**：2026-11-18
> **授权链**：issue Cyning12/ops-desk-workspace#23（m03796 夜间预授权）· 需求真源 workspace docs/01-scope/03-general-agent/18-p4-generalization-design.md §3/§7/§8.2 + 19-p4-contracts.md §7/§11（commit e453a36）· 委派书 p4-t6-run-tree-ddl

## 结论

**GO · PASS · 零阻塞** — task 档范围/非范围/验收/failure_paths/思考轮（R0-R5）齐备，与委派书五面（DDL · claim · REST 投影 · 测试 · 图谱）逐条对齐，修法裁定「19 §7.2 SQL 逐字迁移 · ON CONFLICT 新写 claim 路径 · 归属从父行 · 投影加性两字段 · 图谱登记 lg_rag 行」为契约面最小改动组合，可进 30。

## 核对项

| 项 | 结论 | 依据 |
|----|------|------|
| 范围8条 ↔ 委派书 | 一致 | 迁移三列两索引（19 §7.2 SQL 逐字）· models 同步 __table_args__ · create_run 三可选 kw · claim_child_run（§7.3/§7.4）· 投影两字段（§11.4）· 真 PG 测试 + ruff · 图谱签收 + 过闸落盘 |
| 非范围 | 一致 | T7 委派执行提升（OPS_RUN_TREE_ENABLED 三件套/worker/join）· web T8 · SSE 帧面/行为面/cursor · children 端点/树形合并流 · root_run_id/深度参数化/运行时环检测/delegations 台账 · 零新依赖 · scripts/ 禁入 · .importlinter 零改动 |
| 验收标准 | 9 条全机判锚 | 迁移 scratch 可逆 · uq 三态（IntegrityError/取回零重复/并发一胜）· depth 断言拒建 · 归属继承 · 投影契约（默认 null/0）· 回归零红+全量+ruff · models 同步 · 图谱两件 · 过闸四件 |
| failure_paths | 8 条 | uq abort 教训 · 归属错取 · depth 失守 · 零 diff 口径 · autogenerate 漂移 · 并行冲突 · 脏树期 registry 红常态 · PR CONFLICTING 铁律 |
| 思考轮 | R0-R5 齐 · actual_last_round=R5 | 表头 `| 轮 | 结论 | early_stop |` 合规 |
| 人工闸表 | 三行 approved | HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES · issue #23 m03796 授权 |
| 体例 | 照 task_p2c_t1_planner_tool_awareness done 模板 | registry/invokes/图谱签收承 :41-:47 先例 |
| 仓规条款一 | 遵守 | 本审查文即 20-R1 路径 · 未用 --allow-no-review |

## 关键决策复核

- **DDL 与契约逐字对齐**：19 §7.2 SQL（三列 VARCHAR(64)/VARCHAR(64)/INTEGER NOT NULL DEFAULT 0 + uq 部分唯一 WHERE parent_run_id IS NOT NULL + idx parent）完整无裁剪；parent_run_id 不加 FK 承 run_events 顺序容错先例（models.py:285-288 注释）成立——子 run 先落行、父行后到的乱序窗口结构性存在，FK 会把正常重放打成约束违例。
- **ON CONFLICT 新写路径裁定成立**：14 R10 已记录 PG 同事务撞 uq abort 教训（撞 uq 后同事务后续语句全部 abort）；create_run 现状 check-then-insert（run_store.py:52-75）服务于「幂等建行」语义、不承担委派 claim，零改保既有调用面零 diff；claim_child_run 独立承载 §7.4 SQL 逐字（INSERT ... ON CONFLICT (parent_run_id, subtask_id) WHERE parent_run_id IS NOT NULL DO NOTHING → 未插入 SELECT run_id 取回）。并发正确性依据 §7.3 R9/N6 复核结论（败者阻塞至胜者提交后 SELECT 取回）· subtask_id 签发 f"{run_id}:{seq}" locked 前缀不回退 ⇒ replan 不撞号，撞键仅发生在同一子任务重入的语义正确场景。
- **归属继承裁定成立**：19 §8.2 钉 claim 建行从父行取 tenant_id/user_id/thread_id（承 14 §1.8「请求上下文外创建须显式传身份」纪律）；runs 列表/events/replay 既有 thread_owner/assert_run_owned 校验对子 run 天然通过（同 user 同 thread）零改动；N4 链（run_owner=事件表首行 user_id 反查）在 T7 验收矩阵承接，本波数据面不破坏前提。
- **深度硬上限承载层裁定成立**：19 §7.2 SQL 逐字无 DB CHECK · §7.3 钉 claim 层断言（父 depth=0 否则拒建 + logger.exception · 防御性断言正常路径不可达 · 结构性无环不靠运行时检测）；委派书转述「CHECK depth∈(0,1)」与契约语义一致、仅承载层表述不同——按契约逐字执行并登记偏差，属「最小改动+如实登记」授权内裁定。
- **claim 返回 (run_id, created) 签名预留成立**：created 供 T7 决定 start_delegate_run_worker 是否启动（撞 uq 取回=worker 可能已在飞 · §8.3 断线矩阵「claim 重入撞 uq 取回零重复建行」）· 本波不消费但避免 T7 改签名波及数据面。
- **投影加性豁免裁定成立**：19 §11.5 钉「off 态零 diff = SSE 帧面+行为面零 diff · REST 投影新增 parent_run_id/depth 为加性变更（消费方须容忍未知键）」——字段无条件常加、不引 env 闸 · OPS_RUN_TREE_ENABLED 三件套属 T7 不在本波；不开 children 端点（被否已钉）。
- **图谱登记面裁定成立**：01_modules.md 模块表无 db module_id（l0 db 节点 external PostgreSQL 无表级清单 · p3-t3 HG 行「db 行登记」叙事实际落在签收行文本）——runs 表归属 lg_rag 模块，承 p2c-t1/fix-434 先例登记 lg_rag 行 + HG-GRAPH-MODULES 签收行；委派书「db 行」按此先例落地并登记偏差。
- **registry banned_prefixes=[scripts/] 裁定成立**：wave gate _is_banned 对全部 entry（含 closed）前置 banned_prefixes · 本波须触 alembic/versions/，本 entry 若沿用默认 (scripts/, alembic/) 会自咬在途迁移文件；closed entry 咬在途 alembic 文件属脏树期结构性红（委派书钉明 · 提交后复绿 CI 终裁）。

## 偏差确认

2 条（均在 task 档偏差登记 · 契约优先于委派书转述 · 语义一致）：① 无独立 db 行 → lg_rag 行登记；② 无 DB 层 CHECK → claim 层断言承载。其余零裁剪。

## 机读通过词

PASS（spec-wave task lint 命令：`npx --yes spec-wave@3.5.0 task lint --file docs/tasks/active/task_p4_t6_run_tree_ddl.md`）