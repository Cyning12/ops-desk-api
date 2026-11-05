# 40 invoke · fix-worker-state-send-run-id（核验 30 交付 · 独立复跑 + live 免 shim 全链实测）

| 项 | 内容 |
|----|------|
| **帽** | 40-verify · **日期** 2026-11-05 |
| **task** | `docs/tasks/active/task_fix_worker_state_send_run_id.md` |
| **分支** | `close/worker-state-send-run-id`（reset 自 origin/master `ba03800` = PR #332 squash 合入点 · 40 全程零仓内码改动） |
| **核验对象** | PR #332 全量 diff（`git diff 5bec9d6..ba03800`）+ master 活链实测（**免 shim**） |
| **依据** | issue #329 维护者 comment `6660516133`（40 复跑销项令 · 签收窗口至 2026-11-06 07:00 · 有红停下报不静默修） |
| **结论** | **机制面 PASS（live 免 shim 消费闭环实证 ×2）· 八段真落笔红（上游 planner args · out-of-scope）→ 按令停下报（偏差登记①）** |

---

## 1. 闸态 verify（master `ba03800` 实跑）✅

`npx spec-wave verify --target . --task docs/tasks/active/task_fix_worker_state_send_run_id.md` → **VERIFY: PASS** · 四闸 approved（HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES / HG-WORKER-STATE-RUN-ID-DESIGN）。

## 2. 红线对拍（`git diff 5bec9d6..ba03800`）✅

- 码面 delta 恰 3 文件：`nodes.py` `_worker_state` +8（含注释）/ `tests/test_fix_worker_state_send_run_id.py` +347 / `tests/test_lg_rag_delegation_wiring.py` ±9——全落 30 交付面；
- 文档面 delta：task 档（闸表签认 + 30 回填）/ 20-R1 审查文 / 10·20·30 invoke——全落过程文档面；
- **红线零命中**：`registry.py` / `policy.py` / `event_store` / `hitl/**` / SSE 事件表零 diff（git 对拍空集）；web `hitl.ts` freeze 未碰（跨仓）；resume 单路径 grep 断言由 stage_w 16 枚承接全绿。

## 3. 测试独立复跑（不采信 30 自报）✅

- **新测 6 枚**：`pytest tests/test_fix_worker_state_send_run_id.py` → **6 passed**（负样本真派发路径真落笔三照 / 键集钉双形态 / delegation on 对拍 / FP-9 仍拦）；
- **关联回归 10 文件 + redlines**：`pytest <10 文件> tests/eval/test_capability_redlines.py` → **183 passed**（含 wiring 适配 1 枚 · R14 段 29 passed）；
- **全量**：`pytest tests`（本地真 PG opsdesk_test）→ **2063 passed · 4 failed**——4 failed 与 stage-w 40 登记基线逐枚吻合（diff-whitelist 锚点漂移 ×2 / env 依赖 ×2 · CI skip 面）· **零新增红**；
- `ruff check app tests` 零新增 · `./scripts/graph-compile.sh` EXIT=0。

## 4. live 免 shim 全链实测（八段 · delegation OFF = 被修路径）

**环境**：本机 uvicorn :8012 @ `ba03800` + PG `opsdesk_test`；env 前置：`DATABASE_URL→opsdesk_test` + `OPS_HITL_PERSISTENCE=db` + `OPS_CAPABILITY_PERSISTENCE=db` + `OPS_CAPABILITY_EXTRA_MANIFESTS=<abs>/ops.write.v1.yaml` + `OPS_CAPABILITY_ALLOW_WRITE_TAGS=run_note` + `OPS_STRATEGY_EXTRA_CANDIDATE_CAPABILITY_IDS=ops.write.run_note` + **`LG_RAG_DELEGATION_TOKEN_MODE=off`**（主 checkout .env 为 enforce——切 off 专验本修复的被修面 `_write_execution_approval`）；admin/maintainer cookie 面登录；数据前缀 `fx40`（事后已清理：events 72 / hitl 4 / threads 2 / notes 0）。

| 段 | 结果 | 证据摘录 |
|----|------|----------|
| ① catalog 可见性 | ✅ | `visible_ids` 6 枚含 `ops.write.run_note`（默认加载面不含 · 独立写 tag 放行生效） |
| ② plans 含写 tool → 挂起 | ✅ | supervisor plan `type=tool / tool=ops.write.run_note` → `tool_exec` 帧 `blocked_by=capability_write_hitl_required` + `write_intent` 钉死 → `hitl.waiting` → `done{status:waiting_approval}`（run `5bc63c8b…` · `f193a5b9…` 两轮均达成） |
| ③ pending 可见 | ✅ | `GET /hitl/pending` 列出 `hitl_9849547e…`（owner 过滤生效） |
| ④ decide(approved) | ✅ | HTTP 200 · approved；**重复 decide → 409** live 实证 |
| ⑤ resume 受理 | ✅ | `resume={status:accepted}` 异步单飞；**写窗 409**「Resume is writing new events」live 实证 |
| ⑥ replan 保号 | ✅ | `hitl.resumed` 帧 + replan 保号 `:1`（`hitl.resumed{approved:['…:1']}` · observe→supervisor 前缀保留） |
| ⑦ **消费命中（免 shim 修复核心 live 实证）** | ✅ | 两轮均：`capability_write_approval_consumed{approval_id=hitl_9849547e… / hitl_4144fce3…, blocked_by=capability_write_hitl_required}` → **执行放行**（无 fail-closed 再拦 · 无二次建单）——pre-fix 此处永久再拦（stage-w 40 偏差#1），修复后天然通过 |
| ⑧ 收尾帧 | ⚠️ 偏差① | 消费放行后执行触达 adapter，但 `args_schema_invalid: 期望 type=['object']，实际=str`——**真落笔未达成**（两轮采样一致 · 见偏差登记①） |

## 5. 偏差登记与缺陷实证

**偏差 #1（红 · 停下报 · 不静默修）**：⑦消费命中后真落笔未达成——supervisor planner 产出 `input` 为 **JSON 字符串**（`'{"run_id":…}'`）而非 object，gateway `args_schema` 校验 fail-closed 拒执行（`args_schema_invalid`）。两轮采样（run `5bc63c8b…` 23:01 / `f193a5b9…` 23:04）一致。**归因：stage-w 40 invoke 观察③同源——supervisor system prompt 未文档化 `args` 字段（写工具结构化入参靠提示词即兴）**，属另波 prompt 资产面；**非本 task 改码面（本 task 闸链/提示词一行未动）· 非 #332 引入（#332 前后 planner 行为一致）**。单测/集成面真落笔由 A1 形态负样本全绿承接（载荷经 `_worker_state` 带 run_id → 消费命中 → 真落笔三照断言）。**按维护者令「有红停下报」：请裁定——(a) 机制面 PASS（live 免 shim 消费闭环 ×2 + 全量零新增红）即关账，planner args 另波；或 (b) 另波处理后复跑八段。**

**偏差 #2（环境噪点 · 同源 stage-w 偏差#2）**：本机 siliconflow 间歇挂起/空响应（supervisor complete 调用 4-9 分钟 bounded retry 两轮空 raw）→ 前两轮（`449444ff…` / `9e70fc46…`）规划失败走主 .env 的 `LG_RAG_SUPERVISOR_PLAN_ON_FAIL=single_rag` 降级单 rag；第三轮起显式引导 + off 模式两轮成功规划。环境性，非仓码语义；全程如实留痕。

**偏差 #3（测试等价面差异 · 如实登记）**：enforce 模式（主 .env 默认）下 pre-fix 亦带 run_id（:1666 分支），被修面为 off 模式 W0 写闸——40 专以 off 模式实测被修路径（与 stage-w 40 live 同口径）；enforce 路径消费门同结构（`_approval_consumed` 同源 `_run_id_of`）由单测 + 既有委派测试承接。

## 6. 终态工程面

| 项 | 结果 |
|---|---|
| 40 全程仓内码改动 | **零**（仅本 invoke + task 档 40 自检回填拟入 PR） |
| `ruff check app tests` | 零新增 |
| `./scripts/graph-compile.sh` | EXIT=0（master 态） |
| `npx spec-wave task lint` | LINT: PASS（task 档 40 回填后） |
| 测试数据清理 | events 72 / hitl 4 / threads 2 已 DELETE · notes 0（真落笔未发生 · 与偏差①一致） |

## 给维护者的裁定建议

1. **机制面 PASS 成立**：live 免 shim 消费闭环 ×2 实证（#332 修复核心）· 全量零新增红 · 红线零破——stage-w 40 偏差登记①（本 task 由来）实质销项；
2. **真落笔红（偏差#1）**：planner string-args 为另波 prompt 资产面（stage-w 观察③已登记）· 非本 task 缺陷——建议按 (a) 关账 + 另波跟踪；若要求八段全绿，需先处理 supervisor args 文档化（另立 task）后复跑；
3. 环境噪点（偏差#2）与 enforce/off 口径（偏差#3）如实登记，不阻塞。

## 环境注记

- live 证据文件（ephemeral · 摘录已嵌上文）：/tmp/fx40_sse*.log · /tmp/fx40_replay*.log · /tmp/fx40_server*.log（不入仓）；
- 主 checkout .env 仅 live 用（含 LLM keys · 未入仓未打印）；启动器 env 以绝对路径传 manifest（`extra_manifest_paths()` CWD 相对解析）；
- 本机代理 env 已按先例剔除 bracketed IPv6 条目（服务进程内建清洗双保险）。
