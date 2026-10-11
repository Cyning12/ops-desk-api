# 30 invoke · testing-write-capability（r2 · 裁定四=乙已落地 · 全量交付）

> **帽**：30-implement · **task**：docs/tasks/active/task_testing_write_capability.md（修订版）
> **分支**：task/testing-write-capability（worktree d2-testing-write-capability · base master 57fbf84）
> **日期**：2026-10-09 · **结论**：**交付完成**（F1–F7 全量 · 四 commit · 未 push 未开 PR）
> **前次**：invoke_20261009_30_implement_testing-write-capability.md（GATE_STOP · loader V1/V2 夹击实证）——本次承接裁定四=乙落地，零重蹈

---

## 人工闸扫描（GATE_VERIFY · 首输出）

| human_gate_id | task表status | 用户/invoke声称 | 一致？ | blocks_30 | 30可开工？ |
|---------------|--------------|-----------------|--------|-----------|------------|
| HG-TASK-DRAFT | approved（维护者重签 · 代录=00 · 2026-10-09） | approved（委托令） | Y | Y | ✅ |
| HG-AUDIT-R1 | approved（R2 PASS 重签 · 备注裁定四=乙） | approved | Y | Y | ✅ |
| HG-GRAPH-MODULES | approved（在册 · l1 模块内增量） | approved | Y | — | ✅ |
| HG-PILOT-OPSDESK-GLAYER | n/a | — | Y | N | — |

reviews：task_testing_write_capability_audit_R2_20261009.md 存在且 R2 PASS？ **是**（零阻塞 · O5–O7 非阻塞）
pre-30 invoke：required ∩ {10,20,00} 齐全？ **是**
机械辅助：`npx spec-wave verify --target . --task docs/tasks/active/task_testing_write_capability.md` → **VERIFY: PASS · EXIT=0**（本帽亲跑 2026-10-09）

---

## Commit 拆分（中文 conventional · 未 push 未开 PR）

| # | hash | 内容 |
|---|------|------|
| 1 | 94b3716 | feat(capability): manifest 顶层 idempotency_key 字段与 loader V1/V8 适配（裁定四） |
| 2 | d571e58 | feat(capability): 注册测试专用写能力 testing.write.echo 与 env 门控放行口径 |
| 3 | 336a769 | test(capability): testing-write-capability 验收单测（A2/A3/A4/A5/A6/A8） |
| 4 | （本 invoke 所在 docs commit · hash 见 git log） | docs(graph+invoke): capability 行在册备注 + 本 invoke |

> 拆分说明：types.py 同含 CapabilitySpec（schema）与 CapabilityFilter（filter）两族字段，
> 为保 commit 1 独立可运行（manifest.py 运行期读 `spec.idempotency_key`），
> types.py 的 CapabilitySpec 字段随 commit 1、CapabilityFilter 字段随 commit 2
>（commit 1 落盘前临时摘除 filter hunk · commit 后立即复原 · 两 commit 各自 pytest 语义完整）。

---

## 验收自证（A1–A8 逐项 · 实跑留证）

### A1（enforce 全链）——机制段 pytest 集成已自证；live HTTP 段留 40（如实 · 未伪造）

- **pytest 集成（本帽实跑）**：`tests/test_capability_testing_write.py::test_a4_enforce_chain_suspend_pending_decide_resume`
  用**真 loader 加载的 testing.write.echo** + 真 `_join_subtasks`/`_observe`/`_persist_hitl`/
  `observe_node`（真 interrupt）/`resume_hitl_run` 跑通：
  **挂起**（blocked_by=delegation_issue_hitl_required · hitl_waiting 载荷）→
  **pending 落库可见**（InMemoryHitlStore.alist 命中）→ **decide(approved)**（store.adecide 真守卫）→
  **resume**（图真恢复 · verdict=replan · hitl_unlocked_ids=[sid] · decided_by 留痕）。
  探针独立复现（/tmp/probe_chain.py · 已删）输出逐行同上。
- **30 实证发现（设计真态 · 如实记录 · 判定逻辑零改动纪律下不触碰）**：
  ① delegation 签发审批块 `unlock_subtask_id` 为空（`_persist_hitl` 取 depends_on∩plan_prefix_ids，
  单子任务计划无此前缀）→ HTTP resume 端点对该形态 409（router.py:404-410「已批准但拿不到待解锁的步骤」）；
  ② 即便 driver 级以 approved=[被拦 sid] 恢复，批准后**重下发同 tool 仍再拦**
  （`_delegation_issue_block_reason`/`auto_approve_ok` 不消费审批结果 · 探针实证
  `post-approval issue_block_reason='委派签发需人工审批（…非只读（side_effect=write））'` ·
  `re-blocked on redispatch: ['delegation_issue_hitl_required']`）。
  即「decide(approved) → resume → **done{completed}**」末段在 enforce+写能力下须经
  「replan 后计划不再含写 tool」收敛（LLM 依赖），或另立 task 议「签发审批的消费回路」
  （审批结果回写签发判定）。本 task 钉死契约「判定逻辑零改动」明确禁止本帽触碰该语义。
- **留 40**：live HTTP/SSE 全链（三 env 组 + 真服务 + cookie maintainer：
  `GET /api/ops/hitl/pending` → `decide` → `resume` → done 帧断言）命令与响应摘录落 40 invoke；
  本帽提供机制段断言兜底（task A4④ 明文允许：「真实挂起段由 A1 本地链兜底」）。

### A2（off 零 diff）✅

`test_a2_off_zero_diff`：三 env 皆不设 → `extra_manifest_paths()==()` · snapshot 不含
testing.write.echo · count==5 · baseline 可见集恰为 builtin 5 枚 · 加载 oa 清单后恰 8 枚
（_BUILTIN_IDS|_OA_IDS · 验收基线口径）· 均不含本条目。全量 pytest 对照见末节（零新增红）。

### A3（加载≠可见 · deny_write 不全局松）✅

`test_a3_loaded_but_not_visible_without_allow_env`：只加载不放行 → snapshot 含条目 ·
baseline 可见集不含；`test_allow_tags_does_not_waive_deny_write`（domain_allowlist:102-112 钉死语义）
原样绿（B1 亲跑见下）。

### A4（新增测试）✅

14 枚全绿（`.venv/bin/python -m pytest tests/test_capability_testing_write.py -q` → **14 passed**）：
① allow_write_tags_any 三例（命中豁免/未命中仍裁/high risk 恒裁）② manifest 显式加载后
registry 含条目且 adapter 可调 ③ 罐头零 IO 断言（AST 级）④ enforce 集成（见 A1 机制段）。

### A5（罐头防线）✅

`test_a5_canned_adapter_zero_io`：AST 剔除 docstring 后函数体无
requests/httpx/subprocess/open(/.write/Path/socket/urlopen · 零 import ·
docstring 含「语义 mock」· 同参同果无状态。40 可逐行复核 `defaults.py::testing_write_echo`。

### A6（字段钉死）✅

`test_a6_manifest_loads_and_fields_pinned`：side_effect=write · kind=local_fn ·
hitl.required=true · 顶层 idempotency_key 非空（`{{request_id}}`）· risk_level=medium（≠high）·
tags 含 testing · enabled=true · tenant_scoped=false · 可撤销性四字段齐；
另断言 Policy 写闸第二道仍在（invoke 无确认 → `policy_blocked: write_not_confirmed`）。

### A7（B1 旧测清单 · 12 处亲跑）✅

```
.venv/bin/python -m pytest tests/test_capability_manifest.py tests/test_capability_domain_allowlist.py \
  tests/test_lg_rag_supervisor_capability_catalog.py tests/test_admin_capability_observability.py \
  tests/test_capability_visibility_and_receipts.py tests/test_capability_gateway.py \
  tests/test_strategy_builder.py tests/test_strategy_scenario.py tests/test_prompt_assets.py \
  tests/test_prompt_assembly.py tests/test_hitl_pending_decide.py tests/test_hitl_resume.py \
  tests/test_lg_rag_structured_output_p2.py tests/test_multi_replica_dualproc.py -q
→ 234 passed, 1 skipped in 11.35s   # 1 skipped=DB 门控用例（既有行为）
```

含 O3 补列两处（test_lg_rag_structured_output_p2.py · test_multi_replica_dualproc.py）。
`test_baseline_filter_shape_is_stable` 四字段断言原样绿（新字段默认 None · 允许新增不断言旧删）。

### A8（loader 校验 · 裁定四）✅

四断言全绿（`test_a8_*`）：① 两键皆缺 → ManifestError「V1: side_effect=write 必须有
idempotency_key」（逐字）② 顶层键 → 可加载且 spec.idempotency_key 承载 ③ read 无顶层键 →
加载零 diff（既有 manifest 测试原样绿 · A7 佐证）④ read 误声明顶层键 → ManifestError
「V8: side_effect=read 不应声明 idempotency_key」（逐字）。

### O5–O7 遵守证据

| 观察项 | 遵守实证 |
|--------|----------|
| **O5**（V1/V8 文案逐字节不变） | diff 实证：两处 raise 文案行零改动（仅触发条件从 `http_block.get(...)` 单源放宽为 `http 块键 or 顶层键` 合取）；`tests/eval/test_eval_agent_golden.py` → **9 passed**（baseline_v1.json:102,134 逐字对拍绿） |
| **O6**（字段族文档三处同步） | ① types.py CapabilitySpec 字段注释（裁定四语义 + 无运行期消费方如实标注）② builtin.v1.yaml 头注释补字段族口径 ③ 01_modules.md capability 行备注（见 F5） |
| **O7**（顶层幂等键无运行期消费方 · 语义如实） | defaults.py::testing_write_echo docstring 与 types.py 注释、testing.v1.yaml 头注释、图谱备注四处均如实写「加载期护栏/声明位 · 当前对 local_fn 无运行期消费方」；未虚构任何消费面 |

### F5（图谱同步）✅

`docs/_tech_graph/l1/01_modules.md`：capability 行增「testing-write-capability（2026-10-09 · D2）」
在册备注（manifest/adapter/filter/env/loader 五符号齐 · 不新增一级模块 · 不增 implementedBy ·
零新跨模块边）+ 人签记录表补 HG-GRAPH-MODULES 行（维护者签「图谱在册」2026-10-09 · 00 代录 · 30 回写）。
`./scripts/graph-compile.sh` → **EXIT=0**（全 OK + mermaid check ok）。

### 全量回归与静态检查

- `pytest tests -q`（post-commit 终跑）：**1661 passed · 1 skipped · 0 failed**（59.96s）。
  口径说明：worktree 复制主 checkout .env（gitignored · 供 SILICONFLOW_API_KEY 等），
  命令行显式中和该 .env 里昨日验收残留的 enforce 组
  （`LG_RAG_DELEGATION_TOKEN_MODE=off OPS_CAPABILITY_EXTRA_MANIFESTS= OPS_HITL_PERSISTENCE= OPS_CAPABILITY_PERSISTENCE=`；
  load_dotenv 不覆盖既有 env · 故命令行优先）。
  两轮中间态红均证非新增：① 无 .env 时 test_memory_vector_p1 红=缺 SILICONFLOW_API_KEY
  （master stash 基线同红实证）· test_episode_pattern_mine 红=git porcelain 守护被未跟踪
  testing.v1.yaml 触发（commit 后自绿 · 终跑已含）② 带 .env 未中和时 4 红
  （delegation enforce 残留环境所致）在主 checkout（无本 task 代码）同测同红实证
- `ruff check` 触及路径：零新增（manifest.py 两条 I001/UP034 为 master 基线既有 · 逐文件对拍实证）
- `npx spec-wave task lint` → **LINT: PASS**

---

## 留转 40 清单

1. **A1 live HTTP/SSE 全链**（三 env 组 `OPS_CAPABILITY_EXTRA_MANIFESTS=app/ops/capability/manifests/testing.v1.yaml`
   + `OPS_CAPABILITY_ALLOW_WRITE_TAGS=testing` + `LG_RAG_DELEGATION_TOKEN_MODE=enforce`
   + `LG_RAG_DELEGATION_TOKEN_SECRET` · env 须在 import app 前生效）：起服务 → plans 含
   testing.write.echo 的 run → hitl.waiting（blocked_by=delegation_issue_hitl_required）→
   GET /api/ops/hitl/pending 可见 → decide approved → resume → done 帧断言。
   **注意 30 实证**：单子任务计划 resume 会 409（unlock_subtask_id 空）；批准不消费签发判定
   （重plan 含写 tool 则再拦再挂起）——done{completed} 达不成时如实登记偏差，勿伪造；
   「签发审批消费回路」是否另立 task 由维护者裁定。
2. 任务书「自检结论（执行者）」节回填（A1–A7 结论 + 本 invoke 链接）。
3. task 状态流转与验收登记偏差 #1 闭环由 40/维护者据 live 结果裁定。

## 环境注记

- worktree 无 .env（gitignored 不带入）：已复制主 checkout .env 供全量 pytest（git 零 diff）；
  `.venv` 补装 pytest/pytest-asyncio（仓内既有解释器 · 未改 uv.lock —— `uv run` 的 uv.lock
  副作用已 `git checkout` 还原，承前次 GATE_STOP 教训）。
- /tmp 探针文件（probe_r2.py / probe_chain.py）用后已删。

## 修订

| 日期 | 说明 |
|------|------|
| 2026-10-09 | 30 r2 落盘：F1–F7 全量交付（4 commit）· A1–A8 逐项自证 · B1 十二处亲跑绿 · O5–O7 遵守实证 · A1 live 段与「签发审批消费回路」裁定留转 |
