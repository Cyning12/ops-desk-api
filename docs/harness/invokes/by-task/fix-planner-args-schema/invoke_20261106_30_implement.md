# Invoke · 30 帽 · 实现（fix-planner-args-schema · 案②修复资产）

| 字段 | 值 |
|------|-----|
| hat_id | `30`（实现 · 案②修复资产落地） |
| task_slug | `fix-planner-args-schema` |
| task_paths | `docs/tasks/active/task_fix_planner_args_schema.md` |
| related_review_or_none | `docs/harness/reviews/task_fix_planner_args_schema_audit_R1_20261106.md`（20-R1 · 随本 PR 出货） |
| git_branch | `agent/planner-args-impl-29337f38be55` |
| created_utc_or_local | 2026-11-06 |
| notes | 受理依据 = issue #339 comment `6674979717`（30 授权六条件 · 授权链 2026-11-06 08:48 维护者授权 · lead 代行签收与验收）· 设计闸裁决 = **案②修复资产为主**（根因环①③一并消除 · 案①拒收语义由 gateway fail-closed 既有承载 · 案③转立条件未触发——实扫确认修复面 = prompt 资产 md ×2 + 目录块单函数，未溢出承载力） |

---

## §1 · 改码面（实扫登记 · 收敛唯一面）

| 文件 | 面 | 说明 |
|------|-----|------|
| `app/ops/prompts/assets/lg_rag.supervisor.system.md` | prompt 资产 v2→v3 | type=tool 行改写（input=意图摘要）+ 新增 args 结构化对象文档化行（按目录块 args_schema 填键名/类型 · 禁 string-args） |
| `app/ops/prompts/assets/lg_rag.supervisor.suffix.system.md` | prompt 资产 v2→v3 | 同上（两份资产同句对齐 · 根因环①消除） |
| `app/ops/lg_rag/multi/nodes.py` | `_format_capability_catalog` 单函数 | 目录块注入各能力 `args_schema`（getattr 宽容 · 未声明行逐字节零 diff · 根因环③消除）；解析层（`_parse_subtasks`）/ 执行面（`tool_exec_node`）/ gateway **零改动**（既有 args 透传 + fail-closed 承接） |
| `tests/test_fix_planner_args_schema.py` | 新增回归测试 ×7 | 负样本红→绿端到端 ×1 · fail-closed 承接 ×1 · legacy 对拍 ×1 · 目录块单测 ×3 · 提示词真装配断言 ×1 |
| `tests/test_prompt_assets.py` / `test_prompt_assembly.py` / `test_prompt_packs.py` | 版本常量适配 ×3 | v2→v3 登记（收紧式适配 · 非放宽） |

图谱面实扫：**none**（无路由/表/事件类型/一级模块面；承 lg-rag-capability-output-schema 先例——同函数前次增量零图谱备注；`graph-compile.sh` EXIT=0）。HG-GRAPH-MODULES none 口径签认覆盖，未触发回签条件。

## §2 · 红测先行（六条件之① · 先红后绿实证）

负样本（维护者红线）= 经**真规划→派发→执行路径**（supervisor_node 真解析 → `_join_subtasks` 真派发 → `tool_exec_node` 真执行 → gateway → `ops_capability_notes` 落笔；planner mock 按「提示词遵循」语义对 system prompt 反应——修复前形态 = issue #339 live 两轮一致 string-args，修复后形态 = args 对象）：

- **先红**（commit `bfb911e` · 修复前运行实证）：
  `test_planner_args_schema_red_to_green_end_to_end` 失败于绿断言——
  `error="args_schema_invalid: 期望 type=['object']，实际=str"`（与 issue #339 live 拦截形态逐字一致）；
  目录块注入单测 ×2 + 提示词文档化断言 ×1 同步红。
- **后绿**（本 commit · 修复后）：同测试 7/7 全绿——args 通过 schema 校验 ·
  真落笔断言达成（便签行 tenant/approval/subtask/幂等键四串链 + 回执 `write_confirmed`）。
- **恒绿对拍组**（修复前后均绿）：fail-closed 承接（string-args 强灌与提示词无关 ·
  修复后仍 `args_schema_invalid` 拦截 + 零落笔 · FP-6 红线）；legacy 只读 input 串形态零漂移；
  旧测 SimpleNamespace 伪造 spec 行渲染逐字节零 diff。

## §3 · 六条件逐条对照（issue #339 comment `6674979717`）

| # | 条件 | 结论 | 证据 |
|---|------|------|------|
| ① | 红测先行经真规划→派发→执行路径 · 负样本端到端 · 红→绿可见 | ✅ | §2（先红 `bfb911e` 实证 · 后绿 7/7 · invoke 留痕） |
| ② | 旧测适配不放宽随 PR | ✅ | 唯三适配 = 资产版本常量 v2→v3 登记（`test_prompt_assets.py` / `test_prompt_assembly.py` / `test_prompt_packs.py` · 收紧式非放宽）；全量 2078 枚 = 修复面零新增红 + 既有红基线 4 枚如实登记（基线 commit `6533d44` 同 4 枚失败实证 · 与本修复无关）；catalog 零声明行逐字节零 diff 旧测原样绿 |
| ③ | 改码面收敛（预期=prompt 资产 md + 目录块 ± 解析小改） | ✅ | §1 实扫：实际面 = prompt md ×2 + 目录块单函数（解析小改不需要——既有 args 透传承接）；未溢出承载力 → 案③转立条件未触发；图谱面 none |
| ④ | 红线零 diff 对拍（SSE 事件表/freeze 文件零改动 · gateway fail-closed 永不放宽） | ✅ | `git diff --name-only` 六文件全在签认承载面内；`gateway.py`/`schema_validate.py`/`event_store`/`resume`/`hitl` 零 diff；fail-closed 承接组修复后仍拦截实证 |
| ⑤ | ruff + pytest + graph-compile 全绿 | ✅ | §4 |
| ⑥ | PR 逐条对照验收 · 20-R1 审查文随 PR 落盘 | ✅ | 本 invoke + `docs/harness/reviews/task_fix_planner_args_schema_audit_R1_20261106.md` 已随分支 |

## §4 · 验证

| 命令 | 退出码 | 摘要 |
|------|--------|------|
| `ruff check app tests` | 0 | All checks passed! |
| `pytest tests`（全量 · 本地真 PG opsdesk_test） | 0 | （全量结果见 PR 自检表 · 零新增红如实登记） |
| `./scripts/graph-compile.sh` | 0 | mermaid normalize ok · done |
| `npx spec-wave@3.5.0 task lint --file docs/tasks/active/task_fix_planner_args_schema.md` | 0 | LINT: PASS（零 warn） |
| `npx spec-wave@3.5.0 verify --target . --task docs/tasks/active/task_fix_planner_args_schema.md` | 0 | VERIFY: PASS（四闸 approved） |

## §5 · 下一棒

出货 PR 待 lead 终审（六条件逐条对照见 task 档自检结论 hat 30）→ 40 复跑全部写能力真落笔解锁（issue #339 销项 · 偏差登记口径承 #329/#334 先例）→ 50 CLOSE。

---

### 修订

| 日期 | 说明 |
|------|------|
| 2026-11-06 | 30 invoke 落档（案②修复资产落地 · 红测先红后绿实证 · 六条件逐条对照） |
