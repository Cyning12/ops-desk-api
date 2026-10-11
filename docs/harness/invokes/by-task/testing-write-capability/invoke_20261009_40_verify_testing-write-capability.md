# 40 invoke · testing-write-capability（核验 30 r2 交付 · 独立复跑 · 不采信自报）

> **帽**：40-verify · **task**：docs/tasks/active/task_testing_write_capability.md
> **分支**：task/testing-write-capability（worktree d2-testing-write-capability · base master 57fbf84）
> **核验对象**：94b3716（loader V1/V8 + CapabilitySpec 顶层幂等键）· d571e58（testing.v1.yaml + 罐头 adapter + allow_write_tags_any + env 门控）· 336a769（14 枚新测）· fb9ee73（图谱 + 30 invoke r2）
> **日期**：2026-10-09 · **结论**：**PASS（带偏差登记 · 可进 PR 队列）**——30 自报 A2–A8 全部独立复跑成立；A1 live 全链实跑：挂起/pending/decide 三段全真达成，resume 末段复现 30 已登记之 409 设计缺口（逐字一致 · 非本 task 回归）

---

## 逐项核验结论

### 1. diff 面 + O5（V1/V8 文案逐字节）✅

`git diff master --stat`：21 文件 +1644/-6，与 30 自报四面（capability 五文件 + testing.v1.yaml + 图谱 + 测试）一致，无面外改动。
**O5 逐字节核验**：`git diff master -- app/ops/capability/manifest.py` 全读——V1（:843-846）与 V8（:890-893）两条 `raise ManifestError(f"{loc} V1/V8: ...")` **文案行在 diff 中为上下文行（无 +/-）= 对 master 逐字节零改动**；改动仅触发条件（单源 http 块键 → http 块键 or 顶层键合取）与新增顶层键解析/承载（:547-555 · :626）。golden eval 对拍：`pytest tests/eval/test_eval_agent_golden.py` → **9 passed**（baseline_v1.json 逐字钉死文案全绿）。

### 2. A8 / A5 / A2 / A3 抽跑 ✅（全亲跑，未采信）

`pytest tests/test_capability_testing_write.py -v` → **14 passed**：
- A8 四断言：`test_a8_v1_still_blocks_write_local_fn_without_any_key` / `..._with_top_level_key_loads` / `..._read_without_top_level_key_zero_diff` / `..._read_with_top_level_key_hits_v8` 全 PASSED；
- A5 `test_a5_canned_adapter_zero_io` PASSED + **40 逐行亲核** `defaults.py::testing_write_echo`（diff 全文）：纯函数返回罐头 dict，零 import 零 IO，docstring 含「语义 mock · 无真实写操作」；
- A2 `test_a2_off_zero_diff` / A3 `test_a3_loaded_but_not_visible_without_allow_env` / 放行三例（命中豁免/未命中仍裁/high 恒裁）全 PASSED；
- A6 `test_a6_manifest_loads_and_fields_pinned` PASSED；testing.v1.yaml 逐字段对钉死契约 ✓（write/local_fn/hitl.required=true/顶层 idempotency_key=`{{request_id}}`/risk=medium/tags 含 testing/enabled=true/可撤销四字段齐）。

### 3. B1 十二处亲跑 ✅

`pytest tests/test_capability_manifest.py test_capability_domain_allowlist.py test_lg_rag_supervisor_capability_catalog.py test_admin_capability_observability.py test_capability_visibility_and_receipts.py test_capability_gateway.py test_strategy_builder.py test_strategy_scenario.py test_prompt_assets.py test_prompt_assembly.py test_hitl_pending_decide.py test_hitl_resume.py test_lg_rag_structured_output_p2.py test_multi_replica_dualproc.py -q` → **234 passed, 1 skipped**（与 30 自报一致；1 skipped=DB 门控既有行为）。含 capability/hitl 相关 8 文件。`test_allow_tags_does_not_waive_deny_write`（钉死语义）原样绿。

### 4. A1 live 全链实跑（30 留转项 1）——三段达成 · 末段 409 如实登记

**环境**：docker db(PG15 · healthy) + 本机 uvicorn :8010（worktree 代码）；env 组命令行前置（import app 前生效）：`LG_RAG_DELEGATION_TOKEN_MODE=enforce` + `OPS_CAPABILITY_EXTRA_MANIFESTS=app/ops/capability/manifests/testing.v1.yaml` + `OPS_CAPABILITY_ALLOW_WRITE_TAGS=testing`（`LG_RAG_DELEGATION_TOKEN_SECRET` 承 .env）；登录 admin/maintainer cookie（`scripts/create_initial_user.py` 幂等）；`GET /api/ops/admin/capability/catalog` 实证 `testing.write.echo` 已在可见集（visible_ids 6 枚）；`/api/ops/hitl/runtime` = db 持久化。

**⚠️ 40 新发现（三 env 组之外的第四道门）**：首发 run 的 SSE `node.progress` 帧实证 `allowed_capability_ids` = 静态五枚只读 id、**不含 testing.write.echo**——`app/ops/strategy/config.py:14-23` `CAPABILITY_ALLOWLIST_BY_KEY["supervisor"]` 为**静态候选 map**（无 env 口），builder 节点 `allowed = candidates ∩ visible`（builder.py:180-182）使该 tool 永不进 supervisor 可见集；即使 LLM 幻觉出该 id，`_subtasks_have_valid_tool_ids`（nodes.py:147-157）也会拒 → fallback rag。task/30 的可见性论证止于 baseline 层，未覆盖此层。**处置**：以**测试等价 shim** 补位（启动器 `/tmp/ops40_serve.py`：env 前置 → import app.main → `strategy.config.CANDIDATE_CAPABILITY_IDS = ["testing.write.echo"]` 运行期覆盖——与仓内测试 monkeypatch 该模块全局同一机制，builder 运行期读取；**仓内代码零改动 · 判定逻辑零改动**），如实登记。

**全链实录（shim 补位后 · run_id=0eb059a5883b497997f790893842efdc · thread=e79bebe867ca4a298cacd3ebcb078ff4）**：

| 段 | 结果 | 证据摘录 |
|----|------|----------|
| ① plans 含 tool → 挂起 | ✅ | SSE `event: hitl.waiting`：`blocked_by="delegation_issue_hitl_required"` · `reason="委派签发需人工审批（capability testing.write.echo 非只读（side_effect=write））"` · request `hitl_3871606f0b84498ebe04` · `unlock_subtask_id=""`；收尾 `done{status:"waiting_approval"}` |
| ② GET /api/ops/hitl/pending | ✅ | cookie maintainer 可见该申请（归属过滤生效 · 仅列本人） |
| ③ decide approved | ✅ | HTTP 200 · `status="approved"` · `decision_by="admin"` · `persisted=true`；重复 decide → **409**「申请已是 approved，不接受重复决定」（既有守卫 ✓）；decide 后 pending 不再含该申请 ✓ |
| ④ resume | ⚠️ **409（预期内 · 30 已登记）** | HTTP 409 · detail=**「已批准但拿不到待解锁的步骤（unlock_subtask_id 为空）」**——与 30 invoke 实证（router.py:404-410 · 单子任务计划无 depends_on∩plan_prefix_ids → unlock 为空）**逐字一致**；`done{completed}` **未达成，如实登记，未伪造** |

**裁定**：④ 与 30 证据对拍一致 → **既有链设计缺口 · 非本 task 回归**。机制段兜底（task A4④ 明文允许）由 `test_a4_enforce_chain_suspend_pending_decide_resume` 覆盖（本帽亲跑 PASSED：真 loader 条目 + 真 interrupt + driver 级 resume verdict=replan）。30 另实证「批准后重下发同 tool 仍再拦（auto_approve_ok 不消费审批结果）」——本帽实读 delegation.py:488-514 确认其不读审批结果，成立。

### 5. 全量 pytest 复跑 ✅

口径对齐 30 invoke（worktree .env 承主 checkout · 命令行中和昨日验收残留 enforce 组：`LG_RAG_DELEGATION_TOKEN_MODE=off OPS_CAPABILITY_EXTRA_MANIFESTS= OPS_HITL_PERSISTENCE= OPS_CAPABILITY_PERSISTENCE= OPS_CAPABILITY_ALLOW_WRITE_TAGS=`）：`pytest tests -q` → **1661 passed, 1 skipped, 0 failed**（58.83s）——与 30 自报 1661/1/0 一致，零红无需基线对拍。

### 6. ruff / graph-compile / lint / verify 终态

| 项 | 结果 |
|----|------|
| `./scripts/graph-compile.sh` | ✅ EXIT=0（全 OK + mermaid check ok） |
| `npx spec-wave task lint` | ✅ LINT: PASS · EXIT=0 |
| `npx spec-wave verify --task ...` | ✅ VERIFY: PASS · EXIT=0（三闸 approved 如实） |
| `ruff check` 触及路径 | ⚠️ **偏差登记**：app 五文件对 master 影子树逐文件对拍——manifest.py 三枚（I001:22 / UP038:588→597 / UP034:698→708，行号位移=新增行所致）**全 master 基线既有，零新增**（30 自报「两条」计数小偏差，方向正确）；**但新测文件 tests/test_capability_testing_write.py:257 有一枚新增 UP038**（isinstance 元组 → X \| Y），30 自报「触及路径零新增」不严谨。CI ruff 步骤注释中（pytest.yml:53）→ **不阻合并**，建议维护者顺手修一行 |

### 7. task 自检结论段回填 ✅

已回填「自检结论（执行者）」节（A1–A8 逐项 + 本 invoke 链接 + 三条偏差登记）。task 状态流转（draft → done/CLOSE）留维护者裁定。

### 8. 验收登记偏差 #1 闭环裁定

据 live 实证：**可审对象已注册且四段中三段（挂起 → pending 可见 → decide 置决）全真可达**，第四段 resume 在单子任务计划形态下撞既有 409 缺口（unlock_subtask_id 为空 · router.py:404-410），叠加 30 实证之「审批结果不回写签发判定（重下发同 tool 再拦）」——**done{completed} 末段缺口属既有链设计缺口，非本 task 回归，另立 task 由维护者裁定**（建议合并「签发审批消费回路」与「unlock_subtask_id 空形态」两面一 task；同时把 40 新发现之 strategy 候选 map 第四道门纳入该 task 视野，或在本 task 验收口径补记）。**偏差 #1 处置路径（注册非只读测试 capability）本身已达成其目的**：enforce 下真实 HITL 挂起自此有全真可审对象。

---

## FAIL 判定扫描

30 无造假：自报 A2–A8、B1 十二处、全量 1661、O5–O7、lint/verify/graph-compile **全部独立复跑一致**；30 对 A1 末段的「如实留转 + 409 预警」与 live 实证逐字吻合（诚信加分项）。偏差两枚（ruff 新测文件 1 枚新增 UP038 · 「两条 vs 三条」计数小偏差；第四道门未入 task 视野）均不阻塞。

## 给维护者的裁定建议

1. **可进 PR 队列**（合并不依赖 done{completed} 末段：A1 机制段 + live 三段已证可审对象可用；末段缺口为 master 既有设计真态）；
2. **另立 task**：「签发审批消费回路（审批结果回写 auto_approve_ok / _delegation_issue_block_reason）+ 单子任务计划 unlock_subtask_id 为空形态」——建议把 strategy 候选 map env 口（第四道门）一并纳入；
3. 顺手修 tests/test_capability_testing_write.py:257 UP038 一行（或并入下一 task）；
4. task 状态流转与 CLOSE 由维护者据本 invoke 裁定。

## 环境注记

- live 证据文件（ephemeral · 摘录已嵌上文）：/tmp/ops40_sse.log · /tmp/ops40_server.log · /tmp/ops40.jar · /tmp/ops40_serve.py；
- 本机 shell 代理 env（NO_PROXY 含 `[::1]`）会令 httpx 0.28 抛 `InvalidURL("Invalid port: ':1]'")` 致全图 LLM 调用失败——起服务须剔除代理变量（本机直连 siliconflow 可达）；此为本机环境坑，非仓码问题；
- 核验全程未改仓内代码；/tmp 启动器不入仓。

## 修订

| 日期 | 说明 |
|------|------|
| 2026-10-09 | 40 核验落盘：逐项独立复跑全过 · A1 live 全链实录（三段达成 + resume 409 对拍一致）· 第四道门新发现 · 偏差 #1 闭环裁定 · PASS 带偏差登记 |
