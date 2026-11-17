# R1 审查文 · task_p2c_t1_planner_tool_awareness

> **审查帽**：20-task-audit（R1）
> **task**：docs/tasks/active/task_p2c_t1_planner_tool_awareness.md
> **日期**：2026-11-17
> **授权链**：issue Cyning12/ops-desk-workspace#23（m03064/m03734 夜间授权）· 需求真源 workspace docs/01-scope/03-general-agent/12-p2b-verification.md §5-1/§5-2 + 13-p2b-skill-verification.md §7-2 · 委派书 p2c-t1-planner-tool-awareness

## 结论

**GO · PASS · 零阻塞** — task 档范围/非范围/验收/failure_paths/思考轮（R0-R5）齐备，与委派书五条（勘察 · 硬化设计 · 回归基线 · 测试 · 图谱）逐条对齐，修法裁定「装配点注入 · 行渲染零改 · 静态零 id 引导语 + few-shot + rag 兜底从句」为预算锚内最小有效组合，可进 30。

## 核对项

| 项 | 结论 | 依据 |
|----|------|------|
| 范围6条 ↔ 委派书 | 一致 | 勘察入档 · _build_catalog_block 装配点 + _TOOL_AWARENESS_GUIDANCE · mock 回归基线 6 断言 · FP 迁移 · 真 PG 测试 + ruff · 图谱签收 + 过闸落盘 |
| 非范围 | 一致 | 真冒烟 T2 · translator M1-M3 词表不动 · description 首句蒸馏裁定不做（server 向 G12 承接）· 模板资产 v3 零 bump · fail-closed 解析面不动 · 零新依赖 · alembic//scripts//skill_registry/ 禁入 |
| 验收标准 | 9 条全机判锚 | 引导语注入 · 空目录零追加 · 行渲染零 diff · 零泄漏两锚 · 预算锚 ≤6000 · FP 迁移 · 回归+全量+ruff · 图谱两件 · 过闸四件 |
| failure_paths | 8 条 | 预算突破 · id 泄漏 · 域外恶化 · FP 咬断言 · skill 叠加 · 并行冲突 · 环境性红对照 · 脏树期 registry 红常态 |
| 思考轮 | R0-R5 齐 · actual_last_round=R5 | 表头 `| 轮 | 结论 | early_stop |` 合规 |
| 人工闸表 | 三行 approved | HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES · issue #23 授权 |
| 体例 | 照 fix-planframe-truncation done 模板 | registry/invokes/图谱签收承 fix-planframe 先例 |
| 仓规条款一 | 遵守 | 本审查文即 20-R1 路径 · 未用 --allow-no-review |

## 关键决策复核

- **退化机理定位准确**：app/ops/prompts/assets/lg_rag.supervisor.system.md v3 仅说明三种 type + `$catalog_block` 注入 + 「单一简单问题就只给一个 rag 子任务」单边引导，无正向选工具引导/few-shot——与 12 §5-1「泛化问法未命中 · 显式命名后 3/3」实测吻合（点名 id 补上了缺失的决策锚）。
- **装配点设计成立**：nodes.py:1619 `catalog_block = _format_capability_catalog(caps)` 为 suffix/base 两路共用唯一装配点，改调 `_build_catalog_block` 自动双覆盖；`_format_capability_catalog` 本体零改保 test_capability_output_fields.py:119/:131 与 test_fix_planner_args_schema.py:487/:500 精确相等断言零 diff；FP 两测试（test_hitl_approved_replan_quality.py:209 · test_supervisor_replan_error_feedback.py:252-258）预期构造迁移同一装配点，单一真源防漂移——prompt 文本变更为本波标的，intentional behavior change 登记合规。
- **预算锚余量充足**：§6.5 capability ≤6000 锚（skill_registry/loader.py:41-42 钉明）；默认 registry supervisor 可见 9 条目录实测 3916 字符，引导语+few-shot（~400 字符）注入后仍远低于锚——无需锚内重分配。
- **零泄漏设计成立**：引导语静态恒定、不含任何 capability id；窄 allowlist 过滤（_resolve_supervisor_visible_caps :194- · filter ∩ allowlist）发生在装配前，引导语不随可见集变化——test_supervisor_restricted_allowlist_hides_tool_from_catalog 形态的新断言可钉。
- **域外负例保护成立**：引导语含 rag 兜底从句「仅当目录中没有工具能覆盖该问题时才纯 rag」，给 13 §7-2 数学负例保留 rag 直答正道；fail-closed 解析面（空 plan 判非法 · LG_RAG_SUPERVISOR_PLAN_ON_FAIL blank 停图）零改，负例行为不恶化。
- **§5-2 裁定成立**：translator.py:370 description 原样透传 ~100% 属实；M3 when_to_use 合成面（:349-355）已存在但 catalog 渲染未消费 when_to_use；Host 重写 description 首句与 M3 同源同文（均源自不可信 server 描述），无法语义中和投毒；真缓解属 server 向翻译器策略（G12 文本镜像 · 12 §5-4 已登记 server 向单独立项）；蒸馏增预算无选定率收益。裁定「本波不做」理由链完整，登记后续项合规。
- **mcp 节引导语不受影响**：R3 P2b-T3 `_MCP_CATALOG_GUIDANCE` 在节内（mcp 行之前），本波引导语在块首，两者位置不冲突；test_capability_mcp_translator.py:610-617 只钉 mcp 节内部相对顺序，零破。

## 偏差确认

无（委派书五条全覆盖 · 无裁剪）。

## 机读通过词

PASS（spec-wave task lint 命令：`npx --yes spec-wave@3.5.0 task lint --file docs/tasks/active/task_p2c_t1_planner_tool_awareness.md`）
