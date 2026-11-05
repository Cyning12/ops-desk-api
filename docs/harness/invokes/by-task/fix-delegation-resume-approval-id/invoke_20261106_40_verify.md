# Invoke · 40 帽 · 复跑销项（fix-delegation-resume-approval-id）

| 项 | 内容 |
|----|------|
| **帽** | 40-verify · **日期** 2026-11-06 |
| **task** | `docs/tasks/done/task_fix_delegation_resume_approval_id.md` |
| **分支** | `close/approval-id-fix-task-be209a5f60c8`（reset 自 origin/master `afc8c17` = PR #343 squash 合入点 · 40 全程零仓内码改动 · 独立复跑在 `/tmp/verify40` worktree @ `afc8c17`） |
| **核验对象** | PR #343 全量 diff（`git diff c162d1d..afc8c17` · 7 文件）+ master 活链实测（delegation on） |
| **依据** | issue #334 维护者 comment `34dd980d6805a4db217e264602b1ec92`/`6666638933`（40 复跑销项令 · 签收窗口至 2026-11-06 07:00 · #339 偏差口径 + 有红停下报） |
| **结论** | **机制面 PASS（主结论）：live delegation on 全链单消费实证（签发门唯一台账 · 写闸零重复消费）· 全量零新增红 · 红线零破**——偏差②（真落笔 · planner string-args `args_schema_invalid`）按维护者 item 3 预期口径登记（issue #339 同源 · 预存在非本链） |

---

## 1. 闸态 verify（master `afc8c17` 实跑）✅

`npx spec-wave verify --target . --task docs/tasks/done/task_fix_delegation_resume_approval_id.md` → **VERIFY: PASS** · 四闸 approved。

## 2. 红线对拍（`git diff c162d1d..afc8c17`）✅

- delta 恰 7 文件：码面 `nodes.py::_write_execution_approval`（+18/-3）+ 新测 `test_fix_delegation_resume_approval_id.py`（+290）；文档面 task 档 + 20-R1 审查文 + 10/20/30 invoke——全落 30 交付面；
- **红线零命中**：`hitl/**` / `registry.py` / `policy.py` / `event_store` / SSE 事件表零 diff（git 对拍空集）· web `hitl.ts` freeze 未碰（跨仓）· resume 单路径（`router.py`/`resume.py`）零 diff。

## 3. 测试独立复跑（不采信 30 自报 · `/tmp/verify40` @ `afc8c17`）✅

- **新测 2 枚**：`pytest tests/test_fix_delegation_resume_approval_id.py` → **2 passed**（负样本全链单消费+三照 / 主路径零漂移对拍）；
- **关联回归 9 文件**：`pytest test_hitl_approval_consumption test_write_approval_gate test_hitl_approved_replan_quality test_fix_worker_state_send_run_id test_hitl_resume test_stage_w_write_expand test_capability_testing_write test_lg_rag_delegation_wiring test_capability_delegation` → **190 passed**（零适配）；
- **全量**：`pytest tests` → **2065 passed · 4 failed**——4 failed 与 merge 前分支及 `c162d1d` 基线逐枚同形（diff-whitelist 锚点漂移 ×2 / embedder env ×1 / dualproc env ×1）· **零新增红**；
- `ruff check app tests` 13 枚既有基线零新增 · `./scripts/graph-compile.sh` EXIT=0。

## 4. live delegation on 全链实测（单消费实证 · 修复核心 live 达成）

**环境**：本机 uvicorn :8013 @ `/tmp/verify40`（`afc8c17`）+ PG `opsdesk_test`；env 前置：`DATABASE_URL→opsdesk_test` + `OPS_HITL_PERSISTENCE=db` + `OPS_CAPABILITY_PERSISTENCE=db` + `OPS_CAPABILITY_EXTRA_MANIFESTS=<abs>/ops.write.v1.yaml` + `OPS_CAPABILITY_ALLOW_WRITE_TAGS=run_note` + `OPS_STRATEGY_EXTRA_CANDIDATE_CAPABILITY_IDS=ops.write.run_note` + **`LG_RAG_DELEGATION_TOKEN_MODE=enforce`** + `LG_RAG_DELEGATION_TOKEN_SECRET=fix40-live-secret` + `LG_RAG_HTTP_CHECKPOINTER=postgres` + supervisor 模型 `deepseek-ai/DeepSeek-V4-Pro`（偏差①）；invite cookie 会话（`fix40-tester`/maintainer）；数据前缀 `fix40`（事后已清理 · 零残留实证）。

| 段 | 结果 | 证据摘录（服务端日志 · run `eedd75f3…`） |
|----|------|----------|
| ① 两步任务规划 → 签发门拦下 | ✅ | `delegation token_issue_hitl_required {subtask_id: …:1 / …:2, tool: ops.write.run_note}` → `hitl.waiting` 挂起（blocked_by=delegation_issue_hitl_required） |
| ② pending → decide(approved) → 重复 409 | ✅ | `HITL 浏览器决策 request=hitl_78f72333… decision=approved by=fix40-tester`；重复 decide 409 live 实证 |
| ③ resume 受理 → 重放守卫 → 解锁 | ✅ | `hitl_persist_guard_skip`（approved 新鲜跳过重复建单）→ `HITL 已批准，解锁 1 步… unlocked=['…:1']`（异步单飞 · replan 保号成功） |
| ④ **签发门单消费（修复核心 live 实证 · 主结论证据）** | ✅ | `delegation_approval_consumed {request_id: hitl_78f72333bb0b4a06b1f7, capability_id: ops.write.run_note, decision_by: fix40-tester, ttl_remaining_seconds: 3576}`（03:37:25 · **全链唯一消费台账**） |
| ⑤ 写闸查命中放行 · 零重复消费 | ✅ | `delegation token_issued{subtask_id: …:1}` → `delegation token_verified` → 执行触达 adapter——**全程 `capability_write_approval_consumed` 携带该 approval_id 行数 = 0**（grep 实证 · 双消费合一 live 达成） |
| ⑥ 真落笔 | ⚠️ 偏差② | 执行触达 adapter 但 `args_schema_invalid: 期望 type=['object']，实际=str`——planner string-args（issue #339 · 预存在非本链 · 维护者 item 3 预期口径） |
| ⑦ resume 收口 | ✅ | `HITL 恢复完成 request=hitl_78f72333… approved=['…:1'] replay=…:14` |

## 5. 偏差登记

**偏差①（环境噪点 · 模型层）**：默认 supervisor 模型 `Qwen/Qwen3.6-27B` 对 resume replan **持续返回空 `{"subtasks": []}`**（8/8 轮采样一致 · 含裸 JSON / ```json 围栏两形态）→ `supervisor 输出非法` fail-closed 停图。处置：测试 env 切 `deepseek-ai/DeepSeek-V4-Pro` + 两步任务引导查询（replan 需非空计划以承接保号行）后**首轮即成功**——模型层环境性，非仓码语义（fail-closed 行为本身正确）。

**偏差②（真落笔未达成 · 维护者 item 3 预期口径 · issue #339）**：⑤消费放行后真落笔被 `args_schema_invalid` 拦（planner 产出 string-args 而非 object）——**归因 issue #339 同源**（stage-w 40 观察③ · supervisor prompt 未文档化 args 字段）· **预存在 · 非本链缺陷 · 非 #343 引入**（#343 前后 planner 行为一致）。单测/集成面真落笔三照由 30 负样本全绿承接（对象入参直驱真派发路径 → 消费命中 → 真执行断言）。处置：按维护者 item 3——机制面 PASS 保持主结论，偏差②另波 #339 销项。

**偏差③（实测口径登记）**：live 全程 delegation **on**（本修复被修面）；写闸 capability_write 类形态由 30 主路径对拍测 + 全量回归承接。

## 6. 终态工程面

| 项 | 结果 |
|----|------|
| 40 全程仓内码改动 | **零**（仅本 invoke + 关账文档入 PR） |
| 测试数据清理 | 21 runs 事件 / hitl 行 / 9 threads / 23 invites / 23 sessions / 2 users 全清（`leftover: 0` 逐项实证）· notes 0（真落笔未达成 · 与偏差②一致） |

## FAIL 判定扫描

30 无造假：红线对拍零命中（7 文件全落交付面）/ 新测 2 枚独立复跑绿 / 关联 190 枚绿 / live 单消费日志链完整（签发门 1 笔 + 写闸 0 笔 · token issued/verified + 执行触达）/ 全量零新增红（4 枚基线同形对照）。偏差①②均如实登记，不阻塞机制面 PASS。

## 给维护者的销项建议

1. **40 机制面 PASS 可关账**（live 单消费实证 = 修复核心 live 达成 · 全量零新增红 · 红线零破）；
2. 偏差②真落笔（planner string-args）→ issue #339 另波销项（item 3 预期口径）；
3. 按既定收口出关账 PR（active→done 归档 + CLOSE 档 + 50 invoke + 双 README）；issue #334 关 issue 由维护者执行。

---

### 修订

| 日期 | 说明 |
|------|------|
| 2026-11-06 | 40 复跑销项 invoke 落档：独立复跑（闸态/红线/新测 2/关联 190/全量 2065 零新增红）+ live delegation on 全链单消费实证（run `eedd75f3…` · 签发门唯一台账 · 写闸零重复消费）+ 偏差①（模型层空规划）②（#339 真落笔）登记 · 测试数据零残留 |
