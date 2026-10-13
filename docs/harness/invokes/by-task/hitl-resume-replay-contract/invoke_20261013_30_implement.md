# Invoke：hitl-resume-replay-contract · 30-implement（2026-10-13）

| 字段 | 值 |
|------|-----|
| **hat_id** | 30-implement |
| **task** | `docs/tasks/active/task_hitl_resume_replay_contract.md`（F-OBS-1/2 · web 联调 T-W2 FP-1 报回） |
| **分支** | `task/hitl-resume-obs-drafts`（30 开工前 reset 至 origin/master） |
| **基线** | 4137f60（三闸 approved · #247  merged 后 origin/master） |
| **交付 commit** | a30b3d3（红测先行 · 仅两测试文件 +154 行）→ e4a54d9（F1/F2 实现 GREEN）→ 61094bf（G-L1 modules.md 回写）→ task 回填+本 invoke |
| **三闸核验** | HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 全 approved（闸表 4137f60 在案 · verify PASS 实证见下） |

## Prompt 快照（范围承接）

F1 终帧补 `latency_ms`（必）+ `model`（FP-1 裁定 · 禁伪造）/ F2 在飞 409+Retry-After / F3 契约测试红测先行 / F4 invoke+图谱回写；TC1–TC5（TC5=40 帽 live 对照）；freeze_id=lg-rag-sse-v1 不新 freeze。

## GATE_VERIFY（开工前实证）

| 核验 | 结果 |
|------|------|
| 人工闸表三行 | approved（4137f60 在案 · 维护者签 2026-10-13） |
| `npx spec-wave@3.3.0 verify --task` | **VERIFY: PASS EXIT=0**（30 开工前复跑） |
| pre-30 invoke 齐套 | 10 task_draft + 20 task_audit 在 `docs/harness/invokes/by-task/hitl-resume-replay-contract/` |

## 改动文件清单

| 文件 | 性质 | 说明 |
|------|------|------|
| `tests/test_hitl_resume_events.py` | 段 2b 新增两测（a30b3d3 红 → e4a54d9 绿） | `test_close_done_carries_latency_ms`（RED=KeyError 缺键 · F-OBS-1 同形）+ `test_close_done_has_no_model_key_control`（FP-1 钉案对照 · 断言不硬造 model 键） |
| `tests/test_lg_rag_sse_resume.py` | F-OBS-2 节新增四测（a30b3d3 红 → e4a54d9 绿） | router 面 409+Retry-After（patch `router.load_events_after` side_effect=`LgRagRunInFlightError`）；DB 级三态（skipif not DB_AVAILABLE · 真 PG）：在飞拦截（含默认 flag 关照常返回对照 · 实证读取路径真 PG 下不抛）/ 挂起放行 / 沉降放行 |
| `app/ops/hitl/resume.py` | F1（e4a54d9 · +3 行） | `ResumeEventSink.close()` 终帧 done 增 `latency_ms`：`int((time.perf_counter() - self._started) * 1000)`——与 lg-rag/chat SSE done 同口径 · `_started` 复用零新状态 |
| `app/ops/lg_rag/event_store.py` | F2 存储面（e4a54d9 · +39 行） | `LgRagRunInFlightError` + 只读谓词 `run_stream_closed`（done/error 帧=收尾）+ `load_events_after` kw-only `refuse_in_flight=False`（assert_run_owned 后、SELECT 前拦截 · 缺省关零 diff） |
| `app/ops/lg_rag/router.py` | F2 路由面（e4a54d9 · +28 行） | replay 端点 `load_events_after(..., refuse_in_flight=True)` + 增捕 `LgRagRunInFlightError` → **409 + Retry-After: 2** + docstring 补 409 语义 |
| `docs/_tech_graph/l1/01_modules.md` | F4 回写（61094bf） | `lg_rag` 行 + `hitl` 行各增 2026-10-13 备注（不新增一级模块 · 零新跨模块边 · 不增 implementedBy · 零新表/迁移/SSE 事件） |
| `docs/tasks/active/task_hitl_resume_replay_contract.md` | 回填（本 invoke 轮） | TC1–TC4 勾选 + 自检结论（30）+ 修订记录 |

## 验收命令结果

| # | 命令 | exit | 结果 |
|---|------|------|------|
| 1 | `uv run python -m pytest tests/test_hitl_resume_events.py tests/test_lg_rag_sse_resume.py -q` | 0 | **29 passed**（红测时序：a30b3d3 时 **5 failed 24 passed** · 五红签名全预期：`KeyError 'latency_ms'` / `AttributeError: ... no attribute 'LgRagRunInFlightError'` / `TypeError: ... unexpected keyword argument 'refuse_in_flight'`×3 → e4a54d9 全绿） |
| 2 | `uv run python -m pytest tests -q`（全量 · 真 PG） | 1 | **1803 passed, 1 skipped, 5 failed**；**基线对照**：clean tree（stash 实现改动后同 HEAD a30b3d3）同五用例复跑 **同 5 红同名同因**（test_capability_lookups×3 / test_hitl_approval_consumption::test_ta2_ttl_db_store_expired_not_consumed / test_lg_rag_multi::test_unknown_tool_at_invoke_recorded_and_continues · 环境性既有）→ **零新增红成立** |
| 3 | `uv run ruff check`（五触碰文件） | 0 | **All checks passed**（初跑 2 个 I001 import 排序 --fix 收编进 e4a54d9；仓级 54 个为 clean tree 同量既有 · 零新增） |
| 4 | `./scripts/graph-compile.sh` | 0 | EXIT=0（`docs/_tech_graph/shared/graph.json` 再生 freeze 日期噪音已 checkout 还原 · 纪律「再生噪音文件一律还原」；triggers/branches 词汇 warning 既存不咬 exit） |
| 5 | `npx spec-wave@3.3.0 verify --task` | 0 | VERIFY: PASS（三闸 approved） |

## TC1–TC5 逐条结论

- **TC1 终帧字段契约（红测先行）** ✅：RED（a30b3d3 · `KeyError 'latency_ms'` 与 F-OBS-1 缺口同形）→ GREEN（e4a54d9 · 断言 int ≥ 0）；`model` 按 FP-1 裁定 **不补**，钉案对照测试 `test_close_done_has_no_model_key_control` 在案。
- **TC2 在飞 replay 语义化** ✅：409 + `Retry-After: 2`（正整数）；「不再出现 500」成立路径=在飞面整体不再触达读路径（前置判定拦截于 SELECT 前）；仓内（mock+真 PG）实证在飞读取路径**不抛**——live 500 具体异常类型不可仓内复现，语义化前置判定替代异常映射表（根因留痕口径照登 FP-4：settled 路径未知异常仍 500 fail-closed 不吞错）。
- **TC3 沉降后零 diff** ✅：DB 测 terminal 放行 + 挂起（`done{waiting_approval}`）放行；`refuse_in_flight` 缺省 False 且 `load_events_after` 全仓唯一生产调用方=router replay → 其余面零 diff；404/422 既有断言零新增红存续。
- **TC4 反回归全量对拍** ✅：上表 #2/#3/#4（环境性红 5 枚同名同因照登 · 零新增）。
- **TC5 live 对照（40 帽）** ⏳：待 40 棒复现 web 联调 S2/S3 同形态并回执联调链（环境依赖承 R1 观察项 O3 前例）。

## 关键裁定与实证记录

1. **FP-1 裁定：`model` 键不补（禁伪造钉案）**：`grep model app/ops/lg_rag/sse_stream.py` 零命中 → lg-rag live done 本身无 model；`chat/streaming.py:290-297` 的 model 来自 chat 模块自有 run 记录，非 lg-rag 契约面；resume 全链（`resume_hitl_run`/`_resume_with`/`ResumeEventSink`/`_execute_decided_resume`）无 model 来源；`ops_lg_rag_run_events` 表（`app/db/models.py:323-344`）无 model 列。F1 只补 `latency_ms`，对照测试钉死「不硬造」。
2. **F2 判定面刻意不复用 `run_is_terminal`（回复 R1 观察项 O2）**：`run_is_terminal`（event_store.py:93-125）把 `done{waiting_approval}` 算**非终态**（其语义是「终态」供补偿扫描）；而挂起 run 的 replay 是既有合法操作须零 diff。409 判定面应为「流是否收尾」→ 新只读谓词 `run_stream_closed`（存在 done[任意 status]/error 帧=收尾）。O1（`_started` 可复用）已采纳——零新状态。
3. **在飞 500 根因留痕口径**：仓内无法复现 live 500 的具体异常类型（mock 与真 PG 下在飞读取路径均正常返回）；30 以**前置语义化判定**替代「异常类型→映射表」路线——在飞读取路径整体不再触达，settled 路径未知异常仍 500（FP-4 fail-closed）。此口径即 FP-4「实证枚举异常类型」的实证结论：**仓内无可枚举异常，live 异常类型留 40 live 对照观察**。
4. **环境动作**：本机 postgresql@18（brew）原停止 → `brew services start postgresql@18` 启动后 DB 测真跑（PG 未跑时 `test_stream_frames_include_cursor` 环境性红 · 非本 task 引入 · PG 起后转绿）。pytest 须 `uv run python -m pytest`（系统 python 无 asyncpg）。

## 经验捕获（experience_capture=required）

1. **压缩摘要不可作 edit 锚**：本轮 e1 edit 失败实证——压缩摘要里 `close()` 的简化形态（四键 dict · `self._run_id`）与实际代码（`_emit("done","system",{...})` · `self.run_id` · status 三元表达式）不符；**edit 前必重读精确区域行号**，摘要只作定位索引。
2. **run_code 模板字面量反引号截断两连发**：docstring RST `\`\`x\`\`` 标记与 `\`\`\`` 代码栅在 JS 模板字面量里终止字符串（报 lexing error / "is not a function"）；规避=写盘内容避免反引号，或以 \` 转义。
3. **`uv run` 再生 uv.lock 破坏 `git stash pop`**：stash 窗口内跑 `uv run`（pytest/ruff）即再生 uv.lock 脏改 → pop 冲突；解法 `git checkout -- uv.lock && git stash pop`。基线对拍流程须把「uv.lock 还原」列为固定步骤。
4. **CI pytest 假绿注记存续**：conftest.py:12-16——CI 无 postgres service，DB 用例 skip 绿；真跑基线以本地真 PG（opsdesk_test）为准。本棒全量对拍即本地真 PG 口径。

## 非范围照登

web 仓去兜底（web PR #61 前端兜底已落 · 去留 web 仓自裁）· `model` 键（FP-1 钉案不补）· live 500 异常类型映射表（仓内不可复现 · 前置判定替代）· 40 帽 live 对照（TC5）。

## 修订

| 日期 | 说明 |
|------|------|
| 2026-10-13 | 30 交付：RED a30b3d3（5 红签名全预期）→ GREEN e4a54d9（29 passed）· 全量 1803 passed 零新增红（clean tree stash 对拍同 5 既有红）· ruff 触碰文件全绿 · graph-compile EXIT=0 · modules.md 回写 61094bf · FP-1 model 不补钉案 · F2 `run_stream_closed` 判定面裁定（O2 回复）· TC1–TC4 勾选（TC5 待 40） |
