# Invoke · 30 帽 · 实现（api-w-hitl-tenant-fix）

| 字段 | 值 |
|------|-----|
| hat_id | `30`（实现棒 · auth311 六要求承接） |
| task_slug | `api-w-hitl-tenant-fix` |
| task_paths | `docs/tasks/active/task_api_w_hitl_tenant_fix.md` |
| related_review_or_none | `docs/harness/reviews/task_api_w_hitl_tenant_fix_audit_R1_20261103.md` |
| git_branch | `agent/hitl-tenant-fix-task-955c1cd011b6`（30 PR · base `master`） |
| created_utc_or_local | 2026-11-03 |
| notes | GATE_VERIFY PASS 后开工（`npx spec-wave verify` EXIT=0 · 四闸 approved）；红测先行 RED dc4f4eb → GREEN 8e8e4a1 |

---

## §1 · 裁决值接线（HG-W-TENANT-DESIGN · PR #312 review 维护者签认）

| 裁决 | 接线 |
|------|------|
| ① A+B 组合 | `app/ops/hitl/router.py`：`_resume_row_tenant(row)` 唯一真源（fail-closed 空 tenant → `ResumeError("tenant_missing")`）；`_execute_decided_resume` 驱动图前 `set_current_tenant(row_tenant)` + finally `reset_current_tenant`（**手动/自动同源唯一实现** · 对照 run_worker.py:120/153 成对形态）；`resume_request` 手动入口：session 租户（`request.state.ops_tenant_id`）存在且 ≠ 单据 tenant → 403 `tenant_scope_denied`（对齐 lg_rag/router.py:376-384 先例）；Bearer 机读无 session → 纯快照不拦；空 tenant → 请求内 409 fail-fast |
| ② 守卫扩列 | `app/ops/lg_rag/multi/nodes.py`：`_write_execution_approval` 租户检查 `_BLOCKED_BY_CAPABILITY_WRITE` 单类判断 → `_WRITE_CONSUMABLE_BLOCKED_BY` 两类（delegation 跨租户/空 tenant fail-closed 不消费）· docstring 同步改写 |
| T-fix-2 打戳 | `nodes.py`：新增 `_delegation_blocked_terminal(item, issue_reason)`（blocked_by + hitl_required + `tenant_id=current_tenant_or_default()` · 对齐 capability_write 闸 :1881-1925 stamping 先例 · 无上下文回落 A 同口径）；签发拦截调用点（原 :1274-1276 三连赋值）改用 helper |
| 回执/日志真值 | 消费日志/回执 tenant 走还原后 ContextVar（`_execute_decided_resume` 快照域内），N-R2-1 回落 A 现场根治 |

## §2 · 验证（auth311 要求 1/5）

| 命令 | 退出码 | 摘要 |
|------|--------|------|
| `uv run pytest tests/test_hitl_resume_tenant_fix.py tests/test_write_approval_gate.py` | 0 | 22 passed（RED dc4f4eb：7 failed/1 passed → GREEN：22 passed） |
| `uv run pytest tests/test_hitl_resume.py test_hitl_resume_async.py test_hitl_resume_ttl_gate.py test_hitl_resume_events.py test_hitl_auto_resume.py test_hitl_pending_decide.py test_hitl_approval_consumption.py test_hitl_approved_replan_quality.py test_hitl.py test_tenant_context.py test_hitl_observe_config_injection.py` + 上两行 | 0 | 218 passed（旧测影响面修复后全绿） |
| `uv run pytest tests`（全量 ×2 对拍） | 0（exit 0 含基线红） | 分支 4 failed/2032 passed vs origin/master 同集 4 failed/2020 passed——**失败集与 master 基线逐一同集**（test_tc8_diff_whitelist · embedder_failure_degrades · cross_instance_resume · diff_whitelist_scenario 四红为基线环境红 · 零新增红 · 净 +12 passed 为本波新测） |
| `uv run ruff check app tests` | 0 | All checks passed! |
| `./scripts/graph-compile.sh` | 0 | compile+check+normalize 全 OK（npx 走缓存二进制 · 代理间歇故障绕行记录见 §4） |
| `spec-wave task lint` / `spec-wave verify --target . --task …` | 0/0 | LINT: PASS · VERIFY: PASS（图谱锚点 skipped vocabulary_empty 照登） |

## §3 · 旧测 grep 影响面清单（auth311 要求 2 · 逐条标注）

| # | 用例/fixture | 处置 | 理由 |
|---|--------------|------|------|
| 1 | `test_hitl_resume.py::_approved_row` | **修改** | base 补 `tenant_id=TENANT_A`——裁决①③：新单须带戳、空 tenant fail-closed 拒 resume；旧形态（无 tenant 键）= 旧行为编码。用例语义不变 |
| 2 | `test_hitl_resume.py::_client` | **修改** | 扩可选 `tenant` 参数（默认 None = Bearer 形态零变化）+ 模块级 `Request` import（修 `from __future__ import annotations` 下嵌套依赖 lazy annotation 解析坑——不修的 422 症状：`query:request Field required`） |
| 3 | `test_hitl_resume_events.py::_row` | **修改** | 补 `tenant_id`（事件 sink/replay 用例 · 租户语义默认 A） |
| 4 | `test_hitl_pending_decide.py::_row` | **修改** | 补 `tenant_id`（decide/resume 状态机用例 · 租户语义默认 A） |
| 5 | `test_hitl_pending_decide.py` DB rebuild 内联 dict | **修改** | `tenant_id: ""` → `"ops-desk-pilot"`：原 `''` 为 incidental（未测租户语义），现空 tenant fail-closed 拒 resume 会拦截用例主链 |
| 6 | `test_hitl_approval_consumption.py` TA6 内联 row | **修改** | 补 `tenant_id`（空 unlock 409 用例 · 租户语义默认 A · 空 unlock 断言不动） |
| 7 | `test_hitl_auto_resume.py::_row` | **修改** | 补 `tenant_id`（auto/manual 同源执行体同口径 · 扫描链用例） |
| 8 | `test_write_approval_gate.py::test_w2_delegation_class_row_still_consumed` | **修改 + 更名** `_stamped_tenant_consumed` | 旧断言「delegation 空 tenant 可消费」与裁决②（守卫扩列）直接冲突 → 废止改写为带戳同租户可消费正样本；空 tenant/跨租户负样本新增两条钉死 fail-closed |
| — | 其余 resume/tenant/persist 相关用例（grep 面：`_approved_row`/`_row`/`_write_approved_req`/`tenant_id` 全部消费点） | **保留** | 218 条全绿零改动；`_write_approved_req` 本就带 tenant 戳（W2 面），守卫扩列后语义自洽 |

## §4 · 环境注记（诚实记录 · 不影响交付物真值）

- 本机代理 `127.0.0.1:7890` 间歇故障：gh CLI → api.github.com TLS 握手超时（PR 经 `curl --noproxy` 直连 REST 创建）；npx → npm registry 停滞（graph-compile/spec-wave 改走 `~/.npm/_npx` 缓存二进制 `spec-wave@3.5.0` 直达 · `$SW --version`=3.5.0 实证）；git fetch 直连成功。所有命令真跑，输出留存于本 invoke。

## §5 · 双 freeze 红线核验（auth311 要求 4）

- `lg-rag-sse-v1`：零 diff——未新增/改名/删改任何 SSE `event_type`（resume 段 `hitl.resumed`/`hitl.waiting`/`done` 语义不动；`git diff master...HEAD -- app/ops/lg_rag/sse_stream.py app/ops/lg_rag/event_store.py` 为空）
- `hitl-browser-decide-v1`：文件本体零 diff——`git diff master...HEAD -- docs/tasks/done/task_hitl_browser_decide.md` 为空；decide 400/404/409/422 语义零变化（test_hitl_pending_decide 全绿承接）

## §6 · 下一棒

`40`（自检/验收核对 · 回接条款：联调 C6 复测为人工联调动作，留 workspace 轨）

---

### 修订

| 日期 | 说明 |
|------|------|
| 2026-11-03 | 30 实现棒 invoke：裁决值接线 + 红→绿证据 + 旧测影响面 8 条逐条标注 + 双 freeze 红线核验 + 环境绕行注记 |
