# CLOSE：fix-planner-args-schema（supervisor planner string-args 触发 args_schema_invalid · 八段真落笔阻断 · prompt 资产面）

> 关账日期：2026-11-06 · 关账人：bot 全棒链执行（10 → 20 → 30 → 40 → 50 CLOSE · 同日闭环）· 维护者令 issue #339 comment `6675685940`（40 复跑销项 · 依据 2026-11-06 08:48 授权）
> 体例承 [close_fix_seen_surface_idempotency_20261106.md](close_fix_seen_surface_idempotency_20261106.md)

## 一、任务信息

| 项 | 值 |
|---|---|
| task | [`task_fix_planner_args_schema.md`](../done/task_fix_planner_args_schema.md)（已归档 done/） |
| 性质 | fix / 缺陷修复（prompt 资产面 · supervisor planner 产出 string-args 致 gateway args_schema fail-closed 拒执行 · 预存在非回归 · issue #339 backlog） |
| 由来 | issue #339（来源 #329 40 复跑实测两轮一致 + stage-w 40 观察③同源 · #334/#335 偏差② ×2 复现登记）；**10 档只读诊断五环机制链**（根因环 = 两份 supervisor prompt 资产 v2 未文档化 args 字段 · file:line 全锚） |
| PR | [#348](https://github.com/Cyning12/ops-desk-api/pull/348)（10 起草 · squash `6533d44` · lead review APPROVED `5794838471` 签认四闸 + 裁决案②）· [#349](https://github.com/Cyning12/ops-desk-api/pull/349)（30 实现 · squash `36ef90d` · lead 验收合并）· 关账 PR（50 CLOSE · 本档随船） |
| 闸 | HG-PLANNER-ARGS-DESIGN（裁决 = **案②修复资产为主**：prompt 资产文档化 args + 目录块注入 args_schema · 案①拒收语义由 gateway fail-closed 既有承载 · 案③转立条件未触发）· HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES none 口径（lead 签认 · 依据 PR #348 review `5794838471` + issue #339 comment `6674979717` · 授权链 2026-11-06 08:48） |

## 二、交付清单

| 产物 | 说明 |
|---|---|
| `app/ops/prompts/assets/lg_rag.supervisor.system.md` v2→v3 | type=tool 行改写（input=意图摘要）+ 新增 `args` 结构化对象文档化（按目录块 args_schema 填键名/类型 · 禁 string-args）——根因环①消除 |
| `app/ops/prompts/assets/lg_rag.supervisor.suffix.system.md` v2→v3 | 同上（两份资产同句对齐 · 重规划面同覆盖） |
| `app/ops/lg_rag/multi/nodes.py::_format_capability_catalog` | 目录块注入各能力 `args_schema`（getattr 宽容 · 未声明行逐字节零 diff）——根因环③（目录块信息缺口）消除；解析层 / tool_exec / gateway **零改动**（案①拒收语义由 fail-closed 既有承载） |
| `tests/test_fix_planner_args_schema.py` | 7 枚红测先行：负样本红→绿端到端（真规划→派发→执行 · 先红 `args_schema_invalid` 与 issue #339 live 形态逐字一致 · 后绿真落笔四串链）· fail-closed 承接 ×1 · legacy 对拍 ×1 · 目录块单测 ×3 · 提示词真装配 ×1 |
| 旧测适配 | 唯三版本常量适配（`test_prompt_assets` / `test_prompt_assembly` / `test_prompt_packs` · v2→v3 登记 · 收紧式非放宽） |
| 过程文档 | task 档（四闸签认 + 40 回填 · 全棒自检）· 20-R1 审查文（lead 人审转录 · 非自签）· 10/20/30/40/50 invoke 全落盘 |

## 三、验收核验（全 PASS · 机制面 + live 真落笔双证关账）

| 验收 | 结果 |
|---|---|
| 红测负样本（维护者红线） | ✅ 先红（`bfb911e` · string-args → `args_schema_invalid: 期望 type=['object']，实际=str` · 与 issue #339 live 两轮一致形态逐字一致）→ 后绿（7/7 · args 通过 schema 校验 · 真落笔执行断言达成） |
| 处置形态 | ✅ 按签认案②落地（FP-8 未越权自裁 · 案③转立条件未触发——实扫修复面 = prompt md ×2 + 目录块单函数，未溢出承载力） |
| 四红线零 diff | ✅ SSE 事件表（`event_store`/`sse_*`）· HITL 消费语义 freeze 面 · resume 单路径（`router.py`/`resume.py`）· 改码面收敛（delta 11 文件全落签认承载面）——`git diff 6533d44..36ef90d` 对拍零命中 |
| gateway fail-closed | ✅ 永不放宽：既有负样本组（`test_capability_gateway` / `test_capability_harness_cli`）全绿 · fail-closed 承接组实证 string-args 强灌修复后仍拦截 + 零落笔 |
| 工程面 | ✅ 30 自检 + 40 独立双证：全量 2075 passed · 4 failed = 既有基线同形（diff-whitelist ×2 / embedder env ×1 / dualproc env ×1）· ruff 零新增 · graph-compile EXIT=0 · verify 四闸 PASS |
| **40 复跑销项（主结论）** | ✅ **机制面 PASS + live 真落笔达成**——独立复跑（不采信 30 自报）：worktree `/tmp/verify40-planner` @ `36ef90d` 新测 7 / 关联回归 416 / 全量 2075 零新增红 · 红线对拍零命中；**live 免 shim 全链八段**（uvicorn :8014 + PG opsdesk_test · delegation off · run `7ecfe9d9…`）：写闸挂起 → pending → decide 200+重复 409 → resume 受理+写窗 409 → 消费命中唯一台账 → **`ops_capability_notes` 真落笔落行（approval/subtask/幂等键/tenant 四串链 · 不再撞 `args_schema_invalid`）** → 收口 done{resumed} |

## 四、偏差与裁定留痕

- **偏差①（live · 环境噪点 · 模型层）**：resume 后 supervisor replan（DeepSeek-V4-Pro）一轮采样返回空 `{"subtasks": []}` → 既有 fail-closed 灾备降级单 rag 收终态（主 .env `LG_RAG_SUPERVISOR_PLAN_ON_FAIL=single_rag`）。同 #334 偏差①形态（模型层环境性 · fail-closed 行为本身正确）· **不阻塞销项**——真落笔在降级前已达成，降级仅影响回答收尾形态。处置口径承 #334；本 40 令未含 replan 非空采样要求。
- **偏差②（口径登记）**：live 全程 delegation **off**（专验本修复被修面 planner→gateway→真落笔链）；#334 delegation on 面已由该单 40 承继，本修复与 delegation 闸正交。
- **环境噪点照登**：langfuse/otel exporter 403（dev 键过期面）· 本机代理 env 剔除（fix-no-proxy 先例）——均与本修复无关。
- **同源偏差链销项**：issue #329 40 偏差② / issue #334 40 偏差② / issue #335 偏差②（planner string-args ×3 复现登记）随本修复**实质销项**——三单登记的预期另波即本 task。

## 五、关账动作

- 档迁：`docs/tasks/active/` → `docs/tasks/done/`（本 CLOSE 档 + done/README + active/README 同步 + 40/50 invoke）；
- issue #339：维护者执行关 issue（bot 不 close issue · 已声明）；
- 后续跟踪：四单偏差②销项后，全链八段真落笔验证面解锁；若后续 live 复跑再撞 planner 输出形态问题（模型遵循度非 100%），按同一口径（停下报 · 不静默修）登记新波；
- 评审署名登记：PR #348 / #349 的 lead（Cyning12）review 均因 merge 先于署名改写，**未署名记录**（按规不 rewrite 已合并 PR · 此处登记）。
